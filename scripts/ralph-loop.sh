#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-build}"          # spec_author | plan | build
MAX_ITERS="${2:-10}"        # cap iterations
MODEL="${MODEL:-gpt-5.4}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PROMPT_FILE="prompt/prompt_${MODE}.md"
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "Missing $PROMPT_FILE"
  exit 1
fi

mkdir -p progress

# Derive a conventional branch slug from the active spec when available.
spec_slug=""
if [[ -f "IMPLEMENTATION_PLAN.md" ]]; then
  active_spec="$(grep -E '^Active spec:' -m 1 IMPLEMENTATION_PLAN.md 2>/dev/null | sed -E 's/^Active spec:[[:space:]]*//')"
  if [[ -n "${active_spec:-}" ]]; then
    base="$(basename "$active_spec")"
    spec_slug="${base%.*}"
  fi
fi

# Fallback to PROMPT.md if needed.
if [[ -z "${spec_slug}" && -f "PROMPT.md" ]]; then
  active_spec="$(grep -E '^Active spec:' -m 1 PROMPT.md 2>/dev/null | sed -E 's/^Active spec:[[:space:]]*//')"
  if [[ -n "${active_spec:-}" ]]; then
    base="$(basename "$active_spec")"
    spec_slug="${base%.*}"
  fi
fi

# Final fallback if nothing found.
if [[ -z "${spec_slug}" ]]; then
  spec_slug="$MODE"
fi

# Sanitize slug for branch naming.
spec_slug="$(printf '%s' "$spec_slug" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"

# Safety: always work on a branch.
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
  TS="$(date +%Y%m%d-%H%M%S)"
  NEW_BRANCH="codex/${spec_slug}-${MODE}-${TS}"
  git checkout -b "$NEW_BRANCH"
  echo "Checked out new branch: $NEW_BRANCH"
fi

OUT_LAST="progress/last_message.txt"
LOG="progress/codex.log"

# Run header for traceability.
echo "=== Run started: $(date -Iseconds) mode=$MODE model=$MODEL ===" | tee -a "$LOG"

FLAGS=(
  exec
  --model "$MODEL"
  --sandbox danger-full-access
  --output-last-message "$OUT_LAST"
)

_changed_between_commits() {
  local before="$1"
  local after="$2"
  if [[ "$before" == "$after" ]]; then
    return 0
  fi
  git diff --name-only "$before..$after"
}

_changed_in_worktree() {
  {
    git diff --name-only HEAD
    git diff --name-only --cached HEAD
  } | awk 'NF' | sort -u
}

for ((i=1; i<=MAX_ITERS; i++)); do
  echo "=== Ralph iteration $i/$MAX_ITERS ($MODE) @ $(date -Iseconds) ===" | tee -a "$LOG"

  BEFORE_HEAD="$(git rev-parse HEAD)"

  # Capture pre-run tail for append-to-end enforcement.
  BEFORE_PROGRESS_TAIL=""
  if [[ -f "progress/progress.txt" ]]; then
    BEFORE_PROGRESS_TAIL="$(tail -n 40 progress/progress.txt || true)"
  fi

  # Capture stdout + stderr into the log.
  codex "${FLAGS[@]}" - < "$PROMPT_FILE" 2>&1 | tee -a "$LOG"

  AFTER_HEAD="$(git rev-parse HEAD)"

  # Stop markers / blocked marker from last message file.
  TERMINAL_MARKER="false"
  BLOCKED_MARKER="false"
  if [[ -f "$OUT_LAST" ]]; then
    if grep -Eq "ALL_DONE|PLAN_DONE|SPEC_DONE" "$OUT_LAST"; then
      TERMINAL_MARKER="true"
    fi
    if grep -Eq "^ITERATION_BLOCKED\b" "$OUT_LAST"; then
      BLOCKED_MARKER="true"
    fi
  fi

  # Collect changes committed during the run and/or left in working tree.
  COMMITTED_CHANGED="$(_changed_between_commits "$BEFORE_HEAD" "$AFTER_HEAD" | awk 'NF' | sort -u)"
  WORKTREE_CHANGED="$(_changed_in_worktree)"

  # Combined changed set.
  CHANGED_ALL="$(printf "%s\n%s\n" "$COMMITTED_CHANGED" "$WORKTREE_CHANGED" | awk 'NF' | sort -u)"

  # Enforcement: if blocked, forbid spec/plan completion changes.
  if [[ "$BLOCKED_MARKER" == "true" ]]; then
    if printf "%s\n" "$CHANGED_ALL" | grep -qE '^(specs/.*\.json|IMPLEMENTATION_PLAN\.md)$'; then
      echo "ERROR: ITERATION_BLOCKED but specs/*.json or IMPLEMENTATION_PLAN.md changed. Revert those changes." | tee -a "$LOG"
      exit 1
    fi
  fi

  # Enforcement: if any spec JSON changed, require progress/progress.txt also changed.
  if printf "%s\n" "$CHANGED_ALL" | grep -qE '^specs/.*\.json$'; then
    if ! printf "%s\n" "$CHANGED_ALL" | grep -qx 'progress/progress.txt'; then
      echo "ERROR: Spec changed but progress/progress.txt did not change. Refusing run." | tee -a "$LOG"
      exit 1
    fi
  fi

  # Enforcement: if anything changed and not blocked, progress/progress.txt must change.
  if [[ "$BLOCKED_MARKER" != "true" ]]; then
    if [[ -n "$CHANGED_ALL" ]]; then
      if ! printf "%s\n" "$CHANGED_ALL" | grep -qx 'progress/progress.txt'; then
        echo "ERROR: Repo changed but progress/progress.txt did not change. Every non-blocked iteration must append a progress entry at EOF." | tee -a "$LOG"
        exit 1
      fi
    fi
  fi

  # Enforcement: if progress/progress.txt changed, its EOF tail must change.
  if printf "%s\n" "$CHANGED_ALL" | grep -qx 'progress/progress.txt'; then
    AFTER_PROGRESS_TAIL="$(tail -n 40 progress/progress.txt || true)"
    if [[ -n "$BEFORE_PROGRESS_TAIL" && "$AFTER_PROGRESS_TAIL" == "$BEFORE_PROGRESS_TAIL" ]]; then
      echo "ERROR: progress/progress.txt changed but end-of-file tail did not change. Progress entries must be appended at EOF." | tee -a "$LOG"
      exit 1
    fi
  fi

  # Stop if Codex reports a terminal marker in the last message file.
  if [[ "$TERMINAL_MARKER" == "true" ]]; then
    echo "Terminal marker detected. Exiting." | tee -a "$LOG"
    exit 0
  fi

  # Stop to avoid spinning if the working tree is clean.
  # This may still have created commits; that is fine.
  if [[ -z "$(git status --porcelain)" ]]; then
    echo "No working tree changes detected; stopping." | tee -a "$LOG"
    exit 0
  fi
done

echo "Reached MAX_ITERS=$MAX_ITERS. Review commits and run again if needed." | tee -a "$LOG"
exit 0
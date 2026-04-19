# Progress Log Append Rule

When a Ralph harness run modifies `progress/progress.txt`, the new iteration entry must be appended to the absolute end of the file.

The newest entry must be the final content in the file.

Do not insert a new progress entry above older entries.

Do not keep a footer after the newest entry.

If this rule is violated, the harness may fail with an error similar to:

```text
ERROR: progress/progress.txt changed but end-of-file tail did not change.
Progress entries must be appended at EOF.
```

This rule applies to all modes:

```bash
./scripts/ralph-loop.sh spec_author 1
./scripts/ralph-loop.sh plan 1
./scripts/ralph-loop.sh build 1
```

A non-blocked run that changes files must append a progress entry.

A blocked run must append a blocker entry, but must not mark spec items complete.

Every progress entry should include enough context for a later run to rehydrate what happened without relying on memory:

- date/time with timezone
- mode
- active spec
- selected item if applicable
- repo search summary
- files changed
- tests or checks run
- blockers if any
- next recommended command or item
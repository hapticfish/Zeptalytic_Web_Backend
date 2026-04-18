# Rewards Application and Notification Flows

## Purpose

Define application behavior for rewards, objectives, badges, milestones, points, and notification presentation.

The rewards database schema is assumed to exist. This document controls the application layer.

## Core model concepts

The backend docs and specs must distinguish:

- reward definition
- reward grant
- reward event
- badge definition
- badge award/account badge
- objective definition
- objective completion/progress
- milestone unlock
- notification presentation state

## Core decisions

- One global points balance per user.
- Points do not expire.
- Frontend reward APIs are mostly read-only.
- Reward writes originate from backend jobs, admin/internal operations, Pay-derived events, product-originated events, and referral qualification events.
- Do not award points/rewards before qualification criteria are met.
- Reversal logic is not required in phase 1 because rewards should be granted only after conditions are satisfied.
- Product apps may later emit reward-relevant events through a shared ingestion interface.

## Rewards page data

Rewards page needs:

- total points
- reward tier
- current milestone
- points to next milestone
- active perks
- next milestone details
- objective progress list
- badge/reward gallery
- collected/earned rewards
- milestone notification state

## Objectives page data

Objectives page needs:

- total points
- reward tier
- all available objectives
- objective descriptions
- objective completion status
- staged progress if applicable
- percent progress
- recent objective activity
- tier status
- unviewed completion notification queue

## Progress computation

Progress should be computed from trusted backend records, not frontend assumptions.

Sources may include:

- account points balance
- account objective progress
- reward events
- reward grants
- account badges
- milestone definitions
- objective definitions

## Event triggers

Reward/objective writes may be triggered by:

- referral qualification
- product feature usage confirmation
- subscription state reaching a required condition
- completed product onboarding milestone
- admin grant/internal operation
- product-originated event
- Pay-derived projection/event after required commercial criteria are met

Example:

A referral reward should not be granted until the referred user satisfies the required duration/criteria, such as remaining subscribed for the required threshold.

## Shared reward event ingestion

Plan for a shared ingestion interface so products can later emit reward-relevant events.

Recommended conceptual flow:

```text
Product/backend event
  -> parent reward event ingestion endpoint or internal worker
  -> validate source/auth
  -> normalize event
  -> match objective definitions
  -> update objective progress
  -> grant rewards/points/badges if criteria met
  -> create notification presentation record
```

## Milestone behavior

Milestones are objectives, not disconnected UI decorations.

Milestone rewards are automatically modal-driven when the user visits a page with the progress bar.

Expected frontend flow:

1. Progress bar loads.
2. Progress bar animates to current points.
3. If a new milestone unlock is unviewed, animation and modal can trigger.
4. User views/closes milestone notification.
5. Backend marks notification viewed.

## Non-milestone objective completion behavior

Non-milestone completions do not automatically interrupt every page.

Expected flow:

1. Backend records objective completion.
2. Backend queues unviewed objective/reward notification.
3. Frontend notification indicates user should visit objectives page.
4. Objectives page presents completion modals in order.
5. User can cycle through or skip all.
6. Backend records viewed/skipped state.

## Viewed/unviewed notification state

Use explicit notification presentation state rather than relying only on reward events.

Recommended model concept:

- `notification_subject_type`: milestone_unlock, objective_completion, reward_grant, badge_award
- `notification_subject_id`
- `account_id`
- `viewed_at`
- `skipped_at`
- `created_at`
- `presentation_context`: progress_bar, objectives_page, rewards_page if needed

Examples:

### Per reward event

A reward event creates one notification. Useful when every event maps directly to one notification.

### Per objective completion

An objective completion creates a notification even if it grants multiple things. Useful for objectives page flow.

### Per milestone

A milestone unlock creates a progress-bar notification. Useful for milestone modals.

Recommended approach:

Use a presentation notification record that can reference the subject type. This avoids forcing all notifications into only one table/concept.

## Objective completion ordering

When multiple objective completions are unviewed, present in deterministic order:

1. completion time ascending
2. milestone notifications before non-milestone if shown on progress bar
3. objective priority if configured
4. stable ID tie-breaker

## Badge unlock rules

Badge unlocks should come from objective/reward logic or product/admin events.

Badge gallery should distinguish:

- earned/collected badges
- locked but visible badges
- hidden/secret badges if configured later

## Reward grants

Reward grants represent the account receiving a reward.

Reward definitions represent what can be granted.

Reward events represent the historical event that caused progress/grant/activity.

## Frontend API writes

Allowed frontend writes:

- mark notification viewed
- skip notification(s)
- claim manual reward if a reward is explicitly manual-claim later

Not allowed frontend writes:

- directly add points
- directly complete objective
- directly award badge
- directly create reward event

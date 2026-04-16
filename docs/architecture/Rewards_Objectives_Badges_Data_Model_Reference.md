# Rewards, Objectives, and Badges Data Model Reference

## Purpose
Provide the reference data-model direction for the rewards/objectives/badges domain before implementation specs are written.

This is a design-reference document, not the final migration spec.

## Core domain requirements
The model must support:
- one global points balance per account
- tier progression across Bronze, Silver, Gold, Platinum, Plus
- milestone rewards every 100 points
- larger rewards every 1000 points
- objectives that can be global or product-specific
- objective gating by tier and/or subscription level
- repeatable objectives
- reward grants that may be automatic or manual-claim depending on type
- reward and point reversals in some scenarios
- badges and obtained rewards tracking
- modal/notification sequencing for newly completed objectives and milestones

## Recommended domain tables

### 1. `reward_accounts`
Current reward snapshot per account.

Recommended fields:
- `account_id` (PK/FK)
- `current_points`
- `current_tier`
- `current_tier_progress_points`
- `next_milestone_points`
- `last_recomputed_at`
- `created_at`
- `updated_at`

Purpose:
- fast read for rewards page and dashboard summary
- current tier/progress snapshot

## 2. `reward_events`
Append-only ledger of points/reward-affecting events.

Recommended fields:
- `id`
- `account_id`
- `event_type`
- `points_delta`
- `objective_definition_id` nullable
- `reward_definition_id` nullable
- `badge_definition_id` nullable
- `source_type`
- `source_reference`
- `is_reversal`
- `reversed_event_id` nullable
- `status`
- `metadata`
- `created_at`

Purpose:
- auditability
- reversal traceability
- rebuild current points if needed

## 3. `reward_tier_definitions`
Locked tier definitions.

Recommended fields:
- `id`
- `tier_code`
- `display_name`
- `sort_order`
- `tier_start_points`
- `tier_end_points`
- `created_at`
- `updated_at`

Locked intended tiers:
- BRONZE
- SILVER
- GOLD
- PLATINUM
- PLUS

Each tier spans 1000 points.

## 4. `reward_milestones`
Milestone definitions for the progress bar.

Recommended fields:
- `id`
- `milestone_points`
- `tier_code`
- `is_tier_boundary`
- `linked_objective_definition_id`
- `sort_order`
- `created_at`
- `updated_at`

Purpose:
- every 100-point milestone
- tier-boundary reward at each 1000-point threshold
- preserves the rule that milestones are also objectives

## 5. `reward_definitions`
Catalog of reward payloads.

Recommended fields:
- `id`
- `reward_code`
- `reward_type`
- `display_name`
- `description`
- `is_repeatable`
- `is_revocable`
- `grant_mode`
- `metadata`
- `created_at`
- `updated_at`

Example reward types may include:
- points
- nft
- discount
- feature_access
- cosmetic
- discord_icon
- milestone_reward

## 6. `reward_grants`
Actual granted rewards per account.

Recommended fields:
- `id`
- `account_id`
- `reward_definition_id`
- `source_objective_definition_id` nullable
- `source_reward_event_id` nullable
- `status`
- `granted_at`
- `revoked_at` nullable
- `revocation_reason` nullable
- `metadata`

Purpose:
- track whether a reward was actually granted
- support reversals/revocations

## 7. `objective_definitions`
Catalog of objectives.

Recommended fields:
- `id`
- `objective_code`
- `title`
- `description`
- `scope_type`
- `product_code` nullable
- `objective_type`
- `is_repeatable`
- `repeat_group_key` nullable
- `required_count`
- `tier_gate` nullable
- `subscription_gate_product_code` nullable
- `subscription_gate_plan_code` nullable
- `is_milestone_objective`
- `sort_group`
- `sort_order`
- `active`
- `metadata`
- `created_at`
- `updated_at`

Purpose:
- supports both global and product-specific objectives
- supports milestones as objectives
- supports objectives tied to subscription levels
- supports repeatable referral-style objectives

## 8. `objective_reward_links`
Links one objective to one or more rewards.

Recommended fields:
- `id`
- `objective_definition_id`
- `reward_definition_id`
- `grant_order`
- `created_at`

Purpose:
- objectives may grant multiple reward payloads

## 9. `account_objective_progress`
Current progress state per account/objective.

Recommended fields:
- `id`
- `account_id`
- `objective_definition_id`
- `current_count`
- `completed_count`
- `last_completed_at` nullable
- `last_progress_at` nullable
- `repeat_iteration` nullable
- `status`
- `metadata`
- `created_at`
- `updated_at`

Purpose:
- tracks progress bars and completion state
- supports repeatable objectives
- supports structured display on objectives page

## 10. `badge_definitions`
Catalog of badges/earned display achievements.

Recommended fields:
- `id`
- `badge_code`
- `display_name`
- `description`
- `icon_ref`
- `is_revocable`
- `metadata`
- `created_at`
- `updated_at`

## 11. `account_badges`
Badges earned by an account.

Recommended fields:
- `id`
- `account_id`
- `badge_definition_id`
- `earned_at`
- `revoked_at` nullable
- `revocation_reason` nullable
- `source_objective_definition_id` nullable
- `source_reward_event_id` nullable
- `metadata`

Purpose:
- powers rewards gallery / achieved-badge display

## 12. `reward_notifications`
Tracks what reward/objective/milestone completion items have been surfaced to the user.

Recommended fields:
- `id`
- `account_id`
- `notification_type`
- `objective_definition_id` nullable
- `reward_grant_id` nullable
- `badge_definition_id` nullable
- `reward_event_id` nullable
- `status`
- `queued_at`
- `seen_at` nullable
- `dismissed_at` nullable
- `sequence_order`
- `metadata`

Purpose:
- supports “completed since last viewed” sequencing
- supports skip-all behavior
- supports ordered presentation on objectives page

## Modeling rules implied by the business decisions

### Global points
Use `reward_events.points_delta` as the durable source and `reward_accounts.current_points` as the fast snapshot.

### Tier computation
Tier can be computed from total points, but should also be stored in `reward_accounts.current_tier` for fast reads.

### Milestones as objectives
Each milestone should link to an objective definition rather than be implemented as a disconnected UI-only concept.

### Repeatable objectives
Use `objective_definitions.is_repeatable` plus `account_objective_progress.repeat_iteration` and `completed_count` to support repeated referral-type objectives.

### Reversals
Reversals should be modeled as explicit negative or reversing events linked back to the original event where possible.

### Automatic vs manual reward presentation
Milestone completion can queue immediate presentation entries in `reward_notifications`, while non-milestone completions can create notification records to be consumed on the objectives page.

## Suggested vocabularies to formalize later
Future specs should lock exact vocabularies for:
- `reward_event.event_type`
- `reward_event.status`
- `reward_definition.reward_type`
- `reward_definition.grant_mode`
- `objective_definition.scope_type`
- `objective_definition.objective_type`
- `account_objective_progress.status`
- `reward_notifications.notification_type`
- `reward_notifications.status`

## Intentionally deferred details
These should be resolved in later specs rather than assumed here:
- exact referral repeat tiers and reward payloads
- precise reward reversal retention window values
- exact objective sorting/grouping taxonomy for UI
- whether some rewards require explicit manual claim steps in v1
- whether some badges are automatically granted vs linked through reward definitions

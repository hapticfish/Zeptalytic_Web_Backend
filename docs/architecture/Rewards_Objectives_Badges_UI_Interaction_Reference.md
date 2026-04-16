# Rewards, Objectives, and Badges UI Interaction Reference

## Purpose
Translate the current rewards-domain business rules into UI-facing behavior that future API/application specs can implement without losing the intended UX.

## Page split

### Rewards page
This page is the summary-oriented experience.

It should show:
- current points
- current tier
- current progress within the current 1000-point tier band
- active perks / unlocked items summary
- next milestone summary
- rewards gallery / achieved rewards summary
- milestone-focused overview state

### Objectives page
This page is the detailed organized objective surface.

It should show:
- all relevant objectives
- grouped/ordered objective structure
- objective progress state
- objective descriptions
- rewards tied to each objective
- how to complete each objective
- completion presentation flow for newly achieved objectives

## Progress bar behavior
The progress bar represents movement through the user’s current tier band.

Locked behavior:
- each tier spans 1000 points
- milestones occur every 100 points
- each 1000-point threshold is a tier-boundary milestone with a larger reward
- milestones on the progress bar are also objectives in the objectives page

## Milestone presentation behavior
When a milestone is reached and the user views a page that contains the progress bar:
- the progress bar animates from the prior visible progress to the current progress
- celebratory animation may include confetti, stars, or similar effects
- the background slightly darkens to focus the user on the achievement
- a modal presents the milestone and reward

This automatic modal behavior is specific to milestone progress-bar achievements.

## Non-milestone objective completion behavior
When a non-milestone objective is completed:
- the user should receive a notification encouraging them to visit the objectives page
- the objectives page then handles the focused modal sequence for newly completed items

If multiple objective completions have accumulated since the last objectives-page visit:
- present them in order
- allow the user to step through them
- allow the user to skip all pending reward notifications
- allow the user to close/cycle through them until all are processed

## Modal controls
The completion modal flow should support:
- close / next behavior
- click-off behavior to advance/dismiss as designed
- `Skip all reward notifications` control to bypass the remaining queue

The skip-all control should sit to the left of the close (`X`) button in the upper-right modal area, per the current intended UX direction.

## Objective organization requirements
Objectives must be presented in a way that keeps the following categories understandable:
- progress-tier / milestone objectives
- objectives specific to certain subscription levels
- product-specific objectives
- global objectives
- repeatable objectives such as referrals

The exact grouping taxonomy can be locked later, but the UI/application model must preserve enough metadata to support structured grouping instead of one flat unsorted list.

## Rewards page vs objectives page rule
This is the key rule:
- rewards page = summary
- objectives page = structured detailed objective and reward workflow

Do not collapse these into one generic screen in later specs.

## Reward/achievement visibility requirements
The system should be able to show:
- current tier
- current points
- next milestone
- objective progress bars / counters
- related rewards for each objective
- achieved rewards / badges gallery
- active perks summary

## Repeatable-objective UX implications
Because some objectives are repeatable:
- the UI must support repeated completion cycles
- the objective presentation should make it clear whether an objective can be repeated
- the progress UI should distinguish between “completed once” and “current repeat cycle progress” where relevant

## Reversal UX implications
Because points and some rewards can be reversed:
- the system should not assume every granted reward is permanently retained
- UI copy later may need to explain retention windows or reversal conditions for some reward types
- badge/reward display logic should allow a reward to become unavailable again if the business rules require revocation

## Frontend-to-backend implications
Future backend APIs must support enough information for the frontend to render:
- current reward summary snapshot
- milestone definitions and current next milestone
- ordered objective groups
- per-objective progress counts
- per-objective reward payloads
- queue of newly completed-but-unviewed achievements
- badge/reward gallery data
- active perks summary

## Out of scope for this reference
- exact component names
- exact API route names
- exact animation library choices
- exact notification transport implementation

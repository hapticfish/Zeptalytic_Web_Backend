# Rewards, Objectives, and Badges Domain Decision Record

## Status
Accepted with explicitly deferred sub-rules where noted.

## Purpose
Define the core business rules for the Zeptalytic rewards domain so future schema, API, UI, and test specs use one shared interpretation.

## Domain summary
The rewards domain is centered on a **global points balance per user**, a **tiered progress bar**, a structured **objectives system**, and user-visible **rewards, badges, and milestone unlocks**.

The rewards page is a summary-oriented experience, while the objectives page is the structured detail surface for objective progress, objective requirements, and related rewards.

## Locked decisions

### Global points model
- Each user has **one global points value** across the Zeptalytic ecosystem.
- Points contribute to the progress bar and tier progression.
- Points are applied **immediately** when the objective or milestone is achieved.
- Points do **not expire**.

### Tier model
The locked tier sequence is:
- `BRONZE`
- `SILVER`
- `GOLD`
- `PLATINUM`
- `PLUS`

Each tier spans **1000 points**.

### Milestone model
- There is a milestone every **100 points** on the progress bar.
- Every **1000 points** triggers a larger reward at the tier boundary.
- Progress-bar milestones are also objectives represented on the objectives page.

### Objective scope
Objectives may be:
- global
- product-specific

Objectives may also be gated by:
- tier
- subscription level

### Rewards sources
Rewards are mainly tied to:
- objective completion
- feature usage
- subscription upgrades / qualifying subscription actions
- referrals
- Discord/community engagement
- milestone progression on the points bar

### Reward types currently intended
Examples of rewards may include:
- points
- NFTs
- Discord-related profile icons
- discounts
- limited usage of higher-tier features
- milestone rewards

### Objective repeatability
- Some objectives are repeatable.
- Example: referral objectives have multiple reward tiers.
- The third referral tier is repeatable.
- The repeated version of the third tier should grant the same number of points, but the non-point reward is still being refined.

### Automatic vs non-automatic reward presentation
- Only milestone rewards tied to progress-bar progression should auto-present as milestone popups when triggered through progress-bar viewing behavior.
- Other objective-completion rewards should not immediately force the same auto-popup flow everywhere. Instead, they should notify the user to visit the objectives page, where the achievement presentation sequence occurs.

### Reversal behavior
Points and rewards can be reversed in some cases.

Example locked rule direction:
- If points/rewards are granted for upgrading to another subscription tier and the user does not remain past the qualifying retention window (for example, beyond the refund window / 30-day threshold once finalized), then points are reversed and rewards are removed if possible.

The exact retention-window constants remain implementation-detail inputs that later specs should make configurable.

## Deferred-but-recognized decisions
These are intentionally not fully locked yet and should remain open in future specs unless John later finalizes them:
- the exact repeatable referral reward payload after first redemption vs later repetitions
- the exact reversal window constant for billing-related rewards
- the full catalog of reward types
- all product-specific objective families
- the complete objective gating matrix by tier and subscription plan

## Page behavior decisions

### Rewards page
The rewards page acts as a summary surface that shows current progress, major reward state, and milestone-oriented overview information.

### Objectives page
The objectives page is the detailed structured surface for:
- all objectives
- objective progress
- objective descriptions
- related rewards
- how to obtain those rewards
- milestone/objective completion presentation flow

### Important linkage rule
Milestones on the progress bar are objectives in the objectives page.

That means milestone definitions and objective definitions must be linked or represented in a way that preserves this relationship instead of treating them as unrelated systems.

## Notification and modal behavior

### Milestone completion flow
When a milestone is triggered through progress-bar advancement:
- the user visits/views a page with the progress bar
- the progress bar animates to the new progress value
- a milestone/reward presentation appears
- the UI darkens the screen slightly to focus attention
- milestone-specific animation may include confetti, stars, or similar celebratory effects
- a modal presents the milestone and its reward

### Objective completion flow (non-milestone)
For other objectives:
- a notification prompts the user to visit the objectives page
- on the objectives page, the completion/reward modal sequence is shown
- if multiple objectives were completed since the last objectives-page visit, they are presented in order until all are viewed
- the user can skip them using a `Skip all reward notifications` action
- the user may also cycle/close them sequentially until all are seen

## Data-shape implications
Future DB/API work must support:
- one global points ledger and current balance per account
- current tier per account
- objective definitions with scope/gating
- account-level objective progress
- milestone definitions
- rewards definitions and grants
- badges/earned achievements
- reversible reward events where allowed
- event history/auditability for reward changes
- state that supports “completed since last viewed” presentation sequencing

## Recommended implementation principle
Use event history plus current-state tables where practical:
- append-only reward/points events for auditability
- current snapshot tables for fast UI reads

## Out of scope for this decision record
- exact DB table names
- exact API endpoint names
- frontend implementation details for animation libraries
- exact referral reward math for repeated redemptions
- NFT minting/distribution implementation

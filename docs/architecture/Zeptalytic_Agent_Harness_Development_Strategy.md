# Zeptalytic Agent Harness Development Strategy

## Purpose
This document explains how the Zeptalytic parent-site work should be structured for Ralph/Codex agent-guided development so the implementation remains spec-driven, traceable, and aligned with the controlling architecture decisions.

## Recommended repository doc layout
Place reference docs in a stable repo path such as:

- `docs/architecture/Zeptalytic_Website_Implementation_Control_Plan.md`
- `docs/architecture/Zeptalytic_Feature_Ownership_Register.md`
- `docs/architecture/Zeptalytic_Parent_vs_Pay_Data_Ownership_Matrix.md`
- `docs/architecture/Zeptalytic_Parent_DB_Schema_Plan.md`  *(to be created next)*
- `docs/architecture/Zeptalytic_Pay_Integration_Contract.md`  *(later)*
- `docs/architecture/Zeptalytic_UI_to_API_Matrix.md`  *(later)*

This makes them easy for agent specs to cite explicitly.

## Recommended development split
Do not attempt one giant all-at-once spec. Split the work into logical specs and branches.

Recommended spec order:
1. parent DB foundation
2. parent auth/profile/settings
3. parent support + attachments
4. parent Pay integration read models
5. pricing + checkout
6. billing page
7. dashboard + launcher
8. rewards
9. content/testimonials
10. hardening + tests

## Recommended spec files
Example spec file names:
- `specs/parent_db_foundation.json`
- `specs/parent_auth_profile_settings.json`
- `specs/parent_support_attachments.json`
- `specs/parent_pay_integration_read_models.json`
- `specs/parent_pricing_checkout.json`
- `specs/parent_billing.json`
- `specs/parent_dashboard_launcher.json`
- `specs/parent_rewards.json`
- `specs/parent_content_testimonials.json`
- `specs/parent_hardening_tests.json`

## Branch strategy
Use separate work branches for major workstreams when helpful, but keep them aligned to the same architecture docs.

Suggested branch naming:
- `ralph/parent-db-foundation-<timestamp>`
- `ralph/parent-auth-profile-<timestamp>`
- `ralph/parent-support-<timestamp>`
- `ralph/parent-pay-read-models-<timestamp>`
- `ralph/parent-billing-<timestamp>`

## What each spec should explicitly reference
Every parent-site spec should instruct the agent to consult:
1. the implementation control plan
2. the feature ownership register
3. the parent vs Pay ownership matrix
4. any current schema plan relevant to that work
5. any existing frontend inventory notes relevant to the feature

## Suggested instruction pattern for specs
Each spec should include language equivalent to:

- treat Pay as source of truth for pricing, checkout, orders, payments, refunds, subscriptions, entitlements, disputes, risk, and billing-commercial logic
- do not duplicate billing truth in parent DB
- parent backend is the only browser-facing API
- payment method handling uses Stripe.js / Elements + SetupIntents so parent systems do not receive raw card details
- Coinbase is a checkout rail, not a Stripe-like saved-card subsystem
- consult the ownership and control docs before changing models or routes
- update progress/progress.txt with the specific artifact changes and rationale

## How to keep runs effective
A spec should be narrow enough that:
- one domain is improved at a time
- the agent can validate progress with real diffs and tests
- the agent does not need to infer architecture from scratch

Good examples:
- "Create accounts/auth/security tables and migrations only"
- "Implement settings/profile endpoints and tests only"
- "Add support ticket tables, secure attachment metadata model, and API routes only"

Poor examples:
- "Build the whole website backend"

## What to keep out of early specs
Do not combine these too early:
- auth + billing + rewards in one spec
- support + pricing + launcher in one spec
- Pay promo design + parent settings + dashboard in one spec

## Spec completion rules
A spec should not be marked done unless:
- schema and/or API changes match the controlling docs
- migrations apply
- tests for the touched area exist and pass
- no conflicting ownership boundaries were violated
- progress log explains what changed and what remains

## Recommended next artifact after these docs
Create:
- `docs/architecture/Zeptalytic_Parent_DB_Schema_Plan.md`

That document should convert the approved parent-owned domains into:
- exact tables
- keys
- indexes
- relationships
- migration order
- launch-critical vs later-phase tables

## How to use these docs during implementation
The most effective pattern is:
- keep these docs as stable architecture references in the repo
- make each spec explicitly point to the specific docs it must consult
- keep the actual work instructions in the spec narrow and domain-specific
- do not overload the spec with all architecture content inline when a stable reference doc exists

This keeps the harness cleaner and reduces repetition while preserving consistency.

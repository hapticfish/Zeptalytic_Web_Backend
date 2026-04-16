# Discord and Rewards Workstream Sequence

## Purpose
This document explains the next post-parent-DB workstream sequence for the Zeptalytic Web Backend.

## Why this is split
Discord identity correction and rewards/objectives/badges implementation are related to the parent account domain, but they are not the same complexity level.

The Discord correction is a small corrective schema/data-shape slice:
- place current active Discord linkage on `profiles`
- preserve historical connection state separately
- verify migration/model/test coverage

The rewards/objectives/badges work is a larger business domain and should be implemented as its own staged sequence:
1. domain DB schema
2. verification/regression hardening
3. API/application layer

## Sequence
### 1. `specs/discord_identity_schema_correction.json`
Small corrective spec.
Goal:
- add/align `profiles.discord_user_id`
- add/align `profiles.discord_username`
- add/align `profiles.discord_integration_status`
- add a separate history table for preserved connection/disconnection records
- verify metadata/migrations/tests

### 2. `specs/rewards_domain_db_schema.json`
Domain DB buildout.
Goal:
- create the rewards/objectives/badges/points/progress tables
- encode the currently locked vocabulary and milestone/tier rules
- keep the model layout per-file and domain-organized

### 3. `specs/rewards_verification_and_regression.json`
Regression hardening.
Goal:
- verify migrations, metadata registration, constraints, indexes, and core repository/DB behavior
- verify progression, reversal, repeatable objective, and notification queue data behavior

### 4. `specs/rewards_api_application_layer.json`
Parent backend API/application layer.
Goal:
- implement the parent-owned service/router/schema behavior needed for rewards summary, objectives detail, progression queue handling, and reward claim/notification flows

## Switch rule
The harness reads the active spec from `IMPLEMENTATION_PLAN.md`. After each workstream is fully green, switch the `Active spec:` line to the next spec in sequence before starting the next run cycle.

## Architecture dependencies
These specs depend on:
- `Discord_Integration_Decision_Record.md`
- `Rewards_Objectives_Badges_Domain_Decision_Record.md`
- `Rewards_Objectives_Badges_Data_Model_Reference.md`
- `Rewards_Objectives_Badges_UI_Interaction_Reference.md`

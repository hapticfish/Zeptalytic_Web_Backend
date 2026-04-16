# Discord Integration Decision Record

## Status
Accepted

## Purpose
Define how Discord identity should be represented in the parent-site backend so the frontend settings/integrations area, login/integration behavior, and future ZardBot-related Discord features all use one stable model.

## Locked decisions
- Each Zeptalytic account may have **at most one currently connected Discord account**.
- The **Discord user ID is the canonical Discord identifier**.
- The **Discord username is stored for display**.
- The Discord user ID is **internal only** and is not shown in the settings UI.
- The settings/integrations UI should show:
  - Discord connected/disconnected status
  - Discord username when connected
- Connect/disconnect timestamps are **not required in the UI**.
- Historical connection records should be preserved and marked disconnected rather than fully deleted.
- No additional Discord profile attributes are required right now beyond:
  - Discord user ID
  - Discord username
- Discord is used for:
  - login/integration behavior
  - future ZardBot-related functionality

## Current-state modeling decision
The current active Discord linkage should live directly on `profiles` for simple reads.

Recommended current-state fields on `profiles`:
- `discord_user_id`
- `discord_username`
- `discord_integration_status`

This keeps the most common account/settings reads simple and avoids requiring history-table joins for normal profile rendering.

## Historical-record decision
Historical connect/disconnect state should be preserved in a dedicated history table rather than overloaded into `profiles`.

Recommended history table:
- `discord_connection_history`

Recommended fields:
- `id`
- `account_id`
- `discord_user_id`
- `discord_username`
- `status`
- `created_at`
- `updated_at`

This table exists for audit/history needs, while `profiles` remains the easy source for the currently active linkage.

## Vocabulary guidance
Recommended Discord integration status vocabulary:
- `connected`
- `disconnected`
- `error`
- `pending`

These values should align with the canonical vocabulary decision record already locked for integrations.

## Why Discord user ID belongs on `profiles`
The active Discord identity is effectively part of the account profile/integration state, not just an audit record. Putting it on `profiles` is appropriate because:
- one current Discord account per Zeptalytic account is allowed
- the frontend settings page needs fast access to connection state and username
- the Discord user ID is stable while usernames may change
- the history requirement can be handled separately without complicating current-state reads

## What is intentionally out of scope right now
- storing Discord avatar URL
- storing Discord global display name separately
- guild membership snapshots
- Discord token storage details in this decision record
- role-sync implementation details
- ZardBot-specific Discord feature behavior

## Implementation notes for future specs
Future schema/API specs should:
- enforce one active Discord account per Zeptalytic account
- update `profiles` as the current active linkage source
- preserve historical state changes in `discord_connection_history`
- avoid exposing `discord_user_id` in frontend-facing responses unless explicitly needed for internal/admin surfaces

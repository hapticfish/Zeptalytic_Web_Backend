# Discord Integration Application Flow

## Purpose

Define first-phase Discord integration behavior for the parent backend.

## Scope

Discord integration is mostly a settings/profile linkage and signup capture flow for phase 1.

Discord linkage does not influence:

- rewards
- product access
- launcher eligibility
- subscription eligibility

Historical linkage is internal only.

## Data visibility

User-facing UI may show:

- Discord connected/not connected status
- Discord username

Internal only:

- Discord user ID
- historical linkage records
- connect/disconnect timestamps unless later approved
- OAuth tokens/secrets if any are used

## Signup OAuth flow

Expected conceptual flow:

1. User clicks connect Discord account during signup or settings.
2. User is redirected/presented with Discord authorization.
3. Discord shows the authorization consent screen.
4. User authorizes the Zeptalytic app.
5. Discord redirects back to parent backend/frontend callback.
6. Backend exchanges code for Discord identity data where applicable.
7. Backend stores Discord username and internal Discord user ID.
8. Registration/settings UI displays the connected Discord username.

## Settings flow

Settings integrations card should show:

- Discord integration status
- connected/not connected
- Discord username when connected
- connect action when disconnected
- future integrations placeholder

## Historical state

Historical Discord connection state should be preserved in a separate history table.

One parent account may have at most one currently connected Discord account.

If a different Discord account is linked later, it should update current linkage and preserve prior linkage history.

## Security controls

- Validate OAuth state parameter.
- Protect against CSRF in OAuth flow.
- Do not expose Discord user ID in normal frontend responses.
- Store only required Discord data.
- Do not store long-lived Discord tokens unless there is a clear feature need.
- If tokens are stored, encrypt them and document rotation/expiry handling.

## Not in scope

- Discord-based rewards
- Discord-based product access
- Discord notification delivery
- Discord bot management from parent dashboard
- user-facing historical linkage timeline

# Zeptalytic Web Backend — Next Phase Architecture Bundle

## Purpose

This bundle contains architecture/control documents for the next implementation phase of the Zeptalytic Web Backend.

The database foundation and rewards schema work are assumed to be complete. The next phase is to build the application layer that makes the Zeptalytic parent site functional:

- repository/data-access layer
- service/business-logic layer
- API router and request/response contract layer
- parent-to-Pay integration layer
- dashboard/launcher/billing aggregation
- rewards/objectives/badges application behavior
- support/announcements/status behavior
- auth/session/security flows
- frontend/backend contract alignment

## Important framing

The Zeptalytic Web Backend is the parent-site domain backend. It owns account, profile, settings, support, announcements/status, rewards, launcher state, and frontend aggregation behavior.

The Zeptalytic Pay service remains the source of truth for commercial/payment truth: checkout, orders, payments, refunds, subscriptions, entitlements, disputes, risk, and payment-provider interaction.

The parent backend may initiate commercial actions such as checkout, plan change, pause/cancel, or restart, but those actions must be handed off to Pay. Parent must not duplicate Stripe/Coinbase/payment business rules.

## How to use these docs

Place the markdown files under:

```text
docs/architecture/
```

Use `specs/next_phase_spec_sequence.json` as the planning source for the next set of Ralph harness specs.

Recommended process:

1. Commit these docs first.
2. Add the next active spec from the sequence to `IMPLEMENTATION_PLAN.md`.
3. Run `./scripts/ralph-loop.sh plan 1`.
4. Review the generated plan.
5. Run `./scripts/ralph-loop.sh build 1`.
6. Require the authoritative Docker suite before marking each spec item complete.

## Included docs

- `Parent_Backend_Application_Architecture.md`
- `Parent_Backend_API_Contract_Standards.md`
- `Parent_Backend_Repository_Layer_Design.md`
- `Parent_Backend_Service_Layer_Design.md`
- `Parent_Pay_Integration_and_Projection_Strategy.md`
- `Frontend_Backend_Contract_Map.md`
- `Auth_Session_and_Security_Flows.md`
- `Dashboard_Launcher_Billing_Aggregation_Design.md`
- `Support_Announcements_and_Status_Design.md`
- `Rewards_Application_and_Notification_Flows.md`
- `Discord_Integration_Application_Flow.md`
- `Background_Jobs_Sync_and_Event_Processing.md`
- `Security_Operational_Control_Guide.md`
- `Agent_Non_Goals_and_Implementation_Guardrails.md`

## Included spec roadmap

- `specs/next_phase_spec_sequence.json`

This is not intended to be the final full implementation spec. It is a controlled roadmap for generating focused specs.

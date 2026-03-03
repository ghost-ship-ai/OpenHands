# Requirements: PostHog Analytics Overhaul

**Defined:** 2026-03-03
**Core Value:** Business metrics you can trust — conversion funnels, retention, credit usage, and churn signals backed by server-side events that never get blocked, lost, or sent without context.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Tracking Service

- [x] **TRCK-01**: AnalyticsService wrapper in `openhands/` core with consent gate — silently no-ops when user has not consented
- [x] **TRCK-02**: AnalyticsService branches between SaaS (identified) and OSS (anonymous, `$process_person_profile: False`) modes at init
- [x] **TRCK-03**: Every event includes common properties: distinct_id, org_id, app_mode, is_feature_env
- [x] **TRCK-04**: Event name constants file enforcing PostHog recommended naming (object-action, lowercase with spaces)
- [x] **TRCK-05**: PostHog Python SDK upgraded from ^6.0.0 to ^7.0.0
- [x] **TRCK-06**: `posthog.shutdown()` called in FastAPI lifespan on app exit to flush buffered events
- [x] **TRCK-07**: PostHog session middleware extracts `X-POSTHOG-SESSION-ID` from request headers and stores on `request.state`

### Identity & Groups

- [x] **IDNT-01**: Server-side user identity set on auth with full person properties (email, org_id, org_name, plan_tier, created_at, idp)
- [x] **IDNT-02**: Org-level group tracking via `group_identify("org", org_id)` with properties (org_name, plan_tier, member_count, credit_balance, created_at)
- [x] **IDNT-03**: Feature-env prefix on distinct_id separates staging from production data

### Business Events

- [x] **BIZZ-01**: `user signed up` captured server-side on user creation with idp, email_domain, invitation_source
- [x] **BIZZ-02**: `credit purchased` captured server-side on Stripe success callback with amount_usd, org_id, credit_balance_before, credit_balance_after
- [x] **BIZZ-03**: `credit limit reached` captured server-side with org_id, conversation_id, credit_balance, llm_model
- [x] **BIZZ-04**: `conversation created` captured server-side with conversation_id, trigger, llm_model, agent_type, has_repository, org_id
- [x] **BIZZ-05**: `conversation finished` captured server-side with conversation_id, terminal_state, turn_count, accumulated_cost_usd, prompt_tokens, completion_tokens, llm_model, trigger, org_id
- [x] **BIZZ-06**: `conversation errored` captured server-side with conversation_id, error_type, llm_model, turn_count, org_id

### Activation & Quality Events

- [x] **ACTV-01**: `user activated` captured server-side when user's first conversation reaches FINISHED state, with conversation_id, time_to_activate_seconds, llm_model, trigger
- [x] **ACTV-02**: `git provider connected` captured server-side on successful provider token storage with provider_type, org_id
- [x] **ACTV-03**: `onboarding completed` captured server-side with org group association, role, org_size, use_case

### Client-Side Cleanup

- [x] **CLEN-01**: `useTracking()` hook and all client-side `posthog.capture()` calls removed from React components
- [x] **CLEN-02**: `enterprise/experiments/` directory and all experiment code removed entirely
- [x] **CLEN-03**: `__add_tracing_headers` added to PostHogProvider config for automatic session ID injection to API requests
- [x] **CLEN-04**: posthog-js retained only for session replay, page views, and web vitals — no custom event capture

### PostHog Instance

- [x] **INST-01**: Old event definitions hidden/archived in PostHog UI
- [x] **INST-02**: Orphaned feature flags from removed experiments cleaned up in PostHog UI
- [ ] **INST-03**: Conversion funnel dashboard built (signup → first conversation → finished → credit purchase)
- [ ] **INST-04**: Retention dashboard built (conversation created as recurring engagement, grouped by signup cohort)
- [ ] **INST-05**: Credit usage dashboard built (org-level credit purchased, credit limit reached, credit balance trends)
- [ ] **INST-06**: Churn signal dashboard built (credit limit reached with no subsequent purchase within N days)
- [ ] **INST-07**: Usage pattern dashboard built (events by model, trigger, agent_type; avg cost per conversation)
- [ ] **INST-08**: Product quality dashboard built (success rate by terminal_state, error rates by model/trigger)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Analytics

- **ADVN-01**: Credit burn rate prediction per org (requires external calculation, not native PostHog)
- **ADVN-02**: Per-org usage anomaly alerts (requires threshold calibration from real data)
- **ADVN-03**: Cohort-based onboarding interventions (requires months of behavioral data)
- **ADVN-04**: Native PostHog experiments replacing removed experiment system

## Out of Scope

| Feature | Reason |
|---------|--------|
| Tracking individual agent tool calls | Volume explosion — belongs in LLM observability tools (Langfuse), not product analytics |
| Real-time streaming analytics | PostHog has ingestion delay; use app's own endpoints for real-time data |
| Custom analytics backend | Extreme complexity, not core product — PostHog covers the need |
| Historical event migration | Old events have wrong schemas and missing properties — archive and start fresh |
| A/B testing framework rebuild | Removed entirely; PostHog has native experiments when needed |
| Client-side LLM model tracking | Server has ground truth (ConversationMetadata.llm_model after all overrides) |
| PII in event properties | GDPR exposure — email goes in person properties, org name in group properties, events use IDs only |
| Mobile/native SDKs | Web only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TRCK-01 | Phase 1 | Complete |
| TRCK-02 | Phase 1 | Complete |
| TRCK-03 | Phase 1 | Complete |
| TRCK-04 | Phase 1 | Complete |
| TRCK-05 | Phase 1 | Complete |
| TRCK-06 | Phase 1 | Complete |
| TRCK-07 | Phase 1 | Complete |
| IDNT-01 | Phase 1 | Complete |
| IDNT-02 | Phase 1 | Complete |
| IDNT-03 | Phase 1 | Complete |
| BIZZ-01 | Phase 2 | Complete |
| BIZZ-02 | Phase 2 | Complete |
| BIZZ-03 | Phase 2 | Complete |
| BIZZ-04 | Phase 2 | Complete |
| BIZZ-05 | Phase 2 | Complete |
| BIZZ-06 | Phase 2 | Complete |
| ACTV-01 | Phase 4 | Complete |
| ACTV-02 | Phase 4 | Complete |
| ACTV-03 | Phase 4 | Complete |
| CLEN-01 | Phase 3 | Complete |
| CLEN-02 | Phase 3 | Complete |
| CLEN-03 | Phase 3 | Complete |
| CLEN-04 | Phase 3 | Complete |
| INST-01 | Phase 3 | Complete |
| INST-02 | Phase 3 | Complete |
| INST-03 | Phase 4 | Pending |
| INST-04 | Phase 4 | Pending |
| INST-05 | Phase 4 | Pending |
| INST-06 | Phase 4 | Pending |
| INST-07 | Phase 4 | Pending |
| INST-08 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 31 total
- Mapped to phases: 31
- Unmapped: 0

---
*Requirements defined: 2026-03-03*
*Last updated: 2026-03-03 — traceability filled in after roadmap creation*

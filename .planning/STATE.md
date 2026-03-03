---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
last_updated: "2026-03-03T13:23:15.178Z"
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 13
  completed_plans: 12
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-03)

**Core value:** Business metrics you can trust — conversion funnels, retention, credit usage, and churn signals backed by server-side events that never get blocked, lost, or sent without context.
**Current focus:** Phase 4 - Activation and Dashboards

## Current Position

Phase: 4 of 4 (Activation and Dashboards) — IN PROGRESS
Plan: 2 of 3 in current phase (04-01 and 04-02 complete, 04-03 remaining)
Status: In Progress
Last activity: 2026-03-03 — Completed plan 04-01 (USER_ACTIVATED and GIT_PROVIDER_CONNECTED activation events)

Progress: [█████████░] ~91% overall

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: 3 min
- Total execution time: 0.22 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation | 4 | 12 min | 3 min |
| 02-business-events | 1 | 1 min | 1 min |
| 03-client-cleanup | 1 | 8 min | 8 min |
| 04-activation-and-dashboards | 1 | 3 min | 3 min |

**Recent Trend:**
- Last 5 plans: 01-02 (3 min), 01-03 (3 min), 01-04 (2 min), 02-01 (1 min), 03-01 (8 min)
- Trend: Stable

*Updated after each plan completion*
| Phase 03-client-cleanup P01 | 8 | 1 task | 13 files |
| Phase 02-business-events P01 | 1 | 2 tasks | 2 files |
| Phase 01-foundation P03 | 2 | 3 tasks | 4 files |
| Phase 01-foundation P02 | 3 | 2 tasks | 6 files |
| Phase 02-business-events P02 | 2 | 2 tasks | 2 files |
| Phase 03-client-cleanup P02 | 25 | 2 tasks | 16 files |
| Phase 04-activation-and-dashboards P01 | 2 | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Service in openhands/ core (not enterprise/): OSS needs anonymous telemetry — one service with mode branching, not two services
- Server-side first: Reliability (no ad blockers), richer context, cleaner frontend
- Flush strategy: posthog.shutdown() in lifespan only — no per-request flush (batching performance). Accept minimal event loss on hard kill.
- Remove experiments entirely: enterprise/experiments/ removed as part of Phase 1; PostHog native experiments available if needed later
- [01-01] $process_person_profile: False in OSS mode — prevents person profile creation for anonymous installs, keeps PostHog pricing fair
- [01-01] set_person_properties and group_identify are SaaS-only no-ops in OSS mode
- [01-01] Feature-env prefix (FEATURE_) on distinct_id keeps staging traffic separate from production profiles
- [01-01] SDK errors are caught and logged — analytics must never crash the application
- [01-04] enterprise/experiments/ removed: ExperimentManagerImpl falls back to OSS no-op base class; SaaS deploy must unset OPENHANDS_EXPERIMENT_MANAGER_CLS
- [Phase 01-foundation]: plan_tier and created_at deferred: Org model has neither field in Phase 1 — set to None with inline comments
- [Phase 01-foundation]: credit_balance deferred to Phase 2: billing infrastructure not available in Phase 1
- [Phase 01-foundation]: Device auth identity at verify-authenticated endpoint: user_id available via Depends(get_user_id), correct integration point
- [Phase 01-02]: Lifespan patch placed before openhands.server.app import in saas_server.py so get_app_lifespan_service() returns SaasAppLifespanService at module-load time
- [Phase 01-02]: PostHogSessionMiddleware registered before SetAuthCookieMiddleware (reverse execution order)
- [Phase 01-02]: SaasAppLifespanService.__aexit__ wraps shutdown() in try/except to prevent analytics failures from blocking server shutdown
- [02-01]: is_new_user flag set inside if-not-user block, signup event fires after null guard — ensures user object is valid before capture
- [02-01]: Credit purchased event placed inside with-session block after session.commit() — guarantees event fires only on persisted DB state
- [Phase 02-02]: V0 llm_model is intentionally None in conversation_service.py: initialize_conversation runs before settings load
- [Phase 02-02]: Inline enterprise import pattern established: enterprise imports inside try/except for OSS safety in openhands/ core files
- [Phase 02-02]: org_id resolved inline via UserStore.current_org_id lookup (no separate helper) for simplicity
- [02-03]: turn_count=None: MetricsSnapshot doesn't derive turn count; deferred as follow-up
- [02-03]: STOPPED fires as 'conversation finished' not errored: user cancellation is normal terminal per CONTEXT.md
- [02-03]: Budget dual-fire: credit limit reached fires alongside conversation errored when error_type=budget_exceeded
- [02-03]: V0 error_type='unknown': AgentState.ERROR has no message payload; V0 also does not fire credit limit reached
- [03-01]: __add_tracing_headers injects X-POSTHOG-SESSION-ID via posthog-js fetch/XHR patch — no custom interceptor needed
- [03-01]: login-content handleAuthRedirect provider param removed — was only used for tracking, callers simplified
- [03-01]: exp_add_team_member_button orphan flag removed from code; INST-02 will delete from PostHog UI
- [Phase 03-client-cleanup]: trackError() made no-op rather than deleted: callers in WebSocket contexts do nothing without cascading changes
- [Phase 03-client-cleanup]: conversation-card.tsx auto-fixed (7th file not in plan scope) to achieve zero posthog.capture guarantee
- [Phase 03-client-cleanup]: usePostHog retained for session-replay/consent/identity only - zero custom capture calls remaining
- [03-03]: CLEN-02 formally verified: enterprise/experiments/ confirmed absent (deleted in Phase 1 Plan 01-04)
- [03-03]: INST-01 and INST-02 are PostHog UI admin tasks with no code path — confirmed complete by user
- [04-02]: No DB persistence of onboarding responses — analytics event IS the persistence; DB model deferred if product needs queryable data outside PostHog
- [04-02]: redirect_url hardcoded to '/' on backend; frontend reads from response for future flexibility without frontend changes
- [04-02]: group_identify fires only when org_id_str is non-null — personal-org users still get user-level ONBOARDING_COMPLETED event
- [Phase 04-01]: ACTV-01 gated on FINISHED state only — STOPPED (user cancelled) is not activation
- [Phase 04-01]: Exclude current conversation_id from count query: StoredConversationMetadataSaas row exists at conversation start, prior_count==0 means first conversation
- [Phase 04-01]: ACTV-02 only fires when token_value.token is truthy: host-only updates do not produce git provider connected event

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 2: Conversation lifecycle injection point for terminal state events needs confirmation — SaaSMonitoringListener is the likely hook but needs 30 min of codebase inspection during Phase 2 planning
- Phase 1: RESOLVED — service placed in openhands/ core per KEY DECISIONS in PROJECT.md (not enterprise/)

## Session Continuity

Last session: 2026-03-03
Stopped at: Completed 04-01-PLAN.md (USER_ACTIVATED and GIT_PROVIDER_CONNECTED activation events)
Resume file: .planning/phases/04-activation-and-dashboards/04-03-PLAN.md

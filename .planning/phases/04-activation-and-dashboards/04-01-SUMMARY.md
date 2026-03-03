---
phase: 04-activation-and-dashboards
plan: "01"
subsystem: analytics
tags: [posthog, analytics, user-activation, git-providers, server-side-events]

# Dependency graph
requires:
  - phase: 02-business-events
    provides: BIZZ-05 conversation finished capture block (ACTV-01 placed after it)
  - phase: 01-foundation
    provides: analytics service, consent-guard pattern, inline enterprise import pattern
provides:
  - ACTV-01: USER_ACTIVATED event in V1 webhook_router.py (first finished conversation)
  - ACTV-01: USER_ACTIVATED event in V0 conversation_callback_utils.py (first finished conversation)
  - ACTV-02: GIT_PROVIDER_CONNECTED event in secrets.py (provider token stored with non-empty token)
affects:
  - 04-dashboards: activation funnel dashboard (signup -> first conversation -> activated)
  - 04-git-adoption: git provider adoption tracking

# Tech tracking
tech-stack:
  added: []
  patterns:
    - ACTV-01 placed immediately after BIZZ-05 block, gated on FINISHED-only (not STOPPED/ERROR)
    - Count-query pattern to detect first conversation: exclude current conversation_id from count
    - Timezone-safe time_to_activate_seconds: handle naive datetime with .replace(tzinfo=timezone.utc)
    - OSS-safe inline enterprise import inside try/except for all SaaS-only lookups

key-files:
  created: []
  modified:
    - openhands/app_server/event_callback/webhook_router.py
    - enterprise/server/utils/conversation_callback_utils.py
    - openhands/server/routes/secrets.py

key-decisions:
  - "ACTV-01 gated on FINISHED state only — STOPPED (user cancelled) is not activation"
  - "Exclude current conversation_id from prior count query: StoredConversationMetadataSaas row exists at conversation start so count without current ID == 0 means first"
  - "V0 trigger set to None: V0 callback context has no trigger available"
  - "ACTV-02 only fires when token_value.token is truthy: host-only updates do not produce git provider connected event"
  - "user_id dependency added to store_provider_tokens via Depends(get_user_id): safe in OSS mode (returns None, analytics guard prevents execution)"

patterns-established:
  - "Post-BIZZ-05 activation gate pattern: add ACTV-01 block after CONVERSATION_FINISHED capture inside existing analytics if-block"
  - "First-conversation detection: async count query on StoredConversationMetadataSaas excluding current conversation_id"

requirements-completed: [ACTV-01, ACTV-02]

# Metrics
duration: 2min
completed: 2026-03-03
---

# Phase 4 Plan 01: Activation Events Summary

**Server-side USER_ACTIVATED and GIT_PROVIDER_CONNECTED analytics events with first-conversation count query and consent-guard pattern**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-03T13:20:04Z
- **Completed:** 2026-03-03T13:22:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- USER_ACTIVATED fires on first finished conversation in both V1 (webhook_router.py) and V0 (conversation_callback_utils.py) — gated on FINISHED state only, never STOPPED or ERROR
- First-conversation detection via count query on StoredConversationMetadataSaas excluding current conversation_id (row exists at conversation start)
- GIT_PROVIDER_CONNECTED fires in store_provider_tokens for each provider with a non-empty token, skipping host-only updates

## Task Commits

Each task was committed atomically:

1. **Task 1: Capture 'user activated' event in V1 webhook and V0 callback** - `85f9e19cd` (feat)
2. **Task 2: Capture 'git provider connected' event in store_provider_tokens** - `a523b521e` (feat)

## Files Created/Modified
- `openhands/app_server/event_callback/webhook_router.py` - Added ACTV-01 USER_ACTIVATED capture after BIZZ-05 block, gated on ConversationExecutionStatus.FINISHED, with async count query and timezone-safe time_to_activate_seconds
- `enterprise/server/utils/conversation_callback_utils.py` - Added ACTV-01 USER_ACTIVATED capture after BIZZ-05 block, gated on AgentState.FINISHED, using synchronous session_maker, trigger=None (V0 has no trigger context)
- `openhands/server/routes/secrets.py` - Added user_id Depends(get_user_id) to store_provider_tokens, ACTV-02 GIT_PROVIDER_CONNECTED capture after secrets_store.store() with token_value.token guard

## Decisions Made
- ACTV-01 gated on FINISHED state only — STOPPED (user cancelled) is not activation per plan requirement
- Exclude current conversation_id from prior count query: StoredConversationMetadataSaas row exists at conversation start, so count(other conversations) == 0 means first
- V0 trigger set to None: callback context has no trigger available, documented with inline comment
- ACTV-02 only fires when token_value.token is truthy: host-only updates (custom host URL change, no new token) do not produce a git provider connected event
- user_id dependency added to store_provider_tokens via Depends(get_user_id): returns None in OSS mode, analytics guard prevents any code path execution

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ACTV-01 and ACTV-02 events now captured server-side for both V1 and V0 code paths
- Activation funnel data (signup -> first conversation -> activated) ready for PostHog dashboard construction
- Git provider adoption tracking enabled for dashboards

---
*Phase: 04-activation-and-dashboards*
*Completed: 2026-03-03*

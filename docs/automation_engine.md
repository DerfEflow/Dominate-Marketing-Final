# The Automation Engine (research → generate → schedule → post → refresh)

This is the product's core value: **set up a client once, and the system keeps
their social media fresh, on-trend, and posting automatically.**

## The end-to-end loop (per client)

```
   ┌─────────────────────────────────────────────────────────────┐
   │  run_cycle(client)  — the "autopilot tick"                   │
   │                                                              │
   │  1. refresh_source_data → scrape site, analyze competitors, │
   │     harvest trends → store a fresh research SNAPSHOT on the  │
   │     client (+ last_research_at timestamp)                    │
   │  2. generate_posts → AI turns the fresh research + brand     │
   │     voice into N ready-to-post pieces                        │
   │  3. schedule_posts → spread them across the client's         │
   │     connected platforms over the next cadence window         │
   └─────────────────────────────────────────────────────────────┘
                              │
   ┌──────────────────────────▼──────────────────────────────────┐
   │  Scheduler worker (runs every minute)                        │
   │   • post_due_posts  → publish anything whose time has come   │
   │   • refresh_research → re-run run_cycle() for any client     │
   │     whose research is older than its cadence  ← "continual   │
   │     fresh source data" lives here                            │
   └─────────────────────────────────────────────────────────────┘
```

## Design decisions (made autonomously)

1. **Client-scoped, not user-scoped.** Social accounts, research, scheduled
   posts and automation settings all attach to a **Brand (client)**, because a
   salesperson runs many clients, each with their own accounts and trends.

2. **Runs end-to-end in SIMULATION MODE with no keys or connectors.** Every
   external dependency degrades gracefully:
   - No AI key → research/content use deterministic, on-topic placeholder data
     so the pipeline still flows and is reviewable.
   - No social OAuth app → accounts can be "connected (simulated)" and posts are
     marked posted with a `SIMULATED` marker instead of hitting a real API.
   The moment Fred adds real keys/connectors, the same code paths use them — no
   rewrite. Simulation is controlled by whether the relevant env vars exist
   (overridable with `SOCIAL_SIMULATE` / `AI_SIMULATE`).

3. **Reused what already worked.** The real posting code (Facebook/Instagram/X/
   LinkedIn), the OAuth service, the trend/competitor/profile research services,
   and the scheduler loop already existed — they were just disconnected and
   un-wired. This engine connects them and adds the missing refresh loop,
   client-scoping, simulation fallback, and UI.

## What needs Fred later (hard blocks)
- AI keys (OpenAI/Anthropic/Google) for real content + research.
- Social OAuth apps (Facebook/Instagram/X/LinkedIn/TikTok client id+secret) so
  clients can connect real accounts.
- On Railway: run the `worker` process (already in the Procfile) so the engine
  ticks 24/7 in production.

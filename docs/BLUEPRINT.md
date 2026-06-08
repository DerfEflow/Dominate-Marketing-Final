# Dominate Marketing — Product Blueprint (locked vision)

*Plain-English. This is the north star every build decision serves.*

## The promise
Give any small business — a local lamp shop, a roofer, a bakery — a **social
media presence and marketing-driven sales engine that beats the bigger
competitor down the street who pays a $10–15k/month agency.** Same firepower as a
world-class agency, at the price of a tool, and *better* than the agency because
it does what agencies can't do at scale and generic AI tools don't bother to do.

## The one rule that makes us different from every other AI tool
> **The AI is never allowed to invent content from thin air. It may only
> synthesize fresh, real research into creative output — and never from stale
> data.**

Every other "AI social media tool" is a text generator with a scheduler: the AI
makes up plausible, generic posts. Interchangeable, forgettable, commoditized.
We are the opposite: content is *grounded in real, current, client-specific
truth and real-world signal.* "Simulated creativity," built on facts.

## The moat: The Radar (always-on intelligence)
The differentiator is not the AI (everyone has GPT‑5.5). It's the **proprietary,
continuously-refreshed intelligence pipeline** feeding it. For every client the
system continuously watches four standing feeds, each signal time-stamped:

1. **Culture & Trends** — memes, viral formats, headlines, fashion, markets.
2. **Events & Calendar** — holidays, sports, movies, concerts, conventions,
   product launches, local happenings, high-attention moments.
3. **Competitor Intelligence** — competitors' websites, Google Maps listings,
   Yelp reviews, posting patterns, weaknesses — so we actively *out-position*
   the shop three miles away.
4. **Client & Market News** — the client's own launches/promos/suppliers,
   industry innovations, economic signals (a market dip is a reason for a sale;
   a heat wave sells different lamps than a blackout).

**Freshness is enforced**, not promised: every signal has a timestamp, and the
Strategist may only use signals inside a recency window. Never last week's data.

## The system (six layers)
1. **Foundational Client Profile (the DNA)** — built on day one by scraping the
   client's website, Google Business listing, and online mentions: what they
   sell, their voice, their proof, offers, service area, real customers. Kept
   alive (re-scraped periodically).
2. **The Radar** — the four feeds above, running per client.
3. **The Strategist** — fuses Profile + fresh Radar into a *living marketing
   plan*: themes for the period, what to post where/when, and why each piece
   beats the competitor. A plan, not random posts.
4. **The Studio** — produces content from the plan: **copy always; images on
   Plus; video on Pro/Enterprise.** Everything passes the 8-criteria quality
   gate (coherent / relevant / compelling / fresh / unique / creative / edgy /
   worth-paying); weak pieces are regenerated, not shipped.
5. **Distribution + the Freshness Clock** — schedules and posts (via Zapier or
   direct APIs), re-pulling the Radar each cycle so output reflects today.
6. **Human + Learning loop** — the salesperson reviews/tunes; the system learns
   each client's winning patterns. Software *and* service.

## The endgame (one sentence)
The shop owner does nothing, yet their feed is consistently timelier, sharper,
more local and more on-brand than the big competitor's agency feed — so they win
the attention and the sales. One salesperson runs 100 clients.

## The honest hard part
The product lives or dies on the **Radar's data feeds**, not the AI. Writing
posts is solved; reliably and affordably getting fresh competitor/event/trend
data per client (scraping, APIs, rate limits, terms of service, cost) is the real
work. So "aware of everything" is the north star; the architecture is built so
feeds plug in over time, starting with the highest-signal, most-attainable ones.

## What's live now vs. needs keys/connectors
**Live with no keys** (real data): client **website scrape** → Profile;
**events/holiday calendar**; **Google Trends** (best-effort); **competitor
website scrape** when a competitor URL is on file. AI synthesis runs on GPT‑5.5.

**Needs keys/connectors later** (pluggable, dormant until added): Yelp / Google
Maps reviews, news & sports/movie/concert APIs, deeper market data, image
generation (OpenAI image API — Plus), video (Pro/Enterprise), real social
posting (Zapier per client).

## Build sequence
1. **Grounded pipeline** — replace "AI brainstorm" with Profile → Radar
   (Trends + Events + Competitor basics) → Strategist plan → copy + quality gate.
   *(Re-uses the existing Sell-Profile, competitor, trend, and QualityCheck code.)*
2. **Images** (Plus tier) in the Studio.
3. **Expand Radar feeds** one at a time (reviews, news, market data).
4. **Video** (Pro/Enterprise).

## Tier mapping
- **Basic** — copy only, core feeds.
- **Plus** — + image generation.
- **Pro** — + video, + deeper competitor intelligence.
- **Enterprise** — + fully automated posting, all feeds, priority refresh.

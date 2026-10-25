# Vehicle Radar Agent — Main Implementation Instructions

> **Document role:** This is the source of truth for the current implementation scope. Read it before changing code. `update.md` is a roadmap only; it must not be treated as authorization to implement future features in the current release.
>
> **Product:** A lightweight, extensible, subscription-based vehicle-listing monitoring service for the Iranian market. Telegram is the first interface. All money values stored internally must be normalized to Iranian rials or tomans consistently; this project standardizes on **integer tomans** at the application boundary and must record the original displayed unit and normalization result where relevant.

## 1. Mission and product behavior

Build a service that lets each user create and monitor multiple independent vehicle-search requests. The service periodically obtains listings from approved data sources, normalizes them, matches them against active requests, ranks the best candidates, and sends concise Telegram notifications containing available details, an image when permitted and available, and a direct link to the original listing.

The goal is **useful, explainable matches**, not indiscriminate scraping or a claim that the service verifies a vehicle's real condition.

A listing's seller-written claims (for example, “engine is healthy”) are unverified claims unless a trusted independent verification source explicitly establishes otherwise. Never present inferred or seller-reported condition as a mechanically verified fact.

## 2. Non-negotiable implementation principles

1. **Do not implement the entire product at once.** Deliver the milestones in Section 14 in order. Each milestone must run and have automated tests before the next one begins.
2. **Do not invent API behavior.** Read the current official documentation for every source and build a small real-response contract test before implementing its adapter. Do not assume that search filters, images, condition fields, pagination, or quotas are available just because a website displays them.
3. **Source access is gated.** A source may run only when its registry status is `approved`. Review published terms, API terms, robots rules relevant to crawling, authentication requirements, rate limits, field rights, retention rules, and image/link reuse constraints. An absence of an explicit threat of legal action is **not** proof of permission. If a source explicitly prohibits the proposed automated access, do not crawl it unless the owner grants an applicable permission or API license. Do not bypass login controls, CAPTCHAs, anti-bot controls, paywalls, or technical access restrictions. Respect `robots.txt`; it is not itself a legal license. Stop or pause a source on 403, 429, repeated 5xx, or a clear policy warning; do not rotate identities or proxies to evade controls.
4. **Use public/authorized interfaces first.** Prefer official APIs or documented data feeds. HTML extraction is allowed only after the source review confirms the selected pages and method are permitted. Browser automation (e.g. Playwright) is not the default; use it only when necessary, permitted, and approved for that source.
5. **One collector per source, not one collector per user.** Fetch new/changed listings on a source-level schedule, normalize once, and match against many active requests locally. Never create one polling loop per user or per watch request.
6. **Keep the Telegram interaction responsive.** Do not crawl sources, compute price benchmarks, or perform long DB work inside a Telegram update handler. Enqueue work and respond quickly.
7. **Explain every recommendation.** Store score components and concise reason codes; do not return only an opaque AI score.
8. **Missing is not false or zero.** Unknown color, condition, mileage, year, or price must remain `unknown`/`null`, not silently become a zero or a negative condition.
9. **Keep external services replaceable.** Each listing source, price reference provider, payment provider, and delivery interface must use an adapter/interface. Core matching must not depend on Divar-specific fields or a particular payment provider.
10. **Avoid premature complexity.** Start as a modular monolith with separately runnable worker processes. Do not introduce Kubernetes, microservices, a vector database, an LLM call per listing, or mandatory Redis unless measurements prove it is needed.

## 3. Version-1 scope

### Included

- Telegram bot with inline-keyboard panel; edit the existing panel message as the user moves between steps instead of sending a new message for every step.
- Telegram Mini App for the longer, multi-field request form. The standalone, non-Telegram website panel is out of scope; it belongs only in `update.md`.
- Multiple independent watch requests per user, subject to plan limits.
- Curated reference taxonomies for makes, models, trims, colors, cities, transmission, fuel, body/engine condition values, and common synonyms. Preserve both raw user input and accepted normalized value.
- Confirmation flow when free text closely resembles a known taxonomy entry. If rejected, retain the raw value and use it as a text constraint where possible.
- Approved source adapters, source-level scheduling, normalizing, deduplication, matching, time-aware price context, compact listing records, and notification delivery.
- Subscription/plan model, daily request credits, maximum active watches, per-watch expiration, one-time referral reward, an immutable credit ledger, and idempotent payment/referral handling.
- Operational logs, health status, retry/backoff, rate-limit handling, tests, and backup/restore documentation.

### Explicitly not included in the first release

- A standalone public website or web dashboard. See `update.md`.
- Automatic negotiation, contacting sellers, placing bids, or messaging sellers on a user's behalf.
- Claims that a car is accident-free, mechanically healthy, legally clean, or correctly priced without independent evidence.
- A general-purpose autonomous web-browsing LLM agent.
- Mandatory image downloading or long-term retention of full-resolution listing photos.
- Crawling a source whose use is prohibited or whose access restrictions would need to be bypassed.
- Advanced ML models, embeddings, or a vector database before baseline rules have been measured.

## 4. Required stack and runtime shape

Use the following as the default unless a concrete compatibility issue is demonstrated and documented before changing it:

- Python 3.12.
- `python-telegram-bot` stable 22.x, async APIs.
- FastAPI for the Telegram Mini App backend/API.
- PostgreSQL as the production source of truth.
- SQLAlchemy 2.x async ORM and Alembic migrations.
- HTTPX async client for permitted HTTP/API providers.
- `selectolax` or `lxml` for permitted HTML parsing only; do not install both without a reason.
- Built-in `asyncio` plus a PostgreSQL-backed job table/claiming pattern for the initial queue. Claim due jobs atomically, for example with `FOR UPDATE SKIP LOCKED`. Add Redis/Celery only when a measured bottleneck or reliability requirement justifies the extra service.
- A small scheduler process that places due work into the job table; workers execute source polls, normalization/matching tasks, notification sends, and expiry jobs. Worker concurrency and connection pools must be bounded.
- pytest and async test support; use mocks/fixtures for external services and a separate opt-in integration test for real source credentials.

Run the Telegram bot, API/Mini App server, scheduler, and worker roles as separate processes/commands, even if they initially run on one modest server. They can share a codebase and PostgreSQL database. Do not create detached background tasks from a request handler as a substitute for a durable queue.

Do not start with Playwright. A source adapter must record why a browser is needed and prove that the automation method is permitted before adding it.

## 5. Suggested repository layout

Use this layout as a starting point; make the smallest coherent implementation for each milestone. Do not create empty speculative modules for every possible future feature.

```text
vehicle-radar/
├── AGENTS.md
├── update.md
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── alembic.ini
├── alembic/
├── app/
│   ├── main.py                  # process entrypoint wiring only
│   ├── config.py                # validated environment settings
│   ├── domain/
│   │   ├── enums.py
│   │   ├── money.py
│   │   ├── vehicle_query.py
│   │   ├── listing.py
│   │   └── matching.py
│   ├── db/
│   │   ├── session.py
│   │   ├── models/
│   │   └── repositories/
│   ├── services/
│   │   ├── taxonomy.py
│   │   ├── normalization.py
│   │   ├── matching.py
│   │   ├── deduplication.py
│   │   ├── price_benchmark.py
│   │   ├── watches.py
│   │   ├── credits.py
│   │   ├── subscriptions.py
│   │   ├── referrals.py
│   │   └── notifications.py
│   ├── sources/
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── divar.py
│   │   ├── html_base.py            # only if an approved source needs it
│   │   └── pricing/
│   │       ├── base.py
│   │       └── sourcearena.py      # disabled until verified and approved
│   ├── bot/
│   │   ├── handlers/
│   │   ├── keyboards.py
│   │   └── messages.py
│   ├── miniapp_api/
│   │   ├── routes/
│   │   └── telegram_auth.py
│   ├── workers/
│   │   ├── scheduler.py
│   │   ├── collector.py
│   │   ├── matcher.py
│   │   ├── notifier.py
│   │   └── maintenance.py
│   └── observability/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── source_contracts/
└── scripts/
```

## 6. Source registry and access policy

Every source must have a registry entry with at least:

- `source_key`, display name, source type (`listing` or `price_reference`), official base URL, documentation/terms URL.
- `status`: `candidate`, `approved`, `paused`, `disabled`, or `blocked_by_policy`.
- `access_method`: official API, licensed feed, or permitted page extraction.
- `reviewed_at`, review notes, allowed fields, retention restrictions, image reuse policy, direct-link policy.
- rate limit (requests/minute and daily quota if known), concurrency limit, minimum polling interval, timeout, retry/backoff policy.
- feature capabilities such as search filters, pagination, listing detail, images, source update timestamp, price history, and availability signal; use `unknown` until actually verified.
- Last successful run, last error, rolling error count, and circuit-breaker state.

Only `approved` sources are runnable. Do not silently promote a source from `candidate` because an endpoint responds. Review current source policy before first activation and periodically thereafter. A source-specific adapter must fail closed if the registry is not approved.

Initial source plan:

1. **Divar / Kenar API:** first integration test, subject to API key, required `SEARCH_POST` access, actual quota, and acceptable use/retention terms. Prefer the current documented v2 search endpoint and separately test the documented listing-detail endpoint. Do not assume the legacy endpoint's behavior or quota matches v2. Current docs: <https://divar-ir.github.io/kenar-docs/openapi-doc/finder-search-post-v-2/>, <https://divar-ir.github.io/kenar-docs/post/get_post/>, <https://divar-ir.github.io/kenar-docs/scopes/>.
2. **Bama:** do not automate access without explicit applicable permission; its published terms contain restrictions relevant to automatic browsing/copying. Keep `blocked_by_policy` unless permission changes.
3. **Sheypoor:** do not crawl routes disallowed by its current robots rules; a robots file is not an overall license. Keep disabled unless an approved API/feed or permitted route is confirmed.
4. **Other vehicle marketplaces:** add only after current terms, robots, endpoint behavior, rate controls, and commercial reuse rights are reviewed. Do not infer that unclear terms mean unlimited permission.
5. **Price-reference providers:** evaluate separately. SourceArena documents a price endpoint with model/year/price/update fields and historical lookup, but actual API access, sample quality, update semantics, price units, and commercial license must be tested before enabling. Keep the adapter disabled until then: <https://sourcearena.ir/وب-سرویس-api-قیمت-خودرو/.

If a source provides no confirmed `updated_at`, treat freshness as unknown; do not manufacture timestamps. Record the retrieval time separately from the source's own timestamp.

## 7. Core vehicle-search data model

Represent user preferences explicitly. Do not store one unstructured text blob as the canonical query.

A watch request should support at least:

- make, model, trim/version; raw aliases and normalized taxonomy IDs.
- production year min/max (Solar Hijri by default for Iranian listings); if any conversion is needed, store calendar/source assumptions and do not guess from ambiguous years.
- budget min/max, currency/unit, and budget mode: `strict` or `flexible`.
- maximum acceptable price above the top of budget, as a configurable percentage or amount only when the user enables flexibility.
- mileage min/max.
- city/region and optional distance or district restriction when data exists.
- preferred colors (multiple selections), body condition preferences, engine/mechanical condition preferences, gearbox, fuel, body style, seller type, and other supported fields.
- each criterion's mode: `hard_constraint`, `soft_preference`, or `informational`.
- request creation time, expiration time, status (`draft`, `active`, `paused`, `completed`, `expired`, `cancelled`), notification preferences, fallback-search policy, and a versioned snapshot of the plan settings relevant to this request.
- original user text, canonical/normalized value, confidence/source of normalization, and confirmation result.

Keep reference taxonomy data editable (seeded by migrations or data files, not hardcoded across handlers). Support Persian/Arabic letter normalization, Persian/Latin digits, whitespace/punctuation normalization, common vehicle aliases, and user-confirmed aliases. Never silently change a user's original input.

### Form behavior

- Collect essential fields first; advanced criteria stay optional.
- Offer a shortlist when user text closely matches taxonomy values: “Did you mean X?” User may accept, reject, or keep original text.
- Show a summary before activation and let user edit a field without restarting the whole form.
- Separate strict constraints from flexible preferences. Explain that a hard-constraint violation excludes a listing from the main results even if its overall score is high.

## 8. Listing model, normalization, and deduplication

Canonical listing fields should include:

- `source_id`, `source_listing_id`, source URL, first observed and last observed timestamps, source-provided published/updated timestamps if any, active/seen status.
- title, description excerpt, normalized make/model/trim, model year, mileage, price amount, currency, original price text, price mode (fixed/negotiable/unknown), city/area, color, body condition, engine condition, gearbox, fuel, seller category, image URLs or approved media identifiers.
- for each material field, retain provenance: `structured_source_field`, `seller_claim`, `parsed_from_text`, or `external_reference`; store extraction confidence where relevant.
- hash/fingerprint fields useful for deduplication, without retaining unnecessary personal information.

### Deduplication rules

1. First deduplicate exact records by `(source_id, source_listing_id)`.
2. Detect cross-source duplicates conservatively using normalized vehicle attributes, price, mileage, location, title tokens and available image fingerprints/URLs.
3. A fuzzy match must not merge records solely because make/model/year/price are the same; many distinct cars share these values.
4. Keep source-specific records and canonical cluster links; do not delete provenance. If duplicate confidence is below the configured threshold, leave them separate.
5. Do not send the same listing to the same watch request more than once. Re-notify only for meaningful changes the user has enabled (for example, a meaningful price reduction or a reactivated listing).
6. Store change snapshots only for material changes (price, active state, mileage/specification if changed). Avoid writing a full snapshot every polling cycle.

## 9. Matching and ranking

Implement a deterministic, testable baseline before adding any LLM or ML capability.

### Stage A — eligibility filters

- Exclude inactive/expired source records when the source provides this signal, and mark stale/unknown availability honestly when it does not.
- Enforce all active `hard_constraint` fields.
- Normalize monetary units and vehicle variants before comparing.
- Never bypass a hard constraint in late-stage/fallback suggestions. A flexible budget is a soft constraint only because the user explicitly enabled it.

### Stage B — weighted score

Produce `match_score` from 0 to 100 with configurable, documented components. Suggested dimensions: make/model/trim, year, mileage, budget, body/engine condition, color, location, and remaining preferences. Missing fields should reduce certainty or contribute neutral/penalized values according to the documented policy; they must not be treated as verified matches.

Also produce a separate `data_confidence` score/label based on field completeness, freshness, and provenance. Do not conflate match quality with confidence in the source data.

Every result must contain reason codes and user-readable reasons such as:

- exact model/trim match;
- price is within budget;
- price is 2.9% above the selected ceiling and the user enabled flexible budget;
- mileage is within/near the preferred range;
- color differs from preference;
- seller did not state body/engine condition;
- source update time is old or unknown.

### Stage C — thresholds and fallbacks

- Default primary results: `match_score >= 70`, subject to hard constraints and minimum data-quality rules.
- At 48 hours after a watch starts, if the count of useful primary matches is below a configurable minimum, optionally send lower-confidence suggestions in a distinct “broader matches” section. Default range: 40–69. Never mix these into the main ranking without a label, and never include hard-constraint violations.
- Make thresholds, grace period, minimum-primary-result count, and whether fallback suggestions are enabled configurable in the plan/watch settings.
- Do not claim a score such as 70% is a statistically calibrated probability unless an empirical calibration study has been run. Label it as a matching score.

### Flexible budget example

If the user's budget is 1.5–1.7 billion tomans and the user accepts flexible pricing, a listing at 1.75 billion is 50 million above the upper limit (about 2.94%). Keep it out of strict-budget results; if flexibility and a suitable tolerance are enabled, it may appear as a clearly labeled near-budget candidate. Say it may be worth negotiating, not that a discount is guaranteed. Use listing text to identify negotiability only when explicitly stated.

## 10. Time-aware price intelligence

Keep **listing discovery** and **market price reference** as separate interfaces and data streams. An asking price is not a completed transaction price and should never be described as one.

### Price observation storage

For every provider value, store: provider, normalized make/model/trim/year, location scope if present, mileage/condition scope if present, observed price, currency/unit, source-reported update time, retrieval time, and any quality/coverage metadata. Never overwrite old price observations blindly.

### Benchmarking approach

- Prefer comparable cohorts: same make/model/trim, year band, location where available, and similar mileage/condition. Relax one dimension at a time and disclose when comparison had to broaden.
- Use robust statistics (median/quantiles and outlier handling) rather than a simple average that can be distorted by exceptional values.
- Require a configurable minimum sample count before producing a numeric benchmark. Otherwise say “insufficient comparable data.”
- Apply time decay/freshness weighting, and show benchmark timestamp/freshness. When reference prices change, recompute the benchmark; do not reuse stale market values without marking them stale.
- Keep source asking prices, third-party list prices, and any independently observed transaction prices in separate classes.
- Compare each listing against its current benchmark only when the cohort and freshness are adequate. Show a range or relative difference, not false precision.
- Deduplicate the same provider observation and near-duplicate entries before computing the benchmark. Do not treat repeated reposts of one vehicle as independent market samples.
- Explain limitations: vehicle condition in free text can be incomplete or misleading, and listing prices are not necessarily final sale prices.

A provider is not enabled simply because it has a public documentation page. Run a contract test, inspect real responses, verify updates/units/history behavior, check commercial use rights, set timeout/rate limits, and then change its registry state to `approved`.

## 11. Monitoring, scheduling, and concurrency

- Poll each approved source once per source-level schedule/partition (for example source + city + category/query cohort), not once per watch request.
- Use the source's permitted cadence and quota. Do not promise “real-time” alerts unless the API/contract actually supports a reliable real-time feed.
- Save a cursor or checkpoint only when source behavior supports it. If no cursor/pagination exists, use bounded queries and explicit coverage/limitations rather than assuming every result was seen.
- Use bounded async concurrency, per-source semaphores, connect/read timeouts, exponential backoff with jitter, and a circuit breaker. Honor `Retry-After` where provided.
- Treat 401/403 as credential/permission problems, 429 as rate limiting, and repeated 5xx/timeouts as temporary source failures. Pause the source when required; do not retry indefinitely.
- Use durable jobs with idempotency keys. A worker crash must not produce double credit consumption or duplicate alerts.
- Use DB indexes for active watch status/expiry, listing source identity, normalized search fields, observation timestamps, match dedupe, and credit-ledger references.
- Measure DB connections, query latency, queue lag, per-source poll duration/failures, matching time, notification throughput, and worker memory. Set limits and load-test before claiming capacity.

## 12. Telegram UX and notifications

- Prefer an inline keyboard panel and edit the current panel message through each step. Handle “message is not modified”, missing/deleted message, and edit-window/API failures gracefully; send a fallback message only when editing cannot work.
- Use separate notifications for meaningful events only: watch activated, high-quality new candidate, meaningful price change, watch expiring/expired, payment/referral result, and relevant service errors.
- Avoid chat spam by default. Batch moderate/fallback matches and rate-limit messages per chat. High-quality matches may be delivered promptly under a per-chat quota.
- Listing notification content should include: make/model/trim if known, year, mileage, city, asking price and price mode, body/engine details as sourced, match score, data confidence/unknown-field note, why it matches, source name, timestamp/freshness where useful, photo if permitted/available, and a direct original listing link.
- Escape HTML/Markdown from seller content. Seller-controlled titles/descriptions must never be inserted as trusted markup.
- Do not store full-size images by default. Reuse permitted remote image URLs or a source-provided/Telegram file identifier where supported and permitted. If that fails, show a link-only result.
- Telegram Mini App authentication must validate raw `Telegram.WebApp.initData` server-side using the official signature verification algorithm and reject stale `auth_date` values per configured policy. Never trust `initDataUnsafe`, client-submitted Telegram IDs, prices, plan values, or credit balances. Official guide: <https://core.telegram.org/bots/webapps>.

## 13. Plans, credits, referrals, and payments

Keep plan capabilities in data/config rather than scattering tier names across code. A plan version should define at least:

- daily request credits granted;
- maximum concurrently active watches;
- maximum watch duration;
- sources and features enabled;
- fallback matching policy and notification policy.

Separate these concepts:

- **Daily credit allowance:** how many new watch requests may be created in a day.
- **Active-watch cap:** how many currently active watches the user may have.
- **Watch duration:** expiration deadline for each individual watch.

Do not charge a new daily credit continuously for an already-active watch unless the product specification explicitly changes. Daily credits should have an explicit rollover policy; default to non-accumulating daily allowance unless product configuration says otherwise. A subscription does not silently extend an existing watch beyond its saved expiration.

Credit changes must be an append-only ledger with unique idempotency keys (grant, spend, referral reward, refund/adjustment). Balance changes must be atomic under concurrent requests. Enforce per-user referral constraints and grant the initial one-time referral reward only once for a qualified invite; do not implement recurring referral rewards.

Create a payment-provider interface and test mode. For digital goods/services sold inside Telegram, follow the current Telegram Stars requirements and payment confirmation flow; do not grant entitlement merely because checkout was initiated. Verify the successful-payment event, store its transaction/charge identifier, provide support/terms commands, and make payment handlers idempotent. Official guide: <https://core.telegram.org/bots/payments-stars>. If payment jurisdiction or launch-market constraints are unresolved, keep production checkout disabled rather than inventing a workaround.

## 14. Retention, privacy, and compact archive

- Store the minimum data needed for matching, alerts, and support. Do not collect seller phone numbers or other personal data unless a legitimate, documented feature and source permission require them.
- Keep listing content fields needed for the active watch and a compact history of material changes. Avoid raw HTML, full response blobs, duplicate image files, and full snapshots on every poll.
- After watch expiry, apply a configurable retention policy: preserve a compact record of sent results, source ID/link, score/reasons, and price-change summary only as needed; delete temporary payloads and stale data. Do not promise permanent archival unless required and permitted.
- Retention must respect source contractual limits and user privacy/deletion obligations. If a source requires removal or limits storage, enforce that at adapter/policy level.
- Keep secrets out of source control; provide `.env.example` with names and dummy values only.
- Log IDs, timings, statuses, and error categories, not bot tokens, API keys, payment secrets, full user content, or personal data.
- Validate all external payloads and URLs. Prevent SSRF by allowing only configured source domains and never fetching a URL supplied directly by a user or extracted from an untrusted listing without domain checks.

## 15. Required first implementation tasks and tests

### Milestone 0 — prove data access before building the crawler

1. Read the current official Divar/Kenar v2 search docs and listing-detail docs.
2. Create a source registry entry in `candidate` state until the developer supplies credentials and verifies the approved use case.
3. Build a small opt-in integration script that makes a bounded request with a configured API key; never commit credentials.
4. Save a sanitized sample response as a test fixture (remove any personal/sensitive fields not needed for contract tests).
5. Verify actual schema for listing token/id, direct URL construction or provided link, price units, vehicle fields, images, year/mileage, update timestamp, and available filters. Verify price-filter behavior explicitly; the current v2 docs describe category-specific price ranges, but do not assume every desired field is filterable.
6. Record actual API key scopes, daily quota, minutely rate limit, maximum response size/pagination behavior, and any errors. Test `429` handling without intentionally exhausting a production quota.
7. Decide whether the source can cover the initial product use case. If not, stop and report the blocker before implementing a false “continuous monitoring” promise.

### Tests required before milestone completion

- Persian and Arabic letter normalization; Persian/Latin digits; whitespace/punctuation; billion/million/toman/rial conversions.
- Exact taxonomy hit, close taxonomy suggestion, rejected suggestion preserving raw text, and unknown value handling.
- Strict budget versus flexible budget; example above-ceiling listing; zero/unknown price; negotiable/unspecified price mode.
- Hard constraint never bypassed by fallback suggestions.
- Missing body/engine condition remains unknown.
- Same source listing ingested twice; cross-source probable duplicate; similar-but-different vehicles not incorrectly merged.
- Same result not sent twice; material price drop sends only when configured; insignificant change does not trigger alert.
- Daily credits, active-watch cap, expiration, and simultaneous credit spending/granting under concurrency.
- Referral can grant only one reward per qualified invite.
- Source `paused`/`blocked_by_policy` adapter never runs; 429/403 handling pauses or backs off as configured.
- Telegram Mini App invalid signature and stale `auth_date` rejected.
- Price benchmark rejects stale/insufficient data and avoids counting reposts as independent samples.
- Restart/retry does not duplicate jobs, credit changes, or notifications.

## 16. Completion and agent-work rules

For every task:

1. Inspect the relevant existing files and current documentation before editing.
2. State a short plan and identify assumptions; do not ask the user to re-confirm a decision already in this document.
3. Implement one vertical slice at a time.
4. Add/adjust tests in the same change.
5. Run tests, lint/type checks that are configured, and formatting checks. Report exact commands and outcomes honestly.
6. Update README/config docs if behavior or setup changes.
7. Do not create giant files or silently add dependencies. Explain any new package and its necessity.
8. Do not mark a milestone complete while integration-critical values (API permissions, data coverage, quota, payment config) are merely assumed.
9. If a third-party source fails, keep the rest of the service operational and report that source as degraded; do not silently replace it with prohibited access.
10. If a requirement is ambiguous, choose the smallest safe, testable implementation that preserves the product intent and document the decision. Only ask a question when implementation truly cannot proceed without a choice.

## 17. Official references checked for this blueprint

- Divar/Kenar v2 listing search: <https://divar-ir.github.io/kenar-docs/openapi-doc/finder-search-post-v-2/>
- Divar/Kenar listing details: <https://divar-ir.github.io/kenar-docs/post/get_post/>
- Divar/Kenar API quotas and scopes: <https://divar-ir.github.io/kenar-docs/scopes/>
- Legacy Divar search endpoint warning (do not confuse with v2): <https://divar-ir.github.io/kenar-docs/post/search_post/>
- Bama terms: <https://bama.ir/terms>
- Sheypoor robots rules: <https://www.sheypoor.com/robots.txt>
- Telegram Mini Apps authentication: <https://core.telegram.org/bots/webapps>
- Telegram Stars for digital goods/services: <https://core.telegram.org/bots/payments-stars>
- SourceArena car-price API reference (candidate only; verify service/license/freshness): <https://sourcearena.ir/وب-سرویس-api-قیمت-خودرو/>

# ContextCon 04: master handoff, supplier agent

**Status:** active. Single source for the team. Older research handoffs are marked SUPERSEDED. Planning is complete (6 Nov, 3:07 AM IST as stated by the owner). Background and corrections are in `PLANNING-HANDOVER-supplier.md`.
**Team:** three people. Person 1 is the repo owner (`bratadeepsarkar123`, integrator). Person 2 is `AdityaChittora`. Person 3 is `debugat2am`. Logins are from `TEAMWORK.md`.
**Decisions:** taken by the owner in chat, or by a three-voter round where the owner delegated the choice. See section 2.

---

## 1. What we are building

A supplier agent for a buyer who needs to buy something regularly. Example: 500 industrial temperature sensors, budget $25,000, delivery in 14 days. The agent reads the request, finds candidate suppliers, checks each company is real with Crustdata, asks suppliers for quotes over WhatsApp, compares the quotes against the buyer's policy, and produces an approved vendor record and a purchase order (PO).

**Real and simulated in the demo:**

- **Real:** request parsing, Crustdata company checks, policy comparison, and WhatsApp messages between the team's own phones.
- **Simulated (labelled SIMULATED everywhere):** supplier replies and quotes, the vendor record, and the PO. No message goes to any real supplier.

Second category, later: footwear (TESSCH; its sole is PU, not rubber or foam).

## 2. Decisions

| Decision                           | Status                                                                                                                                                                                                                                    |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Supplier agent over freight        | Chosen. Freight parked.                                                                                                                                                                                                                   |
| First category: industrial sensors | Chosen. Footwear second.                                                                                                                                                                                                                  |
| Insurance and sanctions ideas      | Parked.                                                                                                                                                                                                                                   |
| Repo stays **private** for now     | Owner's choice. Handbook requires public later.                                                                                                                                                                                           |
| **Crustdata demo rule**            | **Option C** (owner, 6 Nov, chose our recommendation). Screens show **where each fact came from** ("Source: Crustdata" and the endpoint and field), never the company values. No raw JSON, export files, download links or full records.  |
| **Supplier names on screen**       | **Neutral labels** ("Supplier 1", "Supplier 2", ...) on every screen, with the citation beside each fact. The real name is kept only in the internal log, never on a screen or in the video. Three-voter round, 6 Nov: 3 of 3 for labels. |
| Discovery method                   | **Ranked search** (`search.query`) with location filters as hard limits. Filters-only is the fallback. Source: claude-7a live test, 6 Nov.                                                                                                |
| Supplier contact channel           | **WhatsApp**, not email. Real messages only between the team's phones (Meta test number). Supplier messages are simulated. Real suppliers need opt-in and approved templates, so they are out of scope for the event.                     |
| Competitor analysis                | Teammate B's file is delivered (`task2-competitor-workflows.md`). It is used for the pitch only. The build does not wait for it.                                                                                                          |
| Zuric Group                        | One note only: a Dubai-based procurement services firm (zuricgroup.com). It does not describe supplier onboarding. Pricing and client figures are not verified. Pitch-only, not blocking.                                                 |

**Display rule under option C (what it means for the build):** option C is a display rule only. Person 2 still fetches `headcount` and `locations` from Crustdata, because the policy check (Person 3) needs them. The screens show only the labels and the citations. The internal log keeps the real names and the values, and nothing from that log goes into the demo or the video.

## 3. Hard rules (link, do not copy)

Full rules: `rules.md` and `build-rules.md` in the repo root. These can disqualify us:

- **History:** the repo's commit history starts at 11:00 PM IST, 5 Nov. No backdating. No force-push over a teammate's work.
- **No secrets:** no Crustdata key, model key, WhatsApp token or password in code, commits, issues, chat, screenshots or video. Keys go in local environment variables and git-ignored files.
- **No real outreach:** no real message, email, call, booking or payment to anyone outside the team. WhatsApp goes only to team-owned phones.
- **Label simulated items** everywhere: product, demo, README.
- **Cite every fact** (endpoint and field, or document page). Say "I don't know" when unverified.
- **Human only for exceptions:** ask a person only when the answer changes the result.

## 4. The agent, end to end

| #   | Step                         | In                | Out                                                | Real or simulated                          | Source and check                                                                                                                                                                                                                                                                                                                                                                                                         |
| --- | ---------------------------- | ----------------- | -------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Parse the request            | Messy text        | Request (section 6)                                | Real                                       | Request text                                                                                                                                                                                                                                                                                                                                                                                                             |
| 2   | Find candidate suppliers     | Request           | Candidate list (labels plus internal names)        | Real (Crustdata)                           | `POST /company/search` with `search.query` (ranked). Filters are hard limits. Run `company_autocomplete` first for any industry filter. Ranked search gives one window of up to 100 results, no paging.                                                                                                                                                                                                                  |
| 3   | Verify each company          | Candidate         | Verified supplier, or NOT VERIFIED                 | Real (Crustdata)                           | `POST /company/identify` (free), then `POST /company/enrich` (2 credits per match) for `headcount` and `locations`. Identify does not return these. **Product-line check:** read `basic_info.description` from `POST /company/enrich` (request it in the `basic_info` fields; identify does not return it). Confirmed by claude-7a, 6 Nov, via the free schema call. If it is empty, the card says `HUMAN_OR_SIMULATED`. |
| 4   | Dedupe                       | Candidates        | One record per company, with match confidence      | Real                                       | Domain and name match, within the window from step 2                                                                                                                                                                                                                                                                                                                                                                     |
| 5a  | **WhatsApp request**         | Verified supplier | Outbound message log                               | Team phones: real. Supplier: **SIMULATED** | Log file                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 5b  | **WhatsApp reply and quote** | Reply             | Quote                                              | **SIMULATED** (labelled)                   | Sample data                                                                                                                                                                                                                                                                                                                                                                                                              |
| 6   | Compare and apply policy     | Quotes and policy | Ranked result, exceptions queue                    | Real logic on simulated data               | Policy file (sample, labelled)                                                                                                                                                                                                                                                                                                                                                                                           |
| 7   | Vendor record and PO         | Chosen supplier   | Vendor record and PO, each with an idempotency key | **SIMULATED**                              | Key stored before any write                                                                                                                                                                                                                                                                                                                                                                                              |

**Human-in-the-loop:** only at step 6 exceptions (no supplier within budget) and step 3 NOT VERIFIED or product-line unknown. Exceptions go to a queue with the reason.

**Idempotency:** every write (WhatsApp send, quote, vendor record, PO) gets a unique key, stored before the write and checked before any retry. A crash or retry never sends or creates twice.

**Screens:** every screen uses the display label (`Supplier 1`, ...). Steps 2, 3, 6 and 7 show the label and the citation beside each fact.

## 5. Work split (three people)

Chosen by majority of three advisers (two of three put the policy check with Person 3). The integrator (Person 1) merges. Nobody edits another person's files without asking.

**File ownership check:** each path has exactly one owner. Shared shapes live only in `src/contracts/*` (Person 1). Changes after the contract freeze need all three people to agree.

### Person 1: repo owner (`bratadeepsarkar123`). Spine, intake, PO, end-to-end run, video

- **Owns:** `src/contracts/*`, `src/intake/*`, `src/po/*`, `src/state/*` (idempotency store and internal name log), orchestrator, `tests/e2e*`, `samples/*`, `README.md`, demo video.
- **Does:** steps 1, 7 and the orchestrator. Runs the end-to-end flow. Owns the end-to-end run, which must pass before 6:30 AM.
- **Acceptance checks:** a sample request runs from step 1 to step 7 with no real network call; repeating the same request creates one PO; the PO and vendor screens show only labels; the internal log is the only place with real names.
- **Must not touch:** Crustdata client, quotes, WhatsApp module.

### Person 2: `AdityaChittora`. Discovery and Crustdata

- **Owns:** `src/discovery/*`, `src/crustdata/*` (client, retry, rate limits), the citation script for the demo, `tests/crustdata*`.
- **Does:** steps 2, 3 and 4. Runs the one live Crustdata call that confirms the open field paths (section 7).
- **Discovery:** ranked `search.query` first; `company_autocomplete` before any industry filter; location filters as hard limits; filters-only as the fallback. One window of up to 100 results; dedupe inside that window.
- **Verification:** identify first (free), then enrich by id (2 credits) for `headcount` and `locations`. Never request `headcount` or `locations` on identify.
- **Acceptance checks:** a fixture run returns labels and citations only on the screen data; a 429 backs off and a 402 or 403 stops the run with a clear message; the product-line check is marked human or simulated until the field is confirmed; the live run uses under 200 credits and `GET /account/credits` is checked first.
- **Must not touch:** quotes, WhatsApp, PO.

### Person 3: `debugat2am`. Quotes, policy, WhatsApp, PO retries

- **Owns:** `src/quotes/*`, `src/policy/*`, `src/whatsapp/*` (new; simulated for suppliers, team phones only), `data/simulated/*`, `tests/failure*`, `docs/*` (diagram).
- **Does:** steps 5a, 5b and 6. Checks retries never send twice.
- **Guards:** the WhatsApp module refuses to run unless mode is `TEAM_PHONE` or `SIMULATED`. A test asserts no outbound call to any other number.
- **Acceptance checks:** quotes and ranked results show labels only; a repeated WhatsApp send with the same key sends once; a quote over budget goes to the exceptions queue with the reason; the diagram labels simulated steps.
- **Must not touch:** Crustdata client, PO writes (Person 1 owns those).

**Integration points, in order:**

1. **IP0, first hour:** Person 1 pushes contracts and fixtures. Everyone pulls.
2. **IP1:** Person 2 pushes discovery output on fixtures. Person 3 consumes it.
3. **IP2, stub end-to-end:** Person 1 runs all steps on fixtures.
4. **IP3:** one live Crustdata run replaces fixtures. Person 2 keeps the citation script for the demo.
5. **IP4:** idempotency wired into the WhatsApp and PO writes. Person 3's failure tests run against it.
6. **IP5:** README, diagram and video frozen. Code freeze at 7:00 AM.

**Shared tests and docs:** each person writes failure tests for their own block. Person 1 writes the README. Person 3 records the video in the last hour. Person 2 checks every Crustdata citation.

## 6. Shared interface contract (JSON shapes)

- **Request:** `{ item, quantity, budget, currency, deadline_days, region, missing_fields[] }`
- **Candidate and verified supplier:** `{ display_label, name_internal (log only, never shown), primary_domain, year_founded, headquarters_internal, headcount_total_internal, industry, product_line_status: "CONFIRMED" | "HUMAN_OR_SIMULATED", sources: [{ field, endpoint }], confidence }`
  - `display_label` is the only supplier identifier that appears on a screen.
  - Fields marked `_internal` are for the policy check and the log. They are never printed on a screen.
- **WhatsApp message:** `{ display_label, direction: "outbound" | "inbound", text, idempotency_key, mode: "TEAM_PHONE" | "SIMULATED", label }`
- **Quote (SIMULATED):** `{ display_label, unit_price, lead_time_days, label: "SIMULATED" }`
- **Vendor record and PO (SIMULATED):** `{ idempotency_key, display_label, po_number, total, status, label: "SIMULATED" }`

Person 1 freezes these in `src/contracts/*` first (IP0).

## 7. Crustdata reference (verified 2026-11-06)

Source: `CRUSTDATA-CHECK-REPORT.md` (sections 2 to 5, and the follow-up), and claude-7a's live checks on 6 Nov. No keys in any of these files.

- **Base:** `https://api.crustdata.com`. **Headers:** `authorization: Bearer <KEY>`, `x-api-version: 2025-11-01`.
- **Enabled (12):** `/company/search`, `/company/identify`, `/company/enrich`, `/company/search/autocomplete`, `/person/search`, `/person/enrich`, `/person/search/autocomplete`, `/job/search`, `/social_post/search`, `/agent/query`, `/web/search/live`, `/web/enrich/live`.
- **Not on our account:** `/job/search/autocomplete` (job autocomplete is MCP-only as `job_autocomplete`). All `/batch/...` endpoints. `/person/identify`, `/person/contact/enrich`, and the professional-network live endpoints.
- **Plan-gated fields (403 if requested):** company `technographics`, `social_posts`, `maps`, `hiring.recent_openings`, `social_profiles.crunchbase`; person `assessment`, `certifications`, `recently_changed_jobs`, `social_posts`, `years_of_experience`, `basic_profile.first_name`, `basic_profile.last_name`. `headcount` and `locations` are plan-gated on identify, so request them on enrich only.
- **Fields to request:** `locations` (for `locations.headquarters`) and `headcount` (for `headcount.total`), on enrich.
- **Field names:** the employer filter is `experience.employment_details.current.company_name`. It comes back as `experience.employment_details.current.name`. `current_company` and `current_employer` do not exist.
- **Department:** `basic_profile.normalized_title.department` (person search).
- **Credits:** `GET /account/credits` returns `account.credits`. Check before any run. Budget: 15,000 per builder.
- **Costs:** company search 0.03 per result (ranked query test: 0.15 for 5 results); company identify free; company enrich 2 per match; person search 0.03 per result (0.23 with experience and education); person enrich 1 base plus extras; job search 0.03 per result; autocomplete free.
- **Per-minute limits:** company search 30; company identify 30; company enrich 15; person search 30; person enrich 15; job search 30; autocomplete 300; web search and enrich 10.
- **Industry filter values are a closed set.** Resolve with `company_autocomplete` before filtering. An unknown value returns zero rows silently.
- **Gaps (not in Crustdata):** PAN and GSTIN, bank account ownership, ISO and RoHS certifications (plan-gated), signing authority.
- **Still unconfirmed:**
  - **Product-line field: confirmed.** `basic_info.description` (company enrich, basic_info group; also returned by company search with `fields: basic_info`). Not in identify's schema summary. Still to check on the live run: whether it is empty for typical candidates.
  - LinkedIn ID: no separate field. Closest is `social_handles.professional_network_identifier.profile_url`, not filterable.
  - Tenure in months: no field. Closest is `experience.employment_details.current.years_at_company_raw`, not confirmed as months.
  - `metadata.date_added` on jobs: meaning not defined in the schema. Jobs are out of scope.
- **Terms:** no clause mentions demos. Restricted: giving data outside the organisation, sharing export files or download links, selling the data as a database or enrichment service. See section 8.

## 8. Demo rule for Crustdata data

- **Decision: option C.** Citations only; no company values on screen. Owner chose our recommendation in chat on 6 Nov.
- **What the screen shows:** "Supplier 1", the field name, "Source: Crustdata", and the endpoint. For example: "Headcount: source Crustdata, company enrich". No values.
- **What never appears on screen, in the video, or in the README:** company values, the real company name, raw JSON, export files, download links or full records.
- **Why:** the judging rules ask for "where each fact came from" (20 points for facts). The Crustdata terms restrict giving data outside the organisation, and the terms do not mention demos.
- **Risk:** a judge may find labels less credible. The citation trail has to carry the proof.

## 9. Open items

Non-blocking items are for the pitch and do not hold the build.

1. **Product-line field: resolved.** Use `basic_info.description` on enrich (section 7). Empty descriptions fall back to `HUMAN_OR_SIMULATED`. Not blocking.
2. **WhatsApp recipient limit and business verification:** the owner checks these on the Meta dashboard. Not blocking; the test number works for the three team phones.
3. **Meta connection (side task):** no Meta or WhatsApp tool is connected in this session. Connecting one needs a token the owner creates in Meta and sets as an environment variable, never pasted into chat. The Graph API may not show the recipient limit, so the dashboard check comes first. Not blocking.
4. **Competitor claims (pitch-only):** other incumbents' discovery features (Coupa, Zycus, JAGGAER, Ivalua, ServiceNow, Zoho, GEP) are unchecked. SAP Ariba Discovery exists (search results only, re-check sap.com). Fees unverified. Pitch-only, not blocking.
5. **Zuric Group (pitch-only):** NOT VERIFIED. The owner calls it "Zurich", the PDF says "Zuric Group", and the 6 Nov web search found no public profile under either name. Confirm with the owner before the pitch; not blocking.
6. **Corrected teammate handoff (`agent-handoff-corrected.md`):** 75 changes plus the Zuric correction. Owner review before it goes to teammates. Pitch-only for the parts not used by the build.
7. **Repo visibility:** stays private for now. Public by the handbook deadline.

## 10. Timeline

Targets set from 3:07 AM IST. The 7:00 AM code freeze is from the handbook; the other times are plan targets.

| Time (IST)     | What happens                                                           |
| -------------- | ---------------------------------------------------------------------- |
| 3:07 to 3:30   | IP0: contracts and fixtures pushed. Everyone pulls.                    |
| 3:30 to 4:15   | IP1 and IP2: discovery on fixtures; stub end-to-end run (Person 1).    |
| 4:15 to 5:00   | IP3: one live Crustdata run replaces fixtures. Citation check.         |
| 5:00 to 5:45   | IP4: idempotency wired into WhatsApp and PO writes. Failure tests run. |
| 5:45 to 6:30   | Fixes only. Video recorded. Rehearsal of the full demo, once.          |
| 6:30 AM        | IP5: README, diagram and video frozen. Last call.                      |
| 7:00 AM, 6 Nov | **Code freeze.** Repo, video and form due. Hard deadline.              |

## 11. Return format for each person

1. Status line: `DONE`, `PARTIAL (what is missing)` or `BLOCKED (why)`.
2. What changed (files).
3. How it was checked (test names, sample run path).
4. Blockers, with the owner decision needed.

## 12. Paste-ready briefs (one per person)

Each person pastes `ContextCon-team-rules\TEAM-AGENT-PROMPT.md` first, then the brief below for their role.

**Person 1 brief:**

```
You are Person 1 (integrator) in MASTER-HANDOFF-supplier.md, sections 5 and 6.
Your files: src/contracts/*, src/intake/*, src/po/*, src/state/*, the orchestrator, tests/e2e*, samples/*, README.md, the demo video.
Your steps: 1 and 7, plus the end-to-end run. Inputs and outputs: section 6.
Acceptance: a sample request runs step 1 to step 7 with no real network call; repeating it creates one PO; screens show only display labels; real names appear only in the internal log.
Do not edit Person 2's or Person 3's files. Do not print or commit any key. Label every simulated item. WhatsApp: team phones only.
Report using section 11.
```

**Person 2 brief:**

```
You are Person 2 (discovery and Crustdata) in MASTER-HANDOFF-supplier.md, sections 5, 6 and 7.
Your files: src/discovery/*, src/crustdata/*, the citation script for the demo, tests/crustdata*.
Your steps: 2, 3 and 4. Discovery is ranked search.query with location filters as hard limits; run company_autocomplete before any industry filter. Verify with identify first (free), then enrich by id (2 credits) for headcount and locations.
Product line: request `basic_info.description` on enrich. If it is empty, mark the check HUMAN_OR_SIMULATED.
Acceptance: fixture run returns labels and citations only on screen data; 429 backs off; 402 and 403 stop with a clear message; live run under 200 credits after checking GET /account/credits.
Do not edit other people's files. Do not print or commit any key. Report using section 11.
```

**Person 3 brief:**

```
You are Person 3 (quotes, policy, WhatsApp, PO retries) in MASTER-HANDOFF-supplier.md, sections 5, 6 and 7.
Your files: src/quotes/*, src/policy/*, src/whatsapp/*, data/simulated/*, tests/failure*, docs/* (diagram).
Your steps: 5a, 5b and 6. Inputs and outputs: section 6. Use display labels only; the policy check may read the _internal fields.
Guards: the WhatsApp module runs only in TEAM_PHONE or SIMULATED mode; a test asserts no call to any other number.
Acceptance: a repeated send with the same key sends once; an over-budget quote goes to the exceptions queue with the reason; the diagram labels simulated steps.
Do not edit Person 1's or Person 2's files. Do not print or commit any key. Report using section 11.
```

---

## 13. Founder path: from idea to MVP (for discussion, not yet decided)

This section is the "why and where" that the build sections assume. Items marked NOT VERIFIED have no source yet.

### 13.1 The idea in one line

Small and mid-size Indian buyers need a regular purchase made. The agent finds vetted suppliers, asks for quotes, applies the buyer's policy, and produces a PO. The buyer does one plain request instead of hours of calls and spreadsheets.

### 13.2 Market check (sourced 6 Nov, research pass; confidence in brackets)

- **Global procurement software:** about $8–10B (2025) and $9–11B (2026), depending on the research firm (Grand View, Fortune BI, and others). Definitions differ; the figure is not a serviceable market for us. [medium]
- **Indian MSMEs:** about 4.72 crore on the Udyam portal (June 2026, secondary source). 7.83 crore+ across Udyam platforms as of 28 Feb 2026 (IBEF, citing government). [medium / high]
- **Late payments to MSMEs:** about ₹8.1 lakh crore stuck in receivables (Economic Survey 2025-26, via Business Standard, Jan 2026). This shows cash pain, not sourcing pain. [high]
- **MSMEs that buy goods regularly:** NOT VERIFIED.
- **MSMEs that struggle to find suppliers:** NOT VERIFIED. This is the core pain; not pursued while the project is demo only.
- **GeM (government buying portal):** only government bodies buy. Private buyers get no supplier discovery there. Seller counts conflict (22 lakh in 2025 vs 62 lakh+ claimed in Feb 2026). [medium]

### 13.3 Competition and price points

- **Coupa:** median about $95,000 a year (Vendr benchmark). [medium]
- **SAP Ariba:** median about $61,500 a year (range $15.5k to $371k). [medium]
- **Jaggaer:** estimated $150k to $650k a year. [medium]
- **Zycus:** contact sales only. Third-party estimates start near $50k a year. [NOT VERIFIED as official]
- **Zoho (ERP with procurement):** ₹999 per user a month, billed annually, minimum 5 users (Zoho's own page); third-party figures conflict. [medium]
- **Small-buyer tools:** OfBusiness is a supplier marketplace; Alvoff is email-first sourcing. Neither is confirmed as doing WhatsApp outreach. [NOT VERIFIED]
- **Read:** the big tools are priced for enterprises. The gap we would test is the small buyer who wants one plain request and WhatsApp follow-up. That gap is a hypothesis, not a finding.

### 13.4 Risks a founder checks first

1. **Willingness to pay:** no source shows what small or mid buyers in India pay for sourcing. Not tested; only relevant if the project becomes real.
2. **WhatsApp policy:** unsolicited B2B supplier outreach and per-message cost are NOT VERIFIED. Read Meta's WhatsApp Business policy and pricing directly before any real outreach.
3. **Data terms:** the Crustdata terms prohibit reselling their data as an enrichment service. A paid product needs a different data source or a licence. This blocks the commercial path as it stands.
4. **Demand evidence:** the sourcing pain itself has no verified figure. Only relevant if the project becomes real.

### 13.5 Path from idea to MVP (proposed order)

| Step | What                                                                                                | Done when                                              | Owner                    |
| ---- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------ |
| 1    | Pick the wedge: one category (industrial sensors), one buyer type, one channel (WhatsApp).          | Decision recorded.                                     | Owner decides            |
| 2    | Build the hackathon MVP: the seven-step flow with simulated supplier replies (sections 4 and 5).    | Demo runs end to end; labels and citations shown.      | Team (sections 5 and 12) |
| 3    | Read Meta's WhatsApp policy and the Crustdata terms with a lawyer or the owner before any real use. | Written note: allowed, not allowed, or needs a change. | Owner                    |
| 4    | **Only if the project becomes real (not planned):** pilot with real buyers and suppliers.           | Not started.                                           | Owner                    |

### 13.6 Decisions for the owner (product direction)

- **Decided (owner, 6 Nov): demo only.** No real business is planned now. The data-terms and WhatsApp-policy checks in section 13.5 step 3 stay on the list in case the plan changes.
- **Demo rules still apply:** Crustdata citations only (option C), WhatsApp to team phones only, no real supplier or buyer contact. These are not optional for a demo either, because the Crustdata terms cover sharing data outside the team.

### 13.7 Where and how to tap (channels, to confirm)

- WhatsApp Business for buyer follow-up, only if the project becomes real and the policy check (step 3) is done.

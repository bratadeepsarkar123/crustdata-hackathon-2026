# ContextCon 04: master handoff, supplier agent

**Status:** active. This replaces the two older research handoffs (kept as history, marked SUPERSEDED).
**Team:** three people. Person 1 is the repo owner (`bratadeepsarkar123`, integrator). Person 2 is `AdityaChittora`. Person 3 is `debugat2am`. Logins are from `TEAMWORK.md`.
**Decisions:** the CTO desk, for the team's owner.

---

## 1. What we are building

A supplier agent for a buyer who needs to buy something regularly. Example: 500 industrial temperature sensors, budget $25,000, delivery in 14 days. The agent reads the request, finds candidate suppliers, checks each company is real with Crustdata, asks suppliers for quotes over WhatsApp, compares the quotes against the buyer's policy, and produces an approved vendor record and a purchase order (PO).

**What is real and what is simulated in the demo:**

- **Real:** the request parsing, the Crustdata company checks, the policy comparison, and WhatsApp messages between the team's own phones.
- **Simulated (labelled SIMULATED everywhere):** supplier replies and quotes, the vendor record, and the PO. No message goes to any real supplier.

Second category, later: footwear (TESSCH; its sole is PU, not rubber or foam).

## 2. Decisions made

| Decision                           | Status                                                                                                                                                                                                                                                            |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Supplier agent over freight        | Chosen. Freight parked.                                                                                                                                                                                                                                           |
| First category: industrial sensors | Chosen. Footwear second.                                                                                                                                                                                                                                          |
| Insurance and sanctions ideas      | Parked.                                                                                                                                                                                                                                                           |
| Repo stays **private** for now     | Owner's choice. Handbook requires public later.                                                                                                                                                                                                                   |
| Crustdata demo rule                | **Option B** (2 of 3 votes): show one example company, 3 to 4 fields, labelled "Source: Crustdata" and the endpoint. No raw JSON, export files, download links or full records. Owner to confirm.                                                                 |
| Supplier contact channel           | **WhatsApp**, not email. Real messages only between the team's own phones (Meta test number, numbers added by the team). Supplier messages are simulated and labelled. Real suppliers need opt-in and approved templates, so they are out of scope for the event. |
| Competitor data                    | Comes only from Teammate B, when he delivers it. The build does not wait for it.                                                                                                                                                                                  |
| Zuric Group                        | Real firm: website zuricgroup.com, based at The Meydan Hotel, Dubai. Procurement services confirmed. Does **not** describe supplier onboarding. Client figures and pricing NOT VERIFIED.                                                                          |

## 3. Hard rules (link, do not copy)

Full rules: `rules.md` and `build-rules.md` in the repo root. These can disqualify us:

- **History:** the repo's commit history starts at 11:00 PM IST, 5 Nov. No backdating. No force-push over a teammate's work.
- **No secrets:** no Crustdata key, model key, WhatsApp token or password in code, commits, issues, chat, screenshots or video. Keys in local environment variables and git-ignored files.
- **No real outreach:** no real message, email, call, booking or payment to anyone outside the team. WhatsApp goes only to team-owned phones.
- **Label simulated items** everywhere: product, demo, README.
- **Cite every fact** (endpoint and field, or document page). Say "I don't know" when unverified.
- **Human only for exceptions:** ask a person only when the answer changes the result.

## 4. The agent, end to end

| #   | Step                         | In                 | Out                                                | Real or simulated                          | Source                                           |
| --- | ---------------------------- | ------------------ | -------------------------------------------------- | ------------------------------------------ | ------------------------------------------------ |
| 1   | Parse the request            | Messy text         | Request (JSON, section 6)                          | Real                                       | Request text                                     |
| 2   | Find candidate suppliers     | Request            | Candidate list                                     | Real (Crustdata)                           | `POST /company/search`                           |
| 3   | Verify each company          | Candidate          | Verified supplier, or NOT VERIFIED                 | Real (Crustdata)                           | `POST /company/identify`, `POST /company/enrich` |
| 4   | Dedupe                       | Candidates         | One record per company, with match confidence      | Real                                       | Domain and name match                            |
| 5a  | **WhatsApp request**         | Verified supplier  | Outbound message log                               | Team phones: real. Supplier: **SIMULATED** | Log file                                         |
| 5b  | **WhatsApp reply and quote** | Reply              | Quote                                              | **SIMULATED** (labelled)                   | Sample data                                      |
| 6   | Compare and apply policy     | Quotes plus policy | Ranked result, exceptions queue                    | Real logic on simulated data               | Policy file (sample, labelled)                   |
| 7   | Vendor record and PO         | Chosen supplier    | Vendor record and PO, each with an idempotency key | **SIMULATED**                              | Key stored before any write                      |

**Human-in-the-loop:** only at step 6 exceptions (no supplier within budget) and step 3 NOT VERIFIED. Exceptions go to a queue with the reason.

**Idempotency:** every write (WhatsApp send, quote, vendor record, PO) gets a unique key, stored before the write and checked before any retry. A crash or retry never sends or creates twice.

## 5. Work split (three people)

Chosen by majority of three advisers (two of three put the policy check with Person 3). The integrator (Person 1) merges. Nobody edits another person's files without asking.

### Person 1: repo owner (`bratadeepsarkar123`). Spine, intake, PO, end-to-end run, video

- **Owns:** `src/contracts/*` (shared JSON shapes, frozen first), `src/intake/*`, `src/po/*`, `src/state/*` (idempotency store), orchestrator, `tests/e2e*`, `samples/*`, `README.md`, demo video.
- **Does:** steps 1 and 7. Runs the whole flow. Owns the end-to-end run, which must pass before 6:30 AM.
- **Starts now:** contracts and fixtures; intake on the three sample requests; idempotency store.
- **Must not touch:** Crustdata client, quotes, WhatsApp module.

### Person 2: `AdityaChittora`. Discovery and Crustdata

- **Owns:** `src/discovery/*`, `src/crustdata/*` (client, retry, rate limits), the demo excerpt script, `tests/crustdata*`.
- **Does:** steps 2, 3 and 4. Runs the one live Crustdata call that confirms the open field paths (section 7).
- **Starts now:** client with headers, 429 backoff, 402/403 stop; dedupe on fixtures.
- **Must not touch:** quotes, WhatsApp, PO.

### Person 3: `debugat2am`. Quotes, policy, WhatsApp, PO retries

- **Owns:** `src/quotes/*`, `src/policy/*`, `src/whatsapp/*` (new; simulated for suppliers, team phones only), `data/simulated/*`, `tests/failure*`, `docs/*` (diagram).
- **Does:** steps 5a, 5b and 6. Checks retries never send twice.
- **Starts now:** simulated quote generator; policy file and scoring formula; WhatsApp log writer.
- **Guards:** the WhatsApp module refuses to run unless mode is set to team-phones or SIMULATED. A test asserts no outbound call to any other number.
- **Must not touch:** Crustdata client, PO writes (Person 1 owns those).

**Integration points, in order:**

1. **IP0, first hour:** Person 1 pushes contracts and fixtures. Everyone pulls.
2. **IP1:** Person 2 pushes discovery output on fixtures. Person 3 consumes it.
3. **IP2, 3:00 AM (due now):** stub end-to-end run through all steps. Person 1 owns it.
4. **IP3:** one live Crustdata run replaces fixtures. Person 2 keeps one excerpt for the demo.
5. **IP4:** idempotency wired into the WhatsApp and PO writes. Person 3's failure tests run against it.
6. **IP5, 6:30 AM:** README, diagram and video frozen. Code freeze at 7:00 AM.

**Shared tests and docs:** each person writes failure tests for their own block. Person 1 writes the README. Person 3 records the video in the last hour. Person 2 checks every Crustdata citation.

## 6. Shared interface contract (JSON shapes)

- **Request:** `{ item, quantity, budget, currency, deadline_days, region, missing_fields[] }`
- **Verified supplier:** `{ name, primary_domain, year_founded, headquarters, headcount_total, industry, sources: [{ field, endpoint }], confidence }`
- **WhatsApp message:** `{ supplier, direction: "outbound" | "inbound", text, idempotency_key, mode: "TEAM_PHONE" | "SIMULATED", label }`
- **Quote (SIMULATED):** `{ supplier, unit_price, lead_time_days, label: "SIMULATED" }`
- **Vendor record and PO (SIMULATED):** `{ idempotency_key, supplier, po_number, total, status, label: "SIMULATED" }`

Person 1 freezes these in `src/contracts/*` first. Changes after that need all three to agree.

## 7. Crustdata reference (verified 2026-11-06)

Source: `CRUSTDATA-CHECK-REPORT.md` (sections 2 to 5, and the follow-up). No keys in that file.

- **Base:** `https://api.crustdata.com`. **Headers:** `authorization: Bearer <KEY>`, `x-api-version: 2025-11-01`.
- **Enabled (12):** `/company/search`, `/company/identify`, `/company/enrich`, `/company/search/autocomplete`, `/person/search`, `/person/enrich`, `/person/search/autocomplete`, `/job/search`, `/social_post/search`, `/agent/query`, `/web/search/live`, `/web/enrich/live`.
- **Not on our account:** `/job/search/autocomplete` (job autocomplete is MCP-only as `job_autocomplete`). All `/batch/...` endpoints. `/person/identify`, `/person/contact/enrich`, and the professional-network live endpoints.
- **Plan-gated fields (403 if requested):** company `technographics`, `social_posts`, `maps`; person `assessment`, `certifications`, `recently_changed_jobs`, `social_posts`, `years_of_experience`, `basic_profile.first_name`, `basic_profile.last_name`.
- **Fields to request:** `locations` (for `locations.headquarters`) and `headcount` (for `headcount.total`).
- **Field names:** the employer filter is `experience.employment_details.current.company_name`. It comes back as `experience.employment_details.current.name`. `current_company` and `current_employer` do not exist.
- **Department:** `basic_profile.normalized_title.department` (person search).
- **Credits:** `GET /account/credits` returns `account.credits`. Check before any batch run. Budget: 15,000 per builder.
- **Costs:** company search 0.03 per result; company identify free; company enrich 2 per match; person search 0.03 per result (0.23 with experience and education); person enrich 1 base plus extras; job search 0.03 per result; autocomplete free.
- **Per-minute limits:** company search 30; company identify 30; company enrich 15; person search 30; person enrich 15; job search 30; autocomplete 300; web search and enrich 10.
- **Gaps (not in Crustdata):** PAN and GSTIN, bank account ownership, ISO and RoHS certifications (plan-gated), signing authority.
- **Still unconfirmed:**
  - LinkedIn ID: no separate field. Closest is `social_handles.professional_network_identifier.profile_url`, which is not filterable.
  - Tenure in months: no field. Closest is `experience.employment_details.current.years_at_company_raw`, not confirmed as months.
  - `metadata.date_added` on jobs: meaning not defined in the schema.
  - Owner-approval items for access: not yet decided.
- **Terms:** no clause mentions demos. Restricted: giving data outside the organisation, sharing export files or download links, selling the data as a database or enrichment service. See section 8.

## 8. Demo rule for Crustdata data

- **Decision:** option B. A small excerpt only: one example company, 3 to 4 fields, labelled "Source: Crustdata" with the endpoint on screen. No raw JSON, no export files, no download links.
- **Why:** the judging rules ask for "where each fact came from" (20 points for facts). The owner's rule is to show data only when it proves a point.
- **Risk:** a judge reads the excerpt as giving data to outsiders. Keep it to one company, keep the source notice visible, never share the file.
- **Fallback:** if the owner wants no values on screen, use field-level citations only (option C).

## 9. Open items

1. **Owner confirms** the demo rule (B) and the three-person split.
2. **Zuric Group:** the owner's "Zurich" is the same firm. Owner to confirm it is the one meant, since its site does not describe onboarding.
3. **Crustdata access:** the Crustdata session says the FDE contact in the handbook is **Ainesh**, not Avinash. Nothing has been sent to the FDE yet. Owner to decide who contacts them and whether to approve the access items.
4. **WhatsApp:** the team creates a Meta test number and adds its three phones to the recipient list. Two facts to check in the Meta dashboard, not in docs: the recipient cap, and how long business verification takes (if needed).
5. **Repo visibility:** stays private for now. Public by the handbook deadline.
6. **Time:** about 3:00 AM now. Freeze at 7:00 AM. Confirm the actual time before using the timeline.
7. **Corrected teammate handoff:** `agent-handoff-corrected.md` has 75 changes plus the Zuric correction. Owner to review.
8. **Teammate B's competitor analysis:** comes only from Teammate B.

## 10. Timeline (handbook; confirm the actual time)

| Time (IST)     | What happens                                              |
| -------------- | --------------------------------------------------------- |
| 3:00 AM        | First end-to-end stub run (IP2).                          |
| 4:30 AM        | One live Crustdata run replaces fixtures (IP3).           |
| 5:30 AM        | Idempotency wired into WhatsApp and PO writes (IP4).      |
| 6:30 AM        | Last call. README, diagram and video frozen (IP5).        |
| 7:00 AM, 6 Nov | **Code freeze.** Repo, video and form due. Hard deadline. |

## 11. Return format for each person

1. Status line: `DONE`, `PARTIAL (what is missing)` or `BLOCKED (why)`.
2. What changed (files).
3. How it was checked (test names, sample run path).
4. Blockers, with the owner decision needed.

## 12. Paste-ready start prompt (for each person's coding agent)

Paste `ContextCon-team-rules\TEAM-AGENT-PROMPT.md` first, then:

```
You are Person [1, 2 or 3] in MASTER-HANDOFF-supplier.md section 5. Your files: [list from section 5]. Your inputs and outputs: section 6. Your acceptance checks: section 4 for your steps. Do not edit other people's files. Do not print or commit any key. Label every simulated item. WhatsApp: team phones only. Report back using section 11.
```

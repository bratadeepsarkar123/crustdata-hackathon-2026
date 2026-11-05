# Crustdata MCP: read this before any Crustdata call

**Who this is for:** every teammate and every AI agent on this team (ContextCon 04).
**What it saves you:** the research and the paid test calls. Do not repeat them. Each builder has their own 15,000 credits (see `rules.md` section 6), so use your own key for your own work.

**Verified:** 2026-11-06 IST, against the live server `https://install.crustdata.com/mcp`, by the repo owner's Claude Code session. Every claim below is marked **verified** (run live, with the result), **plan-blocked** (returns 403 on our key), or **not run** (with the reason). Re-check the free items in section 9 before relying on this for the demo.

---

## 0. Checklist for an agent that is about to use Crustdata

1. Read sections 1, 3 and 4 of this file. Do not start with web searches for Crustdata docs; section 11 lists the sources if you need them.
2. Confirm the connection with `account_credits` (free). A number means you are connected.
3. Choose the call with free tools first: `company_identify`, the `*_autocomplete` tools, `describe_scope`, `account_endpoints`.
4. Write the label line at the top of every script (section 3), dry-run it (free), then run a one-result live test before any larger paid run.
5. Before a paid run bigger than about 10 credits, state the expected cost in the team issue and wait for a yes from a person.
6. Never print, commit, paste or screenshot a Crustdata key or token. The key lives in the MCP sign-in or in environment variables, never in a file in this repo.
7. If Crustdata returns a wrong answer or a misleading error, use the `feedback` tool once for that problem. Do not file 403 (plan), 402 (credits) or 429 (rate limit) as feedback.

---

## 1. Rules that apply (team and Crustdata)

- **Own credits.** Each builder signs up with their own @iitk.ac.in email and gets their own 15,000 credits (`rules.md` section 6). Do not spend another person's key. Section 10 is the record of what was already tested, so nobody needs to test it again.
- **No outreach.** Your agents talk only to your own team and the organisers. Do not send real emails, messages, calls or bookings to people outside the team (`rules.md` section 3).
- **Cite facts.** Every person, company, number and date the product shows must say where it came from. When a fact cannot be checked, say so instead of guessing (`rules.md` section 4).
- **Label simulated actions.** Any simulated quote, booking or payment must be labelled simulated in the product, the demo and the README (`rules.md` section 7).
- **Errors (definitions from the ContextCon 04 Builder Handbook, "When something fails", page 23-24):**
  - **401:** your key is not reaching Crustdata. Copy the key again and send it as `authorization: Bearer YOUR_API_KEY`.
  - **402:** your credits have run out, so a retry will not help. Check the balance with `GET /account/credits` (free), then find the Crustdata team.
  - **403:** this key is not allowed to call that endpoint (or, for MCP, that field). Check the Endpoints page in the dashboard, then find the Crustdata team. Do not retry it.
  - **429:** you are over the limit for that endpoint. Wait a few seconds, retry with a backoff, and read the `x-ratelimit-reset` header for how long to wait.
  - **Who to ask:** the Crustdata team on the floor. The Forward Deployed Engineer is Ainesh. The handbook says to find any Crustdata team member for Crustdata APIs and the MCP server.
- **Robustness.** The judging criteria say the product must never send or pay twice after a crash or retry (`rules.md` section 4). Before re-running any paid step, check whether it already ran (for example, with the stored `upstream_request_id` or a watch's run history).

---

## 2. Connect (Claude Code)

- Endpoint: `https://install.crustdata.com/mcp` (the same for every client).
- Auth: OAuth 2.0 with dynamic client registration. The sign-in opens a browser. Programmatic clients can send `Authorization: Bearer <API key>` instead.
- Claude Code command used here: `claude mcp add --transport http crustdata https://install.crustdata.com/mcp`, then `/mcp` → `crustdata` → sign in. **verified**
- Official docs: https://docs.crustdata.com/for-agents/mcp

---

## 3. How to call it (Code Mode)

Almost all data work goes through one tool, `execute`, which runs a short plain-JavaScript script. The other MCP tools are `get_schema`, `list_tools` and `feedback`.

- **Label comment on the first line.** Every script must start with `// user query: <the user's request>` or `// model query: <what this run does>`. Without it the script is rejected with zero spend.
- **Plain JavaScript only.** No type annotations (`: Type`), no `as`, no generics. A type in the body fails the whole run before anything is billed.
- **One I/O call:** `const r = await callTool('tool_name', { ...params })`. Result: `{ ok: true, data, credits_used, upstream_request_id }` or `{ ok: false, status, errorType, message }`.
- **Always check `r.ok`.** A failed call does not stop the script, so an unchecked failure looks like "no results". `unwrap(await callTool(...))` throws on failure.
- **Await only** `callTool`, `sleep`, `paginate`, `parallelMap`. The query builder and shapers are synchronous.
- **Each `execute` is stateless.** Return the values you need and pass them back as `inputs` in the next call.
- **`dry_run: true` is free but limited.** It catches a missing label, a syntax error, and a missing required path parameter (for example `watch_create` without `dataset`). It does **not** check body field names. A wrong body field only shows up as a live 400. So: dry run, then a one-result live call.
- **Fan out independent work** with `parallelMap` after `chunk(list, 25)`. Do not parallelise cursor pagination or dependent steps. Use `paginate` for cursors.
- **Use `fields` as a whitelist.** Name every group you read (for example `basic_profile`). A group you do not list comes back `undefined`, and naming a plan-blocked field fails the whole call with 403.
- **Parameter names are the tool's own.** Check them with `get_schema(["tool_name"])` before the first live call (section 4 lists the ones verified here).

### Query builder (verified in use)

`eq, ne, lt, lte, gt, gte, in_, nin_, and_, or_, not_, any_of, all_of, has_all, exactToken, excludes, between, geoDistance, chunk`.

- `exactToken(field, "word")` (`[.]`): the literal word or phrase must appear. Use it for brands, products, acronyms, and any keyword in long text (`text`, `content.description`).
- `(.)`: all-words, order-independent, **typo-tolerant** on names and titles (`(.) "founer"` matches "Founder"). It is not a substring match and not regex. It is refused on long text.
- OR: use `any_of(field, [...])`. Do not write `"a|b"`.
- Categorical fields (seniority, function, industry) take exact stored values. Resolve them with the free `*_autocomplete` tools first. A guessed value silently returns 0.
- "Has both X and Y" on the same multi-valued field (two past employers) returns 0 with `and_`. Use the anchor pattern: find the rarer side, collect ids with `paginate`, intersect by `crustdata_person_id`.
- For multi-technology company questions ("Snowflake AND Databricks") use `has_all("technographics.technologies.name", [...])` or `all_of()`, not `and_`.
- Zero results is not proof. For `person_search`, read `r.data.remarks`: `condition_eliminates_all` names the condition that emptied the set.

### Live search vocabulary (different from the database search)

The `*_live` tools take a flat list `[{field, type, value}]` with UPPERCASE types and enum field names such as `CURRENT_COMPANY`, `CURRENT_TITLE`, `PAST_TITLE`, `SCHOOL`, `COMPANY_HEADQUARTERS`, `COMPANY_HEADCOUNT`, `REGION`, `INDUSTRY`. An unknown field returns a 400 that lists the valid names (free). Live search is plan-blocked on our key anyway (section 5).

---

## 4. Tool reference: calls verified on 2026-11-06

Costs are the server's own `credits_used`. Free means 0 credits.

### Free tools

| Tool                                                              | Verified call                                                | Result                                                                                                                                    |
| ----------------------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `account_credits`                                                 | `{}`                                                         | Balance. Reads 15,200 at the start, and 15,225.31 at the end of testing (top-up and recurring wallets). The balance is not a spend meter. |
| `account_endpoints`                                               | `{}`                                                         | 36 endpoints, 12 enabled (list in section 5).                                                                                             |
| `account_usage_events`                                            | `{ limit: 30 }`                                              | Newest-first events with `cost_components` and `upstream_request_id`.                                                                     |
| `account_usage_event`                                             | `{ request_id: "<X-Request-Id>" }`                           | One request. Verified with `abe6d4c7-6e9d-43e2-84f3-094d2f6eeeee` (`person_enrich`, 200, 1 credit).                                       |
| `account_usage_summary`, `account_usage_errors`                   | `{}`                                                         | Totals and grouped errors (verified in the earlier round).                                                                                |
| `company_identify`                                                | `{ names: ["Razorpay"] }` or `{ domains: ["razorpay.com"] }` | Razorpay = `crustdata_company_id` 897127. Stripe (`stripe.com`) = 631394. **One identifier type per call.**                               |
| `company_autocomplete`, `person_autocomplete`, `job_autocomplete` | `(field, query)`                                             | Canonical values. Verified earlier: "Director" for seniority, "Software Development" for industry, "Data Engineer" for job title.         |
| `describe_scope`                                                  | `{ dataset: "person" }`                                      | Broad access on our key (no column restriction). Verified earlier.                                                                        |
| `watch_list`                                                      | `{ dataset: "person" }`                                      | Lists entity watches. Returned 0 after cleanup.                                                                                           |
| `watch_discovery_list`                                            | `{ dataset: "job" }`                                         | Lists discovery watches. Returned 0.                                                                                                      |
| `batch_jobs_list`                                                 | `{}`                                                         | No batch jobs (verified earlier).                                                                                                         |
| `crustdata_docs_search`, `crustdata_docs_fs`                      | `{ query }`                                                  | Docs search (verified earlier).                                                                                                           |

### Searching (charged per result returned)

| Tool                              | Verified call                                                                                                                      | Result and cost                                                                                                                                                                  |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `person_search` (database)        | `filters: eq("experience.employment_details.current.company_id", 631394)`, `limit: 1`, `fields: ["basic_profile"]`                 | Base price only: **0.03 per result**. Verified earlier: 13,554 people at Stripe.                                                                                                 |
| `person_search` with `experience` | same, with `fields: ["basic_profile", "experience"]`                                                                               | **0.23 per result** (base 0.03 + premium 0.1 on each side). Verified: 0.23 for 1 result.                                                                                         |
| `person_search` natural language  | `search: { query: "founder of a fintech payments company in India", mode: "hybrid" }`, `limit: 1`, `fields: ["basic_profile"]`     | **0.03**. Relevance-ordered, no total. Verified.                                                                                                                                 |
| `person_search` count             | `limit: 0`                                                                                                                         | **400**: `'limit' must be at least 1`. To count, use `count: true`, which charges one sample row (0.33 seen earlier). The free count is on `social_post_search` with `limit: 0`. |
| `company_search` natural language | `search: { query: "AI infrastructure for model deployment and monitoring", mode: "hybrid" }`, `limit: 2`, `fields: ["basic_info"]` | **0.06 for 2 companies** (0.03 each). Verified: Perpetuus AI and others returned.                                                                                                |
| `company_search` (database)       | `filters` on `taxonomy.professional_network_industry`, `limit: 2`                                                                  | **0.06 for 2**. Verified earlier (1,267,701 total).                                                                                                                              |
| `job_search`                      | `filters: exactToken("job_details.title", "Data Engineer")`, `limit: 2`                                                            | **0.06 for 2**. Verified earlier (199,637 total).                                                                                                                                |
| `social_post_search`              | `filters: exactToken("text", "hiring")`, `limit: 1`                                                                                | **0.5 per post**. Verified: 1 post for 0.5.                                                                                                                                      |
| `social_post_search` count        | same, `limit: 0`                                                                                                                   | **Free**. Total 36,195,577 (verified earlier).                                                                                                                                   |
| `web_search_live`                 | a query string                                                                                                                     | **1 per query**. Verified earlier: 9 results. Use it for X/Twitter, Reddit and anything outside the datasets.                                                                    |

### Enriching (charged per record returned)

| Tool                                   | Verified call                                                                                                   | Result and cost                                                                                   |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `company_enrich`                       | `crustdata_company_ids: [631394]`, `fields: ["basic_info", "headcount"]`                                        | Stripe, headcount 16,641. **2 credits per returned match.**                                       |
| `company_enrich` with `technographics` | `fields: ["technographics"]`                                                                                    | **403**: `Access denied to fields: technographics`. A gated field fails the whole call.           |
| `person_enrich`                        | `professional_network_profile_urls: ["https://www.linkedin.com/in/williamhgates"]`, `fields: ["basic_profile"]` | **1 credit**, matched.                                                                            |
| `person_enrich` + business email       | same, `fields: ["basic_profile", "contact.business_emails"]`                                                    | **2 credits** total (base 1 + business email 1). Verified.                                        |
| `person_enrich` with `preview: true`   |                                                                                                                 | **400**: `Preview feature is not available for your account`. Not usable on our key.              |
| `web_enrich_live`                      | `urls: ["https://docs.crustdata.com/for-agents/mcp"]`                                                           | **1 credit per page**. Returns the page as **raw HTML** in `content`, so strip the tags yourself. |

### Watches (verified end to end)

Watch rules: preview first (free, creates nothing), show the preview to a person, then create in a later call with the returned `preview_token`. A token only works in the run that minted it.

| Step                    | Verified call                                                                                                                                                                                                                                                                                                                    | Result                                                                                                                     |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Discovery preview (job) | `watch_discovery_create` with `preview: true`, `dataset: "job"`, `filters: exactToken("job_details.title", "Data Engineer")`, `config: { trigger: { type: "interval", every_hours: 24 }, max_results_per_run: 10 }`                                                                                                              | `can_create: true`, `count: 199,637`, a preview token. Nothing created.                                                    |
| Entity preview (person) | `watch_create` with `preview: true`, `dataset: "person"`, `entities: { professional_network_profile_urls: [url] }`, `track: { field: "basic_profile.headline", type: "changed" }`, `fields: ["basic_profile"]`, `config: { trigger: { type: "interval", every_hours: 24 }, max_results_per_run: 10, refresh_frequency_days: 7 }` | `resolved: 1`, a preview token. Nothing created.                                                                           |
| Entity create           | same body, `preview: false`, plus `preview_token` (from the same run's preview)                                                                                                                                                                                                                                                  | Created **watch id 56494**, status `active`. Create cost **0 credits**.                                                    |
| Read                    | `watch_get({ watch_id: 56494 })`                                                                                                                                                                                                                                                                                                 | Status `active`. The parameter is `watch_id`, not `id`.                                                                    |
| Runs                    | `watch_runs({ watch_id: 56494 })`                                                                                                                                                                                                                                                                                                | First run: `SUCCESS`, 1 record searched, 1 matched, 1 new, **0 credits**. The first run is a baseline.                     |
| Cancel                  | `watch_cancel({ watch_id: 56494 })`                                                                                                                                                                                                                                                                                              | Returned 204. A follow-up `watch_get` shows status `cancelled`. **Terminal.** `watch_list` then returned 0 active watches. |

Watch notes: a watch that cannot pay becomes `suspended` silently. A watch left running keeps spending, so cancel test watches as soon as you are done.

### Calls not run, and why

- Discovery watch create, update, test, run summary and run records: not run. There is no link or inline run to read from, and a discovery create would arm a 199k-record backlog. The preview was run instead.
- `watch_preview`, `watch_update`, `watch_test`, `watch_discovery_get`, `watch_discovery_cancel`: not run. Only one entity watch existed and it was cancelled.
- `agent_query`: enabled on the plan (base 2 credits), but **no MCP tool exposes it**. Calling `agent_query` returns "unknown tool". It cannot be used from this MCP.

---

## 5. Plan on our key (as of 2026-11-06)

These are entitlements. Reshaping a request does not change them.

**Enabled (12 endpoints):**
`/agent/query` (no MCP tool, see section 4), `/company/enrich`, `/company/identify`, `/company/search`, `/company/search/autocomplete`, `/job/search`, `/person/enrich`, `/person/search`, `/person/search/autocomplete`, `/social_post/search`, `/web/enrich/live`, `/web/search/live`.

**Plan-blocked (403, free, verified):**

- Person: `person_identify`, `person_contact_enrich` (earlier), `person_enrich_live`, `person_search_live`.
- Company and jobs: `company_search_live`, `job_search_live`.
- Social: `social_post_search_live`, `social_post_list_live`.
- Developer and reviews: `dev_platform_enrich`, `employee_review_enrich`.
- Batch (all 403): `batch_company_enrich`, `batch_person_enrich`, `batch_person_contact_enrich`, `batch_person_identify`, `batch_person_enrich_live`, `batch_person_search`, `batch_company_search`, `batch_job_search`, `batch_person_verify`.
- Batch, not confirmed: `batch_social_post_list_live`, `batch_company_search_live`, `batch_person_search_live`. Each returned a 400 for a validation error before the plan check, so their 403 status is not confirmed. The plan list says disabled.

**Plan-gated response fields** (naming one in `fields` fails the whole call with 403; a gated field inside a requested group comes back empty with no error):

- `person_search`: `years_of_experience`, `years_of_experience_raw`, `basic_profile.first_name`, `basic_profile.last_name`, `contact.last_updated`, `education.last_updated`, and others.
- `person_enrich`: `assessment`, `certifications`, `recently_changed_jobs`, `social_posts`, `basic_profile.last_updated`, `contact.last_updated`, and others.
- `company_enrich`: `technographics` (403 verified), `maps`, `social_posts`, `hiring.recent_openings`, `social_profiles.crunchbase`.
- `company_identify`: `headcount`, `locations`.
- `employee_review_enrich` and `social_post_list_live` have large gated sets. Get the list with `get_schema`.

**Upgrade request** (for the owner, when a gated field blocks a better answer): https://meetings-na2.hubspot.com/chris-pisarski/web-demo-request. Support: support@crustdata.co.

---

## 6. Costs at a glance

- **Free:** every `*_identify`, `*_autocomplete`, `describe_scope`, every `account_*` tool, `watch_list`, `watch_get`, `watch_runs`, `watch_cancel`, every watch preview, `batch_jobs_list`, `batch_job_get`, `batch_results` on a finished job, and `social_post_search` with `limit: 0`.
- **Search:** 0.03 per result base. Adding `experience` or `education` makes it 0.23 per result. Name only the base groups when you do not need them.
- **Enrich:** `person_enrich` 1 base, +1 business email, +2 personal email or phone. `company_enrich` 2 per returned match. A domain or name can match several companies, so identify first and enrich by `crustdata_company_id`.
- **Live web:** `web_search_live` 1 per query, `web_enrich_live` 1 per page.
- **Watches:** create, edit, preview and cancel are free. Each run bills per changed or new record, and a run with nothing new costs nothing.

**Spend record.** This round's per-call credits add up to **4.82** (section 10). The earlier demo's account usage summary showed 2.72. Use the per-call `credits_used` and `credits_remaining`, not the balance.

---

## 7. Gotchas found in testing (this round)

1. **`person_enrich` takes `professional_network_profile_urls` (an array).** The name `crustdata_person_id` is refused with 400: `Exactly one identifier must be provided: professional_network_profile_urls or crustdata_person_ids`.
2. **`person_search` natural-language `mode` is `hybrid`, `lexical` or `semantic`.** `exact` returns 400.
3. **`person_search` `limit` must be at least 1.** `limit: 0` returns 400.
4. **Watch tools use `watch_id`,** not `id`. `watch_create` also needs `dataset` in the body.
5. **`dry_run` does not check body field names.** Make a one-result live call before anything bigger.
6. **`web_enrich_live` returns raw HTML.** Strip the markup before using the text.
7. **A test watch left active keeps running.** Cancel it at once and confirm with `watch_list`.
8. **`company_enrich` with a gated field fails the whole call.** Drop the gated field and re-run (the rest of the call is unaffected if you do).
9. **The balance is not a spend meter.** It rose during testing because of top-up and recurring wallets. Sum `credits_used` instead.

---

## 8. Next actions for the team

1. Each builder: run `account_credits` on your own key to confirm you have your 15,000 credits. Do not use the owner's key.
2. Choose the cheapest path for each question: `company_identify` (free) → `company_enrich` by id (2). For people, `person_search` with base fields (0.03), then `person_enrich` (1) only for the people you keep.
3. For contact details, `person_contact_enrich` is plan-blocked. Use `person_enrich` with `contact.business_emails` (+1) instead.
4. For a watch in the demo: preview, show the preview, create once with the token, read `watch_runs`, then cancel.
5. Put the Crustdata facts you use in the README with their source (the tool name, the call and the date). That is what the judges score under "Facts and verification".
6. Record every paid run in the team issue with its cost, so the team can see the spend.

---

## 9. Re-check quickly (all free)

1. `account_credits`: confirm you are connected and have credits.
2. `account_endpoints`: confirm the 12 endpoints in section 5 are still enabled.
3. `company_identify({ names: ["Razorpay"] })`: expect `crustdata_company_id` 897127.
4. `watch_list({ dataset: "person" })`: expect no active test watches.

---

## 10. Test record (2026-11-06, owner's key, this round)

Paid calls only. Free calls are in section 4. Every credit figure is the server's own `credits_used`. The `upstream_request_id` values are for checking the server's record.

| Call                                  | Credits | upstream_request_id (example)          |
| ------------------------------------- | ------- | -------------------------------------- |
| `web_enrich_live` (1 URL)             | 1       | `a456152d-7ca0-49da-8d3b-978a72602e8e` |
| `social_post_search` (1 post)         | 0.5     | `5147f150-4d17-4f7d-9bdd-26df3af4637a` |
| `person_search` with experience (1)   | 0.23    | `93653c8b-5413-4fa4-966f-d71d614ceab8` |
| `person_enrich` base (1)              | 1       | `abe6d4c7-6e9d-43e2-84f3-094d2f6eeeee` |
| `person_enrich` + business email      | 2       | `522f750a-e457-42ff-9691-0f77e5d037a3` |
| `company_search` natural language (2) | 0.06    | `5001e20a-3947-4123-a609-0fe2dd81b4f3` |
| `person_search` natural language (1)  | 0.03    | `1c4cc407-4e2a-4964-82de-0d5407c85b83` |
| `watch_create` entity (create)        | 0       | `4d6e25a2-84c5-4ca8-9c29-97ed1892b5ca` |
| `watch_runs` (baseline run)           | 0       | `9b13615f-7660-493f-ad7a-5e04a8ad1b41` |
| `watch_cancel`                        | 0       | `aceeaaa9-0e10-4085-b921-c691a0f4f6cd` |

**Total this round: 4.82 credits.** That is the sum of the paid calls above (1.73 + 3.06 + 0.03).

**Plan-blocked (403, free):** `person_enrich_live`, `social_post_search_live`, `batch_company_enrich`, `batch_person_enrich`, `batch_person_contact_enrich`, `batch_person_identify`, `batch_person_enrich_live`, `batch_person_search`, `batch_company_search`, `batch_job_search`, `dev_platform_enrich`, `employee_review_enrich`, `person_identify`, `person_search_live`, `company_search_live`, `job_search_live`, `social_post_list_live`, `batch_person_verify`, `person_contact_enrich`, `company_enrich` with `technographics`.

**Errors that were our own call (free):** wrong `person_enrich` identifier, `person_search` `mode: exact`, `person_search` `limit: 0`, a wrong label name in a test script (`unknown_tool`, twice, before the fix), and `watch_*` calls with `id` instead of `watch_id`. Each is listed in section 7.

---

## 11. Sources

- Official MCP docs: https://docs.crustdata.com/for-agents/mcp
- The live catalog is available as the MCP resource `crustdata://catalog/full` (the Code Mode rules, query builder, shapers, batch jobs, dry runs, costs and watches).
- Tool schemas: `list_tools` and `get_schema(["tool_name"], detail: "summary" | "detailed")` on the live server.
- Team rules: `rules.md` (sections 3, 4, 6 and 7 apply to Crustdata use).
- This file was written from live results, not from the docs alone. Where a doc and a live result disagree, the live result wins, and it is listed above.

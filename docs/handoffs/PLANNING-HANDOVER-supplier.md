# ContextCon 04: planning handover, supplier agent

**Status:** the idea is fixed. Planning is complete. Coding can start.
**Written:** 6 Nov 2026, 3:07 AM IST (time given by the owner). **Code freeze:** 7:00 AM IST, 6 Nov.
**Read with:** `MASTER-HANDOFF-supplier.md` (sectors, JSON shapes, Crustdata reference, timeline). This file does not repeat those sections. Where they differ, this file wins, and the master will be updated to match.

---

## 1. Inputs received

| Input                                                     | Owner                                             | Status                            | What we changed because of it                                                                                  |
| --------------------------------------------------------- | ------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Crustdata check (terms, endpoints, fields, credits)       | Session `claude-7a` (`CRUSTDATA-CHECK-REPORT.md`) | PARTIAL                           | Field names, endpoints and costs are in master section 7. Demo terms still need an owner decision (section 8). |
| Hugging Face "AgenticProcurement" check (two files)       | Teammate A, reviewed by the CTO desk              | Reviewed. Usable with corrections | See section 5.                                                                                                 |
| Competitor workflows (`task2-competitor-workflows.md`)    | Teammate B                                        | DONE, with corrections            | See section 6.                                                                                                 |
| Corrected teammate handoff (`agent-handoff-corrected.md`) | CTO desk                                          | Done. Owner to review             | Master section 9, item 7.                                                                                      |

## 2. Decisions made tonight

Each non-mega decision was put to three cheap advisers with different biases (strict accuracy, speed to freeze, what judges will ask). We acted on the majority. Mega decisions are listed in section 8 for the owner.

| Decision                                            | Options                                                                                                                                                                                                                      | Votes                                  | Result                                                                                                                                                                           |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| How to treat Zuric Group in the competitor analysis | A: note only. B: full row. D: remove entirely                                                                                                                                                                                | Strict: D. Speed: A. Judges: A         | **A.** One note saying it is a human-staffed services firm, using only confirmed facts (services, Dubai, heavy industry). No pricing, no client figures, no workflow comparison. |
| Wording of the market gap in the pitch              | A: "No incumbent does supplier discovery." B: "SAP's Discovery is a posting-based network for its own suppliers. Our agent starts from one plain request and checks each company before any outreach." D: drop the gap claim | Judges-skeptic: B. Speed: B. Judges: B | **B.** Option A is false: SAP Ariba Discovery does supplier discovery.                                                                                                           |
| Price column in the pitch                           | A: keep all with labels. B: keep only prices with an openable primary source, mark the rest "third-party, unverified" or NOT FOUND. D: remove the column                                                                     | Speed: D. Strict: B. Judges: B         | **B.** Prices we cannot source are labelled, not dropped silently. The SAP Ariba fees are labelled unverified until the official SAP page is checked.                            |

Also decided (not votes, only facts): the first and only correct build target is the seven-step flow in master section 4. Freight, insurance and sanctions stay parked.

## 3. The idea, fixed

**One sentence:** a buyer types one plain purchase request, and the agent finds real candidate companies, checks each one with Crustdata, asks the suppliers for quotes over WhatsApp, compares the quotes against the buyer's policy, and produces an approved vendor record and a purchase order.

**Example request:** 500 industrial temperature sensors, budget $25,000, delivery in 14 days.

**Real tonight:**

- request parsing (step 1)
- Crustdata discovery, verification and dedupe (steps 2 to 4), with one live run
- WhatsApp messages between the team's own phones (step 5a, team phones only)
- policy comparison on simulated quotes (step 6)

**Simulated tonight, labelled SIMULATED on every screen:**

- supplier replies and quotes (step 5b)
- the vendor record and the PO (step 7)
- any supplier who is not a team phone

**Not tonight:** real supplier outreach, payments, bank checks, tax IDs (PAN/GSTIN are not in Crustdata), certifications, a second category (footwear comes later), a web UI beyond what the demo needs.

## 4. Workflow and methods

### 4.1 The seven steps (from master section 4)

| #   | Step                     | Input                  | Output                                             | Check a person can run                                                                    |
| --- | ------------------------ | ---------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 1   | Parse the request        | Messy text             | Request JSON                                       | The three sample requests parse; missing fields are listed, not guessed.                  |
| 2   | Find candidates          | Request                | Candidate list                                     | Each candidate has a source call (`POST /company/search`).                                |
| 3   | Verify                   | Candidate              | Verified supplier, or NOT VERIFIED                 | Each verified supplier shows the endpoint and field it came from.                         |
| 4   | Dedupe                   | Candidates             | One record per company, with confidence            | Two sample duplicates collapse into one.                                                  |
| 5a  | WhatsApp request         | Verified supplier      | Message log                                        | Messages go only to the team's listed phones. A test fails if any other number is called. |
| 5b  | WhatsApp reply and quote | Reply (simulated)      | Quote (SIMULATED)                                  | Every quote carries the SIMULATED label.                                                  |
| 6   | Compare and apply policy | Quotes and policy file | Ranked result, exceptions queue                    | A quote over budget goes to the queue with the reason.                                    |
| 7   | Vendor record and PO     | Chosen supplier        | Vendor record and PO, each with an idempotency key | Running the same request twice produces one record, not two.                              |

**Human-in-the-loop:** only at step 6 (no supplier within budget) and step 3 (NOT VERIFIED). Both go to a queue with a plain reason.

### 4.2 Methods (how we build and check)

1. **Fixtures first.** Every step runs on sample files before any live call. This keeps the team unblocked if Crustdata is slow or rate-limited.
2. **One live Crustdata run.** Person 2 runs it once, around 4:30 AM, and keeps one excerpt for the demo. We do not run batches. Check `GET /account/credits` before the run.
3. **Idempotency keys.** Every write (WhatsApp send, quote, vendor record, PO) gets a key, stored before the write and checked before any retry.
4. **Failure tests.** Each person writes tests for their own block: 402 and 403 stop the run, 429 backs off, timeouts retry with the same key, duplicate sends are blocked.
5. **Labels.** Simulated items carry SIMULATED on the screen, in the JSON (`label`) and in the README.
6. **Citations.** Every Crustdata fact shows its endpoint and field. If a field is not confirmed, the screen says so.
7. **Freeze rule.** At 6:30 AM no new feature starts. Only fixes, README and video.

### 4.3 Who does what

Sectors, owners, files and must-not-touch rules: **master section 5, unchanged.** Person 1 integrates and owns the end-to-end run. Person 2 owns Crustdata. Person 3 owns quotes, policy, WhatsApp and the video's last hour.

Integration checkpoints: IP0 (contracts frozen, first hour), IP2 (stub end-to-end, 3:00 AM), IP3 (live Crustdata, 4:30 AM), IP4 (idempotency wired, 5:30 AM), IP5 (README, diagram and video frozen, 6:30 AM), freeze (7:00 AM).

## 5. What we take from the Hugging Face demo

Source: the two research files in `crustdata-hackathon-2026` (untracked, not committed).

**Take:**

- A small tool-based agent layout, with each step as a tool.
- The multi-supplier split display and its radar chart. It is easy to read on screen.
- The honest labelling of the mocked SAP step.

**Do not take:**

- The synthetic supplier generator, the mock PO, or the PPO label. The code uses a hand-written formula as its default (`GlobalMockPPO`). The trained model's use at run time is not shown.

**Corrections to the two research files (fix before anyone quotes them):**

1. **Budget total is wrong.** The files say the example PO totals $51,845.20. Recalculated from their own table: **$51,189.17**. The conclusion holds: about 105% over the $25,000 budget.
2. **"PPO" is overstated.** Say "a hand-written weighted score with a softmax split".
3. **The agent run was never tested.** Only the Python functions were run. Whether the LLM-driven five-step run works is unknown.
4. **"Missing 85%"** has no source. Do not use it.
5. **Licence:** "MIT" comes from the Space metadata. No LICENSE file was quoted. Treat as unverified until checked.
6. **Inference (label it as such):** the six scores are close (0.82 to 0.91), so the split is nearly even (14% to 18% each). The "optimisation" barely chooses between suppliers. Do not present this as a feature of ours.

## 6. Competitive position (corrected)

Source: `task2-competitor-workflows.md`, with corrections.

**What the teammate got right:** Icertis, Coupa, SAP Ariba, Zycus, ServiceNow, JAGGAER, Ivalua, Zoho and GEP are mostly used after a supplier is already chosen. Their workflows start at an invitation or a request form. Bank checks, legal review and final sign-off stay manual in all of them.

**What must change before the pitch:**

1. **"None of these tools find suppliers" is wrong.** SAP Ariba Discovery, now SAP Business Network Discovery, does supplier discovery. Buyers post a need and matched suppliers on the network respond. Source: sap.com and blog.sap-press.com (seen in search results only; the pages were not opened tonight, so re-open sap.com before the pitch). Use the wording in section 2.
2. **The other vendors' discovery features are unchecked.** Do not claim anything about Coupa, Zycus, JAGGAER, Ivalua, ServiceNow, Zoho or GEP discovery until someone opens their pages.
3. **Weak citations.** Several cited links are generic homepages (ariba.com, zoho.com, ivalua.com, jaggaer.com, docs.servicenow.com). One does not match its claim (a Gates Foundation homepage cited as a Coupa onboarding guide). One finifi.io page is cited for Newgen. Mark these as unverified.
4. **Ariba fees** ($50, $750, $2,250, $5,500 a year): several secondary sources agree, but none is SAP's official page. Label "third-party, unverified".
5. **Price column:** keep only prices with an openable primary source. Everything else is labelled or NOT FOUND (decision in section 2).
6. **Zuric Group:** one note only (decision in section 2).
7. **Icertis:** the teammate says "ICARIS" is an unrelated UK grants platform. Accept as the teammate's claim.

**Judge question to prepare for:** "Why not SAP Ariba?" Answer in one line: Ariba's discovery posts to suppliers already on its network, and it does not start from one plain request. We check each company with Crustdata before any outreach. Show this in the video.

## 7. Demo plan (about 2 minutes, one take if possible)

1. **The request** (10 s): type the sensor request in plain words.
2. **Candidates** (20 s): the company list, with "Source: Crustdata" and the endpoint on screen.
3. **One verified company** (20 s): one excerpt, three or four fields, source shown. Option C (citations only, no company values on screen), per the owner's decision.
4. **WhatsApp** (25 s): messages to the team's phones (real). Supplier replies appear with a SIMULATED label.
5. **Comparison and policy** (25 s): ranked quotes, one out of budget, sent to the exceptions queue with its reason.
6. **Vendor record and PO** (15 s): both marked SIMULATED. Run the same request twice and show one record, not two (idempotency).
7. **Close** (15 s): the honest line. Real: discovery, checks, messages to our phones, policy. Simulated: suppliers, quotes, vendor record, PO. Then the Ariba answer from section 6.

Person 3 records the video in the last hour. Person 1 writes the README with the same labels.

## 8. Risks and owner decisions

### 8.1 One message for the owner (mega decision)

**Decision: the Crustdata demo rule.** Options:

- **B:** show one company with three or four fields, labelled "Source: Crustdata". This is the current plan.
- **C:** show only field-level citations, with no values on screen.

**Recommendation: C.** Crustdata's data-export terms restrict giving the data to anyone outside the organisation. Judges are outside. The video is also public. C is safer. The risk: the demo looks less convincing, because judges see no values.

_(If the owner picks B, keep one company, keep the source notice visible, and never share the file.)_

### 8.2 Other owner items (not mega, but need a person)

- **FDE contact.** The handbook names Ainesh, not Avinash. Owner decides who contacts them and whether to approve the Crustdata access items.
- **Team split.** Confirm the three-person split in master section 5.
- **Time.** Confirm the actual time before using the timeline.
- **WhatsApp.** Check the Meta dashboard for the recipient cap and whether business verification is needed.
- **Corrected teammate handoff.** Owner to review `agent-handoff-corrected.md`.

### 8.3 Technical risks

| Risk                                     | Plan                                                                                                     |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Crustdata rate limit or credit drain     | Fixtures first. One live run. Check credits before the run. Stop on 402 or 403.                          |
| WhatsApp messages sent to a wrong number | Guard in code: refuse unless mode is TEAM_PHONE or SIMULATED. A test asserts no other number is called.  |
| Duplicate PO or vendor record on retry   | Idempotency key stored before each write. Failure test runs the same request twice.                      |
| Judge attacks the "Ariba gap"            | Use the section 6 wording. Show the check in the video.                                                  |
| Judge attacks an unsourced price         | Price labelled or removed (section 2).                                                                   |
| Time runs out                            | Freeze rule at 6:30 AM. If the live run has not passed, the demo runs on fixtures and says so on screen. |

## 9. Return format (unchanged)

Each person reports: status line (`DONE`, `PARTIAL (what is missing)` or `BLOCKED (why)`), files changed, how it was checked, and blockers with the owner decision needed. Use master section 11.

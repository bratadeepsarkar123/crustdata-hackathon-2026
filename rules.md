# ContextCon 04 (IIT Kanpur) — Team Rules

Source: the official ContextCon 04 Builder Handbook (Thursday 5 to Friday 6 November 2026, DJAC 206, IIT Kanpur). If this file and the handbook ever disagree, the handbook wins. Check the WhatsApp group for updates.

## 1. Timing (IST)

| Time                   | What happens                                                                            |
| ---------------------- | --------------------------------------------------------------------------------------- |
| Before 11:00 PM, 5 Nov | Planning, sketches, accounts, first Crustdata call. **No code in the submission repo.** |
| 11:00 PM, 5 Nov        | Building begins. The repo's commit history must start here.                             |
| 3:00 AM                | Optional mentor checkpoint.                                                             |
| 6:30 AM                | Last call. Aim to have the README and demo video nearly done.                           |
| 7:00 AM, 6 Nov         | **Code freeze.** Repo, demo video and form are due. Hard deadline.                      |
| 8:00 AM                | Breakfast, demos to watch, People's Choice voting.                                      |
| 8:30 AM                | Ten finalists announced. Finals at 8:45 AM (2-minute demo + 1 minute of questions).     |
| 9:20 AM                | Winners announced.                                                                      |

## 2. The repository rules (these can disqualify us)

- The repo must be **new** and its commit history must **start at 11:00 PM on 5 November**. Anything committed earlier does not count, and an earlier history can make the entry ineligible.
- Do **not** backdate or edit commit timestamps. Commit honestly, as the work happens.
- The repo must be **public** so judges can open it.
- Commit as you go, so judges can see how the product came together.
- Keep notes as you build: what you tried and what worked. These notes are the heart of the demo.
- A README is required in the repo (see section 5).

## 3. Event rules

- Build with any model, framework or tool. Open-source libraries and AI coding tools are allowed.
- Crustdata is encouraged, not mandatory. Every project is judged on the same criteria.
- **Keep your agents in the room.** During the event, your agents talk only to your own team and to the organisers, never to real people outside the team. Do not send real emails, messages, calls, bookings or payments to outside people or companies.
- Be kind. Help each other. If anything makes someone uncomfortable, tell the Techkriti team.
- Team size: up to 4 people, or solo. Each member signs up with their **own** @iitk.ac.in email and gets their own credits.

## 4. Judging (what the judges score)

| Criterion                 | Points | What it means for us                                                                                                                                                                        |
| ------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| End-to-end execution      | 25     | A real request goes in and a finished result comes out. The product asks a person only when the answer changes the result.                                                                  |
| Facts and verification    | 20     | Every person, company, number and date is right for the day it is used. Each decision cites its reasons and sources. When a fact can't be checked, the product says so instead of guessing. |
| Robustness and edge cases | 20     | Handles messy text, missing fields, a tool that times out, nonsense output. After a crash or retry it continues and **never sends or pays twice**.                                          |
| Customer value and idea   | 20     | A job businesses pay for today, with a non-obvious approach. More than a chat interface on a model.                                                                                         |
| Demo and understanding    | 15     | The demo is clear to anyone in the room. We can explain approaches weighed, what worked, what didn't, the hardest case, and what comes next.                                                |

Ties go to End-to-end execution, then Facts and verification.

## 5. Submission

**Before pressing submit (all must be true):**

- [ ] Repo is public, and its commit history starts at 11:00 PM on 5 November.
- [ ] README is in the repo.
- [ ] Demo video is one link (not a folder), two minutes, and plays in a private window. Loom, unlisted YouTube or Google Drive (anyone with the link).
- [ ] Diagram link opens for anyone.
- [ ] Every member's name and email match the YC event registration, and everyone used their @iitk.ac.in address for credits.

**Form fields:** team name (same every time), one-line job description, theme (or own idea), GitHub repo link, demo video link, how the product works (the service it replaces, what it does today, engineering approach, models used, what's next), high-level diagram link, and one page per member (name and email as on YC registration, IIT Kanpur email, roll number, personal email, GitHub username).

**README should cover:** the service (who does the job today and who pays for it), what it does now (start to finish, and where a person is still needed), what it could do next and why not now, how to run it, how it's built (agents, models, tools, data, where it calls Crustdata, where state lives), and the approaches tried (what worked and what didn't).

**Demo video (2 minutes):** start with the request going in, end with the finished work coming out, show where each fact came from, one sentence of intro. If possible show a duplicate record, a changed fact, or a failed call.

- One person submits for the whole team. You may resubmit until 7:00 AM; the latest submission counts.
- The video matters: judges pick the ten finalists from submissions. If we reach the finals, the video is also our backup on stage.

## 6. Crustdata usage

- Sign-up: app.crustdata.com with the @iitk.ac.in email, promo code **CONTEXTCON-IITK** (under "Have a promo code?"). Redeem on app.crustdata.com/billing/credits if signed up without it.
- Each builder gets **15,000 credits**. Check balance with `GET /account/credits` (free).
- Base URL https://api.crustdata.com with headers `authorization: Bearer <KEY>` and `x-api-version: 2025-11-01`.
- MCP server: https://install.crustdata.com/mcp (Claude Code: `claude mcp add --transport http crustdata https://install.crustdata.com/mcp`).
- Default per-endpoint limits (per minute): Person Search 30, Person Enrich 15, Company Search 30, Company Identify 30, Company Enrich 15, Job Search 30, Web Search and Fetch 10, Watcher 10. Each key also has 200 requests/minute across all endpoints. Plans may differ.
- Error handling: 401 → re-copy the key; 402 → out of credits, stop retrying and check the balance; 403 → endpoint not allowed for this key; 429 → wait (`x-ratelimit-reset` header) and retry with backoff.
- **Never** print, commit, paste into chat, or put in a screenshot a Crustdata key or any other credential.

## 7. Safety and honesty

- Simulated inputs or actions (sample rulebooks, quotes, bookings, payments) must be **labelled as simulated** in the product, the demo and the README. Never present a simulated transaction as a real one.
- Facts from Crustdata are treated as trustworthy for this event, but the product should still cite where each fact came from.
- Do not attack the event's systems or anyone else's. Do not scrape beyond what the APIs and public pages allow.
- Do not share team credentials or keys outside the team.

## 8. Team coordination (once the repo exists)

- Agree on one service, its user, a concrete request and the finished outcome before splitting the build. Record it in a GitHub issue.
- One GitHub issue per task with owner, scope, acceptance checks and status.
- Short-lived branches from an up-to-date `main`. Small pull requests. The integrator reviews and merges.
- Integrate early: aim for a first end-to-end run well before 3:00 AM.
- Reserve time at the end for a full rehearsal, the video and the submission check.

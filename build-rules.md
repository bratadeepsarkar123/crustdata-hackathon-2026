# Build Rules — for every coding agent on the ContextCon 04 team

Read this together with `rules.md`. These rules apply to any AI coding agent working in the submission repo (Claude Code, Codex, or any other tool).

## Before you write any code

1. Check the time. Application coding starts at **11:00 PM IST on 5 November 2026**. Do not create commits in the submission repo before then.
2. Read the repo's `README.md`, `TEAMWORK.md` and open GitHub issues. Work only on the task you were given, with the file ownership stated in its issue.
3. Never print, commit or paste secrets (Crustdata keys, model keys, tokens). Keep them in local environment variables and make sure they are git-ignored before creating any file that holds them.

## How to build

- **One request first.** Get one realistic request running end to end before adding breadth. Then harden it.
- **Idempotency is mandatory.** Every action that sends, books, pays or writes a record must have a unique key, be recorded before it happens, and be checked before it is retried. A crash or retry must never send or pay twice.
- **Cite every fact.** Each claim in a decision carries its source (API endpoint and field, URL, document page). Store where each fact came from.
- **Say "I don't know".** If a fact cannot be verified, the output says so. Never fill a gap with a guess.
- **Dedupe entities.** One person or company under two names stays one record. Record the match and its confidence.
- **Human only for exceptions.** Ask a person only when the answer changes the result. Route exceptions to a queue with the reason.
- **Handle failures.** Timeouts, empty results, malformed responses, 429s and 402s must each have a defined behaviour. Test them.
- **Keep the agent in the room.** No real outreach outside the team. Any email, call, booking or payment goes to a sandbox or is clearly simulated and labelled.

## Crustdata calls

- Look up exact filter values with the autocomplete endpoints before filtering.
- Respect the per-endpoint limits in `rules.md` section 6. Add retry with backoff on 429. Stop retrying on 402 and 403.
- Check the credit balance (`GET /account/credits`) before any batch run.
- Prefer cheap calls (Company Identify) before expensive ones (Enrich), and cache results within a run.

## Commits and notes

- Commit small and often, with clear messages, so the judges can see the build's history.
- Keep `NOTES.md` (or the README's "approaches" section) current: what you tried, what worked, what did not, and why you chose this approach. Judges score this.
- Never rewrite, squash-away or backdate commit history. Never force-push over a teammate's work.

## Testing and proof

- Add at least one test or script that runs the end-to-end request and checks the output against the acceptance checks in the issue.
- Keep a sample run's output in the repo so the demo and README can point at real evidence.
- Test the hardest case you know of, and one failure case (timeout or missing field), before 3:00 AM.

## Before the 7:00 AM freeze

- [ ] Repo is public and history starts at 11:00 PM.
- [ ] README complete, including how to run it and what it does not do yet.
- [ ] Diagram link is public.
- [ ] Demo video recorded (two minutes) and plays in a private window.
- [ ] No secrets in the repo, the history, the README or the video.
- [ ] Every simulated input or action is labelled as simulated.

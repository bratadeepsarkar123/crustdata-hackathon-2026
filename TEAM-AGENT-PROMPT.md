# Prompt for your teammates' agents

Copy everything inside the box below and paste it as the first message to your coding agent (Claude Code, Codex or similar), inside your team's ContextCon repo checkout.

```
Before you do anything else, read these two rule files and follow them for this whole session:

1. rules.md — ContextCon 04 event rules, judging criteria, submission checklist and Crustdata usage.
2. build-rules.md — how to build: idempotent actions, cited facts, human only for exceptions, no real outreach, honest commits.

If the files are not in this repo, download them from the team's shared link (or ask a teammate) and place them in the repo root before you continue.

Then:
- Check the current time. Do not create commits in the submission repo before 11:00 PM IST on 5 November 2026.
- Read README.md, TEAMWORK.md and the open GitHub issues. Work only on the task assigned to you in its issue, and only on the files that issue gives you.
- Never print, commit, or paste any API key or token. If you need a Crustdata key, read it from a local environment variable and confirm the file that holds it is git-ignored.
- Before any build step, state the acceptance checks for your task and how you will verify them.
- Keep NOTES.md updated with what you tried, what worked, what did not, and why.

Report back: what you changed, how you checked it, and any blocker.
```

Notes for the team:

- Paste it once per session. Re-paste it if the agent starts a new chat.
- Keep the rule files in the repo root so every teammate's agent reads the same rules.

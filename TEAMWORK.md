# Team coordination

ContextCon 04: IIT Kanpur — building begins at 11:00 PM on November 5. The repository and a two-minute demo video are due by 7:00 AM on November 6, IST. Follow any updated instructions from the organizers.

## Working together

- Choose one service, its user, a concrete request, and the finished outcome before splitting the build. Record the decision and acceptance checks in a GitHub issue.
- Use GitHub Issues as the shared task list. Each task should state its owner, scope, acceptance checks, and current status; flag blockers in the issue. Keep decisions and important links there so they are visible to the whole team.
- `bratadeepsarkar123` is the initial integrator; the team can agree on a different person. The integrator coordinates shared interfaces, configuration and dependencies, reviews changes, and keeps `main` ready to run.
- Create a short-lived branch from an up-to-date `main` for each task, for example `feat/issue-12-intake` or `fix/issue-15-errors`. Work on separate files where possible; agree on ownership before changing shared files.
- Open a small pull request when a task is ready. Include what changed, how it was checked, and any remaining blockers. The integrator reviews and merges after checks pass. Coordinate conflicts with the relevant file owner; do not force-push or reset shared work.
- Give each coding agent a focused task, file ownership, constraints and acceptance checks. Avoid concurrent edits to the same files, and have the task owner review the diff and run the relevant checks.

## Access and credentials

- All three teammates need their own GitHub access and local checkout. The repository owner has admin access; `AdityaChittora` and `debugat2am` have write access.
- Event API and model credentials are pending. Keep keys out of the repository, shared issues, screenshots and chat; use local or deployment environment variables when the team has them. This repository does not yet configure ignored environment files, so check before creating any secret files.
- During the Crustdata walkthrough, confirm how each key is issued, which endpoints and fields it permits, rate limits, credit balance and how to get support. Do not paste keys into documentation.

## Checkpoints

- Aim for a first end-to-end run early, then integrate continuously instead of leaving integration until the deadline.
- Reserve time for a full rehearsal, the two-minute recording, and confirming the repository and video submission before 7:00 AM. Make the demo clearly show the finished result and its evidence.

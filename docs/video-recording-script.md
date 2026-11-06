# Two-minute demo video: recording script (LIVE path)

This replaces the offline script in `demo-architecture-and-script.md`. The offline replay is not used in the video. The video shows a live Crustdata company search, run from your own terminal with your own key.

## Before you hit record (about 3 minutes)

Open PowerShell and run these lines one at a time. Type the key yourself. Do not paste it into chat.

```powershell
cd C:\Users\brata\Downloads\claude\crustdata-hackathon-2026
git checkout feat/live-one-item-demo
$env:CRUSTDATA_API_KEY = "<paste your Crustdata key here>"
node src/demo/live-one-item.cjs --help
```

Expected: the usage text starts with `Live one-item sourcing search (Crustdata).`

Check the key is set without printing it:

```powershell
if ($env:CRUSTDATA_API_KEY) { "key is set" } else { "key is NOT set" }
```

Expected: `key is set`. If it says NOT set, set the key again in the same window (the `$env:` setting lasts only for this window, so do not close it).

Clear the screen (`cls`), enlarge the font, and start the recording.

## Terminal commands for the recording

Run this exact command on camera:

```powershell
node src/demo/live-one-item.cjs --query "sintered neodymium magnet manufacturer" --limit 5
```

Expected screen (from a live run on 2026-11-06, about 0.15 credits):

```
ONE-ITEM SOURCING DEMO (LIVE)
Search: sintered neodymium magnet manufacturer

Shortlist:
  Supplier 1: They are producing customized Neodymium Magnets, Magnetic separations (magnetic tubes and magnetic grids) and magnetic couplings.
    cited: basic_info.description [LIVE Crustdata POST /company/search; self-reported]
  Supplier 2: description withheld (no sentence free of name, location, size or link)
    cited: basic_info.description [LIVE Crustdata POST /company/search; self-reported]
  Supplier 3: description withheld (no sentence free of name, location, size or link)
    cited: basic_info.description [LIVE Crustdata POST /company/search; self-reported]
  Supplier 4: description withheld (no sentence free of name, location, size or link)
    cited: basic_info.description [LIVE Crustdata POST /company/search; self-reported]

Still not verified: minimum order size, sole-source status, thin 3 mm capability.
LIVE - descriptions are self-reported by each company. No company contacted, no email sent.
```

Your results may differ slightly, since the search is live. The labels, the withheld lines and the closing lines must match.

If the call fails, the script prints the reason and exits. Read the message on screen and say it out loud. Examples:

- `HTTP 401` means the key is wrong. Re-set the key and run again.
- `HTTP 402` means the account has run out of credits. Top up before recording.
- `could not reach Crustdata` means there is no internet. Do not fake a result. Say the live call failed and stop.

## Two-minute script

| Time      | On screen                                            | Say (plain words)                                                                                                                                      |
| --------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 0:00–0:15 | Title card, then the terminal                        | "A buyer needs a special part, and finding a supplier is slow. This tool searches a live company database for suppliers."                              |
| 0:15–0:30 | Type the command, press Enter                        | "I'm asking for makers of sintered neodymium magnets. This is a real search on Crustdata right now."                                                   |
| 0:30–1:00 | The Supplier lines                                   | "Each supplier gets a label. We show only the company's own product sentence. If that sentence reveals a name, a place, a year or a size, we hide it." |
| 1:00–1:20 | The `cited:` lines                                   | "Every line says where it came from: a live Crustdata search, self-reported by the company."                                                           |
| 1:20–1:40 | The "Still not verified" lines                       | "We do not claim what we have not checked. Minimum order, sole-source status and thin-part capability are still open."                                 |
| 1:40–2:00 | The last line: "No company contacted, no email sent" | "Nothing is sent to any company. This is the search step only. Next steps need a human decision."                                                      |

## Editing notes

- Record the screen and voice separately if you can. Keep the voice-over to the table lines.
- Cut any pause longer than two seconds. Keep the Enter-key moment, because it proves the search is live.
- Add a short end card: "Live search. Self-reported data. No supplier contacted."
- Do not show the key window or the `$env:` line in the final cut. Trim the start of the recording so it begins after the key is set.

## Credits and cost

One five-result search costs about 0.15 Crustdata credits. The balance was about 15,205 at 2026-11-06 06:30.

## Desk notes (for the CTO desk, not on camera)

- The desk also ran one live search through the Crustdata connector for the video. That run used the same query and returned the same four descriptions. Its output is the basis of the expected screen above.
- The live script is on branch `feat/live-one-item-demo`, local only, not pushed. Its tests: 21 pass, including the one-item demo suite.

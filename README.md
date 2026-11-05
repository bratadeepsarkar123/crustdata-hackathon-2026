# ContextCon supplier agent — offline demo

This is an offline hackathon prototype for a buyer-side supplier sourcing agent. The intended service would help a small or midsize industrial buyer find a supplier, compare a quote with a purchase policy, and prepare a purchase order. Today that work is commonly handled with vendor lists, spreadsheets, and calls or messages; this is a product hypothesis, not validated customer research. The expected user is a procurement or operations lead, and the buyer's business would pay if the service proves useful. Willingness to pay has not been tested.

## What runs today

The demo accepts exact fabricated request texts from `samples/requests.cjs`. The local intake parser turns them into the shared Request shape and checks each result against its expected output. Only the first request has a complete step 1–7 fixture and can create simulated vendor and PO records. The other two sample texts are parsed and tested, but this harness rejects them before any write because they do not have a matching full-flow fixture; the Kanpur request also has an unresolved delivery deadline.

| Stage | Current behavior |
| --- | --- |
| 1. Parse request | Local parser code runs against a `SIMULATED` sample request. Missing fields stay null and stop the PO flow. |
| 2. Find candidates | Prerecorded fictional supplier fixture; no Crustdata call. |
| 3. Verify companies | Prerecorded fixture citations only; no company values are shown. |
| 4. Dedupe | The fixture supplies neutral supplier labels; no live dedupe service runs. |
| 5a. Request a quote | Marked `SIMULATED`; no message is sent. |
| 5b. Receive quotes | Prerecorded simulated quotes with explicit currency metadata. |
| 6. Apply policy | A clearly `SIMULATED` fixture decision stands in for the policy module. The real policy module is not called by this harness. |
| 7. Write vendor and PO | A local simulated writer persists separate idempotency records before each record write. Repeating the same request reuses the same vendor and PO records. |

Every fixture output is labelled `SIMULATED`. Supplier cards show a neutral label such as “Supplier 1” and field/endpoint citations marked as a simulated fixture source. They never show supplier names, domains, locations, headcount, or other company values. The quote record keeps the shared section-6 shape; an outer display wrapper supplies its currency and simulated source. The writer rejects a missing quote currency or one that differs from the request currency. Vendor and PO records keep the shared shape; outer display wrappers show their currency and `SIMULATED local writer` source.

## Run it

Requirements: modern Node.js with CommonJS support. There are no third-party runtime dependencies and no API keys or other credentials are needed.

```powershell
node src/orchestrator.cjs
```

The command prints sanitized JSON. The first-run example is checked in at [`samples/sample-run.json`](samples/sample-run.json). Idempotency state is stored under the OS temporary directory at `contextcon-supplier-agent/offline-fixture-state`, so repeating the command reuses the same keys and reports `EXISTS` for both writes. To isolate a run, pass a state directory that is a child of the OS temporary directory:

```powershell
node src/orchestrator.cjs "$env:TEMP\contextcon-supplier-agent\demo-run"
```

The orchestrator rejects state paths outside the temporary directory. It accepts only exact sample request text, verifies parser output against the expected request, and creates no vendor or PO records for unresolved requests, unsafe or mismatched fixtures, an unapproved policy decision, or a quote currency mismatch.

## Tests

Run each component suite or the combined set:

```powershell
node --test src/intake/request-reader.test.cjs
node --test src/state/idempotency.test.cjs
node --test src/po/writer.test.cjs
node --test tests/e2e.cjs
node --test src/intake/request-reader.test.cjs src/state/idempotency.test.cjs src/po/writer.test.cjs tests/e2e.cjs
```

The end-to-end suite covers all three sample parses, the offline step 1–7 run, repeated idempotent writes, missing/ambiguous/mismatched requests, failed policy and quote gates, quote currency checks, supplier-value privacy, citation injection, and blocked network functions.

## How it is built

The code uses plain Node.js CommonJS. Intake parses local sample text. The orchestrator reads fixture data for stages 2–6 and calls the local PO writer for stage 7. The writer keeps idempotency state as files under the OS temporary directory; its records contain only the section-6 neutral labels and fields. Supplier names and values are not emitted to the screen or written to the PO state. No model is used in this offline harness.

There are no Crustdata calls in this version. The citation field names and endpoint paths identify where live facts would come from in a future integration, but each current citation explicitly says `SIMULATED fixture; no live Crustdata call`. WhatsApp is not connected and no message is sent.

## Approaches tried and next steps

Exact sample-text matching plus a comparison with expected parser output worked for a dependable offline demonstration and prevents the harness from guessing at unrecognized requests. It intentionally supports only these samples; broader messy-request handling is not claimed. Allowlisted citation fields and endpoints keep arbitrary values and URL query strings out of the display projection. The shared quote shape has no currency field, so an explicit per-supplier currency map sits beside the unchanged quote records and the writer refuses to create records unless the chosen quote currency matches the request currency.

The next integration would replace fixture candidate discovery and verification with the team's separately owned discovery module, then connect the real policy module. Any later messaging demo must remain limited to team phones and requires owner direction; this offline run sends nothing. Unresolved or exception cases currently stop with a clear rejection and no PO rather than opening a human exception queue. Live supplier outreach, bookings, payments, and production use are out of scope. A real-data path requires a separate owner decision and data, messaging, and policy review.

No secrets are configured or needed. Do not add keys or local credentials to this repository. Code commits or pushes require explicit direction from the repository owner.

# Agent Handoff: Autonomous Source-to-Onboard Procurement System (CORRECTED)

> Corrected Markdown copy of "Agent handoff.pdf". The PDF was not modified. Endpoints and field names follow the verified Crustdata facts (Crustdata check report, 2026-11-06). Unverified claims are labelled. A Change log is at the end.
>
> **Labels used in this file**
>
> - **SIMULATED**: an invented example value, not real data.
> - **vendor claim, not independently verified**: a figure published by Icertis or taken from an Icertis case study. Not checked.
> - **NOT VERIFIED**: a claim, field name, or behaviour that was not confirmed.
> - **OWNER DECISION**: a question the terms do not answer. The owner must decide it.

| Field          | Value                                                                                                                                                                                                                                                          |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Document Type  | Strategic Research & Architecture Dossier                                                                                                                                                                                                                      |
| Prepared For   | Teammate / Parallel Planning Agent (ContextCon 04)                                                                                                                                                                                                             |
| Core Objective | Provide a self-contained analysis of Zuric Group (Supplier Sourcing) and Icertis (Supplier Onboarding & Contract Lifecycle Management) so the autonomous procurement agent can be designed, scoped, and built without researching either company from scratch. |

**Name note.** The sourcing firm is called "Zuric Group" in the PDF and in team documents. The owner calls it "Zurich". This file keeps the PDF's spelling "Zuric Group" so that the source stays traceable.

**Correction (2026-11-06, after a site check).** An earlier search found no record of Zuric Group. That was wrong: the firm has a website, https://zuricgroup.com/procurement-services/, which describes it as an integrated sourcing and procurement company based at The Meydan Hotel, Dubai. Confirmed from the site: procurement services (Dedicated Procurement Desk, RFQ Management, Project Procurement, Backlog Clearance, Sourcing-as-a-Service) and four-step workflows. Not on the site: pricing, named clients, case studies, certifications, and any supplier-onboarding service. The site says the client keeps "policies, vendor approval, purchase orders and final commercial decisions". So the PDF's claim that Zuric does onboarding is NOT VERIFIED, and its client figures stay NOT VERIFIED.

---

## Executive Summary: The Opportunity

In enterprise business operations, buying goods or services from a third party consists of two distinct halves. They are handled by different human teams and by disconnected software platforms.

1. **Sourcing (finding who to buy from):** Handled by specialized outsourced procurement firms such as Zuric Group. Human buyers take technical specifications, search global markets, solicit Request for Quotation (RFQ) bids, level quotes side-by-side, and make an award recommendation. _(Role of Zuric Group: NOT VERIFIED, see Part 1.)_
2. **Onboarding (making the supplier usable in ERP):** Handled by enterprise Contract Lifecycle Management (CLM) platforms such as Icertis. Procurement operations and legal staff collect compliance documents, verify corporate identity, authenticate signatories, negotiate terms against company policy, and create the active vendor record in ERP systems (SAP, Coupa). _(Icertis role: vendor claim, not independently verified.)_

### The Enterprise Bottleneck

- Even with Icertis, onboarding takes **weeks**, because platforms only manage internal PDFs and text. They cannot autonomously investigate external corporate reality or verify humans. **NOT VERIFIED** (duration and cause).
- Even with Zuric, sourcing stops at a spreadsheet comparison. The client must still work out how to onboard the vendor. **NOT VERIFIED.**
- **The Agent Solution:** By combining Sourcing + Onboarding into a single autonomous pipeline backed by Crustdata, the agent takes a raw purchase request, autonomously screens suppliers, levels quotes, conducts live due diligence (entity validity, headcount stability, signatory employment), self-heals missing vendor data, and outputs an approved **ERP Golden Vendor Record + Purchase Order (PO)**. _(Design proposal. Feasibility depends on the Crustdata gaps in Part 4.0 and the owner decision in Part 4.4.)_

---

## Part 1: Deep Dive on Zuric Group (Supplier Sourcing)

**Status of this whole Part: NOT VERIFIED.** A web search on 2026-11-06 for Zurich and Zuric procurement firms in Dubai and elsewhere found no company profile matching this description. Every claim below comes from the teammate's brief and must be confirmed with the owner before it is used in a demo or a customer-facing document.

### 1.1 Company Overview & Market Positioning

- **Entity:** Zuric Group (operating as Zuric Procurement). **NOT VERIFIED.**
- **Headquarters & Hubs:** Meydan Hotel, Nad Al Sheba, Dubai, UAE; operational sourcing networks in the Asia-Pacific region (India, China). **NOT VERIFIED.**
- **Core Positioning: Procurement-as-a-Service (PaaS).** They act as an _outsourced purchasing department_ for companies whose internal procurement teams are overwhelmed or lack domain expertise in heavy industrial equipment. **NOT VERIFIED.**
- **Sectors Served:** Heavy asset industries: Oil & Gas, Power Generation, Desalination & Water Treatment, EPC (Engineering, Procurement, Construction), Offshore Marine, and Advanced Manufacturing. **NOT VERIFIED.**
- **Hardware Specialization:** Industrial valves (control, cryogenic, ball), motion actuators, positive displacement pumps, rupture disks, and hard-to-find Original Equipment Manufacturer (OEM) critical spares. **NOT VERIFIED.**

### 1.2 Business & Revenue Model

- **Engagement Model:** Co-managed / extended capacity. Zuric does not take ownership of the inventory. They do the sourcing diligence, while the client retains final approval, budget sign-off, and PO issuance. **NOT VERIFIED.**
- **Pricing Structure:** **NOT VERIFIED** for both items below.
  1. **Retainer / Service Fees:** Fixed monthly or project-based fee for dedicated buyer capacity (clearing backlogs, running RFQ campaigns).
  2. **Cost-Plus / Transparent Sourcing Margin:** For one-off spot procurement of emergency OEM spares, Zuric provides open-book cost comparisons and charges a pre-agreed management fee or margin.
- **Value Proposition:** Cost reduction, access to global OEM distributor networks, and prevention of multi-million-dollar plant shutdowns caused by missing parts. **NOT VERIFIED.**

### 1.3 Human Team & Operational Roles

**NOT VERIFIED.** Inside Zuric Group, a procurement campaign involves multiple human roles:

- **Technical Buyer / Sourcing Specialist:** Understands engineering part numbers, ASME/API/ISO standards, material grades, and operating tolerances.
- **RFQ Coordinator:** Maintains supplier directories, emails RFQ packages, and chases suppliers for bid responses.
- **Commercial Analyst:** Normalizes quotes into comparison sheets, calculating total landed cost (factoring currency, freight, customs duties, Incoterms, and payment terms).
- **Expeditor / Logistics Coordinator:** Tracks manufacturing lead times and monitors factory delivery schedules.

### 1.4 Step-by-Step Zuric Workflow

**NOT VERIFIED** as Zuric's own process. This is the teammate's generic sourcing model.

1. Purchase Request Intake (part number, specs, quantity, budget)
2. Technical Spec Review (identify standards, tolerances, lead-time limit)
3. Supplier Longlisting (search OEM directories, distributors, regional stockists)
4. RFQ Distribution (send RFQ packet to 3-5 qualified candidates)
5. Bid Leveling & Quote Normalization (align pricing, Incoterms, MOQ, delivery dates)
6. Commercial Award Memo (recommend winning supplier with rationale)
7. Handoff to Client (client must now handle onboarding and ERP setup)

### 1.5 Data Inputs & Outputs in Sourcing

- **Inputs:**
  - Bill of Materials (BOM) or Part Specification Sheet (e.g., "500 IP67 Industrial Temperature Sensors"). **SIMULATED** example.
  - Target lead time (e.g., "< 14 days"). **SIMULATED** example.
  - Budget ceiling / target price.
  - Delivery location / Incoterms requirement (e.g., DDP, FOB).
- **Outputs:**
  - **Bid Comparison Matrix:** Side-by-side table of suppliers, unit costs, total price, lead time, warranty, and MOQ.
  - **Sourcing Award Recommendation:** Summary document stating which vendor won and why (e.g., best balance of price and delivery certainty).

### 1.6 Key Pain Points & Where Zuric Fails

**NOT VERIFIED.**

1. **High Manual Cost:** Sourcing relies entirely on human phone calls, emails, and spreadsheet wrangling.
2. **Speed Lag:** Manual RFQ collection and comparison takes days or weeks.
3. **The Sourcing Handoff Chasm:** Once Zuric picks the winner, their job is done. The client's internal team must now spend another 3-4 weeks vetting and onboarding that vendor before a single dollar can be paid or an order placed. **NOT VERIFIED** (the 3-4 week figure).

---

## Part 2: Deep Dive on Icertis & Mercedes-Benz (Supplier Onboarding)

**Source status for Part 2:** Figures attributed to Icertis or to its Mercedes-Benz case study are **vendor claim, not independently verified**. Pricing and fee ranges are **NOT VERIFIED**. The teammate did not cite sources for any figure in this Part.

### 2.1 Company Overview & Market Positioning

- **Entity:** Icertis.
- **Flagship Platform:** Icertis Contract Intelligence (ICI), hosted on Microsoft Azure. _(Azure hosting: NOT VERIFIED. Product name: vendor claim, not independently verified.)_
- **Market Position:** The undisputed global leader in enterprise Contract Lifecycle Management (CLM), serving Global 2000 enterprises (Mercedes-Benz, Microsoft, Johnson & Johnson, Cognizant, Sanofi). **vendor claim, not independently verified.** ("Undisputed global leader" is a marketing statement and is not a verifiable fact.)
- **Core Offering:** End-to-end contract creation, automated compliance and obligation tracking, supplier onboarding management, and integration with core ERPs (SAP Ariba, Coupa, Microsoft Dynamics 365). **vendor claim, not independently verified.**

### 2.2 Business & Revenue Model

- **Enterprise SaaS (Annual Recurring Revenue / ARR):** Multi-year contracts (typically 3-5 years). **NOT VERIFIED.**
- **Pricing Architecture:** **NOT VERIFIED** for every item below.
  - **Base Platform License:** $100,000 to $300,000+/year base subscription.
  - **Volume & Entity Scaling:** Prices scale up based on active contract volume and number of enterprise subsidiaries/jurisdictions.
  - **User Tiers:** Differentiates between Power Users (legal/procurement authors) and Casual Users (approvers).
  - **Modular Add-ons:** Vera AI, Risk Assessment Copilot, and ERP connectors are billed as premium additions.
- **Professional Services & Implementation:** High-friction setup requiring Big-4 consultancies (PwC, Deloitte, Accenture) or Icertis specialists. First-year implementation fees typically range from $150,000 to over $1,000,000. **NOT VERIFIED.**

### 2.3 The Mercedes-Benz Case Study: Metrics & Reality

All figures in this section are **vendor claim, not independently verified** (they come from the Icertis-side case study; the teammate gave no independent source).

- **Scale:** Over 500,000 suppliers worldwide, managed by 6,000 internal buyers.
- **Historical Problem:** Daimler/Mercedes had 25-year-old, fragmented procurement systems. Onboarding a single new supplier took an average of 6 weeks of manual back-and-forth across email, paper forms, and regional databases.
- **Solution:** Deployed Icertis Contract Intelligence globally in 5 months.
- **Proven Business Results:**
  - **83% Cycle Time Reduction:** Onboarding time dropped from 6 weeks down to 1 week.
  - **Standardized Multi-Tier ESG Compliance:** Mercedes piloted smart contracts and blockchain tracking to ensure tier-1 and sub-tier suppliers adhered to strict carbon reduction, labor rights, and business ethics standards.
  - **Recognition:** Mercedes awarded Icertis a top award in supplier innovation.

### 2.4 Human Team & Operational Roles

**NOT VERIFIED** (role model written by the teammate, not sourced). In a corporate procurement team using Icertis, the human actors are:

- **Procurement Operations (ProcOps):** Sends onboarding intake forms and monitors supplier completion.
- **Compliance & Risk Analyst:** Manages due diligence questionnaires, checks sanctions lists, and verifies Certificates of Insurance (COI).
- **Legal Counsel:** Reviews contract redlines, indemnification clauses, and deviations from standard terms.
- **Vendor Master Data Administrator:** Manually verifies banking details and enters the approved vendor record into SAP/Oracle/Coupa.

### 2.5 Step-by-Step Icertis Workflow

**NOT VERIFIED** as a description of Icertis's product. Product step names are the teammate's model.

1. Supplier Intake Invitation (buyer invites supplier to portal)
2. Form & Document Upload (supplier uploads tax W-9, bank info, insurance, profile)
3. Contract Drafting (generate standard MSA / NDA from clause library)
4. Negotiation & Redlining (Vera Copilot assists human lawyer with suggestions) _(Vera Copilot: vendor claim, not independently verified)_
5. Approval Hierarchy Routing (Legal, Finance, InfoSec sign off)
6. E-Signature (DocuSign / Adobe Sign) **NOT VERIFIED**
7. ERP Master Record Creation (push vendor record into SAP Ariba or Coupa) **NOT VERIFIED**
8. Obligation Management (track ongoing ESG, audits, renewals)

### 2.6 Where Icertis Stops (The Automation Gap)

**NOT VERIFIED** (these are the teammate's claims about Icertis's limits. The enterprise cost figure is also NOT VERIFIED.)

Even after spending $500,000+ on Icertis, enterprises still experience severe friction:

1. **Icertis Is Blind to the External World:** It has no connection to live corporate registries, LinkedIn, or external company data. If a vendor enters a fake address or claims 500 employees when they have 2, Icertis accepts it.
2. **Signatories Are Never Authenticated:** Icertis cannot verify if the contact person signing the agreement is an authorized corporate officer or a random sales contractor.
3. **Inability to Self-Heal:** If a vendor omits a field (e.g., industry code, headquarters location, corporate registration number), the workflow freezes for days until a human analyst notices and sends an email.
4. **Copilot, Not Autonomous Agent:** Icertis Vera is an interactive chatbot waiting for a human to ask questions. It does not run end-to-end tasks on its own. **NOT VERIFIED.**

---

## Part 3: The Unified Product: Autonomous "Source-to-Onboard" Procurement Agent

By unifying Zuric's sourcing engine with Icertis's onboarding/compliance engine, the agent provides a complete **Source-to-Onboard** pipeline. _(Design proposal.)_

The original PDF shows a flow diagram on this page. It is not reproduced in this Markdown. The flow in text form:

1. Buyer inputs: Supplier Quotes (RFQ bids), Purchase Request (specs, qty, budget), Company Policy (rules, KYC).
2. Phase 1, Sourcing Discovery and Spec Matching: Crustdata Company Search (identify candidates) → Bid Leveling Engine (normalize price, lead time) → Award Decision (select winner with reason).
3. Phase 2, Onboarding and Due Diligence: Crustdata Identify & Canonicalize (resolve Golden Record entity) → Crustdata Company Search (headcount stability, trends, location) → Crustdata Person Search (verify signatory employment) → Policy Engine & Safeguards (PO decision, exception queue).
4. Phase 3, Terminal Outputs: Sourcing Award Memo; Vendor Onboarding Record (ERP-ready, cited data); ERP Golden Vendor Record; Simulated Purchase Order (PO).

---

## Part 4: Crustdata Integration Architecture

### 4.0 Base URL, headers, enabled endpoints, and what Crustdata does not provide

- **Base URL:** `https://api.crustdata.com`
- **Headers on every call:** `authorization: Bearer <KEY>` and `x-api-version: 2025-11-01`. (Added in this correction. The PDF did not list them.)
- **Enabled on our key (12, checked live with the free `account_endpoints` call, 2026-11-06):**
  - POST /agent/query
  - POST /company/enrich
  - POST /company/identify
  - POST /company/search
  - POST /company/search/autocomplete
  - POST /job/search
  - POST /person/enrich
  - POST /person/search
  - POST /person/search/autocomplete
  - POST /social_post/search
  - POST /web/enrich/live
  - POST /web/search/live
- **Job autocomplete is MCP-only.** `/job/search/autocomplete` does NOT exist on our account and is not used in this design. Job autocomplete is available only as the MCP tool `job_autocomplete`. It is not a REST call and is not on any endpoint list in this file.
- **Not available to a builder key (plan gate, 403 or disabled).** The agent must not call these:
  - Person: /person/contact/enrich, /person/identify, /person/professional_network/enrich/live, /person/professional_network/search/live
  - Company and jobs: /company/professional_network/search/live, /job/professional_network/search/live
  - Social posts: /social_post/professional_network/enrich/live, /social_post/professional_network/search/live
  - Developer and reviews: /dev_platform/enrich, /employee_review/enrich
  - Batch (all disabled): /batch/company/enrich, /batch/company/search, /batch/company/professional_network/search/live, /batch/job/search, /batch/job/professional_network/search/live, /batch/person/contact/enrich, /batch/person/enrich, /batch/person/identify, /batch/person/search, /batch/person/verify, /batch/person/professional_network/enrich/live, /batch/person/professional_network/search/live, /batch/social_post/professional_network/enrich/live
  - Autocomplete: /professional_network/search/autocomplete (disabled)
- **Plan-gated fields (named in `fields`, the call fails with 403):**
  - company_enrich: `technographics`, `social_posts`, `maps`
  - person_enrich: `assessment`, `certifications`, `recently_changed_jobs`, `social_posts`
  - person_search: `years_of_experience`, `years_of_experience_raw`, `basic_profile.first_name`, `basic_profile.last_name`
- **Fields need to be listed to come back:**
  - `locations.headquarters` comes back only if `locations` is listed in `fields`.
  - `headcount.total` comes back only if `headcount` is listed in `fields`.

**Crustdata does NOT provide these. The agent must handle them through another source or mark them "I don't know":**

- PAN / GSTIN tax IDs
- Bank account ownership
- ISO / RoHS certifications (person_enrich `certifications` is plan-gated on our key, so this gap stands)
- Signing authority (Crustdata shows current employment, not whether a person may sign)

Because of these gaps, the claim "every step maps directly to Crustdata" in the original PDF is replaced by the table below, which marks each gap.

### 4.1 Workflow-to-API mapping (corrected)

| Workflow Step                | What the Agent Does                                                                                                    | Crustdata API Call                                             | Exact Fields Used                                                                                                                                                                                                                                                                                                                                                                          |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1. Sourcing Discovery        | Find vendors matching product category & location                                                                      | POST /company/search                                           | taxonomy.professional_network_industry (filter; was "industries"), headcount.total (was "company size"; list `headcount` in fields), locations.headquarters (filter; was "headquarters"; list `locations` in fields)                                                                                                                                                                       |
| 2. Entity Normalization      | Resolve messy vendor name into canonical record                                                                        | POST /company/search/autocomplete, then POST /company/identify | basic_info.name (was "company name"), basic_info.primary_domain (was "domain"), linkedin_id **NOT VERIFIED** (not in the verified field list)                                                                                                                                                                                                                                              |
| 3. Operational Due Diligence | Verify operating reality & employee growth                                                                             | POST /company/enrich                                           | headcount.total (was "employee_count"; list `headcount` in fields), basic_info.year_founded. headcount trajectory and growth_metrics **NOT VERIFIED** (no verified field name)                                                                                                                                                                                                             |
| 4. Signatory Authentication  | Verify that the quote submitter is currently employed by the vendor. Signing authority is NOT covered (Crustdata gap). | POST /person/search, POST /person/enrich                       | Filter: experience.employment_details.current.company_name (was "current_company" / "current_employer"; those two names do NOT exist). Read: experience.employment_details.current.name, **exact read path TO CONFIRM ON A LIVE CALL** (the response treats `current` as an array). Title: experience.employment_details.current[].title (was "job title"). tenure_months **NOT VERIFIED** |
| 5. Operational Pulse         | Check if vendor is actively hiring/operating                                                                           | POST /job/search                                               | job_details.title (was "job_title"), metadata.date_added (filterable; was "posting date"; meaning as a posting date **NOT VERIFIED**), department **NOT VERIFIED**                                                                                                                                                                                                                         |
| 6. Credit Budgeting          | Pre-run balance check to prevent out-of-credit failure                                                                 | GET /account/credits                                           | credits remaining field name **NOT VERIFIED**. The "402 out-of-credit" behaviour **NOT VERIFIED**.                                                                                                                                                                                                                                                                                         |

### 4.2 Credit cost and rate limits per call

Source: `account_endpoints` (base_credits, effective_rate_limit_rpm) and the tool descriptions from `get_schema`, checked 2026-11-06. Copied from the check report.

| Endpoint                                     | Base cost            | Per-minute limit | Notes                                                                              |
| -------------------------------------------- | -------------------- | ---------------- | ---------------------------------------------------------------------------------- |
| `POST /company/search`                       | 0.03 per result      | 30               | +premium per filtered or returned premium group                                    |
| `POST /company/identify`                     | free                 | 30               | One identifier type per call                                                       |
| `POST /company/enrich`                       | 2 per returned match | 15               | +2 per match with `technographics` (2 to 4 per match)                              |
| `POST /person/search`                        | 0.03 per result      | 30               | 0.23 per result with `experience` and `education` (default when `fields` is empty) |
| `POST /person/enrich`                        | 1 base               | 15               | +1 business email, +2 personal email, +2 phone, +1 dev profile (cap 7)             |
| `POST /job/search`                           | 0.03 per result      | 30               |                                                                                    |
| `POST /social_post/search`                   | 0.5 per post         | not listed       | `limit: 0` is free and returns the total                                           |
| `POST /web/search/live`                      | 1 per query          | 10               |                                                                                    |
| `POST /web/enrich/live`                      | 1 per page           | 10               | Returns raw HTML                                                                   |
| `POST /agent/query`                          | 2                    | not listed       | Enabled, but no MCP tool exposes it                                                |
| Autocomplete (company, person)               | free                 | 300              |                                                                                    |
| `GET /account/credits`, `/account/endpoints` | free                 | not checked      |                                                                                    |

Watch cost (from `account_endpoints`, per run): entity watches cost 5 to 150 by freshness (30 days down to 1 day); discovery watches cost 0.5 to 150 for person and job, and 2 to 150 for company and social post.

Rate limits confirmed: person search 30, person enrich 15, company search 30, company identify 30, company enrich 15, job search 30; autocomplete 300 for company and person. Job autocomplete: not confirmed (no REST path). Credits: not checked. The MCP reports no separate limit, and the MCP's application of the 200-per-minute key limit is NOT VERIFIED.

### 4.3 Field-name corrections confirmed by the check

- `current_company` and `current_employer` do NOT exist. Filter with `experience.employment_details.current.company_name`. Read the returned name as `experience.employment_details.current.name` (listed as a filter alias in the schema). **Exact read path TO CONFIRM ON A LIVE CALL.**
- `experience.employment_details.current[].title`: the title field. The report confirms the `current` array form for name and title. The read path for the name is the same open item.
- `basic_info.primary_domain`, `basic_info.year_founded`, `taxonomy.professional_network_industry` (company search filter), `job_details.title` (job search), `metadata.date_added` (job search, filterable): correct per the check.
- `locations.headquarters`: filterable on company search. Returned under the `locations` group, so `locations` must be listed in `fields`.
- `headcount.total`: correct. `headcount` must be listed in `fields`.

### 4.4 Demo and terms: OWNER DECISION (not answered by the terms)

**OWNER DECISION. The terms do not answer whether a live demo may show Crustdata data to judges.** No clause in the terms mentions demos, presentations, or hackathons. This file does not state that a live demo is allowed or banned.

Clauses that bear on the question. Quotes come from page fetches on 2026-11-06 and must be checked against the live pages before they are relied on in writing:

- Data-export terms (https://app.crustdata.com/terms/data-export):
  - Section 1 (licence): "share it with employees and contractors who work for you under confidentiality obligations"
  - Section 3, item 1: "Sell, rent, sublicense, publish, or give the Data to anyone outside your organisation, in whole or in part, in any form."
  - Section 3, item 2: "Offer the Data, or a product built on it, as a database, list, directory, or enrichment service" and "or use it to build a product that competes with Crustdata."
  - Section 3, item 3: "Use the Data to train or fine-tune a machine-learning model that reproduces or substitutes for the Data."
  - Section 3, item 4: "Remove or hide any notice that identifies Crustdata as the source."
  - Section 3, item 6: "Share an export file or its download link with anyone outside your organisation."
  - Section 5, item 2: "A download link lasts one hour, and anyone who holds the link during that hour can download the file."
- Website terms (https://www.crustdata.com/terms): "Permission is granted to use the materials for creating derivative works." and "Transfer the materials to another person or "mirror" the materials on any other server." The page does not address demos, sharing outputs, or API keys.

Facts for the owner's decision (not a ruling):

1. Showing results on screen is not clearly banned. Handing judges export files, download links, or raw data is restricted.
2. Keep the Crustdata source notice visible on every screen that shows its data.
3. The product must not be a database, list, directory, or enrichment service sold on top of the data. A product that uses Crustdata to answer one question for a user is a different case.
4. Do not commit data dumps to the repo or share them in the team channel.

### 4.5 Workflow-to-API summary used by Module B

See Part 7. Only the enabled endpoints in 4.0 are called. Job autocomplete is not called over REST.

---

## Part 5: Implementation Blueprints & Schemas

### 5.1 Input Schema: Purchase Request & Policy

**SIMULATED:** every value in this block is an invented example.

```json
{
  "request_id": "PR-2026-8812",
  "category": "Industrial IoT Sensors",
  "specifications": "IP67 rated, -40C to 85C operating temp, Modbus RTU interface",
  "quantity": 500,
  "budget_ceiling_usd": 25000,
  "required_delivery_days": 14,
  "company_policy": {
    "min_vendor_headcount": 10,
    "require_active_business": true,
    "require_verified_signatory": true,
    "allowed_payment_terms": ["Net 30", "Net 45", "Net 60"],
    "required_certifications": ["ISO 9001", "RoHS"]
  }
}
```

Note: "required_certifications" cannot be checked with Crustdata (ISO / RoHS gap, Part 4.0). Those checks need another source.

### 5.2 Input Schema: Candidate Supplier Quotes (Simulated Bids)

**SIMULATED:** every value in this block is invented, including vendor names, domains, contacts, prices, and headcounts.

```json
[
  {
    "quote_id": "Q-V101",
    "vendor_name": "Apex Sensor Systems",
    "vendor_domain": "apexsensors.com",
    "contact_name": "Sarah Jenkins",
    "contact_title": "Director of Commercial Sales",
    "unit_price_usd": 42.0,
    "total_price_usd": 21000.0,
    "lead_time_days": 10,
    "payment_terms": "Net 30",
    "warranty_months": 24,
    "claimed_headcount": 65
  },
  {
    "quote_id": "Q-V102",
    "vendor_name": "Ghost Tech Solutions",
    "vendor_domain": "ghosttech-fake.io",
    "contact_name": "Fake Name",
    "contact_title": "CEO",
    "unit_price_usd": 25.0,
    "total_price_usd": 12500.0,
    "lead_time_days": 5,
    "payment_terms": "Advance 100%",
    "warranty_months": 12,
    "claimed_headcount": 150
  }
]
```

### 5.3 Output Schema: The Golden Vendor Master Record (ERP-Ready)

**SIMULATED:** every value in this block is an invented example, including the timestamp, the company details, the headcounts, the signatory, and the PO. Only the endpoint and field names in the citations are real (see Part 4). The signatory read path is TO CONFIRM ON A LIVE CALL.

```json
{
  "idempotency_key": "VEND-ONBOARD-a7f4e92b3c1d",
  "vendor_status": "APPROVED",
  "onboarding_timestamp": "2026-11-06T01:30:00Z",
  "entity_details": {
    "canonical_name": "Apex Sensor Systems Inc.",
    "domain": "apexsensors.com",
    "hq_address": "Austin, Texas, United States",
    "industry": "Industrial Automation & Measuring Instruments",
    "citations": {
      "canonical_name": {
        "source": "Crustdata POST /company/identify",
        "field": "basic_info.name"
      },
      "hq_address": {
        "source": "Crustdata POST /company/enrich",
        "field": "locations.headquarters"
      }
    }
  },
  "operational_verification": {
    "verified_headcount": 58,
    "claimed_headcount": 65,
    "discrepancy_delta": -7,
    "headcount_trend": "+12% over 12 months (Stable Growth)",
    "headcount_trend_status": "NOT VERIFIED (no confirmed Crustdata field for trend)",
    "verification_status": "PASS",
    "citation": {
      "source": "Crustdata POST /company/enrich",
      "field": "headcount.total"
    }
  },
  "signatory_verification": {
    "signatory_name": "Sarah Jenkins",
    "signatory_title": "Director of Commercial Sales",
    "is_current_employee": true,
    "verification_status": "PASS (current employment only)",
    "signing_authority_status": "NOT VERIFIED (Crustdata gap)",
    "citation": {
      "source": "Crustdata POST /person/search",
      "field": "experience.employment_details.current.name",
      "field_status": "TO CONFIRM ON A LIVE CALL (read path)"
    }
  },
  "policy_compliance_evaluation": {
    "min_headcount_check": "PASS (58 >= 10)",
    "payment_terms_check": "PASS (Net 30 allowed)",
    "certifications_check": "NOT VERIFIED (ISO 9001 / RoHS gap, Crustdata does not provide)",
    "tax_id_check": "I don't know (PAN / GSTIN gap, Crustdata does not provide)",
    "overall_verdict": "ELIGIBLE_FOR_IMMEDIATE_PO (conditional on certifications and tax ID being confirmed from another source)"
  },
  "purchase_order": {
    "po_number": "PO-2026-9901-SIMULATED",
    "vendor_id": "VEND-ONBOARD-a7f4e92b3c1d",
    "line_items": [
      {
        "description": "Industrial Temperature Sensors (IP67)",
        "quantity": 500,
        "unit_price": 42.0,
        "total": 21000.0
      }
    ],
    "terms": "Net 30",
    "simulation_label": "SIMULATED TRANSACTION - CONTEXTCON 04 HACKATHON"
  }
}
```

---

## Part 6: How This Wins Every Rubric Category

_(Scoring rationale written by the teammate. Items marked NOT VERIFIED are claims that must be tested before they are presented as fact.)_

| Rubric Area             | Max Pts | Why This Scores 100%                                                                                                                                                                                                                                                                                                                                    |
| ----------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| End-to-End Execution    | 25      | A purchase request and candidate bids go in → live Crustdata verification runs → bid leveling occurs → a complete ERP-ready Golden Record and Purchase Order come out. The product asks a human only when an actual policy violation or fraud risk occurs.                                                                                              |
| Facts & Verification    | 20      | Every single fact (headcount, address, executive tenure) cites its API source (endpoint, field, timestamp). If insurance or tax ID is missing, the output explicitly marks "I don't know" rather than guessing. Note: tax IDs and certifications are not provided by Crustdata (Part 4.0). "Executive tenure" is **NOT VERIFIED** as a Crustdata field. |
| Robustness & Edge Cases | 20      | **Idempotent:** keyed by hash(request_id + vendor_domain). Repeated execution never duplicates a PO or vendor record. Handles 429 rate limits with exponential backoff **NOT VERIFIED** (rate-limit behaviour not confirmed), checks credit balance (GET /account/credits), and catches fraudulent quotes (e.g. ghost companies).                       |
| Customer Value          | 20      | Solves the $100k+ human labor cost of outsourced procurement desks (Zuric) **NOT VERIFIED**, and closes the 4-week onboarding delay that software like Icertis still leaves behind **NOT VERIFIED**.                                                                                                                                                    |
| 2-Minute Demo           | 15      | Extremely visual: shows the purchase request → live bid comparison → Crustdata live validation → catching a fake vendor → auto-generating the Golden Record and PO. Demo data must be labelled SIMULATED. **Whether live Crustdata results can be shown to judges: OWNER DECISION (Part 4.4).**                                                         |

---

## Part 7: Recommended Development Split for the Team

Once the team gives the green light, we recommend splitting the build into 3 distinct modules. _(The three-module split is still valid after the corrections above.)_

1. **Module A: Sourcing & Bid Leveling Engine (`sourcing_engine.py`):**
   - Ingests purchase request specifications and candidate quotes.
   - Evaluates unit price, lead time, warranty, and Incoterms into a weighted score matrix.
   - Outputs the Sourcing Award Memo.
2. **Module B: Crustdata Verification & Onboarding Client (`crustdata_onboarding.py`):**
   - Connects only to the enabled endpoints in Part 4.0: POST /company/search, POST /company/search/autocomplete, POST /company/identify, POST /company/enrich, POST /person/search, POST /person/enrich, POST /job/search, GET /account/credits (credit checks). Uses caching and the rate limits in Part 4.2.
   - Never calls the not-available endpoints in Part 4.0 (including all batch endpoints).
   - Runs canonical entity identify → company enrich → person search for the signatory.
   - Computes discrepancies between claimed and verified data.
   - Flags every field that Crustdata does not provide (Part 4.0) instead of guessing.
3. **Module C: Policy Evaluation, Idempotent Master Record & PO Generator (`vendor_master.py`):**
   - Compares enriched facts against company policy rules.
   - Emits the Golden Vendor Master Record with citations.
   - Generates the simulated Purchase Order (PO) with an idempotency key.
   - Routes failures to an Exception Queue.

---

## Change log

Format: was / now / reason. Each line is one change.

1. was: POST /screener/company/search / now: POST /company/search / reason: wrong path; verified endpoint is /company/search (Part 4.1, row 1).
2. was: GET /autocomplete / now: POST /company/search/autocomplete / reason: wrong path and wrong method; verified endpoint is POST /company/search/autocomplete (Part 4.1, row 2).
3. was: POST /screener/company/identify / now: POST /company/identify / reason: wrong path; verified (Part 4.1, row 2).
4. was: POST /screener/company/enrich / now: POST /company/enrich / reason: wrong path; verified (Part 4.1, row 3).
5. was: POST /screener/person/search / now: POST /person/search / reason: wrong path; verified (Part 4.1, row 4).
6. was: POST /screener/person/enrich / now: POST /person/enrich / reason: wrong path; verified (Part 4.1, row 4).
7. was: POST /screener/job/search / now: POST /job/search / reason: wrong path; verified (Part 4.1, row 5).
8. was: no headers stated / now: authorization: Bearer <KEY> and x-api-version: 2025-11-01 / reason: required by verified Crustdata facts (Part 4.0).
9. was: "industries" / now: taxonomy.professional_network_industry / reason: verified field name (Part 4.1, row 1).
10. was: "company size" / now: headcount.total / reason: verified field name; requires `headcount` in fields (Part 4.1, row 1).
11. was: "headquarters" / now: locations.headquarters / reason: verified field name; requires `locations` in fields (Part 4.1, row 1).
12. was: "company name" / now: basic_info.name / reason: verified field name (Part 4.1, row 2).
13. was: "domain" / now: basic_info.primary_domain / reason: verified field name (Part 4.1, row 2).
14. was: "linkedin_id" (no status) / now: linkedin_id, marked NOT VERIFIED / reason: not in the verified field list; name not confirmed.
15. was: "employee_count" / now: headcount.total / reason: verified field name for employee count (Part 4.1, row 3; Part 5.3).
16. was: "headcount trajectory" / now: marked NOT VERIFIED, no field named / reason: no verified field; name not confirmed.
17. was: "growth_metrics" / now: marked NOT VERIFIED / reason: no verified field; name not confirmed.
18. was: "current_company" / now: filter experience.employment_details.current.company_name; the name "current_company" does not exist / reason: check report section 5.
19. was: "current_employer" (Part 5.3 citation) / now: experience.employment_details.current.name (read path TO CONFIRM ON A LIVE CALL) / reason: "current_employer" does not exist; the PDF used two names for one field; the report says the response treats `current` as an array, so the exact path is open.
20. was: "job title" (person) / now: experience.employment_details.current[].title / reason: verified field name for the person's current title (report section 5).
21. was: "tenure_months" / now: marked NOT VERIFIED / reason: no verified field; name not confirmed.
22. was: "job_title" / now: job_details.title / reason: verified field name (Part 4.1, row 5).
23. was: "posting date" / now: metadata.date_added, meaning marked NOT VERIFIED / reason: verified field exists and is filterable, but its meaning as a posting date is not confirmed.
24. was: "department" / now: marked NOT VERIFIED / reason: no verified field; name not confirmed.
25. was: "credits_remaining" / now: marked NOT VERIFIED (field name in the GET /account/credits response) / reason: response field name not confirmed.
26. was: citation field "hq_location" / now: locations.headquarters / reason: verified field name; consistent with change 11.
27. was: citation field "name" / now: basic_info.name / reason: verified field name; consistent with change 12.
28. was: citation field "employee_count" / now: headcount.total / reason: verified field name; consistent with change 15.
29. was: Part 4 claim "every step of this workflow maps directly to real Crustdata API capabilities" / now: mapping table with gaps marked / reason: Crustdata does not provide PAN/GSTIN, bank account ownership, ISO/RoHS certifications, or signing authority.
30. was: Part 4 with no list of gaps / now: Part 4.0 lists the four Crustdata gaps / reason: verified facts state these are not provided.
31. was: Part 5.3 signatory "verification_status": "PASS" with no limit stated / now: "PASS (current employment only)" plus "signing_authority_status": "NOT VERIFIED" / reason: Crustdata confirms employment, not signing authority.
32. was: Part 5.3 policy check with no certification or tax ID check / now: "certifications_check" and "tax_id_check" added as NOT VERIFIED / "I don't know" / reason: Crustdata does not provide these; the PDF's own rubric requires "I don't know".
33. was: Part 5.3 headcount_trend "+12% over 12 months" with no label / now: labelled SIMULATED in block and marked NOT VERIFIED for trend field / reason: invented sample value.
34. was: Part 5.3 values (names, address, industry, headcounts, timestamp) with no label / now: whole block labelled SIMULATED / reason: invented example values.
35. was: Part 5.3 citation "Crustdata /company/identify" and "/company/enrich" written with the short form / now: "Crustdata POST /company/identify" and "POST /company/enrich" / reason: states method and the verified path.
36. was: Part 5.1 input values with no label / now: block labelled SIMULATED / reason: invented example values.
37. was: Part 5.1 "required_certifications" with no note / now: note that Crustdata cannot check them / reason: Crustdata gap.
38. was: Part 5.2 bid values with no label / now: block labelled SIMULATED / reason: invented example bids.
39. was: Part 1 (Zuric Group) stated as fact / now: whole Part marked NOT VERIFIED / reason: no public source found in the Zurich check.
40. was: Part 1.1 headquarters "Meydan Hotel, Nad Al Sheba, Dubai" / now: marked NOT VERIFIED / reason: no source found.
41. was: Part 1.2 pricing and engagement model / now: marked NOT VERIFIED / reason: no source found.
42. was: Part 1.3 human roles / now: marked NOT VERIFIED / reason: no source found.
43. was: Part 1.4 workflow with title "Zuric Workflow" / now: heading kept, marked NOT VERIFIED as Zuric's own process / reason: generic model, not confirmed for Zuric.
44. was: Part 1.5 example "500 IP67 Industrial Temperature Sensors" and "< 14 days" / now: labelled SIMULATED / reason: invented example values.
45. was: Part 1.6 pain points and "3-4 weeks" / now: marked NOT VERIFIED / reason: no source found.
46. was: Name "Zuric Group" with no note / now: name note added at top (owner calls it "Zurich"; name not verified) / reason: the owner's name differs from the PDF's and no record was found under either.
47. was: Part 2 header "Icertis & Mercedes-Benz" with no source note / now: source status added (vendor claim / NOT VERIFIED) / reason: the teammate cited no sources.
48. was: Part 2.1 Icertis market claims (leader, customers, ERP integrations) / now: labelled vendor claim, not independently verified / reason: published by Icertis.
49. was: Part 2.1 "hosted on Microsoft Azure" / now: marked NOT VERIFIED / reason: not checked.
50. was: Part 2.2 contract length and pricing / now: marked NOT VERIFIED / reason: no source.
51. was: Part 2.2 implementation fees ($150k to $1M+) / now: marked NOT VERIFIED / reason: no source.
52. was: Part 2.3 Mercedes-Benz case study figures / now: labelled vendor claim, not independently verified / reason: Icertis case study figures.
53. was: Part 2.4 human roles / now: marked NOT VERIFIED / reason: no source.
54. was: Part 2.5 workflow with DocuSign / Adobe Sign / now: marked NOT VERIFIED / reason: no source for Icertis's own product flow.
55. was: Part 2.5 "Vera Copilot" step / now: labelled vendor claim, not independently verified / reason: Icertis product claim.
56. was: Part 2.6 "$500,000+" and "blind to the external world" claims / now: marked NOT VERIFIED / reason: no source.
57. was: Part 3 diagram (image) / now: text summary of the flow; image not reproduced / reason: Markdown cannot hold the image; the flow is kept.
58. was: Part 6 "Why This Scores 100%" / now: rubric wording kept, labelled NOT VERIFIED where claims are unverified / reason: the 429, $100k labor, 4-week delay and executive tenure claims are unchecked.
59. was: Part 6 "Facts & Verification" claiming executive tenure as a fact / now: flagged NOT VERIFIED / reason: tenure field not verified.
60. was: Executive summary "Even with Icertis, onboarding takes weeks" / now: marked NOT VERIFIED / reason: no source.
61. was: Executive summary "Even with Zuric, sourcing stops at a spreadsheet comparison" / now: marked NOT VERIFIED / reason: no source.
62. was: Part 2.6 point 4 "Icertis Vera is an interactive chatbot" / now: marked NOT VERIFIED / reason: product behaviour not checked.
63. was: Part 7 Module B (Crustdata client) with no endpoint list / now: endpoints listed with verified names and gap flagging added / reason: keeps module split aligned with verified endpoints.
64. was: Part 4.0 endpoint list with no enabled/disabled status / now: 12 enabled endpoints listed / reason: account_endpoints check; coordinator instruction 4.
65. was: no list of unavailable endpoints / now: "Not available to a builder key" list in Part 4.0 (including all batch endpoints) / reason: account_endpoints check; coordinator instruction 3.
66. was: job autocomplete implied as a REST option (/job/search/autocomplete in the request) / now: removed; job autocomplete marked MCP-only (tool `job_autocomplete`) / reason: /job/search/autocomplete does not exist on the account; coordinator instruction 2.
67. was: plan-gated fields not mentioned / now: plan-gated fields listed in Part 4.0 / reason: 403 when requested; coordinator instruction 5.
68. was: certifications gap stated without plan note / now: note that person_enrich `certifications` is plan-gated, so the ISO/RoHS gap stands / reason: coordinator instruction 5.
69. was: no cost or rate-limit table / now: table copied from check report section 4, including "not listed" entries / reason: coordinator instruction 6.
70. was: "locations.headquarters needs locations requested" / now: "comes back only if `locations` is listed in fields" (wording and row 1 of Part 4.1) / reason: coordinator instruction 7.
71. was: "headcount.total needs headcount requested" / now: "comes back only if `headcount` is listed in fields" (wording and row 3 of Part 4.1) / reason: coordinator instruction 7.
72. was: demo question not addressed / now: Part 4.4 "OWNER DECISION, not answered by the terms" with clause quotes / reason: coordinator instruction 8; the report says no clause addresses demos.
73. was: Part 6 2-Minute Demo with no terms note / now: owner decision flagged / reason: coordinator instruction 8.
74. was: Part 4.1 row 4 read path "current[].name" / now: read path marked TO CONFIRM ON A LIVE CALL, with the filter path shown separately / reason: coordinator instruction 1.
75. was: Part 5.3 signatory citation field "experience.employment_details.current[].name" / now: "experience.employment_details.current.name" with field_status TO CONFIRM ON A LIVE CALL / reason: coordinator instruction 1.

# Example: What Good Tool Output Looks Like

This shows scoring applied to `response_1_weak.md` against
`rfp_nordframe.md`, as a reference for the level of specificity expected —
especially for Level 2/3. Teams don't need to match this exact format.

---

## Level 1-style output (rubric score only, no RFP comparison)

| Criterion | Score (1–5) | Comment |
|---|---|---|
| Problem Understanding | 3 | States the general problem correctly but only at a surface level |
| Scope & Deliverables Clarity | 2 | Feature list is generic, lacks specifics |
| Pricing Clarity | 1 | Entirely deferred — "provided upon further discussion" |
| Timeline Clarity | 1 | No dates or milestones — "in a timely manner" |
| Completeness vs. RFP Requirements | 2 | Several explicit requirements not addressed |
| Tone & Persuasiveness | 2 | Generic, boilerplate, not tailored to NordFrame |
| Risk/Assumptions Transparency | 1 | Nothing disclosed anywhere |

**Overall: 1.7 / 5 — Needs significant revision before sending.**

---

## Level 2-style output (adds RFP comparison + specific fixes)

> ❌ **Missing: PostgreSQL integration constraint**
> The RFP requires integration with the existing PostgreSQL database with
> "no migration to a new database." The proposal only says "cloud-based
> dashboard," which doesn't confirm this constraint is respected.
> **Suggested fix:** State explicitly that the dashboard connects to the
> existing PostgreSQL database with no migration required.

> ❌ **Missing: Data migration / onboarding plan**
> The RFP asks for a rollout plan across all 6 sites with minimal
> disruption. Nothing in the proposal addresses this.
> **Suggested fix:** Add a "Rollout Plan" section describing the order
> sites go live and how disruption is minimized.

> ❌ **Missing: Support & maintenance / SLA terms**
> The RFP explicitly asks for response times and SLA terms after go-live.
> **Suggested fix:** Add a "Support & Maintenance" section with concrete
> response-time commitments.

> ⚠️ **Vague: Role-based access**
> The RFP asks specifically for warehouse managers to see only their own
> site, and HQ staff to see all sites. The proposal only says "secure login
> for different users."
> **Suggested fix:** State explicitly: "Warehouse managers see only their
> assigned site; HQ staff see all 6 sites."

> ❌ **Deferred: Pricing**
> The RFP gave a budget range (€80k–120k). Pricing is deferred entirely.
> **Suggested fix:** Provide at least a rough breakdown within the stated
> budget, even if final numbers depend on discovery.

> ❌ **Vague: Timeline**
> The RFP asks for a pilot within 3 months and full rollout within 6. The
> proposal gives no dates.
> **Suggested fix:** Add a milestone table mapping to the RFP's 3-month /
> 6-month expectation.

> ❌ **Missing: Risks/assumptions**
> The RFP explicitly asks for risks/assumptions to be documented. Nothing
> is disclosed.
> **Suggested fix:** Add a short "Risks & Assumptions" section naming at
> least one real dependency (e.g. database access, site onboarding time).

---

## Level 3-style addition (interpreted priority + citation)

> **Detected client priority (from RFP):** The RFP repeats "existing
> database, no migration" and "minimal disruption" — suggesting continuity
> and low operational risk matter more to this client than technical
> sophistication.
> *(User confirms/adjusts this before scoring proceeds.)*

> **Citation example:**
> "Completeness — Support & Maintenance: 1/5. RFP, Requirement 6, asks for
> 'support & maintenance terms after go-live (response times, SLAs).'
> Proposal, 'Why BrightPath' section, ends with no mention of support terms
> anywhere in the document."

This level of specificity — pointing to the exact requirement, where it
should appear, and a concrete fix — is what separates a genuinely useful
Proposal Scorer from a generic "looks good / needs work" tool.

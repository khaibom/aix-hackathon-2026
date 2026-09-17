# Proposal: Inventory Intelligence Platform for NordFrame Logistics

**Submitted by:** Fernglow Digital (fictional)
**Variant: STRONG — fully addresses RFP, transparent, specific**

## Our Understanding
NordFrame operates 6 warehouses across Germany and Austria, currently
tracked via spreadsheets and a legacy system. The goal is a single
real-time view of inventory, without disrupting existing data
infrastructure or operations during rollout.

## Proposed Solution

### 1. Real-Time Dashboard
Live inventory levels across all 6 warehouses, refreshed continuously from
your existing PostgreSQL database via a read-only connector — **no
migration or schema changes required.**

### 2. Low-Stock Alerts
Configurable per-item thresholds; alerts sent by email/SMS to the
responsible warehouse manager automatically.

### 3. Role-Based Access
Warehouse managers see only their own site's inventory; HQ staff have
company-wide visibility. Access is enforced at the database query level,
not just hidden in the UI.

### 4. Rollout / Onboarding Plan
| Step | Approach |
|---|---|
| Pilot | 1 warehouse, Weeks 1–10 (within your 3-month target) |
| Validation | 2 weeks running in parallel with existing spreadsheet process, to confirm data accuracy before full cutover |
| Phased rollout | Remaining 5 warehouses added in 2 batches, Weeks 13–24 (within your 6-month target) |

### 5. Support & Maintenance
Included in Year 1 pricing below: 24-hour response time for critical
issues (system down), 3-business-day response for minor issues, during
CET business hours.

## Pricing
| Item | Cost |
|---|---|
| Dashboard + PostgreSQL integration | €58,000 |
| Alerts & role-based access | €14,000 |
| Rollout support (6 sites) | €12,000 |
| Year 1 support & maintenance | €18,000 |
| **Total** | **€102,000** (within your stated budget) |

## Risks & Assumptions
- Assumes read access to the existing PostgreSQL database can be granted
  without changes to your production schema; confirmed feasible based on
  the schema summary shared during scoping.
- Phased rollout assumes each warehouse can name one point-of-contact for a
  1-hour onboarding session; delays here would shift the Week 13–24 plan
  proportionally.
- Alert thresholds are per-item defaults at launch; fine-tuning based on
  real usage may take 2–3 weeks post-launch per site.

## Why Fernglow
We've delivered similar inventory visibility platforms for two regional
logistics operators in the past two years, both still in production today.

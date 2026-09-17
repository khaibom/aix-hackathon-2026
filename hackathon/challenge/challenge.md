3. Context & Problem Statement 
The business or community context - what's happening today, and why it's a problem 
Before a proposal goes out to a client, someone senior usually needs to review it - checking whether it actually 
addresses the client's stated needs, whether pricing and scope are clear, whether it reads as persuasive and 
professional, and whether anything important is missing or risky to promise. That review today is manual, 
inconsistent (quality depends on who reviews it and how much time they have), and it often happens under time 
pressure, right before a deadline - meaning weak spots can slip through. 
Any constraints teams should know about going in 
• No real client data will be used - teams will work with fictional or anonymized sample proposals and 
RFPs (see Section 7). 
• The goal is a useful reviewer, not a proposal writer - teams shouldn't build a tool that generates 
proposals from scratch; the focus is evaluating and improving an existing draft. 
• Feedback should be specific and actionable ("Section 3 doesn't mention the budget the client specified" 
beats "improve clarity"). 
4. Target Users & Stakeholders 
• End-users: Sales, pre-sales, and account managers who need a fast, honest second opinion on a 
proposal before it goes to a client.
• Other stakeholders: Sales managers/directors who currently do this review manually and would benefit 
from more consistent quality checks; and indirectly, clients, who'd receive clearer, better-matched 
proposals. 
• Goal: After the solution exists, a salesperson should be able to get fast, specific, structured feedback on 
a draft proposal - comparable in usefulness to a quick review from an experienced colleague - without 
needing to wait for someone's availability. 
5. Expected Final Product 
Teams are free to decide how far they want to develop the solution based on their skills and available time. A 
well-executed simple solution can score as well as or better than a partially-working ambitious one. 
The solution may include capabilities such as: 
• A score or rating (e.g. 1–5 or a simple traffic-light) across a small fixed set of criteria - e.g. clarity, 
completeness, tone/persuasiveness - plus a short written comment per criterion. 
• A check of whether the proposal actually addresses what the RFP asked for - flagging specific client 
requirements that seem unaddressed, unclear, or mismatched (e.g. "the RFP asks for a maintenance 
plan; the proposal doesn't mention one"). 
• For each significant issue found, a specific suggested fix - a rewritten paragraph, a suggested addition 
to cover a missing requirement, or clearer phrasing for pricing/timelines. 
• Configurable criteria: instead of a fixed rubric, start from a base set of criteria and let the user adjust 
weights or add/remove criteria before scoring - not every proposal should be judged the same way. 
Optional: have the AI read the RFP and suggest which criteria matter most for that specific client, 
rather than the user configuring blind. 
• Citations for scores and comments: each piece of feedback can point back to exactly where it came 
from (e.g. "Completeness: 2/5 - the RFP, Section 4, requires a data migration plan not mentioned 
anywhere in the proposal") - so a reviewer can verify claims against the source text rather than blindly 
trusting a number. 
Whichever approach a team picks, the end result must be something judges can interact with live - pasting or 
uploading a sample proposal and watching the tool produce feedback in real time.
6. Resources & Tools 
Resources: A small set of fictional sample proposals and matching RFPs/briefs will be provided (see Section 7) 
so all teams can test against comparable material, and so judging stays fair across teams. 
Tools: No requirement 
7. Data & Validation 
Data description: A small set of fictional, anonymized sample "draft proposals + original RFP", spanning a 
couple of different scenarios (one clean/strong proposal, one with clear gaps, one with vague pricing/timelines) - 
written specifically for this hackathon, with no real client information. 
For simplicity, the RFP/Proposal will be provided in Markdown format (in real life, RFPs are normally in PDF, 
while Proposals are often prepared in PowerPoint and exported to PDF). 
Validation data: We will bring a separate RFP/Proposal pair, not given to teams in advance and different from 
the sample data, that can be used live during scoring/demo to test how each team's tool performs on an unseen 
example. 
8. Judging Criteria 
• Additional criterion 1: Is the feedback specific and actionable (points to an exact section/issue) rather 
than generic ("could be clearer")? 
• Additional criterion 2: Does the tool meaningfully use the RFP to check whether the proposal addresses 
actual client requirements, rather than scoring the proposal in isolation? 
• Bonus criterion: Can the tool handle longer or more complex documents closer to real-world RFPs and 
proposals, such as PDF documents or proposals exported from PowerPoint to PDF? This is optional 
and not required.

## Appendix A - Additional Scoring Criteria

| # | Criterion | What to check |
|---|---|---|
| 1 | Problem Understanding | Does the proposal correctly reflect the client's actual stated problem/goals (from the RFP), not a generic pitch? |
| 2 | Scope & Deliverables Clarity | Are the deliverables specific and unambiguous? Is it clear what is/isn't included? |
| 3 | Pricing Clarity | Is pricing clearly stated, broken down, and easy to understand (vs. vague or "on request")? |
| 4 | Timeline Clarity | Are milestones and dates concrete, not vague ("in due course," "as soon as possible")? |
| 5 | Completeness vs. RFP Requirements | Does the proposal address every requirement the RFP explicitly asked for? |
| 6 | Tone & Persuasiveness | Does it read as confident, client-focused, and professional - not generic boilerplate? |
| 7 | Risk/Assumptions Transparency | Are assumptions, dependencies, or risks clearly flagged rather than hidden or omitted? |


## Appendix B - Sample Data

Will be provided as separate Markdown files. These are AI-generated, should be used as reference and sample to test the system.

| File | Variant | Purpose |
|---|---|---|
| `rfp_nordframe.md` | — | The single client RFP used for every response below |
| `response_1_weak.md` | Weak | Generic, deferred pricing/timeline, several missing requirements |
| `response_2_medium.md` | Medium | Good functional scope match, but vague pricing/timeline, no risk disclosure |
| `response_3_strong.md` | Strong | Fully addresses the RFP, specific, transparent — contrast case for "good" |
| `response_4_overpromise.md` | Overpromising | Scope balloons beyond the ask, contradicts an explicit constraint, unrealistic timeline/price |
| `scoring_example.md` | — | Example of good tool output, using Response 1 |

**Teams get `rfp_nordframe.md` + Responses 1–4 to build and test against.**
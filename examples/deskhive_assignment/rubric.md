# DeskHive Maintenance Assignment Rubric

Total score: 100 points, plus up to 10 bonus points. This rubric is for
evaluators only and is not shared with candidates.

## R1. Defect B1: finite exhaustion estimate (12 points)

Evidence expectations:

- The credit exhaustion estimate no longer returns infinity for a member with no
  recent visits.
- The fix handles the zero-usage case explicitly rather than by accident.
- The diagnosis log explains the root cause.

Traceable spec quote: "The solution must fix the credit exhaustion estimate so that it returns a finite number of days for members with no recent visits."

## R2. Defect B2: frozen membership expiry (12 points)

Evidence expectations:

- A frozen membership's expiry date moves out by the frozen day count.
- The freeze-day arithmetic is justified in the diagnosis log.

Traceable spec quote: "The solution must extend the membership expiry date by the number of days the membership was frozen."

## R3. Defect B3: free versus paid passes (12 points)

Evidence expectations:

- Free trial passes and paid day passes are tracked as separate balances.
- The remaining balance reported to the member is correct for a mixed account.

Traceable spec quote: "The solution must count free trial passes separately from paid day passes when it reports the remaining balance."

## R4. Defect B4: monthly new-member analytics (12 points)

Evidence expectations:

- The monthly new-member count equals the count of members who actually joined
  that month.
- Any month-boundary or time-zone cause is identified.

Traceable spec quote: "The solution must make the monthly new-member count match the actual members who joined in that month."

## R5. Defect B5: host recommendation spread (10 points)

Evidence expectations:

- Recommendations no longer collapse onto a single host.
- Eligible hosts are selected in a defensible way.

Traceable spec quote: "The recommendation endpoint must never return the same host twice in a row."

## R6. Verification suite (15 points)

Evidence expectations:

- There is at least one automated test per fixed defect.
- The suite runs locally to green without external services.
- A verification design note explains the test structure.

Traceable spec quote: "The solution must include at least one automated test for each defect that was fixed."

## R7. CTO report (15 points)

Evidence expectations:

- A written report summarizes status, defects, and verification for a
  non-engineering reader.
- The report is understandable without reading the code.

Traceable spec quote: "The solution must include a written report addressed to the CTO that summarizes the work."

## R8. Dashboard occupancy panel (10 points)

Evidence expectations:

- The dashboard shows how full each room is.
- The panel is readable and does not break existing dashboard views.

Traceable spec quote: "The solution may add an occupancy summary panel that shows how full each room is."

## RB1. Bonus: AI usage log (+5 points)

Award up to 5 bonus points when the AI tool usage log is included and is detailed
enough to follow the candidate's process. Absence of the log should not be scored
here as a deduction.

Traceable spec quote: "The solution must submit the AI tool usage log as part of the deliverables."

## RB2. Bonus: report depth (+5 points)

Award up to 5 bonus points when the CTO report goes beyond a summary and adds a
short technical-debt or roadmap section.

Traceable spec quote: "The solution must include a written report addressed to the CTO that summarizes the work."

## Q1. Qualitative note: diagnosis process

This note is not scored directly. Review whether the diagnosis log shows a clear
path from symptom to root cause, whether dead ends are recorded honestly, and
whether decisions are justified. Use it to guide written feedback, not to add or
remove points.

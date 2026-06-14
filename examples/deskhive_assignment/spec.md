# DeskHive Back-Office PoC — Maintenance Assignment

## Background

DeskHive is a fictional co-working membership operator that runs five shared
work hubs in a single metro area. It sells monthly desk memberships, sells day
passes, lets members freeze a membership while they travel, and recommends a
meeting-room host to members who book a room. A previous developer built a
proof-of-concept back-office service with the help of an AI coding tool and then
left the team. You are taking over the project. Several defects were reported by
operations staff, and the system has no automated tests.

This assignment is not a contest. We care more about how you diagnose a problem
and justify a decision than about whether you reach a single "correct" answer.

## Deliverables

Submit your fixed source code, a diagnosis log, a verification design note, a
test suite, and a short report. The work must run locally without a network
connection or any paid service. Use any mainstream language you are comfortable
with.

## Phase 0: Environment

Bring the service up locally and confirm the health endpoint responds before you
start. This phase is setup only and is not scored on its own.

## Phase 1: Defect diagnosis and fix (required)

Operations reported five defects. For each one, confirm the symptom, trace the
root cause, fix it, and re-confirm the fixed behavior.

| ID | Reported symptom | Where to check |
|----|------------------|----------------|
| B1 | Credit exhaustion estimate shows infinity for inactive members | member detail endpoint |
| B2 | Frozen memberships expire on the wrong date | member detail endpoint |
| B3 | Remaining-pass balance mixes free and paid passes | pass balance endpoint |
| B4 | Monthly new-member dashboard count does not match the member list | analytics endpoint |
| B5 | Room-host recommendation keeps returning one host | recommendation endpoint |

The solution must fix the credit exhaustion estimate so that it returns a finite
number of days for members with no recent visits.

The solution must extend the membership expiry date by the number of days the
membership was frozen.

The solution must count free trial passes separately from paid day passes when it
reports the remaining balance.

The solution must make the monthly new-member count match the actual members who
joined in that month.

The solution must spread host recommendations across all eligible hosts rather
than favoring one host.

## Phase 2: Verification (required)

Design a small verification suite so the fixed defects do not silently come back.

The solution must include at least one automated test for each defect that was
fixed.

Record the intent and structure of your tests in a verification design note.
Stronger submissions add boundary cases and regression guards, but those are not
strictly required.

## Phase 3: Dashboard enhancement (optional)

If you have time after Phases 1 and 2, you may polish the operator dashboard.

The solution may add an occupancy summary panel that shows how full each room is.

This phase is optional and a submission that skips it is still complete.

## Phase 4: Report (required)

Write up the work for a non-engineering reader.

The solution must include a written report addressed to the CTO that summarizes
the work.

## AI usage disclosure

This assignment expects you to use AI coding tools, just as you would on the job.

The solution must submit the AI tool usage log as part of the deliverables.

## Boundaries

The solution must not modify historical billing records. The solution must not
require a paid service or a live network connection to run. The solution does
not need to support multiple metro areas, real payment processing, or
concurrent multi-user load.

## Acceptance criteria

A reviewer should be able to run the service locally, call each affected
endpoint, see the five reported symptoms resolved, run the test suite to green,
and read the report without engineering background. Phase 3 may be absent.

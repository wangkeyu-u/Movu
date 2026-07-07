# MovU Diagram Relationships

This document lists the relationships needed to draw the MovU use case diagram and sequence diagrams. It is written as a drawing checklist: copy each relationship into your UML tool and connect the same elements.

## 1. Use Case Diagram Relationships

### System Boundary

Draw one system boundary:

```text
MovU Carpooling System
```

Place all use cases inside this boundary. Place actors outside the boundary.

### Actors

Use these main actors:

```text
Rider
Driver
Admin
```

Optional external service actors:

```text
Email Service
Map / Route Service
Payment Provider
```

Use the optional actors only if the diagram needs to show external integrations.

### Rider Relationships

Connect `Rider` to these use cases:

```text
Rider -- Register / Login
Rider -- Verify Email
Rider -- View Account Status
Rider -- Create Ride Request
Rider -- View Match Recommendations
Rider -- Confirm Match
Rider -- Join Trip Network
Rider -- View Driver Live Location
Rider -- Send Trip Message
Rider -- Trigger SOS
Rider -- Rate Driver
Rider -- Report Driver
```

### Driver Relationships

Connect `Driver` to these use cases:

```text
Driver -- Register / Login
Driver -- Verify Email
Driver -- View Account Status
Driver -- Register Vehicle
Driver -- Post Trip
Driver -- View Match Recommendations
Driver -- Accept Assigned Rider
Driver -- Reject Match
Driver -- Join Trip Network
Driver -- Share Driver Live Location
Driver -- Send Trip Message
Driver -- Start Trip
Driver -- Complete Trip
Driver -- Trigger SOS
Driver -- Rate Rider
Driver -- Report Rider
```

### Admin Relationships

Connect `Admin` to these use cases:

```text
Admin -- Login
Admin -- View Dashboard
Admin -- View Pending Users
Admin -- Approve User
Admin -- Reject User
Admin -- Ban User
Admin -- View Vehicles
Admin -- Approve Vehicle
Admin -- Reject Vehicle
Admin -- View Ride Requests
Admin -- View Trips
Admin -- View Matches
Admin -- View SOS Events
Admin -- Update SOS Status
Admin -- View Reports
Admin -- View Payments
Admin -- View Audit Logs
```

### External Service Relationships

Use these if external actors are included:

```text
Email Service -- Verify Email
Map / Route Service -- Create Ride Request
Map / Route Service -- Post Trip
Map / Route Service -- View Match Recommendations
Payment Provider -- View Payments
```

Payment collection is disabled until a production payment provider is configured, so do not draw payment as a completed rider checkout flow unless your diagram explicitly labels it as disabled or future provider integration.

### Include Relationships

Draw these as `<<include>>` relationships:

```text
Create Ride Request <<include>> Check Email Verified
Create Ride Request <<include>> Check Admin Approval
Create Ride Request <<include>> Validate 30km Service Area

Register Vehicle <<include>> Check Email Verified
Register Vehicle <<include>> Check Admin Approval

Post Trip <<include>> Check Email Verified
Post Trip <<include>> Check Admin Approval
Post Trip <<include>> Check Approved Vehicle
Post Trip <<include>> Validate 30km Service Area

View Match Recommendations <<include>> Run Matching Algorithm
View Match Recommendations <<include>> Check Candidate Constraints

Confirm Match <<include>> Check Match Ownership
Confirm Match <<include>> Check Seat Availability
Confirm Match <<include>> Update Match Status

Accept Assigned Rider <<include>> Check Trip Ownership
Accept Assigned Rider <<include>> Update Trip Network

Reject Match <<include>> Check Trip Ownership
Reject Match <<include>> Update Match Status

Join Trip Network <<include>> Check Confirmed Match

View Driver Live Location <<include>> Check Confirmed Rider
Share Driver Live Location <<include>> Check Trip Driver
Share Driver Live Location <<include>> Check Confirmed Trip

Send Trip Message <<include>> Check Trip Network Participant

Trigger SOS <<include>> Check Confirmed Trip Participant

Rate Driver <<include>> Check Completed Trip
Rate Driver <<include>> Check Trip Participant

Rate Rider <<include>> Check Completed Trip
Rate Rider <<include>> Check Trip Participant

Report Driver <<include>> Check Completed Trip
Report Driver <<include>> Check Trip Participant

Report Rider <<include>> Check Completed Trip
Report Rider <<include>> Check Trip Participant

Approve User <<include>> Write Audit Log
Reject User <<include>> Write Audit Log
Ban User <<include>> Write Audit Log
Approve Vehicle <<include>> Write Audit Log
Reject Vehicle <<include>> Write Audit Log
Update SOS Status <<include>> Write Audit Log
```

### Simple Use Case Version

If the diagram needs to be smaller, use this reduced relationship set:

```text
Rider -- Register / Login
Rider -- Create Ride Request
Rider -- View Match Recommendations
Rider -- Confirm Match
Rider -- Join Trip Network
Rider -- View Driver Live Location
Rider -- Trigger SOS
Rider -- Rate / Report Driver

Driver -- Register / Login
Driver -- Register Vehicle
Driver -- Post Trip
Driver -- View Match Recommendations
Driver -- Share Driver Live Location
Driver -- Trigger SOS
Driver -- Rate / Report Rider

Admin -- Approve / Reject / Ban User
Admin -- Approve / Reject Vehicle
Admin -- View Trips / Requests / Matches
Admin -- View SOS / Reports / Audit Logs

Create Ride Request <<include>> Check Approved User
Post Trip <<include>> Check Approved User
View Match Recommendations <<include>> Run Matching Algorithm
Confirm Match <<include>> Check Match Ownership
Join Trip Network <<include>> Check Confirmed Match
Trigger SOS <<include>> Check Confirmed Trip Participant
Rate / Report User <<include>> Check Completed Trip Participant
Admin Actions <<include>> Write Audit Log
```

## 2. Sequence Diagram Relationships

### Recommended Lifeline Order

For a full sequence diagram, arrange lifelines from left to right:

```text
Rider
Driver
User App
Backend API
Matching Algorithm
Database
Admin Dashboard
Admin
```

For a simpler diagram, merge the people into one side:

```text
Rider / Driver
User App
Backend API
Matching Algorithm
Database
Admin Dashboard
Admin
```

## 3. Main Sequence: Account Approval

Draw these messages in order:

```text
Rider -> User App: Register / Login
User App -> Backend API: Send credentials
Backend API -> Database: Create or verify user
Database -> Backend API: Return user data
Backend API -> User App: Return email verification and account status

Rider -> User App: Verify email
User App -> Backend API: Submit verification token
Backend API -> Database: Set email_verified = true
Backend API -> User App: Email verified, waiting for admin approval

Admin -> Admin Dashboard: Review pending user
Admin Dashboard -> Backend API: Approve user
Backend API -> Database: Set verification_status = approved
Backend API -> Database: Write audit log
Backend API -> Admin Dashboard: Approval success
```

Important condition:

```text
email_verified = true only proves the email is real.
verification_status = approved is required before the user can create ride requests, trips, SOS events, or other core actions.
```

## 4. Main Sequence: Ride, Trip, Match

Draw these messages in order:

```text
Driver -> User App: Register vehicle
User App -> Backend API: Submit vehicle information
Backend API -> Backend API: Check approved user
Backend API -> Database: Save vehicle

Admin -> Admin Dashboard: Review vehicle
Admin Dashboard -> Backend API: Approve vehicle
Backend API -> Database: Set vehicle status = approved
Backend API -> Database: Write audit log
Backend API -> Admin Dashboard: Vehicle approved

Driver -> User App: Post trip
User App -> Backend API: Create trip
Backend API -> Backend API: Check approved user and approved vehicle
Backend API -> Backend API: Validate 30km Taylor's University service area
Backend API -> Database: Save trip

Rider -> User App: Create ride request
User App -> Backend API: Submit ride request
Backend API -> Backend API: Check approved user
Backend API -> Backend API: Validate 30km Taylor's University service area
Backend API -> Database: Save ride request

Backend API -> Matching Algorithm: Find matches
Matching Algorithm -> Database: Read trips and ride requests
Database -> Matching Algorithm: Return candidate data
Matching Algorithm -> Matching Algorithm: Apply hard constraints
Matching Algorithm -> Matching Algorithm: Score feasible candidates
Matching Algorithm -> Backend API: Return ranked match results
Backend API -> Database: Save recommended matches
Backend API -> User App: Return recommendations

Rider -> User App: Confirm match
User App -> Backend API: Confirm selected match
Backend API -> Backend API: Check rider owns the ride request
Backend API -> Backend API: Check seat availability
Backend API -> Database: Update match status = confirmed
Backend API -> Database: Reserve seat / update request status
Backend API -> User App: Match confirmed
```

Important condition:

```text
Only confirmed matches can enter trip network, live location, SOS, and rating/report flows.
```

## 5. Main Sequence: Trip Network And Location

Draw these messages in order:

```text
Driver -> User App: Start trip
User App -> Backend API: Update trip status = ongoing
Backend API -> Backend API: Check driver owns trip
Backend API -> Database: Update trip status

Driver -> User App: Send live location
User App -> Backend API: Upload driver location
Backend API -> Backend API: Check driver owns trip
Backend API -> Backend API: Check confirmed trip
Backend API -> Database: Save location log
Backend API -> User App: Location accepted

Rider -> User App: View live location
User App -> Backend API: Request trip location
Backend API -> Backend API: Check rider has confirmed match
Backend API -> Database: Read latest driver location
Backend API -> User App: Return driver location

Rider -> User App: Send trip message
User App -> Backend API: Submit trip message
Backend API -> Backend API: Check trip network participant
Backend API -> Database: Save message
Backend API -> User App: Message saved

Driver -> User App: Complete trip
User App -> Backend API: Update trip status = completed
Backend API -> Backend API: Check driver owns trip
Backend API -> Database: Update trip status
Backend API -> User App: Trip completed
```

## 6. Main Sequence: SOS

Draw these messages in order:

```text
Rider / Driver -> User App: Trigger SOS
User App -> Backend API: Create SOS event
Backend API -> Backend API: Check confirmed trip participant
Backend API -> Database: Save SOS event
Backend API -> User App: SOS created

Admin -> Admin Dashboard: View SOS event
Admin Dashboard -> Backend API: Load SOS events
Backend API -> Database: Read SOS events
Backend API -> Admin Dashboard: Return SOS events

Admin -> Admin Dashboard: Update SOS status
Admin Dashboard -> Backend API: Update SOS status
Backend API -> Backend API: Check admin role
Backend API -> Database: Update SOS status
Backend API -> Database: Write audit log
Backend API -> Admin Dashboard: SOS updated
```

## 7. Main Sequence: Ratings And Reports

Draw these messages in order:

```text
Rider -> User App: Rate or report driver
User App -> Backend API: Submit rating / report
Backend API -> Backend API: Check completed trip
Backend API -> Backend API: Check rider participated in trip
Backend API -> Backend API: Check target user is related to trip
Backend API -> Database: Save rating / report
Backend API -> User App: Success

Driver -> User App: Rate or report rider
User App -> Backend API: Submit rating / report
Backend API -> Backend API: Check completed trip
Backend API -> Backend API: Check driver owns trip
Backend API -> Backend API: Check target rider is confirmed on trip
Backend API -> Database: Save rating / report
Backend API -> User App: Success

Admin -> Admin Dashboard: View reports
Admin Dashboard -> Backend API: Load reports
Backend API -> Database: Read reports
Backend API -> Admin Dashboard: Return reports
```

## 8. Main Sequence: Payments

Draw payment as disabled unless a production provider is configured:

```text
Rider -> User App: Open payment action
User App -> Backend API: Request payment
Backend API -> Backend API: Check production payment provider
Backend API -> User App: Payment collection disabled
```

If showing local-only testing behavior:

```text
Rider -> User App: Create local test payment
User App -> Backend API: Submit match payment
Backend API -> Backend API: Check rider owns confirmed match
Backend API -> Backend API: Reject if environment = production
Backend API -> Database: Save local test payment
Backend API -> User App: Payment recorded for local test
```

## 9. Permission Rules To Put Beside The Diagrams

Use these as notes beside the diagrams:

```text
Only approved users can create ride requests.
Only approved drivers with approved vehicles can post trips.
Rider can only confirm a match for their own ride request.
Driver can only reject or manage matches for their own trip.
Only the trip driver can upload driver location.
Only confirmed riders can view driver location.
Only confirmed trip participants can trigger SOS.
Only completed trip participants can rate or report.
Users cannot rate or report unrelated users.
Only admins can approve, reject, or ban users.
Only admins can approve or reject vehicles.
Only admins can update SOS status.
All security-sensitive admin actions write audit logs.
Production blocks simulated payments.
```

## 10. Oral Drawing Guide

When explaining how to draw the use case diagram:

```text
First, draw the MovU Carpooling System boundary.
Then place Rider, Driver, and Admin outside the boundary.
Inside the boundary, draw account, ride, trip, match, location, SOS, rating/report, and admin management use cases.
Connect Rider to ride request, match confirmation, location, SOS, and rating/report.
Connect Driver to vehicle registration, trip posting, location sharing, SOS, and rating/report.
Connect Admin to approval, monitoring, reports, SOS management, and audit logs.
Finally, add include relationships for approval checks, ownership checks, confirmed match checks, completed trip checks, and audit logging.
```

When explaining how to draw the sequence diagram:

```text
First, place lifelines from left to right: user, app, backend, matching algorithm, database, and admin dashboard.
Start with registration and email verification.
Then show admin approval because core actions require approved status.
Next show driver vehicle approval and trip posting.
Then show rider ride request creation.
After that, show the backend calling the matching algorithm, the algorithm reading database candidates, scoring them, and returning ranked matches.
Then show rider match confirmation.
After match confirmation, draw trip network, live location, SOS, and rating/report flows.
Use permission checks as short self-calls on Backend API.
```

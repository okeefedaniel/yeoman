# Yeoman User Manual

Yeoman is the speaking-engagement and event-scheduling product in the
DockLabs suite. It moves an invitation — for a hearing, keynote, panel,
ribbon-cutting, site visit, fireside chat, or any other ask on the
principal's time — from public intake through triage, decision,
delegation, calendar push, and completion, with a full audit trail.

This manual covers the user-facing surface end to end. For engineering
notes, see the suite-wide [keel/CLAUDE.md](../keel/CLAUDE.md).

---

## Contents

1. [Overview](#overview)
2. [Roles](#roles)
3. [Getting Started](#getting-started)
4. [Dashboard](#dashboard)
5. [Invitations](#invitations)
6. [Workflow & Status](#workflow--status)
7. [Assignment, Principal & Delegation](#assignment-principal--delegation)
8. [Notes & Attachments](#notes--attachments)
9. [Calendar & iCal](#calendar--ical)
10. [Map](#map)
11. [Public Intake](#public-intake)
12. [Reports & Exports](#reports--exports)
13. [Beacon CRM Sync](#beacon-crm-sync)
14. [Helm Inbox](#helm-inbox)
15. [Notifications](#notifications)
16. [Principal Settings](#principal-settings)
17. [Status Reference](#status-reference)
18. [Keyboard Shortcuts](#keyboard-shortcuts)
19. [Support](#support)

---

## Overview

Yeoman is built around one record — the **Invitation** — and the
lifecycle a request for the principal's time travels through:

> public intake → triage → decision (accept / tentative / decline) →
> optional delegation → calendar push → completion

Yeoman does not store legislative bills, FOIA requests, or grants. It
focuses on the calendar of a principal (typically a Commissioner or
agency head) and the people, organizations, and logistics around each
event.

When the suite is fully deployed, Yeoman pushes new submitter contacts
into Beacon (the CRM) and surfaces open invitations on Helm's "Awaiting
Me" inbox. Standalone deployment works — those integrations gracefully
no-op when their peer URLs aren't configured.

---

## Roles

Yeoman roles are issued via Keel SSO and surfaced in your sidebar
profile.

| Role | Capability |
|---|---|
| **Administrator** (`yeoman_admin`) | Full access. Triage, decide, delegate, schedule, complete, cancel, reopen. Manage principal profile and reference addresses. |
| **Scheduler** (`yeoman_scheduler`) | Triage and operate the queue. Start review, request info, push to calendar, complete, and cancel. Cannot accept / decline / delegate (those are Administrator decisions). |
| **Principal** (`yeoman_principal`) | The person whose time is being scheduled. Once a Scheduler has triaged a request to **Under Review** or **Tentative**, the Principal can personally accept, decline, or mark it tentative. No access to triage, delegation, or scheduling. |
| **Delegate** (`yeoman_delegate`) | Read invitations delegated to you. Receive delegation notifications. |
| **Viewer** (`yeoman_viewer`) | Read-only across the dashboard, list, and calendar. |

Suite-level `system_admin` inherits Administrator behavior on Yeoman.

---

## Getting Started

### Signing in

1. From any DockLabs product, click **Yeoman** in the fleet switcher,
   or visit `https://yeoman.docklabs.ai/`.
2. Click **Sign in with DockLabs** (the suite OIDC button).
3. You'll land on `/dashboard/`.

If you're already signed in to another DockLabs product, the redirect
is seamless — no second login form.

> **Note on URLs.** Yeoman keeps allauth mounted at `/auth/` (so the
> registered OIDC redirect URI `/auth/oidc/keel/login/callback/` keeps
> working), while the canonical login form lives at `/accounts/login/`
> like the rest of the suite. The legacy `/auth/login/` 301-redirects to
> the canonical path.

### What you'll see first

- **Dashboard** — counts by status, your queue, today's events, and
  upcoming events.
- **Invitations** — full list with filters.
- **Calendar** — month/week/day view of every event.
- **Map** — geographic plot of in-person events.
- **Reports** — activity rollups and export.

---

## Dashboard

`/dashboard/` — the staff landing page. Surfaces:

- **Status counters** — quick view of how many invitations sit in
  Received, Under Review, Needs Info, Accepted, Tentative, Scheduled,
  Delegated, Declined, Completed, Cancelled.
- **My queue** — invitations where you are the assignee, the
  principal, or the delegate, ordered by event date.
- **Today** — events happening today.
- **Upcoming** — the next 7–30 days.

The dashboard is read-oriented; click any invitation to act on it.

---

## Invitations

`/invitations/` — the operational list of every invitation in your
agency, with filters for status, priority, format, modality, date range,
assignee, and tag.

### Anatomy of an invitation

Each invitation carries:

- **Submitter info** — first/last name, email, phone, organization,
  title.
- **Event details** — name, description, date, start/end time,
  timezone, format (presentation, keynote, panel, site visit,
  ribbon-cutting, etc.), modality (in-person, virtual, hybrid).
- **Location** — venue name, full address, lat/lng (geocoded
  automatically when an address is provided), or virtual platform +
  link.
- **Assignment** — assigned coordinator (`assigned_to`), principal
  (`principal`), and optional delegate (`delegated_to` /
  `delegated_by` / `delegated_at`).
- **Priority** — Low, Normal, High, Urgent.
- **Tags** — agency-defined labels (e.g. `legislative`, `economic-dev`,
  `education`).
- **Logistics** — expected attendees, surrogate-OK flag, press
  expected (yes/no/unknown), will-be-recorded (yes/no/unknown).
- **Outcome** — decline reason, calendar event ID, push timestamp,
  recipients of the calendar invite.
- **Status history** — every transition logged with actor and comment.
- **Attachments** — uploaded files (briefing materials, agendas, prior
  speeches, related decks).
- **Notes** — internal staff notes.
- **Beacon status** — has the submitter been added to Beacon as a
  contact?
- **Status token** — UUID powering the public submitter status page
  (`/invite/status/<token>/`).

### Creating an invitation

Most arrive via the public intake form. Staff can also create one
directly from the list page if a request came in over email or by
phone.

### Editing

Click an invitation row → **Edit**. Changes are written through the
workflow engine where applicable, and any audit-relevant fields are
captured in status history.

---

## Workflow & Status

Yeoman uses Keel's `WorkflowEngine` for every state change. The full
graph:

```
received → under_review → needs_info → under_review
          ↓              ↓
          → accepted     → declined (comment required)
          → tentative
          → declined (comment required)

tentative → accepted
tentative → declined (comment required)

accepted  → delegated
tentative → delegated

accepted  → scheduled  (push to calendar)
tentative → scheduled
delegated → scheduled

scheduled → completed

(any open status) → cancelled
declined  → under_review (Reopen)
cancelled → under_review (Reopen)
```

### Who can do what

| Transition | Required role |
|---|---|
| Start Review, Request Info, Info Received | Scheduler or Administrator |
| Accept, Mark Tentative, Confirm | Administrator |
| Decline (any path) | Administrator (comment required) |
| Delegate | Administrator |
| Push to Calendar / Confirm & Schedule | Scheduler or Administrator |
| Complete | Scheduler or Administrator |
| Cancel | Scheduler or Administrator |
| Reopen | Administrator |

Each transition writes an immutable `InvitationStatusHistory` row
capturing the actor, the from/to status, the timestamp, and any
comment.

---

## Assignment, Principal & Delegation

Yeoman tracks three independent user pointers on every invitation:

- **`assigned_to`** — the **coordinator**: the staff member managing
  logistics, communicating with the submitter, and pushing the calendar
  event when the time comes. Set via the **Claim** action; cleared via
  **Unclaim**.
- **`principal`** — the **person speaking**: the Commissioner or agency
  head whose time is being scheduled. Set when the invitation is
  triaged.
- **`delegated_to`** — the **stand-in**: when the principal can't
  attend, an Administrator delegates to a deputy. The delegation is
  logged in `DelegationLog` along with a note explaining the rationale.

### Claim / Unclaim

Open an invitation → click **Claim** to take ownership. You become
`assigned_to`. The previous coordinator (if any) is replaced. Click
**Unclaim** to release; the invitation returns to the pool.

### Delegate

From an Accepted or Tentative invitation, an Administrator picks a
delegate, optionally adds delegation notes, and the invitation moves to
the **Delegated** status. The delegate receives an
`invitation_delegated` notification. The full chain is preserved in the
delegation history view on the invitation detail page.

---

## Notes & Attachments

### Notes

Internal staff notes live alongside the invitation
(`InvitationNote(AbstractInternalNote)`). Notes are staff-only —
submitters never see them. Use them for internal reasoning, conflicts
to flag, or coordination context.

### Attachments

Drag-and-drop file uploads on the invitation detail page. Each
attachment carries:

- **Original filename** + content type + size.
- **Uploaded by** (user) and **uploaded by staff** flag (distinguishes
  files the submitter sent through intake vs. files staff added later).
- **Label** — optional human-readable description.

Files are scanned by `keel.security.FileSecurityValidator` on upload
to enforce size and extension policy.

---

## Calendar & iCal

`/calendar/` — month/week/day FullCalendar view of every invitation
with an event_date. Color-coded by status. Click any event to open the
invitation detail page.

### Per-invitation iCal export

`/invitations/<uuid>/ical/` — download a single `.ics` file for an
invitation. Useful when you want to forward an event to someone outside
the suite without granting them Yeoman access.

### Send calendar invite

`/invitations/<uuid>/send-calendar/` — email a calendar invite (via
`keel.calendar`) to one or more recipients. The recipients are stored
on the invitation in `calendar_sent_to` along with the time and the
sender, so future audits can see who got it.

### Push to external calendar

Invitations in **Accepted**, **Tentative**, or **Delegated** status can
be pushed to Outlook / Exchange via `keel.calendar.push_event`. The
external event ID is stored as `calendar_event_id` and the timestamp as
`calendar_pushed_at`. Cancelling a scheduled invitation calls back to
`keel.calendar.cancel_event` so the external event is removed.

---

## Map

`/map/` — geographic plot of in-person and hybrid invitations. Each
marker is one invitation, colored by status. Use it to spot scheduling
clusters, evaluate driving distance from the principal's reference
addresses, and plan travel days.

Geocoding runs automatically on save when an address is present and
coordinates are not yet recorded. If geocoding fails, the invitation is
still created — it just doesn't appear on the map until staff fix the
address.

---

## Public Intake

`/invite/` — the public-facing form anyone can use to request the
principal's time. The form captures submitter identity, event details,
location/virtual fields, attachments, and contextual flags (press
expected, will-be-recorded, surrogate-OK).

When submitted, Yeoman:

1. Creates an `Invitation` row in the **received** status.
2. Geocodes the venue address if present.
3. Fires an `invitation_received` notification to schedulers and
   administrators in the agency.
4. Issues a `status_token` UUID to the submitter so they can return to
   `/invite/status/<token>/` and check progress without logging in.
5. (If configured) Pushes the submitter to Beacon as a contact via the
   intake API. See [Beacon CRM Sync](#beacon-crm-sync).

There is also a programmatic intake endpoint at
`/api/v1/intake/invitation/` (bearer-token auth) for automation —
e.g. forwarding a public-website form to Yeoman, or re-pushing
invitations from a legacy system.

### Submitter status page

`/invite/status/<status_token>/` — anyone holding the token URL can
see the current status of their invitation, the assigned coordinator's
name (when available), and the event date once confirmed. No internal
notes, no attachments other than the ones the submitter uploaded
themselves, no PII about other invitations.

---

## Reports & Exports

`/reports/` — activity dashboard:

- Invitation volume by month / quarter.
- Acceptance rate.
- Median time-to-decision and time-to-schedule.
- Breakdowns by format, modality, and tag.
- Top organizations and top regions.

### CSV export

`/reports/export/` — download a CSV of every invitation (filtered by
the current report parameters) with status, dates, assignee, principal,
delegate, format, modality, and outcome fields. Suitable for finance
or annual-report rollups.

---

## Beacon CRM Sync

When the suite is deployed with Beacon, Yeoman can push every
submitter to Beacon as a contact, capturing the speaking-engagement
relationship.

### Add to Beacon

On an invitation detail page, an Administrator sees an **Add to
Beacon** control if `BEACON_INTAKE_URL` and `BEACON_INTAKE_API_KEY` are
configured. Click it, and Yeoman:

1. Posts the submitter to Beacon's intake API.
2. Records the resulting Beacon contact ID on the invitation
   (`beacon_contact_id`).
3. Sets `beacon_status='added'` and stamps the time + actor.
4. Drops a provenance entry on the Beacon contact pointing back to
   this Yeoman invitation, so a Beacon user can see where the contact
   came from.

If the integration isn't configured, the button is **hidden** —
there are no silent no-ops. The control reappears automatically once
Beacon is reachable.

### Skip

Use the **Skip** control to mark a submitter as intentionally not added
(`beacon_status='declined'`). This prevents the "Add to Beacon" prompt
from re-appearing on every invitation review.

---

## Helm Inbox

Yeoman exposes `/api/v1/helm-feed/inbox/` — Helm's per-user companion
endpoint. When you open Helm's **Today** tab, the **Awaiting Me** column
queries this endpoint and lists Yeoman invitations where you are the
gating dependency:

- Invitations where you are the **assigned coordinator** in an open
  status (received, under review, accepted) — labeled "Coordinate:
  &lt;event name&gt;".
- Invitations where you are the **principal** — labeled "Speak:
  &lt;event name&gt;".
- Invitations where you are the **delegate** — labeled "Cover for:
  &lt;event name&gt;".

The event_date drives the due_date. The link returns you to the
Yeoman invitation detail page in one hop.

---

## Notifications

Yeoman's notification catalog (event types you may receive):

| Event | When it fires |
|---|---|
| `invitation_received` | A new invitation was submitted via the public form. Routes to schedulers and administrators. |
| `invitation_assigned` | An invitation was claimed or assigned to you. |
| `invitation_delegated` | An invitation was delegated to you. |
| `invitation_accepted` | An invitation was accepted (email channel by default). |
| `invitation_declined` | An invitation was declined (email channel by default). |
| `invitation_scheduled` | An invitation was pushed to the calendar. |
| `invitation_status_changed` | The status of an invitation you're on changed (in-app channel by default). |

Channels (in-app + email) are user-configurable at
`/notifications/preferences/`. The link is in the sidebar user-menu
dropdown.

---

## Principal Settings

`/settings/principal/` — Administrator-only configuration of the
principal whose time Yeoman is scheduling. Captures:

- **Display name** — e.g. "Commissioner O'Keefe".
- **Title** — e.g. "Commissioner of Economic Development".
- **Email** + **phone** — internal contact info.
- **Notes** — anything reviewers should know (preferred briefing
  format, dietary needs for receptions, etc.).
- **Reference addresses** — named locations (Home, Office, Capitol)
  used to compute driving distance from incoming invitations. One
  address can be marked the default; sort order controls how they
  appear on each invitation detail page.

There is one principal profile per agency. If your deployment serves
multiple principals, use multiple agencies (each with its own users
and invitations).

---

## Status Reference

| Status | Meaning |
|---|---|
| **Received** | Just arrived from intake. Untouched by staff. |
| **Under Review** | Staff has started triage. |
| **Needs Info** | Waiting on the submitter to clarify date, format, audience, etc. |
| **Accepted** | Confirmed — the principal will attend. |
| **Tentative** | Soft yes pending a final calendar slot. |
| **Delegated** | A deputy will attend in the principal's place. |
| **Scheduled** | Pushed to the external calendar. |
| **Completed** | Event has occurred and been wrapped. |
| **Declined** | Not attending. Comment required to enter. |
| **Cancelled** | Event was cancelled before it occurred. |

### Priority

Low, Normal, High, Urgent. Drives sort in the queue and the priority
field on Helm's Awaiting Me payload.

### Format

Presentation, Keynote, Panel Moderator, Panel Participant, Site Visit,
Roundtable, Ribbon Cutting, Meeting, Reception, Conference, Fireside
Chat, Tour, Other.

### Modality

In Person, Virtual, Hybrid.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| **⌘K** / **Ctrl+K** | Open the suite-wide search modal. |

---

## Support

- **Email** — info@docklabs.ai (1–2 business day response).
- **Feedback widget** — bottom-right corner of every page; routes to
  the shared support queue.
- **Per-product help** — for questions specific to Helm, Beacon, or
  any other peer product, open the help link inside that product.

---

*Last updated: 2026-04-30.*

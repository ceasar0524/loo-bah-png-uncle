## ADDED Requirements

### Requirement: Share LIFF page

The system SHALL expose a GET `/liff/share` Flask route that returns an HTML page suitable for display as a LINE LIFF app.

The page SHALL accept `store` and `lat`/`lng` query parameters.

On load, the page SHALL call `liff.shareTargetPicker()` with a Flex Message containing:
- Store name
- Google Maps link derived from lat/lng
- The current user's title and title number (fetched from `/api/user-title` using the LIFF access token)
- A fixed bot join invitation line

After the user selects a target and the share completes, the LIFF page SHALL close automatically.

The page SHALL be registered as a separate LIFF app in LINE Developers Console.

#### Scenario: User opens share LIFF and selects a target

- **WHEN** a user opens `/liff/share?store=<store_name>&lat=<lat>&lng=<lng>` inside LINE
- **THEN** the page SHALL immediately invoke `liff.shareTargetPicker()` with the store Flex Message
- **AND** after the user selects a contact or group and confirms, the LIFF page SHALL close

#### Scenario: Share target picker dismissed

- **WHEN** a user opens the share LIFF page
- **AND** dismisses the shareTargetPicker without selecting a target
- **THEN** the LIFF page SHALL close without sending any message

---

### Requirement: User title API endpoint

The system SHALL expose a GET `/api/user-title` endpoint, accessible with a valid LIFF access token, that returns the current user's title and title number.

The response SHALL be JSON: `{ "title": "魯肉飯勇者", "title_number": 12, "display": "魯肉飯勇者#12" }`.

If the user has no title record, the response SHALL return the default title 「無職轉生者」with a suffix derived from the user ID.

#### Scenario: User title API returns title

- **WHEN** a GET request is made to `/api/user-title` with a valid LINE access token in the Authorization header
- **THEN** the system SHALL return the user's current title and title number as JSON

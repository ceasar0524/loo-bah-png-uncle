# line-bot-webhook Specification

## Purpose

TBD - created by archiving change 'line-bot-webhook-interface'. Update Purpose after archive.

## Requirements

### Requirement: LINE webhook endpoint

The system SHALL expose a POST `/webhook` endpoint that accepts LINE Messaging API webhook events.

The endpoint SHALL verify the `X-Line-Signature` header using the `LINE_CHANNEL_SECRET` environment variable. Requests with an invalid or missing signature SHALL be rejected with HTTP 400.

Valid requests SHALL be acknowledged with HTTP 200 regardless of processing outcome.

#### Scenario: Valid webhook request received

- **WHEN** a POST request arrives at `/webhook` with a valid `X-Line-Signature`
- **THEN** the system SHALL return HTTP 200 and process the event payload

#### Scenario: Invalid signature rejected

- **WHEN** a POST request arrives at `/webhook` with an invalid or missing `X-Line-Signature`
- **THEN** the system SHALL return HTTP 400 and discard the request


<!-- @trace
source: line-bot-webhook-interface
updated: 2026-03-27
code:
  - app.py
  - requirements.txt
  - .env.example
-->

---
### Requirement: Image message handling

The system SHALL handle LINE `MessageEvent` events where the message type is `ImageMessageContent`.

Upon receiving an image message, the system SHALL:
1. Download the image binary from LINE's content server using the message ID
2. Pass the image to `pipeline.run()` via a temporary file
3. Reply to the user with the returned string using LINE's Reply Message API
4. Delete the temporary file after pipeline execution completes or fails

#### Scenario: User sends a photo

- **WHEN** a LINE user sends an image message to the bot
- **THEN** the system SHALL download the image, run the pipeline, and reply with the uncle's response string

#### Scenario: Pipeline error during image processing

- **WHEN** `pipeline.run()` raises an exception
- **THEN** the system SHALL reply with an in-character fallback message and SHALL NOT propagate the exception to LINE


<!-- @trace
source: line-bot-webhook-interface
updated: 2026-03-27
code:
  - app.py
  - requirements.txt
  - .env.example
-->

---
### Requirement: Non-image message handling

The system SHALL silently ignore all non-image message events. No reply SHALL be sent for text messages, stickers, or other message types.

#### Scenario: User sends a text message

- **WHEN** a LINE user sends a text message to the bot
- **THEN** the system SHALL not reply and shall return HTTP 200 to LINE


<!-- @trace
source: line-bot-webhook-interface
updated: 2026-03-27
code:
  - app.py
  - requirements.txt
  - .env.example
-->

---
### Requirement: Environment variable configuration

The system SHALL require the following environment variables at startup:
- `LINE_CHANNEL_SECRET`: used to verify webhook signatures
- `LINE_CHANNEL_ACCESS_TOKEN`: used to authenticate Reply Message API calls

The application SHALL fail to start if either variable is missing.

#### Scenario: Missing environment variable at startup

- **WHEN** either `LINE_CHANNEL_SECRET` or `LINE_CHANNEL_ACCESS_TOKEN` is not set
- **THEN** the application SHALL raise an error and exit before accepting any requests


<!-- @trace
source: line-bot-webhook-interface
updated: 2026-03-27
code:
  - app.py
  - requirements.txt
  - .env.example
-->

---
### Requirement: Deployment target

The system SHALL be deployable to GCP Cloud Run via a Docker image built from `Dockerfile`. The webhook endpoint SHALL be accessible over HTTPS as required by LINE Messaging API.

The `Dockerfile` SHALL pre-download the CLIP model at build time so that cold starts do not trigger model downloads at request time.

The three required environment variables (`ANTHROPIC_API_KEY`, `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`) SHALL be injected via Cloud Run environment variable configuration, not baked into the image.

The reply from the bot SHALL appear in the user's LINE conversation thread — the same chat window where the user sent the image.

#### Scenario: Bot reply appears in LINE chat

- **WHEN** the pipeline completes and the Reply Message API call succeeds
- **THEN** the uncle's response SHALL appear as a message in the user's LINE conversation with the bot

#### Scenario: Cloud Run deployment via GitHub push

- **WHEN** a commit is pushed to the main branch on GitHub
- **THEN** Cloud Run SHALL automatically build and deploy the updated image via Continuous Deployment integration

<!-- @trace
source: line-bot-webhook-interface
updated: 2026-03-27
code:
  - app.py
  - requirements.txt
  - .env.example
-->

---
### Requirement: Quick Reply button after recognition response

After sending a recognition response where `is_lu_rou_fan` is true and matches is non-empty, the system SHALL append a Quick Reply button labeled「找附近類似的 📍」to the response message.

#### Scenario: Quick Reply button shown after successful recognition

- **WHEN** the recognition result has `is_lu_rou_fan: true` and at least one store match
- **THEN** the LINE response SHALL include a Quick Reply button labeled「找附近類似的 📍」

#### Scenario: Quick Reply button not shown for non-lu-rou-fan

- **WHEN** the recognition result has `is_lu_rou_fan: false`
- **THEN** the LINE response SHALL NOT include the Quick Reply button


<!-- @trace
source: nearby-recommendation
updated: 2026-04-10
code:
  - app.py
  - data/store_notes.json
  - haiku_features_cache_v2.json
  - src/nearby_search/__init__.py
  - eval_dino.py
  - src/nearby_search/searcher.py
  - src/uncle_persona/persona.py
  - src/pipeline.py
  - index_vit_l14.npz
-->

---
### Requirement: Handle Quick Reply button tap

When the user taps the Quick Reply button, the system SHALL reply with a location-request message asking the user to share their current location.

#### Scenario: User taps Quick Reply button

- **WHEN** the system receives a postback or message event matching the Quick Reply action
- **THEN** the system SHALL send a message prompting the user to share their location


<!-- @trace
source: nearby-recommendation
updated: 2026-04-10
code:
  - app.py
  - data/store_notes.json
  - haiku_features_cache_v2.json
  - src/nearby_search/__init__.py
  - eval_dino.py
  - src/nearby_search/searcher.py
  - src/uncle_persona/persona.py
  - src/pipeline.py
  - index_vit_l14.npz
-->

---
### Requirement: Handle location message

The system SHALL handle LINE location message events. Upon receiving a location message, the system SHALL retrieve the stored query vector for that user, run nearby store search, and send the uncle persona's nearby recommendation response.

#### Scenario: Location received with valid session

- **WHEN** a location message is received and a query vector exists in session for that user
- **THEN** the system SHALL run nearby store search and return the uncle persona recommendation response

#### Scenario: Location received with expired session

- **WHEN** a location message is received but no query vector exists in session for that user
- **THEN** the system SHALL respond asking the user to send a photo first

<!-- @trace
source: nearby-recommendation
updated: 2026-04-10
code:
  - app.py
  - data/store_notes.json
  - haiku_features_cache_v2.json
  - src/nearby_search/__init__.py
  - eval_dino.py
  - src/nearby_search/searcher.py
  - src/uncle_persona/persona.py
  - src/pipeline.py
  - index_vit_l14.npz
-->
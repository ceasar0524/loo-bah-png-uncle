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

The system SHALL handle the following text keywords in `handle_text`:
- 隨機驚喜: triggers random nearby recommendation flow
- 巷子口: triggers hidden gems district selection
- 個人化: triggers the taste preference quiz flow
- 統計 (admin only): returns usage statistics

All other text messages SHALL be silently ignored. No reply SHALL be sent.

#### Scenario: User sends 個人化

- **WHEN** a LINE user sends the text message「個人化」
- **THEN** the system SHALL reply with the first taste quiz question and Quick Reply buttons
- **AND** the system SHALL store the quiz state in the user's session

#### Scenario: User sends an unrecognized text message

- **WHEN** a LINE user sends a text message that does not match any keyword
- **THEN** the system SHALL not reply and SHALL return HTTP 200 to LINE


<!-- @trace
source: personal-recommendation
updated: 2026-04-19
code:
  - app.py
  - data/store_hours.json
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

The system SHALL handle LINE location message events. Upon receiving a location message, the system SHALL retrieve the stored session value for that user and branch based on the value:

- If the session value is `"__random__"`: run `search_random_nearby_store` (with `seen` set) and send a Flex Message recommendation
- If the session value is a store name: run `search_nearby_stores` and send a Flex Message recommendation

The session SHALL store a `seen` set tracking all stores recommended in the current random surprise flow. When `search_random_nearby_store` returns None (all stores seen), the system SHALL reset `seen` and retry once.

#### Scenario: Location received with valid session (style match)

- **WHEN** a location message is received and the session contains a store name (not `"__random__"`)
- **THEN** the system SHALL run nearby store search and return the uncle persona recommendation as a Flex Message

#### Scenario: Location received with random surprise session

- **WHEN** a location message is received and the session value is `"__random__"`
- **THEN** the system SHALL run `search_random_nearby_store` with the current `seen` set, add the result to `seen`, and return a Flex Message recommendation

#### Scenario: All nearby stores seen — auto reset

- **WHEN** `search_random_nearby_store` returns None because all stores within 5 km have been seen
- **THEN** the system SHALL reset `seen` and call `search_random_nearby_store` again with an empty `seen`

#### Scenario: Location received with expired session

- **WHEN** a location message is received but no session exists for that user
- **THEN** the system SHALL respond asking the user to send a photo first


<!-- @trace
source: random-surprise
updated: 2026-04-13
code:
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_5.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_10.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_2.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_3.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_7.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_1.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_6.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_13.jpg
  - src/nearby_search/__init__.py
  - index_dino_crop.npz
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_10.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_10.jpg
  - haiku_features_cache_v2.json
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_1.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_10.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_10.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_11.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_5.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_12.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_13.png
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_12.jpg
  - src/uncle_persona/persona.py
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_10.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_8.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_10.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_1.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_2.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_15.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_1.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_5.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_10.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_10.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_6.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_10.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_6.jpg
  - eval_dino.py
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_2.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_6.jpg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_7.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_3.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_6.jpg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_11.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_5.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_11.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_1.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_8.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_1.jpeg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_10.jpg
  - src/nearby_search/searcher.py
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_7.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_9.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_1.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_11.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_10.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_1.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_11.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_1.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_1.png
  - index_vit_l14.npz
  - photos_sauce_crop/天天利美食坊（稠）/photo_5.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_3.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_11.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_7.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_1.jpeg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_10.jpg
  - app.py
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_11.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_14.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_1.jpg
-->

---
### Requirement: Random surprise trigger via text keyword

The system SHALL handle the text keyword「隨機驚喜」in `handle_text`. Upon receiving this keyword, the system SHALL:
1. Reply with a prompt message asking the user to share their location
2. Store the special session value `"__random__"` for that user

#### Scenario: User sends 隨機驚喜

- **WHEN** a LINE user sends the text message「隨機驚喜」
- **THEN** the system SHALL reply with a location-request Quick Reply message and store `"__random__"` in the user's session

<!-- @trace
source: random-surprise
updated: 2026-04-13
code:
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_5.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_10.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_2.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_3.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_7.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_1.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_6.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_13.jpg
  - src/nearby_search/__init__.py
  - index_dino_crop.npz
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_10.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_10.jpg
  - haiku_features_cache_v2.json
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_1.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_10.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_10.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_11.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_5.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_12.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_13.png
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_1.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_12.jpg
  - src/uncle_persona/persona.py
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_10.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_8.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_10.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_1.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_2.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_15.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_1.jpg
  - photos_sauce_crop/曉迪筒仔米糕（中正區）（水）/photo_5.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_10.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_10.jpg
  - photos_sauce_crop/阿英滷肉飯（稠）/photo_4.jpg
  - photos_sauce_crop/雙胖子（稠）   /photo_6.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_10.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_6.jpg
  - eval_dino.py
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_2.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_6.jpg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_11.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_7.jpg
  - photos_sauce_crop/天天利美食坊（稠）/photo_3.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/啊興阿滷肉飯（稠）/photo_6.jpg
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_11.jpg
  - photos_sauce_crop/明志派出所對面滷肉飯(泰山區)（水）/photo_5.jpg
  - photos_sauce_crop/五燈獎豬腳滷肉飯（三重區）（水）/photo_11.jpg
  - photos_sauce_crop/北北車魯肉飯（中正區）（稠）/photo_1.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_8.jpg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_1.jpeg
  - photos_sauce_crop/黃記魯肉飯（中山區）（稠）/photo_10.jpg
  - src/nearby_search/searcher.py
  - photos_sauce_crop/店小二魯肉飯（三重區）（水）/photo_1.jpg
  - photos_sauce_crop/矮仔財滷肉飯（北投區）（稠）/photo_7.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_9.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_1.jpg
  - photos_sauce_crop/今大魯肉飯（三重區）（稠）/photo_11.jpg
  - photos_sauce_crop/龍記小吃店（中山區）（水）/photo_10.jpg
  - photos_sauce_crop/阿興魯肉飯（中和區）（水）/photo_1.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_11.jpg
  - photos_sauce_crop/313號鵝肉擔（北投區）（水）/photo_1.jpg
  - photos_sauce_crop/滷三塊五花肉飯（北投區）（稠）/photo_1.png
  - index_vit_l14.npz
  - photos_sauce_crop/天天利美食坊（稠）/photo_5.jpg
  - photos_sauce_crop/大稻埕魯肉飯（大同區）（稠）/photo_3.jpg
  - photos_sauce_crop/司機俱樂部（松山區）（水）/photo_11.jpg
  - photos_sauce_crop/小王煮瓜（水）/photo_7.jpg
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_1.jpeg
  - photos_sauce_crop/富霸王豬腳（中山區）（水）/photo_10.jpg
  - app.py
  - photos_sauce_crop/晴光小吃(林口區)（水）/photo_11.jpg
  - photos_sauce_crop/玉女號滷肉飯（稠）/photo_3.jpg
  - photos_sauce_crop/一甲子餐飲（萬華區）（水）/photo_14.jpg
  - photos_sauce_crop/珠記大橋頭油飯(大同區)（水）/photo_1.jpg
-->

---
### Requirement: Handle preference save confirmation

The system SHALL handle「儲存 ✅」and「不用 ❌」responses when a `taste_save_pending` session key exists.

#### Scenario: User taps 儲存

- **WHEN** a user taps「儲存 ✅」and `taste_save_pending` exists in the session
- **THEN** the system SHALL write preferences to Firestore
- **AND** clear `taste_save_pending` from the session
- **AND** set session store to `__taste__` and prompt for location

#### Scenario: User taps 不用

- **WHEN** a user taps「不用 ❌」and `taste_save_pending` exists in the session
- **THEN** the system SHALL clear `taste_save_pending` from the session
- **AND** set session store to `__taste__` and prompt for location


<!-- @trace
source: save-taste-preference
updated: 2026-04-19
code:
  - app.py
-->

---
### Requirement: Handle 直接用 and 重新填 Quick Reply responses

The system SHALL handle「直接用 ✅」and「重新填 🔄」when a `taste_loaded` session key exists.

#### Scenario: User taps 直接用

- **WHEN** a user taps「直接用 ✅」and `taste_loaded` exists in the session
- **THEN** the system SHALL use the loaded preferences, set session store to `__taste__`, and prompt for location

#### Scenario: User taps 重新填

- **WHEN** a user taps「重新填 🔄」and `taste_loaded` exists in the session
- **THEN** the system SHALL clear `taste_loaded` from the session and start the quiz from question 1

<!-- @trace
source: save-taste-preference
updated: 2026-04-19
code:
  - app.py
-->

---
### Requirement: Handle taste quiz Quick Reply responses

The system SHALL handle Quick Reply responses during an active taste quiz session.

When a user has an active `taste_quiz` session and sends a message matching one of the quiz answer options, the system SHALL record the answer and advance the quiz.

#### Scenario: User answers a quiz question mid-flow

- **WHEN** a user with an active `taste_quiz` session taps a Quick Reply button
- **THEN** the system SHALL store the answer, advance to the next question or prompt for location if all four answers are collected


<!-- @trace
source: personal-recommendation
updated: 2026-04-19
code:
  - app.py
  - data/store_hours.json
-->

---
### Requirement: Handle location message with taste session

The system SHALL handle location messages when the user has a completed taste quiz session (`__taste__`).

Upon receiving the location, the system SHALL run taste-based store matching and reply with a Flex Message listing 2–3 stores.

#### Scenario: Location received with taste session

- **WHEN** a location message is received and the session value is `"__taste__"`
- **THEN** the system SHALL run taste-based matching using stored preferences and return a Flex Message recommendation


<!-- @trace
source: personal-recommendation
updated: 2026-04-19
code:
  - app.py
  - data/store_hours.json
-->

---
### Requirement: 附近巷仔口店家 keyword

The system SHALL handle the keyword「附近巷仔口店家」as a dedicated trigger for nearby hidden gems lookup using a saved location.

「巷仔口」SHALL always show the standard district selection menu regardless of session state.

#### Scenario: User sends 附近巷仔口店家 with saved location

- **WHEN** a user sends「附近巷仔口店家」
- **AND** a `last_location` is saved in the session
- **THEN** the system SHALL query hidden gems within 3 km and return a Flex Message (up to 3 stores)
- **AND** the system SHALL clear `last_location` from the session

#### Scenario: User sends 附近巷仔口店家 without saved location

- **WHEN** a user sends「附近巷仔口店家」
- **AND** no `last_location` exists in the session
- **THEN** the system SHALL not reply

<!-- @trace
source: personal-recommendation
updated: 2026-04-19
code:
  - app.py
  - data/store_hours.json
-->

---
### Requirement: Footprint keyword handler

The system SHALL handle the keyword「足跡」as a top-level message trigger.

When a user sends「足跡」, the system SHALL query Firestore for that user's check-in records and reply with the footprint Flex Message.

#### Scenario: User sends 足跡

- **WHEN** a user sends the text「足跡」
- **THEN** the system SHALL read check-in records from `user_footprint/<user_id>/records/`
- **AND** reply with the footprint summary Flex Message


<!-- @trace
source: luroufan-footprint
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

---
### Requirement: Check-in confirmation handler

The system SHALL handle the message「就是這家 ✅」as a check-in confirmation trigger.

The system SHALL look up the pending check-in store name stored in the user session under `pending_checkin`, write the check-in record, and clear the session state.

#### Scenario: User confirms check-in

- **WHEN** a user sends「就是這家 ✅」
- **AND** a `pending_checkin` entry exists in the user session
- **THEN** the system SHALL write the check-in record to Firestore
- **AND** clear `pending_checkin` from the session
- **AND** reply with a confirmation message


<!-- @trace
source: luroufan-footprint
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->

---
### Requirement: Check-in rescue handler

The system SHALL handle the message「打卡這碗 📍」as a check-in rescue trigger.

The system SHALL set a `checkin_rescue` flag in the user session and send a location request.

When the subsequent location event is received with `checkin_rescue` active, the system SHALL search nearby stores (500 m) across both databases and present them as Quick Reply buttons.

#### Scenario: User initiates check-in rescue

- **WHEN** a user sends「打卡這碗 📍」
- **THEN** the system SHALL set `checkin_rescue: true` in the session
- **AND** reply with a location request using LocationAction Quick Reply

#### Scenario: Location received during check-in rescue

- **WHEN** a location event is received
- **AND** the user session contains `checkin_rescue: true`
- **THEN** the system SHALL search `store_notes` and `hidden_gems` for stores within 500 m
- **AND** present results as Quick Reply buttons (up to 5 stores)
- **AND** clear `checkin_rescue` from the session

<!-- @trace
source: luroufan-footprint
updated: 2026-04-22
code:
  - src/pipeline.py
  - app.py
  - .github/workflows/deploy.yml
-->
---
### Requirement: 下一抽 keyword handler

The system SHALL handle the keyword「下一抽 🎲」as a re-draw trigger for random recommendation.

When received, the system SHALL read `last_location` from the session and run the full random recommendation logic without requiring the user to re-share their location.

#### Scenario: User sends 下一抽

- **WHEN** a user sends「下一抽 🎲」
- **AND** `last_location` exists in the session
- **THEN** the system SHALL run random recommendation logic using the saved location and return a new recommendation

#### Scenario: No saved location

- **WHEN** a user sends「下一抽 🎲」
- **AND** no `last_location` exists in the session
- **THEN** the system SHALL reply with a location prompt

<!-- @trace
source: random-surprise-redraw
updated: 2026-05-11
code:
  - app.py
-->

---
### Requirement: 肉盾 text trigger

The system SHALL handle the text「肉盾」as a skill trigger for users with title「肉汁騎士」or above.

#### Scenario: 肉盾 trigger with sufficient title

- **WHEN** a user with Lv.1+ title sends the text「肉盾」
- **THEN** the system SHALL enter the meat shield evaluation flow as defined in `title-skill-meat-shield`

#### Scenario: 肉盾 trigger with insufficient title

- **WHEN** a user with title「無職轉生者」sends the text「肉盾」
- **THEN** the system SHALL reply indicating the skill has not been unlocked yet


<!-- @trace
source: title-unlock-skills
updated: 2026-05-16
code:
  - assets/rpg_map.png
  - Dockerfile
  - data/hidden_gems.json
  - data/store_hours.json
  - app.py
  - .github/workflows/deploy.yml
-->

---
### Requirement: 魯拉 text trigger

The system SHALL handle the text「魯拉」as a skill trigger for users with title「魯肉飯勇者」or above.

#### Scenario: 魯拉 trigger with sufficient title

- **WHEN** a user with Lv.3+ title sends the text「魯拉」
- **THEN** the system SHALL enter the Lura navigation flow as defined in `title-skill-lura`

#### Scenario: 魯拉 trigger with insufficient title

- **WHEN** a user with title below「魯肉飯勇者」sends the text「魯拉」
- **THEN** the system SHALL reply indicating the skill has not been unlocked yet


<!-- @trace
source: title-unlock-skills
updated: 2026-05-16
code:
  - assets/rpg_map.png
  - Dockerfile
  - data/hidden_gems.json
  - data/store_hours.json
  - app.py
  - .github/workflows/deploy.yml
-->

---
### Requirement: 號令 text trigger

The system SHALL handle the text「號令」as a skill trigger.

For users with title「魯肉飯大神」, the system SHALL enter the decree posting flow.

For all other users, the system SHALL display the Decree Wall (today's recommendations).

#### Scenario: 號令 trigger for 大神 user

- **WHEN** a user with title「魯肉飯大神」sends the text「號令」
- **THEN** the system SHALL enter the decree posting flow as defined in `title-skill-decree`

#### Scenario: 號令 trigger for non-大神 user

- **WHEN** a user with title below「魯肉飯大神」sends the text「號令」
- **THEN** the system SHALL display the Decree Wall

<!-- @trace
source: title-unlock-skills
updated: 2026-05-16
code:
  - assets/rpg_map.png
  - Dockerfile
  - data/hidden_gems.json
  - data/store_hours.json
  - app.py
  - .github/workflows/deploy.yml
-->
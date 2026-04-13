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
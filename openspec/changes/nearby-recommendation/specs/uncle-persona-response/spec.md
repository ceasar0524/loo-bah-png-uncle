# uncle-persona-response delta Specification

## ADDED Requirements

### Requirement: Nearby recommendation response

The system SHALL generate an in-character uncle persona response for nearby store recommendations. The response SHALL reference the style of the original queried bowl and name the recommended stores with brief in-character commentary.

When no nearby stores are found, the uncle SHALL respond in-character acknowledging that there are no similar stores nearby.

#### Scenario: Nearby stores found

- **WHEN** the nearby search returns one or more stores
- **THEN** the uncle persona SHALL generate a response naming the recommended stores with distance information and in-character flavor commentary
- **THEN** the response SHALL include at most 2 stores, ordered by distance ascending (nearest first)
- **THEN** each recommended store SHALL include its distance in kilometers (e.g., "距你約 1.2 公里"), embedded naturally within the uncle's in-character commentary
- **THEN** each recommended store SHALL include a Google Maps static URL (`https://maps.google.com/?q=<lat>,<lng>`) as a navigation link

#### Scenario: No nearby stores found — stores exist but none match style

- **WHEN** the nearby search returns an empty list and `any_in_radius=True`
- **THEN** the uncle persona SHALL respond acknowledging stores were found nearby but none matched the style, in the spirit of "找了一圈，附近沒有風格相近的，大叔默默走去面壁 🧱"

#### Scenario: No nearby stores found — no stores in area

- **WHEN** the nearby search returns an empty list and `any_in_radius=False`
- **THEN** the uncle persona SHALL respond acknowledging the area has no coverage yet, in the spirit of "殘念！🏪 這附近大叔還在開發中，敬請期待... 🙇"

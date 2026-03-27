## MODIFIED Requirements

### Requirement: Non-lu-rou-fan input handling

The system SHALL return a hardcoded in-character response when `is_lu_rou_fan` is false, without calling the Claude API.

The fixed response SHALL be: "所以我說，那個滷肉呢？大叔千里迢迢來鑑定，你給我看這個？"

#### Scenario: Non-lu-rou-fan input returns hardcoded response

- **WHEN** visual.is_lu_rou_fan is false
- **THEN** the module SHALL immediately return the hardcoded uncle response without calling the Claude API, regardless of confidence level

### Requirement: Store background knowledge

When a store match is found and that store has a corresponding entry in `data/store_notes.json`, the system SHALL read that store's `notes` (background story) and `known_toppings` (toppings known to be served there) and incorporate them into the uncle's response.

When the result is a tie and all tied stores have entries in `data/store_notes.json` with `known_toppings` defined, the system SHALL compute the intersection of all tied stores' `known_toppings` and use that intersection as the filter for CLIP-detected toppings. Only toppings present in the intersection SHALL be passed to the uncle.

If the intersection of `known_toppings` is empty, the system SHALL report no toppings regardless of CLIP detections.

If any tied store lacks a `known_toppings` entry, the system SHALL fall back to trusting CLIP detections unfiltered.

The uncle SHALL only mention toppings or characteristics that are supported by either the visual recognition result or the store background knowledge. Fabricating details not grounded in either source is forbidden.

#### Scenario: Store background knowledge available

- **WHEN** the matched store has an entry in `data/store_notes.json` with `notes` and/or `known_toppings`
- **THEN** the response SHALL reference relevant details from that entry (e.g., the shop's story, signature toppings), blended naturally into the uncle's voice

#### Scenario: No store background knowledge available

- **WHEN** the matched store has no entry in `data/store_notes.json`
- **THEN** the response SHALL rely solely on the visual recognition results, with no fabricated store details

#### Scenario: Tie with known_toppings intersection empty

- **WHEN** matching.is_tie is true and all tied stores have known_toppings defined as empty lists
- **THEN** the system SHALL report no toppings to the uncle, overriding any CLIP detections

#### Scenario: Tie with known_toppings intersection non-empty

- **WHEN** matching.is_tie is true and the intersection of all tied stores' known_toppings is non-empty
- **THEN** the system SHALL pass only the intersected toppings to the uncle

#### Scenario: Tie with missing known_toppings entry

- **WHEN** matching.is_tie is true and at least one tied store has no known_toppings entry in store_notes.json
- **THEN** the system SHALL fall back to trusting CLIP detections unfiltered

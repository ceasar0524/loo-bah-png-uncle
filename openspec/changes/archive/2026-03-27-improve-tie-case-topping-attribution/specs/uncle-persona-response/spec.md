## MODIFIED Requirements

### Requirement: Store background knowledge

When a store match is found and that store has a corresponding entry in `data/store_notes.json`, the system SHALL read that store's `notes` (background story) and `known_toppings` (toppings known to be served there) and incorporate them into the uncle's response.

When the result is a tie and all tied stores have entries in `data/store_notes.json` with `known_toppings` defined, the system SHALL compute the **union** of all tied stores' `known_toppings` and split toppings into two categories:

1. **Shared toppings**: toppings present in ALL tied stores' `known_toppings`. These SHALL be passed to the uncle as confirmed present.
2. **Exclusive toppings**: toppings present in only SOME tied stores' `known_toppings`. These SHALL be passed to the uncle with attribution indicating which store has them, and the uncle SHALL use conditional language when mentioning them (e.g., "如果是 XX 那碗的話，可能有...").

If the union of `known_toppings` is empty, the system SHALL report no toppings regardless of CLIP detections.

If any tied store lacks a `known_toppings` entry, the system SHALL fall back to trusting CLIP detections unfiltered.

The uncle SHALL only mention toppings or characteristics that are supported by either the visual recognition result or the store background knowledge. Fabricating details not grounded in either source is forbidden.

#### Scenario: Store background knowledge available

- **WHEN** the matched store has an entry in `data/store_notes.json` with `notes` and/or `known_toppings`
- **THEN** the response SHALL reference relevant details from that entry (e.g., the shop's story, signature toppings), blended naturally into the uncle's voice

#### Scenario: No store background knowledge available

- **WHEN** the matched store has no entry in `data/store_notes.json`
- **THEN** the response SHALL rely solely on the visual recognition results, with no fabricated store details

#### Scenario: Tie with shared toppings

- **WHEN** matching.is_tie is true and a topping appears in ALL tied stores' known_toppings
- **THEN** the uncle SHALL mention that topping as confirmed present, without conditional language

#### Scenario: Tie with exclusive toppings

- **WHEN** matching.is_tie is true and a topping appears in only SOME tied stores' known_toppings
- **THEN** the uncle SHALL use conditional language when mentioning that topping (e.g., "如果是 XX 那碗的話，可能有 YY"), not assert it as definitely present

#### Scenario: Tie with known_toppings union empty

- **WHEN** matching.is_tie is true and all tied stores have known_toppings defined as empty lists
- **THEN** the system SHALL report no toppings to the uncle, overriding any CLIP detections

#### Scenario: Tie with missing known_toppings entry

- **WHEN** matching.is_tie is true and at least one tied store has no known_toppings entry in store_notes.json
- **THEN** the system SHALL fall back to trusting CLIP detections unfiltered

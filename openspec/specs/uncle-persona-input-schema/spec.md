# uncle-persona-input-schema Specification

## Purpose

TBD - created by archiving change 'data-schema'. Update Purpose after archive.

## Requirements

### Requirement: Uncle persona input schema

The uncle-persona module SHALL accept an input conforming to the following structure, combining visual recognition and store matching results:

```
{
  "visual": {                  # visual recognition result (see visual-recognition-schema)
    "is_lu_rou_fan": bool,
    "confidence": float,
    "toppings": list[str],
    "pork_part": str | None,   # translated to Chinese label before passing to uncle
    "fat_ratio": str | None,   # translated to Chinese label before passing to uncle
    "sauce_color": str | None, # translated to Chinese label before passing to uncle
    "skin": str | None,
    "rice_quality": str | None
  },
  "matching": {                # store matching result (see store-matching-schema)
    "is_tie": bool,
    "matches": [
      {
        "store_name": str,
        "similarity": float,
        "confidence_level": str,
        "photo_count": int
      }
    ]
  }
}
```

Before the input is passed to the uncle-persona module, the following pre-processing SHALL be applied:

1. **Chinese label translation**: The `pork_part`, `fat_ratio`, and `sauce_color` fields SHALL be translated from their English classifier keys to their corresponding Chinese display labels. The uncle-persona module SHALL only receive Chinese labels, never raw English keys.

2. **Topping cross-filtering** (non-tie case — applied when a single matched store has `known_toppings` defined):
   - If the matched store has `known_toppings`: retain only toppings that CLIP detected AND are in `known_toppings`, then supplement with any toppings in `known_toppings` that CLIP missed.
   - If the matched store has no `known_toppings` (or there is no store match): trust CLIP results entirely without modification.

3. **Tie topping attribution** (tie case — applied when `is_tie` is true and tied stores have `known_toppings`):
   - Only the **top 2** tied stores (as ranked by the store matching result) SHALL be considered for topping attribution.
   - Compute the **union** of the top-2 tied stores' `known_toppings`.
   - Split into **shared** (present in ALL top-2 tied stores) and **exclusive** (present in only SOME top-2 tied stores).
   - Shared toppings SHALL be passed as confirmed present.
   - Exclusive toppings SHALL be passed with store attribution so the uncle can use conditional language.
   - If any of the top-2 tied stores has no `known_toppings` entry, fall back to unfiltered CLIP detections.

#### Scenario: Full input with matches

- **WHEN** both visual recognition and store matching results are available
- **THEN** the uncle-persona module SHALL accept the combined input and generate a response referencing both

#### Scenario: Input with tie result

- **WHEN** matching.is_tie is true
- **THEN** the uncle-persona module SHALL generate a tie-specific in-character response

#### Scenario: Input with empty matches

- **WHEN** matching.matches is empty and is_tie is false
- **THEN** the uncle-persona module SHALL generate a response without store recommendation

#### Scenario: Non-lu-rou-fan input

- **WHEN** visual.is_lu_rou_fan is false
- **THEN** the uncle-persona module SHALL return an in-character rejection without processing further fields

#### Scenario: Topping cross-filtering with known_toppings (non-tie)

- **WHEN** the matched store has `known_toppings` defined and is_tie is false
- **THEN** the toppings list passed to the uncle SHALL be the intersection of CLIP-detected toppings and `known_toppings`, supplemented by any `known_toppings` entries that CLIP did not detect

#### Scenario: Tie topping attribution with exclusive toppings

- **WHEN** matching.is_tie is true and a topping belongs to only some of the top-2 tied stores' known_toppings
- **THEN** the topping SHALL be passed with attribution (which store has it) so the uncle uses conditional language

#### Scenario: Topping cross-filtering without known_toppings

- **WHEN** there is no store match or the matched store has no `known_toppings`
- **THEN** the toppings list passed to the uncle SHALL be the unmodified CLIP detection result

#### Scenario: Visual fields passed as Chinese labels

- **WHEN** the input is prepared for the uncle-persona module
- **THEN** `pork_part`, `fat_ratio`, and `sauce_color` SHALL each be a Chinese display label, not an English classifier key

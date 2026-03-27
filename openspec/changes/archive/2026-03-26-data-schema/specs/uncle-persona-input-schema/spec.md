## ADDED Requirements

### Requirement: Uncle persona input schema

The uncle-persona module SHALL accept an input conforming to the following structure, combining visual recognition and store matching results:

```
{
  "visual": {                  # visual recognition result (see visual-recognition-schema)
    "is_lu_rou_fan": bool,
    "confidence": float,
    "toppings": list[str],
    "pork_part": str | None,
    "fat_ratio": str | None,
    "skin": str | None,
    "sauce_color": str | None,
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

## ADDED Requirements

### Requirement: Visual recognition result schema

The visual recognition module SHALL return a result conforming to the following structure:

```
{
  "is_lu_rou_fan": bool,
  "confidence": float,        # 0.0–1.0, overall recognition confidence
  "toppings": list[str],      # e.g. ["cilantro", "braised_egg", "bamboo_shoots"]
  "pork_part": str,           # "belly" | "fatty" | "lean" | "skin_heavy" (configurable)
  "fat_ratio": str,           # "fat_heavy" | "balanced" | "lean_heavy" (configurable)
  "skin": str,                # "with_skin" | "no_skin" (configurable)
  "sauce_color": str,         # "light" | "medium" | "dark" | "black_gold" (configurable)
  "rice_quality": str         # "fluffy" | "soft" | "mushy" (configurable)
}
```

When `is_lu_rou_fan` is false, all other fields except `confidence` SHALL be empty or None.

#### Scenario: Valid lu-rou-fan result

- **WHEN** the module successfully recognizes a lu-rou-fan image
- **THEN** the result SHALL include is_lu_rou_fan: true and all analysis fields populated

#### Scenario: Non-lu-rou-fan result

- **WHEN** the module determines the image is not lu-rou-fan
- **THEN** the result SHALL include is_lu_rou_fan: false and analysis fields set to None or empty

#### Scenario: Low confidence result

- **WHEN** overall recognition confidence is below 0.5
- **THEN** the result SHALL include is_lu_rou_fan: true (if applicable) with confidence value set accordingly

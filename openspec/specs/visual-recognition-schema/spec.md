# visual-recognition-schema Specification

## Purpose

TBD - created by archiving change 'data-schema'. Update Purpose after archive.

## Requirements

### Requirement: Visual recognition result schema

The visual recognition module SHALL return a result conforming to the following structure:

```
{
  "is_lu_rou_fan": bool,
  "confidence": float,        # 0.0–1.0, overall recognition confidence
  "toppings": list[str],      # e.g. ["cilantro", "braised_egg"]
  "bowl_color": str | None,   # "bright_green" | "olive_green" | "light_gray_green" | "white" | "yellow" | "red" | "black" | "brown" | "other"
  "bowl_shape": str | None,   # "round_bowl" | "wide_flat_plate" | "rectangular_box" | "other"
  "bowl_texture": str | None, # "matte_ceramic" | "glossy_ceramic" | "plastic" | "styrofoam" | "other"
  "pork_part": str | None,    # "belly" | "fatty" | "lean" | "skin_heavy"
  "fat_ratio": str | None,    # "fat_heavy" | "balanced" | "lean_heavy"
  "skin": str | None,         # "with_skin" | "no_skin"
  "sauce_color": str | None,  # "light" | "medium" | "dark" | "black_gold"
  "rice_quality": str | None  # "fluffy" | "soft" | "mushy"
}
```

When `is_lu_rou_fan` is false, all fields except `confidence` SHALL be empty list or None.

#### Scenario: Valid lu-rou-fan result

- **WHEN** the module successfully recognizes a lu-rou-fan image
- **THEN** the result SHALL include is_lu_rou_fan: true and all analysis fields populated

#### Scenario: Non-lu-rou-fan result

- **WHEN** the module determines the image is not lu-rou-fan
- **THEN** the result SHALL include is_lu_rou_fan: false, bowl_color/bowl_shape/bowl_texture set to None, toppings set to empty list, and all other feature fields set to None

#### Scenario: Low confidence result

- **WHEN** overall recognition confidence is below 0.5
- **THEN** the result SHALL include is_lu_rou_fan: true (if applicable) with confidence value set accordingly

## ADDED Requirements

### Requirement: Predict sauce consistency from query image

The system SHALL use a DINOv2 model (dinov2_vitb14) to classify a query image's sauce consistency as either 稠 (thick) or 水 (thin) by computing cosine similarity against reference embeddings stored in `index_dino_crop.npz`.

The prediction SHALL use center-crop preprocessing (resize to 256, center crop to 224) consistent with how the reference index was built.

The prediction SHALL use top-K nearest neighbor voting (default K=5) over the reference embeddings. The predicted class SHALL be the majority label among the top-K neighbors.

If the prediction cannot be made (model unavailable, index missing, or no clear majority), the system SHALL return `None`.

#### Scenario: Consistent query image predicts 稠

- **WHEN** a query image of a 稠-style bowl is provided
- **THEN** the predictor SHALL return "稠" based on KNN majority vote from reference embeddings

#### Scenario: Watery query image predicts 水

- **WHEN** a query image of a 水-style bowl is provided
- **THEN** the predictor SHALL return "水" based on KNN majority vote from reference embeddings

#### Scenario: Model unavailable returns None

- **WHEN** the DINOv2 model cannot be loaded or the index file does not exist
- **THEN** the predictor SHALL return `None` and log a warning

---

### Requirement: Sauce consistency tiebreak in store matching

When the KNN matching result is a tie and the top two candidates have different `sauce_consistency` labels in `store_notes.json`, the system SHALL use the DINOv2 predictor to classify the query image and promote the candidate whose label matches the prediction to first place.

The tiebreak SHALL only activate when ALL of the following conditions are met:
- `DINO_TIEBREAK_ENABLED` environment variable is set to `"true"`
- The matching result `is_tie` is `True`
- At least 2 candidates are present
- candidates[0] and candidates[1] have different `sauce_consistency` values (both must be non-empty)
- The DINOv2 prediction is not `None`

If any condition is not met, the original candidate order SHALL be returned unchanged.

#### Scenario: Tiebreak promotes matching candidate

- **WHEN** candidates[0] is labeled 稠 and candidates[1] is labeled 水 and DINOv2 predicts 水
- **THEN** candidates[1] SHALL be promoted to first place in the result list

#### Scenario: Tiebreak skipped when labels are the same

- **WHEN** candidates[0] and candidates[1] both have `sauce_consistency: "稠"`
- **THEN** the original order SHALL be returned unchanged

#### Scenario: Tiebreak skipped when feature flag is off

- **WHEN** `DINO_TIEBREAK_ENABLED` is not set or set to `"false"`
- **THEN** the sauce consistency tiebreak SHALL NOT be triggered

#### Scenario: Tiebreak skipped when prediction fails

- **WHEN** the DINOv2 predictor returns `None`
- **THEN** the original candidate order SHALL be returned unchanged

#### Scenario: Store without sauce_consistency label skipped

- **WHEN** a candidate store has no `sauce_consistency` field in store_notes
- **THEN** that candidate SHALL be treated as having no label and the tiebreak SHALL NOT activate for that pair

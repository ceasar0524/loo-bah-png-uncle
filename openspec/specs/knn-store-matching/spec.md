# knn-store-matching Specification

## Purpose

TBD - created by archiving change 'store-matching'. Update Purpose after archive.

## Requirements

### Requirement: KNN store matching

The system SHALL load the embedding index and find the K most similar photo vectors to the query embedding using cosine similarity, then determine the matching store by photo-count-normalized vote among the top-K results.

The vote for each store SHALL be normalized by dividing the raw vote count by that store's total photo count, ensuring stores with fewer photos are not disadvantaged against stores with larger photo libraries.

The default value of K SHALL be 5. K SHALL be configurable by the caller.

#### Scenario: Store identified by normalized vote

- **WHEN** a query embedding is provided and K=5
- **THEN** the system SHALL find the 5 most similar vectors in the index, compute each store's normalized vote (raw vote count / photo_count), and return the store with the highest normalized vote

#### Scenario: Normalized vote corrects for unequal photo counts

- **WHEN** store A has 15 photos and store B has 3 photos and both receive 2 votes in top-K
- **THEN** store B's normalized vote (2/3) SHALL be higher than store A's (2/15), and store B SHALL win

#### Scenario: Similarity score computed as average

- **WHEN** a winning store is determined by majority vote
- **THEN** the similarity score SHALL be the average cosine similarity of the winning store's vectors among the top-K results

#### Scenario: Results ordered by similarity descending

- **WHEN** multiple stores meet the similarity threshold
- **THEN** the result list SHALL be ordered by similarity score descending

---
### Requirement: Similarity threshold filtering

The system SHALL filter out stores whose computed similarity score falls below a configurable threshold (default: 0.5). An empty list SHALL be returned when no store meets the threshold.

#### Scenario: Low similarity result excluded

- **WHEN** the winning store's similarity score is below the threshold
- **THEN** the system SHALL return an empty list

#### Scenario: Threshold configurable

- **WHEN** the caller specifies a custom threshold
- **THEN** the system SHALL apply that threshold instead of the default

---
### Requirement: Tie detection

The system SHALL detect when multiple stores are sufficiently close in normalized vote count that no clear winner can be determined, and return all tied stores as candidates instead of forcing a single result.

A tie SHALL be declared when two or more stores have normalized vote counts within a configurable margin (default: 0.15) of the highest normalized vote count. This replaces the previous requirement of strictly equal normalized vote counts.

When a tie is detected and Haiku features are available, the system SHALL rank tied stores using a combined score of Haiku feature compatibility and average cosine similarity. The Haiku feature scoring SHALL use the same rules as the override mechanism (topping matches, distinctive bowl features). Stores with higher Haiku scores SHALL be ranked above stores with no Haiku score. When Haiku scores are equal, stores SHALL be ranked by average cosine similarity descending.

#### Scenario: Tie returns multiple candidates

- **WHEN** two or more stores have normalized vote counts within tie_margin of the highest normalized vote count
- **THEN** the system SHALL return a result with `is_tie: true` and all tied stores listed in the matches list, ordered by (Haiku feature score descending, average cosine similarity descending)

#### Scenario: Tie ranking uses Haiku features when available

- **WHEN** a tie is detected and haiku_features are provided
- **THEN** tied stores with detected toppings or bowl features matching their store_notes SHALL be ranked above stores with no Haiku feature match

#### Scenario: Clear majority not a tie

- **WHEN** one store has a normalized vote count that exceeds all others by more than tie_margin
- **THEN** the system SHALL proceed with normal majority vote result and `is_tie: false`

#### Scenario: Tie margin configurable

- **WHEN** the caller specifies a custom tie_margin
- **THEN** the system SHALL apply that margin instead of the default 0.15

---
### Requirement: Similarity confidence level

The system SHALL classify the match similarity into confidence levels to allow the uncle-persona to vary its language accordingly.

- **high**: similarity >= 0.8
- **medium**: 0.5 <= similarity < 0.8
- **low / no match**: similarity < 0.5 or empty matches

#### Scenario: High confidence match

- **WHEN** the winning store's similarity score is >= 0.8
- **THEN** the result SHALL include `confidence_level: "high"`

#### Scenario: Medium confidence match

- **WHEN** the winning store's similarity score is >= 0.5 and < 0.8
- **THEN** the result SHALL include `confidence_level: "medium"`

---
### Requirement: Haiku feature override for high-confidence distinctive features

After the CLIP KNN result is computed, the system SHALL apply a Haiku feature override when the classifier has detected a high-confidence distinctive visual feature that uniquely identifies a store.

The override SHALL consult `data/store_notes.json` for each store's `bowl` entry and `known_toppings`. The override scoring SHALL be:

- Bowl color match on a store marked `distinctive: true`: +0.5
- Bowl shape match on a store marked `distinctive: true`: +0.2
- Bowl texture match on a store marked `distinctive: true`: +0.3
- Cilantro (`cilantro`) detected and present in a store's `known_toppings`: +0.8
- Other topping detected and present in a store's `known_toppings`: +0.3

The override SHALL only fire when a single store reaches or exceeds the override threshold (default: 0.75) with no tie. If multiple stores reach the threshold simultaneously, the override SHALL be suppressed and the CLIP result SHALL be used.

When the override fires, the matched store SHALL be returned with `confidence_level: "high"` regardless of the underlying CLIP similarity score.

When the override does not fire, the CLIP KNN result SHALL be returned unchanged.

#### Scenario: Distinctive bowl colour alone does not trigger override when threshold is 0.75

- **WHEN** the classifier detects `bowl_color: "bright_green"` and store 晴光小吃 has `bowl.color: "bright_green"` with `distinctive: true` but no matching topping is detected
- **THEN** the score for 晴光小吃 SHALL be 0.5, which is below the 0.75 threshold, and the override SHALL NOT fire

#### Scenario: Bowl colour plus topping triggers override for 晴光

- **WHEN** the classifier detects `bowl_color: "bright_green"` and `pickled_radish` in toppings, and store 晴光小吃 has `bowl.color: "bright_green"` with `distinctive: true` and `pickled_radish` in `known_toppings`
- **THEN** the score for 晴光小吃 SHALL be 0.5 + 0.3 = 0.8, which meets the threshold, and the system SHALL override the CLIP result and return 晴光小吃 with `confidence_level: "high"`

#### Scenario: Competing stores with same distinctive bowl colour — no override

- **WHEN** two stores (e.g., 晴光小吃 and 司機俱樂部) both have `bowl.color: "bright_green"` with `distinctive: true` and no matching topping is detected
- **THEN** both stores SHALL score 0.5, neither reaches the 0.75 threshold, the override SHALL be suppressed, and the CLIP KNN result SHALL be returned unchanged

#### Scenario: Cilantro triggers override for 阿興

- **WHEN** the classifier detects `cilantro` in toppings and 阿興魯肉飯 has `cilantro` in `known_toppings`
- **THEN** the system SHALL override the CLIP result and return 阿興魯肉飯 with `confidence_level: "high"`

#### Scenario: Override suppressed when multiple stores qualify

- **WHEN** detected features match more than one store above the override threshold
- **THEN** the system SHALL suppress the override and return the CLIP KNN result unchanged

#### Scenario: No distinctive features falls back to CLIP

- **WHEN** no detected feature scores any store at or above the override threshold
- **THEN** the system SHALL return the CLIP KNN result unchanged


<!-- @trace
source: tune-haiku-override-and-add-stores
updated: 2026-03-29
code:
  - src/visual_recognition/classifier.py
  - data/store_notes.json
  - eval_hybrid.py
-->

---
### Requirement: Sauce consistency tiebreak

When a tie is detected and the top two candidates have different `sauce_consistency` labels in `store_notes.json`, the system SHALL optionally apply a DINOv2-based sauce consistency tiebreak as a third-layer signal.

The tiebreak is gated by the `DINO_TIEBREAK_ENABLED` environment variable (default: `false`). When disabled, tie detection and ranking proceed unchanged.

When enabled, the system SHALL:
1. Check whether the top two tied candidates have different `sauce_consistency` labels (`稠` or `水`). If labels are the same or either is missing, skip tiebreak.
2. Embed the query image using DINOv2 (dinov2_vitb14) with center-crop preprocessing, and predict the sauce consistency class via class-normalized KNN voting against `index_sauce_crop.npz`.
3. Apply asymmetric confidence thresholds for the two possible actions:
   - **Confirm** (prediction matches first candidate, no position change): threshold ≥ 0.65
   - **Swap** (prediction matches second candidate, promote to first): threshold ≥ 0.80
4. If neither threshold is met, retain original ordering and `is_tie: true`.
5. When the tiebreak resolves the tie (confirm or swap), set `is_tie: false`.

The DINOv2 model SHALL be loaded lazily on first use with a process-level cache. Prediction failures SHALL be handled gracefully by returning `None` and skipping the tiebreak.

#### Scenario: Tiebreak confirms first candidate

- **WHEN** top two tied candidates are store A (稠) and store B (水), DINOv2 predicts 稠 with confidence ≥ 0.65
- **THEN** store A SHALL remain first, `is_tie` SHALL be set to `false`

#### Scenario: Tiebreak swaps second candidate to first

- **WHEN** top two tied candidates are store A (水) and store B (稠), DINOv2 predicts 稠 with confidence ≥ 0.80
- **THEN** store B SHALL be promoted to first, `is_tie` SHALL be set to `false`

#### Scenario: Swap blocked by insufficient confidence

- **WHEN** DINOv2 predicts the second candidate's class but confidence < 0.80
- **THEN** ordering SHALL remain unchanged and `is_tie` SHALL remain `true`

#### Scenario: Tiebreak skipped when labels are identical

- **WHEN** both top candidates have the same `sauce_consistency` label
- **THEN** tiebreak SHALL be skipped and original ordering retained

#### Scenario: Tiebreak skipped when disabled

- **WHEN** `DINO_TIEBREAK_ENABLED` is `false` (default)
- **THEN** DINOv2 SHALL NOT be loaded or invoked

<!-- @trace
source: sauce-consistency-tiebreak
updated: 2026-04-12
code:
  - src/store_matching/matcher.py
  - src/sauce_consistency/predictor.py
  - src/sauce_consistency/__init__.py
  - data/store_notes.json
  - index_sauce_crop.npz
-->

---
### Requirement: Result conforms to store-matching-schema

The system SHALL return results conforming to the store-matching-schema defined in data-schema, including store_name, similarity, and photo_count.

#### Scenario: Result includes photo_count

- **WHEN** a match result is returned
- **THEN** each entry SHALL include the photo_count from the index for that store
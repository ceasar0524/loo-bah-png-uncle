# end-to-end-pipeline Specification

## Purpose

TBD - created by archiving change 'recognizer-cli'. Update Purpose after archive.

## Requirements

### Requirement: End-to-end pipeline from image to uncle-persona response

The system SHALL provide a pipeline function that accepts an image path and executes the full recognition flow in order:

1. image-preprocessing
2. visual-recognition（Haiku 分類 + 碗特徵提取；CLIP 肉型醬汁特徵辨識）
3. store-matching with Haiku override（僅在 is_lu_rou_fan 為 true 且提供 index_path 時執行）
4. uncle-persona response generation

The function SHALL accept the following parameters:
- `image_source`: 圖片路徑
- `index_path`: 向量索引路徑（.npz）；None 則跳過 store-matching
- `threshold`: 魯肉飯判定門檻（預設 0.6）
- `store_notes_path`: store_notes.json 路徑；None 則使用預設路徑（data/store_notes.json）

When store-matching is performed, the pipeline SHALL load store_notes.json and extract bowl/topping features from the VisualResult, passing them to match_store as `haiku_features` and `store_notes` to enable the Haiku feature override mechanism.

The function SHALL return the uncle-persona response string.

#### Scenario: Full pipeline runs successfully

- **WHEN** a valid image path of a lu-rou-fan photo is provided
- **THEN** the system SHALL return the uncle-persona response string after completing all pipeline stages

#### Scenario: Non-lu-rou-fan image skips store-matching

- **WHEN** visual-recognition returns is_lu_rou_fan: false
- **THEN** the system SHALL skip store-matching and pass the visual result directly to uncle-persona

#### Scenario: Pipeline function importable by other modules

- **WHEN** a Line Bot or web layer imports the pipeline module
- **THEN** it SHALL be able to call the pipeline function directly without invoking the CLI

#### Scenario: Missing store_notes falls back gracefully

- **WHEN** store_notes_path is provided but the file does not exist
- **THEN** the system SHALL log a warning and proceed without Haiku override (CLIP result used as-is)

---
### Requirement: CLI entry point accepts image path argument

The system SHALL provide a `recognize.py` script that accepts a single positional argument (image file path) and prints the uncle-persona response to stdout.

#### Scenario: Response printed to stdout

- **WHEN** `python recognize.py <image_path>` is executed with a valid image
- **THEN** the uncle-persona response SHALL be printed to stdout

#### Scenario: Missing file handled gracefully

- **WHEN** the provided image path does not exist
- **THEN** the system SHALL print a user-friendly error message in Traditional Chinese and exit with a non-zero code

#### Scenario: Missing API key handled gracefully

- **WHEN** the ANTHROPIC_API_KEY environment variable is not set
- **THEN** the system SHALL print a clear Traditional Chinese message instructing the user to set it and exit

---
### Requirement: Model loading progress indicated

The system SHALL print a loading indicator when the CLIP model is being loaded, so the user is aware the system is working and not frozen.

#### Scenario: Loading message shown during model init

- **WHEN** the CLIP model is loading for the first time
- **THEN** the system SHALL print a message such as "載入模型中..." to stdout before the model is ready

---
### Requirement: Training photos excluded from version control

The `photos/` directory SHALL be listed in `.gitignore` to prevent training photos from being committed to the repository. The vector index (`index.npz`) SHALL remain under version control as it is required for store matching at runtime.

#### Scenario: photos/ not tracked by git

- **WHEN** a developer runs `git status` or `git add .`
- **THEN** files under `photos/` SHALL NOT appear as tracked or staged files

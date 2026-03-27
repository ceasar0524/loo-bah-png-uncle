## ADDED Requirements

### Requirement: Detect toppings using binary CLIP classification

The system SHALL detect the presence of each topping independently using CLIP zero-shot binary classification ("a bowl of lu-rou-fan with X" vs "a bowl of lu-rou-fan without X").

The topping list SHALL be loaded from a configurable file (e.g., `toppings.yaml`), allowing new toppings to be added without modifying code. Default toppings when the file is absent: cilantro, braised_egg, bamboo_shoots, tofu, pickled_mustard, soft_boiled_egg, hard_boiled_egg, oyster, pickled_radish, cucumber, pork_floss, shredded_chicken, braised_cabbage, green_onion, fried_shallots.

#### Scenario: Cilantro detected

- **WHEN** the image contains visible cilantro on the lu-rou-fan
- **THEN** the system SHALL include "cilantro" in the toppings list

#### Scenario: No toppings detected

- **WHEN** the image shows plain lu-rou-fan with no identifiable toppings
- **THEN** the system SHALL return an empty toppings list

#### Scenario: Multiple toppings detected simultaneously

- **WHEN** the image contains both braised egg and bamboo shoots
- **THEN** both SHALL be included in the toppings list

#### Scenario: Topping list loaded from config file

- **WHEN** a toppings config file exists at the configured path
- **THEN** the system SHALL use the toppings defined in that file instead of the defaults

#### Scenario: Missing config file falls back to defaults

- **WHEN** the toppings config file does not exist
- **THEN** the system SHALL use the built-in default topping list and SHALL NOT crash

### Requirement: Classify pork part from configurable categories

The system SHALL classify the pork part using a category list loaded from a configurable file (`pork_parts.yaml`). Each category SHALL define a label and a descriptive CLIP text prompt. Default categories when the file is absent: belly (五花), fatty (肥肉多), lean (瘦肉多), skin_heavy (皮多).

#### Scenario: Pork part classified by highest CLIP similarity

- **WHEN** pork part classification is performed
- **THEN** the system SHALL return the label of the category whose prompt has the highest cosine similarity to the image

#### Scenario: Pork part categories loaded from config file

- **WHEN** a pork_parts config file exists at the configured path
- **THEN** the system SHALL use the categories defined in that file instead of the defaults

#### Scenario: Missing pork part config falls back to defaults

- **WHEN** the pork_parts config file does not exist
- **THEN** the system SHALL use the built-in default categories and SHALL NOT crash

### Requirement: Classify fat-to-lean ratio from configurable categories

The system SHALL classify the fat-to-lean ratio of the pork using a category list loaded from a configurable file (`fat_ratio.yaml`). Default categories when the file is absent: fat_heavy (7:3), balanced (5:5), lean_heavy (3:7).

#### Scenario: Fat ratio classified by highest CLIP similarity

- **WHEN** fat ratio classification is performed
- **THEN** the system SHALL return the label of the category whose prompt has the highest cosine similarity to the image

#### Scenario: Fat ratio categories loaded from config file

- **WHEN** a fat_ratio config file exists at the configured path
- **THEN** the system SHALL use the categories defined in that file instead of the defaults

#### Scenario: Missing fat ratio config falls back to defaults

- **WHEN** the fat_ratio config file does not exist
- **THEN** the system SHALL use the built-in default categories and SHALL NOT crash

### Requirement: Detect pork skin presence from configurable categories

The system SHALL classify whether the pork includes skin using a category list loaded from a configurable file (`skin.yaml`). Default categories when the file is absent: with_skin, no_skin.

#### Scenario: Pork with skin detected

- **WHEN** the image shows braised pork with visible skin and gelatinous texture
- **THEN** the system SHALL return skin: "with_skin"

#### Scenario: Skin presence categories loaded from config file

- **WHEN** a skin config file exists at the configured path
- **THEN** the system SHALL use the categories defined in that file instead of the defaults

#### Scenario: Missing skin config falls back to defaults

- **WHEN** the skin config file does not exist
- **THEN** the system SHALL use the built-in default categories and SHALL NOT crash

### Requirement: Classify sauce color from configurable categories

The system SHALL classify the braising sauce color using a category list loaded from a configurable file (e.g., `sauce_colors.yaml`). Each category SHALL define a label and a descriptive CLIP text prompt. Default categories when the file is absent: light (淺褐), medium (中褐), dark (深褐).

#### Scenario: Sauce color classified by highest CLIP similarity

- **WHEN** sauce color classification is performed
- **THEN** the system SHALL return the label of the category whose prompt has the highest cosine similarity to the image

#### Scenario: Sauce color categories loaded from config file

- **WHEN** a sauce_colors config file exists at the configured path
- **THEN** the system SHALL use the categories defined in that file instead of the defaults

#### Scenario: Missing sauce color config falls back to defaults

- **WHEN** the sauce_colors config file does not exist
- **THEN** the system SHALL use the built-in default categories and SHALL NOT crash

### Requirement: Classify rice quality from configurable categories

The system SHALL classify the rice texture using a category list loaded from a configurable file (e.g., `rice_qualities.yaml`). Each category SHALL define a label and a descriptive CLIP text prompt. Default categories when the file is absent: fluffy (鬆散), soft (軟), mushy (糊爛).

#### Scenario: Rice quality classified by highest CLIP similarity

- **WHEN** rice quality classification is performed
- **THEN** the system SHALL return the label of the category whose prompt has the highest cosine similarity to the image

#### Scenario: Rice quality categories loaded from config file

- **WHEN** a rice_qualities config file exists at the configured path
- **THEN** the system SHALL use the categories defined in that file instead of the defaults

#### Scenario: Missing rice quality config falls back to defaults

- **WHEN** the rice_qualities config file does not exist
- **THEN** the system SHALL use the built-in default categories and SHALL NOT crash

### Requirement: Feature recognition only runs on confirmed lu-rou-fan

The system SHALL only perform feature recognition when is_lu_rou_fan is true. If the classifier returns false, all feature fields SHALL be skipped and set to None or empty.

#### Scenario: Feature recognition skipped for non-lu-rou-fan

- **WHEN** the lu-rou-fan classifier returns is_lu_rou_fan: false
- **THEN** the system SHALL NOT invoke feature recognition and SHALL return None for all feature fields

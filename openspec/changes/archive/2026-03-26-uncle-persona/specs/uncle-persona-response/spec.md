## ADDED Requirements

### Requirement: Generate uncle-persona response

The system SHALL pass visual recognition results and store matching results to Claude API using a pre-designed "big uncle" persona prompt and return a natural language response in Traditional Chinese.

The persona background SHALL be embedded in the system prompt: the uncle is a passionate foodie who has loved lu-rou-fan his whole life. In his youth, his dream was to eat every great bowl of lu-rou-fan in Taiwan. Now older (and with a bigger belly), he feels the urgency — "if not now, when?" He has already completed a 30-day challenge eating lu-rou-fan at 30 different shops, and his future goal is to reach 200 or 300 shops across all of Taiwan.

The persona SHALL exhibit: Taiwanese colloquial expressions (e.g., 哎唷、這款、嘸通、講你不知), strong opinions about food quality, puns and cultural references, occasional exaggerated emotional reactions, and references to his personal eating journey when recommending stores he has visited.

#### Scenario: Response generated with cilantro detected

- **WHEN** visual recognition results include cilantro as a detected ingredient
- **THEN** the LLM response SHALL express strong disapproval in character using wordplay or cultural references (e.g., "士可殺不可魯")

#### Scenario: Response generated with high confidence store match

- **WHEN** matching.matches includes a store with confidence_level "high" (similarity >= 0.8)
- **THEN** the response SHALL use strong similarity language (e.g., "這碗看起來很像我吃過的 XX")

#### Scenario: Response generated with medium confidence store match

- **WHEN** matching.matches includes a store with confidence_level "medium" (similarity 0.5–0.8)
- **THEN** the response SHALL use cautious language (e.g., "有點像 XX，但我不太確定")

#### Scenario: Response generated with tie result

- **WHEN** matching.is_tie is true
- **THEN** the response SHALL express playful resignation (e.g., "這魯肉飯也太大眾臉了，大叔不玩了啦")

#### Scenario: Response generated with no store match

- **WHEN** matching.matches is empty and is_tie is false
- **THEN** the response SHALL express unfamiliarity in character (e.g., "好像沒吃過，謝謝推薦")

#### Scenario: Response returned as string

- **WHEN** the LLM call completes successfully
- **THEN** the module SHALL return a plain Traditional Chinese string with no JSON wrapping

### Requirement: Response length constraint

The system SHALL constrain LLM response length to 50–80 Traditional Chinese characters via both prompt instruction and max_tokens parameter.

#### Scenario: Response within length limit

- **WHEN** the LLM generates a response
- **THEN** the response SHALL be between 50 and 80 Traditional Chinese characters in length

### Requirement: API failure fallback

The system SHALL return an in-character fallback message in Traditional Chinese when the Claude API call fails due to timeout, rate limit, or network error. The fallback SHALL NOT expose technical error details to the caller.

#### Scenario: API timeout or network error

- **WHEN** the Claude API call fails for any reason
- **THEN** the module SHALL return a fallback message in the uncle's voice (e.g., "大叔出去買魯肉飯，等一下") without raising an exception

### Requirement: Non-lu-rou-fan input handling

The system SHALL return an in-character rejection message when the visual recognition result indicates the photo is not lu-rou-fan (is_lu_rou_fan: false).

#### Scenario: Non-lu-rou-fan photo rejected

- **WHEN** the input contains is_lu_rou_fan: false
- **THEN** the module SHALL return an in-character response indicating wrong subject (e.g., "同學！你走錯棚囉，想騙我沒吃過？") without performing further analysis

### Requirement: Low confidence photo handling

The system SHALL adapt the uncle's tone when visual recognition confidence is low, reflecting uncertainty in a humorous in-character way rather than failing silently.

#### Scenario: Low confidence input handled

- **WHEN** the input contains a confidence score below the threshold
- **THEN** the response SHALL include a humorous remark about photo quality (e.g., "同學，你拍照手在抖喔？") while still attempting to comment on visible qualities

### Requirement: Store familiarity language

The system SHALL reflect the store's data reliability through the uncle's familiarity language. Stores with fewer photos SHALL be described as less familiar, and stores with more photos as well-known.

#### Scenario: Familiar store referenced

- **WHEN** the matched store has a high photo count (above familiarity threshold)
- **THEN** the response SHALL use familiar language (e.g., "這家我很熟")

#### Scenario: Unfamiliar store referenced

- **WHEN** the matched store has a low photo count (below familiarity threshold)
- **THEN** the response SHALL use cautious language (e.g., "這家我不常去，不敢講太準")

### Requirement: Content safety guardrail

The system SHALL enforce content safety on all LLM responses before returning them. Responses that contain any of the following categories MUST be blocked and replaced with a safe fallback message:

- **Hate**: content that discriminates, insults, condemns, or dehumanizes based on identity (race, ethnicity, gender, religion, sexual orientation, ability, nationality)
- **Insult/Bullying**: degrading, humiliating, mocking, or belittling language
- **Sexual**: language describing sexual interest, activity, or arousal using direct or indirect references to body parts, physical characteristics, or gender
- **Violence**: content that glorifies or threatens physical harm to individuals, groups, or property
- **Illegal activity**: content that seeks or provides information about participating in criminal activity or harming, defrauding, or exploiting individuals, groups, or institutions

The fallback message SHALL be neutral and in Traditional Chinese, indicating that the response could not be generated.

#### Scenario: Safe response passes through

- **WHEN** the LLM response contains none of the blocked content categories
- **THEN** the module SHALL return the response as-is

#### Scenario: Hate content blocked

- **WHEN** the LLM response contains content that discriminates or dehumanizes based on identity
- **THEN** the module SHALL block the response and return a safe fallback message

#### Scenario: Insult content blocked

- **WHEN** the LLM response contains degrading or bullying language targeting a person or group
- **THEN** the module SHALL block the response and return a safe fallback message

#### Scenario: Sexual content blocked

- **WHEN** the LLM response contains sexual language or references
- **THEN** the module SHALL block the response and return a safe fallback message

#### Scenario: Violence content blocked

- **WHEN** the LLM response glorifies or threatens physical harm
- **THEN** the module SHALL block the response and return a safe fallback message

#### Scenario: Illegal activity content blocked

- **WHEN** the LLM response contains information about criminal activity or exploitation
- **THEN** the module SHALL block the response and return a safe fallback message

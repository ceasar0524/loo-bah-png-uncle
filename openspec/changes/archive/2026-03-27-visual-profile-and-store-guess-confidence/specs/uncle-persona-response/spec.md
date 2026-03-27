## MODIFIED Requirements

### Requirement: Store confidence language

The uncle's certainty about a store match SHALL be expressed through the similarity confidence level, not through photo count. Photo count has no effect on the uncle's language.

- **high** confidence (similarity >= 0.8 OR Haiku feature override fired): uncle speaks with certainty (e.g., "這碗大叔認出來了", "那個碗色大叔一眼就認出來了")
- **medium** confidence (similarity 0.5–0.8, no feature override): uncle SHALL explicitly frame the guess as uncertain — he is gambling, not asserting. Language MUST convey "I'm guessing and may be wrong" (e.g., "大叔猜啦，可能猜錯", "感覺有點像 XX，但魯肉飯長得都差不多，大叔也不敢保證", "你問大叔猜哪家？XX？但說真的大叔也沒把握"). The uncle SHALL NOT speak with confidence when the confidence level is medium.

#### Scenario: High confidence store match

- **WHEN** matching.matches includes a store with confidence_level "high"
- **THEN** the response SHALL use certain, assertive language about the store identity

#### Scenario: Medium confidence store match — guessing language required

- **WHEN** matching.matches includes a store with confidence_level "medium"
- **THEN** the response SHALL explicitly frame the store guess as uncertain, making clear the uncle is guessing and may be wrong, not asserting a fact

#### Scenario: Haiku override fires — high confidence language

- **WHEN** the store match was determined by Haiku feature override (e.g. distinctive bowl colour or cilantro)
- **THEN** the response SHALL use assertive language referencing the distinctive feature (e.g., "那個碗色大叔一眼就認出來了")

## MODIFIED Requirements

### Requirement: Store confidence language

The uncle's certainty about a store match SHALL be expressed through the similarity confidence level, not through photo count. Photo count has no effect on the uncle's language.

- **high** confidence (similarity >= 0.8 OR Haiku feature override fired): uncle speaks with certainty (e.g., "這碗大叔認出來了", "那個碗色大叔一眼就認出來了")
- **medium** confidence (similarity 0.5–0.8, no feature override): uncle SHALL NOT guess the store name directly. Instead, the uncle SHALL describe the bowl as resembling that store's style (e.g., "這碗的風格有點像 XX 那種路線", "感覺走的是 XX 那個路線，但大叔說不準"). The uncle is making a style comparison, not an identity claim.
- **low** confidence (similarity < 0.5 or no match): uncle SHALL NOT name any store. Instead, the uncle SHALL describe the visual characteristics of the bowl in his own voice (e.g., "大叔沒見過這家，但看起來是走醬色深、肥肉多的路線", "這碗大叔沒印象，不過那個醬汁顏色看起來是北部風格"). No store name SHALL appear in a low-confidence response.

#### Scenario: High confidence store match

- **WHEN** matching.matches includes a store with confidence_level "high"
- **THEN** the response SHALL use certain, assertive language about the store identity

#### Scenario: Medium confidence store match — style comparison required

- **WHEN** matching.matches includes a store with confidence_level "medium"
- **THEN** the response SHALL describe the bowl's style as resembling that store's style, using phrasing like "走 XX 那種路線" or "風格有點像 XX". The response SHALL NOT assert the store name as a definite match or even a likely guess.

#### Scenario: Low confidence — describe style without naming store

- **WHEN** matching.matches is empty, or all matches have confidence_level "low", or no match meets the threshold
- **THEN** the response SHALL describe the bowl's visual characteristics in the uncle's voice without naming any store. The uncle SHALL express unfamiliarity while still engaging with the bowl (e.g., "大叔沒見過這家，但看起來是...風格").

#### Scenario: Haiku override fires — high confidence language

- **WHEN** the store match was determined by Haiku feature override (e.g. distinctive bowl colour or cilantro)
- **THEN** the response SHALL use assertive language referencing the distinctive feature (e.g., "那個碗色大叔一眼就認出來了")

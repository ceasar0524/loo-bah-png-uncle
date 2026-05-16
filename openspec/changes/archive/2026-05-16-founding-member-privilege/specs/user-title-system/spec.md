## ADDED Requirements

### Requirement: Founding member marking during Lv.1 upgrade

When a user first upgrades to Lv.1 (「肉汁騎士」), the system SHALL synchronously call `_mark_founding_member` before dispatching the background Firestore update thread, so the member number is available for message assembly.

#### Scenario: Founding member Flex appended to upgrade reply

- **WHEN** a non-admin user first reaches 「肉汁騎士」
- **AND** `_mark_founding_member` returns (True, N)
- **THEN** the system SHALL append `_build_founding_member_flex(N)` to the upgrade reply messages

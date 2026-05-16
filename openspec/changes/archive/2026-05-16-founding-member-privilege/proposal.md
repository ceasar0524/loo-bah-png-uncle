## Why

早期加入的用戶是產品成長的核心貢獻者，應給予特別回饋。前 25 位（非管理者）升到 Lv.1 的用戶，自動取得「封測成員」身份，直接解鎖 Lv.2～3 技能，並在升級時收到專屬畫面。

## What Changes

- 新增 `founding_member` 欄位於 Firestore `user_footprint` 文件
- 新增 `title_counter/founding_member` 計數器，追蹤目前封測成員人數（上限 25）
- 首次升到 Lv.1（肉汁騎士）且非管理者時，若 counter < 25，自動標記 `founding_member: true`
- `_check_skill_unlocked` 加入 `founding_member` 判斷：`founding_member=True` 且 required_level ≤ 3 直接通過
- 升級畫面新增封測成員專屬 Flex Message，顯示「你是第 N 位封測成員」及 Lv.2～3 技能解鎖說明
- Lv.4（號令）不受影響，仍需達到 魯肉飯大神 條件

## Capabilities

### New Capabilities

- `founding-member-privilege`: 封測成員特權系統，前 25 位升到 Lv.1 的非管理者用戶自動解鎖 Lv.2~3 技能

### Modified Capabilities

- `user-title-system`: 升級流程新增封測成員標記與專屬 Flex Message 顯示邏輯

## Impact

- Affected specs: `founding-member-privilege`（新增）、`user-title-system`（修改）
- Affected code: `app.py`（`_mark_founding_member`、`_build_founding_member_flex`、`_check_skill_unlocked`、`_get_user_title_and_count`、`_handle_checkin`）

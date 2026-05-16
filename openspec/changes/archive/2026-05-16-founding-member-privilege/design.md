## Context

系統目前有稱號升級機制（無職轉生者 → 肉汁騎士 → 滷鍋守護者 → 魯肉飯勇者 → 魯肉飯大神），技能解鎖依稱號等級判斷。封測階段（用戶數 220 人）需給予早期忠實用戶特別回饋，讓他們即使還在低等級也能體驗較高階技能。

## Goals / Non-Goals

**Goals:**
- 前 25 位升到 Lv.1 的非管理者用戶自動取得封測成員特權
- 封測成員可直接使用 Lv.1～3 技能（肉盾、絕對滷域、魯拉）
- 升級時顯示專屬 Flex Message，告知用戶其封測成員身份與第幾位

**Non-Goals:**
- Lv.4 技能（號令）不在封測特權範圍內
- 管理者不計入封測成員配額
- 不支援手動指定封測成員（由系統自動依升級順序決定）

## Decisions

### Firestore founding_member 標記方式

使用 `user_footprint/{user_id}` 文件的 `founding_member: true` 欄位標記封測成員身份。計數器存於 `title_counter/founding_member` 的 `count` 欄位，使用 Firestore transaction 確保計數準確、不超額。

**替代方案：** 維護一個獨立的 `founding_members` collection。→ 不採用，因需額外 query，`user_footprint` 文件本身已是單一來源，合併更省讀取次數。

### 同步執行 founding_member 標記

`_mark_founding_member` 在打卡升級流程中**同步執行**（非在背景 thread），以便取得回傳的成員編號用於組裝 Flex Message。Firestore title 更新仍在 thread 中執行。

**替代方案：** 全部在 thread 中執行。→ 不採用，無法在同一個 reply 中加入封測成員畫面。

### _check_skill_unlocked 擴充 founding_member 參數

在 `_check_skill_unlocked(user_title, required_title, founding_member=False)` 加入第三個參數。`founding_member=True` 且 `required_level <= 3` 時直接回傳 True，Lv.4 不受影響。

## Risks / Trade-offs

- **計數超額風險** → 使用 Firestore transaction，保證 counter 原子性更新，不會超過 25
- **封測成員編號已標記但升級 Flex 失敗** → 編號仍保留，用戶下次查詢稱號時仍有 founding_member 權限，僅畫面未補發
- **舊有 Lv.1+ 用戶需手動補標** → 透過 `mark_founding_members.py` 一次性 script 處理，並以 `push_founding_member.py` 補發畫面

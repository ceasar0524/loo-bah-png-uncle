## 1. Firestore founding_member 標記方式

- [x] 1.1 新增 `_FOUNDING_MEMBER_LIMIT = 25` 常數
- [x] 1.2 新增 `_mark_founding_member(user_id)` 函式，使用 Firestore transaction 原子性更新 `title_counter/founding_member` 計數器，回傳 `(True, N)` 或 `(False, 0)`（founding member auto-marking on Lv.1 upgrade）

## 2. 技能權限擴充

- [x] 2.1 擴充 `_get_user_title_and_count` 回傳 `tuple[str, int, bool]`，同時讀取 `founding_member` 欄位
- [x] 2.2 擴充 `_check_skill_unlocked 擴充 founding_member 參數`：`founding_member=True` 且 `required_level <= 3` 時直接回傳 True（founding member skill access）
- [x] 2.3 更新肉盾、魯拉、號令三個觸發點，傳入 `founding_member` 參數（founding member cannot use Lv.4 skill）

## 3. 升級畫面封測成員 Flex

- [x] 3.1 新增 `_build_founding_member_flex(member_number)` 函式，顯示「🎖️ 封測成員特權」、第 N 位、Lv.2～3 技能解鎖說明（founding member upgrade Flex Message）
- [x] 3.2 修改 `_handle_checkin` 升級流程：同步執行 founding_member 標記，首次升到 Lv.1 時呼叫 `_mark_founding_member`，成功時將封測成員 Flex 加入回覆（founding member marking during Lv.1 upgrade）

## 4. 既有用戶補標

- [x] 4.1 執行 `mark_founding_members.py` 手動標記已升到 Lv.1+ 的早期用戶（Firestore founding_member 標記方式）
- [x] 4.2 執行 `push_founding_member.py` 補發封測成員特別畫面給已升級用戶

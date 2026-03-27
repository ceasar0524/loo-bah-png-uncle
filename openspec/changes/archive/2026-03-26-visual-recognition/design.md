## Context

魯肉飯辨識器的視覺分析模組，負責從照片中萃取語意資訊供 uncle-persona 使用。系統使用 CLIP（openai/clip-vit-base-patch32）做 zero-shot 分類，與 store-embedding-db 共用同一模型實例以節省記憶體。輸出遵循 data-schema 定義的 visual-recognition-schema。

## Goals / Non-Goals

**Goals:**

- 判斷照片是否為魯肉飯（is_lu_rou_fan + confidence）
- 辨識常見配料：香菜、滷蛋、筍乾、豆腐、酸菜
- 辨識肉質切法：絞肉（minced）、手切（hand_cut）、厚片（thick_slice）
- 辨識醬汁顏色：淺褐（light）、中褐（medium）、深褐（dark）
- 辨識米飯品質：鬆散（fluffy）、軟（soft）、糊爛（mushy）

**Non-Goals:**

- 不做卡路里計算
- 不做精確的食材重量估算
- 不訓練自訂分類器（全程 zero-shot）
- 不處理影片或連續幀

## Decisions

### 使用 CLIP zero-shot 做視覺辨識，不訓練分類器

**選擇**：CLIP zero-shot（文字提示 vs 圖片相似度）
**放棄**：訓練自訂 CNN 分類器、ResNet fine-tuning

**原因**：
- 400-500 張照片不足以訓練可靠的多類別分類器
- CLIP 已對大量食物圖片預訓練，zero-shot 在常見食物上效果良好
- 新增辨識類別只需修改文字提示，不需重新訓練
- 與 store-embedding-db 共用同一模型，不增加額外記憶體與載入時間

### 每個特徵獨立做 zero-shot 分類

**選擇**：每個特徵（配料、切法、醬色、米飯）各自用一組候選文字提示做 softmax 選擇
**放棄**：單一大型提示涵蓋所有特徵

**原因**：
- 獨立分類讓每個特徵的候選詞彙更精準
- 失敗時可單獨 debug 某個特徵
- 未來新增特徵不影響其他分類器

### 配料辨識使用二元判斷而非多選一

**選擇**：每種配料各自判斷「有/無」（binary presence detection）
**放棄**：多標籤 softmax

**原因**：
- 一碗魯肉飯可以同時有香菜 + 滷蛋，不是互斥選項
- 對每種配料問「這碗飯有沒有 X」比「這碗飯最像哪種配料組合」更自然
- 門檻值可個別調整（香菜容易誤判，門檻設高一點）

### is_lu_rou_fan 使用較高門檻（0.6）

**選擇**：CLIP 相似度 >= 0.6 才判定為魯肉飯
**放棄**：預設 0.5

**原因**：
- uncle-persona 對非魯肉飯照片有特定回應（「你走錯棚囉」）
- 寧可低召回（漏掉邊緣案例）也不要高誤判（把其他食物說成魯肉飯）
- 門檻設計為可配置，日後可調整

## Risks / Trade-offs

- **CLIP zero-shot 對台灣食物的英文描述可能偏弱** → 同時準備中英文提示詞，取較高信心值
- **光線不足或角度不佳的照片辨識率下降** → 前處理（亮度正規化）已在 image-preprocessing 模組處理；本模組假設輸入已預處理
- **配料辨識對細小配料（如蔥花）可能偏弱** → 初版只辨識視覺特徵明顯的配料（香菜、滷蛋、筍乾），蔥花等小配料不列入

## Context

目前大叔在 medium 信心時會猜店名但加免責說明（「大叔猜啦，可能猜錯」），在 low 信心或無比對時說「好像沒吃過」。這兩種情況都隱含「我在猜這是哪家」的語意，即使信心不足也在做身份推論。

應用定位是提供有趣回應，而非精密辨識儀器。大叔遇到沒把握的碗，改說「這碗走 XX 那種路線」比硬猜店名更自然，也更符合真實美食達人的行為。

## Goals / Non-Goals

**Goals:**

- medium 信心改為描述風格相似（「走 XX 那種路線」），不再猜店名
- low 信心 / 無比對改為描述碗的視覺風格特徵，不提店名
- high 信心行為不變

**Non-Goals:**

- 變更 confidence_level 的計算邏輯或門檻
- 修改 Haiku override 機制
- 修改平手（tie）的處理路徑

## Decisions

**只改 system prompt 中的信心等級語氣規則。** 信心等級由 matcher 決定，persona 只負責翻譯成語氣。調整 persona.py 的 system prompt 中 medium/low 對應的語氣指示即可，不需動 matcher 或 pipeline。

medium 範例語：「這碗的風格有點像 XX 那種路線，但大叔說不準是不是這家」
low 範例語：「大叔沒見過這家，不過看起來是走醬色深、肥肉丁偏多的路線」

## Risks / Trade-offs

- medium 改成風格比較後，使用者可能覺得大叔「說了跟沒說一樣」。但這比硬猜出錯更好——誠實的不確定比錯誤的自信更有趣。
- low 信心時純描述視覺特徵，需要 Haiku 視覺特徵（bowl_color、bowl_shape 等）有意義的輸出才能描述。若視覺特徵均為 None，大叔退回說「大叔沒見過這家」即可。

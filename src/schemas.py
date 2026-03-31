"""
共用資料結構定義。
所有模組之間傳遞的資料都使用這裡定義的 TypedDict。
"""
from typing import Optional
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Visual Recognition Schema
# ---------------------------------------------------------------------------

class VisualResult(TypedDict):
    """
    visual-recognition 模組的輸出格式。

    is_lu_rou_fan: 是否為魯肉飯
    confidence:    辨識信心值 0.0–1.0
    toppings:      偵測到的配料列表（e.g. ["cilantro", "braised_egg"]）
    bowl_color:    碗色（e.g. "bright_green" | "white" | "other"）；非魯肉飯時為 None
    bowl_shape:    碗形（e.g. "round_bowl" | "wide_flat_plate" | "other"）；非魯肉飯時為 None
    bowl_texture:  碗質感（e.g. "matte_ceramic" | "glossy_ceramic" | "other"）；非魯肉飯時為 None
    pork_part:     肉的部位（e.g. "belly" | "fatty" | "lean" | "skin_heavy"）
    fat_ratio:     肥瘦比例（e.g. "fat_heavy" | "balanced" | "lean_heavy"）
    skin:          是否有皮（"with_skin" | "no_skin"）
    sauce_color:   醬汁顏色（e.g. "light" | "medium" | "dark" | "black_gold"）
    rice_quality:  米飯品質（e.g. "fluffy" | "soft" | "mushy"）

    當 is_lu_rou_fan 為 False 時，除 confidence 外所有欄位為 None 或空列表。
    """
    is_lu_rou_fan: bool
    food_type: Optional[str]  # "lu_rou_fan" | "kong_rou_fan" | "other"
    confidence: float
    toppings: list
    bowl_color: Optional[str]
    bowl_shape: Optional[str]
    bowl_texture: Optional[str]
    pork_part: Optional[str]
    fat_ratio: Optional[str]
    skin: Optional[str]
    sauce_color: Optional[str]
    rice_quality: Optional[str]


# ---------------------------------------------------------------------------
# Store Matching Schema
# ---------------------------------------------------------------------------

class StoreMatch(TypedDict):
    """單一店家比對結果。"""
    store_name: str
    similarity: float
    confidence_level: str  # "high" | "medium"
    photo_count: int


class MatchingResult(TypedDict):
    """
    store-matching 模組的輸出格式。

    is_tie:  top-K 投票平手時為 True
    matches: 符合門檻的店家清單，依相似度降序排列；平手或無符合時為空列表
    """
    is_tie: bool
    matches: list  # list[StoreMatch]


# ---------------------------------------------------------------------------
# Uncle Persona Input Schema
# ---------------------------------------------------------------------------

class UnclePersonaInput(TypedDict):
    """
    uncle-persona 模組的輸入格式，組合視覺辨識與店家比對結果。
    """
    visual: VisualResult
    matching: MatchingResult

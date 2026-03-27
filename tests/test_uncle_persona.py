"""
整合測試：uncle_persona 模組
測試各情境的回應是否符合預期語氣
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.uncle_persona import UnclePersona

persona = UnclePersona()


def test_cilantro_high_confidence():
    """5.1 有香菜 + 高信心比對"""
    visual = {
        "is_lu_rou_fan": True,
        "confidence": 0.9,
        "toppings": ["cilantro", "braised_egg"],
        "pork_part": "belly",
        "sauce_color": "dark",
        "rice_quality": "fluffy",
    }
    matching = {
        "is_tie": False,
        "matches": [{"store_name": "阿財切仔麵", "similarity": 0.85, "confidence_level": "high", "photo_count": 15}],
    }
    result = persona.generate(visual, matching)
    print(f"[香菜+高信心] ({len(result)}字)\n{result}\n")
    assert isinstance(result, str)
    assert 20 <= len(result) <= 150


def test_medium_confidence():
    """5.2 中信心比對"""
    visual = {
        "is_lu_rou_fan": True,
        "confidence": 0.75,
        "toppings": [],
        "pork_part": "hand_cut",
        "sauce_color": "medium",
        "rice_quality": "soft",
    }
    matching = {
        "is_tie": False,
        "matches": [{"store_name": "東門城魯肉飯", "similarity": 0.65, "confidence_level": "medium", "photo_count": 8}],
    }
    result = persona.generate(visual, matching)
    print(f"[中信心] ({len(result)}字)\n{result}\n")
    assert isinstance(result, str)


def test_tie():
    """5.3 平手（is_tie: true）"""
    visual = {
        "is_lu_rou_fan": True,
        "confidence": 0.82,
        "toppings": [],
        "pork_part": "minced",
        "sauce_color": "medium",
        "rice_quality": "soft",
    }
    matching = {
        "is_tie": True,
        "matches": [
            {"store_name": "阿財", "similarity": 0.72, "confidence_level": "medium", "photo_count": 12},
            {"store_name": "老王", "similarity": 0.71, "confidence_level": "medium", "photo_count": 10},
        ],
    }
    result = persona.generate(visual, matching)
    print(f"[平手] ({len(result)}字)\n{result}\n")
    assert isinstance(result, str)


def test_no_match():
    """5.4 空 matches"""
    visual = {
        "is_lu_rou_fan": True,
        "confidence": 0.78,
        "toppings": [],
        "pork_part": "minced",
        "sauce_color": "light",
        "rice_quality": "fluffy",
    }
    matching = {"is_tie": False, "matches": []}
    result = persona.generate(visual, matching)
    print(f"[無比對] ({len(result)}字)\n{result}\n")
    assert isinstance(result, str)


def test_non_lu_rou_fan():
    """非魯肉飯照片"""
    visual = {"is_lu_rou_fan": False, "confidence": 0.3}
    matching = {"is_tie": False, "matches": []}
    result = persona.generate(visual, matching)
    print(f"[走錯棚] ({len(result)}字)\n{result}\n")
    assert "走錯" in result or "不是" in result or "棚" in result


def test_missing_examples_fallback():
    """5.5 範例檔不存在時 fallback"""
    p = UnclePersona(examples_path="/nonexistent/path/examples.json")
    visual = {"is_lu_rou_fan": True, "confidence": 0.8, "toppings": [], "sauce_color": "medium"}
    matching = {"is_tie": False, "matches": []}
    result = p.generate(visual, matching)
    print(f"[fallback範例] ({len(result)}字)\n{result}\n")
    assert isinstance(result, str)


if __name__ == "__main__":
    print("=== Uncle Persona 整合測試 ===\n")
    test_cilantro_high_confidence()
    test_medium_confidence()
    test_tie()
    test_no_match()
    test_non_lu_rou_fan()
    test_missing_examples_fallback()
    print("✓ 所有測試通過")

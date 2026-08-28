"""
辨識故障（Anthropic API 失敗）不得被當成「不是魯肉飯」。
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
import anthropic
from PIL import Image

from src.visual_recognition import classifier
from src.uncle_persona.persona import UnclePersona, _NOT_LU_ROU_FAN_RESPONSES


def _fake_image():
    return Image.new("RGB", (64, 64), (200, 150, 100))


def _patch_create(raiser):
    """暫時把 classifier._client.messages.create 換成會拋錯的版本"""
    original = classifier._client.messages.create
    classifier._client.messages.create = raiser
    return original


def _restore_create(original):
    classifier._client.messages.create = original


def test_classify_api_error_marks_food_type_error():
    """API 回 400（用量上限）時，food_type 必須是 error，不是 other"""
    def boom(**kwargs):
        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        raise anthropic.APIStatusError(
            "You have reached your specified API usage limits.",
            response=httpx.Response(400, request=request),
            body=None,
        )

    original = _patch_create(boom)
    try:
        is_lrf, confidence, features = classifier.classify(_fake_image())
    finally:
        _restore_create(original)

    assert is_lrf is False
    assert features["food_type"] == "error", features
    print("[classify API 400] food_type=error ✓")


def test_classify_unexpected_error_marks_food_type_error():
    """非 APIStatusError 的例外同樣視為辨識故障"""
    def boom(**kwargs):
        raise RuntimeError("connection reset")

    original = _patch_create(boom)
    try:
        _, _, features = classifier.classify(_fake_image())
    finally:
        _restore_create(original)

    assert features["food_type"] == "error", features
    print("[classify 未預期例外] food_type=error ✓")


def test_persona_error_response_is_not_not_lu_rou_fan():
    """food_type=error 時大叔要說故障，不能說「這不是魯肉飯」"""
    persona = UnclePersona()
    visual = {"is_lu_rou_fan": False, "food_type": "error", "confidence": 0.0}
    matching = {"is_tie": False, "matches": []}
    result = persona.generate(visual, matching)

    assert isinstance(result, str) and result
    assert result not in _NOT_LU_ROU_FAN_RESPONSES, result
    print(f"[辨識故障回應] {result}")


if __name__ == "__main__":
    print("=== 辨識故障處理測試 ===\n")
    test_classify_api_error_marks_food_type_error()
    test_classify_unexpected_error_marks_food_type_error()
    test_persona_error_response_is_not_not_lu_rou_fan()
    print("\n✓ 所有測試通過")

"""
共用 CLIP 模型 singleton。
store_embedding_db 與 visual_recognition 都從這裡取得同一個模型實例，避免重複載入。
"""
import clip
import torch

_model = None
_preprocess = None
_MODEL_NAME = "ViT-B/32"


def get_model():
    """回傳 (model, preprocess)，全程只載入一次。"""
    global _model, _preprocess
    if _model is None:
        _model, _preprocess = clip.load(_MODEL_NAME, device="cpu")
        _model.eval()
    return _model, _preprocess


def encode_text(texts: list[str]) -> "torch.Tensor":
    """將文字列表編碼為 L2 正規化向量。"""
    model, _ = get_model()
    tokens = clip.tokenize(texts)
    with torch.no_grad():
        feats = model.encode_text(tokens)
        feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats


def encode_image(pil_image) -> "torch.Tensor":
    """將 PIL Image 編碼為 L2 正規化向量。"""
    model, preprocess = get_model()
    tensor = preprocess(pil_image).unsqueeze(0)
    with torch.no_grad():
        feats = model.encode_image(tensor)
        feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats

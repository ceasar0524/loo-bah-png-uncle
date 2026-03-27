#!/usr/bin/env python3
"""
魯肉飯辨識器 CLI。

用法：
    python recognize.py <照片路徑> [--index ./index.npz]
"""
import argparse
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="魯肉飯辨識器：輸入照片，大叔幫你鑑定！")
    parser.add_argument("image", help="要辨識的照片路徑")
    parser.add_argument(
        "--index",
        default="index.npz",
        help="向量索引路徑（預設：index.npz）；不存在時跳過店家比對",
    )
    args = parser.parse_args()

    # 檔案存在檢查
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"錯誤：找不到照片「{args.image}」，請確認路徑正確。")
        sys.exit(1)

    # API key 檢查
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("錯誤：請設定環境變數 ANTHROPIC_API_KEY 後再執行。")
        print("  export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    print("載入模型中...")
    sys.path.insert(0, str(Path(__file__).parent))

    try:
        from src.pipeline import run
        response = run(str(image_path), index_path=args.index)
        print(f"\n{response}")
    except ValueError as e:
        print(f"錯誤：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"執行失敗：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

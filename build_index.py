#!/usr/bin/env python3
"""
建立店家照片向量索引。

用法：
    python build_index.py --photos ./photos --output ./index.npz
"""
import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main():
    parser = argparse.ArgumentParser(description="建立魯肉飯店家向量索引")
    parser.add_argument("--photos", required=True, help="店家照片根目錄（每家店一個子目錄）")
    parser.add_argument("--output", default="index.npz", help="索引輸出路徑（預設：index.npz）")
    args = parser.parse_args()

    if not Path(args.photos).is_dir():
        print(f"錯誤：找不到照片目錄「{args.photos}」，請確認路徑正確。")
        sys.exit(1)

    print(f"載入模型中...")
    sys.path.insert(0, str(Path(__file__).parent))
    from src.store_embedding_db import build_index

    try:
        summary = build_index(args.photos, args.output)
        print(f"完成！共處理 {summary['stores']} 家店、{summary['photos']} 張照片。")
    except Exception as e:
        print(f"錯誤：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

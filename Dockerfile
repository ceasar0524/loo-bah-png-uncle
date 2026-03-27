FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 預先下載 CLIP 模型（避免 cold start 時才下載）
RUN python -c "import clip; clip.load('ViT-B/32', device='cpu')"

# 複製程式碼與資料
COPY src/ src/
COPY data/ data/
COPY index.npz .
COPY store_index.pkl.npz .
COPY app.py .

ENV PORT=8080

CMD ["python", "app.py"]

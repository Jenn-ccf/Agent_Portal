# === agent dockerfile ===

FROM python:3.11-slim


# 設定位置在專案根目錄
WORKDIR /agent
COPY requirements.txt ./
# 安裝 Python 套件
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .


# 預設執行程式腳本
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]


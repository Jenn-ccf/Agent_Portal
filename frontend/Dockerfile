# === frontend dockerfile ===

FROM python:3.11-slim

# 設定位置在專案根目錄
WORKDIR /frontend

COPY requirements.txt ./
# 安裝 Python 套件
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# 啟動 Streamlit
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]


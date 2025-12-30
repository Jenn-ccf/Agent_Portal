import os
import time
from typing import Set
from datetime import datetime

def create_time_log_entry(filename: str, description: str, start_time: float) -> str:
    """
    計算從 start_time 開始到現在的耗時，並產生標準格式的日誌記錄條目。
    """
    # 1. 計算耗時
    elapsed_time = round(time.time() - start_time, 4)
    # 2. 獲取當前時間並格式化
    end_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 3. 格式化 log 條目
    log_entry = f"{end_timestamp} | {filename} | {description} | 耗時: {elapsed_time} 秒 \n"
    return log_entry

def log_to_file(log_entry: str, log_file_path: str) -> None:
    """
    將日誌條目附加到指定的日誌檔案中。如果檔案不存在，則會自動建立。
    """
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    # 開啟舊檔案讀取並刪除舊檔案
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            old_content = f.read()
            os.remove(log_file_path)
    except Exception:
        old_content = ""
    # 開啟新檔案將舊內容與新內容寫入
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write(old_content + log_entry)

def get_processed_files(log_file_path: str) -> Set[str]:
    """
    讀取log檔案，獲取已處理過的PDF檔案列表
    """
    processed_files = set()
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if " | " in line and "狀態：成功" in line:
                        pdf_filename = line.split(" | ")[1].strip()
                        processed_files.add(pdf_filename)
        except Exception as e:
            print(f"讀取log檔案時發生錯誤: {e}")
    return processed_files
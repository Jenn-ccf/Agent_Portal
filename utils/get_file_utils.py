import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config


def get_folder_paths(folder_name: str) -> dict:
    """
    根據資料夾名稱，返回相關的路徑字典
    """
    pdf_dir = f"{config.PDF_BASE_DIRECTORY}/{folder_name}"  # PDF子資料夾路徑
    json_dir = f"{pdf_dir}/json_files"   # ocr 後的json檔案路徑
    chunked_dir = f"{pdf_dir}/chunked_json_files"    # chunking 後的json檔案路徑
    summary_dir = f"{pdf_dir}/summary_json_files"  # summary 後的json檔案路徑
    indexer_ocr_log_dir = f"{pdf_dir}/logs/ocr_logs"  # indexer ocr log檔案路徑
    indexer_chunk_log_dir = f"{pdf_dir}/logs/chunk_logs"  # indexer chunking log檔案路徑
    summary_log_dir = f"{pdf_dir}/logs/summary_logs"  # summary log檔案路徑
    indexer_embed_log_dir = f"{pdf_dir}/logs/embed_logs"  # indexer embedding log檔案路徑
    summary_embed_log_dir = f"{pdf_dir}/logs/embed_logs"  # summary embedding log檔案路徑
    chunk_collection = f"chunk_{folder_name}"  # 子資料夾對應的 chunk collection name
    summary_collection = f"summary_{folder_name}"  # 子資料夾對應的 summary collection name
    
    return {
        'pdf_directory': pdf_dir,
        'json_directory': json_dir,
        'chunked_json_directory': chunked_dir,
        'summary_json_directory': summary_dir,
        'indexer_ocr_log_directory': indexer_ocr_log_dir,
        'indexer_chunk_log_directory': indexer_chunk_log_dir,
        'summary_log_directory': summary_log_dir,
        'indexer_embed_log_directory': indexer_embed_log_dir,
        'summary_embed_log_directory': summary_embed_log_dir,
        'chunk_collection': chunk_collection,
        'summary_collection': summary_collection
    }

# === 多資料夾處理 ===
def get_pdf_folders(folder_path: str) -> list:
    """
    獲取PDF基礎目錄下的所有資料夾
    """
    if not os.path.exists(folder_path):
        print(f"PDF基礎目錄不存在: {folder_path}")
        return []
    folders = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            folders.append(item)
    return folders

def process_all_folders(processing_method: callable) -> None:
    """
    使用指定的處理方法處理PDF基礎目錄下的所有資料夾
    """
    print("開始處理所有PDF資料夾...")
    folders = get_pdf_folders(config.PDF_BASE_DIRECTORY)
    if not folders:
        print("沒有找到任何PDF資料夾")
        return
    print(f"找到 {len(folders)} 個資料夾: {folders}")
    for folder in folders:
        processing_method(folder)
    print("\n🎉 所有資料夾處理完成!")
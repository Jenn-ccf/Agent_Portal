import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config
import time
import json
from typing import Dict, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from utils.get_file_utils import get_folder_paths, process_all_folders
from utils.log_utils import get_processed_files, create_time_log_entry, log_to_file
from summary import summarize_document_from_json
from utils.embedding_utils import EmbeddingProcessor


class Summary:
    def __init__(self, embedding_processor, client):
        """
        初始化 Summary 類別：向量處理器與 Qdrant 客戶端
        """
        self.embedding_processor = embedding_processor
        try:
            self.client = client
        except Exception as e:
            print(f"向量資料庫連線發生錯誤: {str(e)}")
            self.client = None

    def process_folder(self, folder_name: str) -> Optional[Dict[str, int]]:
        """
        處理單一資料夾中的原始 JSON 檔案： Summary -> Embedding -> Upsert
        """
        # 取得資料夾相關路徑
        paths = get_folder_paths(folder_name) 
        pdf_directory = paths['pdf_directory'] # 原始 PDF 資料夾
        json_directory = paths['json_directory'] # OCR 產生的 JSON 資料夾
        summary_json_directory = paths['summary_json_directory'] # Summary 產生的 JSON 資料夾
        summary_log_directory = paths['summary_log_directory'] # Summary 日誌資料夾
        summary_embed_log_directory = paths['summary_embed_log_directory'] # Embedding+Upsert 日誌資料夾
        summary_collection = paths['summary_collection'] # Summary 向量集合名稱
        print(f"\n處理資料夾: {pdf_directory}")
        
        # 建立或連接向量集合
        if self.client is None:
            print("❌ Qdrant 連線失敗，無法執行流程。")
            return None 
        try: # 嘗試連接已存在的集合
            chunk_info = self.client.get_collection(summary_collection)
            print(f"{summary_collection} 集合連接成功，包含 {chunk_info.points_count} 條記錄")
        except Exception: # 若不存在則建立新集合
            self.client.create_collection(
                collection_name=summary_collection,
                vectors_config=VectorParams(
                    size=1024,
                    distance=Distance.COSINE
                )
            )
            print(f"已創建向量集合: {summary_collection} ")
        
        # 確保 JSON 資料夾存在，不存在即建立
        os.makedirs(json_directory, exist_ok=True)  
        # 獲取資料夾中 JSON 檔案列表
        if not os.path.exists(json_directory):
            print(f"JSON 資料夾不存在: {json_directory}")
            return
        json_files = [f for f in os.listdir(json_directory) if f.lower().endswith('.json')]
        if not json_files:
            print(f"在 {json_directory} 中沒有找到JSON檔案")
            return
        # 獲取已處理過的檔案列表
        processed_files = get_processed_files(summary_log_directory + "/summary.log")
        unprocessed_files = [f for f in json_files if f not in processed_files]
        if not unprocessed_files:
            print("所有JSON檔案都已處理完成")
            return
        # 顯示處理狀況
        print(f"找到 {len(json_files)} 個JSON檔案，其中 {len(processed_files)} 個已處理")
        print(f"開始處理剩餘的 {len(unprocessed_files)} 個檔案...")  
        
        # 初始化計數器
        summary_success_count = 0
        summary_failed_count = 0
        embed_sucess_count = 0
        embed_failed_count = 0
        # === 流程 I & II: 逐一檔案進行 Summary -> Embedding & Upsert ===
        for i, json_file in enumerate(unprocessed_files, 1):
            json_path = os.path.join(json_directory, json_file)
            summary_filename = f"summary_{json_file}"
            summary_json = os.path.join(summary_json_directory, summary_filename)
            print(f"[{i}/{len(unprocessed_files)}] 處理: {json_file}")
            
            # --- 階段 I: Summary (JSON -> Summary JSON) ---
            summary_start = time.time()
            # 呼叫 summarize_document_from_json 進行摘要抽取
            summary_success = summarize_document_from_json(input_json_path=json_path, output_json_path=summary_json)
            description = "JSON 文件內容抽取摘要"
            if not summary_success:
                summary_failed_count += 1
                log_entry = create_time_log_entry(json_file, f"{description}｜狀態：失敗", summary_start)
                log_to_file(log_entry, os.path.join(summary_log_directory, "summary.log"))
                print(f" ❌ 抽取摘要失敗 (跳過向量化): {json_file}")  
                continue # 跳過後續的 Embedding 步驟
            summary_success_count += 1
            log_entry = create_time_log_entry(json_file, f"{description}｜狀態：成功", summary_start)
            log_to_file(log_entry, os.path.join(summary_log_directory, "summary.log"))
            print(f" ✅ 成功抽取摘要: {json_file}")     

            # --- 階段 II: Embedding + Upsert (Summary JSON -> Qdrant) ---
            try:
                with open(summary_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # 呼叫 summary_embedding_upsert 進行 embedding + upsert
                embed_success = self.embedding_processor.summary_embedding_upsert(data, summary_collection, summary_embed_log_directory)
                if embed_success:
                    embed_sucess_count += 1
                    print(f"✅ 成功向量化並儲存: {data.get('filename', json_file)}")
                else:
                    embed_failed_count += 1
                    print(f" ❌ 向量化儲存失敗: {data.get('filename', json_file)}")
            except Exception as e:
                embed_failed_count += 1
                print(f" ❌ 讀取或向量化時發生錯誤: {data.get('filename', json_file)}, Error: {str(e)}")
        # === 最終統計 ===
        print("\n📊 處理結果總結:")
        print(f" 階段 I (Summary) 成功/失敗: {summary_success_count}/{summary_failed_count}")
        print(f" 階段 II (Embedding+Upsert) 成功/失敗: {embed_sucess_count}/{embed_failed_count}")
        return {
            "summary_success": summary_success_count,
            "summary_failed": summary_failed_count,
            "embed_success": embed_sucess_count,
            "embed_failed": embed_failed_count,
        }  
     
def main():
    """
    主程式入口：連接 Qdrant，載入模型，處理所有資料夾
    """
    print("🔄 連接 Qdrant 向量資料庫...")
    qdrant_client = QdrantClient(path=config.PERSIST_DIRECTORY) # 使用本地檔案存取模式
    # qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT) # 使用網路存取模式
    print("✅ Qdrant 連接成功！")
    print("🔄 BGE-M3 模型載入...")
    embedding_model = HuggingFaceEmbeddings(
                model_name=config.MODEL_NAME,
                model_kwargs=config.MODEL_KWARGS
            )
    print("✅ BGE-M3 模型載入完成！")
    embedding_processor = EmbeddingProcessor(embedding_model=embedding_model, client=qdrant_client)
    summary = Summary(embedding_processor=embedding_processor, client=qdrant_client)
    process_all_folders(summary.process_folder)

if __name__ == "__main__":
    main()
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
from chunking import process_json_to_chunks
from utils.ocr_utils import convert_pdf_to_json
from utils.embedding_utils import EmbeddingProcessor


class Indexer:
    def __init__(self, embedding_processor, client):
        """
        初始化 Indexer 類別：向量處理器＋Qdrant 客戶端
        """
        self.embedding_processor = embedding_processor
        try:
            self.client = client
        except Exception as e:
            print(f"向量資料庫連線發生錯誤: {str(e)}")
            self.client = None

    def process_folder(self, folder_name: str) -> Optional[Dict[str, int]]:
        """
        處理單一資料夾中的 PDF 檔案： OCR -> Chunking -> Embedding -> Upsert
        """
        # 取得資料夾相關路徑
        paths = get_folder_paths(folder_name)
        pdf_directory = paths['pdf_directory']  # 原始 PDF 資料夾
        json_directory = paths['json_directory'] # OCR 產生的 JSON 資料夾
        chunked_json_directory = paths['chunked_json_directory'] # Chunking 產生的 JSON 資料夾
        indexer_ocr_log_directory = paths['indexer_ocr_log_directory'] # OCR 日誌資料夾
        indexer_chunk_log_directory = paths['indexer_chunk_log_directory'] # Chunking 日誌資料夾
        indexer_embed_log_directory = paths['indexer_embed_log_directory'] # Embedding+Upsert 日誌資料夾
        chunk_collection = paths['chunk_collection'] # Chunk 向量集合名稱
        print(f"\n處理資料夾: {pdf_directory}")
        
        # 建立或連接向量集合
        if self.client is None:
            print("❌ Qdrant 連線失敗，無法執行流程。")
            return None 
        try: # 嘗試連接已存在的集合
            chunk_info = self.client.get_collection(chunk_collection)
            print(f"{chunk_collection} 集合連接成功，包含 {chunk_info.points_count} 條記錄")
        except Exception: # 若不存在則建立新集合
            self.client.create_collection(
                collection_name=chunk_collection,
                vectors_config=VectorParams(
                    size=1024,
                    distance=Distance.COSINE
                )
            )
            print(f"已創建向量集合: {chunk_collection} ")
        
        # 確保 JSON 資料夾存在，不存在即建立
        os.makedirs(json_directory, exist_ok=True)  
        # 獲取資料夾中 PDF檔案列表
        if not os.path.exists(pdf_directory):
            print(f"PDF資料夾不存在: {pdf_directory}")
            return
        pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
        if not pdf_files:
            print(f"在 {pdf_directory} 中沒有找到PDF檔案")
            return
        
        # 獲取已處理過的檔案列表
        processed_files = get_processed_files(indexer_ocr_log_directory + "/indexer_ocr.log")
        unprocessed_files = [f for f in pdf_files if f not in processed_files]
        if not unprocessed_files:
            print("所有PDF檔案都已處理完成")
            return
        # 顯示處理狀況
        print(f"找到 {len(pdf_files)} 個PDF檔案，其中 {len(processed_files)} 個已處理")
        print(f"開始處理剩餘的 {len(unprocessed_files)} 個檔案...")  
        
        # 初始化計數器
        ocr_success_count = 0
        ocr_failed_count = 0
        chunk_success_count = 0
        chunk_failed_count = 0
        embed_sucess_count = 0
        embed_failed_count = 0
        # === 流程 I & II & III: 逐一檔案進行 OCR -> Chunking -> Embedding & Upsert ===
        for i, pdf_file in enumerate(unprocessed_files, 1):
            pdf_path =  os.path.join(pdf_directory, pdf_file)
            json_filename = os.path.splitext(pdf_file)[0] + '.json'
            json_path = os.path.join(json_directory, json_filename)
            chunked_filename = f"chunked_{json_filename}"
            chunked_json = os.path.join(chunked_json_directory, chunked_filename)
            print(f"[{i}/{len(unprocessed_files)}] 處理: {pdf_file}")
            
            # --- 階段 I: OCR (PDF -> JSON) ---
            ocr_start = time.time()
            # 呼叫 convert_pdf_to_json 進行 OCR 
            ocr_success = convert_pdf_to_json(pdf_path, json_path)
            description = "PDF 轉換為 OCR JSON"
            if not ocr_success:
                ocr_failed_count += 1
                log_entry = create_time_log_entry(pdf_file, f"{description}｜狀態：失敗", ocr_start)
                log_to_file(log_entry, os.path.join(indexer_ocr_log_directory, "indexer_ocr.log"))
                print(f" ❌ OCR 失敗 (跳過chunking+向量化): {pdf_file}")  
                continue # 跳過後續的 Chunking+Embedding 步驟
            ocr_success_count += 1
            log_entry = create_time_log_entry(pdf_file, f"{description}｜狀態：成功", ocr_start)
            log_to_file(log_entry, os.path.join(indexer_ocr_log_directory, "indexer_ocr.log"))
            print(f" ✅ 成功 OCR: {json_filename}") 

            # --- 階段 II: Chunking (JSON -> chunked JSON) ---
            chunk_start = time.time()
            # 呼叫 process_json_to_chunks 進行 chunking
            chunk_success= process_json_to_chunks(input_json_path = json_path, output_json_path = chunked_json)
            description = "JSON 轉換為 Chunked JSON"
            if not chunk_success:
                chunk_failed_count += 1
                log_entry = create_time_log_entry(json_filename, f"{description}｜狀態：失敗", chunk_start)
                log_to_file(log_entry, os.path.join(indexer_chunk_log_directory, "indexer_chunk.log"))
                print(f" ❌ Chunking 失敗 (跳過向量化): {pdf_file}")  
                continue # 跳過後續的 Embedding 步驟
            chunk_success_count += 1
            log_entry = create_time_log_entry(json_filename, f"{description}｜狀態：成功", chunk_start)
            log_to_file(log_entry, os.path.join(indexer_chunk_log_directory, "indexer_chunk.log"))
            print(f" ✅ 成功 Chunking: {json_filename}") 

            # --- 階段 III: Embedding & Upsert (chunked JSON -> Qdrant) ---
            try:
                with open(chunked_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                chunks = list(data.values())
                # 呼叫 chunk_embedding_upsert 進行 embedding + upsert
                embed_success = self.embedding_processor.chunk_embedding_upsert(chunks, json_filename, chunk_collection, indexer_embed_log_directory)
                if embed_success:
                    embed_sucess_count += 1
                    print(f"✅ 成功向量化並儲存: {json_filename}")
                else:
                    embed_failed_count += 1
                    print(f" ❌ 向量化儲存失敗: {json_filename}")
            except Exception as e:
                embed_failed_count += 1
                print(f" ❌ 讀取或向量化時發生錯誤: {json_filename}, Error: {str(e)}")
        
        # === 最終統計 ===
        print("\n📊 處理結果總結:")
        print(f" 階段 I (OCR) 成功/失敗: {ocr_success_count}/{ocr_failed_count}")
        print(f" 階段 II (Chunking) 成功/失敗: {chunk_success_count}/{chunk_failed_count}")
        print(f" 階段 III (Embedding+Upsert) 成功/失敗: {embed_sucess_count}/{embed_failed_count}")
        return {
            "ocr_success": ocr_success_count,
            "ocr_failed": ocr_failed_count,
            "chunk_success": chunk_success_count,
            "chunk_failed": chunk_failed_count,
            "embed_success": embed_sucess_count,
            "embed_failed": embed_failed_count
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
    indexer = Indexer(embedding_processor=embedding_processor, client=qdrant_client)
    process_all_folders(indexer.process_folder)

if __name__ == "__main__":
    main()
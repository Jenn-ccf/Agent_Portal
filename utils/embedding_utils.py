import os
import time
import uuid
import hashlib
from typing import List, Dict
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config
from qdrant_client.models import PointStruct
from utils.log_utils import create_time_log_entry, log_to_file


class EmbeddingProcessor:
    def __init__(self, embedding_model, client):
        """
        初始化模型＋向量資料庫連線
        """
        self.embedding = embedding_model
        try:
            self.client = client
        except Exception as e:
            print(f"向量資料庫連線發生錯誤: {str(e)}")
            self.client = None
    
    def _generate_point_id(self, filename: str, page: int, index: int, search_type: str) -> str:
        """
        生成唯一的點ID
        """
        point_id_string = f"{filename}_{page}_{index}_{search_type}"
        point_id_hash = hashlib.md5(point_id_string.encode('utf-8')).hexdigest()
        return str(uuid.UUID(point_id_hash))
    
    def _embed_text(self, texts: List[str], filename: str, desc: str, log_file_path: str) -> List[List[float]]:
        """
        對文本列表進行向量化，並記錄日誌
        """
        try:
            embedding_start = time.time()
            vectors = self.embedding.embed_documents(texts)
            log_entry = create_time_log_entry(filename, f"{desc}｜狀態：成功", embedding_start)
            log_to_file(log_entry, log_file_path)
            return vectors
        except Exception as e:
            error_description = f"ERROR: {desc} failed: {str(e)}"
            error_log_entry = create_time_log_entry(filename, error_description, 0)
            log_to_file(error_log_entry, log_file_path)
            print(f"{filename}｜{desc} 發生錯誤: {str(e)}")
            raise e
    
    def _upsert_points(self, collection: str, points: List[PointStruct], filename: str, desc: str, log_file_path: str) -> None:
        """
        將點列表上傳到 Qdrant，並記錄日誌
        """
        try:
            upsert_start = time.time()
            self.client.upsert(collection_name=collection, points=points)
            log_entry = create_time_log_entry(filename, f"{desc}｜狀態：成功", upsert_start)
            log_to_file(log_entry, log_file_path)
        except Exception as e:
            error_description = f"ERROR: {desc} failed: {str(e)}"
            error_log_entry = create_time_log_entry(filename, error_description, 0)
            log_to_file(error_log_entry, log_file_path)
            print(f"{filename}｜{desc} 發生錯誤: {str(e)}")
            raise e
    
    def chunk_embedding_upsert(self, chunks: List[Dict], filename: str, collection: str, log_file_path: str, batch_size: int=config.chunk_batch_size) -> bool:
        """
        對切塊文本進行向量化並上傳到 Qdrant
        """
        success_flag = True
        indexer_embed_log_path = os.path.join(log_file_path, "indexer_embed.log")
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        for i in range(0, len(chunks), batch_size):
            batch_num = i // batch_size + 1
            batch_chunks = chunks[i:i+batch_size]
            try:
                # === 1. 向量化 ===
                content = [c["content"] for c in batch_chunks]
                batch_vectors = self._embed_text(
                    content,
                    filename,
                    f"Chunk embedding batch {batch_num}/{total_batches}",
                    indexer_embed_log_path
                )
                points = []
                # === 2. 建立資料點 ===
                for j, (chunk_dict, vector) in enumerate(zip(batch_chunks, batch_vectors)):
                    # 生成唯一的 point id
                    point_id = self._generate_point_id(filename, chunk_dict.get('page', 1), i+j, "chunk")
                    # 建立 payload
                    payload = {
                        'filename': chunk_dict.get("filename", filename),  # 來源檔名
                        'page': chunk_dict.get("page", 1),  # 來源的頁數
                        'content': chunk_dict.get("content", ""),  # chunk 內容
                    }
                    point = PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                    points.append(point)
                # === 3. 上傳 ===
                self._upsert_points(
                    collection,
                    points,
                    filename,
                    f"Chunk upsert batch {batch_num}/{total_batches}",
                    indexer_embed_log_path
                )
            except Exception as e:
                success_flag = False
                print(f"{filename}｜Chunk batch {batch_num} failed: {e}")
                continue
        return success_flag

    def summary_embedding_upsert(self, summary_data: Dict, collection: str, log_file_path: str) -> bool:
        """
        讀取單一摘要 JSON，向量化後上傳到 Qdrant
        """
        success_flag = True
        summary_embed_log_path = os.path.join(log_file_path, "summary_embed.log")
        # 如果摘要本身就標記為錯誤，直接略過
        if "error" in summary_data:
            return False
        fname = summary_data.get("filename", "unknown_file")
        text = f"{summary_data.get('title', '')} {summary_data.get('summary', '')}"
        try:
            # === 1. 向量化 ===
            vector = self._embed_text(
                [text],
                fname,
                "Summary embedding",
                summary_embed_log_path
            )[0]
            # === 2. 建立資料點 ===
            point_id = self._generate_point_id(fname, 0, 0, "summary")
            payload = {
                "filename": fname,
                "title": summary_data.get("title", ""),
                "file_type": summary_data.get("file_type", ""),
                "metadata": summary_data.get("metadata", []),
                "summary": summary_data.get("summary", "")
            }
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            # === 3. 上傳 ===
            self._upsert_points(
                collection,
                [point],
                fname,
                "Summary upsert",
                summary_embed_log_path
            )
        except Exception as e:
            success_flag = False
            print(f"{fname}｜Summary upsert failed: {e}")
        return success_flag
from typing import List, Any, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
import datetime
datetime = datetime.datetime
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config

# =======================
# 向量搜尋
# =======================
class VectorSearch:
    def __init__(self, embedding_model: Any) -> None:
        """初始化模型＋向量資料庫連線"""
        self.embedding = embedding_model
        try:
            # 雲端用
            # self.client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
            # 本機端測試用
            self.client = QdrantClient(path=config.PERSIST_DIRECTORY)
            print("✅ 向量資料庫連線成功！")
        except Exception as e:
            print(f"向量資料庫連線發生錯誤: {str(e)}")
            self.client = None

    def embed_query(self, text: str) -> List[float]:
        """將User query轉換為 embedding"""
        try:
            return self.embedding.embed_query(text)
        except Exception as e:
            print(f"❌ 向量化查詢時發生錯誤: {str(e)}")
            return []
        
    def _build_category_filter(self, categories: List[str] = None) -> Filter:
        """建立metadata類別過濾條件（目前無使用）"""
        if not categories:
            return None
        matching_sources = []
        for pdf_name, pdf_categories in config.PDF_METADATA.items():
            if any(category in pdf_categories for category in categories):
                matching_sources.append(pdf_name)
        if matching_sources:
            return Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchAny(any=matching_sources)
                    )
                ]
            )
        return None
    
    async def search(self, query: str, top_k: int, search_type: str, collection: str, categories: List[str] = None) -> Tuple[List[float], List[Any]]:
        """執行向量相似度搜尋"""
        # 建立過濾條件
        query_filter = self._build_category_filter(categories)
        if categories and not query_filter:
            return {"results": [], "total_count": 0}
        # 開始搜尋
        try:
            # === 1. 查詢向量化 ===
            print(f"🔍 查詢向量化 | query={query} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            embedding_start = time.time()
            query_vector = self.embed_query(query)
            embedding_elapsed = round(time.time() - embedding_start, 4)
            print(f"✅ 查詢向量化完成 | 耗時：{embedding_elapsed} 秒")
            # === 2. 執行搜尋 ===
            print(f"🔍 向量搜尋 | query={query} | top_k={top_k}")
            search_start = time.time()
            search_result = self.client.query_points(
                    collection_name=f"{search_type}_{collection}",
                    query=query_vector,
                    query_filter=query_filter,
                    with_payload=True,
                    limit=top_k
                ).points
            search_elapsed = round(time.time() - search_start, 4)
            print(f"✅ 向量搜尋完成 | 耗時：{search_elapsed} 秒 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return query_vector, search_result
        except Exception as e:
            print(f"❌ 搜尋時發生錯誤: {str(e)}")
            return []
from typing import List, Dict, Any
import numpy as np
import datetime
datetime = datetime.datetime
import time

# =======================
# 重排序方法：僅在 summary search 使用
# =======================
class Rerank:
    def __init__(self, embedding_model):
        """初始化重排序類別"""
        self.embedding = embedding_model
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """計算兩個向量的cos sim"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
        
    async def rerank_by_title(self, query_vector: List[float], results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """根據文件 title 與 query 相關性進行重排序"""
        print(f"🔄 開始 rerank_by_title，總文件數：{len(results)} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        rerank_start = time.time()
        reranked = []
        for res in results:
            # 計算 title 與 query 的相似度
            title_vector = self.embedding.embed_query(res["title"])
            res["title_similarity"] = self._cosine_similarity(query_vector, title_vector)
        reranked = sorted(results, key=lambda x: x["title_similarity"], reverse=True)
        reranked_elapsed = round(time.time() - rerank_start, 4)
        print(f"✅ rerank_by_title 完成 | 耗時：{reranked_elapsed} 秒 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Rerank 後，相似度分數範圍: {min(r['title_similarity'] for r in reranked):.4f} - {max(r['title_similarity'] for r in reranked):.4f}")
        return reranked
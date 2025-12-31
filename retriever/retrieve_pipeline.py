from typing import List, Dict, Union, Any
from langchain_community.embeddings import HuggingFaceEmbeddings
import datetime
datetime = datetime.datetime
from search import VectorSearch
from rerank import Rerank
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config

# =======================
# 檢索器
# =======================
class Retriever:
    def __init__(self, search_tool, rerank_tool):
        """初始化檢索器，注入依賴的工具實例"""
        self.searcher = search_tool
        self.reranker = rerank_tool
    
    def _process_search_results(self, search_type: str, search_result: List[Any]) -> List[Dict[str, Any]]:
        """處理搜尋結果，分成chunk與summary兩種格式"""
        results = []
        if search_type == "chunk":
            for point in search_result:
                result = {
                    'similarity_score': point.score,
                    'filename': point.payload.get('filename', ''),
                    'page': point.payload.get('page', ''),
                    'content_preview': point.payload.get('content', '')[:200] + "..." if len(point.payload.get('content', '')) > 200 else point.payload.get('content', ''),
                    'full_content': point.payload.get('content', '')
                }
                results.append(result)
        else:  # summary
            for point in search_result:
                result = {
                    'similarity_score': point.score,
                    'filename': point.payload.get('filename', ''),
                    'title': point.payload.get('title', ''),
                    'file_type': point.payload.get('file_type'),
                    'metadata': point.payload.get('metadata', []),
                    'summary': point.payload.get('summary', '')
                }
                results.append(result)        
        return results  
    
    async def retrieve(self, query: str, threshold_score: float, top_k: int, collection: str, search_type: str, categories: List[str] = None) -> Dict[str, Union[List[Any], int]]:
        """主要檢索流程"""
        # 執行向量搜尋
        query_vector, search_result = await self.searcher.search(query, top_k, search_type, collection, categories)
        # 處理搜尋結果
        results = self._process_search_results(search_type, search_result)
        print(f"📊 Search 後，相似度分數範圍: {min(r['similarity_score'] for r in results):.4f} - {max(r['similarity_score'] for r in results):.4f}")
        # 根據搜尋類型進行後處理
        # summary -> 重排序
        if search_type == "summary":
            reranked_output = await self.reranker.rerank_by_title(query_vector, results)
            filtered_reranked = [res for res in reranked_output if res['title_similarity'] >= threshold_score]
            return {
                "results": filtered_reranked,
                "total_count": len(filtered_reranked)   
            } 
        else: # chunk -> 直接過濾
            filtered_results = [res for res in results if res['similarity_score'] >= threshold_score]
            return {
                "results": filtered_results, 
                "total_count": len(filtered_results)
            }


# =======================
# 測試程式
# =======================
if __name__ == "__main__":
    # 模型載入
    print("🔄 開始載入 BGE-M3 模型...")
    EMBEDDING_MODEL = HuggingFaceEmbeddings(
                model_name=config.MODEL_NAME,
                model_kwargs=config.MODEL_KWARGS
            )
    print("✅ BGE-M3 模型載入完成！")
    
    # 實例化 searcher & reranker
    search_tool = VectorSearch(embedding_model=EMBEDDING_MODEL)
    rerank_tool = Rerank(embedding_model=EMBEDDING_MODEL)
    retriever = Retriever(search_tool=search_tool, rerank_tool=rerank_tool)
    
    # 執行檢索測試
    search_type = "summary"  
    # search_type = "chunk"
    collection = "form"
    test_query = "癌症保險 疾病等待期間"
    
    import asyncio
    resultDICT = asyncio.run(
        retriever.retrieve(
            query=test_query,
            threshold_score=config.THRESHOLD_SCORE,
            top_k=config.TOP_K,
            collection=collection,
            search_type=search_type
        )
    )
    print(f"📍搜尋方式：{search_type}｜回傳 {resultDICT['total_count']} 筆結果")
    
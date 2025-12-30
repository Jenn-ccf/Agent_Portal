from contextlib import asynccontextmanager
from typing import List, Dict, Any, Union, Optional
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from search import VectorSearch
from rerank import Rerank
from retrieve_pipeline import Retriever
from langchain_community.embeddings import HuggingFaceEmbeddings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔄 開始載入 EMBEDDING 模型...")
    EMBEDDING_MODEL = HuggingFaceEmbeddings(
        model_name=config.MODEL_NAME,
        model_kwargs=config.MODEL_KWARGS
    )
    print("✅ EMBEDDING 模型載入完成！")

    print("🔄 實例化 searcher & reranker...")
    search_tool = VectorSearch(embedding_model=EMBEDDING_MODEL)
    rerank_tool = Rerank(embedding_model=EMBEDDING_MODEL)
    print("✅ searcher & reranker 實例化完成！")
    
    app.state.retriever = Retriever(
        search_tool=search_tool,
        rerank_tool=rerank_tool
    )
    print("✅ RAG 檢索器初始化完成！")

    # 啟動完成 → 進入主程式
    yield

    # === shutdown 處理（可選）===
    print("🛑 服務正在關閉...")

app = FastAPI(title="RAG Retrieve API", lifespan=lifespan)

# =======================
# 定義 API 查詢請求模型
# =======================
class QueryRequest(BaseModel):
    """使用者查詢請求格式"""
    query: str  # 查詢內容
    top_k: int = config.TOP_K  # 返回結果數量
    threshold_score: float = config.THRESHOLD_SCORE  # 相似度閾值
    collection: Optional[str]   # 查詢 intent，用來指定 collection 名稱
    search_type: str  # 查詢類型：chunk 或 summary

# =======================
# API 路由設定
# =======================
@app.post("/retrieve")
async def retrieve(req: QueryRequest, request: Request) -> Dict[str, Union[List[Any], int]]:
    """使用檢索器處理搜尋請求並返回結果"""
    retriever = request.app.state.retriever

    if retriever is None:
        raise HTTPException(status_code=503, detail="檢索服務尚未啟動或初始化失敗。")
    try:
        final_output = await retriever.retrieve(
            query=req.query,
            top_k=req.top_k,
            threshold_score=req.threshold_score,
            collection=req.collection,
            search_type=req.search_type
        )
        return final_output
    except Exception as e:
        print(f"❌ 檢索過程中發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"檢索服務內部錯誤: {str(e)}")
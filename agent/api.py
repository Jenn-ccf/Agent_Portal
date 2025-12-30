from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
from agent_pipeline import agent_flow 

# =======================
# 初始化 FastAPI 應用
# =======================
app = FastAPI(title="MRKL Agent API")

# =======================
# 定義 API 查詢請求模型
# =======================
class QueryRequest(BaseModel):
    """使用者查詢請求格式"""
    query: str  # 查詢內容

# =======================
# API 路由設定
# =======================
@app.post("/agent")
async def ask_agent(req: QueryRequest) -> Dict[str, Any]:
    """處理 Agent 查詢請求並返回結果"""
    try:
        result_dict = agent_flow(
            req.query
        )
        return result_dict
    except Exception as e:
        return {"error": str(e)}


# =======================
# 結果格式範例 Memo
# =======================
"""
result_dict = {
    "query": query,
    "steps": steps,
    "final_result": final_answer
}
"""

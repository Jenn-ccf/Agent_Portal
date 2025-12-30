import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config
from typing import Dict, Any
from mrkl import MRKLAgent
   
def agent_flow(query: str) -> Dict[str, Any]:
    """主函數：執行 MRKL Agent，儲存整個查詢過程和最終結果"""
    steps = [
        {"start": "開始 Agent 執行..."},
    ]
    agent = MRKLAgent()
    result, final_answer = agent.query(query)
    steps.extend(result)
    steps.append({"end": "Agent 執行完成"})
    print(steps)
    return {
            "query": query,
            "steps": steps,
            "final_result": final_answer
        }

# =======================
# 測試主程式入口
# =======================
if __name__ == "__main__":
    query = "長照保險理賠流程？"
    agent_flow(query)
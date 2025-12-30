import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config
from typing import List, Tuple, Dict
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_aws import ChatBedrockConverse
from agent.search_tools import search_customer_policy, search_form, search_medical, search_product


# =======================
# MRKL Agent 類別：四個資料夾分別設定四個搜索工具
# =======================
class MRKLAgent:
    def __init__(self):
        """初始化 MRKL Agent，使用 Amazon Bedrock LLM"""
        print("🚀 Initializing MRKLAgent")
        try:
            self.llm = ChatBedrockConverse(
                model_id=config.BEDROCK_MODEL_ID,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                top_p=config.TOP_P,
            )
            print("✅ Bedrock LLM initialized successfully")
        except Exception as e:
            print("❌ Failed to initialize Bedrock LLM:", str(e))
        self._setup_tools()
        self._setup_agent()       
    
    def _setup_tools(self) -> None:
        """設置工具"""
        self.search_form_tool = Tool(
            name="Form Search",
            func=search_form,
            description="搜索「申請書、表單、聲明書」的collection"
        )
        self.search_product_tool = Tool(
            name="Product Search",
            func=search_product,
            description="搜索「商品、行銷」的collection"
        )
        self.search_policy_tool = Tool(
            name="Customer Policy Search",
            func=search_customer_policy,
            description="搜索「客戶服務、理賠、契約變更」的collection"
        )
        self.search_medical_tool = Tool(
            name="Medical Search",
            func=search_medical,
            description="搜索「投保、核保、醫務」的collection"
        )
    
    def _setup_agent(self) -> None:
        """設置 Agent"""
        print("🚀 Setting up MRKL Agent")
        try:
            # 初始化 agent 設定
            self.agent = initialize_agent(
                tools=[
                    self.search_form_tool,
                    self.search_product_tool,
                    self.search_policy_tool,
                    self.search_medical_tool
                ],
                llm=self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                agent_kwargs={
                    "prompt": config.FEW_SHOT_PROMPT
                },
                max_iterations=config.max_iterations,  # 最大迭代次數
                max_execution_time=config.max_execution_time,  # 最大執行時間（秒）
                verbose=True,  # 即時輸出日誌
                return_intermediate_steps=True,  # 返回中間步驟
                handle_parsing_errors=True,  # 處理解析錯誤
                early_stopping_method="generate"  # 提前停止方法
            )
            print("✅ MRKL Agent setup successfully")
        except Exception as e:
            print("❌ Failed to set up MRKL Agent:", str(e))

    def query(self, question: str) -> Tuple[List[Dict[str, str]], str]:
        """處理查詢，返回中間步驟和最終答案"""
        try:
            print("🚀 Invoking MRKL Agent")
            # 呼叫 agent
            response = self.agent.invoke({"input": question})
            print("✅ MRKL Agent invocation successful")
            print(f"Response: {response} | Type: {type(response)}")
            print(f"Intermediate Steps: {response.get('intermediate_steps'[0])}")
            # 處理中間步驟，存為列表
            inter_steps = []
            for agent_action, observation in response.get("intermediate_steps", []):
                step = {
                    "thought": agent_action.log.split("\n")[0],
                    "action": agent_action.tool,
                    "action_input": agent_action.tool_input,
                    "observation": str(observation)
                }
                inter_steps.append(step)
            # 最後加上 final answer
            final_step = {
                "final_answer": response.get("output", "未能獲取回答")
            }
            inter_steps.append(final_step)
            return inter_steps, final_step["final_answer"]
        except Exception as e:
            error_steps = [
                {"start": "開始 Agent 執行..."},
                {"error": f"處理查詢時發生錯誤: {str(e)}"}
            ]
            return error_steps, f"處理查詢時發生錯誤：{str(e)}"
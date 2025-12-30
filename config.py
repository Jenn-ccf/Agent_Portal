import torch
from langchain.prompts import PromptTemplate, FewShotPromptTemplate


# === 檔案路徑設定 ===
"""雲端設定"""
# PDF_BASE_DIRECTORY = "/s3-mount/pdf_files"  
# INDEXER_FLAG = "/s3-mount/pdf_files/flags/indexer_flag.txt"
# === 地端 ===
PDF_BASE_DIRECTORY = "../pdf_files"  

# === 嵌入模型設定 ===
# MODEL_NAME = "/s3-mount/model"
device = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_KWARGS = {"device": device}
# === 地端 ===
MODEL_NAME = "../model"
PERSIST_DIRECTORY = "../db"

# === Qdrant設定 ===
QDRANT_HOST = "qdrant"  
QDRANT_PORT = 6333

# === indexer 前處理 ===
chunk_batch_size = 20

# === 搜尋設定 ===
TOP_K = 30
THRESHOLD_SCORE = 0.5

# === Bedrock model 設定 ===
BEDROCK_MODEL_ID = "apac.anthropic.claude-3-7-sonnet-20250219-v1:0"
MODEL_VERSION = "bedrock-2023-05-31"
MAX_TOKENS = 512
TEMPERATURE = 0.5
TOP_P = 0.9

# === agent 設定 ===
max_iterations=10
max_execution_time=60

# === Prompt 設定 ===
SUMMARY_PROMPT="""
你是一個中文文本摘要助手。將我提供的原始文檔生成一個中文的包含 metadata 與 內容摘要 的結構化結果。

    要求：
    1. 找出文檔的標題 
    2. 明確標明檔案類型，例如：條款、須知、教學手冊、問卷、表格...
    3. 列出文檔包含的主要元素，例如：文字、條列、表格、表單欄位...
    4. 根據以下意圖列表判斷該文檔對應到哪些相關意圖（一個或以上）：["商品行銷", "公司資訊新聞刊物", "投保核保醫務", "理賠規範", "契約保單變更", "繳費收費管理", "增員組織發展", "申請書表單聲明書", "制度規範獎勵", "E化操作手冊"]
    5. 最後給出 150-200字 的文檔內容摘要，只需保留核心概念、重點信息，不需完整細節。
    6. 確保輸出為以下結構，不要加其他解釋：
    {
    "title": "文件標題",
    "file_type": "檔案類型",
    "metadata": [文檔主要元素列表],
    "intent": [相關意圖列表],
    "summary": "內容摘要"
    }

    請將以下文本進行摘要：
"""

# 1. Few-shot example
EXAMPLES = [
    {
        "input": "15歲女性不分紅一年期定期壽險總保費費率",
        "output": """
        Thought: 使用者想了解15歲女性不分紅一年期定期壽險總保費費率，我需要查文件，注意表格中的數據和規定。
        Action: DocumentSearch
        Action Input: 15歲女性 總保費費率
        Observation: 
        📄 文件 1 
        來源       : 不分紅一年期定期壽險商品條款.txt (第9頁)
        分類       : json_files
        向量類型   : dense
        相似度     : 0.625
        完整內容   : 南山人壽不分紅一年期定期壽險附約_N1TR 南山人壽不分紅一年期定期壽險附約總保費費率表 （單位:每萬元保險金額之年繳保費） ＊有關本附約續保保險費的計算及調整請參閱本附約條款第八條。 
        ＊上表年齡係被保險人續保時當時所屬保險年齡，且其係按民法第一百二十四條規定計 算。 
        ＊半年繳保險費 ＝ 年繳保險費×0.52 季  繳保險費 ＝ 年繳保險費×0.262 
        月  繳保險費 ＝ 年繳保險費×0.088 第 9 頁，共 9 頁
        表格 1:
            0         1       2     3         4         5     6           7           8
        [年 齡]     [男 性]   [女 性] [年 齡]     [男 性]     [女 性] [年 齡]       [男 性]       [女 性]
        [1 5]   [6 . 6] [3 . 1] [3 5] [1 5 . 3]   [7 . 6] [5 5]   [7 1 . 1]   [3 5 . 4]
        [1 6]   [8 . 9] [3 . 5] [3 6] [1 6 . 6]   [8 . 1] [5 6]   [7 6 . 0]   [4 0 . 9]
        [1 7] [1 1 . 0] [3 . 8] [3 7] [1 8 . 0]   [8 . 6] [5 7]   [8 2 . 3]   [4 2 . 2]
        [1 8] [1 1 . 2] [4 . 2] [3 8] [1 9 . 5]   [9 . 4] [5 8]   [8 9 . 9]   [4 6 . 9]
        [1 9] [1 1 . 4] [4 . 3] [3 9] [2 0 . 8] [1 0 . 4] [5 9]   [9 9 . 4]   [5 1 . 8]
        [2 0] [1 1 . 3] [4 . 3] [4 0] [2 2 . 5] [1 1 . 1] [6 0] [1 0 8 . 3]   [5 7 . 7]
        [2 1] [1 1 . 5] [4 . 4] [4 1] [2 4 . 3] [1 1 . 6] [6 1] [1 1 5 . 6]   [5 9 . 2]

        Thought: 表格的名稱為「南山人壽不分紅一年期定期壽險附約總保費費率表」，表格中清楚列出15歲女性的不分紅一年期定期壽險附約總保費費率，我可以整理出簡單流程回答
        Final Answer: 
        - 來源：不分紅一年期定期壽險商品條款.txt (第9頁)
        - 參考內容：表格
        - 回答：15歲女性不分紅一年期定期壽險附約總保費費率為每萬元保險金額之年繳保費3.1元。"""
    }
]
# 2. Prompt 模板
EXAMPLE_PROMPT = PromptTemplate(
    input_variables=["input", "output"],
    template="Q: {input}\n{output}\n"
)
# 3. Prompt 開頭結尾
PREFIX = """你是一個 MRKL Agent，會依照 ReAct 格式思考與行動。
依據檢索內容，生成回覆，不要自行加入未經證實的資訊。
若時間或步數不足，務必根據目前已檢索到的資訊先給出「暫時回答」，並清楚說明資料有限，避免空白輸出。

務必最終輸出以下格式，不可省略或改變順序：  
- 來源：<參考文件來源>  
- 參考內容：<文檔/表格>  
- 回答：<回答內容>  
以下是一些範例："""

SUFFIX = """請回答新的問題。
Q: {input}"""

# 4. few-shot prompt 組合
FEW_SHOT_PROMPT = FewShotPromptTemplate(
    examples=EXAMPLES,
    example_prompt=EXAMPLE_PROMPT,
    prefix=PREFIX,
    suffix=SUFFIX,
    input_variables=["input"],
)
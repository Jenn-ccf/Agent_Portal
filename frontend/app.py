"""
frontend/app.py - Streamlit 前端應用程式
- 建立使用者介面讓使用者能夠輸入查詢問題
- 分為 Agent 或 Document Search 進行查詢，最後顯示結果並收集使用者回饋
"""
import streamlit as st
import requests
import pandas as pd
import os
import datetime
import time
from typing import Tuple, List, Dict
from intent import expand_query
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config
import json
import logging
# === 設定 logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
def debug_log(msg):
    """同時輸出到 console 和 Streamlit"""
    logging.info(msg)
    st.info(f"{msg}")

# === 設定服務主機名稱 ===
# 雲端
RETRIEVER_HOST = "retriever"
AGENT_HOST = "agent"
# 本地
# RETRIEVER_HOST = "localhost"
# AGENT_HOST = "localhost"


# =======================
# 查詢功能： 分為 Agent 與 Document Search
# =======================
def run_agent(query: str) -> Tuple[list, str]:
    """ 1. Agent Search：呼叫 Agent API，返回 steps 與最終答案"""
    with st.spinner("Agent 正在思考中..."):
        try:
            url = f"http://{AGENT_HOST}:8001/agent"
            payload = {
                "query": query
            }
            debug_log(f"📤 呼叫 Agent API：{url}")
            call_agent_start = time.time()
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                call_agent_elapsed = round(time.time() - call_agent_start, 4)
                debug_log(f"🕒 Query：{query} | Agent API 呼叫 & 執行耗時：{call_agent_elapsed} 秒")
                return data.get("steps", []), data.get("final_answer", "")
            else:
                st.error("Agent API 連接失敗")
                return [], ""
        except Exception as e:
            st.error(f"執行 Agent 查詢時發生錯誤: {str(e)}")
            return [], ""

def run_document_search(intent_classify: tuple) -> Tuple[List[Dict], int]:
    """ 2. Document Search：呼叫 Retriever API，返回 final_results 與 total_counts"""
    with st.spinner("搜尋中..."):
        final_results = []
        total_count = 0
        for intent_collection, expanded_query in intent_classify:
            if intent_collection:
                st.info(f"**擴充後查詢：** {expanded_query} (分類至 {intent_collection})")
                try:
                    url = f"http://{RETRIEVER_HOST}:8000/search"
                    payload = {
                        "query": expanded_query,
                        "top_k": config.TOP_K,
                        "threashold_score": config.THRESHOLD_SCORE,
                        "collection": intent_collection,
                        "search_type": "summary"
                    }
                    debug_log(f"📤 呼叫 Document Search API：{url}")
                    call_search_start = time.time()
                    response = requests.post(url, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        call_search_elapsed = round(time.time() - call_search_start, 4)
                        debug_log(f"🕒 Query：{expanded_query} | Collection：summary_{intent_collection} | Retriver API 呼叫 & 執行耗時：{call_search_elapsed} 秒")
                        results = data.get("results", [])
                        count = data.get("total_count", 0)
                        final_results.extend(results)
                        total_count += count
                        st.success(f"✅ 搜尋完成")
                    else:
                        st.error("API 連接失敗")
                except Exception as e:
                    st.error(f"執行查詢時發生錯誤: {str(e)}")
        return final_results, total_count

# =======================
# 回饋處理
# =======================
def save_feedback(query: str, pdf_name: str, rating: str) -> None:
    """儲存使用者回饋到 JSON 檔案"""
    print("📢 呼叫儲存回饋功能")
    feedback_file = config.FEEDBACK_PATH
    feedback_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "query": query,
            "pdf_name": pdf_name,
            "rating": rating
        }     
    if os.path.exists(feedback_file):
        try:
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)
                st.success("✅ 成功讀取舊有回饋資料")
                try:
                    os.remove(feedback_file)
                    st.info("🗑️ 刪除舊檔案成功")
                except Exception as e:
                    st.error(f"⚠️ 刪除舊檔案失敗：{e}")
        except Exception as e:
            st.error(f"⚠️ 讀取舊有回饋資料失敗：{e}")
    else:
        st.info("📋 回饋檔案不存在，將建立新檔案")
        feedbacks = []
    feedbacks.append(feedback_data)
    # 儲存回 JSON
    try:
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)
            if os.path.exists(feedback_file):
                st.success("✅ 回饋資料已成功儲存")
    except Exception as e:
        # 區分錯誤原因
        if not os.path.exists(feedback_file):
            st.error(f"⚠️ 建立新檔案失敗：{e}")
        else:
            st.error(f"⚠️ 儲存回饋資料失敗：{e}")

# =======================
# 結果渲染：分為 Agent 與 Document 結果
# =======================
def display_agent_results(agent_steps: list) -> None:
    """ 1. Agent 結果渲染"""
    st.subheader("🧠 Agent 思考過程")
    for i, step in enumerate(agent_steps, 1):
        with st.container():
            if "start" in step:
                st.success("🚀 " + step["start"])
            elif "thought" in step and "action" in step:
                st.markdown(f"**💭 Thought：** {step['thought']}")
                st.markdown(f"**🛠 Action：** {step['action']}")
                st.markdown(f"**📥 Action Input：** {step['action_input']}")
                st.markdown("**👀 Observation：**")
                documents = step['observation'].split("------------------------------------------------------------")
                for j, doc in enumerate(documents, 1):
                    doc = doc.strip()
                    if not doc:
                        continue
                    with st.expander(f"📄 文件 {j}"):
                        st.write(doc)
                st.markdown("---")
            elif "final_answer" in step:
                st.subheader("🎯 最終回答")
                st.markdown(step["final_answer"])
            elif "end" in step:
                st.success("✅ " + step["end"])
            elif "error" in step:
                st.error("❌ " + step["error"])

def display_document_results(query: str, results: dict, total_count: int) -> None:
    """ 2. Document 結果渲染"""
    # # 加上threshold過濾
    # filtered_results = [r for r in results if r.get('title_similarity', 0) >= similarity_threshold]
    # # 排序過濾後的結果
    # sorted_results = sorted(filtered_results, key=lambda x: x['title_similarity'], reverse=True)
    # 原結果做排序
    sorted_results = sorted(results, key=lambda x: x['title_similarity'], reverse=True)
    st.success(f"✅ 搜尋完成，共找到 {total_count} 筆結果")
    st.subheader("相關文件搜尋結果")
    for i, result in enumerate(sorted_results):
        pdf_name = result.get("filename", "未命名PDF")
        similarity_score = result.get("title_similarity", 0)
        title = result.get("title", "未命名標題")
        summary = result.get("summary", "（無摘要）")
        col1, col2, col3 = st.columns([4, 2, 2])
        # 顯示檢索文件結果
        with col1:
            with st.expander(f"{pdf_name} - {title} - 相似分數：{similarity_score}", expanded=False):
                st.write(f"**摘要：** {summary}")
        # 回饋按鈕
        with col2:
            if st.button("有幫助👍", key=f"like_{pdf_name}_{i}"):
                save_feedback(query, pdf_name, "helpful")
                st.success("感謝你的評價！👍")
        with col3:
            if st.button("沒幫助👎", key=f"dislike_{pdf_name}_{i}"):
                save_feedback(query, pdf_name, "unhelpful")
                st.success("感謝你的評價！👎")   
        if i < len(sorted_results) - 1:
            st.divider()

# =======================
# Streamlit 前端應用程式
# =======================
st.title("📋一站式業務員平台 - 知識管理")
tab1, tab2 = st.tabs(["🤖 智能問答","📊 評價統計"])
# 查詢頁面
with tab1:
    if "agent_steps" not in st.session_state:
        st.session_state.agent_steps = []
    if "agent_answer" not in st.session_state:
        st.session_state.agent_answer = ""
    if "final_results" not in st.session_state:
        st.session_state.final_results = []
    if "total_counts" not in st.session_state:
        st.session_state.total_counts = 0
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""
    
    col1, col2 = st.columns([4,2])
    with col1:
        query = st.text_input("請輸入您的問題：", key="agent_query_2", placeholder="例如：15歲女性不分紅一年期定期壽險總保費費率")
    with col2:
        top_k = st.number_input("Top K results:", min_value=1, max_value=20, value=20, key="top_k_2")
    similarity_threshold = st.slider(
        "相似度門檻 (threshold)",
        min_value=0.0,
        max_value=1.0,
        value=0.6,  # 預設值
        step=0.01,
        key="similarity_threshold"
    )   
    # 開始查詢
    if st.button("Search", key="search_btn") and query:
        # 清空之前的結果
        st.session_state.last_query = query
        st.session_state.agent_steps = []
        st.session_state.agent_answer = ""
        st.session_state.final_results = []
        st.session_state.total_counts = 0
        
        if len(query) > 8:
            # 長 query → 直接 Agent
            st.session_state.agent_steps, st.session_state.agent_answer = run_agent(query)
        else:
            # 短 query → 嘗試 intent mapping
            checker, intent_classify = expand_query(query)  # 回傳 list of tuples [(collection, expanded_query), ...]
            if checker:
                # 命中 mapping → document search specific collections
                st.session_state.final_results, st.session_state.total_counts = run_document_search(intent_classify)
            else:
                # 沒命中 mapping → document search all collections
                st.info("查無相關分類，將 query 搜尋全部 collection")
                intent_classify = []
                for collection in config.ALL_COLLECTIONS:
                    # 把 query 配對到每個 collection
                    intent_classify.append((collection, query))
                st.session_state.final_results, st.session_state.total_counts = run_document_search(intent_classify)
    # 顯示結果 
    if st.session_state.agent_steps:
        display_agent_results(st.session_state.agent_steps)
    if st.session_state.final_results:
        display_document_results(st.session_state.last_query, st.session_state.final_results, st.session_state.total_counts)

# 評價統計頁面        
with tab2:
    feedback_file = config.FEEDBACK_PATH
    if os.path.exists(feedback_file):
        try:
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)
            if feedbacks:
                helpful_count = len([f for f in feedbacks if f['rating'] == 'helpful'])
                unhelpful_count = len([f for f in feedbacks if f['rating'] == 'unhelpful'])
                total_feedback = len(feedbacks)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👍 有幫助", helpful_count)
                with col2:
                    st.metric("👎 沒幫助", unhelpful_count)
                with col3:
                    st.metric("總評價數", total_feedback)
                if total_feedback > 0:
                    satisfaction_rate = (helpful_count / total_feedback) * 100
                    st.metric("滿意度", f"{satisfaction_rate:.1f}%")
                
                st.subheader("評價記錄")
                df = pd.DataFrame(feedbacks)
                display_df = df.copy()
                display_df['時間'] = df['timestamp'].str[:19]
                display_df['評價'] = df['rating'].apply(lambda x: "👍" if x == 'helpful' else "👎")
                final_df = display_df[['時間', 'query', 'pdf_name', '評價']].tail(20)
                final_df.columns = ['時間', '查詢問題', 'PDF檔名稱', '評價']
                
                st.dataframe(final_df, use_container_width=True)
            else:
                st.info("尚無評價記錄")
        except Exception as e:
            st.error(f"讀取評價記錄時發生錯誤: {e}")
    else:
        st.info("尚無評價記錄")
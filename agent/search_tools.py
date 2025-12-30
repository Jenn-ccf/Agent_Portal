import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config
import requests
import time
from datetime import datetime

# HOST = "retriever" # 雲端
HOST = "localhost"   # 本地

def search_form(query: str) -> str:
    """ 
    1. 搜索「其他各項表單」（chunk_other）
    """
    try:
        print(f"🔍 問題：{query} | Collection: chunk_other | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        search_start = time.time()
        # 呼叫 Retriever API
        response = requests.post(
            f"http://{HOST}:8000/retrieve",
            json={
                "query": query,
                "top_k": config.TOP_K,
                "threshold": config.THRESHOLD_SCORE,
                "search_type": "chunk",
                "collection": "other"
            }
        )
        # 處理回應
        if response.status_code == 200:
            results = response.json().get("results", [])
            if not results:
                return "沒有找到相關文件。"
            elapsed = round(time.time() - search_start, 4)
            print(f"✅ 搜尋結果返回，處理 format | 耗時：{elapsed} 秒")
            #  格式化結果
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted = (
                    f"📄 文件 {i}\n"
                    f"   來源: {result.get('filename', '未知')} (第{result.get('page', 'N/A')}頁)\n"
                    f"   相似度: {result.get('similarity_score', 0):.3f}\n"
                    f"   完整內容: {result.get('full_content', '').strip()}\n"
                    "------------------------------------------------------------"
                )
                formatted_results.append(formatted)
            print(f"✅ 格式化完成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return "\n".join(formatted_results)
        else:
            return f"❌ Error: Retriever API returned status code {response.status_code}"
    except Exception as e:
        return f"❌ Exception: {str(e)}"

def search_product(query: str) -> str:
    """ 
    2. 搜索「商品總覽」（chunk_product-overview）
    """
    try:
        print(f"🔍 問題：{query} | Collection: chunk_product-overview | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        search_start = time.time()
        # 呼叫 Retriever API
        response = requests.post(
            f"http://{HOST}:8000/retrieve",
            json={
                "query": query,
                "top_k": config.TOP_K,
                "threshold": config.THRESHOLD_SCORE,
                "search_type": "chunk",
                "collection": "product-overview"     
            }
        )
        # 處理回應
        if response.status_code == 200:
            results = response.json().get("results", [])
            if not results:
                return "沒有找到相關文件。"
            elapsed = round(time.time() - search_start, 4)
            print(f"✅ 搜尋結果返回，處理 format | 耗時：{elapsed} 秒")
            #  格式化結果
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted = (
                    f"📄 文件 {i}\n"
                    f"   來源: {result.get('filename', '未知')} (第{result.get('page', 'N/A')}頁)\n"
                    f"   相似度: {result.get('similarity_score', 0):.3f}\n"
                    f"   完整內容: {result.get('full_content', '').strip()}\n"
                    "------------------------------------------------------------"
                )
                formatted_results.append(formatted)
            print(f"✅ 格式化完成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return "\n".join(formatted_results)
        else:
            return f"❌ Error: Retriever API returned status code {response.status_code}"
    except Exception as e:
        return f"❌ Exception: {str(e)}"
        
def search_customer_policy(query: str) -> str:
    """ 
    3. 搜索「客戶服務保單服務」（chunk_costomer-policy-service）
    """
    try:
        print(f"🔍 問題：{query} | Collection: chunk_costomer-policy-service | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        search_start = time.time()
        # 呼叫 Retriever API
        response = requests.post(
            f"http://{HOST}:8000/retrieve",
            json={
                "query": query,
                "top_k": config.TOP_K,
                "threshold": config.THRESHOLD_SCORE,
                "search_type": "chunk",
                "collection": "costomer-policy-service"     
            }
        )
        # 處理回應
        if response.status_code == 200:
            results = response.json().get("results", [])
            if not results:
                return "沒有找到相關文件。"
            elapsed = round(time.time() - search_start, 4)
            print(f"✅ 搜尋結果返回，處理 format | 耗時：{elapsed} 秒")
            # 格式化結果
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted = (
                    f"📄 文件 {i}\n"
                    f"   來源: {result.get('filename', '未知')} (第{result.get('page', 'N/A')}頁)\n"
                    f"   相似度: {result.get('similarity_score', 0):.3f}\n"
                    f"   完整內容: {result.get('full_content', '').strip()}\n"
                    "------------------------------------------------------------"
                )
                formatted_results.append(formatted)
            print(f"✅ 格式化完成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return "\n".join(formatted_results)
        else:
            return f"❌ Error: Retriever API returned status code {response.status_code}"
    except Exception as e:
        return f"❌ Exception: {str(e)}"

def search_medical(query: str) -> str:
    """ 
    4. 搜索「投保與醫務」（chunk_application-and-medical）
    """
    try:
        print(f"🔍 問題：{query} | Collection: chunk_application-and-medical | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        search_start = time.time()
        # 呼叫 Retriever API
        response = requests.post(
            f"http://{HOST}:8000/retrieve",
            json={
                "query": query,
                "top_k": config.TOP_K,
                "threshold": config.THRESHOLD_SCORE,
                "search_type": "chunk",
                "collection": "application-and-medical"     
            }
        )
        # 處理回應
        if response.status_code == 200:
            results = response.json().get("results", [])
            if not results:
                return "沒有找到相關文件。"
            elapsed = round(time.time() - search_start, 4)
            print(f"✅ 搜尋結果返回，處理 format | 耗時：{elapsed} 秒")
            # 格式化結果
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted = (
                    f"📄 文件 {i}\n"
                    f"   來源: {result.get('filename', '未知')} (第{result.get('page', 'N/A')}頁)\n"
                    f"   相似度: {result.get('similarity_score', 0):.3f}\n"
                    f"   完整內容: {result.get('full_content', '').strip()}\n"
                    "------------------------------------------------------------"
                )
                formatted_results.append(formatted)
            print(f"✅ 格式化完成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return "\n".join(formatted_results)
        else:
            return f"❌ Error: Retriever API returned status code {response.status_code}"
    except Exception as e:
        return f"❌ Exception: {str(e)}"
    
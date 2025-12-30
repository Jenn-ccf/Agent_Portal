import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as config
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

def summarize_text(text: str) -> Optional[Dict[str, Any]]:
    """
    呼叫模型產生文章摘要
    """
    brt = boto3.client("bedrock-runtime")
    prompt = config.SUMMARY_PROMPT + text
    native_request = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": config.MAX_TOKENS,
        "temperature": config.TEMPERATURE,
        "top_p": config.TOP_P,
        "anthropic_version": config.MODEL_VERSION
    }   
    request = json.dumps(native_request)
    try:
        response = brt.invoke_model(
            modelId=config.BEDROCK_MODEL_ID,
            body=request
        )
        model_response = json.loads(response["body"].read())
        summary = model_response["content"][0]["text"]
        return summary.strip()
    except (ClientError, Exception) as e:
        print(f"❌ ERROR: 無法處理此文本。原因：{e}")
        return None

def summarize_document_from_json(input_json_path: str, output_json_path: str) -> Optional[Dict[str, Any]]:
    """
    讀取 OCR 輸出的 JSON 檔案，合併所有頁面的內容，
    然後呼叫 LLM 進行文件級別的摘要。
    """
    try:
        # 1. 讀取輸入的 JSON 檔案
        with open(input_json_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except Exception as e:
        print(f"讀取檔案 {input_json_path} 時發生錯誤: {str(e)}")
        return None
    # 2. 合併所有頁面的內容
    filename = input_data[0].get("filename", os.path.basename(input_json_path).replace('.json', '')) if input_data else "unknown_document"
    all_page_contents = []
    for item in input_data:
        content = item.get("content", "").strip()
        if content:
            # 使用兩行換行符分隔每頁內容，確保模型能區分頁面邊界
            all_page_contents.append(content)
    document_text = "\n\n".join(all_page_contents)
    if not document_text:
        print(f"⚠️ 文件 {filename} (來自 {input_json_path}) 內容為空，無法摘要。")
        return None
    print(f"ℹ️ 正在處理文件 {filename}，總長度為 {len(document_text)} 個字元...")
    # 3. 呼叫模型進行摘要，並解析成json
    summary_result = summarize_text(document_text)
    if summary_result:
        try:
            # 組織並返回結果
            summary_json = json.loads(summary_result)
            # 解析成功：加入 "filename" 鍵值對
            if isinstance(summary_json, dict):
                summary_json["filename"] = filename
                final_summary_data = summary_json
                print(f"✅ {filename} 已成功摘要並解析 JSON")
            else:
                # 即使解析成功，但如果不是字典（例如解析成 List 或單一字串），也視為格式錯誤
                raise json.JSONDecodeError("Model output is not a JSON object (dictionary).", summary_result, 0)
        except json.JSONDecodeError:
            print(f"⚠️ {filename} 解析失敗，將原始文字存入")
            final_summary_data = {
                "filename": filename,
                "error": "無法解析輸出，模型輸出不是有效的 JSON 格式", 
                "raw_output": summary_result
            }
    else:
        print(f"❌ 模型未能為文件 {filename} 產生摘要。")
        final_summary_data = {
            "filename": filename,
            "error": "模型未返回任何摘要內容", 
            "raw_output": document_text
        }
    # 4. 將結果寫入獨立 JSON 檔案
    try:
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(final_summary_data, f, ensure_ascii=False, indent=2)
        print(f"💾 摘要結果已儲存到 {output_json_path}")
        return True
    except Exception as e:
        print(f"❌ 寫入 JSON 檔案 {output_json_path} 失敗: {e}")
        return False
    
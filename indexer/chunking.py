import os
import json
from typing import List

def create_chunks(text: str, chunk_size: int = 1000) -> List[str]: 
    """
    將文本分塊
    """
    if not text:
        return []    
    if not isinstance(text, str):
        text = str(text)
    chunks = []
    text = text.replace('\n\n', '\n').strip()
    paragraphs = text.split('\n')
    current_chunk = ""    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < chunk_size:
            current_chunk += paragraph + "\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n"
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= chunk_size:
            final_chunks.append(chunk)
        else:
            sentences = chunk.split('。')
            temp_chunk = ""
            for sentence in sentences:
                if len(temp_chunk) + len(sentence) < chunk_size:
                    temp_chunk += sentence + "。"
                else:
                    if temp_chunk.strip():
                        final_chunks.append(temp_chunk.strip())
                    temp_chunk = sentence + "。"
            if temp_chunk.strip():
                final_chunks.append(temp_chunk.strip())
    return [chunk for chunk in final_chunks if len(chunk.strip()) > 50]

def process_json_to_chunks(input_json_path: str, output_json_path: str, metadata: List[str] = None) -> bool:
    """
    將原始 JSON檔中的文本切塊，並存為chunk JSON檔
    """
    try:
        # 1. 讀取輸入的 JSON 檔案
        with open(input_json_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        all_chunks = {}
        chunk_counter = 1
        # 目前沒有用到 metadata相關資訊
        if metadata is None:
            metadata = ["未分類"]
        # 2. 處理每一頁內容
        for item in input_data:
            filename = item.get("filename", "unknown_file")
            page_num = item.get("page", 0)
            content = item.get("content", "")
            if not content.strip():
                continue
            # 3. 對所有內容進行 chunking
            chunks = create_chunks(content)
            for chunk_content in chunks:
                chunk_key = f"chunk_{chunk_counter}"
                # 每個 chunk 會攜帶的資訊
                all_chunks[chunk_key] = {
                    "filename": filename, # 來源檔名
                    "page": page_num , # 來源的頁數
                    "content": chunk_content # chunk 內容
                }
                chunk_counter += 1
        # 4. 將結果寫入新的 JSON 檔案
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        print(f"✅ 已完成 chunking，共產生 {len(all_chunks)} 個 chunks，輸出存到 {output_json_path}")
        return True
    except Exception as e:
        print(f"處理 JSON 檔案 {input_json_path} 時發生錯誤: {str(e)}")
        return False
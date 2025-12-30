import fitz  # PyMuPDF
from img2table.document import PDF
from img2table.ocr import TesseractOCR
from collections import OrderedDict
from img2table.tables.objects.extraction import ExtractedTable, BBox
from typing import List, Dict, Tuple
import json
import os
import pandas as pd


def merge_tables_by_position(tables_dict:  Dict[int, List[ExtractedTable]]) -> Dict[int, List[ExtractedTable]]:
    """
    合併相鄰且應該是同一個表格的表格
    """
    merged_tables_dict = {}

    for page_num, table_list in tables_dict.items():
        if not table_list:
            merged_tables_dict[page_num] = []
            continue

        sorted_tables = sorted(table_list, key=lambda t: t.bbox.y1)
        merged_list = []

        i = 0
        while i < len(sorted_tables):
            current = sorted_tables[i]

            if i + 1 < len(sorted_tables):
                next_table = sorted_tables[i + 1]
                y_diff = next_table.bbox.y1 - current.bbox.y2

                if (y_diff < 100 and
                    abs(len(current.df.columns) - len(next_table.df.columns)) <= 1 and
                    abs(current.bbox.x1 - next_table.bbox.x1) < 100):

                    merged_content = OrderedDict()
                    for idx, row in current.content.items():
                        merged_content[idx] = row

                    offset = len(current.content)
                    for idx, row in next_table.content.items():
                        merged_content[idx + offset] = row

                    merged_bbox = BBox(
                        x1=min(current.bbox.x1, next_table.bbox.x1),
                        y1=current.bbox.y1,
                        x2=max(current.bbox.x2, next_table.bbox.x2),
                        y2=next_table.bbox.y2
                    )

                    merged_title = None
                    if current.title and next_table.title:
                        merged_title = current.title + " " + next_table.title
                    elif current.title:
                        merged_title = current.title
                    elif next_table.title:
                        merged_title = next_table.title

                    merged_table = ExtractedTable(
                        bbox=merged_bbox,
                        title=merged_title,
                        content=merged_content
                    )
                    i += 2
                    merged_list.append(merged_table)
                    continue
            merged_list.append(current)
            i += 1
        merged_tables_dict[page_num] = merged_list
    return merged_tables_dict


def extract_tables_and_text(pdf_path: str) -> Tuple[Dict[int, List[str]], Dict[int, List[pd.DataFrame]]]:
    """
    從 PDF 中提取表格和文字
    """
    ocr = TesseractOCR(n_threads=1, lang="eng+chi_tra")
    pdf_doc = PDF(src=pdf_path, pdf_text_extraction=True)
    extracted_tables = {}
    try:
        all_tables = pdf_doc.extract_tables(
            ocr=ocr,
            borderless_tables=True,
            min_confidence=50
        )
        extracted_tables = all_tables
    except Exception as e:
        print(f"警告：提取表格時發生錯誤，將略過表格提取: {e}")
        extracted_tables = {}

    try:
        merged_tables = merge_tables_by_position(extracted_tables)
    except Exception as e:
        print(f"警告：合併表格時發生錯誤: {e}")
        merged_tables = extracted_tables

    doc = fitz.open(pdf_path)
    tables_per_page = {}
    texts_per_page = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        tables = merged_tables.get(page_num, [])
        tables_per_page[page_num] = []
        table_bboxes = []
        for table in tables:
            try:
                scale = 72 / 200
                x0 = table.bbox.x1 * scale
                y0 = table.bbox.y1 * scale
                x1 = table.bbox.x2 * scale
                y1 = table.bbox.y2 * scale
                table_bboxes.append(fitz.Rect(x0, y0, x1, y1))
                tables_per_page[page_num].append(table.df)
            except Exception as e:
                print(f"警告：跳過第 {page_num+1} 頁的一個問題表格: {e}")
                continue
        blocks = page.get_text("blocks", sort=True)
        page_text = []
        for block in blocks:
            block_rect = fitz.Rect(block[0], block[1], block[2], block[3])
            if not any(block_rect.intersects(tb) for tb in table_bboxes):
                text = block[4].strip()
                if text:
                    page_text.append(text)
        combined_text = " ".join(page_text)
        texts_per_page[page_num] = [combined_text] if combined_text else []
    return texts_per_page, tables_per_page

def convert_pdf_to_json(pdf_path: str, json_path: str, with_tables: bool = True) -> bool:
    """
    將 PDF 內容轉換成 JSON 格式儲存。
    輸出格式為： [{"filename": ..., "page": ..., "content": ...}, ...]
    """
    try:
        text_pages, table_pages = extract_tables_and_text(pdf_path)
        # 找到最大頁碼
        all_pages = set(list(text_pages.keys()) + list(table_pages.keys()))
        if not all_pages:
            print(f"⚠️ PDF 檔案 {pdf_path} 中未提取到任何內容。")
            with open(json_path, 'w', encoding='utf-8') as f:
                 json.dump([], f, ensure_ascii=False, indent=4)
            return True
        max_page = max(all_pages)
        # 獲取檔名
        filename = os.path.basename(pdf_path)
        # 儲存結果的列表
        json_data = []
        for page_num in range(max_page + 1):
            page_content = []
            # 1. 加入文字內容
            if page_num in text_pages and text_pages[page_num]:
                for text in text_pages[page_num]:
                    if text.strip():
                        page_content.append(text.strip())
            # 2. 加入表格內容
            if with_tables and page_num in table_pages and table_pages[page_num]:
                for i, table in enumerate(table_pages[page_num]):
                    try:
                        table_text = f"--- 表格 {i+1} START ---\n"
                        if isinstance(table, pd.DataFrame):
                            table_text += table.to_string(index=False)
                        else:
                            table_text += str(table)
                        table_text += "\n--- 表格 END ---"
                        page_content.append(table_text)
                    except Exception as e:
                        print(f"處理頁碼 {page_num+1} 的表格時發生錯誤: {e}")
                        continue
            # 將該頁的所有內容合併成一個大字串
            combined_content = "\n".join(page_content)
            # 如果該頁有內容，則加入結果列表
            if combined_content.strip():
                json_data.append({
                    "filename": filename,
                    "page": page_num + 1,  # 頁碼從 1 開始
                    "content": combined_content
                })
        # 寫入 JSON 檔案
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        print(f"✅ 已完成轉換，共處理 {len(json_data)} 頁，輸出存到 {json_path}")
        return True
    except Exception as e:
        # 處理 PDF 檔案開啟或提取時的錯誤
        print(f"轉換 {pdf_path} 時發生錯誤: {str(e)}")
        return False
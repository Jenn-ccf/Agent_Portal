"""
frontend/intent.py - 關鍵詞查詢意圖擴展模組
讀取 kw_mapping.json，根據輸入的關鍵詞查找對應的意圖和相關詞
"""
import json
import config
from collections import defaultdict
import time
from typing import Tuple
import jieba
import re
from io import StringIO
from pprint import pprint

# 讀入 mapping.json
with open("kw_mapping.json", "r", encoding="utf-8") as f:
    mapping_data = json.load(f)

# 建立 keyword -> list of (intent, related_words)
mapping_dict = defaultdict(list)
for item in mapping_data:
    keyword = item["keyword"]
    intent = str(item["intent"])
    related_words = item["related_words"]
    mapping_dict[keyword].append((intent, related_words))

# 從 mapping_dict 提取所有關鍵字建立自定義字典
global_keywords = set(mapping_dict.keys())
user_dict_content: str = "\n".join(global_keywords)
user_dict_file = StringIO(user_dict_content)  # 模擬文件載入
jieba.load_userdict(user_dict_file)

print(f"✅ 成功從 {len(global_keywords)} 個關鍵字載入結巴自定義辭典！")
# 擴充查詢函數
def expand_query(query: str) -> Tuple[bool, list]:
    """
    回傳 list of tuples: (collection, expanded_query)
    每個 intent 對應一個 expanded query
    """
    results = []
    # 使用結巴斷詞
    word_list = jieba.lcut(query, cut_all=False)
    matched_keywords = set()
    for word in word_list:
        if word in mapping_dict:
            matched_keywords.add(word)   
    if matched_keywords:
        checker = True
        for matched_keyword in matched_keywords:
            # 取得對應的意圖和相關詞彙列表
            intent_list = mapping_dict[matched_keyword]
            for intent, related_words in intent_list:
                # 對應 collection
                collection = config.INTENT_COLLECTION_MAP.get(intent)
                # 移除標點，轉空格
                cleaned_related_words = re.sub(r'[、,，]', ' ', related_words).strip()
                expanded_query = matched_keyword + " " + cleaned_related_words
                results.append((collection, expanded_query))
    else:
        # 沒匹配到
        checker = False
        results.append(("NA", query))  
    return checker, results

# 使用範例
if __name__ == "__main__":
    input = "醫療"
    start_time = time.time()
    checker, results = expand_query(input)
    elapsed_time = round(time.time() - start_time, 4)
    print(f"Query Expansion 耗時：{elapsed_time} 秒")
    print(checker)
    pprint(results)

# Example output:
"""
results = expand_query(input_query)

results = [
    (intent_collection, expanded_query),
    (intent_collection, expanded_query),
    ...
]
results = [
    ('product', '保險金 保額 保險金額 基本保額'),
    ('claims', '保險金 理賠金 保險給付 給付金 保險金扣抵醫療費 保險金扣抵醫療費授權書 保險金扣抵醫療費服務流程 保險金扣抵醫療費相關問題'),
    ('changes', '保險金 保險理賠金 保險金申請書 理賠申請')
]

results[0][0] = "intent_collection" = 'product'
results[0][1] = "expanded_query" = '保險金 保額 保險金額 基本保額'
"""

import argparse
import time
from notion_helper import NotionHelper
import utils

# 提取文本的函数（复用 diary.py 的逻辑）
def get_text_from_blocks(blocks):
    """递归提取 Block 中的纯文本"""
    text_content = ""
    for block in blocks:
        b_type = block.get("type")
        if b_type in block and "rich_text" in block[b_type]:
            rich_texts = block[b_type].get("rich_text", [])
            for rt in rich_texts:
                text_content += rt.get("plain_text", "")
        
        # 简单处理子块（例如列表下的缩进），这里只处理一层以兼顾速度
        if block.get("has_children"):
            pass 
    return text_content

def count_history():
    helper = NotionHelper()
    print("正在获取所有日记页面，准备统计Word Count...")
    
    # 1. 获取所有日记
    all_pages = helper.query_all(helper.day_database_id)
    total = len(all_pages)
    print(f"共找到 {total} 篇日记。")

    count = 0
    for index, page in enumerate(all_pages):
        page_id = page.get("id")
        properties = page.get("properties")
        
        # 获取标题，方便日志显示
        title_prop = properties.get("Name") or properties.get("标题")
        title = "未知日期"
        if title_prop and title_prop.get("title"):
            title = title_prop.get("title")[0].get("plain_text")

        # 检查是否已经统计过（可选优化：如果Word Count已经大于0，可以选择跳过，节省时间）
        # word_count_prop = properties.get("Word Count", {}).get("number", 0)
        # if word_count_prop and word_count_prop > 0:
        #     print(f"[{index+1}/{total}] {title} 已有Word Count ({word_count_prop})，跳过。")
        #     continue

        print(f"[{index+1}/{total}] 正在统计: {title} ...")
        
        try:
            # 2. 读取页面内容块
            blocks = helper.get_block_children(page_id)
            full_text = get_text_from_blocks(blocks)
            
            # 3. 计算Word Count (去除空格换行)
            clean_text = full_text.replace(" ", "").replace("\n", "")
            word_count = len(clean_text)
            
            # 4. 更新属性
            new_props = {
                "Word Count": utils.get_number(word_count)
            }
            helper.update_page(page_id, new_props)
            print(f"   ✅ 更新成功: {word_count} 字")
            
            count += 1
            # 稍微暂停一下，避免触发 Notion API 速率限制
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ 处理失败 {title}: {e}")

    print(f"历史Word Count统计完成！共更新了 {count} 篇日记。")

if __name__ == "__main__":
    count_history()

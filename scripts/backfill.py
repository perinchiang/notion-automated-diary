import argparse
import pendulum
from notion_helper import NotionHelper
import utils
import time
# 引入你在 config.py 中定义的固定图标
from config import TARGET_ICON_URL 

def backfill_relations():
    helper = NotionHelper()
    print("🚀 开始执行：保持“日”动态图标，重置“年/月/周”为固定图标...")
    
    # 1. 获取所有日记页面
    all_pages = helper.query_all(helper.day_database_id)
    print(f"📦 共找到 {len(all_pages)} 篇日记。")

    count = 0
    # 记录已重置过的周期页面，避免重复操作
    reset_pages = set()

    for index, page in enumerate(all_pages):
        try:
            page_id = page.get("id")
            properties = page.get("properties")
            
            # --- A. 获取并解析日期 ---
            date_prop = properties.get("Date") or properties.get("日期")
            if not date_prop or not date_prop.get("date"):
                continue
                
            date_str = date_prop.get("date").get("start")
            date_obj = pendulum.parse(date_str).in_timezone("Asia/Shanghai")
            date_iso = date_obj.to_date_string()

            # --- B. 获取关联 ID ---
            year_id = helper.get_year_relation_id(date_obj)
            month_id = helper.get_month_relation_id(date_obj)
            week_id = helper.get_week_relation_id(date_obj)
            all_id = helper.get_relation_id("All", helper.all_database_id, "https://www.notion.so/icons/site-selection_gray.svg")

            # --- C. 更新“日”页面：继续使用动态图标 (type=2) ---
            # 加入 v 参数防止 Notion 缓存导致的显示错误
            day_icon_url = f"https://api.wolai.com/v1/icon?type=2&locale=en_US&date={date_iso}&pro=0&color=red&v={page_id[:8]}"
            
            new_props = {
                "Year": utils.get_relation([year_id]),
                "Month": utils.get_relation([month_id]),
                "Week": utils.get_relation([week_id]),
                "All": utils.get_relation([all_id])
            }
            
            helper.client.pages.update(
                page_id=page_id, 
                properties=new_props, 
                icon=utils.get_icon(day_icon_url)
            )

            # --- D. 重置“年/月/周”页面为固定图标 ---
            # 使用 config.py 里的 TARGET_ICON_URL，或者你自定义一个 URL
            fixed_icon = utils.get_icon(TARGET_ICON_URL)

            if year_id not in reset_pages:
                helper.client.pages.update(page_id=year_id, icon=fixed_icon)
                reset_pages.add(year_id)
                print(f"   ∟ 🏗️ 已重置年份图标: {date_obj.year}")

            if month_id not in reset_pages:
                helper.client.pages.update(page_id=month_id, icon=fixed_icon)
                reset_pages.add(month_id)
                print(f"   ∟ 📅 已重置月份图标: {date_obj.format('MMMM')}")

            if week_id not in reset_pages:
                helper.client.pages.update(page_id=week_id, icon=fixed_icon)
                reset_pages.add(week_id)
                print(f"   ∟ 🗓️ 已重置周进度图标: Week {date_obj.week_of_year}")

            count += 1
            if count % 20 == 0:
                print(f"✅ 已同步 {count} 篇日记...")
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ 处理出错: {e}")

    print(f"\n🎉 任务完成！“日”页面已美化，周期页面已回归简约。")

if __name__ == "__main__":
    backfill_relations()

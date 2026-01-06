import argparse
import pendulum
from notion_helper import NotionHelper
import utils
from config import TARGET_ICON_URL 

def backfill_relations():
    helper = NotionHelper()
    print("🚀 开始执行：强制刷新关联并同步日期图标...")
    
    all_pages = helper.query_all(helper.day_database_id)
    print(f"📦 共找到 {len(all_pages)} 篇日记。")

    count = 0
    # 定义基础图标 API 地址
    ICON_BASE_URL = "https://api.wolai.com/v1/icon?type=1&locale=cn&pro=0&color=red&method=f1"

    for index, page in enumerate(all_pages):
        try:
            page_id = page.get("id")
            properties = page.get("properties")
            
            # 1. 获取日期
            date_prop = properties.get("Date") or properties.get("日期")
            if not date_prop or not date_prop.get("date"):
                continue
                
            date_str = date_prop.get("date").get("start")
            date_obj = pendulum.parse(date_str).in_timezone("Asia/Shanghai")
            day_num = date_obj.day # 获取这一天是几号

            # 2. 计算关联 ID
            relation_ids = {
                "Year": helper.get_year_relation_id(date_obj),
                "Month": helper.get_month_relation_id(date_obj),
                "Week": helper.get_week_relation_id(date_obj),
                "All": helper.get_relation_id("All", helper.all_database_id, "https://www.notion.so/icons/site-selection_gray.svg")
            }

            # 3. 准备更新数据
            new_props = {
                "Year": utils.get_relation([relation_ids["Year"]]),
                "Month": utils.get_relation([relation_ids["Month"]]),
                "Week": utils.get_relation([relation_ids["Week"]]),
                "All": utils.get_relation([relation_ids["All"]])
            }

            # 🔴 关键点：动态生成日期图标 URL
            target_icon_url = f"{ICON_BASE_URL}&day={day_num}"
            new_icon = utils.get_icon(target_icon_url)

            # 4. 执行更新 (同时更新属性和图标)
            # 注意：helper.update_page 默认可能只改属性，我们要确保它也改了 icon
            helper.client.pages.update(
                page_id=page_id, 
                properties=new_props, 
                icon=new_icon
            )
            
            count += 1
            if count % 10 == 0:
                print(f"🔄 已处理 {count}/{len(all_pages)} 篇...")
            
        except Exception as e:
            print(f"❌ 处理出错 {page.get('id')}: {e}")

    print(f"\n🎉 迁移与图标同步完成！共处理了 {count} 篇日记。")

if __name__ == "__main__":
    backfill_relations()

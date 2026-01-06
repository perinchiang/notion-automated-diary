import argparse
import pendulum
from notion_helper import NotionHelper
import utils
import time

def backfill_relations():
    helper = NotionHelper()
    print("🚀 开始执行：全量同步日记、周、月、年【四合一】动态图标...")
    
    # 1. 获取所有日记页面
    all_pages = helper.query_all(helper.day_database_id)
    print(f"📦 共找到 {len(all_pages)} 篇日记。")

    count = 0
    # 用于记录已经更新过图标的页面ID，避免重复请求
    updated_pages = set()

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
            date_iso = date_obj.to_date_string() # 格式: 2026-01-07

            # --- B. 获取所有关联 ID ---
            # 这里的逻辑会确保 Year, Month, Week 页面存在并拿到 ID
            year_id = helper.get_year_relation_id(date_obj)
            month_id = helper.get_month_relation_id(date_obj)
            week_id = helper.get_week_relation_id(date_obj)
            all_id = helper.get_relation_id("All", helper.all_database_id, "https://www.notion.so/icons/site-selection_gray.svg")

            # --- C. 更新“日”页面 (图标 type=2) ---
            day_icon_url = f"https://api.wolai.com/v1/icon?type=2&locale=en_US&date={date_iso}&pro=0&color=red&v={page_id[:8]}"
            new_props = {
                "Year": utils.get_relation([year_id]),
                "Month": utils.get_relation([month_id]),
                "Week": utils.get_relation([week_id]),
                "All": utils.get_relation([all_id])
            }
            helper.client.pages.update(page_id=page_id, properties=new_props, icon=utils.get_icon(day_icon_url))

            # --- D. 递归更新：年、月、周页面的图标 (如果还没更新过) ---
            
            # 1. 更新月份图标 (type=4)
            if month_id not in updated_pages:
                first_day_month = date_obj.start_of('month').to_date_string()
                month_icon = f"https://api.wolai.com/v1/icon?type=4&locale=cn&date={first_day_month}&pro=0&color=red"
                helper.client.pages.update(page_id=month_id, icon=utils.get_icon(month_icon))
                updated_pages.add(month_id)
                print(f"   ∟ 📅 已更新月份图标: {date_obj.format('MMMM')}")

            # 2. 更新周图标 (type=10)
            if week_id not in updated_pages:
                # 获取该周周一的日期
                first_day_week = date_obj.start_of('week').to_date_string()
                week_icon = f"https://api.wolai.com/v1/icon?type=10&locale=cn&date={first_day_week}&pro=0&color=red"
                helper.client.pages.update(page_id=week_id, icon=utils.get_icon(week_icon))
                updated_pages.add(week_id)
                print(f"   ∟ 🗓️ 已更新周进度图标: Week {date_obj.week_of_year}")

            # 3. 更新年份图标 (type=5)
            if year_id not in updated_pages:
                first_day_year = date_obj.start_of('year').to_date_string()
                year_icon = f"https://api.wolai.com/v1/icon?type=5&locale=cn&date={first_day_year}&pro=0&color=red"
                helper.client.pages.update(page_id=year_id, icon=utils.get_icon(year_icon))
                updated_pages.add(year_id)
                print(f"   ∟ 🏗️ 已更新年份图标: {date_obj.year}")

            count += 1
            if count % 20 == 0:
                print(f"✅ 已同步 {count} 篇日记及其关联图标...")
            
            time.sleep(0.1) # 稍微减速，保护 API
            
        except Exception as e:
            print(f"❌ 处理页面时出错: {e}")

    print(f"\n🎉 完美达成！共处理 {count} 篇日记，同步了所有周期图标。")

if __name__ == "__main__":
    backfill_relations()

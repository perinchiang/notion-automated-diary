import argparse
import pendulum
from notion_helper import NotionHelper
import utils

def backfill_relations():
    helper = NotionHelper()
    print("正在获取所有日记数据，这可能需要一点时间...")
    
    # 1. 获取“日”数据库中的所有页面
    # query_all 会自动翻页获取所有数据
    all_pages = helper.query_all(helper.day_database_id)
    print(f"共找到 {len(all_pages)} 篇日记。")

    count = 0
    for page in all_pages:
        try:
            page_id = page.get("id")
            properties = page.get("properties")
            
            # 2. 获取日记的日期
            # 注意：这里对应你数据库里的日期列名 "Date"
            date_prop = properties.get("Date")
            if not date_prop or not date_prop.get("date"):
                print(f"跳过无日期的页面: {page_id}")
                continue
                
            date_str = date_prop.get("date").get("start")
            # 解析日期
            date_obj = pendulum.parse(date_str)
            # 统一转为 Asia/Shanghai 以计算周数
            date_obj = date_obj.in_timezone("Asia/Shanghai")
            
            # 3. 检查是否已经有关联 (为了节省资源，如果年月日周都有了，就不更新了)
            # 你可以注释掉下面这段 check，强制全部刷新
            has_year = len(properties.get("Year", {}).get("relation", [])) > 0
            has_month = len(properties.get("Month", {}).get("relation", [])) > 0
            has_week = len(properties.get("Week", {}).get("relation", [])) > 0
            
            if has_year and has_month and has_week:
                # print(f"跳过已归档页面: {date_str}")
                continue

            # 4. 计算关联 ID
            print(f"正在归档: {date_str} ...")
            relation_ids = {}
            relation_ids["Year"] = helper.get_year_relation_id(date_obj)
            relation_ids["Month"] = helper.get_month_relation_id(date_obj)
            relation_ids["Week"] = helper.get_week_relation_id(date_obj)
            relation_ids["All"] = helper.get_relation_id("全部", helper.all_database_id, "https://www.notion.so/icons/site-selection_gray.svg")

            # 5. 更新页面
            new_props = {}
            new_props["Year"] = utils.get_relation([relation_ids["Year"]])
            new_props["Month"] = utils.get_relation([relation_ids["Month"]])
            new_props["Week"] = utils.get_relation([relation_ids["Week"]])
            new_props["All"] = utils.get_relation([relation_ids["All"]])
            
            # 为了美观，我们也顺便把标题刷新一下，确保格式统一（可选）
            # new_props["Name"] = utils.get_title(date_obj.to_date_string())

            helper.update_page(page_id=page_id, properties=new_props)
            count += 1
            
        except Exception as e:
            print(f"处理页面出错 {page.get('id')}: {e}")

    print(f"处理完成！共更新了 {count} 篇日记。")

if __name__ == "__main__":
    backfill_relations()

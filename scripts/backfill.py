import argparse
import pendulum
from notion_helper import NotionHelper
import utils
from config import TARGET_ICON_URL # 确保引入图标配置

def backfill_relations():
    helper = NotionHelper()
    print("正在获取所有日记数据，准备迁移关联到英文属性...")
    
    # 1. 获取“日”数据库中的所有页面
    all_pages = helper.query_all(helper.day_database_id)
    print(f"共找到 {len(all_pages)} 篇日记。")

    count = 0
    for index, page in enumerate(all_pages):
        try:
            page_id = page.get("id")
            properties = page.get("properties")
            
            # 2. 获取日记的日期 (你改成了 Date，这里读取 Date)
            date_prop = properties.get("Date")
            if not date_prop or not date_prop.get("date"):
                # 如果 Date 没读到，尝试读一下老的中文“日期”防止遗漏，如果都没有则跳过
                date_prop = properties.get("日期")
                if not date_prop or not date_prop.get("date"):
                    print(f"⚠️ 跳过无日期的页面: {page_id}")
                    continue
                
            date_str = date_prop.get("date").get("start")
            # 解析日期
            date_obj = pendulum.parse(date_str)
            # 统一转为 Asia/Shanghai
            date_obj = date_obj.in_timezone("Asia/Shanghai")
            
            # 3. 检查是否已经有【英文】关联
            # 如果 Year, Month, Week, All 都有值了，就跳过（节省时间）
            # 如果你想强制全部刷新，请把下面这几行注释掉
            has_year = len(properties.get("Year", {}).get("relation", [])) > 0
            has_month = len(properties.get("Month", {}).get("relation", [])) > 0
            has_week = len(properties.get("Week", {}).get("relation", [])) > 0
            has_all = len(properties.get("All", {}).get("relation", [])) > 0
            
            if has_year and has_month and has_week and has_all:
                # print(f"   跳过已完成迁移的页面: {date_str}")
                continue

            # 4. 计算关联 ID
            print(f"[{index+1}/{len(all_pages)}] 正在迁移: {date_str} ...")
            relation_ids = {}
            relation_ids["Year"] = helper.get_year_relation_id(date_obj)
            relation_ids["Month"] = helper.get_month_relation_id(date_obj)
            relation_ids["Week"] = helper.get_week_relation_id(date_obj)
            # 注意：这里图标 URL 我直接写死或者从 config 引用，确保不出错
            relation_ids["All"] = helper.get_relation_id("All", helper.all_database_id, "https://www.notion.so/icons/site-selection_gray.svg")

            # 5. 更新页面 (关键修改：这里把 Key 改成新的英文属性名)
            new_props = {}
            new_props["Year"] = utils.get_relation([relation_ids["Year"]])
            new_props["Month"] = utils.get_relation([relation_ids["Month"]])
            new_props["Week"] = utils.get_relation([relation_ids["Week"]])
            new_props["All"] = utils.get_relation([relation_ids["All"]])
            
            # 选做：如果你原来的标题也没写对，顺便刷新一下标题 (去掉注释即可)
            # new_props["Name"] = utils.get_title(date_obj.to_date_string())

            helper.update_page(page_id=page_id, properties=new_props)
            count += 1
            print(f"   ✅ 迁移成功！")
            
        except Exception as e:
            print(f"❌ 处理页面出错 {page.get('id')}: {e}")

    print(f"🎉 全部完成！共迁移了 {count} 篇日记的关联。")

if __name__ == "__main__":
    backfill_relations()

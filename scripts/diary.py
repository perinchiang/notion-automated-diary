import argparse
import os
import requests
import pendulum
from notion_helper import NotionHelper
import utils
from config import RELATION, TITLE, DATE

# 动态图标
DIARY_ICON = "https://api.wolai.com/v1/icon?type=1&locale=cn&pro=0&color=red&method=f1"

# 多邻国配置
DUOLINGO_HEADERS = {
    "Accept": "*/*",
    "User-Agent": "request",
}

def get_text_from_blocks(blocks):
    """递归提取 Block 中的纯文本"""
    text_content = ""
    for block in blocks:
        # 尝试提取 rich_text 内容
        b_type = block.get("type")
        if b_type in block and "rich_text" in block[b_type]:
            rich_texts = block[b_type].get("rich_text", [])
            for rt in rich_texts:
                text_content += rt.get("plain_text", "")
        
        # 如果有子块（比如缩进的内容），虽然 Notion API 限制两层，但尽量尝试
        if block.get("has_children"):
            # 注意：Github Action 运行时间有限，且 Notion API 读取子块较慢
            # 这里为了速度，暂时只读取第一层内容的Word Count，通常足够了
            pass
            
    return text_content

def update_word_count(page_id):
    """统计页面Word Count并更新"""
    print(f"正在统计Word Count (Page ID: {page_id})...")
    try:
        # 获取所有 Block
        blocks = helper.get_block_children(page_id)
        full_text = get_text_from_blocks(blocks)
        
        # 统计Word Count (中文按字符统计，去除空格换行)
        clean_text = full_text.replace(" ", "").replace("\n", "")
        count = len(clean_text)
        
        # 更新到 Notion
        # 请确保你的 Notion 数据库里有一个叫 "Word Count" 的 Number 属性
        properties = {
            "Word Count": utils.get_number(count) 
        }
        helper.update_page(page_id, properties)
        print(f"✅ Word Count统计更新完毕: {count} 字")
        
    except Exception as e:
        print(f"❌ Word Count统计失败: {e}")

def get_duolingo_daily_stats():
    """获取多邻国数据 (保持原有逻辑)"""
    try:
        jwt = os.getenv('JWT')
        username = os.getenv('USER_NAME')
        if not jwt or not username:
            return None

        DUOLINGO_HEADERS["Authorization"] = f"Bearer {jwt.strip()}"
        r_user = requests.get(f"https://www.duolingo.com/users/{username.strip()}", headers=DUOLINGO_HEADERS)
        if not r_user.ok: return None
        
        user_data = r_user.json()
        duolingo_id = user_data["id"]
        streak = user_data.get("site_streak", 0)

        now = pendulum.now("Asia/Shanghai")
        today_str = now.to_date_string()
        start_date = now.subtract(days=1).to_date_string()
        
        r_xp = requests.get(
            f"https://android-api.duolingo.com/2017-06-30/users/{duolingo_id}/xp_summaries?endDate={today_str}&startDate={start_date}&timezone=Asia/Shanghai",
            headers=DUOLINGO_HEADERS,
        )
        
        today_xp = 0
        study_time = 0
        sessions = 0

        if r_xp.ok:
            summaries = r_xp.json().get("summaries", [])
            for item in summaries:
                date_ts = item.get("date")
                item_date = pendulum.from_timestamp(date_ts, tz="Asia/Shanghai").to_date_string()
                if item_date == today_str:
                    today_xp = item.get("gainedXp", 0)
                    study_time = item.get("totalSessionTime", 0)
                    sessions = item.get("numSessions", 0)
                    break
        
        minutes = study_time // 60
        content_str = f"连胜: {streak}天 | 经验: {today_xp} XP | 时长: {minutes} 分钟 | 单元: {sessions} 个"
        
        return [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "🦉 多邻国打卡"}}],
                    "color": "default"
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": content_str}}],
                    "icon": {"emoji": "🔥" if today_xp > 0 else "💤"},
                    "color": "green_background" if today_xp > 0 else "gray_background"
                }
            }
        ]
    except Exception as e:
        print(f"获取多邻国数据出错: {e}")
        return None

def create_daily_log():
    now = pendulum.now("Asia/Shanghai")
    today_str = now.to_date_string()
    print(f"开始处理日期: {today_str}")

    # 检查页面是否存在
    day_filter = {"property": "Name", "title": {"equals": today_str}}
    response = helper.query(database_id=helper.day_database_id, filter=day_filter)
    
    if len(response.get("results")) > 0:
        print(f"页面 {today_str} 已存在。")
        page_id = response.get("results")[0].get("id")
        
        # 【新功能】如果页面存在，说明可能是晚上运行，尝试更新Word Count
        update_word_count(page_id)
        return

    # 下面是创建页面的逻辑 (早上运行)
    relation_ids = {}
    relation_ids["年"] = helper.get_year_relation_id(now)
    relation_ids["月"] = helper.get_month_relation_id(now)
    relation_ids["周"] = helper.get_week_relation_id(now)
    relation_ids["全部"] = helper.get_relation_id("全部", helper.all_database_id, "https://www.notion.so/icons/site-selection_gray.svg")

    properties = {}
    properties["Name"] = utils.get_title(today_str)
    properties["Date"] = utils.get_date(now.to_date_string())
    properties["年"] = utils.get_relation([relation_ids["年"]])
    properties["月"] = utils.get_relation([relation_ids["月"]])
    properties["周"] = utils.get_relation([relation_ids["周"]])
    properties["全部"] = utils.get_relation([relation_ids["全部"]])
    # 初始化Word Count为 0
    properties["Word Count"] = utils.get_number(0)

    parent = {"database_id": helper.day_database_id, "type": "database_id"}
    new_page = helper.create_page(parent=parent, properties=properties, icon=utils.get_icon(DIARY_ICON))
    
    page_id = new_page.get("id")
    print(f"成功创建日记页面: {today_str}")

    # 写入多邻国数据
    duolingo_blocks = get_duolingo_daily_stats()
    if duolingo_blocks:
        helper.append_blocks(page_id, duolingo_blocks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    helper = NotionHelper()
    create_daily_log()

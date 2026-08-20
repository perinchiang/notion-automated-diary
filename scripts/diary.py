import argparse
import re
import pendulum
from notion_helper import NotionHelper
import utils
import time

# 动态图标（日期烧进 URL，渲染固定日期；type/颜色与模板手动建的页面保持一致）
DIARY_ICON = "https://api.wolai.com/v1/icon?type=2&locale=en_US&pro=0&color=red&v=2de28fdf&date={date}"

ALL_ICON_URL = "https://www.notion.so/icons/site-selection_gray.svg"


def get_text_from_blocks(blocks):
    """提取 Block 中的纯文本"""
    text_content = ""
    for block in blocks:
        b_type = block.get("type")
        if b_type in block and "rich_text" in block[b_type]:
            rich_texts = block[b_type].get("rich_text", [])
            for rt in rich_texts:
                text_content += rt.get("plain_text", "")
    return text_content


def count_words(page_id):
    blocks = helper.get_block_children(page_id)
    clean_text = get_text_from_blocks(blocks).replace(" ", "").replace("\n", "")
    return len(clean_text)


def get_title(props):
    title_prop = props.get("Name") or props.get("标题")
    if title_prop and title_prop.get("title"):
        return title_prop["title"][0].get("plain_text", "未知日期")
    return "未知日期"


def relation_filled(props, name):
    prop = props.get(name) or {}
    return bool(prop.get("relation"))


def maintain_page(page, day, day_str):
    """维护一篇已存在的日记：补 Date、补 Year/Month/Week/All 关联、统计字数。不创建任何页面。"""
    page_id = page.get("id")
    props = page.get("properties", {})
    print(f"📝 {day_str} ({get_title(props)}) ...", end="")

    updates = {}
    if not (props.get("Date") or {}).get("date"):
        updates["Date"] = utils.get_date(day_str)

    if not relation_filled(props, "Year"):
        updates["Year"] = utils.get_relation([helper.get_year_relation_id(day)])
    if not relation_filled(props, "Month"):
        updates["Month"] = utils.get_relation([helper.get_month_relation_id(day)])
    if not relation_filled(props, "Week"):
        updates["Week"] = utils.get_relation([helper.get_week_relation_id(day)])
    if not relation_filled(props, "All"):
        updates["All"] = utils.get_relation(
            [helper.get_relation_id("All", helper.all_database_id, ALL_ICON_URL)]
        )

    try:
        count = count_words(page_id)
        updates["Word Count"] = utils.get_number(count)
        extra = "，已补日期/关联" if len(updates) > 1 else ""
        print(f" ✅ {count} 字{extra}")
    except Exception as e:
        print(f" ❌ 字数统计失败: {e}")

    if updates:
        helper.update_page(page_id, updates)
    time.sleep(0.5)


def maintain_recent_days(days=7):
    now = pendulum.now("Asia/Shanghai")
    start_date = now.subtract(days=days).to_date_string()
    print(f"🔍 扫描最近 {days} 天的日记（只维护，不创建）...")

    seen = set()

    # 1. 按 Date 属性找（标题随意但设置了 Date 的页面）
    response = helper.query(
        database_id=helper.day_database_id,
        filter={"property": "Date", "date": {"on_or_after": start_date}},
    )
    for page in response.get("results", []):
        date_value = ((page.get("properties") or {}).get("Date") or {}).get("date") or {}
        start = date_value.get("start")
        if not start:
            continue
        seen.add(page.get("id"))
        maintain_page(page, pendulum.parse(start[:10], tz="Asia/Shanghai"), start[:10])

    # 2. 按标题找（标题是 YYYY-MM-DD 但没设 Date 的页面）
    for i in range(days):
        day = now.subtract(days=i)
        day_str = day.to_date_string()
        response = helper.query(
            database_id=helper.day_database_id,
            filter={"property": "Name", "title": {"equals": day_str}},
        )
        for page in response.get("results", []):
            if page.get("id") in seen:
                continue
            seen.add(page.get("id"))
            maintain_page(page, day, day_str)

    print(f"📦 近期扫描共处理 {len(seen)} 篇。")
    return seen


def maintain_unlinked(seen=None):
    """全库兜底：找出任何缺 Date / Year / Month / Week / All / Word Count 的页面（不限日期），
    覆盖'心血来潮导入一篇旧日记'的场景——只要 Date 设对或标题是 YYYY-MM-DD，就会被自动关联。"""
    seen = seen or set()
    flt = {
        "or": [
            {"property": "Date", "date": {"is_empty": True}},
            {"property": "Year", "relation": {"is_empty": True}},
            {"property": "Month", "relation": {"is_empty": True}},
            {"property": "Week", "relation": {"is_empty": True}},
            {"property": "All", "relation": {"is_empty": True}},
            {"property": "Word Count", "number": {"is_empty": True}},
        ]
    }
    results = []
    cursor = None
    while True:
        kwargs = {"database_id": helper.day_database_id, "filter": flt, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        response = helper.query(**kwargs)
        results.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    print(f"🧹 兜底扫描：发现 {len(results)} 篇缺关联/字数的页面（不限日期）...")

    fixed, skipped = 0, 0
    for page in results:
        if page.get("id") in seen:
            continue
        props = page.get("properties", {})
        date_value = (props.get("Date") or {}).get("date") or {}
        start = (date_value.get("start") or "")[:10]

        title = ""
        title_prop = props.get("Name") or {}
        for t in title_prop.get("title", []):
            title += t.get("plain_text", "")

        day = None
        if start:
            day = pendulum.parse(start, tz="Asia/Shanghai")
        else:
            m = re.match(r"^(\d{4}-\d{2}-\d{2})", title.strip())
            if m:
                day = pendulum.parse(m.group(1), tz="Asia/Shanghai")

        if day is None:
            skipped += 1
            print(f"   ⏭️ 跳过「{title or '无标题'}」：既无 Date，标题也不是 YYYY-MM-DD")
            continue

        maintain_page(page, day, day.to_date_string())
        fixed += 1

    print(f"🧹 兜底修复 {fixed} 篇，跳过 {skipped} 篇（无法判断日期，不碰）。")


def create_daily_log():
    """旧行为：自动创建今日页面。用 --create 启用。"""
    now = pendulum.now("Asia/Shanghai")
    today_str = now.to_date_string()
    print(f"🚀 开始今日任务: {today_str}")

    day_filter = {"property": "Name", "title": {"equals": today_str}}
    response = helper.query(database_id=helper.day_database_id, filter=day_filter)

    if len(response.get("results")) > 0:
        print(f"✅ 今日页面 {today_str} 已存在。")
    else:
        print(f"✨ 创建新页面: {today_str}")
        relation_ids = {}
        relation_ids["Year"] = helper.get_year_relation_id(now)
        relation_ids["Month"] = helper.get_month_relation_id(now)
        relation_ids["Week"] = helper.get_week_relation_id(now)
        relation_ids["All"] = helper.get_relation_id("All", helper.all_database_id, ALL_ICON_URL)

        properties = {}
        properties["Name"] = utils.get_title(today_str)
        properties["Date"] = utils.get_date(today_str)
        properties["Year"] = utils.get_relation([relation_ids["Year"]])
        properties["Month"] = utils.get_relation([relation_ids["Month"]])
        properties["Week"] = utils.get_relation([relation_ids["Week"]])
        properties["All"] = utils.get_relation([relation_ids["All"]])
        properties["Word Count"] = utils.get_number(0)

        parent = {"database_id": helper.day_database_id, "type": "database_id"}
        icon_url = DIARY_ICON.format(date=today_str)
        helper.create_page(parent=parent, properties=properties, icon=utils.get_icon(icon_url))

    maintain_recent_days(7)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, help="维护最近 N 天")
    parser.add_argument("--create", action="store_true", help="启用旧的自动创建页面行为")
    args = parser.parse_args()
    helper = NotionHelper()
    if args.create:
        create_daily_log()
    else:
        seen = maintain_recent_days(args.days)
        maintain_unlinked(seen)

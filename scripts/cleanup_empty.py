"""一次性清理：归档历史遗留的自动创建空日记页。

判定条件（全部满足才归档）：
1. Word Count 为空或 0
2. Mood 关联为空
3. Categories 关联为空
4. Date 早于今天（今天的页面绝不碰）
5. 逐页读取正文确认没有任何文字或附件（防止"写了但没同步字数"的页面误删）

默认只预览，加 --apply 才真正归档。归档的页面可在 Notion 回收站恢复。
"""
import argparse
import pendulum
import time
from notion_helper import NotionHelper


ATTACHMENT_TYPES = {"image", "file", "pdf", "video", "audio", "embed", "bookmark"}


def has_content(blocks):
    """文字、图片、PDF、语音、视频、附件、书签，任何一样都算有内容。"""
    for block in blocks:
        b_type = block.get("type")
        if b_type in ATTACHMENT_TYPES:
            return True
        if b_type in block and "rich_text" in block[b_type]:
            if any(rt.get("plain_text", "").strip() for rt in block[b_type].get("rich_text", [])):
                return True
    return False


def get_title(props):
    title = ""
    for t in (props.get("Name") or {}).get("title", []):
        title += t.get("plain_text", "")
    return title


def query_candidates(database_id, before_date):
    flt = {
        "and": [
            {"property": "Date", "date": {"on_or_before": before_date}},
            {"property": "Mood", "relation": {"is_empty": True}},
            {"property": "Categories", "relation": {"is_empty": True}},
            {
                "or": [
                    {"property": "Word Count", "number": {"is_empty": True}},
                    {"property": "Word Count", "number": {"equals": 0}},
                ]
            },
        ]
    }
    results = []
    cursor = None
    while True:
        kwargs = {"database_id": database_id, "filter": flt, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        response = helper.query(**kwargs)
        results.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return results


def main(apply):
    yesterday = pendulum.now("Asia/Shanghai").subtract(days=1).to_date_string()
    candidates = query_candidates(helper.day_database_id, yesterday)
    print(f"🧹 候选空页面 {len(candidates)} 篇（无字数/0字 + 无心情 + 无分类 + 日期早于 {yesterday}）")

    archived, protected = 0, 0
    for page in candidates:
        page_id = page.get("id")
        title = get_title(page.get("properties", {}))
        try:
            blocks = helper.get_block_children(page_id)
            if has_content(blocks):
                protected += 1
                print(f"   🛡️ 「{title}」正文有内容/附件，保护跳过（交给每晚脚本补字数）")
                continue
            if apply:
                helper.client.pages.update(page_id=page_id, archived=True)
                print(f"   🗑️ 已归档「{title}」")
            else:
                print(f"   👀 预览：将归档「{title}」")
            archived += 1
            time.sleep(0.4)
        except Exception as e:
            print(f"   ❌ 「{title}」处理失败: {e}")

    action = "已归档" if apply else "预览（未执行，dispatch 时勾选 apply 才会真正归档）"
    print(f"\n{'🗑️' if apply else '👀'} {action} {archived} 篇，{protected} 篇有内容被保护。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="真正执行归档；默认只预览")
    args = parser.parse_args()
    helper = NotionHelper()
    main(args.apply)

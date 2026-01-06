import logging
import os
import re
import time
# 引入 locale 库以支持月份英文名（可选，但使用 pendulum format 更方便）
import pendulum 

from notion_client import Client
from retrying import retry
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()
from utils import (
    format_date,
    get_date,
    get_first_and_last_day_of_month,
    get_first_and_last_day_of_week,
    get_first_and_last_day_of_year,
    get_icon,
    get_number,
    get_relation,
    get_rich_text,
    get_title,
    timestamp_to_date,
    get_property_value,
)
from config import (
    TARGET_ICON_URL,
    TAG_ICON_URL,
    USER_ICON_URL,
    BOOKMARK_ICON_URL,
)


class NotionHelper:
    # 🔴 修改点 1：把这里的中文名全部改为英文，对应 Notion 数据库的新名字
    database_name_dict = {
        "DAY_DATABASE_NAME": "Day",
        "WEEK_DATABASE_NAME": "Week",
        "MONTH_DATABASE_NAME": "Month",
        "YEAR_DATABASE_NAME": "Year",
        "ALL_DATABASE_NAME": "All",
        "MISTAKE_DATABASE_NAME": "Mistakes", # 如果你有错题本也顺便改了
    }
    database_id_dict = {}
    heatmap_block_id = None

    def __init__(self):
        self.client = Client(auth=os.getenv("NOTION_TOKEN"), log_level=logging.ERROR)
        self.__cache = {}
        self.page_id = self.extract_page_id(os.getenv("NOTION_PAGE"))
        self.search_database(self.page_id)
        for key in self.database_name_dict.keys():
            if os.getenv(key) != None and os.getenv(key) != "":
                self.database_name_dict[key] = os.getenv(key)

        self.day_database_id = self.database_id_dict.get(
            self.database_name_dict.get("DAY_DATABASE_NAME")
        )
        self.week_database_id = self.database_id_dict.get(
            self.database_name_dict.get("WEEK_DATABASE_NAME")
        )
        self.month_database_id = self.database_id_dict.get(
            self.database_name_dict.get("MONTH_DATABASE_NAME")
        )
        self.year_database_id = self.database_id_dict.get(
            self.database_name_dict.get("YEAR_DATABASE_NAME")
        )
        self.all_database_id = self.database_id_dict.get(
            self.database_name_dict.get("ALL_DATABASE_NAME")
        )
        self.mistake_database_id = self.database_id_dict.get(
            self.database_name_dict.get("MISTAKE_DATABASE_NAME")
        )

        if self.day_database_id:
            self.write_database_id(self.day_database_id)

    def write_database_id(self, database_id):
        env_file = os.getenv('GITHUB_ENV')
        if env_file:
            with open(env_file, "a") as file:
                file.write(f"DATABASE_ID={database_id}\n")

    def extract_page_id(self, notion_url):
        match = re.search(
            r"([a-f0-9]{32}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",
            notion_url,
        )
        if match:
            return match.group(0)
        else:
            raise Exception(f"获取NotionID失败，请检查输入的Url是否正确")

    def search_database(self, block_id):
        children = self.client.blocks.children.list(block_id=block_id)["results"]
        for child in children:
            if child["type"] == "child_database":
                self.database_id_dict[child.get("child_database").get("title")] = (
                    child.get("id")
                )
            elif child["type"] == "embed" and child.get("embed").get("url"):
                if (
                    child.get("embed")
                    .get("url")
                    .startswith("https://heatmap.malinkang.com/")
                ):
                    self.heatmap_block_id = child.get("id")
            if "has_children" in child and child["has_children"]:
                self.search_database(child["id"])

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def update_heatmap(self, block_id, url):
        return self.client.blocks.update(block_id=block_id, embed={"url": url})

    def get_week_relation_id(self, date):
        # 🔴 修改点 2：周标题格式化 (例如: 2026 Week 1)
        year = date.isocalendar().year
        week_num = date.isocalendar().week
        week_title = f"{year} Week {week_num}"
        
        start, end = get_first_and_last_day_of_week(date)
        properties = {"Date": get_date(format_date(start), format_date(end))}
        return self.get_relation_id(
            week_title, self.week_database_id, TARGET_ICON_URL, properties
        )

    def get_month_relation_id(self, date):
        # 🔴 修改点 3：月标题格式化 (例如: January 2026)
        # 使用 pendulum 的 format 功能，locale='en' 确保是英文
        month_title = date.format("MMMM YYYY", locale="en")
        
        start, end = get_first_and_last_day_of_month(date)
        # 注意：这里的Date属性名我保持了中文"Date"，如果你的月数据库列名也改成了"Date"，请把下面的"Date"改为"Date"
        properties = {"Date": get_date(format_date(start), format_date(end))}
        return self.get_relation_id(
            month_title, self.month_database_id, TARGET_ICON_URL, properties
        )

    def get_year_relation_id(self, date):
        # 年标题 (2026) 纯数字不用改
        year = date.strftime("%Y")
        start, end = get_first_and_last_day_of_year(date)
        # 注意：同上，确认年数据库的Date列名
        properties = {"Date": get_date(format_date(start), format_date(end))}
        return self.get_relation_id(
            year, self.year_database_id, TARGET_ICON_URL, properties
        )

    def get_day_relation_id(self, date):
        new_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day = new_date.strftime("%Y-%m-%d")
        properties = {
            "Date": get_date(format_date(date)),
        }
        # 🔴 修改点 4：这里生成日记时的关联键名也要改成英文
        properties["Year"] = get_relation([self.get_year_relation_id(new_date)])
        properties["Month"] = get_relation([self.get_month_relation_id(new_date)])
        properties["Week"] = get_relation([self.get_week_relation_id(new_date)])
        
        return self.get_relation_id(
            day, self.day_database_id, TARGET_ICON_URL, properties
        )

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def get_relation_id(self, name, id, icon, properties={}):
        key = f"{id}{name}"
        if key in self.__cache:
            return self.__cache.get(key)
        
        # 这里的 Name 保持不变，因为我们之前统一了所有库的第一列都叫 Name
        filter = {"property": "Name", "title": {"equals": name}}
        
        response = self.client.databases.query(database_id=id, filter=filter)
        if len(response.get("results")) == 0:
            parent = {"database_id": id, "type": "database_id"}
            properties["Name"] = get_title(name)
            
            page_id = self.client.pages.create(
                parent=parent, properties=properties, icon=get_icon(icon)
            ).get("id")
        else:
            page_id = response.get("results")[0].get("id")
        self.__cache[key] = page_id
        return page_id

    # ... (后面的 create_page, update_page 等通用函数保持不变即可) ...
    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def update_book_page(self, page_id, properties):
        return self.client.pages.update(page_id=page_id, properties=properties)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def update_page(self, page_id, properties):
        return self.client.pages.update(page_id=page_id, properties=properties)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def create_page(self, parent, properties, icon):
        return self.client.pages.create(parent=parent, properties=properties, icon=icon)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def query(self, **kwargs):
        kwargs = {k: v for k, v in kwargs.items() if v}
        return self.client.databases.query(**kwargs)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def get_block_children(self, id):
        response = self.client.blocks.children.list(id)
        return response.get("results")

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def append_blocks(self, block_id, children):
        return self.client.blocks.children.append(block_id=block_id, children=children)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def append_blocks_after(self, block_id, children, after):
        return self.client.blocks.children.append(
            block_id=block_id, children=children, after=after
        )

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def delete_block(self, block_id):
        return self.client.blocks.delete(block_id=block_id)

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def query_all_by_book(self, database_id, filter):
        results = []
        has_more = True
        start_cursor = None
        while has_more:
            response = self.client.databases.query(
                database_id=database_id,
                filter=filter,
                start_cursor=start_cursor,
                page_size=100,
            )
            start_cursor = response.get("next_cursor")
            has_more = response.get("has_more")
            results.extend(response.get("results"))
        return results

    @retry(stop_max_attempt_number=3, wait_fixed=5000)
    def query_all(self, database_id):
        results = []
        has_more = True
        start_cursor = None
        while has_more:
            response = self.client.databases.query(
                database_id=database_id,
                start_cursor=start_cursor,
                page_size=100,
            )
            start_cursor = response.get("next_cursor")
            has_more = response.get("has_more")
            results.extend(response.get("results"))
        return results

    def get_date_relation(self, properties, date, include_day=False):
        if include_day:
            properties["Day"] = get_relation(
                [self.get_day_relation_id(date)]
            )
        properties["Year"] = get_relation(
            [self.get_year_relation_id(date)]
        )
        properties["Month"] = get_relation(
            [self.get_month_relation_id(date)]
        )
        properties["Week"] = get_relation(
            [self.get_week_relation_id(date)]
        )
        properties["All"] = get_relation(
            [self.get_relation_id("All", self.all_database_id, TARGET_ICON_URL)]
        )

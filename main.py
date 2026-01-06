# main.py
import os
import sys
from datetime import datetime
import pytz
from NotionHelper import NotionHelper

# 设置时区为 台北/北京时间 (UTC+8)
# GitHub 默认为 UTC 时间，必须强制转换，否则你会发现“今天”是“昨天”
tz = pytz.timezone('Asia/Shanghai') 
today = datetime.now(tz)

print(f"开始执行自动化归档，当前时间: {today.strftime('%Y-%m-%d %H:%M:%S')}")

try:
    helper = NotionHelper()
    
    # 这一行代码是核心：
    # 它会自动计算今天属于哪一年、哪个月、哪一周
    # 如果对应的年/月/周页面不存在，它会自动创建
    # 最后，它会创建今天的日记页，并把上面那些关系全部关联好
    page_id = helper.get_day_relation_id(today)
    
    print(f"✅ 成功创建/获取今日页面，Page ID: {page_id}")
    
except Exception as e:
    print(f"❌ 执行失败: {e}")
    sys.exit(1)

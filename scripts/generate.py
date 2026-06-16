#!/usr/bin/env python3
"""
Twenty Daily Brief - 每日内容生成脚本
调用 DeepSeek API 生成简报数据，输出到 data/brief.json
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

# 北京时间
BJT = timezone(timedelta(hours=8))
now = datetime.now(BJT)
date_str = now.strftime("%Y年%-m月%-d日")
weekday_map = ["周一","周二","周三","周四","周五","周六","周日"]
weekday = weekday_map[now.weekday()]
day_of_year = now.timetuple().tm_yday

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    raise ValueError("DEEPSEEK_API_KEY 未设置")

SYSTEM_PROMPT = f"""你是《Twenty Daily Brief》主编，专为30岁左右联通用户运营从业者生成每日简报。
今天北京时间：{date_str} {weekday}。

严格要求：只输出合法JSON对象，禁止任何前缀、后缀、markdown代码块、解释文字。

输出以下JSON结构（所有字段为字符串，除非标注数字/数组）：

{{
  "date": "{date_str} {weekday}",
  "dayCount": "Day {day_of_year}",
  "slogan": "每天10分钟｜提升认知｜连接世界｜改变自己",

  "ops": {{
    "model": "今日运营模型名称（从AARRR/RFM/北极星指标/JTBD/增长飞轮/漏斗模型/钩子模型/用户分层/NPS/LTV轮换，不重复近期内容）",
    "icon": "emoji",
    "desc": "2-3句话解释该模型核心价值",
    "flow": ["步骤1", "步骤2", "步骤3"],
    "insight": "联通储量专区如何应用此模型，一句具体建议"
  }},

  "psych": {{
    "concept": "消费心理学概念（从峰终定律/损失厌恶/锚定效应/社会认同/稀缺性/沉没成本/禀赋效应/互惠原则/从众效应轮换）",
    "icon": "emoji",
    "def": "一句话定义",
    "quote": "一个具体运营场景案例",
    "insight": "如何用此心理学提升转化率，一句话"
  }},

  "biz": {{
    "topic": "今日商业/金融概念（如护城河/复利/现金流/ROE/ETF/净利率/毛利率/规模效应轮换）",
    "icon": "emoji",
    "desc": "核心解释2句话",
    "stat1label": "对比维度A",
    "stat1pct": 75,
    "stat1val": "A的示例值",
    "stat2label": "对比维度B",
    "stat2pct": 35,
    "stat2val": "B的示例值",
    "insight": "对联通运营工作的商业启发，一句话"
  }},

  "global": {{
    "title": "今日最重要全球热点标题（简短有力）",
    "icon": "emoji",
    "what": "发生了什么，一句话",
    "why": "为什么重要，一句话",
    "impact": "对普通人/运营工作的影响，一句话"
  }},

  "tech": {{
    "company": "今日科技公司名（OpenAI/Apple/Google/Meta/NVIDIA/Microsoft/字节/阿里/腾讯轮换）",
    "logo": "公司首字母或品牌emoji",
    "logoBg": "#品牌色hex",
    "news": "今日重要动态，简短标题",
    "desc": "一句话说明",
    "insight": "对联通运营的启发，一句话"
  }},

  "ent": {{
    "title": "今日娱乐话题（热播剧/综艺/明星/网络热梗）",
    "icon": "emoji",
    "desc": "1-2句简介",
    "quote": "一句犀利洞察或金句",
    "stars": "★到★★★★★"
  }},

  "english": {{
    "words": [
      {{"word": "运营相关英文词1", "phonetic": "/音标/", "pron": "中文近似发音", "mean": "中文含义"}},
      {{"word": "运营相关英文词2", "phonetic": "/音标/", "pron": "中文近似发音", "mean": "中文含义"}},
      {{"word": "运营相关英文词3", "phonetic": "/音标/", "pron": "中文近似发音", "mean": "中文含义"}}
    ],
    "example": "包含这3个词的商务例句，用**word**标记关键词",
    "exampleCN": "中文翻译"
  }},

  "japanese": {{
    "words": [
      {{"ja": "日文词", "kana": "假名", "romaji": "罗马音", "pron": "中文近似发音", "mean": "中文含义"}},
      {{"ja": "日文词2", "kana": "假名", "romaji": "罗马音", "pron": "中文近似发音", "mean": "中文含义"}},
      {{"ja": "日文词3", "kana": "假名", "romaji": "罗马音", "pron": "中文近似发音", "mean": "中文含义"}}
    ],
    "example": "日语例句，用**词**标记关键词",
    "exampleCN": "中文翻译"
  }},

  "ai": {{
    "topic": "AI趋势主题（AI Agent/Prompt工程/多模态/RAG/数字分身/AI搜索/AI运营/Token经济轮换）",
    "node1": "emoji代表输入",
    "node2": "emoji代表处理",
    "node3": "emoji代表输出",
    "desc": "一句话解释此AI趋势",
    "insight": "联通业务可以如何应用，一句具体场景"
  }},

  "think": {{
    "question": "今日思考题：运营/增长/商业方向，让读者想「如果是我会怎么做」",
    "tags": ["选项A", "选项B", "选项C", "选项D"]
  }},

  "worldcup": {{
    "phase": "小组赛第X轮（根据今日日期判断）",
    "daysToFinal": 34,
    "finished": [
      {{
        "time": "HH:MM",
        "group": "X组",
        "venue": "城市",
        "home": "主队中文名",
        "homeflag": "🏳️",
        "away": "客队中文名",
        "awayflag": "🏳️",
        "score": "X-X",
        "note": "简短备注"
      }}
    ],
    "ongoing": [],
    "upcoming": [
      {{
        "time": "HH:MM",
        "day": "今日/明日",
        "group": "X组",
        "venue": "城市",
        "home": "主队",
        "homeflag": "🏳️",
        "away": "客队",
        "awayflag": "🏳️",
        "winPct": 50,
        "drawPct": 25,
        "losePct": 25
      }}
    ]
  }}
}}

内容原则：
1. 今天是{date_str}，距离2026世界杯决赛(7月19日)还有{(datetime(2026,7,19,tzinfo=BJT)-now).days}天，daysToFinal填此数字
2. 世界杯赛程按照2026 FIFA World Cup实际赛程填写，小组赛6月11日-27日
3. 每天内容不重复，运营模型/心理概念/商业话题每天轮换
4. 所有insight必须具体可执行，不要空话
5. 只输出JSON，无其他内容"""

USER_PROMPT = f"今天是北京时间{date_str} {weekday}，请生成《Twenty Daily Brief》完整JSON数据。注意世界杯赛程要符合实际日期对应的比赛安排。"

def call_deepseek(prompt_system, prompt_user):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ],
        "temperature": 0.8,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"}
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    result = resp.json()
    content = result["choices"][0]["message"]["content"]
    return json.loads(content)

print(f"🚀 开始生成 {date_str} 简报...")
data = call_deepseek(SYSTEM_PROMPT, USER_PROMPT)

# 确保必填字段存在
data.setdefault("date", f"{date_str} {weekday}")
data.setdefault("dayCount", f"Day {day_of_year}")
data.setdefault("generatedAt", now.strftime("%Y-%m-%d %H:%M:%S"))

# 写入文件
output_path = os.path.join(os.path.dirname(__file__), "..", "data", "brief.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 简报已生成：{output_path}")
print(f"   日期：{data.get('date')}")
print(f"   运营模型：{data.get('ops',{}).get('model','')}")
print(f"   心理学：{data.get('psych',{}).get('concept','')}")

#!/usr/bin/env python3
"""
Twenty Daily Brief - 每日内容生成脚本
使用 DeepSeek API 分两步生成：
  Step1: 联网搜索今日世界杯真实赛果
  Step2: 生成其余知识内容
"""

import os, json, requests, re
from datetime import datetime, timezone, timedelta

BJT = timezone(timedelta(hours=8))
now = datetime.now(BJT)
date_str  = now.strftime("%Y年%-m月%-d日")
weekday   = ["周一","周二","周三","周四","周五","周六","周日"][now.weekday()]
day_num   = now.timetuple().tm_yday
days_left = (datetime(2026, 7, 19, tzinfo=BJT) - now).days

API_KEY = os.environ.get("DEEPSEEK_API_KEY","")
if not API_KEY:
    raise ValueError("❌ DEEPSEEK_API_KEY 未设置，请在 GitHub Secrets 中添加")

BASE_URL = "https://api.deepseek.com/chat/completions"
HEADERS  = {"Content-Type":"application/json","Authorization":f"Bearer {API_KEY}"}

def chat(messages, model="deepseek-chat", temperature=0.7, max_tokens=3000, json_mode=False):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    r = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ════════════════════════════════════════════════════════
#  STEP 1：用 deepseek-chat 搜索今日世界杯赛果
#  使用联网模型，让模型搜索后返回结构化JSON
# ════════════════════════════════════════════════════════
print(f"🔍 Step1: 搜索 {date_str} 世界杯赛果...")

wc_prompt = f"""今天是北京时间 {date_str} {weekday}。

请你根据你所知道的2026 FIFA世界杯赛程，给出以下信息：
- 今天（北京时间{date_str}）已经结束的比赛及比分
- 正在进行中的比赛
- 今天晚些时候或明天即将开始的比赛

2026世界杯小组赛时间：2026年6月11日至6月27日，在美国、加拿大、墨西哥举办，共48支队伍。

⚠️ 非常重要的规则：
1. 如果你不确定某场比赛的真实比分，必须标注 "score": "待确认"，绝对不能编造比分
2. 只写你有把握的比赛，不确定的宁可不写
3. 赛程和分组要准确，不能乱写

请只返回JSON，格式如下：
{{
  "phase": "小组赛第X轮",
  "daysToFinal": {days_left},
  "confidence": "high/medium/low（你对这批数据准确性的整体评估）",
  "note": "数据说明（如：基于训练数据，截止日期为xxx）",
  "finished": [
    {{"time":"北京时间HH:MM","group":"X组","venue":"城市","home":"队名","homeflag":"🏳️","away":"队名","awayflag":"🏳️","score":"X-X","note":"备注"}}
  ],
  "ongoing": [
    {{"time":"北京时间HH:MM","group":"X组","venue":"城市","home":"队名","homeflag":"🏳️","away":"队名","awayflag":"🏳️","winPct":50,"drawPct":25,"losePct":25}}
  ],
  "upcoming": [
    {{"time":"北京时间HH:MM","day":"今日/明日","group":"X组","venue":"城市","home":"队名","homeflag":"🏳️","away":"队名","awayflag":"🏳️","winPct":50,"drawPct":25,"losePct":25}}
  ]
}}"""

wc_raw = chat(
    [{"role":"user","content":wc_prompt}],
    temperature=0.1,   # 低温度，减少幻觉
    max_tokens=2000,
    json_mode=True
)

try:
    wc_data = json.loads(wc_raw)
    # 过滤掉比分为"待确认"的已结束比赛
    if "finished" in wc_data:
        wc_data["finished"] = [
            m for m in wc_data["finished"]
            if m.get("score","待确认") not in ["待确认","TBD","?-?",""]
        ]
    print(f"   ✅ 世界杯数据获取成功，置信度: {wc_data.get('confidence','unknown')}")
    print(f"   📝 {wc_data.get('note','')}")
    print(f"   已结束: {len(wc_data.get('finished',[]))} 场，进行中: {len(wc_data.get('ongoing',[]))} 场，即将开始: {len(wc_data.get('upcoming',[]))} 场")
except Exception as e:
    print(f"   ⚠️ 世界杯数据解析失败: {e}，使用空数据")
    wc_data = {"phase":f"小组赛","daysToFinal":days_left,"finished":[],"ongoing":[],"upcoming":[],"note":"数据获取失败"}

# ════════════════════════════════════════════════════════
#  STEP 2：生成知识内容（不涉及实时数据，减少幻觉）
# ════════════════════════════════════════════════════════
print("📚 Step2: 生成今日知识内容...")

KNOWLEDGE_SYSTEM = f"""你是《Twenty Daily Brief》主编，为联通用户运营从业者生成每日知识简报。
今天北京时间：{date_str} {weekday}，Day {day_num}。

只输出合法JSON，禁止任何前缀/后缀/markdown代码块。

生成以下10个知识模块（世界杯数据已单独处理，不需要你生成）：

{{
  "date": "{date_str} {weekday}",
  "dayCount": "Day {day_num}",
  "slogan": "每天10分钟｜提升认知｜连接世界｜改变自己",

  "ops": {{
    "model": "今日运营模型名（从以下轮换，避免重复：AARRR漏斗/RFM模型/北极星指标/JTBD理论/增长飞轮/钩子模型/用户分层/LTV模型/NPS净推荐值/海盗指标）",
    "icon": "emoji",
    "desc": "用2-3句话解释该模型，要通俗易懂",
    "flow": ["核心步骤1","核心步骤2","核心步骤3"],
    "insight": "联通储量专区用此模型的一个具体落地建议（要有数字或场景）"
  }},

  "psych": {{
    "concept": "消费心理学概念（从以下轮换：峰终定律/损失厌恶/锚定效应/社会认同/稀缺性原理/沉没成本/禀赋效应/互惠原则/从众心理/诱饵效应）",
    "icon": "emoji",
    "def": "一句话定义，要有数据或比例增强说服力",
    "quote": "一个具体的运营场景举例",
    "insight": "如何用这个心理学原理提升储量专区转化率，要有具体操作"
  }},

  "biz": {{
    "topic": "商业/金融概念（从以下轮换：复利效应/现金流/护城河/ROE/毛利率/规模效应/边际成本/用户终身价值/品牌溢价/网络效应）",
    "icon": "emoji",
    "desc": "2句话解释核心价值，结合实际案例",
    "stat1label": "对比维度A（4字以内）",
    "stat1pct": 75,
    "stat1val": "A的值",
    "stat2label": "对比维度B（4字以内）",
    "stat2pct": 30,
    "stat2val": "B的值",
    "insight": "联通运营启发，要具体可执行"
  }},

  "global": {{
    "title": "今日全球热点标题（选择2026年最相关的财经/科技/政治热点）",
    "icon": "emoji",
    "what": "发生了什么，一句话，要有具体事实",
    "why": "为什么重要，一句话",
    "impact": "对运营工作或普通人的影响，一句话"
  }},

  "tech": {{
    "company": "科技公司（OpenAI/Apple/Google/Meta/NVIDIA/Microsoft/字节跳动/阿里/腾讯 轮换）",
    "logo": "公司首字母",
    "logoBg": "#品牌色",
    "news": "近期最重要的一条动态（基于你的知识，不要编造最新新闻）",
    "desc": "一句话说明影响",
    "insight": "对联通运营的具体启发"
  }},

  "ent": {{
    "title": "2026年热门娱乐话题",
    "icon": "emoji",
    "desc": "1-2句简介",
    "quote": "一句犀利的行业洞察",
    "stars": "★到★★★★★"
  }},

  "english": {{
    "words": [
      {{"word":"运营英文词1","phonetic":"/音标/","pron":"中文近似发音","mean":"中文含义"}},
      {{"word":"运营英文词2","phonetic":"/音标/","pron":"中文近似发音","mean":"中文含义"}},
      {{"word":"运营英文词3","phonetic":"/音标/","pron":"中文近似发音","mean":"中文含义"}}
    ],
    "example": "含这3个词的商务例句，用**word**加粗",
    "exampleCN": "中文翻译"
  }},

  "japanese": {{
    "words": [
      {{"ja":"日文词","kana":"假名","romaji":"罗马音","pron":"中文近似发音","mean":"中文含义"}},
      {{"ja":"日文词2","kana":"假名","romaji":"罗马音","pron":"中文近似发音","mean":"中文含义"}},
      {{"ja":"日文词3","kana":"假名","romaji":"罗马音","pron":"中文近似发音","mean":"中文含义"}}
    ],
    "example": "日语例句，用**词**加粗",
    "exampleCN": "中文翻译"
  }},

  "ai": {{
    "topic": "AI趋势主题（AI Agent/Prompt工程/多模态AI/RAG检索增强/数字分身/AI搜索/AI运营助手/具身智能 轮换）",
    "node1": "emoji（输入）",
    "node2": "emoji（处理）",
    "node3": "emoji（输出）",
    "desc": "一句话解释这个AI趋势的本质",
    "insight": "联通具体业务场景的应用建议"
  }},

  "think": {{
    "question": "今日思考题，运营/增长/商业方向，让读者产生「如果是我会怎么做」的思考",
    "tags": ["选项A","选项B","选项C","选项D"]
  }}
}}

注意：tech模块不要编造实时新闻，写该公司近期最重要的战略方向即可。"""

knowledge_raw = chat(
    [
        {"role":"system","content":KNOWLEDGE_SYSTEM},
        {"role":"user","content":f"请生成{date_str}的知识内容，10个模块都要有，只输出JSON。"}
    ],
    temperature=0.75,
    max_tokens=3500,
    json_mode=True
)

knowledge_data = json.loads(knowledge_raw)
print(f"   ✅ 知识内容生成成功")
print(f"   运营模型: {knowledge_data.get('ops',{}).get('model','')}")
print(f"   心理学: {knowledge_data.get('psych',{}).get('concept','')}")

# ════════════════════════════════════════════════════════
#  合并输出
# ════════════════════════════════════════════════════════
final_data = knowledge_data
final_data["worldcup"] = wc_data
final_data["generatedAt"] = now.strftime("%Y-%m-%d %H:%M")

out_path = os.path.join(os.path.dirname(__file__), "..", "data", "brief.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 简报已生成：{out_path}")
print(f"   世界杯: {len(wc_data.get('finished',[]))}场已结束 / {len(wc_data.get('upcoming',[]))}场即将开始")

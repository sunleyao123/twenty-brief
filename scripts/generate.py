#!/usr/bin/env python3
"""
Twenty Daily Brief - 每日内容生成脚本 v3
- 世界杯：调用 football-data.org 免费API获取真实赛果
- 新闻：调用 NewsAPI 获取当日真实头条
- 防重复：读取 brief.json 历史记录，避免连续重复
"""

import os, json, requests
from datetime import datetime, timezone, timedelta

# ── 时间 ───────────────────────────────────────────────
BJT       = timezone(timedelta(hours=8))
now       = datetime.now(BJT)
date_str  = now.strftime("%Y年%-m月%-d日")
weekday   = ["周一","周二","周三","周四","周五","周六","周日"][now.weekday()]
day_num   = now.timetuple().tm_yday
days_left = max(0, (datetime(2026, 7, 19, tzinfo=BJT) - now).days)

# ── API Keys ───────────────────────────────────────────
DEEPSEEK_KEY  = os.environ.get("DEEPSEEK_API_KEY", "")
FOOTBALL_KEY  = os.environ.get("FOOTBALL_API_KEY", "")   # football-data.org 免费key
NEWS_KEY      = os.environ.get("NEWS_API_KEY", "")        # newsapi.org 免费key

if not DEEPSEEK_KEY:
    raise ValueError("❌ DEEPSEEK_API_KEY 未设置")

# ── DeepSeek 调用 ──────────────────────────────────────
def deepseek(system, user, temp=0.8, max_tokens=3500):
    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Content-Type":"application/json","Authorization":f"Bearer {DEEPSEEK_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role":"system","content":system},{"role":"user","content":user}],
            "temperature": temp,
            "max_tokens": max_tokens,
            "response_format": {"type":"json_object"}
        },
        timeout=120
    )
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])

# ═══════════════════════════════════════════════════════
#  STEP 0：读取历史记录（防重复）
# ═══════════════════════════════════════════════════════
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "brief.json")
HISTORY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "history.json")

# 读取历史已用话题
history = {"ops": [], "psych": [], "biz": [], "ai": []}
try:
    if os.path.exists(HISTORY_PATH):
        history = json.load(open(HISTORY_PATH, encoding="utf-8"))
except:
    pass

used_ops   = history.get("ops",   [])[-7:]   # 最近7天已用的运营模型
used_psych = history.get("psych", [])[-7:]
used_biz   = history.get("biz",   [])[-7:]
used_ai    = history.get("ai",    [])[-7:]

print(f"📋 历史记录：已用运营模型 {used_ops}")

# ═══════════════════════════════════════════════════════
#  STEP 1：获取真实世界杯赛果
# ═══════════════════════════════════════════════════════
print("⚽ Step1: 获取世界杯真实赛果...")

wc_data = {"phase":"小组赛", "daysToFinal": days_left, "finished":[], "ongoing":[], "upcoming":[]}

if FOOTBALL_KEY:
    try:
        # football-data.org API - 2026世界杯赛事代码 WC
        today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        headers_fd = {"X-Auth-Token": FOOTBALL_KEY}

        # 获取今日比赛
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/WC/matches",
            headers=headers_fd,
            params={"dateFrom": today_utc, "dateTo": today_utc},
            timeout=15
        )
        if r.status_code == 200:
            matches = r.json().get("matches", [])
            flag_map = {
                "Germany":"🇩🇪","Japan":"🇯🇵","Netherlands":"🇳🇱","Spain":"🇪🇸",
                "France":"🇫🇷","Brazil":"🇧🇷","Argentina":"🇦🇷","England":"🏴󠁧󠁢󠁥󠁮󠁧󠁿",
                "Portugal":"🇵🇹","Belgium":"🇧🇪","Uruguay":"🇺🇾","Mexico":"🇲🇽",
                "USA":"🇺🇸","Canada":"🇨🇦","Australia":"🇦🇺","South Korea":"🇰🇷",
                "Saudi Arabia":"🇸🇦","Morocco":"🇲🇦","Senegal":"🇸🇳","Ghana":"🇬🇭",
                "Iran":"🇮🇷","New Zealand":"🇳🇿","Sweden":"🇸🇪","Tunisia":"🇹🇳",
                "Ivory Coast":"🇨🇮","Ecuador":"🇪🇨","Curaçao":"🇨🇼","Cape Verde":"🇨🇻",
                "Egypt":"🇪🇬","Croatia":"🇭🇷","Serbia":"🇷🇸","Poland":"🇵🇱",
            }
            name_cn = {
                "Germany":"德国","Japan":"日本","Netherlands":"荷兰","Spain":"西班牙",
                "France":"法国","Brazil":"巴西","Argentina":"阿根廷","England":"英格兰",
                "Portugal":"葡萄牙","Belgium":"比利时","Uruguay":"乌拉圭","Mexico":"墨西哥",
                "USA":"美国","Canada":"加拿大","Australia":"澳大利亚","South Korea":"韩国",
                "Saudi Arabia":"沙特","Morocco":"摩洛哥","Senegal":"塞内加尔","Ghana":"加纳",
                "Iran":"伊朗","New Zealand":"新西兰","Sweden":"瑞典","Tunisia":"突尼斯",
                "Ivory Coast":"科特迪瓦","Ecuador":"厄瓜多尔","Curaçao":"库拉索","Cape Verde":"佛得角",
                "Egypt":"埃及","Croatia":"克罗地亚","Serbia":"塞尔维亚","Poland":"波兰",
            }
            for m in matches:
                kick_utc = datetime.fromisoformat(m["utcDate"].replace("Z","+00:00"))
                kick_bjt = kick_utc.astimezone(BJT)
                time_str = kick_bjt.strftime("%H:%M")
                home_en  = m["homeTeam"]["name"]
                away_en  = m["awayTeam"]["name"]
                home_cn  = name_cn.get(home_en, home_en)
                away_cn  = name_cn.get(away_en, away_en)
                home_fl  = flag_map.get(home_en, "🏳️")
                away_fl  = flag_map.get(away_en, "🏳️")
                group    = m.get("group","") or ""
                venue    = m.get("venue","") or ""
                status   = m["status"]
                score_h  = m["score"]["fullTime"]["home"]
                score_a  = m["score"]["fullTime"]["away"]

                if status in ("FINISHED",):
                    wc_data["finished"].append({
                        "time": time_str, "group": group, "venue": venue,
                        "home": home_cn, "homeflag": home_fl,
                        "away": away_cn, "awayflag": away_fl,
                        "score": f"{score_h}-{score_a}", "note": ""
                    })
                elif status in ("IN_PLAY","PAUSED","HALFTIME"):
                    wc_data["ongoing"].append({
                        "time": time_str, "group": group, "venue": venue,
                        "home": home_cn, "homeflag": home_fl,
                        "away": away_cn, "awayflag": away_fl,
                        "winPct":50,"drawPct":25,"losePct":25
                    })
                elif status in ("SCHEDULED","TIMED"):
                    wc_data["upcoming"].append({
                        "time": time_str, "day":"今日", "group": group, "venue": venue,
                        "home": home_cn, "homeflag": home_fl,
                        "away": away_cn, "awayflag": away_fl,
                        "winPct":50,"drawPct":25,"losePct":25
                    })
            wc_data["phase"] = "小组赛"
            print(f"   ✅ 足球API获取成功: {len(wc_data['finished'])}场已结束, {len(wc_data['upcoming'])}场待开球")
        else:
            print(f"   ⚠️ 足球API返回 {r.status_code}")
    except Exception as e:
        print(f"   ⚠️ 足球API异常: {e}")
else:
    print("   ℹ️ 未配置 FOOTBALL_API_KEY，世界杯显示为空")

# ═══════════════════════════════════════════════════════
#  STEP 2：获取真实新闻（NewsAPI）
# ═══════════════════════════════════════════════════════
print("📰 Step2: 获取真实新闻...")

real_news_global = ""
real_news_tech   = ""

if NEWS_KEY:
    try:
        today_str_news = now.strftime("%Y-%m-%d")
        # 全球财经/政治新闻（中文）
        r = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"category":"business","language":"zh","pageSize":3,"apiKey":NEWS_KEY},
            timeout=10
        )
        if r.status_code == 200:
            articles = r.json().get("articles",[])
            if articles:
                a = articles[0]
                real_news_global = f"标题：{a['title']}\n来源：{a.get('source',{}).get('name','')}\n摘要：{a.get('description','')}"
                print(f"   ✅ 全球新闻: {a['title'][:40]}")

        # 科技新闻（英文）
        r2 = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"category":"technology","language":"en","pageSize":3,"apiKey":NEWS_KEY},
            timeout=10
        )
        if r2.status_code == 200:
            arts2 = r2.json().get("articles",[])
            if arts2:
                a2 = arts2[0]
                real_news_tech = f"Title: {a2['title']}\nSource: {a2.get('source',{}).get('name','')}\nDesc: {a2.get('description','')}"
                print(f"   ✅ 科技新闻: {a2['title'][:40]}")
    except Exception as e:
        print(f"   ⚠️ NewsAPI异常: {e}")
else:
    print("   ℹ️ 未配置 NEWS_API_KEY，新闻由AI生成（可能非实时）")

# ═══════════════════════════════════════════════════════
#  STEP 3：DeepSeek 生成知识内容（带防重复约束）
# ═══════════════════════════════════════════════════════
print("📚 Step3: DeepSeek 生成知识内容...")

# 构建防重复约束
ops_list   = ["AARRR漏斗","RFM模型","北极星指标","JTBD理论","增长飞轮","钩子模型","用户分层模型","LTV计算","NPS净推荐值","海盗指标AAARR","用户生命周期","漏斗转化优化"]
psych_list = ["峰终定律","损失厌恶","锚定效应","社会认同","稀缺性原理","沉没成本","禀赋效应","互惠原则","从众心理","诱饵效应","心理账户","禀赋效应"]
biz_list   = ["复利效应","现金流管理","护城河","ROE净资产收益率","毛利率","规模效应","边际成本","用户终身价值LTV","品牌溢价","网络效应","定价策略","损益表解读"]
ai_list    = ["AI Agent自主代理","Prompt工程","多模态AI","RAG检索增强","数字分身","AI搜索","AI运营助手","具身智能","Fine-tuning微调","向量数据库","MCP协议","AI工作流"]

# 从候选中排除最近7天已用的
avail_ops   = [x for x in ops_list   if x not in used_ops]   or ops_list
avail_psych = [x for x in psych_list if x not in used_psych] or psych_list
avail_biz   = [x for x in biz_list   if x not in used_biz]   or biz_list
avail_ai    = [x for x in ai_list    if x not in used_ai]     or ai_list

news_global_instruction = f"""
【今日真实全球新闻参考，请基于此写global模块】
{real_news_global if real_news_global else "（无实时新闻，请基于2026年重要财经/地缘事件生成，要具体，不要太宽泛）"}
""".strip()

news_tech_instruction = f"""
【今日真实科技新闻参考，请基于此写tech模块】
{real_news_tech if real_news_tech else "（无实时新闻，请选择OpenAI/Apple/Google/Meta/NVIDIA/Microsoft/字节/阿里/腾讯中一家，写其2026年最重要的一个具体动态）"}
""".strip()

SYSTEM = f"""你是《Twenty Daily Brief》主编，为联通用户运营从业者生成每日知识简报。
今天北京时间：{date_str} {weekday}，Day {day_num}。
只输出合法JSON对象，禁止markdown代码块、前缀、后缀。

{news_global_instruction}

{news_tech_instruction}

⚠️ 防重复规则（最近7天已用，今天必须选其他的）：
- 运营模型 已用过：{used_ops}，今天必须从以下选一个：{avail_ops}
- 心理学概念 已用过：{used_psych}，今天必须从以下选一个：{avail_psych}
- 商业概念 已用过：{used_biz}，今天必须从以下选一个：{avail_biz}
- AI趋势 已用过：{used_ai}，今天必须从以下选一个：{avail_ai}

输出以下JSON结构：
{{
  "date": "{date_str} {weekday}",
  "dayCount": "Day {day_num}",
  "slogan": "每天10分钟｜提升认知｜连接世界｜改变自己",
  "ops": {{
    "model": "【必须从可选列表选】{avail_ops[0]}",
    "icon": "emoji",
    "desc": "2-3句通俗解释",
    "flow": ["步骤1","步骤2","步骤3"],
    "insight": "联通储量专区具体落地建议，含场景或数字"
  }},
  "psych": {{
    "concept": "【必须从可选列表选】{avail_psych[0]}",
    "icon": "emoji",
    "def": "一句话定义，含数据或比例",
    "quote": "具体运营场景举例",
    "insight": "提升储量专区转化率的具体操作"
  }},
  "biz": {{
    "topic": "【必须从可选列表选】{avail_biz[0]}",
    "icon": "emoji",
    "desc": "2句话解释，结合实际案例",
    "stat1label": "维度A（4字内）",
    "stat1pct": 75,
    "stat1val": "值",
    "stat2label": "维度B（4字内）",
    "stat2pct": 35,
    "stat2val": "值",
    "insight": "联通运营具体可执行启发"
  }},
  "global": {{
    "title": "基于上方真实新闻提炼的标题",
    "icon": "emoji",
    "what": "发生了什么，一句话，要有具体事实",
    "why": "为什么重要，一句话",
    "impact": "对运营工作或普通人的影响"
  }},
  "tech": {{
    "company": "基于上方真实科技新闻的公司名",
    "logo": "首字母",
    "logoBg": "#品牌色hex",
    "news": "基于真实新闻的标题（不要编造）",
    "desc": "一句话说明",
    "insight": "对联通运营的启发"
  }},
  "ent": {{
    "title": "2026年当下热门娱乐话题（影视/综艺/体育/网络热点）",
    "icon": "emoji",
    "desc": "1-2句简介",
    "quote": "一句犀利洞察",
    "stars": "★★★★☆"
  }},
  "english": {{
    "words": [
      {{"word":"运营词1","phonetic":"/音标/","pron":"中文近似发音","mean":"中文含义"}},
      {{"word":"运营词2","phonetic":"/音标/","pron":"中文近似发音","mean":"中文含义"}},
      {{"word":"运营词3","phonetic":"/音标/","pron":"中文近似发音","mean":"中文含义"}}
    ],
    "example": "含这3词的商务例句，**加粗**关键词",
    "exampleCN": "中文翻译"
  }},
  "japanese": {{
    "words": [
      {{"ja":"日文词","kana":"假名","romaji":"罗马音","pron":"中文近似发音","mean":"含义"}},
      {{"ja":"日文词2","kana":"假名","romaji":"罗马音","pron":"中文近似发音","mean":"含义"}},
      {{"ja":"日文词3","kana":"假名","romaji":"罗马音","pron":"中文近似发音","mean":"含义"}}
    ],
    "example": "日语例句，**加粗**关键词",
    "exampleCN": "中文翻译"
  }},
  "ai": {{
    "topic": "【必须从可选列表选】{avail_ai[0]}",
    "node1": "emoji",
    "node2": "emoji",
    "node3": "emoji",
    "desc": "一句话解释本质",
    "insight": "联通具体业务应用场景"
  }},
  "think": {{
    "question": "今日思考题，运营/增长/商业方向，让读者想「如果是我怎么做」",
    "tags": ["选项A","选项B","选项C","选项D"]
  }}
}}"""

data = deepseek(SYSTEM, f"请严格按要求生成{date_str}的简报JSON，注意防重复规则和使用真实新闻。", temp=0.85)
print(f"   ✅ 运营模型: {data.get('ops',{}).get('model','')}")
print(f"   ✅ 心理学: {data.get('psych',{}).get('concept','')}")
print(f"   ✅ 商业: {data.get('biz',{}).get('topic','')}")
print(f"   ✅ AI趋势: {data.get('ai',{}).get('topic','')}")

# ═══════════════════════════════════════════════════════
#  STEP 4：合并 & 输出
# ═══════════════════════════════════════════════════════
data["worldcup"]    = wc_data
data["generatedAt"] = now.strftime("%Y-%m-%d %H:%M")

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n✅ brief.json 已保存")

# 更新历史记录（防重复用）
history["ops"]   = (history.get("ops",  []) + [data["ops"]["model"]])[-14:]
history["psych"] = (history.get("psych",[]) + [data["psych"]["concept"]])[-14:]
history["biz"]   = (history.get("biz",  []) + [data["biz"]["topic"]])[-14:]
history["ai"]    = (history.get("ai",   []) + [data["ai"]["topic"]])[-14:]

hist_path = os.path.join(os.path.dirname(__file__), "..", "data", "history.json")
with open(hist_path, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
print("✅ history.json 已更新（防重复记录）")

#!/usr/bin/env python3
"""
Twenty Daily Brief - 每日内容生成脚本 v4
修复：
1. 新闻加时间校验，只接受36小时内的真实新闻，并展示发布时间
2. 世界杯重构：今日已完赛显示比分，未完赛只显示队伍（不猜比分）
3. 球队名全部中文化（扩充48强队伍映射表）
4. 新增明日赛程 + AI预测胜率
5. 统一北京时间
"""

import os, json, requests
from datetime import datetime, timezone, timedelta

# ── 时间 ───────────────────────────────────────────────
BJT       = timezone(timedelta(hours=8))
now       = datetime.now(BJT)
today_bjt = now.date()
tomorrow_bjt = today_bjt + timedelta(days=1)
date_str  = now.strftime("%Y年%-m月%-d日")
weekday   = ["周一","周二","周三","周四","周五","周六","周日"][now.weekday()]
day_num   = now.timetuple().tm_yday
days_left = max(0, (datetime(2026, 7, 19, tzinfo=BJT) - now).days)

# ── API Keys ───────────────────────────────────────────
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
FOOTBALL_KEY = os.environ.get("FOOTBALL_API_KEY", "")
NEWS_KEY     = os.environ.get("NEWS_API_KEY", "")

if not DEEPSEEK_KEY:
    raise ValueError("❌ DEEPSEEK_API_KEY 未设置")

def deepseek(system, user, temp=0.8, max_tokens=3500):
    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Content-Type":"application/json","Authorization":f"Bearer {DEEPSEEK_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role":"system","content":system},{"role":"user","content":user}],
            "temperature": temp, "max_tokens": max_tokens,
            "response_format": {"type":"json_object"}
        },
        timeout=120
    )
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])

# ═══════════════════════════════════════════════════════
#  STEP 0：读取历史记录（防重复）
# ═══════════════════════════════════════════════════════
DATA_PATH    = os.path.join(os.path.dirname(__file__), "..", "data", "brief.json")
HISTORY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "history.json")

history = {"ops": [], "psych": [], "biz": [], "ai": []}
try:
    if os.path.exists(HISTORY_PATH):
        history = json.load(open(HISTORY_PATH, encoding="utf-8"))
except: pass

used_ops   = history.get("ops",   [])[-7:]
used_psych = history.get("psych", [])[-7:]
used_biz   = history.get("biz",   [])[-7:]
used_ai    = history.get("ai",    [])[-7:]

# ═══════════════════════════════════════════════════════
#  STEP 1：世界杯真实赛果（football-data.org）
#  规则：今日已完赛→显示比分；今日未完赛→只显示队伍；
#        明日比赛→显示队伍+AI预测胜率
# ═══════════════════════════════════════════════════════
print("⚽ Step1: 获取世界杯赛果...")

# 48强球队中英文对照表（尽量覆盖2026世界杯所有可能参赛队）
TEAM_CN = {
    "Mexico":"墨西哥","Canada":"加拿大","United States":"美国","USA":"美国",
    "Germany":"德国","France":"法国","Brazil":"巴西","Argentina":"阿根廷",
    "England":"英格兰","Spain":"西班牙","Portugal":"葡萄牙","Netherlands":"荷兰",
    "Belgium":"比利时","Italy":"意大利","Croatia":"克罗地亚","Switzerland":"瑞士",
    "Denmark":"丹麦","Sweden":"瑞典","Norway":"挪威","Poland":"波兰",
    "Serbia":"塞尔维亚","Austria":"奥地利","Ukraine":"乌克兰","Wales":"威尔士",
    "Scotland":"苏格兰","Turkey":"土耳其","Türkiye":"土耳其","Greece":"希腊",
    "Czech Republic":"捷克","Slovakia":"斯洛伐克","Slovenia":"斯洛文尼亚",
    "Hungary":"匈牙利","Romania":"罗马尼亚","Finland":"芬兰","Iceland":"冰岛",
    "Ireland":"爱尔兰","Republic of Ireland":"爱尔兰","Russia":"俄罗斯",
    "Uruguay":"乌拉圭","Colombia":"哥伦比亚","Chile":"智利","Peru":"秘鲁",
    "Ecuador":"厄瓜多尔","Paraguay":"巴拉圭","Bolivia":"玻利维亚","Venezuela":"委内瑞拉",
    "Japan":"日本","South Korea":"韩国","Korea Republic":"韩国","Australia":"澳大利亚",
    "Saudi Arabia":"沙特","Iran":"伊朗","Qatar":"卡塔尔","Iraq":"伊拉克",
    "United Arab Emirates":"阿联酋","Uzbekistan":"乌兹别克斯坦","Jordan":"约旦",
    "China":"中国","China PR":"中国","Indonesia":"印度尼西亚","India":"印度",
    "Morocco":"摩洛哥","Senegal":"塞内加尔","Tunisia":"突尼斯","Algeria":"阿尔及利亚",
    "Egypt":"埃及","Nigeria":"尼日利亚","Ghana":"加纳","Cameroon":"喀麦隆",
    "Ivory Coast":"科特迪瓦","Côte d'Ivoire":"科特迪瓦","South Africa":"南非",
    "Mali":"马里","DR Congo":"刚果民主共和国","Cape Verde":"佛得角",
    "Gabon":"加蓬","Benin":"贝宁","Jamaica":"牙买加","Panama":"巴拿马",
    "Costa Rica":"哥斯达黎加","Honduras":"洪都拉斯","Curacao":"库拉索","Curaçao":"库拉索",
    "Haiti":"海地","Suriname":"苏里南","New Zealand":"新西兰","New Caledonia":"新喀里多尼亚",
    "Fiji":"斐济",
}
TEAM_FLAG = {
    "墨西哥":"🇲🇽","加拿大":"🇨🇦","美国":"🇺🇸","德国":"🇩🇪","法国":"🇫🇷","巴西":"🇧🇷",
    "阿根廷":"🇦🇷","英格兰":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","西班牙":"🇪🇸","葡萄牙":"🇵🇹","荷兰":"🇳🇱","比利时":"🇧🇪",
    "意大利":"🇮🇹","克罗地亚":"🇭🇷","瑞士":"🇨🇭","丹麦":"🇩🇰","瑞典":"🇸🇪","挪威":"🇳🇴",
    "波兰":"🇵🇱","塞尔维亚":"🇷🇸","奥地利":"🇦🇹","乌克兰":"🇺🇦","威尔士":"🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "苏格兰":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","土耳其":"🇹🇷","希腊":"🇬🇷","捷克":"🇨🇿","斯洛伐克":"🇸🇰",
    "斯洛文尼亚":"🇸🇮","匈牙利":"🇭🇺","罗马尼亚":"🇷🇴","芬兰":"🇫🇮","冰岛":"🇮🇸",
    "爱尔兰":"🇮🇪","俄罗斯":"🇷🇺","乌拉圭":"🇺🇾","哥伦比亚":"🇨🇴","智利":"🇨🇱",
    "秘鲁":"🇵🇪","厄瓜多尔":"🇪🇨","巴拉圭":"🇵🇾","玻利维亚":"🇧🇴","委内瑞拉":"🇻🇪",
    "日本":"🇯🇵","韩国":"🇰🇷","澳大利亚":"🇦🇺","沙特":"🇸🇦","伊朗":"🇮🇷","卡塔尔":"🇶🇦",
    "伊拉克":"🇮🇶","阿联酋":"🇦🇪","乌兹别克斯坦":"🇺🇿","约旦":"🇯🇴","中国":"🇨🇳",
    "印度尼西亚":"🇮🇩","印度":"🇮🇳","摩洛哥":"🇲🇦","塞内加尔":"🇸🇳","突尼斯":"🇹🇳",
    "阿尔及利亚":"🇩🇿","埃及":"🇪🇬","尼日利亚":"🇳🇬","加纳":"🇬🇭","喀麦隆":"🇨🇲",
    "科特迪瓦":"🇨🇮","南非":"🇿🇦","马里":"🇲🇱","刚果民主共和国":"🇨🇩","佛得角":"🇨🇻",
    "加蓬":"🇬🇦","贝宁":"🇧🇯","牙买加":"🇯🇲","巴拿马":"🇵🇦","哥斯达黎加":"🇨🇷",
    "洪都拉斯":"🇭🇳","库拉索":"🇨🇼","海地":"🇭🇹","苏里南":"🇸🇷","新西兰":"🇳🇿",
    "新喀里多尼亚":"🇳🇨","斐济":"🇫🇯",
}

def to_cn(name_en):
    return TEAM_CN.get(name_en, name_en)

def to_flag(name_cn):
    return TEAM_FLAG.get(name_cn, "🏳️")

wc_data = {
    "phase": "小组赛",
    "daysToFinal": days_left,
    "todayDate": now.strftime("%-m月%-d日"),
    "tomorrowDate": (now + timedelta(days=1)).strftime("%-m月%-d日"),
    "finished": [],       # 今日已完赛
    "todayScheduled": [], # 今日未完赛（只显示队伍）
    "tomorrow": []        # 明日赛程+预测
}

if FOOTBALL_KEY:
    try:
        headers_fd = {"X-Auth-Token": FOOTBALL_KEY}
        # 用较宽的UTC时间范围查询，再按北京时间精确分类
        date_from = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        date_to   = (now + timedelta(days=2)).strftime("%Y-%m-%d")

        r = requests.get(
            "https://api.football-data.org/v4/competitions/WC/matches",
            headers=headers_fd,
            params={"dateFrom": date_from, "dateTo": date_to},
            timeout=15
        )

        if r.status_code == 200:
            matches = r.json().get("matches", [])
            print(f"   📦 API返回 {len(matches)} 场比赛（{date_from} ~ {date_to} UTC）")

            for m in matches:
                kick_utc = datetime.fromisoformat(m["utcDate"].replace("Z","+00:00"))
                kick_bjt = kick_utc.astimezone(BJT)
                match_date_bjt = kick_bjt.date()

                home_cn = to_cn(m["homeTeam"]["name"])
                away_cn = to_cn(m["awayTeam"]["name"])
                home_fl = to_flag(home_cn)
                away_fl = to_flag(away_cn)
                group   = (m.get("group") or "").replace("Group ","")
                venue   = m.get("venue") or ""
                status  = m["status"]
                score_h = m["score"]["fullTime"]["home"]
                score_a = m["score"]["fullTime"]["away"]
                time_str = kick_bjt.strftime("%H:%M")

                base = {
                    "time": time_str, "group": f"{group}组" if group else "",
                    "venue": venue, "home": home_cn, "homeflag": home_fl,
                    "away": away_cn, "awayflag": away_fl
                }

                # ── 今天的比赛 ──
                if match_date_bjt == today_bjt:
                    if status == "FINISHED":
                        wc_data["finished"].append({**base, "score": f"{score_h}-{score_a}"})
                    else:
                        # 未完赛：只显示队伍，不猜比分
                        wc_data["todayScheduled"].append(base)

                # ── 明天的比赛：显示队伍，后续补充AI预测 ──
                elif match_date_bjt == tomorrow_bjt:
                    wc_data["tomorrow"].append(base)

            print(f"   ✅ 今日已完赛: {len(wc_data['finished'])}场")
            print(f"   ✅ 今日未完赛: {len(wc_data['todayScheduled'])}场")
            print(f"   ✅ 明日赛程: {len(wc_data['tomorrow'])}场")
        else:
            print(f"   ⚠️ 足球API返回状态码 {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"   ⚠️ 足球API异常: {e}")
else:
    print("   ℹ️ 未配置 FOOTBALL_API_KEY")

# ── 给明日比赛加 AI 预测胜率（仅对明日比赛，不涉及比分编造） ──
if wc_data["tomorrow"]:
    print("🔮 为明日赛程生成AI预测胜率...")
    matches_desc = "\n".join([f"{i+1}. {m['home']} vs {m['away']}（{m['group']}）" for i,m in enumerate(wc_data["tomorrow"])])
    predict_prompt = f"""以下是明天的世界杯比赛对阵：
{matches_desc}

请基于球队历史实力、近期状态等因素，给出每场比赛的胜平负预测百分比（三者相加=100）。
只返回JSON数组，顺序与上面一致：
{{"predictions":[{{"winPct":50,"drawPct":25,"losePct":25}}, ...]}}"""
    try:
        pred = deepseek("你是足球数据分析师，给出合理的胜率预测。", predict_prompt, temp=0.3, max_tokens=800)
        preds = pred.get("predictions", [])
        for i, m in enumerate(wc_data["tomorrow"]):
            if i < len(preds):
                m["winPct"]  = preds[i].get("winPct", 40)
                m["drawPct"] = preds[i].get("drawPct", 30)
                m["losePct"] = preds[i].get("losePct", 30)
            else:
                m["winPct"], m["drawPct"], m["losePct"] = 40, 30, 30
        print(f"   ✅ 预测完成")
    except Exception as e:
        print(f"   ⚠️ 预测生成失败: {e}")
        for m in wc_data["tomorrow"]:
            m["winPct"], m["drawPct"], m["losePct"] = 40, 30, 30

# ═══════════════════════════════════════════════════════
#  STEP 2：获取真实新闻（带时间校验）
# ═══════════════════════════════════════════════════════
print("📰 Step2: 获取真实新闻（带时效校验）...")

FRESHNESS_HOURS = 36  # 只接受36小时内的新闻

def fetch_fresh_news(category, language, max_age_hours=FRESHNESS_HOURS):
    """获取新闻并校验时效性，返回 (新闻字典 or None)"""
    if not NEWS_KEY:
        return None
    try:
        r = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"category":category, "language":language, "pageSize":10, "apiKey":NEWS_KEY},
            timeout=10
        )
        if r.status_code != 200:
            print(f"   ⚠️ NewsAPI({category}/{language}) 状态码 {r.status_code}")
            return None

        articles = r.json().get("articles", [])
        now_utc = datetime.now(timezone.utc)

        for a in articles:
            pub_str = a.get("publishedAt", "")
            if not pub_str:
                continue
            try:
                pub_time = datetime.fromisoformat(pub_str.replace("Z","+00:00"))
            except:
                continue
            age_hours = (now_utc - pub_time).total_seconds() / 3600

            if age_hours <= max_age_hours and a.get("title") and a.get("description"):
                pub_bjt = pub_time.astimezone(BJT)
                return {
                    "title": a["title"],
                    "desc": a.get("description",""),
                    "source": a.get("source",{}).get("name",""),
                    "publishedAt": pub_bjt.strftime("%-m月%-d日 %H:%M"),
                    "ageHours": round(age_hours,1)
                }
        print(f"   ⚠️ {category}/{language}: 所有新闻均超过{max_age_hours}小时，跳过")
        return None
    except Exception as e:
        print(f"   ⚠️ NewsAPI({category}) 异常: {e}")
        return None

news_global = fetch_fresh_news("business", "zh")
news_tech   = fetch_fresh_news("technology", "en")

if news_global:
    print(f"   ✅ 全球新闻: {news_global['title'][:40]} ({news_global['publishedAt']}, {news_global['ageHours']}h前)")
else:
    print("   ℹ️ 无符合时效要求的全球新闻，将由AI基于近期事件生成")

if news_tech:
    print(f"   ✅ 科技新闻: {news_tech['title'][:40]} ({news_tech['publishedAt']}, {news_tech['ageHours']}h前)")
else:
    print("   ℹ️ 无符合时效要求的科技新闻，将由AI基于近期事件生成")

# ═══════════════════════════════════════════════════════
#  STEP 3：DeepSeek 生成知识内容
# ═══════════════════════════════════════════════════════
print("📚 Step3: 生成知识内容...")

ops_list   = ["AARRR漏斗","RFM模型","北极星指标","JTBD理论","增长飞轮","钩子模型","用户分层模型","LTV计算","NPS净推荐值","海盗指标AAARR","用户生命周期","漏斗转化优化"]
psych_list = ["峰终定律","损失厌恶","锚定效应","社会认同","稀缺性原理","沉没成本","禀赋效应","互惠原则","从众心理","诱饵效应","心理账户","目标趋近效应"]
biz_list   = ["复利效应","现金流管理","护城河","ROE净资产收益率","毛利率","规模效应","边际成本","用户终身价值LTV","品牌溢价","网络效应","定价策略","损益表解读"]
ai_list    = ["AI Agent自主代理","Prompt工程","多模态AI","RAG检索增强","数字分身","AI搜索","AI运营助手","具身智能","Fine-tuning微调","向量数据库","MCP协议","AI工作流自动化"]

avail_ops   = [x for x in ops_list   if x not in used_ops]   or ops_list
avail_psych = [x for x in psych_list if x not in used_psych] or psych_list
avail_biz   = [x for x in biz_list   if x not in used_biz]   or biz_list
avail_ai    = [x for x in ai_list    if x not in used_ai]     or ai_list

if news_global:
    global_block = f"""【今日真实新闻 - 发布于{news_global['publishedAt']}（{news_global['ageHours']}小时前），来源：{news_global['source']}】
标题：{news_global['title']}
摘要：{news_global['desc']}
请基于此真实新闻撰写global模块，不要编造其他内容。"""
else:
    global_block = "（无可用实时新闻）请基于2026年当下真实存在的重要财经/地缘事件生成，要具体明确，避免泛泛而谈。"

if news_tech:
    tech_block = f"""【今日真实科技新闻 - 发布于{news_tech['publishedAt']}（{news_tech['ageHours']}小时前），来源：{news_tech['source']}】
Title: {news_tech['title']}
Desc: {news_tech['desc']}
请基于此真实新闻撰写tech模块（翻译为中文），不要编造其他内容。"""
else:
    tech_block = "（无可用实时新闻）请选择一家科技巨头，写其2026年真实存在的重要战略动态，避免泛泛而谈。"

SYSTEM = f"""你是《Twenty Daily Brief》主编，为联通用户运营从业者生成每日知识简报。
今天北京时间：{date_str} {weekday}，Day {day_num}。
只输出合法JSON，禁止markdown代码块。

【全球热点素材】
{global_block}

【科技动态素材】
{tech_block}

⚠️防重复：
- 运营模型不能用：{used_ops}，请选：{avail_ops[0]}
- 心理学不能用：{used_psych}，请选：{avail_psych[0]}
- 商业概念不能用：{used_biz}，请选：{avail_biz[0]}
- AI趋势不能用：{used_ai}，请选：{avail_ai[0]}

输出JSON结构：
{{
  "date": "{date_str} {weekday}",
  "dayCount": "Day {day_num}",
  "slogan": "每天10分钟｜提升认知｜连接世界｜改变自己",
  "ops": {{"model":"{avail_ops[0]}","icon":"emoji","desc":"2-3句解释","flow":["步骤1","步骤2","步骤3"],"insight":"联通储量专区具体建议"}},
  "psych": {{"concept":"{avail_psych[0]}","icon":"emoji","def":"一句话定义","quote":"运营场景举例","insight":"提升转化率的具体操作"}},
  "biz": {{"topic":"{avail_biz[0]}","icon":"emoji","desc":"2句话解释","stat1label":"维度A","stat1pct":75,"stat1val":"值","stat2label":"维度B","stat2pct":35,"stat2val":"值","insight":"运营启发"}},
  "global": {{"title":"基于真实新闻的标题","icon":"emoji","what":"发生了什么","why":"为什么重要","impact":"对普通人影响","newsTime":"{news_global['publishedAt'] if news_global else ''}","newsSource":"{news_global['source'] if news_global else ''}"}},
  "tech": {{"company":"公司名","logo":"首字母","logoBg":"#hex色","news":"基于真实新闻的标题","desc":"一句话说明","insight":"对联通运营启发","newsTime":"{news_tech['publishedAt'] if news_tech else ''}","newsSource":"{news_tech['source'] if news_tech else ''}"}},
  "ent": {{"title":"2026年热门娱乐话题","icon":"emoji","desc":"1-2句简介","quote":"一句洞察","stars":"★★★★☆"}},
  "english": {{"words":[{{"word":"词1","phonetic":"/音标/","pron":"中文发音","mean":"含义"}},{{"word":"词2","phonetic":"/音标/","pron":"中文发音","mean":"含义"}},{{"word":"词3","phonetic":"/音标/","pron":"中文发音","mean":"含义"}}],"example":"含3词的例句**加粗**","exampleCN":"翻译"}},
  "japanese": {{"words":[{{"ja":"词1","kana":"假名","romaji":"罗马音","pron":"中文发音","mean":"含义"}},{{"ja":"词2","kana":"假名","romaji":"罗马音","pron":"中文发音","mean":"含义"}},{{"ja":"词3","kana":"假名","romaji":"罗马音","pron":"中文发音","mean":"含义"}}],"example":"日语例句**加粗**","exampleCN":"翻译"}},
  "ai": {{"topic":"{avail_ai[0]}","node1":"emoji","node2":"emoji","node3":"emoji","desc":"一句话本质","insight":"联通应用场景"}},
  "think": {{"question":"今日思考题","tags":["选项A","选项B","选项C","选项D"]}}
}}"""

data = deepseek(SYSTEM, f"生成{date_str}简报JSON，严格遵守防重复和真实新闻要求。", temp=0.85)
print(f"   ✅ 运营:{data['ops']['model']} 心理:{data['psych']['concept']} 商业:{data['biz']['topic']} AI:{data['ai']['topic']}")

# ═══════════════════════════════════════════════════════
#  合并输出
# ═══════════════════════════════════════════════════════
data["worldcup"]    = wc_data
data["generatedAt"] = now.strftime("%Y-%m-%d %H:%M")

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n✅ brief.json 已保存")

history["ops"]   = (history.get("ops",  []) + [data["ops"]["model"]])[-14:]
history["psych"] = (history.get("psych",[]) + [data["psych"]["concept"]])[-14:]
history["biz"]   = (history.get("biz",  []) + [data["biz"]["topic"]])[-14:]
history["ai"]    = (history.get("ai",   []) + [data["ai"]["topic"]])[-14:]
with open(HISTORY_PATH, "w", encoding="utf-8") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
print("✅ history.json 已更新")

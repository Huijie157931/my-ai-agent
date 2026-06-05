import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, datetime, timedelta
import yfinance as yf
import google.generativeai as genai
import requests
import feedparser
from io import StringIO
import streamlit.components.v1 as components
import time, re

# ---------- 初始化 ----------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="Personal AI Agent", page_icon="🤖", layout="wide")
st.title("🤖 Personal AI Assistant – Full Demo")
today_date = date.today().strftime("%B %d, %Y")
st.caption(f"📅 {today_date}")

task = st.sidebar.selectbox(
    "Choose a task",
    [
        "Task 1: German News Sentence",
        "Task 2: Stock Indices",
        "Task 3: STM Industry News",
        "Task 4: Global Frontiers Update",
        "Task 5: Tech Trends & Podcast",
        "Task 6: Daily Check-in & Dashboard",
    ],
)

# ==================== TASK 1 ====================
if task.startswith("Task 1"):
    st.subheader("📰 Today’s German Learning Sentence")
    st.caption(f"Based on news of {today_date}")
    if st.button("Generate Sentence"):
        with st.spinner("Generating..."):
            try:
                prompt = (
                    f"Today is {today_date}. Based on today's real-world news, generate: "
                    "1) A single German sentence at A2 level. "
                    "2) Its accurate English translation. "
                    "3) A list of 3-5 key German words from the sentence, each with its English meaning and a short example phrase. Format as 'Word (part of speech): meaning | Example: ...' "
                    "4) One brief grammar explanation (in English) that highlights a structure used in the sentence. "
                    "Format your response exactly as follows, do not add any other text:\n\n"
                    "German: <sentence>\n"
                    "English: <translation>\n"
                    "Vocabulary:\n"
                    "- <Word1 (pos)>: <meaning> | Example: <example>\n"
                    "- <Word2 (pos)>: <meaning> | Example: <example>\n"
                    "...\n"
                    "Grammar: <explanation>"
                )
                response = model.generate_content(prompt)
                text = response.text
                lines = text.split("\n")
                german = english = grammar = ""
                vocab = []
                mode = None
                for line in lines:
                    line = line.strip()
                    if line.startswith("German:"):
                        german = line.replace("German:", "").strip()
                    elif line.startswith("English:"):
                        english = line.replace("English:", "").strip()
                    elif line.startswith("Grammar:"):
                        grammar = line.replace("Grammar:", "").strip()
                    elif line.startswith("Vocabulary:"):
                        mode = "vocab"
                    elif mode == "vocab" and line.startswith("-"):
                        vocab.append(line.lstrip("- ").strip())
                if german:
                    st.success(f"**🇩🇪 German:** {german}")
                    # 语音按钮紧贴下方
                    tts_html = f"""
                    <button onclick="speak()" style="padding:6px 12px; font-size:14px; margin-top:8px;">🔊 Listen</button>
                    <script>
                    function speak() {{
                        var msg = new SpeechSynthesisUtterance();
                        msg.text = `{german}`;
                        msg.lang = 'de-DE';
                        msg.rate = 0.9;
                        window.speechSynthesis.speak(msg);
                    }}
                    </script>
                    """
                    components.html(tts_html, height=50)
                if english:
                    st.info(f"**🇬🇧 English:** {english}")
                if vocab:
                    st.markdown("**📖 Key Vocabulary:**")
                    for v in vocab:
                        st.markdown(f"- {v}")
                if grammar:
                    st.markdown(f"**📐 Grammar Note:** {grammar}")
            except Exception as e:
                st.error(f"API error: {e}")
    else:
        st.info("Click the button to generate a sentence based on today’s news.")

# ==================== TASK 2 ====================
elif task.startswith("Task 2"):
    st.subheader("📈 Major Stock Indices")
    st.caption(f"Latest data as of {today_date}")
    indices = {
        "SSE Composite": "000001.SS",
        "Shenzhen Index": "399001.SZ",
        "Hang Seng": "^HSI",
        "NASDAQ": "^IXIC",
        "S&P 1500": "^SP1500",
        "Dow Jones": "^DJI",
    }
    if st.button("Fetch Latest Data"):
        data = []
        for name, ticker in indices.items():
            try:
                info = yf.Ticker(ticker).history(period="5d")
                if not info.empty:
                    last = info['Close'].iloc[-1]
                    prev = info['Close'].iloc[-2] if len(info) > 1 else last
                    change = (last - prev) / prev * 100
                    color = "green" if change >= 0 else "red"
                    data.append([name, round(last, 2), f"{change:+.2f}%", color])
                else:
                    data.append([name, "N/A", "-", "gray"])
            except:
                data.append([name, "Error", "-", "gray"])
        df = pd.DataFrame(data, columns=["Index", "Last Price", "Change", "Color"])
        # 带颜色显示
        def color_change(val):
            if val == "green":
                return "color: green"
            elif val == "red":
                return "color: red"
            return ""
        styled_df = df.style.applymap(color_change, subset=["Color"])
        st.dataframe(styled_df, use_container_width=True)

        # 走势图：示例用纳斯达克
        try:
            nasdaq = yf.Ticker("^IXIC").history(period="1mo")
            if not nasdaq.empty:
                fig, ax = plt.subplots(figsize=(6,3))
                ax.plot(nasdaq.index, nasdaq['Close'], color='blue')
                ax.set_title("NASDAQ 1-Month Trend")
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                st.pyplot(fig)
        except:
            pass
    else:
        st.info("Click to fetch real-time stock data.")

# ==================== TASK 3 ====================
elif task.startswith("Task 3"):
    st.subheader("🔬 STM Publishing Industry News")
    st.caption(f"Latest updates (last 7 days)")
    # 可靠的 RSS 源
    rss_urls = [
        "https://scholarlykitchen.sspnet.org/feed/",
        "https://retractionwatch.com/feed/",
        "https://www.stm-assoc.org/feed/",
        "https://www.alpsp.org/feed/",
        "https://publicationethics.org/feed/",
        "https://www.sspnet.org/feed/",
    ]
    if st.button("Summarize Latest News"):
        with st.spinner("Fetching and summarizing..."):
            entries = []
            for url in rss_urls:
                try:
                    feed = feedparser.parse(url)
                    for entry in feed.entries[:3]:  # 每个源取前3条
                        entries.append(f"Title: {entry.title}\nLink: {entry.link}\nPublished: {entry.get('published','')}")
                except:
                    continue
            if entries:
                combined = "\n\n".join(entries)
                prompt = (
                    f"Today is {today_date}. Based on the following STM publishing news items from the last week, "
                    "provide a concise summary in 3-4 bullet points. Focus on the most important industry developments. "
                    "Do not include generic statements, only specific news.\n\n{combined}"
                )
                try:
                    resp = model.generate_content(prompt)
                    st.markdown(resp.text)
                except Exception as e:
                    st.error(f"Gemini API error: {e}")
            else:
                st.warning("Could not fetch any RSS feeds. Try again later.")
    else:
        st.info("Click to generate a summary of STM industry news.")

# ==================== TASK 4 ====================
elif task.startswith("Task 4"):
    st.subheader("🌍 Five Global Frontiers (Last 7 Days)")
    st.caption(f"Authoritative milestones since {(date.today()-timedelta(7)).strftime('%B %d')}")
    # 为每个领域指定 RSS 源
    domain_rss = {
        "AGI / AI": [
            "https://www.artificialintelligence-news.com/feed/",
            "https://www.technologyreview.com/feed/",
        ],
        "Geopolitics": [
            "https://www.reuters.com/world/rss",
            "https://www.cfr.org/feed",
        ],
        "Space": [
            "https://spacenews.com/feed/",
            "https://www.nasa.gov/feed/",
        ],
        "Nuclear Fusion": [
            "https://www.iter.org/rss",
            "https://www.world-nuclear-news.org/feed",
        ],
        "Life Science / BCI": [
            "https://www.labiotech.eu/feed/",
            "https://www.statnews.com/feed/",
        ],
    }
    if st.button("Get Latest Milestones"):
        with st.spinner("Aggregating and summarizing..."):
            combined_items = []
            for domain, urls in domain_rss.items():
                domain_entries = []
                for url in urls:
                    try:
                        feed = feedparser.parse(url)
                        for entry in feed.entries[:2]:
                            domain_entries.append(f"- [{entry.title}]({entry.link}) ({entry.get('published','')})")
                    except:
                        continue
                if domain_entries:
                    combined_items.append(f"**{domain}**\n" + "\n".join(domain_entries))
            if combined_items:
                all_news = "\n\n".join(combined_items)
                prompt = (
                    f"Today is {today_date}. Below are recent headlines from the last 7 days across five domains. "
                    "For each domain, select the 1-2 most significant milestones or official announcements, "
                    "and present them in bullet points with the date. Exclude any speculation or rumors. "
                    "If an item is older than one week, ignore it.\n\n{all_news}"
                )
                try:
                    resp = model.generate_content(prompt)
                    st.markdown(resp.text)
                except Exception as e:
                    st.error(f"API error: {e}")
            else:
                st.warning("No RSS feeds could be retrieved. Please try later.")
    else:
        st.info("Click to get a summary of global frontier breakthroughs.")

# ==================== TASK 5 ====================
elif task.startswith("Task 5"):
    st.subheader("💡 Tech Trends & Podcast Recommendation")
    st.caption(f"Trending this week")
    # Product Hunt RSS
    ph_rss = "https://www.producthunt.com/feed"
    podcast_list = [
        "The a16z Show",
        "Exponential View",
        "Hard Fork",
        "Latent Space",
        "No Priors AI",
    ]
    if st.button("Analyze & Recommend"):
        with st.spinner("Analyzing..."):
            try:
                feed = feedparser.parse(ph_rss)
                ph_entries = [f"{e.title} - {e.link}" for e in feed.entries[:5]]
                ph_text = "\n".join(ph_entries)
            except:
                ph_text = "Product Hunt data unavailable."
            prompt = (
                f"Today is {today_date}. Based on the latest Product Hunt trending products and the following podcasts: {', '.join(podcast_list)}. "
                "First, list in bullet points the top 3 tech/AI trends this week (concise). "
                "Second, recommend the single best podcast episode from the list that matches this week's biggest trend. "
                "Provide the episode title and, if possible, a direct listen link (search for the most recent episode). "
                "If no link can be verified, suggest the search format (e.g., 'Search: Hard Fork latest episode')."
            )
            try:
                resp = model.generate_content(prompt)
                st.markdown(resp.text)
            except Exception as e:
                st.error(f"API error: {e}")
    else:
        st.info("Click to get tech trend and podcast recommendation.")

# ==================== TASK 6 ====================
elif task.startswith("Task 6"):
    st.subheader("🏋️ Daily Activity Check-in & YTD Dashboard")
    st.caption(f"{today_date}")

    # 内置示例数据（使用你的CSV格式，tab分隔）
    sample_csv = """Month	Day	Daily	Daily	Daily	Daily	Daily	Daily	Daily	Daily	Weekly	Weekly	Weekly	Weekly	Monthly	Monthly	Monthly	Monthly	Monthly	Quartely	Quartely	Annual	Annual	Annual	Annual	Annual	Daily Recap	Daily Recap	Daily Recap	Daily Recap	Daily Recap	Daily Recap	Daily Recap	Daily Recap
MEVB Category		B	B	B	B	M	M	V	V	V	M	M	B	V	M	M	E	E	V	M	V	V	E	B	B	E	V	E	E	E	M	M	V
Activity		Food & Water & Self care	Energy, Focus and Emotion	Basic Exercise	Foot step	>.5hour MAG	>.5hour books	Meditation	Sketch	Life Admin	Learn sth new	Movie	Extra Exercise	Monthly review	Invest	Play/Exhibits/lecture	Meet new people	Deep exposure to nature	Quarterly Review 	CV & Jobs	Yearly Review + Plan 	Annual leave	Family Gathering	Health Check	Extensive Journey (km)	People	Give back	Engage. Get buy in. Inspire.	Seek for help	Confident & Brave	Storytelling/talkative	AI	Growth Mindset
BUDGET		330	280	365	200	300	300	365	365	53	50	54	200	12	12	25	25	15	4	6	2	20	20	8	7	300	100	225	200	120	100	200	330
YTD		139	118	145	42	105	53	149	149	22	44	10	31	3	9	3	26	16	1	11	0	0	10	5	0	90	52	68	58	54	27	38	122
vs YTD BU (%)		3%	3%	-3%	-49%	-14%	-57%	0%	0%	2%	116%	-55%	-62%	-39%	84%	-71%	155%	161%	-39%	349%	-100%	-100%	22%	53%	-100%	-27%	27%	-26%	-29%	10%	-34%	-53%	-9%
Jan	1	X	X	X		X	X	X	X														X			X	X	X	X				X
Jan	2	X	X			X	X	X	X														X	X		X		X	X				X
Jan	3	X	X	X		X	X	X	X														X				X		X				X
Jan	4	X	X	X	X	X	X	X	X																	X		X					X
Jan	5	X	X	X	X	X		X	X																	X		X				X	X
Jan	6	X	X	X	X	X		X	X																				X	X		X	X
Jan	7		X	X		X		X	X																	X	X	X		X			X
Jan	8	X		X	X	X		X	X																					X	X		X
Jan	9	X	X	X	X			X	X						X											X		X					
Jan	10	X		X				X	X	X					X											X	X						X"""

    # 文件上传
    uploaded = st.file_uploader("Upload your activity tracker CSV (tab or comma separated)", type="csv")
    if uploaded is not None:
        raw = uploaded.read().decode("utf-8")
        st.session_state["raw_csv"] = raw
        st.success("CSV uploaded.")
    elif "raw_csv" not in st.session_state:
        st.session_state["raw_csv"] = sample_csv
        st.info("Using built-in demo data. Upload your own CSV to replace it.")

    raw_csv = st.session_state["raw_csv"]

    # 智能检测分隔符：如果tab数量多就用tab，否则逗号
    sample_line = raw_csv.split("\n")[0]
    if sample_line.count("\t") > sample_line.count(","):
        sep = "\t"
    else:
        sep = ","

    lines = raw_csv.split("\n")
    if len(lines) < 7:
        st.error("CSV must have at least 7 rows (header, category, activity, budget, ytd, vs ytd, and data rows).")
        st.stop()

    # 解析第二行（类别）和第三行（活动名称）
    cat_line = lines[1].split(sep)
    act_line = lines[2].split(sep)
    budget_line = lines[3].split(sep) if len(lines) > 3 else None

    activities = []
    for i in range(2, len(act_line)):
        if i < len(cat_line) and cat_line[i].strip() in ("B","V","M","E"):
            name = act_line[i].strip()
            cat = cat_line[i].strip()
            budget_val = 0
            if budget_line and i < len(budget_line):
                try:
                    budget_val = float(budget_line[i].strip())
                except:
                    budget_val = 0
            activities.append({"name": name, "category": cat, "budget": budget_val})

    if not activities:
        st.error("No activities parsed. Check CSV format: second row must contain B/V/M/E categories, third row activity names.")
        st.stop()

    # 解析每日数据（从第6行索引5开始）
    records = []
    for row_idx in range(5, len(lines)):
        cols = lines[row_idx].split(sep)
        if len(cols) < 3:
            continue
        month_str = cols[0].strip()
        day_str = cols[1].strip()
        if not month_str or not day_str:
            continue
        month_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
        month = month_map.get(month_str, 1)
        try:
            day = int(day_str)
        except:
            continue
        # 假设年份为今年（如果历史数据跨年，可以改进，这里简单处理）
        record_date = date(date.today().year, month, day)
        for idx, act in enumerate(activities):
            col_idx = idx + 2
            if col_idx < len(cols):
                val = cols[col_idx].strip()
                if val.upper() == "X":
                    achieved = 1.0
                elif val.replace(".","",1).isdigit():
                    achieved = float(val)
                else:
                    achieved = 0.0
                records.append({
                    "date": record_date,
                    "activity": act["name"],
                    "category": act["category"],
                    "achieved": achieved,
                    "budget": act["budget"]
                })

    df_hist = pd.DataFrame(records)
    if df_hist.empty:
        st.warning("No historical records found. Start by checking in today!")
    else:
        df_hist["date"] = pd.to_datetime(df_hist["date"]).dt.date

    # 今日打卡
    col_cat = {"B": "🟢 Body", "V": "🟣 Value", "M": "🔵 Mental", "E": "🔴 Emotion"}
    categories = ["B","V","M","E"]
    new_entries = []
    st.markdown("### ✅ Today's Check-in")
    for cat in categories:
        st.markdown(f"**{col_cat.get(cat, cat)}**")
        cat_acts = [a for a in activities if a["category"] == cat]
        cols = st.columns(len(cat_acts))
        for i, act in enumerate(cat_acts):
            # 检查今天是否已存在记录
            existing = df_hist[(df_hist["date"] == date.today()) & (df_hist["activity"] == act["name"])]
            if not existing.empty:
                cols[i].checkbox(act["name"], value=True, disabled=True, key=f"{act['name']}_{date.today()}_disabled")
            else:
                checked = cols[i].checkbox(act["name"], key=f"{act['name']}_{date.today()}")
                if checked:
                    new_entries.append({
                        "date": date.today(),
                        "activity": act["name"],
                        "category": cat,
                        "achieved": 1,
                        "budget": act["budget"]
                    })
    if st.button("💾 Save Today's Check-in"):
        if new_entries:
            new_df = pd.DataFrame(new_entries)
            df_hist = pd.concat([df_hist, new_df], ignore_index=True)
            st.session_state["updated_df"] = df_hist
            st.success(f"Saved {len(new_entries)} activities.")
            st.rerun()  # 修复后的 rerun
        else:
            st.warning("No new activities selected.")

    # YTD 看板
    st.markdown("### 📊 Year-to-Date Performance")
    if not df_hist.empty:
        ytd = df_hist[df_hist["date"].apply(lambda x: x.year == date.today().year)]
        if not ytd.empty:
            daily_cat = ytd.groupby(["date","category"])["achieved"].sum().unstack(fill_value=0)
            cumulative = daily_cat.cumsum()
            # 计算目标线（简化：将各活动 budget 按天均摊）
            target_daily = {}
            for act in activities:
                target_daily[act["category"]] = target_daily.get(act["category"], 0) + act["budget"] / 365
            days_passed = (date.today() - date(date.today().year,1,1)).days + 1
            cumulative_target = {cat: t * days_passed for cat, t in target_daily.items()}

            fig, ax = plt.subplots(figsize=(10,5))
            colors = {"B":"green", "V":"purple", "M":"blue", "E":"red"}
            for cat in categories:
                if cat in cumulative.columns:
                    ax.plot(cumulative.index, cumulative[cat], label=cat, color=colors.get(cat,"black"), marker='.')
            ax.set_title("YTD Cumulative Completed Activities")
            ax.legend()
            st.pyplot(fig)

            st.markdown("### ⚠️ Progress vs Target")
            for cat in categories:
                if cat in cumulative.columns:
                    actual = cumulative[cat].iloc[-1]
                    target = cumulative_target.get(cat, 0)
                    shortfall = target - actual
                    if shortfall > 2:
                        st.warning(f"**{cat} ({col_cat.get(cat)})** is behind by {shortfall:.0f} units. Consider increasing effort.")
                    else:
                        st.info(f"**{cat}** on track (actual {actual:.1f} / target {target:.1f})")
        else:
            st.info("No data for current year yet.")
    else:
        st.info("No activity data loaded.")

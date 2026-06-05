import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, datetime, timedelta
import yfinance as yf
import google.generativeai as genai
import requests
import feedparser
import streamlit.components.v1 as components
import time, re, io

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
                    # 语音按钮高度增加防止截断
                    tts_html = f"""
                    <div style="margin-top:8px;">
                        <button onclick="speak()" style="padding:6px 12px; font-size:14px;">🔊 Listen</button>
                    </div>
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
                    components.html(tts_html, height=60)
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
        rows = []
        for name, ticker in indices.items():
            try:
                info = yf.Ticker(ticker).history(period="5d")
                if not info.empty:
                    last = info['Close'].iloc[-1]
                    prev = info['Close'].iloc[-2] if len(info) > 1 else last
                    change = (last - prev) / prev * 100
                    sign = "+" if change >= 0 else ""
                    color = "green" if change >= 0 else "red"
                    rows.append((name, f"{last:.2f}", f"{sign}{change:.2f}%", color))
                else:
                    rows.append((name, "N/A", "-", "gray"))
            except:
                rows.append((name, "Error", "-", "gray"))
        # 生成 HTML 表格
        html = "<table style='width:100%; border-collapse: collapse;'>"
        html += "<tr><th>Index</th><th>Last Price</th><th>Change</th></tr>"
        for name, price, chg, color in rows:
            html += f"<tr><td>{name}</td><td>{price}</td><td style='color:{color}; font-weight:bold;'>{chg}</td></tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

        # 纳斯达克 30 天走势图
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
    st.subheader("🔬 STM Publishing Industry News (Last 7 Days)")
    rss_urls = [
        ("Scholarly Kitchen", "https://scholarlykitchen.sspnet.org/feed/"),
        ("Retraction Watch", "https://retractionwatch.com/feed/"),
        ("STM Association", "https://www.stm-assoc.org/feed/"),
        ("ALPSP", "https://www.alpsp.org/feed/"),
        ("COPE", "https://publicationethics.org/feed/"),
        ("SSP", "https://www.sspnet.org/feed/"),
    ]
    if st.button("Summarize Latest News"):
        with st.spinner("Fetching..."):
            entries = []
            for src_name, url in rss_urls:
                try:
                    feed = feedparser.parse(url)
                    for entry in feed.entries[:2]:
                        entries.append((src_name, entry.title, entry.link, entry.get("published","")))
                except:
                    continue
            if entries:
                # 构造带来源的文本
                combined_lines = []
                for src, title, link, pub in entries:
                    combined_lines.append(f"Source: {src} | Title: {title} | Link: {link} | Date: {pub}")
                combined = "\n".join(combined_lines)
                prompt = (
                    f"Today is {today_date}. Below are recent STM publishing news headlines from the last week. "
                    "Write a concise summary in 3-4 bullet points. For each bullet, include the key point and cite the source name (e.g., 'According to Scholarly Kitchen...'). "
                    "Do not invent any information not present in the headlines. Only use the provided items.\n\n"
                    f"{combined}"
                )
                try:
                    resp = model.generate_content(prompt)
                    st.markdown(resp.text)
                    # 显示来源链接
                    with st.expander("View all sources"):
                        for src, title, link, pub in entries:
                            st.markdown(f"- **{src}**: [{title}]({link}) ({pub})")
                except Exception as e:
                    st.error(f"Gemini error: {e}")
            else:
                st.warning("Could not fetch any RSS feeds. Try again later.")
    else:
        st.info("Click to generate summary.")

# ==================== TASK 4 ====================
elif task.startswith("Task 4"):
    st.subheader("🌍 Five Global Frontiers (Last 7 Days)")
    # 严格对应的 RSS 源
    domain_rss = {
        "AGI / Artificial General Intelligence": [
            ("Synced Review", "https://syncedreview.com/feed/"),
            ("AI News", "https://www.artificialintelligence-news.com/feed/"),
        ],
        "Global Order Restructuring": [
            ("Reuters World", "https://www.reuters.com/world/rss"),
            ("CFR", "https://www.cfr.org/feed"),
        ],
        "Space Exploration": [
            ("SpaceNews", "https://spacenews.com/feed/"),
            ("NASA", "https://www.nasa.gov/feed/"),
        ],
        "Controlled Nuclear Fusion": [
            ("World Nuclear News", "https://www.world-nuclear-news.org/feed"),
            ("ScienceDaily Nuclear", "https://www.sciencedaily.com/rss/matter_energy/nuclear_energy.xml"),
        ],
        "Life Science / Anti-Aging + BCI": [
            ("STAT News", "https://www.statnews.com/feed/"),
            ("Fierce Biotech", "https://www.fiercebiotech.com/feed"),
        ],
    }
    if st.button("Get Latest Milestones"):
        with st.spinner("Aggregating..."):
            all_domain_news = {}
            for domain, feeds in domain_rss.items():
                headlines = []
                for src_name, url in feeds:
                    try:
                        feed = feedparser.parse(url)
                        for entry in feed.entries[:2]:
                            headlines.append((src_name, entry.title, entry.link, entry.get("published","")))
                    except:
                        continue
                if headlines:
                    all_domain_news[domain] = headlines
            if not all_domain_news:
                st.warning("No RSS feeds could be retrieved. Please try later.")
            else:
                # 构建每个领域的摘要输入
                combined_for_prompt = []
                for domain, items in all_domain_news.items():
                    combined_for_prompt.append(f"**{domain}**")
                    for src, title, link, pub in items:
                        combined_for_prompt.append(f"- {src}: {title} ({pub}) Link: {link}")
                input_text = "\n".join(combined_for_prompt)
                prompt = (
                    f"Today is {today_date}. Below are headlines from the last 7 days for five specific frontier areas. "
                    "For each area, present 1-2 most important milestones in bullet points. Include the date and source (e.g., 'June 4, 2026 - Reuters: ...'). "
                    "If a domain has no significant news, say 'No major announcements this week.' "
                    "DO NOT fabricate or extrapolate. Only use the provided headlines.\n\n"
                    f"{input_text}"
                )
                try:
                    resp = model.generate_content(prompt)
                    st.markdown(resp.text)
                    # 展开查看所有原始链接
                    with st.expander("View all raw headlines"):
                        for domain, items in all_domain_news.items():
                            st.markdown(f"**{domain}**")
                            for src, title, link, pub in items:
                                st.markdown(f"- [{title}]({link}) ({src}, {pub})")
                except Exception as e:
                    st.error(f"Gemini error: {e}")
    else:
        st.info("Click to get frontier updates.")

# ==================== TASK 5 ====================
elif task.startswith("Task 5"):
    st.subheader("💡 Tech Trends & Podcast Recommendation")
    st.caption("Based on Product Hunt trending products")
    # Product Hunt RSS
    ph_rss = "https://www.producthunt.com/feed"
    podcast_names = ["The a16z Show", "Exponential View", "Hard Fork", "Latent Space", "No Priors AI"]
    if st.button("Analyze & Recommend"):
        with st.spinner("Analyzing..."):
            ph_entries = []
            try:
                feed = feedparser.parse(ph_rss)
                for entry in feed.entries[:5]:
                    ph_entries.append(f"{entry.title} – {entry.link}")
            except:
                pass
            ph_text = "\n".join(ph_entries) if ph_entries else "Product Hunt data unavailable."
            prompt = (
                f"Today is {today_date}. Based on the following Product Hunt trending products, identify the top 2-3 tech/AI trends this week. "
                "Present as bullet points. Then, choose one podcast from this list: The a16z Show, Exponential View, Hard Fork, Latent Space, No Priors AI "
                "that best matches the current trend. Explain your choice in one sentence. "
                "IMPORTANT: Do not fabricate episode names or links. If you cannot verify, say 'I recommend checking the latest episode of [Podcast]' without a link. "
                "Be concise.\n\n"
                f"Product Hunt:\n{ph_text}"
            )
            try:
                resp = model.generate_content(prompt)
                st.markdown(resp.text)
            except Exception as e:
                st.error(f"API error: {e}")
    else:
        st.info("Click to get trend analysis and podcast recommendation.")

# ==================== TASK 6 ====================
elif task.startswith("Task 6"):
    st.subheader("🏋️ Daily Activity Check-in & YTD Dashboard")
    st.caption(f"{today_date}")

    # ---- 内置示例数据 ----
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

    # 上传或使用示例
    uploaded = st.file_uploader("Upload your activity tracker CSV", type="csv")
    if uploaded is not None:
        raw = uploaded.read().decode("utf-8")
        st.session_state["raw_csv"] = raw
    elif "raw_csv" not in st.session_state:
        st.session_state["raw_csv"] = sample_csv
        st.info("Using built-in demo data. Upload your own CSV to replace it.")

    raw_csv = st.session_state["raw_csv"]
    # 检测分隔符
    sample_line = raw_csv.split("\n")[0]
    sep = "\t" if sample_line.count("\t") > sample_line.count(",") else ","
    lines = raw_csv.split("\n")
    if len(lines) < 7:
        st.error("CSV must have at least 7 rows.")
        st.stop()

    cat_line = lines[1].split(sep)
    act_line = lines[2].split(sep)
    budget_line = lines[3].split(sep) if len(lines) > 3 else []

    # 解析活动列表及 budget
    activities = []
    for i in range(2, len(act_line)):
        if i < len(cat_line) and cat_line[i].strip() in ("B","V","M","E"):
            name = act_line[i].strip()
            cat = cat_line[i].strip()
            budget = 0
            if i < len(budget_line):
                try:
                    budget = float(budget_line[i].strip())
                except:
                    pass
            activities.append({"name": name, "category": cat, "budget": budget})

    if not activities:
        st.error("No activities parsed. Check format: second row B/V/M/E, third row names.")
        st.stop()

    # 解析历史记录
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
        month = month_map.get(month_str)
        if not month:
            continue
        try:
            day = int(day_str)
        except:
            continue
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
    if not df_hist.empty:
        df_hist["date"] = pd.to_datetime(df_hist["date"]).dt.date

    # ---------- 1. 打卡日历 ----------
    st.markdown("### 📅 Select Date for Check-in")
    selected_date = st.date_input("Pick a date", date.today())
    st.markdown(f"**Activities for {selected_date.strftime('%B %d, %Y')}**")
    # 获取该日期的记录
    if not df_hist.empty:
        day_records = df_hist[df_hist["date"] == selected_date]
    else:
        day_records = pd.DataFrame()

    col_cat = {"B": "🟢 Body", "V": "🟣 Value", "M": "🔵 Mental", "E": "🔴 Emotion"}
    categories = ["B","V","M","E"]
    updated_entries = {}
    for cat in categories:
        st.markdown(f"**{col_cat[cat]}**")
        cat_acts = [a for a in activities if a["category"] == cat]
        cols = st.columns(len(cat_acts))
        for i, act in enumerate(cat_acts):
            key = f"{act['name']}_{selected_date}"
            # 查找现有记录
            existing = day_records[day_records["activity"] == act["name"]] if not day_records.empty else pd.DataFrame()
            current_val = existing["achieved"].values[0] if not existing.empty else 0.0
            checked = cols[i].checkbox(act["name"], value=(current_val > 0), key=key)
            updated_entries[act["name"]] = 1.0 if checked else 0.0

    if st.button("💾 Save Check-in for this date"):
        # 删除该日期的现有记录，然后插入新记录
        if not df_hist.empty:
            df_hist = df_hist[df_hist["date"] != selected_date]
        new_rows = []
        for act in activities:
            new_rows.append({
                "date": selected_date,
                "activity": act["name"],
                "category": act["category"],
                "achieved": updated_entries[act["name"]],
                "budget": act["budget"]
            })
        df_new = pd.DataFrame(new_rows)
        df_hist = pd.concat([df_hist, df_new], ignore_index=True)
        st.session_state["updated_df"] = df_hist
        st.success("Check-in saved!")
        st.rerun()

    # ---------- 2. YTD 看板与 Budget 修改 ----------
    st.markdown("### 📊 Year-to-Date Performance")
    if not df_hist.empty:
        ytd = df_hist[df_hist["date"].apply(lambda x: x.year == date.today().year)]
        if not ytd.empty:
            # 按活动计算实际完成次数
            actual_by_act = ytd.groupby("activity")["achieved"].sum()
            # 年目标
            target_by_act = {act["name"]: act["budget"] for act in activities}
            days_passed = (date.today() - date(date.today().year,1,1)).days + 1
            # 理想进度
            progress = []
            for act in activities:
                name = act["name"]
                budget = target_by_act[name]
                actual = actual_by_act.get(name, 0)
                expected = (budget / 365) * days_passed
                progress.append({
                    "Category": act["category"],
                    "Activity": name,
                    "Annual Target": budget,
                    "Actual (YTD)": actual,
                    "Expected (YTD)": round(expected, 1),
                    "Status": "On Track" if actual >= expected else f"Behind by {round(expected - actual, 1)}"
                })
            progress_df = pd.DataFrame(progress)
            st.dataframe(progress_df, use_container_width=True)

            # 落后提醒
            st.markdown("### ⚠️ Lagging Activities")
            lagging = [p for p in progress if p["Status"] != "On Track"]
            if lagging:
                for item in lagging:
                    st.warning(f"{item['Activity']} ({item['Category']}): Actual {item['Actual (YTD)']} vs Expected {item['Expected (YTD)']}")
            else:
                st.success("All activities are on track!")

            # 累计折线图（按类别）
            daily_cat = ytd.groupby(["date","category"])["achieved"].sum().unstack(fill_value=0)
            cumulative = daily_cat.cumsum()
            fig, ax = plt.subplots(figsize=(10,5))
            colors = {"B":"green", "V":"purple", "M":"blue", "E":"red"}
            for cat in categories:
                if cat in cumulative.columns:
                    ax.plot(cumulative.index, cumulative[cat], label=cat, color=colors[cat], marker='.')
            ax.set_title("YTD Cumulative Completed Activities")
            ax.legend()
            st.pyplot(fig)
        else:
            st.info("No data for current year.")
    else:
        st.info("No activity data loaded.")

    # ---------- 3. 编辑全年 Budget ----------
    st.markdown("### ✏️ Edit Annual Budget")
    with st.form("budget_form"):
        new_budgets = {}
        for act in activities:
            new_val = st.number_input(f"{act['name']} ({act['category']})", min_value=0, value=int(act["budget"]), key=f"budget_{act['name']}")
            new_budgets[act["name"]] = new_val
        if st.form_submit_button("Update Budget"):
            for act in activities:
                act["budget"] = new_budgets[act["name"]]
            st.success("Budgets updated! Refresh to see new targets.")
            # 注意：预算修改后需重新生成 CSV 或仅保存在 session 中，这里直接更新 activities 列表，后续 YTD 计算会使用新 budget。

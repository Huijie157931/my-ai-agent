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
import time, re, io, random

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
    st.caption("Based on a real news headline from BBC")

    # 抓取 BBC 新闻
    bbc_rss = "http://feeds.bbci.co.uk/news/rss.xml"
    news_title = ""
    news_link = ""
    try:
        feed = feedparser.parse(bbc_rss)
        if feed.entries:
            # 随机选一条或取第一条
            chosen = feed.entries[0]  # 可改为 random.choice(feed.entries[:5])
            news_title = chosen.title
            news_link = chosen.link
    except:
        news_title = "Unable to fetch news"
        news_link = ""

    if news_title:
        st.markdown(f"**📌 Today's headline:** {news_title}")
        if news_link:
            st.markdown(f"[🔗 Read full article]({news_link})")
    else:
        st.warning("Could not fetch latest news. Using generic prompt.")

    if st.button("Generate Sentence"):
        with st.spinner("Generating..."):
            prompt = (
                f"Today is {today_date}. The reference news headline is: '{news_title}'. "
                "Based on this exact news topic, generate: "
                "1) A single German sentence at A2 level. "
                "2) Its accurate English translation. "
                "3) 3-5 key German words from the sentence, each with its English meaning and a short example phrase. Format as 'Word (part of speech): meaning | Example: ...' "
                "4) One brief grammar explanation (in English). "
                "Format exactly:\n"
                "German: <sentence>\n"
                "English: <translation>\n"
                "Vocabulary:\n"
                "- <Word1 (pos)>: <meaning> | Example: <example>\n"
                "- ...\n"
                "Grammar: <explanation>"
            )
            try:
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
        # 表格数据
        rows = []
        for name, ticker in indices.items():
            try:
                info = yf.Ticker(ticker).history(period="5d")
                if not info.empty:
                    last = info['Close'].iloc[-1]
                    prev = info['Close'].iloc[-2] if len(info) > 1 else last
                    change = (last - prev) / prev * 100
                    sign = "+" if change >= 0 else ""
                    # 用户要求：红涨绿跌
                    color = "red" if change >= 0 else "green"
                    rows.append((name, f"{last:.2f}", f"{sign}{change:.2f}%", color))
                else:
                    rows.append((name, "N/A", "-", "gray"))
            except:
                rows.append((name, "Error", "-", "gray"))

        html = "<table style='width:100%; border-collapse: collapse;'>"
        html += "<tr><th>Index</th><th>Last Price</th><th>Change</th></tr>"
        for name, price, chg, color in rows:
            html += f"<tr><td>{name}</td><td>{price}</td><td style='color:{color}; font-weight:bold;'>{chg}</td></tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

        # 当日分时走势图（尝试获取分钟数据）
        st.markdown("**📊 Today's Intraday (from open to latest)**")
        fig, axes = plt.subplots(3, 2, figsize=(12, 10))
        axes = axes.flatten()
        for idx, (name, ticker) in enumerate(indices.items()):
            ax = axes[idx]
            try:
                df_intra = yf.Ticker(ticker).history(period="1d", interval="5m")
                if not df_intra.empty and len(df_intra) > 1:
                    ax.plot(df_intra.index, df_intra['Close'], color='blue')
                    ax.set_title(name, fontsize=9)
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                else:
                    # 降级为简单显示开盘和当前
                    info = yf.Ticker(ticker).history(period="1d")
                    if not info.empty:
                        open_price = info['Open'].iloc[0]
                        last_price = info['Close'].iloc[-1]
                        ax.bar(['Open','Current'], [open_price, last_price], color=['gray','blue'])
                        ax.set_title(name, fontsize=9)
                    else:
                        ax.text(0.5,0.5,'No data', ha='center')
            except:
                ax.text(0.5,0.5,'Error', ha='center')
        plt.tight_layout()
        st.pyplot(fig)

        # 一个月走势（2x3子图）
        st.markdown("**📅 1-Month Trend**")
        fig2, axes2 = plt.subplots(3, 2, figsize=(12, 10))
        axes2 = axes2.flatten()
        for idx, (name, ticker) in enumerate(indices.items()):
            ax = axes2[idx]
            try:
                hist = yf.Ticker(ticker).history(period="1mo")
                if not hist.empty:
                    ax.plot(hist.index, hist['Close'], color='blue')
                    ax.set_title(name, fontsize=9)
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                else:
                    ax.text(0.5,0.5,'No data', ha='center')
            except:
                ax.text(0.5,0.5,'Error', ha='center')
        plt.tight_layout()
        st.pyplot(fig2)
    else:
        st.info("Click to fetch real-time stock data.")

# ==================== TASK 3 ====================
# (保留上一版的 Task3 代码，不做大改)
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
                combined_lines = []
                for src, title, link, pub in entries:
                    combined_lines.append(f"Source: {src} | Title: {title} | Link: {link} | Date: {pub}")
                combined = "\n".join(combined_lines)
                prompt = (
                    f"Today is {today_date}. Below are recent STM publishing news headlines from the last week. "
                    "Write a concise summary in 3-4 bullet points. For each bullet, include the key point and cite the source name. "
                    "Do not invent any information.\n\n{combined}"
                )
                try:
                    resp = model.generate_content(prompt)
                    st.markdown(resp.text)
                    with st.expander("View all sources"):
                        for src, title, link, pub in entries:
                            st.markdown(f"- **{src}**: [{title}]({link}) ({pub})")
                except Exception as e:
                    st.error(f"Gemini error: {e}")
            else:
                st.warning("Could not fetch any RSS feeds.")
    else:
        st.info("Click to generate summary.")

# ==================== TASK 4 ====================
elif task.startswith("Task 4"):
    st.subheader("🌍 Five Global Frontiers (Last 7 Days)")
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
                st.warning("No RSS feeds could be retrieved.")
            else:
                combined_for_prompt = []
                for domain, items in all_domain_news.items():
                    combined_for_prompt.append(f"**{domain}**")
                    for src, title, link, pub in items:
                        combined_for_prompt.append(f"- {src}: {title} ({pub}) Link: {link}")
                input_text = "\n".join(combined_for_prompt)
                prompt = (
                    f"Today is {today_date}. Below are headlines from the last 7 days for five specific frontier areas. "
                    "For each area, present 1-2 most important milestones in bullet points. Include the date and source. "
                    "DO NOT fabricate.\n\n{input_text}"
                )
                try:
                    resp = model.generate_content(prompt)
                    st.markdown(resp.text)
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
                "IMPORTANT: Do not fabricate episode names or links. If you cannot verify, say 'I recommend checking the latest episode of [Podcast]' without a link.\n\n"
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

    # 上传 CSV
    uploaded = st.file_uploader("Upload your activity tracker CSV", type="csv")
    if uploaded is not None:
        raw = uploaded.read().decode("utf-8")
        st.session_state["raw_csv"] = raw
    elif "raw_csv" not in st.session_state:
        st.session_state["raw_csv"] = sample_csv
        st.info("Using built-in demo data. Upload your own CSV to replace it.")

    raw_csv = st.session_state["raw_csv"]
    sample_line = raw_csv.split("\n")[0]
    sep = "\t" if sample_line.count("\t") > sample_line.count(",") else ","
    lines = raw_csv.split("\n")
    if len(lines) < 7:
        st.error("CSV must have at least 7 rows.")
        st.stop()

    cat_line = lines[1].split(sep)
    act_line = lines[2].split(sep)
    budget_line = lines[3].split(sep) if len(lines) > 3 else []

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
        st.error("No activities parsed.")
        st.stop()

    # 初始化或读取历史记录到 session_state
    if "df_hist" not in st.session_state:
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
        st.session_state["df_hist"] = pd.DataFrame(records)
        if not st.session_state["df_hist"].empty:
            st.session_state["df_hist"]["date"] = pd.to_datetime(st.session_state["df_hist"]["date"]).dt.date

    df_hist = st.session_state["df_hist"]

    # ----- 1. 打卡日历 -----
    st.markdown("### 📅 Select Date for Check-in")
    selected_date = st.date_input("Pick a date", date.today())
    st.markdown(f"**Activities for {selected_date.strftime('%B %d, %Y')}**")
    day_records = df_hist[df_hist["date"] == selected_date] if not df_hist.empty else pd.DataFrame()

    col_cat = {"B": "🟢 Body", "V": "🟣 Value", "M": "🔵 Mental", "E": "🔴 Emotion"}
    categories = ["B","V","M","E"]
    updated_entries = {}
    for cat in categories:
        st.markdown(f"**{col_cat[cat]}**")
        cat_acts = [a for a in activities if a["category"] == cat]
        cols = st.columns(len(cat_acts))
        for i, act in enumerate(cat_acts):
            key = f"{act['name']}_{selected_date}"
            existing = day_records[day_records["activity"] == act["name"]] if not day_records.empty else pd.DataFrame()
            current_val = existing["achieved"].values[0] if not existing.empty else 0.0
            checked = cols[i].checkbox(act["name"], value=(current_val > 0), key=key)
            updated_entries[act["name"]] = 1.0 if checked else 0.0

    if st.button("💾 Save Check-in for this date"):
        # 删除旧记录，写入新记录
        df_hist = df_hist[df_hist["date"] != selected_date] if not df_hist.empty else df_hist
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
        df_hist["date"] = pd.to_datetime(df_hist["date"]).dt.date
        st.session_state["df_hist"] = df_hist
        st.success("Check-in saved!")
        st.rerun()

    # ----- 2. YTD Progress (百分比，颜色) -----
    st.markdown("### 📊 Year-to-Date Progress")
    if not df_hist.empty:
        ytd = df_hist[df_hist["date"].apply(lambda x: x.year == date.today().year)]
        if not ytd.empty:
            days_passed = (date.today() - date(date.today().year,1,1)).days + 1
            progress_rows = []
            for act in activities:
                name = act["name"]
                budget = act["budget"]
                actual = ytd[ytd["activity"] == name]["achieved"].sum()
                expected_ratio = (budget / 365) * days_passed / budget if budget > 0 else 0
                actual_ratio = actual / budget if budget > 0 else 0
                # 状态定义
                if actual_ratio >= expected_ratio * 1.05:
                    status = "Ahead"
                    color = "green"
                elif actual_ratio >= expected_ratio * 0.95:
                    status = "On Track"
                    color = "green"
                else:
                    status = "Behind"
                    color = "red"
                progress_rows.append({
                    "Category": act["category"],
                    "Activity": name,
                    "Annual Target": budget,
                    "Actual YTD": actual,
                    "Expected YTD": round(budget * days_passed / 365, 1),
                    "Progress %": f"{actual_ratio:.1%}",
                    "Status": status,
                    "Status Color": color
                })
            df_progress = pd.DataFrame(progress_rows)

            # 带颜色显示
            def color_status(val):
                if val == "Ahead" or val == "On Track":
                    return "color: green"
                return "color: red"
            styled = df_progress.style.applymap(color_status, subset=["Status"])
            st.dataframe(styled, use_container_width=True)

            # 大类进度（B/V/M/E）
            st.markdown("**Category Totals**")
            cat_summary = []
            for cat in categories:
                cat_acts = [a for a in activities if a["category"] == cat]
                if cat_acts:
                    total_budget = sum(a["budget"] for a in cat_acts)
                    total_actual = sum(ytd[ytd["activity"] == a["name"]]["achieved"].sum() for a in cat_acts)
                    expected = total_budget * days_passed / 365
                    cat_progress_pct = total_actual / total_budget if total_budget > 0 else 0
                    cat_expected_pct = expected / total_budget if total_budget > 0 else 0
                    cat_status = "On Track" if total_actual >= expected * 0.95 else "Behind"
                    cat_color = "green" if cat_status == "On Track" else "red"
                    cat_summary.append({
                        "Category": cat,
                        "Total Target": total_budget,
                        "Actual": total_actual,
                        "Expected": round(expected, 1),
                        "Progress %": f"{cat_progress_pct:.1%}",
                        "Status": cat_status,
                        "Color": cat_color
                    })
            df_cat = pd.DataFrame(cat_summary)
            def color_cat_status(val):
                if val == "On Track":
                    return "color: green"
                return "color: red"
            styled_cat = df_cat.style.applymap(color_cat_status, subset=["Status"])
            st.dataframe(styled_cat, use_container_width=True)

        else:
            st.info("No data for this year yet.")
    else:
        st.info("No activity data loaded.")

    # ----- 3. 编辑 Budget (下拉菜单) -----
    st.markdown("### ✏️ Edit Annual Budget")
    selected_activity = st.selectbox("Select activity to modify:", [a["name"] for a in activities])
    current_budget = next(a["budget"] for a in activities if a["name"] == selected_activity)
    new_budget = st.number_input(f"New budget for {selected_activity}", value=int(current_budget), min_value=0)
    if st.button("Update Budget"):
        for a in activities:
            if a["name"] == selected_activity:
                a["budget"] = new_budget
                break
        # 同时更新 df_hist 中该活动的 budget 列
        if not df_hist.empty:
            mask = df_hist["activity"] == selected_activity
            df_hist.loc[mask, "budget"] = new_budget
            st.session_state["df_hist"] = df_hist
        st.success(f"Budget for '{selected_activity}' updated to {new_budget}.")
        st.rerun()

    # ----- 4. 导出 CSV -----
    st.markdown("### 📥 Export Data")
    csv_buffer = io.StringIO()
    if not df_hist.empty:
        df_hist.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download activity log as CSV",
            data=csv_buffer.getvalue(),
            file_name=f"activity_log_{date.today()}.csv",
            mime="text/csv"
        )
    else:
        st.info("No data to export yet.")

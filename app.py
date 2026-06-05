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
import time, io, random

# ---------- 初始化 ----------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="Personal AI Agent", page_icon="🤖", layout="wide")
st.title("🤖 Personal AI Assistant – Full Demo")
today_date = date.today().strftime("%B %d, %Y")
st.caption(f"📅 {today_date}")

# ---------- 辅助绘图函数（时区安全）----------
def safe_tz_convert(df, tz_name):
    if df.empty:
        return df
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert(tz_name)
    else:
        df.index = df.index.tz_convert(tz_name)
    return df

def plot_intraday(name, ticker, tz_name):
    try:
        df = yf.Ticker(ticker).history(period="1d", interval="5m")
        if df.empty or len(df) < 2:
            fig, ax = plt.subplots(figsize=(3.5, 1.8))
            ax.text(0.5, 0.5, 'Not enough intraday data', ha='center', va='center', fontsize=8)
            ax.set_title(f"{name} (Real-Time)", fontsize=8)
            st.pyplot(fig)
            return
        df = safe_tz_convert(df, tz_name)
        open_price = df['Open'].iloc[0]
        last_price = df['Close'].iloc[-1]
        change = (last_price - open_price) / open_price * 100
        line_color = "red" if change >= 0 else "green"
        fig, ax = plt.subplots(figsize=(3.5, 1.8))
        ax.plot(df.index, df['Close'], color=line_color, linewidth=1)
        ax.set_title(f"{name} (Real-Time)", fontsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=tz_name))
        plt.xticks(fontsize=6)
        plt.yticks(fontsize=6)
        st.pyplot(fig)
    except Exception:
        fig, ax = plt.subplots(figsize=(3.5, 1.8))
        ax.text(0.5, 0.5, 'Error loading data', ha='center', va='center', fontsize=8)
        ax.set_title(f"{name} (Real-Time)", fontsize=8)
        st.pyplot(fig)

def plot_monthly(name, ticker, tz_name):
    try:
        df = yf.Ticker(ticker).history(period="1mo")
        if df.empty or len(df) < 2:
            fig, ax = plt.subplots(figsize=(3.5, 1.8))
            ax.text(0.5, 0.5, 'Not enough monthly data', ha='center', va='center', fontsize=8)
            ax.set_title(f"{name} (1M)", fontsize=8)
            st.pyplot(fig)
            return
        df = safe_tz_convert(df, tz_name)
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        change = (end_price - start_price) / start_price * 100
        line_color = "red" if change >= 0 else "green"
        fig, ax = plt.subplots(figsize=(3.5, 1.8))
        ax.plot(df.index, df['Close'], color=line_color, linewidth=1)
        ax.set_title(f"{name} (1M)", fontsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d', tz=tz_name))
        plt.xticks(fontsize=6)
        plt.yticks(fontsize=6)
        st.pyplot(fig)
    except Exception:
        fig, ax = plt.subplots(figsize=(3.5, 1.8))
        ax.text(0.5, 0.5, 'Error loading data', ha='center', va='center', fontsize=8)
        ax.set_title(f"{name} (1M)", fontsize=8)
        st.pyplot(fig)

# ---------- 任务选择 ----------
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
    bbc_rss = "http://feeds.bbci.co.uk/news/rss.xml"
    news_title = ""
    news_link = ""
    try:
        feed = feedparser.parse(bbc_rss)
        if feed.entries:
            chosen = random.choice(feed.entries[:5]) if len(feed.entries) >= 5 else feed.entries[0]
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
    else:
        st.info("Click the button to generate a sentence based on today’s news.")

# ==================== TASK 2 ====================
elif task.startswith("Task 2"):
    st.subheader("📈 Major Stock Indices")
    st.caption(f"Latest data as of {today_date}")

    stocks = {
        "A-Share": {"SSE Composite": "000001.SS", "Shenzhen Index": "399001.SZ"},
        "HK": {"Hang Seng": "^HSI"},
        "US": {"NASDAQ": "^IXIC", "S&P 1500": "^SP1500", "Dow Jones": "^DJI"}
    }

    if st.button("Fetch Real-time Data"):
        rows = []
        for region, names in stocks.items():
            for name, ticker in names.items():
                try:
                    info = yf.Ticker(ticker).history(period="1d", interval="5m")
                    if not info.empty:
                        last = info['Close'].iloc[-1]
                        open_price = info['Open'].iloc[0]
                        change = (last - open_price) / open_price * 100
                        sign = "+" if change >= 0 else ""
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

        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.markdown("**🇨🇳 A-Share / HK (Beijing Time)**")
            plot_intraday("SSE Composite", "000001.SS", "Asia/Shanghai")
            plot_intraday("Shenzhen Index", "399001.SZ", "Asia/Shanghai")
            plot_intraday("Hang Seng", "^HSI", "Asia/Shanghai")
        with col_right:
            st.markdown("**🇺🇸 US Market (New York Time)**")
            plot_intraday("NASDAQ", "^IXIC", "America/New_York")
            plot_intraday("S&P 1500", "^SP1500", "America/New_York")
            plot_intraday("Dow Jones", "^DJI", "America/New_York")

        st.markdown("**📅 1-Month Trend**")
        col_trend_left, col_trend_right = st.columns([1, 1])
        with col_trend_left:
            plot_monthly("SSE Composite", "000001.SS", "Asia/Shanghai")
            plot_monthly("Shenzhen Index", "399001.SZ", "Asia/Shanghai")
            plot_monthly("Hang Seng", "^HSI", "Asia/Shanghai")
        with col_trend_right:
            plot_monthly("NASDAQ", "^IXIC", "America/New_York")
            plot_monthly("S&P 1500", "^SP1500", "America/New_York")
            plot_monthly("Dow Jones", "^DJI", "America/New_York")
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
Activity		Food & Water & Self care	Energy, Focus and Emotion	Basic Exercise	Foot step	>.5hour MAG	>.5hour books	Meditation	Sketch	Life Admin	Learn sth new	Movie	Extra Exercise	Monthly review	Invest	Play/Exhibits/lecture	Meet new people	Deep exposure to nature	Quarterly Review	CV & Jobs	Yearly Review + Plan	Annual leave	Family Gathering	Health Check	Extensive Journey (km)	People	Give back	Engage. Get buy in. Inspire.	Seek for help	Confident & Brave	Storytelling/talkative	AI	Growth Mindset
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

    uploaded = st.file_uploader("Upload your activity tracker CSV", type="csv")
    if uploaded is not None:
        raw = uploaded.read().decode("utf-8")
        st.session_state["raw_csv"] = raw
        if "df_hist" in st.session_state:
            del st.session_state["df_hist"]
        if "budgets" in st.session_state:
            del st.session_state["budgets"]
        st.success("CSV uploaded. Data refreshed.")
    elif "raw_csv" not in st.session_state:
        st.session_state["raw_csv"] = sample_csv
        st.info("Using built-in demo data. Upload your own CSV to replace it.")

    raw_csv = st.session_state["raw_csv"]
    sep = "\t"  # 强制使用 Tab 分隔符

    lines = raw_csv.split("\n")
    if len(lines) < 7:
        st.error("CSV must have at least 7 rows.")
        st.stop()

    cat_line = lines[1].split(sep)
    act_line = lines[2].split(sep)
    budget_line = lines[3].split(sep) if len(lines) > 3 else []

    if "budgets" not in st.session_state:
        st.session_state["budgets"] = {}
    activities = []
    for i in range(2, len(act_line)):
        if i < len(cat_line) and cat_line[i].strip() in ("B","V","M","E"):
            name = act_line[i].strip()
            cat = cat_line[i].strip()
            if name in st.session_state["budgets"]:
                budget = st.session_state["budgets"][name]
            else:
                try:
                    budget = float(budget_line[i].strip())
                except:
                    budget = 0
                st.session_state["budgets"][name] = budget
            activities.append({"name": name, "category": cat, "budget": budget})

    if not activities:
        st.error("No activities parsed.")
        st.stop()

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

    # ---------- 打卡界面 ----------
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

    # ---------- YTD 进度 ----------
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
                expected = round(budget * days_passed / 365, 1)
                actual_ratio = actual / budget if budget > 0 else 0
                if actual >= expected:
                    status = "On Track"
                elif actual >= expected * 0.8:
                    status = "Slightly Behind"
                else:
                    status = "Behind"
                progress_rows.append({
                    "Category": act["category"],
                    "Activity": name,
                    "Annual Target": int(round(budget)),
                    "Actual YTD": int(round(actual)),
                    "Expected YTD": int(round(expected)),
                    "Progress %": f"{actual_ratio:.1%}",
                    "Status": status
                })
            df_progress = pd.DataFrame(progress_rows)

            def status_color(val):
                if val == "On Track":
                    return "background-color: #d4edda; color: #155724"
                elif val == "Slightly Behind":
                    return "background-color: #fff3cd; color: #856404"
                else:
                    return "background-color: #f8d7da; color: #721c24"

            styled = df_progress.style.map(status_color, subset=["Status"])
            st.dataframe(styled, use_container_width=True)

            st.markdown("**Category Totals**")
            cat_summary = []
            for cat in categories:
                cat_acts = [a for a in activities if a["category"] == cat]
                if cat_acts:
                    total_budget = sum(a["budget"] for a in cat_acts)
                    total_actual = sum(ytd[ytd["activity"] == a["name"]]["achieved"].sum() for a in cat_acts)
                    expected_cat = total_budget * days_passed / 365
                    cat_status = "On Track" if total_actual >= expected_cat else "Behind"
                    cat_summary.append({
                        "Category": cat,
                        "Total Target": int(round(total_budget)),
                        "Actual": int(round(total_actual)),
                        "Expected": int(round(expected_cat)),
                        "Progress %": f"{total_actual / total_budget:.1%}" if total_budget > 0 else "0%",
                        "Status": cat_status
                    })
            df_cat = pd.DataFrame(cat_summary)
            styled_cat = df_cat.style.map(
                lambda val: "background-color: #d4edda; color: #155724" if val == "On Track" else "background-color: #f8d7da; color: #721c24",
                subset=["Status"]
            )
            st.dataframe(styled_cat, use_container_width=True)
        else:
            st.info("No data for current year yet.")
    else:
        st.info("No activity data loaded.")

    # ---------- 编辑 Budget ----------
    st.markdown("### ✏️ Edit Annual Budget")
    selected_activity = st.selectbox("Select activity to modify:", [a["name"] for a in activities])
    current_budget = next(a["budget"] for a in activities if a["name"] == selected_activity)
    new_budget = st.number_input(f"New budget for {selected_activity}", value=int(current_budget), min_value=0)
    if st.button("Update Budget"):
        st.session_state["budgets"][selected_activity] = float(new_budget)
        for a in activities:
            if a["name"] == selected_activity:
                a["budget"] = float(new_budget)
                break
        if not df_hist.empty:
            mask = df_hist["activity"] == selected_activity
            df_hist.loc[mask, "budget"] = float(new_budget)
            st.session_state["df_hist"] = df_hist
        st.success(f"Budget for '{selected_activity}' updated to {new_budget}.")
        st.rerun()

    # ---------- 导出 CSV（宽表格式）----------
    st.markdown("### 📥 Export Data")
    if not df_hist.empty:
        wide_df = df_hist.pivot_table(index='date', columns='activity', values='achieved', aggfunc='sum')
        wide_df = wide_df.reset_index().sort_values('date')
        csv_buffer = io.StringIO()
        wide_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download activity log as CSV (wide format)",
            data=csv_buffer.getvalue(),
            file_name=f"activity_log_{date.today()}.csv",
            mime="text/csv"
        )
    else:
        st.info("No data to export yet.")

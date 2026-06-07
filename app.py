import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date, datetime, timedelta, timezone
import yfinance as yf
import google.generativeai as genai
import requests
import feedparser
import streamlit.components.v1 as components
from supabase import create_client, Client
import time, io, random, csv, re

# ---------- 初始化 ----------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# Supabase 客户端
supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.set_page_config(page_title="Personal AI Agent", page_icon="🤖", layout="wide")
st.title("🤖 Personal AI Assistant – Full Demo")
today_date = date.today().strftime("%B %d, %Y")
st.caption(f"📅 {today_date}")

# ---------- 辅助绘图函数（不变）----------
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
        "Task 5: Product Hunt",
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
    if st.button("Fetch Latest News"):
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
                st.markdown("**📡 Sources (click to read full article)**")
                for src, title, link, pub in entries:
                    st.markdown(f"- **{src}**: [{title}]({link}) ({pub})")
            else:
                st.warning("Could not fetch any RSS feeds. Please try again later.")
    else:
        st.info("Click to fetch the latest STM publishing headlines.")

# ==================== TASK 4 ====================
elif task.startswith("Task 4"):
    st.subheader("🌍 Five Global Frontiers (Last 30 Days)")
    domain_rss = {
        "AGI / AI Agents": [
            ("Synced Review", "https://syncedreview.com/feed/"),
            ("AI News", "https://www.artificialintelligence-news.com/feed/"),
            ("MIT Technology Review", "https://www.technologyreview.com/feed/"),
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

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    if st.button("Fetch Latest Headlines"):
        with st.spinner("Fetching..."):
            for domain, feeds in domain_rss.items():
                st.markdown(f"### {domain}")
                found_any = False
                for src_name, url in feeds:
                    try:
                        feed = feedparser.parse(url)
                        count = 0
                        for entry in feed.entries:
                            pub_parsed = entry.get("published_parsed")
                            if pub_parsed:
                                pub_dt = datetime(*pub_parsed[:6], tzinfo=timezone.utc)
                                if pub_dt < cutoff:
                                    continue
                            found_any = True
                            st.markdown(f"- **{src_name}**: [{entry.title}]({entry.link}) ({entry.get('published','')})")
                            count += 1
                            if count >= 3:
                                break
                    except:
                        continue
                if not found_any:
                    st.caption("No recent headlines in the past 30 days.")
    else:
        st.info("Click to fetch headlines for each frontier area (past 30 days).")

# ==================== TASK 5: Product Hunt (top 7, no noise) ====================
elif task.startswith("Task 5"):
    st.subheader("🔥 Trending on Product Hunt")
    st.caption("Latest 7 products with description and time")

    def clean_ph_description(raw_html):
        text = re.sub(r'<[^>]+>', '', raw_html).strip()
        filtered_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if re.fullmatch(r'Discussion\s*', stripped, re.IGNORECASE):
                continue
            if re.fullmatch(r'Link\s*', stripped, re.IGNORECASE):
                continue
            if stripped == '|':
                continue
            filtered_lines.append(stripped)
        cleaned = '\n'.join(filtered_lines).strip()
        if cleaned.lower().replace(' ','').replace('\n','') == 'discussion|link':
            cleaned = ""
        if len(cleaned) > 200:
            cleaned = cleaned[:200] + "..."
        return cleaned

    ph_rss = "https://www.producthunt.com/feed"

    if st.button("Refresh Product Hunt"):
        with st.spinner("Fetching..."):
            try:
                feed = feedparser.parse(ph_rss)
                if feed.entries:
                    for i, entry in enumerate(feed.entries[:7]):
                        title = entry.title
                        link = entry.link
                        pub_time = entry.get("published", entry.get("updated", ""))
                        raw_desc = entry.get("summary", entry.get("description", ""))
                        clean_desc = clean_ph_description(raw_desc)

                        st.markdown(f"#### [{title}]({link})")
                        if pub_time:
                            st.caption(f"🕒 {pub_time}")
                        if clean_desc:
                            st.markdown(clean_desc)
                        if i < 6:
                            st.markdown("---")
                else:
                    st.warning("No products found.")
            except Exception as e:
                st.error(f"Error fetching Product Hunt: {e}")
    else:
        st.info("Click to fetch the latest Product Hunt products.")

# ==================== TASK 6 (Supabase 版) ====================
elif task.startswith("Task 6"):
    import csv, io
    from collections import defaultdict
    from datetime import date

    st.subheader("🏋️ Daily Activity Check-in & YTD Dashboard")
    st.caption("All changes are saved automatically. Data will not change on refresh.")

    # ---------- 硬编码活动定义（顺序与你原 CSV 一致）----------
    DEFAULT_ACTIVITIES = [
        {"name": "Food & Water & Self care", "category": "B", "budget": 330},
        {"name": "Energy, Focus and Emotion", "category": "B", "budget": 280},
        {"name": "Basic Exercise", "category": "B", "budget": 365},
        {"name": "Foot step", "category": "B", "budget": 200},
        {"name": ">.5hour MAG", "category": "M", "budget": 300},
        {"name": ">.5hour books", "category": "M", "budget": 300},
        {"name": "Meditation", "category": "V", "budget": 365},
        {"name": "Sketch", "category": "V", "budget": 365},
        {"name": "Life Admin", "category": "V", "budget": 53},
        {"name": "Learn sth new", "category": "M", "budget": 50},
        {"name": "Movie", "category": "M", "budget": 54},
        {"name": "Extra Exercise", "category": "B", "budget": 200},
        {"name": "Monthly review", "category": "V", "budget": 12},
        {"name": "Invest", "category": "M", "budget": 12},
        {"name": "Play/Exhibits/lecture", "category": "M", "budget": 25},
        {"name": "Meet new people", "category": "E", "budget": 25},
        {"name": "Deep exposure to nature", "category": "E", "budget": 15},
        {"name": "Quarterly Review", "category": "V", "budget": 4},   # 已去除尾部空格
        {"name": "CV & Jobs", "category": "M", "budget": 6},
        {"name": "Yearly Review + Plan", "category": "V", "budget": 2}, # 已去除尾部空格
        {"name": "Annual leave", "category": "V", "budget": 20},
        {"name": "Family Gathering", "category": "E", "budget": 20},
        {"name": "Health Check", "category": "B", "budget": 8},
        {"name": "Extensive Journey (km)", "category": "B", "budget": 7},
        {"name": "People", "category": "E", "budget": 300},
        {"name": "Give back", "category": "V", "budget": 100},
        {"name": "Engage. Get buy in. Inspire.", "category": "E", "budget": 225},
        {"name": "Seek for help", "category": "E", "budget": 200},
        {"name": "Confident & Brave", "category": "E", "budget": 120},
        {"name": "Storytelling/talkative", "category": "M", "budget": 100},
        {"name": "AI", "category": "M", "budget": 200},
        {"name": "Growth Mindset", "category": "V", "budget": 330},
    ]

    # ---------- 初始化活动到 Supabase（仅首次）----------
    def init_activities_to_db():
        for act in DEFAULT_ACTIVITIES:
            supabase.table("activities").upsert({
                "name": act["name"],
                "category": act["category"],
                "budget": act["budget"]
            }, on_conflict="name").execute()

    # ---------- 解析纯数据 CSV ----------
    def parse_data_csv(uploaded_file):
        """
        纯数据 CSV 格式：
          - 第 1 列：日期 (Jan 1)
          - 第 2~33 列：对应 32 个活动的完成情况（1 或空），列顺序必须与 DEFAULT_ACTIVITIES 一致
          - 无任何表头行
        """
        content = uploaded_file.read().decode("utf-8-sig")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if len(rows) < 1:
            st.error("CSV must contain at least one data row.")
            return None

        month_map = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
            "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
            "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
        }
        history = []
        current_year = date.today().year

        for row in rows:
            if not row or not row[0].strip():
                continue
            date_str = row[0].strip()
            parts = date_str.split()
            if len(parts) != 2:
                continue
            month_abbr, day_str = parts[0], parts[1]
            month = month_map.get(month_abbr)
            if not month:
                continue
            try:
                day = int(day_str)
                record_date = date(current_year, month, day)
            except (ValueError, TypeError):
                continue

            for idx in range(32):   # 共 32 个活动
                col = idx + 1
                if col >= len(row):
                    break
                raw = row[col].strip().upper()
                if raw in ("X", "1"):
                    achieved = 1.0
                elif raw.replace(".", "", 1).isdigit():
                    achieved = float(raw)
                else:
                    continue
                history.append({
                    "date": record_date,
                    "activity_name": DEFAULT_ACTIVITIES[idx]["name"],
                    "achieved": achieved,
                })
        return history

    def import_history(hist_list):
        if not hist_list:
            return
        res = supabase.table("activities").select("id, name").execute()
        name_to_id = {r["name"]: r["id"] for r in res.data} if res.data else {}
        records = []
        for rec in hist_list:
            act_id = name_to_id.get(rec["activity_name"])
            if act_id is None:
                continue
            records.append({
                "checkin_date": rec["date"].isoformat(),
                "activity_id": act_id,
                "achieved": rec["achieved"],
            })
        if records:
            supabase.table("checkins").upsert(records, on_conflict="checkin_date,activity_id").execute()

    # ---------- 保证活动已初始化 ----------
    df_act = supabase.table("activities").select("*").order("id").execute()
    if not df_act.data:
        init_activities_to_db()
        st.success("Activities initialised from built‑in list.")
        st.rerun()

    activities = df_act.data  # 从数据库读取，包含 id

    # ---------- 每日打卡 ----------
    st.markdown("### 📅 Select Date for Check-in")
    sel_date = st.date_input("Date", date.today())
    st.markdown(f"**{sel_date.strftime('%B %d, %Y')}**")

    checkin = (
        supabase.table("checkins")
        .select("activity_id, achieved")
        .eq("checkin_date", sel_date.isoformat())
        .execute()
    )
    day_map = {r["activity_id"]: r["achieved"] for r in checkin.data} if checkin.data else {}

    updated = {}
    total = 0
    cats = {"B": "🟢 Body", "V": "🟣 Value", "M": "🔵 Mental", "E": "🔴 Emotion"}

    for cat, label in cats.items():
        cat_acts = [a for a in activities if a["category"] == cat]
        if not cat_acts:
            continue
        st.markdown(f"**{label}**")
        cols = st.columns(len(cat_acts))
        for i, a in enumerate(cat_acts):
            val = day_map.get(a["id"], 0)
            checked = cols[i].checkbox(
                a["name"], value=(val > 0), key=f"{a['id']}_{sel_date}"
            )
            updated[a["id"]] = 1.0 if checked else 0.0
            if checked:
                total += 1

    st.markdown(f"**✅ Today: {total} / {len(activities)}**")

    if st.button("💾 Save Check-in"):
        supabase.table("checkins").delete().eq("checkin_date", sel_date.isoformat()).execute()
        rows_to_insert = [
            {"checkin_date": sel_date.isoformat(), "activity_id": a_id, "achieved": ach}
            for a_id, ach in updated.items()
            if ach > 0
        ]
        if rows_to_insert:
            supabase.table("checkins").insert(rows_to_insert).execute()
        st.success("Saved!")
        st.rerun()

    # ---------- YTD 进度 ----------
    st.markdown("### 📊 Year-to-Date Progress")

    year_start = date(date.today().year, 1, 1).isoformat()
    today_iso = date.today().isoformat()
    dp = min((date.today() - date(date.today().year, 1, 1)).days + 1, 365)

    res_ytd = (
        supabase.table("checkins")
        .select("checkin_date, activity_id, achieved")
        .gte("checkin_date", year_start)
        .lte("checkin_date", today_iso)
        .execute()
    )

    achieved_by_id = defaultdict(float)
    if res_ytd.data:
        for r in res_ytd.data:
            achieved_by_id[r["activity_id"]] += float(r["achieved"])

    prog_rows = []
    for act in activities:
        b = float(act["budget"])
        a = achieved_by_id.get(act["id"], 0.0)
        ex = round(b * dp / 365, 1)
        ratio = a / b if b > 0 else 0.0
        if a >= ex:
            status = "On Track"
        elif a >= ex * 0.8:
            status = "Slightly Behind"
        else:
            status = "Behind"
        prog_rows.append({
            "Category": act["category"],
            "Activity": act["name"],
            "Target": int(round(b)),
            "Actual": int(round(a)),
            "Expected": int(round(ex)),
            "Progress": f"{ratio:.1%}",
            "Status": status,
        })

    df_prog = pd.DataFrame(prog_rows)

    def color_status(s):
        if s == "On Track":
            return "background-color:#d4edda; color:#155724"
        if s == "Slightly Behind":
            return "background-color:#fff3cd; color:#856404"
        return "background-color:#f8d7da; color:#721c24"

    st.dataframe(
        df_prog.style.map(color_status, subset=["Status"]),
        use_container_width=True,
    )

    # 类别汇总
    cat_rows = []
    for cat, _ in cats.items():
        acts_c = [a for a in activities if a["category"] == cat]
        tb = sum(float(a["budget"]) for a in acts_c)
        ta = sum(achieved_by_id.get(a["id"], 0.0) for a in acts_c)
        ec = tb * dp / 365
        sts = "On Track" if ta >= ec else "Behind"
        cat_rows.append({
            "Category": cat,
            "Target": int(round(tb)),
            "Actual": int(round(ta)),
            "Expected": int(round(ec)),
            "Progress": f"{ta/tb:.1%}" if tb > 0 else "0%",
            "Status": sts,
        })

    df_cat = pd.DataFrame(cat_rows)
    st.dataframe(
        df_cat.style.map(
            lambda s: (
                "background-color:#d4edda; color:#155724"
                if s == "On Track"
                else "background-color:#f8d7da; color:#721c24"
            ),
            subset=["Status"],
        ),
        use_container_width=True,
    )

    # ---------- 编辑预算 ----------
    st.markdown("### ✏️ Edit Annual Budget")
    sel_act_name = st.selectbox("Activity", [a["name"] for a in activities])
    if sel_act_name:
        act_sel = next(a for a in activities if a["name"] == sel_act_name)
        new_b = st.number_input("New Budget", value=int(act_sel["budget"]), min_value=0)
        if st.button("Update Budget"):
            supabase.table("activities").update({"budget": new_b}).eq("id", act_sel["id"]).execute()
            st.success("Updated!")
            st.rerun()

    # ---------- 导入历史数据 ----------
    st.markdown("### 📤 Import History from Data-Only CSV")
    st.caption("Upload a CSV with only dates and 1/empty flags (no headers), columns must match the built‑in order.")
    with st.form("reimport"):
        up_hist = st.file_uploader("Upload Data CSV", type="csv")
        if st.form_submit_button("Import History") and up_hist is not None:
            hist = parse_data_csv(up_hist)
            if hist is not None:
                import_history(hist)
                st.success(f"Imported {len(hist)} records.")
                st.rerun()

    # ---------- 导出 ----------
    st.markdown("### 📥 Export Data")
    if st.button("Generate Download Link"):
        full_res = supabase.table("checkins").select("*").execute()
        if full_res.data:
            df_all = pd.DataFrame(full_res.data)
            df_all = df_all.merge(pd.DataFrame(activities)[["id", "name"]], left_on="activity_id", right_on="id")
            pivot = df_all.pivot_table(
                index="checkin_date", columns="name",
                values="achieved", aggfunc="sum", fill_value=0,
            ).reset_index()
            buf = io.StringIO()
            pivot.to_csv(buf, index=False)
            st.download_button(
                "Download CSV", buf.getvalue(),
                file_name=f"backup_{date.today()}.csv",
            )
        else:
            st.info("No data to export.")

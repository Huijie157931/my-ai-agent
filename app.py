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
    st.subheader("🏋️ Daily Activity Check-in & YTD Dashboard")
    st.caption("All changes are saved automatically to the cloud database.")

    # ---------- 辅助函数 ----------
    # 注意：不加任何缓存，保证数据实时
    def load_activities_from_db():
        res = supabase.table("activities").select("*").order("id").execute()
        if res.data:
            return pd.DataFrame(res.data)
        else:
            return pd.DataFrame(columns=["id", "name", "category", "budget"])

    def parse_csv_to_activities_and_history(uploaded_file):
        """返回 activities 列表 (dict) 和 history 列表 (dict)，名称已 trim"""
        content = uploaded_file.read().decode("utf-8-sig")
        reader = csv.reader(content.splitlines())
        lines = list(reader)
        if len(lines) < 4:
            st.error("CSV must have at least 4 rows (Day header, Category, Activity, Target).")
            return None, None

        cat_line = lines[1]
        act_line = lines[2]
        tgt_line = lines[3] if len(lines) > 3 else []

        activities = []
        for i in range(1, len(act_line)):
            cat = cat_line[i].strip() if i < len(cat_line) else ""
            name = act_line[i].strip() if i < len(act_line) else ""
            if cat in ("B","V","M","E") and name:
                budget_str = tgt_line[i].strip() if i < len(tgt_line) else "0"
                try:
                    budget = float(budget_str)
                except:
                    budget = 0.0
                activities.append({"name": name, "category": cat, "budget": budget})

        month_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
                     "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
        history = []
        for row in lines[4:]:
            if not row or len(row) < 2:
                continue
            date_str = row[0].strip()
            if not date_str:
                continue
            parts = date_str.split()
            if len(parts) != 2:
                continue
            month_abbr, day_str = parts[0], parts[1]
            month = month_map.get(month_abbr)
            if not month:
                continue
            try:
                day = int(day_str)
            except:
                continue
            record_date = date(date.today().year, month, day)
            for idx, act in enumerate(activities):
                col_idx = idx + 1
                if col_idx < len(row):
                    val = row[col_idx].strip().upper()
                    if val == "X" or val == "1":
                        achieved = 1.0
                    elif val.replace(".","",1).isdigit():
                        achieved = float(val)
                    else:
                        achieved = 0.0
                    if achieved > 0:
                        history.append({
                            "date": record_date,
                            "activity_name": act["name"],   # 已经 trim
                            "achieved": achieved
                        })
        return activities, history

    def init_activities_from_list(act_list):
        for act in act_list:
            supabase.table("activities").upsert({
                "name": act["name"],
                "category": act["category"],
                "budget": act["budget"]
            }, on_conflict="name").execute()
        # 清除可能存在的旧缓存（如果有）
        st.cache_data.clear()

    def import_history(history_list):
        if not history_list:
            return
        res = supabase.table("activities").select("id, name").execute()
        name_to_id = {r["name"]: r["id"] for r in res.data} if res.data else {}
        for rec in history_list:
            act_name = rec["activity_name"]
            if act_name not in name_to_id:
                continue
            act_id = name_to_id[act_name]
            supabase.table("checkins").upsert({
                "checkin_date": rec["date"].isoformat(),
                "activity_id": act_id,
                "achieved": rec["achieved"]
            }, on_conflict="checkin_date, activity_id").execute()

    # ---------- 加载当前活动 ----------
    df_activities = load_activities_from_db()
    if df_activities.empty:
        st.warning("No activities found in database. Please upload your CSV to initialize the tracker.")
        uploaded = st.file_uploader("Upload activity tracker CSV", type="csv", key="init_upload")
        if uploaded is not None:
            acts, hist = parse_csv_to_activities_and_history(uploaded)
            if acts is None:
                st.stop()
            init_activities_from_list(acts)
            import_history(hist)
            st.success("Activities and history imported! Refreshing...")
            st.rerun()
        st.stop()

    # 构建 activities 列表（带 id）
    activities = []
    for _, row in df_activities.iterrows():
        activities.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "budget": row["budget"]
        })

    # ---------- 打卡界面 ----------
    st.markdown("### 📅 Select Date for Check-in")
    selected_date = st.date_input("Pick a date", date.today())
    st.markdown(f"**Activities for {selected_date.strftime('%B %d, %Y')}**")

    checkin_res = supabase.table("checkins").select("activity_id, achieved").eq("checkin_date", selected_date.isoformat()).execute()
    day_map = {r["activity_id"]: r["achieved"] for r in checkin_res.data} if checkin_res.data else {}

    col_cat = {"B": "🟢 Body", "V": "🟣 Value", "M": "🔵 Mental", "E": "🔴 Emotion"}
    categories = ["B","V","M","E"]
    updated_entries = {}
    for cat in categories:
        st.markdown(f"**{col_cat[cat]}**")
        cat_acts = [a for a in activities if a["category"] == cat]
        cols = st.columns(len(cat_acts))
        for i, act in enumerate(cat_acts):
            current_val = day_map.get(act["id"], 0)
            checked = cols[i].checkbox(act["name"], value=(current_val > 0), key=f"{act['id']}_{selected_date}")
            updated_entries[act["id"]] = 1.0 if checked else 0.0

    if st.button("💾 Save Check-in"):
        for act_id, achieved in updated_entries.items():
            supabase.table("checkins").delete().eq("checkin_date", selected_date.isoformat()).eq("activity_id", act_id).execute()
            if achieved > 0:
                supabase.table("checkins").insert({
                    "checkin_date": selected_date.isoformat(),
                    "activity_id": act_id,
                    "achieved": achieved
                }).execute()
        st.success("Check-in saved! Dashboard updated.")
        st.rerun()

    # ---------- YTD 看板（无缓存，实时查询）----------
    st.markdown("### 📊 Year-to-Date Progress")
    year_start = date(date.today().year, 1, 1).isoformat()
    today_iso = date.today().isoformat()
    res = supabase.table("checkins").select("checkin_date, activity_id, achieved").gte("checkin_date", year_start).lte("checkin_date", today_iso).execute()
    if res.data:
        df_checkins = pd.DataFrame(res.data)
        df_checkins["checkin_date"] = pd.to_datetime(df_checkins["checkin_date"]).dt.date
        df_full = df_checkins.merge(df_activities, left_on="activity_id", right_on="id")
        actual = df_full.groupby(["activity_id", "name", "category", "budget"])["achieved"].sum().reset_index()
    else:
        actual = pd.DataFrame()

    if not actual.empty:
        days_passed = (date.today() - date(date.today().year, 1, 1)).days + 1
        progress_rows = []
        for _, row in actual.iterrows():
            budget = row["budget"]
            achieved = row["achieved"]
            expected = round(budget * days_passed / 365, 1)
            ratio = achieved / budget if budget > 0 else 0
            if achieved >= expected:
                status = "On Track"
            elif achieved >= expected * 0.8:
                status = "Slightly Behind"
            else:
                status = "Behind"
            progress_rows.append({
                "Category": row["category"],
                "Activity": row["name"],
                "Annual Target": int(round(budget)),
                "Actual YTD": int(round(achieved)),
                "Expected YTD": int(round(expected)),
                "Progress %": f"{ratio:.1%}",
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
            cat_df = actual[actual["category"] == cat]
            if not cat_df.empty:
                total_budget = cat_df["budget"].sum()
                total_actual = cat_df["achieved"].sum()
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
        if cat_summary:
            df_cat = pd.DataFrame(cat_summary)
            styled_cat = df_cat.style.map(
                lambda val: "background-color: #d4edda; color: #155724" if val == "On Track" else "background-color: #f8d7da; color: #721c24",
                subset=["Status"]
            )
            st.dataframe(styled_cat, use_container_width=True)
    else:
        st.info("No check-ins this year yet. Start by saving today's activities!")

    # ---------- 编辑 Budget ----------
    st.markdown("### ✏️ Edit Annual Budget")
    selected_act = st.selectbox("Select activity to modify:", [a["name"] for a in activities])
    if selected_act:
        act = next(a for a in activities if a["name"] == selected_act)
        new_budget = st.number_input(f"New budget for {selected_act}", value=int(act["budget"]), min_value=0)
        if st.button("Update Budget"):
            supabase.table("activities").update({"budget": new_budget}).eq("id", act["id"]).execute()
            st.success(f"Budget for '{selected_act}' updated to {new_budget}.")
            st.rerun()

    # ---------- 批量上传 / 更新历史 ----------
    st.markdown("### 📤 Upload CSV to Import / Update History")
    st.caption("Re-upload your CSV at any time to refresh past check-ins (duplicates will be updated, not added).")
    uploaded_history = st.file_uploader("Upload CSV", type="csv", key="history_upload")
    if uploaded_history is not None:
        acts_parsed, hist_parsed = parse_csv_to_activities_and_history(uploaded_history)
        if acts_parsed is None:
            st.stop()
        init_activities_from_list(acts_parsed)   # 确保活动存在
        import_history(hist_parsed)               # 导入所有历史
        st.success("History imported! Dashboard numbers should now match your CSV.")
        st.rerun()

    # ---------- 导出备份 ----------
    st.markdown("### 📥 Export Data")
    if st.button("Generate Download Link"):
        full_res = supabase.table("checkins").select("*").execute()
        if full_res.data:
            df_all = pd.DataFrame(full_res.data)
            df_all = df_all.merge(df_activities[["id", "name"]], left_on="activity_id", right_on="id")
            pivot = df_all.pivot_table(index="checkin_date", columns="name", values="achieved", aggfunc="sum", fill_value=0)
            pivot = pivot.reset_index()
            csv_buffer = io.StringIO()
            pivot.to_csv(csv_buffer, index=False)
            st.download_button("Download CSV", csv_buffer.getvalue(), file_name=f"activity_backup_{date.today()}.csv")
        else:
            st.info("No data to export.")

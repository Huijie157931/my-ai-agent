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
import time, io, random, csv, re

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
        "Task 5: Product Hunt",
        "Task 6: Daily Check-in & Dashboard (coming soon)",
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

# ==================== TASK 6 (placeholder) ====================
elif task.startswith("Task 6"):
    st.subheader("🏋️ Daily Check-in & Dashboard")
    st.info("We are currently refining this module. Please use your existing Numbers tracker for now. The full interactive version will be back soon!")

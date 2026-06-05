import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta
import yfinance as yf
import google.generativeai as genai
import requests
import feedparser
from io import StringIO
import streamlit.components.v1 as components
import time

# ---------- 初始化 ----------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="Personal AI Agent", page_icon="🤖", layout="wide")
st.title("🤖 Personal AI Assistant – Full Demo")

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
    if st.button("Generate Sentence"):
        with st.spinner("Generating..."):
            try:
                prompt = (
                    "You are a German language tutor. Based on today's world news, generate: "
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
                if english:
                    st.info(f"**🇬🇧 English:** {english}")
                if vocab:
                    st.markdown("**📖 Key Vocabulary:**")
                    for v in vocab:
                        st.markdown(f"- {v}")
                if grammar:
                    st.markdown(f"**📐 Grammar Note:** {grammar}")
                if german:
                    tts_html = f"""
                    <button onclick="speak()" style="padding:6px 12px; font-size:14px;">🔊 Listen to German</button>
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
            except Exception as e:
                st.error(f"API error: {e}")
    else:
        st.info("Click the button to generate a sentence based on today’s news.")

# ==================== TASK 2 ====================
elif task.startswith("Task 2"):
    st.subheader("📈 Major Stock Indices")
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
                info = yf.Ticker(ticker).history(period="1d")
                if not info.empty:
                    last = info['Close'].iloc[-1]
                    change = (last - info['Open'].iloc[0]) / info['Open'].iloc[0] * 100
                    data.append([name, round(last, 2), f"{change:.2f}%"])
                else:
                    data.append([name, "N/A", "-"])
            except:
                data.append([name, "Error", "-"])
        df = pd.DataFrame(data, columns=["Index", "Last Price", "Change"])
        st.table(df)
    else:
        st.info("Click to fetch real-time stock data.")

# ==================== TASK 3 ====================
elif task.startswith("Task 3"):
    st.subheader("🔬 STM Publishing Industry News")
    urls = [
        "https://scholarlykitchen.sspnet.org/",
        "https://retractionwatch.com/",
        "https://www.stm-assoc.org/",
        "https://www.alpsp.org/",
        "https://publicationethics.org/",
        "https://www.sspnet.org/",
    ]
    if st.button("Summarize Latest News"):
        with st.spinner("Fetching and summarizing..."):
            snippets = []
            for url in urls[:3]:  # 只抓前3个避免超时
                try:
                    resp = requests.get(url, timeout=8)
                    # 简单截取前2000字符
                    text = resp.text[:2000]
                    snippets.append(f"Source: {url}\n{text}")
                except:
                    continue
            if snippets:
                combined = "\n\n".join(snippets)
                prompt = f"Summarize the latest STM publishing news in 3 bullet points based on the following website snippets:\n{combined}"
                try:
                    resp = model.generate_content(prompt)
                    st.write(resp.text)
                except Exception as e:
                    st.error(f"Gemini API error: {e}")
            else:
                st.warning("Could not fetch any data. Try again later.")
    else:
        st.info("Click to generate a summary of STM industry news.")

# ==================== TASK 4 ====================
elif task.startswith("Task 4"):
    st.subheader("🌍 Five Global Frontiers")
    if st.button("Get Latest Updates"):
        with st.spinner("Generating..."):
            prompt = """
            Summarize the most important, authoritative updates across these 5 areas.
            Only include real milestones, data, and official announcements.
            1. AGI / Artificial General Intelligence (agents, long-term memory, reasoning, real-world deployment)
            2. Global Order Restructuring (geopolitics, multipolarity, major power dynamics)
            3. Space Exploration (manned moon landing, lunar bases, commercial space)
            4. Controlled Nuclear Fusion (experiments, energy gain, engineering progress)
            5. Life Science / Anti-Aging + Brain-Computer Interface (clinical trials, longevity, BCI implants)
            Provide one paragraph per area.
            """
            try:
                resp = model.generate_content(prompt)
                st.write(resp.text)
            except Exception as e:
                st.error(f"API error: {e}")
    else:
        st.info("Click to get a summary of global frontier breakthroughs.")

# ==================== TASK 5 ====================
elif task.startswith("Task 5"):
    st.subheader("💡 Tech Trends & Podcast Recommendation")
    if st.button("Analyze & Recommend"):
        with st.spinner("Analyzing..."):
            # 尝试抓取 Product Hunt 首页
            try:
                r = requests.get("https://www.producthunt.com/", timeout=8)
                ph_text = r.text[:2000]
            except:
                ph_text = "Product Hunt data unavailable."

            prompt = f"""
            Based on today's tech trends (Product Hunt snippet: {ph_text}) and the following podcast list:
            - The a16z Show
            - Azeem Azhar’s Exponential View
            - Hard Fork
            - Latent Space: The AI Engineer Podcast
            - No Priors AI
            Summarize today's top tech/AI trend in one sentence, and recommend one podcast episode from the list that best matches today's theme. Explain your choice.
            """
            try:
                resp = model.generate_content(prompt)
                st.write(resp.text)
            except Exception as e:
                st.error(f"API error: {e}")
    else:
        st.info("Click to get tech trend and podcast recommendation.")

# ==================== TASK 6 ====================
elif task.startswith("Task 6"):
    st.subheader("🏋️ Daily Activity Check-in & YTD Dashboard")

    # ---- 1. 上传 CSV ----
    uploaded = st.file_uploader("Upload your activity tracker CSV (must contain header rows with categories and activity names)", type="csv")
    if uploaded is not None:
        # 读取整个CSV，保留原始行
        raw = uploaded.read().decode("utf-8")
        st.session_state["raw_csv"] = raw
        st.success("CSV uploaded and parsed.")
    elif "raw_csv" not in st.session_state:
        # 使用内置示例数据（你的CSV的前几行）
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
        st.session_state["raw_csv"] = sample_csv
        st.info("Using built-in demo data. Upload your own CSV to replace it.")

    # ---- 2. 解析CSV ----
    csv_data = st.session_state["raw_csv"]
    lines = csv_data.split("\n")
    # 找到类别行和活动行（第2行和第3行，索引1和2）
    # 第一行是合并表头，第二行是MEVB Category，第三行是Activity，第四行是BUDGET，第五行是YTD，第六行是vs YTD，后面是每日数据
    if len(lines) < 7:
        st.error("CSV format incorrect: need at least 7 rows.")
        st.stop()
    # 跳过第一行（Month,Day等），读取第二行作为类别映射
    cat_line = lines[1].split("\t")
    act_line = lines[2].split("\t")
    budget_line = lines[3].split("\t")
    ytd_line = lines[4].split("\t")
    # 前两列是 Month, Day，从第三列开始是活动
    activities = []
    for i in range(2, len(act_line)):
        if i < len(cat_line) and cat_line[i].strip() in ("B","V","M","E"):
            name = act_line[i].strip()
            cat = cat_line[i].strip()
            budget = float(budget_line[i].strip()) if budget_line[i].strip() else 0
            activities.append({"name": name, "category": cat, "budget": budget})
    # 解析每日记录（从第6行开始，即索引5及之后）
    records = []
    for row_idx in range(5, len(lines)):
        cols = lines[row_idx].split("\t")
        if len(cols) < 3:
            continue
        month_str = cols[0].strip()
        day_str = cols[1].strip()
        if month_str == "" or day_str == "":
            continue
        # 简单转换月份缩写到数字
        month_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
        month = month_map.get(month_str, 1)
        try:
            day = int(day_str)
        except:
            continue
        record_date = date(2025, month, day)  # 假设年份为2025，可调整
        for idx, act in enumerate(activities):
            col_idx = idx + 2  # 在行中的位置
            if col_idx < len(cols):
                val = cols[col_idx].strip()
                if val == "X":
                    achieved = 1
                elif val.replace(".","",1).isdigit():
                    achieved = float(val)
                else:
                    achieved = 0
                records.append({
                    "date": record_date,
                    "activity": act["name"],
                    "category": act["category"],
                    "achieved": achieved,
                    "budget": act["budget"]
                })

    if not activities:
        st.error("No activities parsed. Check CSV format.")
        st.stop()

    df_hist = pd.DataFrame(records) if records else pd.DataFrame(columns=["date","activity","category","achieved","budget"])

    # ---- 3. 今日打卡界面 ----
    st.markdown("### ✅ Today's Check-in")
    today = date.today()
    col_cat = {"B": "🟢 Body", "V": "🟣 Value", "M": "🔵 Mental", "E": "🔴 Emotion"}
    # 获取今日已有记录
    today_recs = df_hist[df_hist["date"] == today] if not df_hist.empty else pd.DataFrame()
    # 展示所有活动，按类别分组
    categories = ["B","V","M","E"]
    new_entries = []
    for cat in categories:
        st.markdown(f"**{col_cat.get(cat, cat)}**")
        cat_acts = [a for a in activities if a["category"] == cat]
        cols = st.columns(len(cat_acts))
        for i, act in enumerate(cat_acts):
            # 查看今天是否已有记录
            if not today_recs.empty and act["name"] in today_recs["activity"].values:
                already = today_recs[today_recs["activity"] == act["name"]]["achieved"].values[0]
                cols[i].checkbox(act["name"], value=(already>0), key=f"{act['name']}_{today}", disabled=True)
            else:
                checked = cols[i].checkbox(act["name"], key=f"{act['name']}_{today}")
                if checked:
                    new_entries.append({"date": today, "activity": act["name"], "category": cat, "achieved": 1, "budget": act["budget"]})
    if st.button("💾 Save Today's Check-in"):
        if new_entries:
            new_df = pd.DataFrame(new_entries)
            df_hist = pd.concat([df_hist, new_df], ignore_index=True)
            st.session_state["updated_df"] = df_hist
            st.success(f"Saved {len(new_entries)} activities.")
            # 更新CSV缓存（简单合并，不覆盖原始文件）
            st.experimental_rerun()
        else:
            st.warning("No new activities selected.")

    # ---- 4. YTD 看板 ----
    st.markdown("### 📊 Year-to-Date Performance")
    if not df_hist.empty:
        df_hist["date"] = pd.to_datetime(df_hist["date"])
        ytd = df_hist[df_hist["date"].dt.year == today.year]
        if not ytd.empty:
            # 汇总每个类别每日完成次数
            daily_cat = ytd.groupby(["date","category"])["achieved"].sum().unstack(fill_value=0)
            cumulative = daily_cat.cumsum()
            # 计算目标：每日每个活动的目标为 budget（假设 budget 是年总次数，则每日目标 = budget/365）
            # 简化处理：用 budget 列求和 / 365 作为每日预期
            targets = {}
            for act in activities:
                cat = act["category"]
                daily_target = act["budget"] / 365
                targets[cat] = targets.get(cat, 0) + daily_target
            # 累积目标
            days_passed = (today - date(today.year,1,1)).days + 1
            cumulative_target = {cat: t * days_passed for cat, t in targets.items()}

            # 画图
            fig, ax = plt.subplots(figsize=(10,5))
            colors = {"B":"green", "V":"purple", "M":"blue", "E":"red"}
            for cat in categories:
                if cat in cumulative.columns:
                    ax.plot(cumulative.index, cumulative[cat], label=cat, color=colors.get(cat,"black"), marker='.')
            ax.set_title("YTD Cumulative Completed Activities")
            ax.legend()
            st.pyplot(fig)

            # 落后提醒
            st.markdown("### ⚠️ Progress vs Target")
            for cat in categories:
                if cat in cumulative.columns:
                    actual = cumulative[cat].iloc[-1] if not cumulative.empty else 0
                    target = cumulative_target.get(cat, 0)
                    shortfall = target - actual
                    if shortfall > 2:
                        st.warning(f"**{cat} ({col_cat.get(cat)})** is behind by {shortfall:.0f} units. Consider increasing effort.")
                    else:
                        st.info(f"**{cat}** on track (actual {actual:.1f} / target {target:.1f})")
        else:
            st.info("No data for current year yet.")
    else:
        st.info("No historical data loaded.")

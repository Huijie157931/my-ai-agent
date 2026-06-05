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
import time, io, random, csv, base64, json

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

# ---------- URL 持久化工具 ----------
def save_state_to_url():
    """将当前状态编码到 URL 中，实现永久保存"""
    state = {
        "template": st.session_state.get("activity_template", []),
        "budgets": st.session_state.get("budgets", {}),
        "df_hist": st.session_state.get("df_hist", pd.DataFrame()).to_dict(orient="records") if not st.session_state.get("df_hist", pd.DataFrame()).empty else []
    }
    # 将日期转换为字符串以便 JSON 序列化
    for record in state["df_hist"]:
        if isinstance(record.get("date"), date):
            record["date"] = record["date"].isoformat()
    json_str = json.dumps(state)
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    st.query_params["data"] = encoded

def load_state_from_url():
    """从 URL 参数中恢复状态"""
    encoded = st.query_params.get("data")
    if encoded:
        try:
            json_str = base64.urlsafe_b64decode(encoded.encode()).decode()
            state = json.loads(json_str)
            # 恢复模板
            if state.get("template"):
                st.session_state["activity_template"] = state["template"]
            if state.get("budgets"):
                st.session_state["budgets"] = state["budgets"]
            # 恢复历史记录
            if state.get("df_hist"):
                df = pd.DataFrame(state["df_hist"])
                if not df.empty:
                    df["date"] = pd.to_datetime(df["date"]).dt.date
                st.session_state["df_hist"] = df
            return True
        except:
            pass
    return False

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
    # （Task 1 代码保持不变，请直接粘贴你之前稳定运行的版本）
    # 为节省篇幅，此处省略，实际使用时需保留原有代码
    pass

# ==================== TASK 2 ====================
elif task.startswith("Task 2"):
    # （Task 2 代码保持不变）
    pass

# ==================== TASK 3 ====================
elif task.startswith("Task 3"):
    # （Task 3 代码保持不变）
    pass

# ==================== TASK 4 ====================
elif task.startswith("Task 4"):
    # （Task 4 代码保持不变）
    pass

# ==================== TASK 5 ====================
elif task.startswith("Task 5"):
    # （Task 5 代码保持不变）
    pass

# ==================== TASK 6 ====================
elif task.startswith("Task 6"):
    st.subheader("🏋️ Daily Activity Check-in & YTD Dashboard")
    st.caption(f"{today_date}")

    # ---------- 辅助：加载模板 + 历史数据 ----------
    def load_template_and_history(raw_csv):
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(raw_csv[:1024])
            reader = csv.reader(raw_csv.splitlines(), dialect)
        except:
            reader = csv.reader(raw_csv.splitlines(), delimiter='\t')
        lines = list(reader)
        if len(lines) < 4:
            return [], {}, []
        cat_line = lines[1]
        act_line = lines[2]
        budget_line = lines[3] if len(lines) > 3 else []
        template = []
        budgets = {}
        start = next((i for i, c in enumerate(cat_line) if c.strip() in ("B","V","M","E")), 2)
        for i in range(start, len(act_line)):
            cat = cat_line[i].strip() if i < len(cat_line) else ""
            if cat in ("B","V","M","E"):
                name = act_line[i].strip()
                if not name:
                    continue
                try:
                    budget = float(budget_line[i].strip()) if i < len(budget_line) and budget_line[i].strip() else 0
                except:
                    budget = 0
                template.append({"name": name, "category": cat})
                budgets[name] = budget

        # 解析历史数据
        month_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
        history = []
        for row in lines[5:]:
            if not row or len(row) < 3:
                continue
            month_str = row[0].strip()
            day_str = row[1].strip()
            if not month_str or not day_str:
                continue
            month = month_map.get(month_str)
            if not month:
                continue
            try:
                day = int(day_str)
            except:
                continue
            record_date = date(date.today().year, month, day)
            for idx, act in enumerate(template):
                col_idx = start + idx
                if col_idx < len(row):
                    val = row[col_idx].strip()
                    if val.upper() == "X":
                        achieved = 1.0
                    elif val.replace(".","",1).isdigit():
                        achieved = float(val)
                    else:
                        achieved = 0.0
                    history.append({
                        "date": record_date,
                        "activity": act["name"],
                        "category": act["category"],
                        "achieved": achieved,
                        "budget": budgets[act["name"]]
                    })
        return template, budgets, history

    # 内置演示数据
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

    # 初始化 session_state（优先从 URL 恢复）
    if "activity_template" not in st.session_state:
        st.session_state["activity_template"] = []
    if "budgets" not in st.session_state:
        st.session_state["budgets"] = {}
    if "df_hist" not in st.session_state:
        st.session_state["df_hist"] = pd.DataFrame()

    # 尝试从 URL 恢复数据
    url_loaded = load_state_from_url()
    if url_loaded:
        st.sidebar.success("✅ Data loaded from saved link.")

    # 上传模板 CSV
    uploaded = st.file_uploader("Upload activity tracker CSV (template)", type="csv")
    if uploaded is not None:
        raw = uploaded.read().decode("utf-8-sig")
        st.session_state["raw_csv"] = raw
        template, budgets, hist = load_template_and_history(raw)
        st.session_state["activity_template"] = template
        st.session_state["budgets"] = budgets
        df_hist = pd.DataFrame(hist) if hist else pd.DataFrame()
        if not df_hist.empty:
            df_hist["date"] = pd.to_datetime(df_hist["date"]).dt.date
        st.session_state["df_hist"] = df_hist
        save_state_to_url()
        st.success("New template loaded and saved to URL.")
    elif not st.session_state["activity_template"] and not url_loaded:
        # 首次加载演示数据
        template, budgets, hist = load_template_and_history(sample_csv)
        st.session_state["activity_template"] = template
        st.session_state["budgets"] = budgets
        st.session_state["raw_csv"] = sample_csv
        df_hist = pd.DataFrame(hist)
        if not df_hist.empty:
            df_hist["date"] = pd.to_datetime(df_hist["date"]).dt.date
        st.session_state["df_hist"] = df_hist
        save_state_to_url()
        st.info("Using built-in demo template. Your progress is automatically saved in the link.")

    # 确保从 session_state 取最新数据
    activity_template = st.session_state["activity_template"]
    budgets = st.session_state["budgets"]
    df_hist = st.session_state["df_hist"]

    # 构建活动列表（实时使用最新 budget）
    activities = []
    for t in activity_template:
        name = t["name"]
        cat = t["category"]
        budget = budgets.get(name, 0)
        activities.append({"name": name, "category": cat, "budget": budget})

    # ---------- 侧边栏备份/恢复 ----------
    st.sidebar.markdown("---")
    st.sidebar.caption("💾 Backup & Restore")
    if not df_hist.empty:
        backup_csv = df_hist.to_csv(index=False)
        st.sidebar.download_button(
            "Download Backup",
            backup_csv,
            file_name=f"activity_backup_{date.today()}.csv"
        )
    else:
        st.sidebar.info("No data to back up yet.")
    backup_file = st.sidebar.file_uploader("Restore from backup CSV", type="csv", key="restore")
    if backup_file is not None:
        try:
            restored = pd.read_csv(backup_file)
            if {"date","activity","category","achieved","budget"}.issubset(restored.columns):
                restored["date"] = pd.to_datetime(restored["date"]).dt.date
                st.session_state["df_hist"] = restored
                save_state_to_url()
                st.success("Backup restored! Data saved to URL.")
                st.rerun()
            else:
                st.sidebar.error("Invalid backup format.")
        except:
            st.sidebar.error("Error reading backup file.")

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
        save_state_to_url()
        st.success("Check-in saved! Your progress is now in the URL (bookmark this page).")
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
        st.info("No activity data loaded. Start checking in or restore a backup.")

    # ---------- 编辑 Budget ----------
    st.markdown("### ✏️ Edit Annual Budget")
    if activities:
        selected_activity = st.selectbox("Select activity to modify:", [a["name"] for a in activities])
        current_budget = next((a["budget"] for a in activities if a["name"] == selected_activity), 0)
        new_budget = st.number_input(f"New budget for {selected_activity}", value=int(current_budget), min_value=0)
        if st.button("Update Budget"):
            st.session_state["budgets"][selected_activity] = float(new_budget)
            if not df_hist.empty:
                mask = df_hist["activity"] == selected_activity
                df_hist.loc[mask, "budget"] = float(new_budget)
                st.session_state["df_hist"] = df_hist
            save_state_to_url()
            st.success(f"Budget updated to {new_budget}.")
            st.rerun()

    # ---------- 导出当前进度 ----------
    st.markdown("### 📥 Export Current Data")
    if not df_hist.empty:
        wide_df = df_hist.pivot_table(index='date', columns='activity', values='achieved', aggfunc='sum')
        wide_df = wide_df.reset_index().sort_values('date')
        csv_buffer = io.StringIO()
        wide_df.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download activity log (wide format)",
            csv_buffer.getvalue(),
            file_name=f"activity_log_{date.today()}.csv"
        )
    else:
        st.info("No data to export yet.")

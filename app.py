elif task.startswith("Task 6"):
    st.subheader("🏋️ Daily Activity Check-in & YTD Dashboard")
    st.caption(f"{today_date}")

    # ---------- 样本 CSV ----------
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

    # ---------- 文件上传 ----------
    uploaded = st.file_uploader("Upload your activity tracker CSV", type="csv")
    if uploaded is not None:
        raw = uploaded.read().decode("utf-8")
        st.session_state["raw_csv"] = raw
        # 清除旧历史，强制重新解析
        if "df_hist" in st.session_state:
            del st.session_state["df_hist"]
        if "budgets" in st.session_state:
            del st.session_state["budgets"]
        st.success("CSV uploaded. Data refreshed.")
    elif "raw_csv" not in st.session_state:
        st.session_state["raw_csv"] = sample_csv
        st.info("Using built-in demo data. Upload your own CSV to replace it.")

    raw_csv = st.session_state["raw_csv"]
    # ---- 修复：强制使用制表符分隔 ----
    sep = "\t"

    lines = raw_csv.split("\n")
    if len(lines) < 7:
        st.error("CSV must have at least 7 rows.")
        st.stop()

    cat_line = lines[1].split(sep)
    act_line = lines[2].split(sep)
    budget_line = lines[3].split(sep) if len(lines) > 3 else []

    # 解析活动列表，优先使用已修改的 budgets
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

    # ---------- 初始化历史记录 ----------
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

            # 大类进度
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

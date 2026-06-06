# ==================== TASK 5: Product Hunt（前7个，去噪音）====================
elif task.startswith("Task 5"):
    st.subheader("🔥 Trending on Product Hunt")
    st.caption("Latest 7 products with description and time")

    # 专用清洗函数（已经彻底删除 Discussion|Link）
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
                    # 改为前7个产品
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
                        # 最后一个不加分割线
                        if i < 6:
                            st.markdown("---")
                else:
                    st.warning("No products found.")
            except Exception as e:
                st.error(f"Error fetching Product Hunt: {e}")
    else:
        st.info("Click to fetch the latest Product Hunt products.")

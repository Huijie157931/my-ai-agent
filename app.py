import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="Personal AI Agent", page_icon="🤖")
st.title("🤖 Personal AI Assistant – Interview Demo")

task = st.sidebar.selectbox(
    "Choose a task",
    ["Task 1: German News Sentence", "Task 6: Daily Check-in"]
)

if task.startswith("Task 1"):
    st.subheader("📰 Today’s German Learning Sentence")
    if st.button("Generate Sentence"):
        with st.spinner("Generating..."):
            try:
                # 让 Gemini 一次性返回德语、英文翻译、单词解释（逐词）、语法解释
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

                # 解析回复
                lines = text.split("\n")
                german = ""
                english = ""
                vocab = []
                grammar = ""
                mode = None

                for line in lines:
                    line = line.strip()
                    if line.startswith("German:"):
                        german = line.replace("German:", "").strip()
                    elif line.startswith("English:"):
                        english = line.replace("English:", "").strip()
                    elif line.startswith("Grammar:"):
                        grammar = line.replace("Grammar:", "").strip()
                    elif line.startswith("Vocabulary:") or line == "Vocabulary:":
                        mode = "vocab"
                    elif mode == "vocab" and line.startswith("-"):
                        vocab.append(line.lstrip("- ").strip())

                # 展示德语和英文
                if german:
                    st.success(f"**🇩🇪 German:** {german}")
                if english:
                    st.info(f"**🇬🇧 English:** {english}")

                # 展示逐个词汇
                if vocab:
                    st.markdown("**📖 Key Vocabulary:**")
                    for item in vocab:
                        st.markdown(f"- {item}")

                # 展示语法解释
                if grammar:
                    st.markdown(f"**📐 Grammar Note:** {grammar}")

                # 语音朗读按钮（德语）
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

elif task.startswith("Task 6"):
    st.subheader("🏋️ Daily Activity Check-in")
    st.write("Full check-in and dashboard module will be added in the next version.")

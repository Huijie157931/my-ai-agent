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
                # 让 Gemini 一次性返回德语 + 英文翻译 + 词汇解释
                prompt = (
                    "You are a German language tutor. Based on today's world news, generate: "
                    "1) A single German sentence at A2 level. "
                    "2) Its English translation. "
                    "3) A brief explanation of key vocabulary (in English). "
                    "Format your response exactly like this:\n"
                    "German: <sentence>\nEnglish: <translation>\nVocab: <explanation>"
                )
                response = model.generate_content(prompt)
                text = response.text

                # 解析回复
                lines = text.split("\n")
                german = ""
                english = ""
                vocab = ""
                for line in lines:
                    if line.startswith("German:"):
                        german = line.replace("German:", "").strip()
                    elif line.startswith("English:"):
                        english = line.replace("English:", "").strip()
                    elif line.startswith("Vocab:"):
                        vocab = line.replace("Vocab:", "").strip()

                if german:
                    st.success(f"**🇩🇪 German:** {german}")
                if english:
                    st.info(f"**🇬🇧 English:** {english}")
                if vocab:
                    st.markdown(f"**📖 Vocabulary:** {vocab}")

                # 语音朗读按钮（使用浏览器内置 TTS）
                if german:
                    # 构造一个简单的 HTML，点击按钮后调用 SpeechSynthesis
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

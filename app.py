import streamlit as st
import google.generativeai as genai

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
                prompt = (
                    "Based on today's world news, create a single German sentence suitable for A2 learners. "
                    "Then briefly explain the key vocabulary in English."
                )
                response = model.generate_content(prompt)
                st.success(response.text)
            except Exception as e:
                st.error(f"API error: {e}")
    else:
        st.info("Click the button to generate a sentence based on today’s news.")

elif task.startswith("Task 6"):
    st.subheader("🏋️ Daily Activity Check-in")
    st.write("Full check-in and dashboard module will be added in the next version.")

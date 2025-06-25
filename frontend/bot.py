import streamlit as st
import requests
import os

API_URL = os.environ.get("RAG_API_URL", "http://localhost:8000/chat")

st.title("📖 Uni-Q")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if query := st.chat_input("Ask a question about your documents..."):
    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message("user").write(query)
    with st.spinner("🤔 Thinking..."):
        try:
            response = requests.post(API_URL, json={"question": query})
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "No answer returned.")
                sources = data.get("sources", [])
                if sources:
                    answer += "\n\n📚 **Sources:**\n"
                    for src in sources:
                        file_name = src.get("file_name")
                        if file_name:
                            pdf_url = f"/documents/{file_name}"
                            answer += f"- {file_name} [View PDF]({pdf_url})\n"
            else:
                answer = f"❌ Error: {response.text}"
        except Exception as e:
            answer = f"❌ Error: {e}"
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").write(answer)
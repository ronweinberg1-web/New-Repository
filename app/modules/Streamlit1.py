import streamlit as st

from dotenv import load_dotenv
import os



from main import orchestrate_conversation_with_memory

st.title("Welcome to Best Company to work for")
st.write("Experiment with OpenAI HR Chatbot")

# User input
prompt = st.chat_input("Your prompt")

if prompt:
    
    session_id = "user77"
# Turn 3
    response=orchestrate_conversation_with_memory(prompt, session_id=session_id)
# ...keep calling per turn as needed...

    st.chat_message("user").write(prompt)
    
    st.chat_message("assistant").write(response)
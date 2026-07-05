import streamlit as st

from dotenv import load_dotenv
import os

#from my_module_chat_conv import ChatGPT_Conversation

from main import orchestrate_conversation_with_memory

st.title("Welcome to Best Company to work for")
st.write("Experiment with OpenAI HR Chatbot")

# Initialize chat history (no system message)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):  # st.chat_message(msg["role"]).write(msg["content"])  --  Alternatively -- instead "with"
        st.markdown(msg["content"])

# User input
prompt = st.chat_input("Your prompt")

if prompt:
    
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):  # st.chat_message("user").write(user_input)  --  Alternatively -- instead "with"
        st.markdown(prompt)

    session_id = "user77"
# Turn 3
    response=orchestrate_conversation_with_memory(prompt, session_id=session_id)
# ...keep calling per turn as needed...

# Add assistant reply to history and display it
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):  # st.chat_message("assistant").write(reply)  --  Alternatively -- instead "with"
        st.markdown(response)
    

#    st.chat_message("user").write(prompt)
    
#    st.chat_message("assistant").write(response)
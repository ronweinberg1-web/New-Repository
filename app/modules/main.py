from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser  # Added for cleaner string output
from langchain_classic.agents import create_openai_tools_agent, AgentExecutor

from embedding.emb import get_job_info, build_index
from Scheduling.sched import get_nearest_dates
from Exit.exit_agent import ExitDecisionAgent

from datetime import date

import os
from dotenv import load_dotenv


# 1. Load the variables from the .env file at the very start of the app runtime
load_dotenv()

# 2. Extract the key securely from the system environment
API_KEY = os.getenv("OPENAI_API_KEY")

build_index()   # run once at startup

# Define the tools
jobtool = [get_job_info]
datetool = [get_nearest_dates]

llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0)

# --- GLOBAL AGENT INITIALIZATION ---
# Instantiating the exit agent once here prevents reprocessing the JSON file on every turn.
exit_agent = ExitDecisionAgent(dataset_path="sms_conversations.json", api_key=API_KEY)

# --- 1. MAIN ROUTER (Converted from an Agent to a standard Chain) ---

with open("main.txt", "r", encoding="utf-8") as f:
    main_instructions = f.read()

main_prompt = ChatPromptTemplate.from_messages([
    ("system", main_instructions),
    MessagesPlaceholder(variable_name="history"),
    ("user", "{input}")
])

# A simple chain is faster and won't infinite-loop when no tools are present
main_chain = main_prompt | llm | StrOutputParser()

# Memory store for user sessions
store = {}
def get_history(session_id):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# Wrap the main chain with memory
main_agent_with_memory = RunnableWithMessageHistory(
    main_chain,
    get_session_history=get_history,
    input_messages_key="input",
    history_messages_key="history"
)

# --- ADVISOR AGENT ---
with open("schedule.txt", "r", encoding="utf-8") as f:
    sched_instructions = f.read()

advisor_prompt = ChatPromptTemplate.from_messages([
    ("system", sched_instructions + "\n\nCRITICAL CONTEXT: Today's current real-world date is {current_date}. Use this exact date as the baseline for any relative calculations like 'tomorrow', 'next week', or 'yesterday'."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),                              
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

advisor_agent = create_openai_tools_agent(llm, tools=datetool, prompt=advisor_prompt)
advisor_executor = AgentExecutor(agent=advisor_agent, tools=datetool)
# used for testing, verbose=True)

# --- JOB AGENT ---
with open("info.txt", "r", encoding="utf-8") as f:
    job_instructions = f.read()

job_prompt = ChatPromptTemplate.from_messages([
    ("system",  job_instructions),
    MessagesPlaceholder(variable_name="chat_history"), 
    ("user", "{input}"),                               
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

job_agent = create_openai_tools_agent(llm, tools=jobtool, prompt=job_prompt)
job_executor = AgentExecutor(agent=job_agent, tools=jobtool)
# used for testing, verbose=True)



# --- 4. ORCHESTRATION ---
def orchestrate_conversation_with_memory(user_input, session_id="user1"):
    """
    Handles one turn of user input for the main agent (with memory),
    and if needed, passes the full memory/history to the advisor/job agent.
    """
    
    # 1. Fetch current session history object
    session_history = get_history(session_id)
    
    # Main chain directly outputs a string now because of StrOutputParser()
    main_output = main_agent_with_memory.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}}
    )
    print("Main Agent:", main_output)
    print("\n")
    
    all_messages = store[session_id].messages
    
    # Slice the history array:
    # - The last message [-1] is the main agent's routing response ("I will check...")
    # - The second to last [-2] is the current user_input
    # - everything before [:-2] is the true past chat history
    # If there are fewer than 2 messages, use all available messages
    if all_messages[-1] in ["I will check available slots for you", "I will check Python Developer Job Info for you"]:
        past_history = all_messages[:-2]
    else:
        past_history = all_messages
            
    # Convert the array of message objects into a unified text transcript
    history_transcript = ""
    for msg in past_history:
        speaker = "User" if msg.type == "human" else "Agent"
        history_transcript += f"{speaker}: {msg.content}\n"

    # Pass the clean string to your exit agent
    verdict = exit_agent.evaluate(history_transcript)

    # Safe check for NoneType to prevent crash if OpenAI structured output validation fails
    if verdict is None:
        print("[Supervisor Error]: Failed to parse routing response. Defaulting to 'continue'.")
        decision_str = "continue"
    else:
        print(f"[Supervisor Reason]: {verdict.reasoning}")
        print(f"[Routing Decision ]: {verdict.decision.upper()}")
        decision_str = verdict.decision.lower()
        print(f"Decision!!!: {decision_str}")
        
    # 2. Check for End phase
    if decision_str == "end":
        return "Thank you for your time. The conversation has ended."        

    # 3. Check for Scheduling phase
    if decision_str == "schedule" or "I will check available slots for you" in main_output:
        advisor_response = advisor_executor.invoke({
            "input": user_input, 
            "chat_history": past_history,
            "current_date": date.today().strftime("%Y-%m-%d")
        })["output"]
        
        # CRITICAL FIX: Overwrite the main agent message in memory with the actual advisor response
        # This deletes the placeholder "I will check slots" and saves what was actually said to the user
        if len(session_history.messages) >= 1:
            session_history.messages[-1].content = advisor_response
            
        return advisor_response
        
    # 4. Check for Job info phase
    if "I will check Python Developer Job Info for you" in main_output:
        job_response = job_executor.invoke({
            "input": user_input, 
            "chat_history": past_history
        })["output"]
        return job_response

    return main_output
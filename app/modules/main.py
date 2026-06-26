from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser  # Added for cleaner string output
from langchain_classic.agents import create_openai_tools_agent, AgentExecutor

from embedding.emb import get_job_info, build_index
from Scheduling.sched import get_nearest_dates

from datetime import date


build_index()   # run once at startup

# Define the tools
jobtool = [get_job_info]
datetool = [get_nearest_dates]

llm = ChatOpenAI(model="gpt-4o-2024-11-20", temperature=0)

# --- 1. MAIN ROUTER (Converted from an Agent to a standard Chain) ---
main_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an assistant in a company. If the user wants to schedule an appointment, respond: "
     "'I will check available slots for you.' Otherwise, answer normally."
     "If the user asks about Python Developer Job Description, respond:"
     "'I will check Python Developer Job Info for you.'"
     "Otherwise, answer normally."),
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

# --- 2. ADVISOR AGENT ---
with open("schedule.txt", "r", encoding="utf-8") as f:
    instructions = f.read()

advisor_prompt = ChatPromptTemplate.from_messages([
    ("system", instructions + "\n\nCRITICAL CONTEXT: Today's current real-world date is {current_date}. Use this exact date as the baseline for any relative calculations like 'tomorrow', 'next week', or 'yesterday'."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),                              
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

advisor_agent = create_openai_tools_agent(llm, tools=datetool, prompt=advisor_prompt)
advisor_executor = AgentExecutor(agent=advisor_agent, tools=datetool, verbose=True)

# --- 3. JOB AGENT ---
job_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a job advisor. Extract any preferred information from the full conversation. "
     "Then, answer the user specific questions regarding the Python Developer job."
     "You can use the jobtool provided."
     "If no relevant info is found, say there is no info about the job."),
    MessagesPlaceholder(variable_name="chat_history"), 
    ("user", "{input}"),                               
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

job_agent = create_openai_tools_agent(llm, tools=jobtool, prompt=job_prompt)
job_executor = AgentExecutor(agent=job_agent, tools=jobtool, verbose=True)


# --- 4. ORCHESTRATION ---
def orchestrate_conversation_with_memory(user_input, session_id="user1"):
    """
    Handles one turn of user input for the main agent (with memory),
    and if needed, passes the full memory/history to the advisor/job agent.
    """
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
    past_history = all_messages[:-2]

    # If scheduling is detected
    if "I will check available slots for you" in main_output:
        advisor_response = advisor_executor.invoke({
            "input": user_input, 
            "chat_history": past_history,
            "current_date": date.today().strftime("%Y-%m-%d")
        })["output"]
        return advisor_response
        
    # If job info is detected
    if "I will check Python Developer Job Info for you" in main_output:
        job_response = job_executor.invoke({
            "input": user_input, 
            "chat_history": past_history
        })["output"]
        return job_response

    return main_output
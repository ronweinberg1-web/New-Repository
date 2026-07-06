import json
from typing import List, Dict, Any

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

def build_few_shot_context(json_file_path: str) -> str:
    """
    Parses the multi-turn recruiter JSON file and builds a structured,
    readable few-shot context block for the LLM.
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        conversations = json.load(f)
        
    formatted_examples = []
    
    for conv in conversations:
        history = []
        for i, turn in enumerate(conv['turns']):
            speaker = turn['speaker']
            text = turn['text']
            history.append(f"{speaker.capitalize()}: {text}")
            
            # Whenever the candidate speaks, look ahead to see what the recruiter did next.
            # That next recruiter label is our true target state.
            if speaker == 'candidate' and (i + 1) < len(conv['turns']):
                next_turn = conv['turns'][i + 1]
                if next_turn['speaker'] == 'recruiter':
                    example_str = (
                        f"--- Conversation Snippet ---\n"
                        f"Transcript:\n" + "\n".join(history) + "\n"
                        f"Correct Decision Tag: {next_turn['label']}\n"
                    )
                    formatted_examples.append(example_str)
                    
    return "\n".join(formatted_examples)

from typing import Literal
from pydantic import BaseModel
from openai import OpenAI

# 1. Define strict output layout matching your dataset's targets
class RoutingVerdict(BaseModel):
    reasoning: str
    decision: Literal["continue", "schedule", "end"]

class RoutingResponse(BaseModel):
    reasoning: str = Field(description="Explanation for the decision")
    decision: str = Field(description="Must be one of: 'continue', 'schedule', or 'end'")

class ExitDecisionAgent:
    def __init__(self, dataset_path, api_key):
        # Initialize LLM with structured output constraint
        base_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
        self.structured_llm = base_llm.with_structured_output(RoutingResponse)
        
    def evaluate(self, transcript: str):
        if not transcript.strip():
            # Handle empty transcript gracefully
            return RoutingResponse(reasoning="Initial turn", decision="continue")

        with open("exit.txt", "r", encoding="utf-8") as f:
            exit_instructions = f.read()
            
        system_prompt = exit_instructions
        
        try:
            # This returns a reliable RoutingResponse Pydantic object directly
            result = self.structured_llm.invoke([
                ("system", system_prompt),
                ("user", f"Transcript:\n{transcript}")
            ])
            return result
        except Exception as e:
            print(f"Underlying model error: {e}")
            return None
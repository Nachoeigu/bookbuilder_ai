import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from langgraph.graph import END
from src.utils import State

def should_go_to_brainstorming_writer(state: State):
    if state.get('instructor_documents', '') == '':
        return "human_feedback"
    else:
        return "brainstorming_writer"
    
def should_continue_with_critique(state: State):
    if state['critique_brainstorming_messages'] == []: 
        return "brainstorming_critique"
    elif state['is_approved_brainstorming'] == True:
        return END
    else:
        return "brainstorming_critique"
    
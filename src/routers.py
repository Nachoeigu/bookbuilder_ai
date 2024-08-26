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
    if state.get('is_plan_approved', None) is None: 
        return "brainstorming_critique"
    elif state['is_plan_approved'] == True:
        return "writer"
    else:
        return "brainstorming_critique"
    
def has_writer_ended_book(state: State):
    if state['current_chapter'] == len(state['chapters_summaries']):
        return END
    else:
        return "writer"


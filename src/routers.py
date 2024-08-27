import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from langgraph.graph import END
from src.utils import State
from typing import Literal

def should_go_to_brainstorming_writer(state: State) -> Literal['human_feedback','brainstorming_writer']:
    if state.get('instructor_documents', '') == '':
        return "human_feedback"
    else:
        return "brainstorming_writer"
    
def should_continue_with_critique(state: State) -> Literal['brainstorming_critique','writer']:
    if state.get('is_plan_approved', None) is None: 
        return "brainstorming_critique"
    elif state['is_plan_approved'] == True:
        return "writer"
    else:
        return "brainstorming_critique"


def has_writer_ended_book(state: State) -> Literal[END, 'writer']:

    if (state['current_chapter'] == len(state['chapters_summaries']))&(state['is_chapter_approved'] == True):
        return END
    else:
        return "writer"

    

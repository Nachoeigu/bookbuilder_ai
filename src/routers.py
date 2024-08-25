import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from langgraph.graph import END
from src.utils import State

def should_go_to_writer(state: State):
    if state.get('instructor_documents','') == '':
        return "read_human_feedback"
    else:
        return END
    
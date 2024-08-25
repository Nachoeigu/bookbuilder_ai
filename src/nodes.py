import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from langchain_openai.chat_models import ChatOpenAI
from src.constants import INSTRUCTOR_PROMPT
from src.utils import State, DocumentationReady
from langchain_core.messages import SystemMessage


def get_clear_instructions(state: State):
    model = ChatOpenAI(model = 'gpt-4o-mini', temperature = 0)
    model = model.bind_tools([DocumentationReady])
    messages = [SystemMessage(content = INSTRUCTOR_PROMPT)] + state['user_instructor_messages']
    
    reply = model.invoke(messages)

    if len(reply.tool_calls) == 0:
        return {'user_instructor_messages': [reply]}
    else:
        return {
            'instructor_documents': reply.tool_calls[0]['args']
            }

def read_human_feedback(state: State):
    pass
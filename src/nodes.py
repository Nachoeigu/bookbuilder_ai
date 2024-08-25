import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from langchain_openai.chat_models import ChatOpenAI
from src.constants import INSTRUCTOR_PROMPT, BRAINSTORMING_PROMPT, CRITIQUE_PROMPT
from src.utils import State, DocumentationReady, ApprovedBrainstormingIdea
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


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

def brainstorming_critique(state: State):
    model = ChatOpenAI(model = 'gpt-4o-mini', temperature = 0.5)
    model = model.bind_tools([ApprovedBrainstormingIdea])
    
    if state['critique_brainstorming_messages'] == []:
        user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()])
        messages = [
         SystemMessage(content = CRITIQUE_PROMPT.format(user_requirements=user_requirements)),
         HumanMessage(content = state['writer_brainstorming_messages'][-1].content)
        ]

        output = model.invoke(messages)

    else:
        messages = state['critique_brainstorming_messages'] + [HumanMessage(content = state['writer_brainstorming_messages'][-1].content)]
        output = model.invoke(messages)

    if len(output.tool_calls) == 0:
        return {'is_approved_brainstorming': False,
                'critique_brainstorming_messages': [output]}
    
    else:
        return {'is_approved_brainstorming': True}



def making_writer_brainstorming(state: State):
    #model = ChatGoogleGenerativeAI(model = 'gemini-1.5-pro-exp-0801', temperature = 1)
    model = ChatGroq(temperature=1, model_name="llama-3.1-70b-versatile")
    user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()])
    system_prompt = SystemMessage(content = BRAINSTORMING_PROMPT.format(user_requirements=user_requirements))
    if state['is_approved_brainstorming'] is None:
        output = model.invoke([system_prompt] + [HumanMessage(content = "Start it...")])
        return {'writer_brainstorming_messages': [output]}
    
    else:
        if state['is_approved_brainstorming'] == False:
            output = model.invoke(state['writer_brainstorming_messages'] + [HumanMessage(content=f"Based on this critique, adjust your entire idea and return it again with the adjustments: {state['critique_brainstorming_messages'][-1].content}")])

            return {'writer_brainstorming_messages': [output]}

        else:
            output = model.invoke(state['writer_brainstorming_messages'] + [HumanMessage(content="Based on all this improvements, returns the final and complete version of your idea")])

            return {'writer_brainstorming_messages': [output]}


import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

import operator
from typing import Annotated, List, Literal, TypedDict
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_core.messages import RemoveMessage, AIMessage, AnyMessage,HumanMessage, SystemMessage
from langchain_openai.chat_models import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.pydantic_v1 import BaseModel, Field
from src.constants import INSTRUCTOR_PROMPT

class WriterStructuredOutput(BaseModel):
    """The way the writer should answer a request"""
    content: str = Field(description = "The content inside the developed chapter.")
    chapter_summary: str = Field(description = "A summary in 2 paragraphs about the story in the chapter")
    chapter_name: str = Field(description = "The name of the developed chapter.")

class DocumentationReady(TypedDict):
    requirements: str = Field(description = "A highly detailed description to the writer about the requirements should consider while developing the book")
    total_pages: int = Field(description = "Number of total pages the book should contain")
    chapter_length: Literal['long','medium','short'] = Field(description = "The length of each chapter in the book.")

class State(TypedDict):
    content: Annotated[List[str], operator.add]
    user_instructor_messages: Annotated[List[AnyMessage], operator.add]
    instructor_documents: DocumentationReady
    prologue: str
    title: str
    total_pages: int
    chapter_length: Literal['long','medium','short']

class GraphInput(TypedDict):
    user_instructor_messages: List[HumanMessage]

class GraphOutput(TypedDict):
    content: str
    prologue: str
    book_title: str

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

def should_go_to_writer(state: State):
    if state.get('instructor_documents','') == '':
        return "read_human_feedback"
    else:
        return END
    
def read_human_feedback(state: State):
    pass




# model = ChatGoogleGenerativeAI(model = 'gemini-1.5-pro-exp-0801', temperature = 0.8)
# model_with_structured_output = model.with_structured_output(WriterStructuredOutput)
# messages = [
#     SystemMessage(content = ""),
# ]
# def generate_content(state: State):
#     if state['content'] == []:
#         model_with_structured_output
#     else:

workflow = StateGraph(State, input = GraphInput)
workflow.add_node("get_clear_instructions", get_clear_instructions)
workflow.add_node("read_human_feedback", read_human_feedback)
workflow.add_conditional_edges(
    "get_clear_instructions",
    should_go_to_writer
)
workflow.add_edge("read_human_feedback","get_clear_instructions")
workflow.set_entry_point("get_clear_instructions")

app = workflow.compile(interrupt_before=['read_human_feedback'])

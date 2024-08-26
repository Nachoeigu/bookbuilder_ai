import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

import operator
from typing import Annotated, List, Literal, TypedDict, Dict
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai.chat_models import ChatOpenAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from src.constants import *
import time
import re

class GraphConfig(TypedDict):
    language: Literal['english', 'spanish']
    instructor_model: Literal['openai', 'google','meta']
    brainstormer_model: Literal['openai','google','meta']
    critique_model: Literal['openai', 'google','meta']
    writer_model: Literal['openai', 'google','meta']
    


class BrainstormingStructuredOutput(BaseModel):
    story_overview: str = Field(description = "Provide a highly detailed overview of the story that highlight the introduction, development and ending.")
    characters: str = Field(description = "Enumerate the main characters in the story and a description of each of them.")
    writing_style: str = Field(description = "The style and way the writter should write")
    introduction: str = Field(description = "Display how will be the introduction shown.")
    development: str = Field(description = "The well developed middle of the story with its conflict and resolution.")
    ending: str = Field(description = "Explain how you will end the story and provide the excellent join you make between development into ending.")
    chapters_summaries: List[str] = Field(description = "Each element in the list is each chapter of the book with a highly detailed summary of what happen on it. Each summary MUST HAVE a length of 5 sentences minimum.")
    total_paragraphs_per_chapter: int = Field(description = "The number of paragraphs in each chapter. Assuming each paragraph is around 5 sentences.")
    book_name: str = Field(description = "The name of the book")
    book_prologue: str = Field(description = "The prologue of the book. It should catch the attention of the audience heavily.")


class WriterStructuredOutput(BaseModel):
    """The way the writer should answer a request"""
    content: str = Field(description = "The content inside the developed chapter.")
    chapter_name: str = Field(description = "The name of the developed chapter.")

class DocumentationReady(TypedDict):
    requirements: str = Field(description = "A highly detailed description to the writer about the requirements should consider while developing the book")

class ApprovedBrainstormingIdea(BaseModel):
    feedback: str = Field(description = "If the grade is below 9, provide feedback of improvements. Otherwise, empty string.")
    grade: int = Field(ge=0, le=10, description = "The overall grade assigned to the draft idea based on the criterias. It should be allign with the feedback.")

class State(TypedDict):
    content: Annotated[List[str], operator.add]
    chapter_names: Annotated[List[str], operator.add]
    writer_memory: Annotated[List[AnyMessage], operator.add]
    user_instructor_messages: Annotated[List[AnyMessage], operator.add]
    plannified_messages: Annotated[List[AnyMessage], operator.add]
    critique_brainstorming_messages: Annotated[List[AnyMessage], operator.add]
    is_plan_approved: bool
    current_chapter: int
    instructor_documents: DocumentationReady
    book_prologue: str
    book_title: str
    plannified_intro: str
    plannified_development: str
    plannified_ending: str
    characters: str
    writing_style: str
    story_overview: str
    chapters_summaries: List[str]
    total_paragraphs_per_chapter: int



class GraphInput(TypedDict):
    user_instructor_messages: List[HumanMessage]

class GraphOutput(TypedDict):
    book_title: str
    book_prologue: str
    content: Annotated[List[str], operator.add]
    chapter_names: Annotated[List[str], operator.add]

def _get_language(config: GraphConfig, prompt_case:Literal['INSTRUCTOR_PROMPT', 'BRAINSTORMING_PROMPT','CRITIQUE_PROMPT','WRITER_PROMPT'], default:Literal['spanish','english']='english'):
    language = config['configurable'].get('language', default)
    if language == 'spanish':
        return globals()[f"{prompt_case}_ES"]
    elif language == 'english':
        return globals()[prompt_case]

def _get_model(config: GraphConfig, key:Literal['instructor_model','brainstormer_model','critique_model','writer_model'], temperature:float, default:Literal['openai', 'google','meta']='openai'):
    model = config['configurable'].get(key, default)
    if model == "openai":
        return ChatOpenAI(temperature=temperature, model="gpt-4o-mini")
    elif model == "google":
        return ChatGoogleGenerativeAI(temperature=temperature, model="gemini-1.5-pro-exp-0801")
    elif model == 'meta':
        return ChatGroq(temperature=temperature, model="llama-3.1-70b-versatile")
    else:
        raise ValueError
    
def check_chapter(msg_content:str):
    """
    This function validates that the generated chapter contains a minimum size (of at least 5 paragraphs)
    """
    if len(msg_content.split('\n\n')) >= 4:
        return True
    else:
        return False
    

def adding_delay_for_rate_limits(model):
    """
    Google API and Groq API free plans has limit rates so we avoid reaching them
    """
    try:
        model_name = model.model_name
    except:
        model_name = model.model
    if re.search('gemini|llama', model_name) is not None:
        time.sleep(6)

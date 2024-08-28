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
from langchain_aws.chat_models import ChatBedrock
from src.constants import *
import time
import re

class GraphConfig(TypedDict):
    """
    Initial configuration to trigger the AI system.

    Attributes:
    - language: The language in which the system prompts will be generated. Options are 'english' or 'spanish'.
    - critiques_in_loop: Set to False if you only want a single critique per writing. Set to True if you want multiple critique iterations until the writing is approved.
    - instructor_model: Select the model for the instructor node. Options include 'openai', 'google', 'meta', or 'amazon'.
    - brainstormer_model: Select the model for the brainstormer node. Options include 'openai', 'google', 'meta', or 'amazon'.
    - critique_model: Select the model for the critique node. Options include 'openai', 'google', 'meta', or 'amazon'.
    - writer_model: Select the model for the writer node. Options include 'openai', 'google', 'meta', or 'amazon'.
    - writing_reviewer_model: Select the model for the writing reviewer node. Options include 'openai', 'google', 'meta', or 'amazon'.
    """
    language: Literal['english', 'spanish']
    critiques_in_loop: bool
    instructor_model: Literal['openai', 'google','meta','amazon']
    brainstormer_model: Literal['openai','google','meta', 'amazon']
    critique_model: Literal['openai', 'google','meta','amazon']
    writer_model: Literal['openai', 'google','meta','amazon']
    writing_reviewer_model: Literal['openai', 'google','meta','amazon']

class BrainstormingStructuredOutput(BaseModel):
    """
    This tool defines and structures the proposed idea in detailed sections.  
    """
    story_overview: str = Field(description = "Provide a highly detailed overview of the narrative that includes a strong introduction, a well-developed middle, and a satisfying conclusion.")
    characters: str = Field(description = "Describe the characters of the story, in one paragraph each one.")
    writing_style: str = Field(description = "The style and tone the writer should consider while developing the book.")
    introduction: str = Field(description="Introduces the story by setting up the first key events, main characters, and important themes or conflicts. This part should smoothly lead into the middle of the story.")
    development: str = Field(description="Continues from the introduction by exploring more events, growing the conflicts, and deepening the characters and themes. This middle part should build up and naturally move towards the ending.")
    ending: str = Field(description="Wraps up the story by resolving conflicts, finishing the main events, and completing the characters' journeys. This part should connect back to the introduction and development to give a complete ending.")
    chapters_summaries: List[str] = Field(description = "Provide a list where each element is the summary of each chapter. Each one should contain a detailed description of what happen on it. Each summary MUST HAVE a length of 5 sentences minimum.")
    total_paragraphs_per_chapter: int = Field(description = "The number of paragraphs in each chapter. Assuming each paragraph is around 5 sentences.")
    book_name: str = Field(description="The title of the book. It should be unique, creative, and original.")
    book_prologue: str = Field(description="The opening section of the book. It should be engaging and designed to strongly capture the audience's attention.")


class WriterStructuredOutput(BaseModel):
    """This tool structures the way the writer invention"""
    content: str = Field(description = "The content inside the developed chapter.")
    chapter_name: str = Field(description = "The name of the developed chapter.")

class DocumentationReady(TypedDict):
    """
    This tool confirms that the Instructor has the necessary information to pass to the writer
    """
    requirements: str = Field(description = "A highly detailed description to the writer about the requirements should consider while developing the book")

class ApprovedWriterChapter(TypedDict):
    """
    This tool approves the chapter and its content based on your analysis.
    """
    is_approved: bool = Field(description = 'This tool should be invoke only if the chapter is quite well  and it could be defined as MVP, based on your analysis.')

class CritiqueWriterChapter(TypedDict):
    """
    This tool retrieves critiques and highlight improvements over the developed chapter.
    """
    feedback: str = Field(description = 'Provide highly detailed suggestions and points of improvements based on your analysis.')

class ApprovedBrainstormingIdea(BaseModel):
    """
    This tool evaluates if the brainstormed idea is quite good or need further improvements
    """
    grade: int = Field(description = "The overall grade (in scale from 0 to 10) assigned to the draft idea based on the criterias. It should be allign with the feedback.")
    feedback: str = Field(description = "Provide highly detailed feedback and improvements in case it is not approved.")

class State(TypedDict):
    content: Annotated[List[str], operator.add]
    content_of_approved_chapters: Annotated[List[str], operator.add]
    chapter_names_of_approved_chapters: Annotated[List[str], operator.add]
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
    writing_reviewer_memory: Annotated[List[AnyMessage], operator.add]
    is_chapter_approved: bool



class GraphInput(TypedDict):
    """
    The initial message that starts the AI system
    """
    user_instructor_messages: List[HumanMessage]

class GraphOutput(TypedDict):
    """
    The output of the AI System
    """
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

def _get_model(config: GraphConfig, key:Literal['instructor_model','brainstormer_model','critique_model','writer_model'], temperature:float, default:Literal['openai', 'google','meta','amazon']='openai'):
    model = config['configurable'].get(key, default)
    if model == "openai":
        return ChatOpenAI(temperature=temperature, model="gpt-4o-mini")
    elif model == "google":
        return ChatGoogleGenerativeAI(temperature=temperature, model="gemini-1.5-pro-exp-0801")
    elif model == 'meta':
        return ChatGroq(temperature=temperature, model="llama-3.1-70b-versatile")
    elif model == 'amazon':
        return ChatBedrock(model_id = 'anthropic.claude-3-sonnet-20240229-v1:0', model_kwargs = {'temperature':temperature})
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
        try:
            model_name = model.model
        except:
            model_name = model.model_id
    if re.search('gemini|llama', model_name) is not None:
        time.sleep(6)

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
    - language: The language in which the system prompts will be generated. eg: 'english', 'spanish', etc...
    - critiques_in_loop: Set to False if you only want a single critique per writing. Set to True if you want multiple critique iterations until the writing is approved.
    - instructor_model: Select the model for the instructor node. Options include 'openai', 'google', 'meta', or 'amazon'.
    - brainstormer_idea_model: Select the model for the brainstormer idea node. Options include 'openai', 'google', 'meta', or 'amazon'.
    - brainstormer_critique_model: Select the model for the brainstormer critique node. Options include 'openai', 'google', 'meta', or 'amazon'.

    - writer_model: Select the model for the writer node. Options include 'openai', 'google', 'meta', or 'amazon'.
    - writing_reviewer_model: Select the model for the writing reviewer node. Options include 'openai', 'google', 'meta', or 'amazon'.
    """
    language: Literal['english', 'spanish', 'portuguese', 'poland', 'french', 'german', 'italian', 'dutch','swedish', 'norwegian', 'danish', 'finnish', 'russian', 'chinese', 'japanese', 'korean','arabic', 'turkish', 'greek', 'hebrew']
    critiques_in_loop: bool
    instructor_model: Literal['openai', 'google','meta','amazon']
    brainstormer_idea_model: Literal['openai','google','meta', 'amazon']
    brainstormer_critique_model: Literal['openai','google','meta', 'amazon'] 
    writer_model: Literal['openai', 'google','meta','amazon']
    writing_reviewer_model: Literal['openai', 'google','meta','amazon']
    translator_model: Literal['openai', 'google','meta','amazon']
    n_chapters: int

class BrainstormingNarrativeStructuredOutput(BaseModel):
    """
    This tool defines the narrative of the story based on the original set up. 
    """
    chapters_summaries: List[str] = Field(description = "A list where each element is the summary of each chapter. Each one should contain a detailed description of what happen on it. Each summary MUST HAVE a length of 5 sentences minimum.")

class BrainstormingStructuredOutput(BaseModel):
    """
    This tool defines and structures the proposed idea in detailed sections.  
    """
    story_overview: str = Field(description="A highly detailed overview of the narrative that includes a strong introduction, a well-developed middle, and a satisfying conclusion.")
    characters: str = Field(description = "Describe the characters of the story, in one paragraph each one.  Describe their background, motivations, and situations along the at the story journey. Be as detailed as possible.")
    writing_style: str = Field(description="The style and tone the writer should consider while developing the book.")
    book_name: str = Field(description="The title of the book. It should be unique, creative, and original.")
    book_prologue: str = Field(description="The opening section of the book. It should be engaging and designed to strongly capture the audience's attention.")
    context_setting: str = Field(description="Describe the time, place, and atmosphere where the story takes place. Include any necessary background information relevant to the story.")
    inciting_incident: str = Field(description="Describe the event that disrupts the protagonist’s normal life and initiates the main plot. It should set up the central conflict or challenge.")
    themes_conflicts_intro: str = Field(description="Introduce the central themes and conflicts that will be explored in the story. Mention any internal or external conflicts.")
    transition_to_development: str = Field(description="Ensure a smooth transition from the Introduction to the Development stage. Detail how the story moves from the setup to the rising action.")
    rising_action: str = Field(description="Describe the key events that increase tension and advance the central conflict. Include challenges that force the protagonist to grow or change.")
    subplots: str = Field(description="Outline any secondary storylines that complement the main plot. Describe how these subplots intersect with the main plot.")
    midpoint: str = Field(description="Identify a significant event that alters the direction of the story or escalates the conflict. It could be a turning point or a major revelation.")
    climax_build_up: str = Field(description="Detail the events leading up to the climax. Explain how these events escalate the conflict and set the stage for the story's peak moment.")
    climax: str = Field(description="Describe the decisive moment where the main conflict reaches its peak. Explain how the protagonist confronts the greatest challenge or opposition.")
    falling_action: str = Field(description="Outline the immediate aftermath of the climax. Describe how the resolution of the main conflict affects the characters and world.")
    resolution: str = Field(description="Tie up any remaining loose ends and conclude the story, reflecting on themes and character changes.")
    epilogue: str = Field(description="Provide a final reflection or glimpse into the characters' future, showing the long-term impact of the story.")

class TranslatorStructuredOutput(BaseModel):
    """ This tool structures the way the translator should reply """
    translated_content: str = Field(description = "Your final translation from the original content provided")
    translated_chapter_name: str = Field(description = "Translation of the chapter name.")

class TranslatorSpecialCaseStructuredOutput(BaseModel):
    """ This tool structures the way the translator should reply """
    translated_book_name: str = Field(description = "The translation of the book name")
    translated_book_prologue: str = Field(description= "The translation of the prologue of the book")

class WriterStructuredOutput(BaseModel):
    """This tool structures the way the writer invention"""
    content: str = Field(description = "The content inside the developed chapter, avoid putting the name of the chapter here.")
    chapter_name: str = Field(description = "The name of the developed chapter.")

class DocumentationReady(TypedDict):
    """
    This tool confirms that the Instructor has the necessary information to pass to the writer
    """
    topic: str = Field(description="The required topic defined for the user, with high details")
    target_audience: str = Field(description = "The required target audience the book should point to,  with high details")
    genre: str = Field(description="Genre of the book to develop,  with high details")
    writing_style: str = Field(description="The desired tone, style or book reference the writing should respect, with high details")
    additional_requirements: str = Field(description = "More requirements beyond topic, target audience, genre and writing style.")


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
    translated_content: Annotated[List[str], operator.add]
    translated_chapter_names: Annotated[List[str], operator.add]
    content_of_approved_chapters: Annotated[List[str], operator.add]
    chapter_names_of_approved_chapters: Annotated[List[str], operator.add]
    chapter_names: Annotated[List[str], operator.add]
    writer_memory: Annotated[List[AnyMessage], operator.add]
    translator_memory: Annotated[List[AnyMessage], operator.add]
    user_instructor_messages: Annotated[List[AnyMessage], operator.add]
    plannified_messages: Annotated[List[AnyMessage], operator.add]
    critique_brainstorming_messages: Annotated[List[AnyMessage], operator.add]
    is_general_story_plan_approved: bool
    is_detailed_story_plan_approved: bool
    instructor_model: str
    brainstorming_writer_model: str
    brainstorming_critique_model: str
    writer_model: str
    reviewer_model: str
    translator_model: str
    translated_book_prologue: str
    translated_book_name: str
    current_chapter: int
    translated_current_chapter: int    
    instructor_documents: DocumentationReady
    book_prologue: str
    book_title: str
    plannified_context_setting: str
    plannified_inciting_incident: str
    plannified_themes_conflicts_intro: str
    plannified_transition_to_development: str
    plannified_rising_action: str
    plannified_subplots: str
    plannified_midpoint: str
    plannified_climax_build_up: str
    plannified_climax: str
    plannified_falling_action: str
    plannified_resolution: str
    plannified_epilogue: str
    plannified_chapters_summaries: List[str]
    plannified_chapters_messages: Annotated[List[AnyMessage], operator.add]
    characters: str
    writing_style: str
    story_overview: str
    writing_reviewer_memory: Annotated[List[AnyMessage], operator.add]
    is_chapter_approved: bool
    english_version_book: str
    translated_version_book: str
    critique_brainstorming_narrative_messages: Annotated[List[AnyMessage], operator.add]




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

def _get_model(config: GraphConfig, key:Literal['instructor_model','brainstormer_idea_model','brainstormer_critique_model','writer_model','writing_reviewer_model','translator_model'], temperature:float, default:Literal['openai', 'google','meta','amazon']='openai'):
    model = config['configurable'].get(key, default)
    if model == "openai":
        return ChatOpenAI(temperature=temperature, model="gpt-4o-mini")
    elif model == "google":
        return ChatGoogleGenerativeAI(temperature=temperature, model="gemini-1.5-pro-exp-0801")
    elif model == 'meta':
        return ChatGroq(temperature=temperature, model="llama-3.1-70b-versatile")
    elif model == 'amazon':
        return ChatBedrock(model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0', model_kwargs = {'temperature':temperature})
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
    
def retrieve_model_name(model):
    try:
        model_name = model.model_name
    except:
        try:
            model_name = model.model
        except:
            model_name = model.model_id

    return model_name

def adding_delay_for_rate_limits(model):
    """
    Google API and Groq API free plans has limit rates so we avoid reaching them
    """
    model_name = retrieve_model_name(model)
    if re.search('gemini|llama', model_name) is not None:
        time.sleep(6)

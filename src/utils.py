import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from pydantic import BaseModel
import json
import operator
from typing import Annotated, List, Literal, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage
from pydantic import BaseModel, Field
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
    - instructor_model: Select the model for the instructor node. Options include 'openai', 'google', 'meta', 'deepseek', or 'amazon'.
    - brainstormer_idea_model: Select the model for the brainstormer idea node. Options include 'openai', 'google', 'meta', 'deepseek', or 'amazon'.
    - brainstormer_critique_model: Select the model for the brainstormer critique node. Options include 'openai', 'google', 'meta', 'deepseek', or 'amazon'.

    - writer_model: Select the model for the writer node. Options include 'openai', 'google', 'meta', 'deepseek', or 'amazon'.
    - writing_reviewer_model: Select the model for the writing reviewer node. Options include 'openai', 'google', 'meta', 'deepseek', or 'amazon'.
    """
    language: Literal['english', 'spanish', 'portuguese', 'poland', 'french', 'german', 'italian', 'dutch','swedish', 'norwegian', 'danish', 'finnish', 'russian', 'chinese', 'japanese', 'korean','arabic', 'turkish', 'greek', 'hebrew']
    critiques_in_loop: bool
    instructor_model: Literal['openai', 'google','meta','amazon','deepseek']
    brainstormer_idea_model: Literal['openai','google','meta', 'amazon','deepseek']
    brainstormer_critique_model: Literal['openai','google','meta', 'amazon','deepseek'] 
    writer_model: Literal['openai', 'google','meta','amazon','deepseek']
    writing_reviewer_model: Literal['openai', 'google','meta','amazon','deepseek']
    translator_model: Literal['openai', 'google','meta','amazon','deepseek']
    n_chapters: int
    min_paragraph_per_chapter: int
    min_sentences_in_each_paragraph_per_chapter: int

class DocumentationReady(BaseModel):
    """
    This tool is called for confirming that the Instructor has the necessary information to pass to the writer about the user requirements
    """

    reasoning_step: str = Field(description = "In-depth explanation of your step by step reasoning about how to proceed.")
    reflection_step: str = Field(description = "In-depth review of your reasoning process so, if you detect that you made a mistake in your thoughts, at any point, correct yourself in this field.")
    topic: str = Field(description="The desired topic of the user, with high details and optimized with the reasoning and reflection steps")
    target_audience: str = Field(description = "The desired target audience the book should point to,  with high details,  and optimized with the reasoning and reflection steps")
    genre: str = Field(description="Genre of the book to develop,  with high details,  optimized based on the reasoning and reflection steps")
    writing_style: str = Field(description="The desired tone, style or book reference the writing should respect, with high details,  optimized based on the reasoning and reflection steps")
    additional_requirements: str = Field(description = "More requirements beyond topic, target audience, genre and writing style.  Optimized based on the reasoning and reflection steps")

class NarrativeBrainstormingStructuredOutput(BaseModel):
    """
    This tool defines the foundational narrative of the story based on the original set up. 
    """
    reasoning_step: str = Field(description = "In-depth explanation of your step by step reasoning about how to develop the general narrative along the evolution of the story.")
    reflection_step: str = Field(description = "In-depth review of your thoughts: If you detect that you made a mistake in your reasoning step, at any point, correct yourself in this field.")
    chapters_summaries: List[str] = Field(description = "A list where each element is a summary of each chapter. Each one should contain a detailed description of what happen on it, with well explained intro-development-ending stages. Each summary MUST HAVE a length of 5 sentences minimum. Optimized based on the reasoning and reflection steps.")

class IdeaBrainstormingStructuredOutput(BaseModel):
    """
    This tool is used in order to structure the proposed writting idea into specific detailed sections that covers the main points of the story.
    """
    reasoning_step: str = Field(description = "In-depth explanation of your step by step reasoning about how how the story will consist based on the user requirements")
    reflection_step: str = Field(description = "In-depth review of your thoughts: if you detect that you made a mistake in your reasoning step, at any point, correct yourself in this field.")
    story_overview: str = Field(description="Place a highly detailed overview of the narrative that includes a strong introduction, a well-developed middle, and a satisfying conclusion. Optimized based on the reasoning and reflection steps.")
    characters: str = Field(description = "Place the description of the characters of the story, in one paragraph each one.  Describe their background, motivations, and situations along the at the story journey. Be as detailed as possible.  Optimized based on the reasoning and reflection steps.")
    writing_style: str = Field(description="Place the style and tone the writer should consider while developing the book.  Optimized based on the reasoning and reflection steps.")
    book_name: str = Field(description="Place the title of the book. It should be unique, creative, and original. Optimized based on the reasoning and reflection steps.")
    book_prologue: str = Field(description="Place an engaging introduction to the book, crafted to capture the reader's attention without revealing key details. It should spark curiosity and create excitement, leaving them eager to explore the full story.")
    context_setting: str = Field(description="Describe the time, place, and atmosphere where the story takes place. Include any necessary background information relevant to the story. Optimized based on the reasoning and reflection steps.")
    inciting_incident: str = Field(description="Describe the event that disrupts the protagonist's normal life and initiates the main plot. It should set up the central conflict or challenge. Optimized based on the reasoning and reflection steps.")
    themes_conflicts_intro: str = Field(description="Introduce the central themes and conflicts that will be explored in the story. Mention any internal or external conflicts. Optimized based on the reasoning and reflection steps.")
    transition_to_development: str = Field(description="Ensure a smooth transition from the Introduction to the Development stage. Detail how the story moves from the setup to the rising action. Optimized based on the reasoning and reflection steps.")
    rising_action: str = Field(description="Describe the key events that increase tension and advance the central conflict. Include challenges that force the protagonist to grow or change. Optimized based on the reasoning and reflection steps.")
    subplots: str = Field(description="Outline any secondary storylines that complement the main plot. Describe how these subplots intersect with the main plot. Optimized based on the reasoning and reflection steps.")
    midpoint: str = Field(description="Identify a significant event that alters the direction of the story or escalates the conflict. It could be a turning point or a major revelation. Optimized based on the reasoning and reflection steps.")
    climax_build_up: str = Field(description="Detail the events leading up to the climax. Explain how these events escalate the conflict and set the stage for the story's peak moment. Optimized based on the reasoning and reflection steps.")
    climax: str = Field(description="Describe the decisive moment where the main conflict reaches its peak. Explain how the protagonist confronts the greatest challenge or opposition. Optimized based on the reasoning and reflection steps.")
    falling_action: str = Field(description="Outline the immediate aftermath of the climax. Describe how the resolution of the main conflict affects the characters and world. Optimized based on the reasoning and reflection steps.")
    resolution: str = Field(description="Tie up any remaining loose ends and conclude the story, reflecting on themes and character changes. Optimized based on the reasoning and reflection steps.")
    epilogue: str = Field(description="Provide a final reflection or glimpse into the characters' future, showing the long-term impact of the story. Optimized based on the reasoning and reflection steps.")

class TranslatorStructuredOutput(BaseModel):
    """
    This tool is used in order to structure the way the translator should reply
    """
    translated_content: str = Field(description = "The final translation from the original content provided")
    translated_chapter_name: str = Field(description = "Translation of the chapter name.")

class TranslatorSpecialCaseStructuredOutput(BaseModel):
    """
    This tool structures the way the translator should reply
    """
    translated_book_name: str = Field(description = "The translation of the book name")
    translated_book_prologue: str = Field(description= "The translation of the prologue of the book")

class WriterStructuredOutput(BaseModel):
    """
    This tool is used for structuring the generation of the writer.
    """
    reasoning_step: str = Field(description = "In-depth explanation of your step by step reasoning about how you will write the story based on the proposed idea")
    reflection_step: str = Field(description = "In-depth review of your thoughts: if you detect that you made a mistake in your reasoning step, at any point, correct yourself in this field.")
    content: str = Field(description = "Place the content inside the developed chapter, avoid putting the name of the chapter here. Optimized based on the reasoning and reflection steps.")
    chapter_name: str = Field(description = "Place the name of the developed chapter. It should be original and creative. Optimized based on the reasoning and reflection steps.")

class ApprovedWriterChapter(BaseModel):
    """
    This tool is used when the reviewer approves the chapter and its content based on its analysis.
    """
    is_approved: bool = Field(description = 'This tool should be invoke only if the chapter is quite well  and it could be defined as MVP, based on your analysis.')

class CritiqueWriterChapter(BaseModel):
    """
    This tool is used when the chapter needs improvements based on the current state of it.
    """
    feedback: str = Field(description = 'Highly detailed suggestions and points of improvements based on your analysis.')

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

def _get_model(config: GraphConfig, key:Literal['instructor_model','brainstormer_idea_model','brainstormer_critique_model','writer_model','writing_reviewer_model','translator_model'], temperature:float, default:Literal['openai', 'google','meta','amazon']='openai', top_k=50, top_p=0.9):
    model = config['configurable'].get(key, default)
    if model == "openai":
        return ChatOpenAI(temperature=temperature, model="gpt-4o-mini", top_k = top_k, top_p = top_p)
    elif model == "google":
        return ChatGoogleGenerativeAI(temperature=temperature, model="gemini-exp-1206", top_k = top_k, top_p = top_p)
    elif model == 'meta':
        return ChatGroq(temperature=temperature, model="llama-3.3-70b-versatile", model_kwargs = {'top_p':top_p}) #Groq doesnt support top_k
    elif model == 'deepseek':
        return ChatGroq(temperature=temperature, model="deepseek-r1-distill-llama-70b",model_kwargs = {'top_p':top_p}) #Groq doesnt support top_k
    
    elif model == 'amazon':
        return ChatBedrock(model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0', model_kwargs = {'temperature':temperature, 'top_k': top_k, 'top_p': top_p})
    else:
        raise ValueError(f"Unsupported model: '{model}'. Expected one of: 'openai', 'google', 'meta', 'deepseek', 'amazon'")

    
def check_chapter(msg_content:str, min_paragraphs: int):
    """
    This function validates that the generated chapter contains a the minimum size that the user asks for in terms of paragraphs
    """
    if len(msg_content.split('\n\n')) >= min_paragraphs:
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

class NoJson(Exception):
    pass

class BadFormattedJson(Exception):
    pass

def cleaning_llm_output(llm_output):

    content = llm_output.content
    
    # Phase 1: JSON Extraction
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
        if not match:
            match_inline = re.search(r"({.*?}|\[.*?\])", content, re.DOTALL)
            if match_inline:
                json_content = match_inline.group(0).strip()
            else:
                raise NoJson("The output does not contain a JSON code block")
        else: 
            json_content = match.group(1)
        
    except re.error as e:
        print(f"Regex error during extraction: {str(e)}")
        return content

    # Phase 2: Content Cleaning
    try:
        # Remove remaining backticks and normalize whitespace
        try:
            json_content = re.sub(r"```", "", json_content)
            parsed = json.loads(json_content)                                
            return parsed
        except:
            pass
        try:
            json_content = re.sub(r"\s+", " ", json_content)
            parsed = json.loads(json_content)
            return parsed
        except:
            pass
        
        json_content = json_content.replace('\\', '')
        json_content = json_content.strip()

    except re.error as e:
        print(f"Regex error during cleaning: {str(e)}")
        return content

    # Phase 3: JSON Validation
    try:
        # Fix common JSON issues
        json_content = re.sub(
            r',\s*([}\]])', r'\1',  # Remove trailing commas
            json_content
        )
        json_content = re.sub(
            r"([{:,])\s*'([^']+)'\s*([,}])",  # Convert single quotes to double
            r'\1"\2"\3', 
            json_content
        )
        
    except re.error as e:
        return content

    # Phase 4: Parsing
    try:
        parsed = json.loads(json_content)
        return parsed
    except:
        try:
            def escape_value_quotes(match):
                value = match.group(1)
                return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'

            # Improved regex to handle whitespace and escaped quotes in values
            pattern = r'(?<=:)\s*"(.*?[^\\])"(?=\s*[,}\]])'

            json_content = re.sub(pattern, escape_value_quotes, json_content)

            return json.loads(json_content)

        except json.JSONDecodeError as e:
            raise BadFormattedJson({"error": f"While trying to format the JSON object you have generated we detect the following error: {e.args[0]}", "detail": f"Error location: Line {e.lineno}, Column {e.colno}", "context": f"{e.doc[e.pos-20:e.pos+20]}"})




def get_json_schema(pydantic_class: BaseModel) -> dict:
    """
    This function receives a Pydantic class and returns its JSON schema representation.

    :param pydantic_class: A Pydantic class that inherits from BaseModel
    :return: A dictionary representing the JSON schema of the input class
    """
    data = pydantic_class.model_json_schema()
    schema_description = data['description']
    data_keys = [{"description": data['properties'][key]['description'], "data_type": data['properties'][key]['type']} for key in list(data['properties'].keys())]
    description = f"The schema is about: '{schema_description}'\n\nThis is the schema definition:\n" + json.dumps(data_keys, indent = 4)
    return description


if __name__ == '__main__':
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    x = get_json_schema(DocumentationReady)
    reply = AIMessage(content = "<think>\nOkay, I need to create a story based on the user's requirements. The topic is about scandalous infidelity in a couple leading to dramatic and embarrassing situations, but presented in an entertaining and comic way. The target audience is adults in relationships, so the story should explore themes relevant to them while keeping it entertaining.\n\nFirst, I should consider the genre, which is a dramedy. That means blending drama and comedy. I'll need to ensure the story doesn't lean too heavily in one direction. The writing style should be engaging, humorous, and slightly satirical, similar to authors like Sophie Kinsella or Emily Giffin.\n\nI need to develop relatable characters. Maybe the couple has been together for a while and is facing common relationship issues. The infidelity should create tension but also comedic situations. Perhaps the husband's attempt to cover up the affair leads to funny mishaps.\n\nThe setting could be a suburban area to make it relatable. The context should include elements that highlight the monotony of their routine, which might have led to the infidelity. \n\nFor the inciting incident, maybe the wife discovers the affair through a humorous mistake, like a wrong text message or an awkward encounter. This can create both drama and comedy. \n\nThe themes should include trust, communication, and the challenges of maintaining a relationship. The conflicts would be both internal, as each character deals with their emotions, and external, as they navigate the fallout.\n\nIn the rising action, the couple tries to navigate the aftermath, perhaps through couples therapy or comedic attempts to save the marriage. Subplots could involve friends or family members who complicate things, adding more humor and depth.\n\nThe midpoint could be a turning point where they almost reconcile but face another setback, keeping the tension high. The climax might involve a public confrontation or a dramatic revelation that forces them to confront their issues head-on.\n\nThe falling action would show the immediate effects of the climax, leading to the resolution where they decide to work on their relationship or part ways. The epilogue should give a sense of closure, maybe showing them in a better place or reflecting on their journey.\n\nI need to make sure the story flows smoothly, with a clear beginning, middle, and end. The prologue should hook the reader with a glimpse into their relationship before the infidelity. The writing style should balance humor with deeper emotional moments to keep it engaging.\n\nI should also think about the title. Something catchy that hints at both the drama and comedy, like \"Love in the Time of Chaos\" or \"The Misadventures of Marriage.\"\n\nNow, putting it all together, I'll outline the story with these elements, ensuring each part aligns with the user's requirements and the dramedy genre.\n</think>\n\n{\n    \"description\": \"This tool is used in order to structure the proposed writing idea into specific detailed sections that covers the main points of the story.\",\n    \"properties\": {\n        \"reasoning_step\": \"The story revolves around a couple, Alex and Maddie, who have been together for over a decade. Their relationship, once passionate, has become routine. The inciting incident occurs when Alex, feeling neglected, has a one-night stand with a younger woman, Mia, during a business trip. Maddie discovers this through a humorous mix-up involving a misplaced phone and a series of awkward encounters. The narrative explores the aftermath, blending dramatic tension with comedic elements arising from Alex's clumsy attempts to cover his tracks and Maddie's humorous yet poignant reactions. The story delves into themes of trust, communication, and the challenges of maintaining a relationship, with a satirical take on modern marriage and infidelity. The writing style is fast-paced, engaging, and humorous, with a touch of satire, drawing inspiration from authors like Sophie Kinsella and Emily Giffin. The setting is contemporary, in a suburban town, providing a relatable backdrop for the couple's journey.\",\n        \"reflection_step\": \"Upon reflection, I considered balancing drama and comedy without trivializing the gravity of infidelity. The story maintains a respectful tone while incorporating humor through situational comedy and character quirks. The focus remains on the emotional journey of the couple, ensuring relatable and engaging character development.\",\n        \"story_overview\": \"Alex and Maddie, a couple in their late 30s, face a crisis when Alex's infidelity is revealed. The story follows their journey from discovery to reconciliation, blending dramatic moments with comedic mishaps. The narrative explores themes of trust, love, and the complexities of modern relationships, offering a humorous yet heartfelt exploration of marriage and forgiveness.\",\n        \"characters\": \"Alex: A well-intentioned but slightly insecure husband in his late 30s, struggling with feelings of neglect in his marriage. His infidelity stems from a desire for validation and excitement, leading to a series of comedic attempts to cover his mistake. Maddie: A strong, independent wife in her late 30s, who loves Alex deeply but feels unappreciated. Her discovery of the affair leads to a mix of anger, sadness, and dark humor as she navigates her emotions and the absurdity of the situation.\",\n        \"writing_style\": \"Engaging, humorous, and slightly satirical, with a fast-paced narrative that balances lighthearted moments with deeper emotional exploration. The tone is conversational, making the characters relatable and the situations both poignant and amusing.\",\n        \"book_name\": \"Love in the Time of Chaos\",\n        \"book_prologue\": \"In the quiet suburban town of Maplewood, the ordinary lives of its residents often hide extraordinary secrets. For Alex and Maddie, a typical evening turns into an unexpected revelation that will change their lives forever. Dive into their story, where love, laughter, and a little bit of chaos collide.\",\n        \"context_setting\": \"Contemporary suburban setting, providing a relatable backdrop for the couple's journey. The routine and monotony of their daily lives contrast with the sudden disruption caused by the infidelity, highlighting the challenges of modern relationships.\",\n        \"inciting_incident\": \"Alex's one-night stand with Mia, a younger woman he meets during a business trip, sets off a chain of events. The discovery happens through a misplaced phone and a series of awkward encounters, blending drama with comedic elements.\",\n        \"themes_conflicts_intro\": \"Themes include trust, communication, and the complexities of maintaining a relationship. Conflicts are both internal, as each character grapples with their emotions, and external, as they navigate the fallout of the affair.\",\n        \"transition_to_development\": \"The story smoothly transitions from the initial discovery to the couple's attempts to navigate their relationship. The narrative moves from the setup of their routine life to the rising action of dealing with the aftermath of the affair.\",\n        \"rising_action\": \"Alex's clumsy attempts to cover his tracks lead to humorous situations, while Maddie's reactions range from anger to dark humor. The couple's interactions with friends and family add depth and comedy, complicating their journey toward reconciliation.\",\n        \"subplots\": \"Subplots involve interactions with friends and family, who offer advice and sometimes complicate the situation. These secondary storylines add humor and depth, exploring the broader impact of the affair on their social circle.\",\n        \"midpoint\": \"A turning point occurs when Alex and Maddie almost reconcile, but another setback arises, keeping the tension high and the story engaging.\",\n        \"climax_build_up\": \"The build-up to the climax involves escalating tension as the truth becomes harder to hide. The couple's interactions become more intense, leading to a dramatic confrontation that forces them to face their issues head-on.\",\n        \"climax\": \"The climax features a public confrontation where the affair is revealed, leading to a dramatic and emotional showdown. This moment is both intense and cathartic, pushing the couple to confront their challenges directly.\",\n        \"falling_action\": \"The immediate aftermath of the climax shows the couple dealing with the consequences of the confrontation. The narrative shifts toward resolution as they begin to heal and work on their relationship.\",\n        \"resolution\": \"The story concludes with the couple deciding to work on their marriage, showing growth and a renewed commitment. The resolution ties up loose ends, reflecting on themes of forgiveness and the effort required to sustain love.\",\n        \"epilogue\": \"The epilogue offers a glimpse into the couple's future, showing them in a better place, with a sense of closure and hope. It reflects on their journey, highlighting the long-term impact of their experiences.\"\n    },\n    \"required\": [\n        \"reasoning_step\",\n        \"reflection_step\",\n        \"story_overview\",\n        \"characters\",\n        \"writing_style\",\n        \"book_name\",\n        \"book_prologue\",\n        \"context_setting\",\n        \"inciting_incident\",\n        \"themes_conflicts_intro\",\n        \"transition_to_development\",\n        \"rising_action\",\n        \"subplots\",\n        \"midpoint\",\n        \"climax_build_up\",\n        \"climax\",\n        \"falling_action\",\n        \"resolution\",\n        \"epilogue\"\n    ],\n    \"title\": \"IdeaBrainstormingStructuredOutput\",\n    \"type\": \"object\"\n}")
    cleaning_llm_output(llm_output = reply)
    print('-')

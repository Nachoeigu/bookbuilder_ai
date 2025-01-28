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
    min_paragraph_per_chapter: int
    min_sentences_in_each_paragraph_per_chapter: int

class DocumentationReady(BaseModel):
    """
    This tool is called for confirming that the Instructor has the necessary information to pass to the writer about the user requirements
    """

    reasoning_step: str = Field(description = "In-deep explanation of your step by step reasoning about how to proceed.")
    reflection_step: str = Field(description = "In-deep review of your reasoning process so, if you detect that you made a mistake in your thoughts, at any point, correct yourself in this field.")
    topic: str = Field(description="The desired topic of the user, with high details and optimized with the reasoning and reflection steps")
    target_audience: str = Field(description = "The desired target audience the book should point to,  with high details,  and optimized with the reasoning and reflection steps")
    genre: str = Field(description="Genre of the book to develop,  with high details,  optimized based on the reasoning and reflection steps")
    writing_style: str = Field(description="The desired tone, style or book reference the writing should respect, with high details,  optimized based on the reasoning and reflection steps")
    additional_requirements: str = Field(description = "More requirements beyond topic, target audience, genre and writing style.  Optimized based on the reasoning and reflection steps")

class NarrativeBrainstormingStructuredOutput(BaseModel):
    """
    This tool defines the foundational narrative of the story based on the original set up. 
    """
    reasoning_step: str = Field(description = "In-deep explanation of your step by step reasoning about how to develop the general narrative along the evolution of the story.")
    reflection_step: str = Field(description = "In-deep review of your thoughts: If you detect that you made a mistake in your reasoning step, at any point, correct yourself in this field.")
    chapters_summaries: List[str] = Field(description = "A list where each element is a summary of each chapter. Each one should contain a detailed description of what happen on it, with well explained intro-development-ending stages. Each summary MUST HAVE a length of 5 sentences minimum. Optimized based on the reasoning and reflection steps.")

class IdeaBrainstormingStructuredOutput(BaseModel):
    """
    This tool is used in order to structure the proposed writting idea into specific detailed sections that covers the main points of the story.
    """
    reasoning_step: str = Field(description = "In-deep explanation of your step by step reasoning about how how the story will consist based on the user requirements")
    reflection_step: str = Field(description = "In-deep review of your thoughts: if you detect that you made a mistake in your reasoning step, at any point, correct yourself in this field.")
    story_overview: str = Field(description="A highly detailed overview of the narrative that includes a strong introduction, a well-developed middle, and a satisfying conclusion. Optimized based on the reasoning and reflection steps.")
    characters: str = Field(description = "Describe the characters of the story, in one paragraph each one.  Describe their background, motivations, and situations along the at the story journey. Be as detailed as possible.  Optimized based on the reasoning and reflection steps.")
    writing_style: str = Field(description="The style and tone the writer should consider while developing the book.  Optimized based on the reasoning and reflection steps.")
    book_name: str = Field(description="The title of the book. It should be unique, creative, and original. Optimized based on the reasoning and reflection steps.")
    book_prologue: str = Field(description="The opening section of the book. It should be engaging and designed to strongly capture the audience's attention. Optimized based on the reasoning and reflection steps.")
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
    reasoning_step: str = Field(description = "In-deep explanation of your step by step reasoning about how you will write the story based on the proposed idea")
    reflection_step: str = Field(description = "In-deep review of your thoughts: if you detect that you made a mistake in your reasoning step, at any point, correct yourself in this field.")
    content: str = Field(description = "The content inside the developed chapter, avoid putting the name of the chapter here. Optimized based on the reasoning and reflection steps.")
    chapter_name: str = Field(description = "The name of the developed chapter. It should be original and creative. Optimized based on the reasoning and reflection steps.")

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

def _get_model(config: GraphConfig, key:Literal['instructor_model','brainstormer_idea_model','brainstormer_critique_model','writer_model','writing_reviewer_model','translator_model'], temperature:float, default:Literal['openai', 'google','meta','amazon']='openai'):
    model = config['configurable'].get(key, default)
    if model == "openai":
        return ChatOpenAI(temperature=temperature, model="gpt-4o-mini")
    elif model == "google":
        return ChatGoogleGenerativeAI(temperature=temperature, model="gemini-2.0-flash-exp")
    elif model == 'meta':
        return ChatGroq(temperature=temperature, model="llama-3.3-70b-versatile")
    elif model == 'amazon':
        return ChatBedrock(model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0', model_kwargs = {'temperature':temperature})
    else:
        raise ValueError(f"Unsupported model: '{model}'. Expected one of: 'openai', 'google', 'meta', 'amazon'")

    
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


def cleaning_llm_output(llm_output):
    try:
        content = llm_output.content
        
        # Phase 1: JSON Extraction
        try:
            match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
            if not match:
                print("No JSON code block found")
                raise NoJson("The output does not contain a JSON code block")
                
            json_content = match.group(1)
            print("Phase 1: JSON extraction successful")
            
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
            
            json_content = json_content.replace("\\", "")
            json_content = json_content.strip()
            print("Phase 2: Content cleaning successful")

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
            print("Phase 3: JSON validation complete")
            
        except re.error as e:
            print(f"Regex error during validation: {str(e)}")
            return content

        # Phase 4: Parsing
        try:
            parsed = json.loads(json_content)
            print("Phase 4: JSON parsing successful")
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {str(e)}")
            print(f"Error location: Line {e.lineno}, Column {e.colno}")
            print(f"Context: {e.doc[e.pos-20:e.pos+20]}")
            return content
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return content



def get_json_schema(pydantic_class: BaseModel) -> dict:
    """
    This function receives a Pydantic class and returns its JSON schema representation.

    :param pydantic_class: A Pydantic class that inherits from BaseModel
    :return: A dictionary representing the JSON schema of the input class
    """
    
    return json.dumps(pydantic_class.model_json_schema(), indent = 4)

if __name__ == '__main__':
    from langchain_core.messages import AnyMessage, HumanMessage, AIMessage 

    output = AIMessage(content = "```json\n{\n  \"reasoning_step\": \"I need to expand the previous chapter to include at least 5 paragraphs while maintaining the pacing and tension. I will focus on sensory details to enhance the feeling of unease and use the paragraphs to build the tension incrementally, leading up to the final collapse. I will make sure the paragraphs are balanced in length and contribute to the overall narrative flow, avoiding repetition and keeping the focus on specific observations and interactions to create a more immersive experience for the reader. I will also make sure that all the key elements of the previous iteration are still present, and that no key is forgotten in the JSON output.\",\n  \"reflection_step\": \"The previous iteration was good but needed to be more structured and expanded to meet the paragraph requirements. I will use specific observations and sensory details to amplify the sense of unease and use the 5 paragraphs to create a clear progression from initial apprehension to full-blown panic, setting the stage for the disaster that is to come. I will make sure each paragraph has a specific purpose, either introducing new elements of unease or building on the existing ones, and I will keep the language vivid and engaging to maintain the reader's attention.\",\n  \"content\": \"The whistle's sharp blast pierced the air, marking the start of the game, but the usual roar of the crowd seemed distant, muffled by a growing knot of dread in my stomach. On the pitch, the players moved like distant figures, their actions a blur, and my focus was drawn away from the game, towards subtle irregularities that were becoming increasingly hard to ignore. A gate, usually guarded by a security officer, hung open, the metal barrier swaying loosely in the wind, and I scanned the area, searching for the missing guard, but he was nowhere to be seen, a chill running down my spine. Further up, near the Tercera bandeja, a group of fans were arguing loudly, their voices rising above the din, and I strained to hear their words, realizing they were discussing the structural integrity of the section, their faces etched with concern. The air itself seemed to thicken, the usual pre-game excitement replaced by an unusual stillness, a sense of anticipation tinged with dread, and I tried to shake off my apprehension, but the subtle signs of danger kept chipping away at my resolve. \\n\\nEl Ruso, ever the cynic, leaned closer, his voice low and gravelly, “Did you see that guard, viejo? The one near the gate? Vanished into thin air.” His words, though spoken with his usual detached tone, intensified my anxiety, and I knew I wasn't alone in sensing that something was terribly wrong. I tried to focus on the game, to lose myself in the action on the pitch, but the image of the unguarded gate and the arguing fans kept flashing through my mind, and I felt a growing sense of helplessness, as if we were all trapped in a nightmare about to unfold. The players moved with frantic energy, their actions almost desperate, and the chants of the crowd grew more strained, the usual passion replaced by unease. I could smell the sweat of the crowd, a metallic tang in the air, and I felt a pressure building, like a storm gathering force. \\n\\nEl Ruso scoffed, his gaze fixed on the Tercera bandeja, “They're arguing about the cracks, Nico. They know it’s not safe, but nobody is doing anything about it.” His words, though cynical, were a stark reminder of the danger lurking above us, and my heart pounded in my chest, a frantic drumbeat against the rising tide of fear. I saw a few more security guards gesturing frantically towards the Tercera bandeja, their faces etched with panic, and I followed their gaze, my heart skipping a beat. The cracks were spreading, the concrete sagging more visibly, and I knew the situation was rapidly deteriorating, that we were running out of time. The chants of the crowd grew more desperate, the energy more chaotic, and I could feel the tension rising, almost unbearable, and I looked around, trying to gauge the mood, but everyone seemed lost in the game, oblivious to the danger. \\n\\nI felt a sudden urge to leave, to get out of the stadium, to escape the feeling of impending disaster, but I was frozen in place, unable to move, and I knew it was too late, that the tragedy was about to strike, that the vibrant energy of the stadium was about to be shattered. The ground seemed to tremble beneath our feet, the stadium groaned, and I knew the moment of disaster was about to arrive, and I closed my eyes, bracing myself for the inevitable. The air grew heavy, the stadium seemed to hold its breath, and the silence was broken by a low, ominous creaking sound, a sound that seemed to come from the very depths of the earth. \\n\\nI opened my eyes, my heart pounding, and I saw that the section of concrete on the Tercera bandeja was now visibly collapsing, the cracks spreading across its surface like a spiderweb, and I knew the moment of disaster had arrived. The screams began, a chorus of terror that filled the air, and I saw people scrambling, desperately trying to escape the collapsing structure. The chaos was immediate, the vibrant atmosphere of the stadium shattering into pandemonium, and I grabbed El Ruso's arm, shouting his name, and we both started to run, desperately trying to find a way out, our hearts pounding, our minds racing with fear and adrenaline, knowing that our lives depended on it.\",\n  \"chapter_name\": \"The Unfolding Nightmare\"\n}\n```")
    data = {
    "reasoning_step": "I will revise the chapter again, ensuring it is structured into at least five paragraphs while maintaining the improvements from the previous revision. I will continue to focus on conciseness, action, and a dynamic pace, minimizing internal monologues and repetitive descriptions. The goal is to create a more impactful and suspenseful narrative with a clear progression of events and a strong sense of urgency.",
    "reflection_step": "The previous revision successfully addressed the issues of repetition and excessive internal monologue. The chapter now needs to be structured into at least five paragraphs to improve readability and flow. I will ensure that each paragraph contributes to the overall narrative, focusing on the escalating tension and the immediate events leading to the stadium's collapse. The key is to maintain the dynamic approach and focus on action, while also creating a more structured and engaging reading experience.",
    "content": "The whistle blew, signaling the start of the game, yet the roar of the crowd seemed muted, a distant hum against the cold dread settling in my gut. The players on the pitch were mere blurs, their movements insignificant compared to the alarming sight of a usually guarded gate swinging open, the guard nowhere in sight. A chill snaked down my spine. Nearby, towards the Tercera bandeja, a group of fans argued heatedly, their voices rising above the general din, their frantic words about cracks and danger amplifying my unease. El Ruso, his voice tight, confirmed my fears, \"That guard is gone, and they know about the cracks, Nico. Something is terribly wrong.\"",
    "content": "I tried to focus on the game, but the image of the open gate and the agitated fans kept flashing in my mind, each detail fueling my growing panic. The players moved with a desperate energy, their movements frantic, and the crowd's chants, once celebratory, now sounded strained and anxious. I attempted to ignore the rising sense of dread, but it was becoming overwhelming, an oppressive weight in the air. El Ruso’s gaze was fixed on the Tercera bandeja. \"They're getting louder, Nico. They know it's not safe,\" he said, his words a stark confirmation of the mounting danger, my heart pounding against the rising tide of fear.",
    "content": "The game continued, a surreal backdrop to the growing chaos, but the atmosphere had shifted dramatically. I saw security guards gesturing urgently towards the Tercera bandeja, their faces pale with alarm. The cracks in the concrete were spreading, each one a visible sign of the stadium's impending doom. The crowd's chants turned desperate, a chaotic mix of calls and screams, and I searched the faces around me, but most seemed lost in the game, oblivious to the imminent danger. A sudden urge to escape washed over me, but I was frozen, paralyzed by the sheer magnitude of what was unfolding.",
    "content": "Then, the ground trembled, a low groan echoing through the stadium, and I closed my eyes, bracing myself for the inevitable. A sharp creaking sound sliced through the air, and I snapped my eyes open, my heart hammering against my ribs. I saw the concrete of the Tercera bandeja collapsing, a horrifying sight that triggered a chorus of screams. People were scrambling, desperately trying to escape the crumbling structure, and chaos erupted all around me. I grabbed El Ruso, shouting his name above the din, and we ran, desperately searching for an escape route, our lives hanging precariously in the balance.",
    "content": "The world dissolved into a cacophony of screams, the grinding of concrete, and the pounding of feet. We pushed through the throng, the fear of being crushed and buried alive propelling us forward. The game was forgotten, replaced by the desperate, primal need to survive. The air was thick with dust, and I could barely see, but I could feel the panic all around me, the sheer desperation of those trying to escape the collapsing structure. My only focus was to keep moving, to find a way out of this nightmare, a fight for survival in the heart of the chaos.",
    "chapter_name": "The Breaking Point"
    }

    x = cleaning_llm_output(output)    

    WriterStructuredOutput(**data)
    print('-')

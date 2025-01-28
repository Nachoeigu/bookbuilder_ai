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
    book_prologue: str = Field(description="An engaging introduction to the book, crafted to capture the reader's attention without revealing key details. It should spark curiosity and create excitement, leaving them eager to explore the full story.")
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
        "reasoning_step": "I will craft a story that adheres to the user's specifications: a first-person narrative of a tragic event during a Boca-River match at La Bombonera in 2008. The story will emphasize the mass behavior contributing to the chaos and the socio-political context of Argentina at the time. The narrative will follow a clear structure, with a compelling beginning, middle, and end. I will focus on creating a realistic and suspenseful atmosphere and the specific details of the stadium and the event. The protagonist will be an ordinary fan, and the writing style will be intense and immersive.",
        "reflection_step": "I've reviewed the user's requirements and will focus on the first-person perspective, the 2008 setting, and the mass behavior aspects. I will ensure that the story is realistic, avoids sensationalism, and captures the gravity of the tragic events. I will also make sure that the characters are well-defined and relatable, and that the narrative maintains a suspenseful and emotional tone throughout.",
        "story_overview": "The story opens with a Boca Juniors fan, Mateo, preparing for the Superclásico against River Plate at La Bombonera in 2008. The atmosphere is electric, charged with the intense rivalry and the socio-political tensions of the time. As the match progresses, the crowd becomes increasingly agitated, fueled by alcohol, machismo, and a sense of collective identity. The narrative details the escalating chaos, the pushing and shoving, and the growing sense of panic. A sudden surge of the crowd leads to a stampede, resulting in a tragic loss of life. Mateo, caught in the middle, witnesses the horror and struggles to survive. The story then shifts to the aftermath, exploring the emotional toll on Mateo and the community, the search for accountability, and the lasting impact of the tragedy on Argentine society. The narrative concludes with Mateo trying to find a way to cope with the trauma, forever changed by the events he endured.",
        "characters": {
            "mateo": "Mateo, a 28-year-old working-class man, is a lifelong Boca fan. He is passionate about football and sees it as a way to escape the mundane reality of his life. He is not prone to violence but gets carried away by the intense atmosphere of La Bombonera. He is relatable, with a strong sense of loyalty and a hidden vulnerability that comes to the fore during the tragedy. The events of the match shake his core beliefs and leave him grappling with survivor's guilt and the fragility of life.",
            "sofia": "Sofia, Mateo's girlfriend, is a more pragmatic and level-headed character. She is not as invested in football as Mateo, but she understands its importance to him. She is concerned about Mateo's safety and the potential for violence at the match. Her perspective offers a contrast to Mateo's passion, and she becomes a source of support for him after the tragedy. She represents the voice of reason and caution.",
            "el_viejo": "El Viejo, an older, seasoned Boca fan, is a mentor figure to Mateo. He is a regular at La Bombonera and has witnessed many derbies. He represents the old guard of Boca fans, with a deep understanding of the rivalry and the traditions of the club. He is initially full of fervor and passion, but is shaken by the tragedy, revealing his own hidden fears and vulnerabilities. He provides a sense of history and continuity.",
            "ramon": "Ramón, a younger, more aggressive Boca fan, is part of the barra brava. He is fueled by anger and a desire for conflict. He embodies the toxic elements of the fanbase and contributes to the escalating violence. He is a foil to Mateo, representing the dangers of unchecked passion and mob mentality. His actions are part of what leads to the tragedy."
        },
        "writing_style": "The narrative will be in the first person, present tense, to create a sense of immediacy and immersion. The tone will be intense, suspenseful, and emotionally charged, reflecting Mateo's experience of the unfolding tragedy. The writing will be descriptive and evocative, capturing the atmosphere of La Bombonera and the escalating chaos. The style will aim for journalistic realism, avoiding sensationalism while conveying the gravity of the events. The language will be raw and authentic, reflecting Mateo's working-class background. The narrative will be interspersed with Mateo's inner thoughts and reflections, giving the reader access to his emotional state.",
        "book_name": "The Blue and Gold Inferno",
        "book_prologue": "The air crackles. Not just with the anticipation of the Superclásico, but with something else, something dark and volatile. It's 2008, and La Bombonera is a pressure cooker about to explode. I can feel it in the sweat on my palms, in the roar of the crowd, in the way my heart hammers against my ribs. This isn't just a game; it's a war, and we're all soldiers in the blue and gold army. But today, the enemy isn't just the team in red and white. Today, the enemy is something else, something far more insidious.",
        "context_setting": "The story is set in Buenos Aires, Argentina, in 2008. The country is still recovering from the economic crisis of the early 2000s, and there's a palpable sense of social and political unrest. Football, particularly the rivalry between Boca Juniors and River Plate, is a major outlet for these tensions. La Bombonera, Boca's stadium, is an iconic symbol of the club's identity and a cauldron of intense passion. The pre-match atmosphere is electric, with fans drinking, chanting, and lighting flares. The stadium is overcrowded, with inadequate safety measures, creating a dangerous environment.",
        "inciting_incident": "The inciting incident is the start of the match itself. The initial excitement and anticipation quickly give way to a sense of unease as the crowd becomes more agitated. The pushing and shoving become more intense, and there are several near-misses of people falling. The tension in the stadium rises as the match progresses, the referee's calls, the actions on the field, all contribute to the overall tension and the fans' agitation.",
        "themes_conflicts_intro": "The central themes of the story are the dangers of mass behavior, the fragility of life, and the psychological impact of trauma. The main conflicts are both external and internal. The external conflict is the escalating chaos and violence within the stadium. The internal conflict is Mateo's struggle to reconcile his passion for football with the horrific events he witnesses, and the survivor's guilt that consumes him. The story will also explore the themes of identity, loyalty, and the search for meaning in the face of tragedy.",
        "transition_to_development": "The story transitions from the initial excitement of the match to the rising tension as the crowd becomes more volatile. The narrative shifts from Mateo's personal experience to a broader view of the collective behavior of the crowd. The descriptions become more detailed and visceral, capturing the sights, sounds, and smells of the stadium as it descends into chaos. The use of present tense and first person perspective intensifies the feeling of being there, as the reader feels the increasing tension with Mateo.",
        "rising_action": "The rising action involves the increasing intensity of the crowd's behavior. The pushing and shoving become more aggressive, and there are several near-misses of people being injured. The narrative details the escalating violence, the use of flares and fireworks, and the growing sense of panic among the fans. Mateo witnesses acts of aggression and feels the collective madness taking over. The match becomes secondary to the chaos unfolding in the stands, as the focus shifts to the growing sense of danger and impending disaster.",
        "subplots": "One subplot will involve the story of El Viejo, the older fan who serves as a mentor to Mateo. His experience of the game and his reaction to the tragedy will be explored, highlighting the generational impact of the event. Another subplot will focus on the actions of Ramón and the barra brava, showing the role of organized violence in the tragedy. A minor subplot will explore Sofia's perspective on Mateo's passion for football and her growing concern for his safety.",
        "midpoint": "The midpoint of the story is the moment when the crowd surge begins. There is a sudden, overwhelming push, and people start falling. The air is filled with screams and the sounds of bodies crashing against each other. This is when the tragic consequences of the chaos become apparent, and the focus shifts to the struggle for survival. Mateo finds himself trapped in the middle of the stampede, desperately trying to stay on his feet and protect himself.",
        "climax_build_up": "The climax build-up involves the chaos of the stampede reaching its peak. The narrative becomes more frantic and visceral, describing the horrors of the event in vivid detail. Mateo witnesses people being crushed, trampled, and suffocated. He struggles to breathe, feels the weight of the crowd pressing down on him, and loses sight of his friends. The sense of panic and desperation intensifies, as the hope of survival diminishes. The crowd is no longer a collective, but a destructive force.",
        "climax": "The climax is the moment when the stampede reaches its peak, and the full extent of the tragedy becomes apparent. Mateo witnesses the loss of life firsthand and experiences a moment of complete despair and helplessness. He manages to find a small pocket of space and struggles to keep himself from being crushed. The descriptions are raw and unflinching, capturing the horrific reality of the event. This is the moment of the greatest tension, where Mateo's survival hangs in the balance.",
        "falling_action": "The falling action involves the immediate aftermath of the stampede. The crowd slowly begins to disperse, and the scene of devastation becomes visible. Mateo, battered and bruised, struggles to comprehend what has happened. The narrative focuses on the emotional toll of the tragedy, the shock, the grief, and the survivor's guilt. Mateo tries to find his friends, while the stadium becomes a scene of chaos and despair. The emergency services arrive, but their efforts seem almost futile in the face of the immense scale of the disaster.",  "resolution": "The resolution focuses on Mateo's attempt to cope with the trauma and the long-term impact of the tragedy. He is haunted by the memories of the event, struggling with nightmares and flashbacks. The narrative explores the emotional toll on the community, the search for accountability, and the lasting changes in the way football matches are managed. Mateo reflects on the meaning of loyalty and identity, and tries to find a way to move forward, forever changed by the events he endured. He starts to see the game in a different light, and his old passion is replaced by a sense of loss.",
        "epilogue": "The epilogue takes place a few years after the tragedy. Mateo is still grappling with the emotional scars, but he has found a way to live with them. He no longer attends matches at La Bombonera, but he still feels a connection to the club and its fans. The story ends with Mateo reflecting on the fragility of life and the importance of remembering the victims of the tragedy. He has found a measure of peace, but he will never forget the day the blue and gold became an inferno."
        }

#    x = cleaning_llm_output(output)    
    try:
        IdeaBrainstormingStructuredOutput(**data)
    except Exception as e:
        print('-')
    print('-')

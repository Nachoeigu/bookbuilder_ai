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
    reasoning_step: str = Field(description = "In-deep explanation of your step by step reasoning about how you will write the story based on the proposed idea")
    reflection_step: str = Field(description = "In-deep review of your thoughts: if you detect that you made a mistake in your reasoning step, at any point, correct yourself in this field.")
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
        return ChatGoogleGenerativeAI(temperature=temperature, model="gemini-2.0-flash-exp", top_k = top_k, top_p = top_p)
    elif model == 'meta':
        return ChatGroq(temperature=temperature, model="llama-3.3-70b-versatile", top_k = top_k, top_p = top_p)
    elif model == 'amazon':
        return ChatBedrock(model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0', model_kwargs = {'temperature':temperature, 'top_k': top_k, 'top_p': top_p})
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

class BadFormattedJson(Exception):
    pass

def cleaning_llm_output(llm_output):

    content = llm_output.content
    
    # Phase 1: JSON Extraction
    try:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
        if not match:
            raise NoJson("The output does not contain a JSON code block")
            
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
        
        json_content = json_content.replace("\\", "")
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
        
    except json.JSONDecodeError as e:
        raise BadFormattedJson({"error": f"While trying to format the JSON object you have generated we detect the following error: {e.args[0]}", "detail": f"Error location: Line {e.lineno}, Column {e.colno}", "context": f"{e.doc[e.pos-20:e.pos+20]}"})




def get_json_schema(pydantic_class: BaseModel) -> dict:
    """
    This function receives a Pydantic class and returns its JSON schema representation.

    :param pydantic_class: A Pydantic class that inherits from BaseModel
    :return: A dictionary representing the JSON schema of the input class
    """
    
    return json.dumps(pydantic_class.model_json_schema(), indent = 4)

if __name__ == '__main__':
    from langchain_core.messages import AnyMessage, HumanMessage, AIMessage 

    output = AIMessage(content = """
```json
{
  "reasoning_step": "I will revise the chapter again, ensuring it contains at least 10 paragraphs, and each paragraph has at least 10 sentences. I will maintain the improvements from the previous revision, focusing on subtlety, nuance, and plot progression while avoiding melodrama and excessive repetition. I will ensure that the descriptions are concise yet evocative, the dialogue is natural, and the pacing is dynamic. The focus will remain on showing rather than telling, with character development revealed through actions and interactions. I will also ensure that the chapter is focused, original, and compelling, and that it avoids clich\u00e9s and stereotypes.",
  "reflection_step": "I have carefully reviewed the previous revision and the new constraint. I will now ensure that the chapter is structured into at least 10 distinct paragraphs, each fulfilling the requirement of containing at least 10 sentences. I will also maintain the previous improvements, ensuring that the chapter is more nuanced, subtle, and engaging. The pacing will be carefully managed to maintain a balance between character development and plot advancement. The descriptions will be more concise and evocative, and the dialogue will be more natural. I will make sure that the chapter is focused, original, and compelling, avoiding melodrama and excessive repetition, and that the chapter is more sophisticated and less predictable.",
  "content": "The initial shock of Thorne's confession reverberated through Port Blossom like a tidal wave, washing away the facade of normalcy and revealing the deep cracks in the community's foundation, the news spreading like wildfire through the narrow streets and across the bustling marketplace, each whisper carrying the weight of betrayal and disbelief, the townspeople grappling with the realization that the man they had trusted, the man they had elected, was a wolf in sheep's clothing, his charismatic smile and reassuring words now replaced by the cold, hard truth of his corruption, the sense of security they had once felt replaced by a gnawing unease, the once-familiar faces of their neighbors now tinged with suspicion and anger, the quiet murmur of daily life replaced by the clamor of outrage and confusion, the once-harmonious community now fractured into a thousand different pieces, each one reflecting the pain and turmoil of the moment, the uncertainty of what was to come. Thorne's arrest was swift and decisive, the authorities moving with a newfound urgency to secure the man who had once held so much sway, the handcuffs clicking around his wrists a symbolic end to his reign of power, the once-proud mayor now a shadow of his former self, his eyes filled with a mixture of fear and resentment, the illusion of his invincibility shattered into a million pieces, his carefully constructed world crumbling around him, the weight of his crimes finally catching up to him, the whispers of his treachery now becoming a chorus of condemnation, the once-revered figure now a pariah in his own town, his legacy forever tarnished by his greed and deceit, his name a synonym for corruption and betrayal, a stark reminder of the darkness that can lurk beneath the surface of even the most seemingly respectable individuals. The community was forced to confront the uncomfortable truth about itself, the systemic flaws that had allowed Thorne to rise to power, the blindness that had allowed his corruption to fester, the apathy that had allowed him to manipulate the town for so long, the realization that they were not as innocent as they had believed, the uncomfortable understanding that they had been complicit in their own misfortune, the heavy burden of responsibility now weighing on their shoulders, the feeling that they had to make amends, the feeling that they had to change, the feeling that they had to seek justice, the feeling that they had to rebuild their community from the ground up, the feeling that they had to ensure that such a tragedy would never happen again, the weight of that responsibility palpable and profound.

  Divisions within the town emerged almost immediately, old grievances bubbling to the surface, new alliances forming along fault lines of suspicion and distrust, some demanding immediate justice and retribution, others advocating for a more measured approach, some seeking to protect their own interests, others genuinely striving for a better future, the once-united community now fractured into warring factions, each convinced of the righteousness of their cause, the streets once filled with the sounds of laughter and camaraderie now echoed with angry shouts and bitter accusations, the fragile peace of Port Blossom now shattered into a million pieces, the future uncertain and fraught with peril, the path to healing long and arduous, the challenges ahead seemingly insurmountable. Elara, the catalyst for this upheaval, found herself thrust into a new role, her courage and determination now the focus of both admiration and resentment, some hailing her as a hero, the brave truth-seeker who had exposed the corruption, others viewing her with suspicion, wary of the changes she had wrought, the weight of her actions now resting heavily on her shoulders, her name now synonymous with both hope and discord, her story now a legend that would be told and retold for generations, her impact on Port Blossom undeniable and irreversible, her journey far from over. She felt the weight of the town's expectations, the burden of responsibility heavy on her young shoulders, the realization that she had set into motion forces she could not fully control, the understanding that the future of Port Blossom now rested in part on her actions, the feeling that she had to guide them through this tumultuous time, the feeling that she had to help them rebuild their lives, the feeling that she had to help them heal from the wounds of betrayal, the feeling that she had to make things right, the feeling that she had to do her part to create a better future, the feeling that she could not just stand by and watch as the town she loved fell apart.

  The personal cost of her actions was also beginning to take its toll, the rifts within her own social circle widening, the divisions within her community causing her deep pain, the knowledge that she had shattered the fragile peace of Port Blossom weighing heavily on her conscience, the understanding that she had exposed the darkness but also unleashed chaos, the feeling that she had to do her part to help the community heal, the feeling that she had to find a way to bridge the divides, the feeling that she had a duty to help them move forward, the feeling that she had a responsibility to guide them towards a more just future, the understanding that she had to learn to live with the consequences of her actions, the realization that her journey was far from over. Elara retreated to her sanctuary, the small cottage overlooking the sea, seeking solace in the familiar sounds of the waves crashing against the shore, the vast expanse of the ocean a reminder of the endless possibilities that lay ahead, the quiet solitude a temporary escape from the turmoil of the town, the need to reflect and gather her strength palpable, the understanding that she could not allow the chaos to consume her, the determination to find a way to help her community heal and rebuild, the conviction that she could not give up hope, the belief that she could make a difference, the resolve to face the challenges ahead with courage and determination. She ran her fingers over the worn pages of her sister's journal, the familiar words a comfort, the memories of her sister's courage a source of inspiration, the reminder that she was not alone in her fight for justice, the understanding that her sister's legacy lived on through her actions, the feeling that she had a duty to honor her memory, the determination to continue the fight for truth and justice, the belief that she could make a difference, the resolve to face the challenges ahead with courage and determination, the quiet whisper of her sister's voice in her heart, urging her to keep going.

  The days that followed were a blur of meetings, arguments, and quiet moments of reflection, the townspeople struggling to come to terms with the enormity of the betrayal, the discussions ranging from calls for immediate retribution to pleas for understanding and reconciliation, the old wounds of the past being reopened, new ones being inflicted, the path forward unclear and uncertain, the need for a leader palpable, the hope that someone would step forward to guide them through the darkness, the understanding that they had to rebuild their community, the feeling that they had to create a better future, the sense that they had to find a way to heal, the belief that they could emerge from the ashes stronger and more united. Elara found herself drawn into the center of the storm, the townspeople seeking her guidance and support, her quiet strength and unwavering determination a beacon of hope in the midst of the chaos, the weight of their expectations heavy on her shoulders, the responsibility of leadership thrust upon her, the understanding that she had to use her influence wisely, the feeling that she had to be the voice of reason, the feeling that she had to help them find their way, the feeling that she had to guide them towards a better future, the feeling that she had to be the anchor in the storm, the feeling that she had to be strong for them, the feeling that she had to be brave for them, the feeling that she had to be the change she wanted to see in Port Blossom. The local council, once a bastion of Thorne's power, was now in disarray, the members scrambling to distance themselves from his crimes, the old guard clinging to their positions, a new generation of voices rising to challenge the status quo, the struggle for power creating further divisions within the town, the need for a new system of governance apparent, the understanding that they had to start from scratch, the feeling that they had to build something new and better, the feeling that they had to learn from their mistakes, the feeling that they had to create a future where such corruption could never take root again, the feeling that they had to do it together, the hope that they could overcome the challenges before them.

  The whispers of dissent grew louder, the old guard clinging to their power, using fear and misinformation to sow further division, the newly emboldened voices of change rising to challenge the status quo, the battle for the soul of Port Blossom now underway, the future of the town hanging in the balance, the need for unity and understanding more urgent than ever, the hope that they could find a way to bridge the divides, the understanding that they had to rebuild their community, the feeling that they had to create a better future, the feeling that they had to work together, the feeling that they had to find common ground, the feeling that they had to choose hope over despair. The small businesses in the town struggled to stay afloat, their livelihoods threatened by the economic uncertainty and the lingering suspicion, the once-thriving marketplace now a shadow of its former self, the community's resilience being tested to its limits, the need for support and solidarity more crucial than ever, the understanding that they were all in this together, the feeling that they had to help each other, the feeling that they had to find a way to survive, the feeling that they had to keep moving forward, the feeling that they had to find a way to rebuild their lives, the belief that they could overcome the challenges before them, the determination to persevere. Elara found herself drawn to the heart of the community, the marketplace, where she had once felt so lost and alone, now a place where she was sought out for guidance and support, the people looking to her for answers, the realization that they had placed their faith in her, the feeling that she could not let them down, the feeling that she had to do everything in her power to help them, the feeling that she had to be their leader, the feeling that she had to be their guiding light, the feeling that she had to be their strength, the feeling that she had to be their hope, the feeling that she had to be their voice.

   She spent her days listening to the concerns of the townspeople, offering words of encouragement and hope, working to bridge the divides that had formed, her unwavering commitment to justice and her genuine empathy for their struggles earning her the respect of many, the understanding that she was not just a hero, but a member of their community, the realization that she was just as vulnerable as they were, the feeling that they were all in this together, the feeling that they had to support each other, the feeling that they had to heal together, the feeling that they had to rebuild their community together, the feeling that they had to create a better future together, the feeling that they had to find their way together, the feeling that they had to trust each other, the feeling that they had to believe in each other. The children of Port Blossom, once full of laughter and play, now carried the weight of the town's turmoil on their small shoulders, the innocence of their childhoods threatened by the chaos and uncertainty, the need to protect them and ensure their safety more paramount than ever, the understanding that they were the future of Port Blossom, the feeling that they had to help them understand, the feeling that they had to give them hope, the feeling that they had to protect them from the darkness, the feeling that they had to show them that things could get better, the feeling that they had to be their strength, the feeling that they had to be their hope, the feeling that they had to be their guiding light, the feeling that they had to be their future. Elara started spending time with them, telling them stories of courage and resilience, teaching them the importance of truth and justice, offering them a glimpse of hope in the midst of the darkness, her kindness and gentle nature bringing smiles back to their faces, the understanding that they were not forgotten, the feeling that they were still loved, the feeling that they were still safe, the feeling that they were still part of something bigger than themselves, the feeling that they were still the future of Port Blossom, the feeling that they were still the hope of Port Blossom.

  The nights were filled with quiet contemplation, Elara wrestling with the weight of her responsibilities, the understanding that she had to make difficult choices, the feeling that she had to be strong, the feeling that she had to be wise, the feeling that she had to be brave, the feeling that she had to be the leader they needed, the feeling that she had to do what was right, the feeling that she could not falter, the feeling that she could not give up, the feeling that she had to keep going, the feeling that she had to find a way to move forward, the feeling that she had to help them heal, the feeling that she had to help them rebuild, the feeling that she had to help them create a better future, the feeling that she had to be there for them. She revisited her sister's journal, the words now resonating with a deeper meaning, the understanding that her sister's fight for justice was not in vain, the feeling that she had to carry on her legacy, the feeling that she had to make her proud, the feeling that she had to continue to seek the truth, the feeling that she had to continue to fight for justice, the feeling that she had to continue to believe in the power of hope, the feeling that she had to continue to be brave, the feeling that she had to continue to be strong, the feeling that she had to continue to be the voice of change, the feeling that she had to continue to be the leader they needed. The sea became her confidante, the waves washing away her doubts and fears, the vastness of the ocean reminding her that she was part of something bigger than herself, the quiet rhythm of the tides a constant source of comfort, the knowledge that she was not alone in her struggles, the feeling that she had the strength to face the challenges ahead, the feeling that she had the courage to keep going, the feeling that she had the wisdom to guide her community, the feeling that she had the hope to create a better future, the feeling that she had the power to make a difference.

  Elara began to formulate a plan, a way to rebuild Port Blossom from the ground up, a vision of a community that was more just, more equitable, and more united, the understanding that they had to start with the foundation of their governance, the feeling that they had to create a system that was transparent and accountable, the feeling that they had to empower the people, the feeling that they had to give them a voice, the feeling that they had to give them a stake in their own future, the feeling that they had to find a way to heal their wounds, the feeling that they had to learn from their mistakes, the feeling that they had to create a better future, the feeling that they had to work together, the feeling that they had to trust each other, the feeling that they had to believe in each other. She reached out to the various factions within the town, inviting them to come together, to put aside their differences, to work towards a common goal, the understanding that they were all part of the same community, the feeling that they were all in this together, the feeling that they had to support each other, the feeling that they had to heal together, the feeling that they had to rebuild together, the feeling that they had to create a better future together, the feeling that they had to find their way together, the feeling that they had to believe in each other. The initial meetings were tense, the old wounds still raw, the mistrust still palpable, but Elara persevered, her unwavering commitment to justice and her genuine empathy for their struggles slowly breaking down the barriers between them, the understanding that they all wanted the same thing, the feeling that they could work together, the feeling that they could overcome their differences, the feeling that they could create a better future, the feeling that they could heal their community, the feeling that they could find their way, the feeling that they could trust each other, the feeling that they could believe in each other.

   The townspeople began to see a glimmer of hope, a belief that they could rebuild, a sense that they could overcome the challenges before them, the understanding that they had to work together, the feeling that they had to support each other, the feeling that they had to heal together, the feeling that they had to create a better future together, the feeling that they had to find their way together, the feeling that they had to trust each other, the feeling that they had to believe in each other, the feeling that they had to move forward, the feeling that they had to learn from their mistakes, the feeling that they had to be stronger, the feeling that they had to be wiser, the feeling that they had to be braver, the feeling that they had to be better. Elara continued to lead them, her quiet strength and unwavering determination a source of inspiration, the understanding that she was not just a leader, but a member of their community, the realization that she was just as vulnerable as they were, the feeling that they were all in this together, the feeling that they had to support each other, the feeling that they had to heal together, the feeling that they had to rebuild their community together, the feeling that they had to create a better future together, the feeling that they had to find their way together, the feeling that they had to trust each other, the feeling that they had to believe in each other, the feeling that they had to be a beacon of hope for each other. The journey ahead was still long and arduous, but for the first time since Thorne's confession, the people of Port Blossom felt a sense of hope, a belief that they could emerge from the darkness stronger and more united, the understanding that they had the power to shape their own future, the feeling that they had the courage to face the challenges ahead, the feeling that they had the wisdom to rebuild their community, the feeling that they had the hope to create a better future, the feeling that they had each other, the feeling that they had Elara, the feeling that they had a chance to start again, the feeling that they had a chance to heal, the feeling that they had a chance to move forward, the feeling that they had a chance to be better, the feeling that they had a chance to be the community that they always knew they could be.
"chapter_name": "Shattered Shores"
}
```                       
""")
    try:
        x = cleaning_llm_output(output)    
    except BadFormattedJson as e:
        print('-')
    try:
        WriterStructuredOutput(**x)
    except Exception as e:
        print('-')
    print('-')

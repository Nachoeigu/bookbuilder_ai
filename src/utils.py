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
    chapters_summaries: List[str] = Field(description = "A list where each element is a STRING summary of each chapter. Each element on the list should contain a detailed description of what happen on it, with well explained intro-development-ending stages. Each summary MUST HAVE a length of 5 sentences minimum. Optimized based on the reasoning and reflection steps.")

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
            raise BadFormattedJson({"error": f"While trying to format the JSON object you have generated we detect the following error: {e.args[0]}", "detail": f"Error location: Line {e.lineno}, Column {e.colno}", "context": f"{e.doc[e.pos-50:e.pos+50]}"})




def get_json_schema(pydantic_class: BaseModel) -> dict:
    """
    This function receives a Pydantic class and returns its JSON schema representation.

    :param pydantic_class: A Pydantic class that inherits from BaseModel
    :return: A dictionary representing the JSON schema of the input class
    """
    data = pydantic_class.model_json_schema()
    schema_description = data['description']
    data_keys = {key: {"description": value['description'], "type": value['type']} for key, value in data['properties'].items()}
    description = f"The schema is about: '{schema_description}'\n\nThis is the schema definition:\n" + json.dumps(data_keys, indent = 4)
    return description


if __name__ == '__main__':
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    x = get_json_schema(WriterStructuredOutput)

    reply = AIMessage(content = "```json\n{\n\"reasoning_step\": \"I need to expand the chapter to meet the requirements of 8 paragraphs with at least 9 sentences each. I will add more detail to the existing scenes, focusing on Mark's investigative process and his interactions with Sarah and Emily. I'll also introduce the threatening note in a more dramatic fashion, emphasizing the danger Mark is in. The goal is to build suspense and intrigue while keeping the narrative fast-paced and action-driven. I'll ensure that each new paragraph and sentence adds value to the story, either by advancing the plot, developing the characters, or enhancing the atmosphere. The unseen figure's presence will be a recurring motif, adding an extra layer of mystery and tension.\",\n\"reflection_step\": \"The challenge is to add more content without making the chapter feel bloated or slow. Every addition must serve a purpose. I need to be mindful of the pacing, ensuring that the new details enhance the story's flow rather than hinder it. The descriptions need to be vivid but concise, painting a picture of Harmony Creek and its inhabitants without getting bogged down in unnecessary details. Mark's internal conflict should be conveyed through his actions and interactions, not through lengthy introspection. The dialogue must remain sharp and to the point. The ending of the chapter needs to be particularly strong, leaving the reader on the edge of their seat, eager to find out what happens next.\",\n\"content\": \"The crisp morning air, thick with the scent of pine and damp earth, was shattered by a single gunshot that echoed through the woods. Hunters were a common sight in the forests surrounding Harmony Creek, but this shot felt different—final and deliberate. A few hundred yards from the well-trodden path, Arthur Jenkins lay motionless on a bed of fallen leaves, his prized hunting rifle resting beside him. The scene was picture-perfect, too perfect. A single, precise wound marked his chest; there was no sign of a struggle, no disturbance in the surrounding foliage. It looked like a hunting accident, but the meticulous arrangement screamed murder. Someone had gone to great lengths to stage the scene, every detail carefully considered. From a hidden vantage point, an unseen figure observed the unfolding drama, a ghost in the periphery. Their eyes, cold and calculating, tracked the movements of the first responders, a slight smile playing on their lips as they melted back into the woods, leaving the scene undisturbed, their presence unknown, their motives a chilling mystery.\\n\\nMark Thompson arrived to find the area cordoned off, yellow tape fluttering in the breeze like a macabre decoration. His boots crunched on the frost-covered leaves as he approached, each step heavy with dread. He had known Arthur Jenkins since they were kids, their bond forged through countless shared adventures and unwavering loyalty. Seeing his best friend like this, lifeless and cold, sent a chill down his spine that had nothing to do with the autumn air. Sheriff Emily Carter, another childhood friend, stood nearby, her expression grim. \\\"It looks like an accident, Mark,\\\" she said, her voice unusually tight. \\\"But something feels off.\\\" He nodded, his gaze fixed on the too-perfect scene, his instincts screaming that this was no accident. He knelt beside Arthur, a wave of sorrow washing over him as he took in the details, the unnatural stillness of his friend's body, the way the light caught the edges of the wound, the absence of any sign of a struggle.\\n\\n\\\"We need to treat this as a homicide, Emily,\\\" Mark stated, his voice firm despite the tremor in his heart. \\\"This was staged.\\\" He crouched beside Arthur's body, his trained eye picking up the subtle inconsistencies that others might miss. The angle of the wound, the lack of blood spatter, the undisturbed ground—it all pointed to murder. Emily hesitated, her eyes darting nervously around the scene, avoiding Mark's probing gaze. \\\"I don't know, Mark,\\\" she said, her voice barely above a whisper. \\\"It's Arthur. Everyone loved him.\\\" Mark stood up, his gaze hardening as he met Emily's eyes. \\\"That's exactly why we need to do this right,\\\" he said, his resolve strengthening with each passing moment, a steely determination taking root in his gut. He knew he had to uncover the truth, no matter how painful it might be, no matter who might be implicated.\\n\\nLater that day, Sarah Jenkins, Arthur's widow, arrived at Mark's small, cluttered office, her eyes red-rimmed from crying. She was a striking woman, her beauty now tinged with a deep sorrow that seemed to age her beyond her years. \\\"Mark, you have to find out what happened,\\\" she pleaded, her voice cracking as she fought back tears. \\\"Arthur wouldn't be so careless. He was the best hunter I knew.\\\" Mark, who had always harbored a deep respect for Sarah, felt a pang of sympathy for her. He saw the raw grief in her eyes, the desperation that mirrored his own. \\\"I will, Sarah,\\\" he promised, his voice unwavering, a vow he intended to keep. \\\"I'll find out who did this.\\\" He placed a comforting hand on her arm, feeling the tension in her muscles, the silent plea for justice in her touch, the unspoken bond between them solidifying in that shared moment of grief and determination.\\n\\nMark began his investigation by revisiting the scene of Arthur's death, hoping to find something that had been overlooked. He meticulously combed through the area, his eyes scanning every inch of the ground, every leaf and twig. He found nothing new, but the feeling that he was missing something crucial gnawed at him. The perfection of the scene was its most unsettling aspect; it was as if the killer had meticulously planned every detail, leaving nothing to chance. As he walked back to his car, a glint of metal caught his eye, reflecting the weak sunlight filtering through the trees. He bent down and picked up a small, intricately designed locket, half-hidden beneath a pile of leaves. It was Sarah's; he recognized it instantly, a familiar piece she often wore. A knot tightened in his stomach as he wondered what she had been doing out here, a new layer of complexity added to the already intricate puzzle.\\n\\nBack at Arthur's house, a stately Victorian on the edge of town, Mark started to go through his friend's belongings. The house felt empty and silent, the air thick with the lingering scent of Arthur's pipe tobacco and the faint, sweet aroma of Sarah's perfume. He moved from room to room, each filled with memories of happier times, of laughter and camaraderie now replaced by an eerie silence. In Arthur's study, a room lined with bookshelves and hunting trophies, Mark began to search for anything that might provide a clue. He sifted through papers, examined photographs, and scanned the titles of the countless books, hoping to find something that would shed light on Arthur's death. The room was a reflection of Arthur's life—orderly, successful, and filled with the trappings of a man who had everything. Yet, beneath the surface, Mark sensed a hidden layer, a secret that Arthur had kept hidden from the world, a secret that might have cost him his life.\\n\\nAs he was about to give up, Mark noticed a small, almost imperceptible gap in the back of a drawer in Arthur's large oak desk. It was a detail he might have missed had he not been trained to look for such anomalies. He pried it open and found a hidden compartment containing a single, folded piece of paper, his pulse quickening with anticipation. His hands trembled slightly as he unfolded it, his heart pounding in his chest. The note was short and to the point, written in a hurried scrawl: \\\"Stop digging, or you're next.\\\" A chill ran down his spine as he realized the true danger he was in, the words on the paper a stark confirmation of his suspicions. This was no random act of violence; it was a targeted threat, a warning from someone who knew about his investigation and was prepared to silence him. He carefully placed the note in an evidence bag, his mind racing, trying to piece together the fragments of information, the implications of this new threat sinking in. The killer was aware of his efforts, and they were prepared to do whatever it took to stop him, even if it meant adding another body to the count.\\n\\n The weight of the situation pressed down on Mark, the realization that he was now a target settling in like a heavy shroud. He looked around Arthur's study, the familiar surroundings now feeling menacing. Every shadow seemed to hide a potential threat, every creak of the floorboards a possible footstep of the killer. He knew he couldn't back down; he had made a promise to Sarah, and more importantly, to Arthur. He had to find the truth, no matter the cost. But now, the stakes were higher, the danger more palpable. He was no longer just investigating a murder; he was fighting for his own survival. As he left the house, he glanced back, a sense of foreboding washing over him, knowing that Harmony Creek was no longer the safe haven he once thought it was. The unseen figure watched him from a distance, their presence a silent promise of the danger to come, a constant reminder that he was being hunted as he hunted.\n```")

    x = cleaning_llm_output(llm_output = reply)
    try:
        a = WriterStructuredOutput(**x)
    except Exception as e:
        print(e)

    print('-')

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
    
    return json.dumps(pydantic_class.model_json_schema(), indent = 4)

if __name__ == '__main__':
    from langchain_core.messages import AnyMessage, HumanMessage, AIMessage 

    output = AIMessage(content = """
```json\n{\n    \"translated_content\": \"El año es 2050. Un silencio, una quietud preñada de expectación, cubría el globo. Era un silencio tan profundo que casi se podía oír el latido colectivo de miles de millones de personas, todas sintonizadas en un único y definitorio momento. Elon Musk, un nombre que se había convertido en sinónimo de la audaz búsqueda de lo imposible, se encontraba bañado en el frío y etéreo resplandor de mil pantallas. Detrás de él, la Starship, un titán plateado, un testamento al ingenio humano, brillaba bajo la vasta extensión del cielo de Texas. Con una voz que portaba el peso de la historia, una mezcla de férrea determinación y celo visionario, pronunció las palabras que alterarían para siempre la trayectoria de la humanidad: \\\"Hoy, nos encontramos al borde de una nueva era. Hoy, nos embarcamos en la primera misión tripulada a Marte\\\". No era un mero anuncio; era el disparo de salida en una carrera hacia las estrellas, una llamada de clarín que resonó a través de los continentes, encendiendo una tormenta de sueños y aspiraciones. El mundo estalló, no en un simple aplauso, sino en un rugido visceral de aprobación, un grito primigenio de una especie que anhela romper las cadenas de su cuna terrestre, un sonido que reverberó a través de ciudades y pueblos, a través de montañas y océanos, uniendo a la humanidad en un momento compartido de asombro y maravilla. Esto era la historia desplegándose, un momento crucial que trascendía fronteras, ideologías y generaciones, uniendo a la humanidad en un sueño compartido de alcanzar el cosmos, un sueño tan antiguo como el tiempo mismo, ahora finalmente a nuestro alcance.\\n\\nEn un pequeño y abarrotado apartamento en Moscú, donde el aroma del té preparándose se mezclaba con el olor de los libros viejos, la Dra. Anya Sharma sintió un temblor recorrer su propio ser. No era solo el retumbar de los motores de la Starship lo que sentía, sino el cambio sísmico en la trayectoria de su propia vida, un punto de inflexión que había anticipado durante mucho tiempo pero que nunca creyó realmente que llegaría. Su cabello negro enmarcaba un rostro grabado con una vida de incesante curiosidad, sus ojos, oscuros y luminosos, reflejaban las imágenes parpadeantes en la pantalla, absorbiendo cada detalle, cada matiz del trascendental anuncio. Anya había pasado años adentrándose en los misterios de la vida, su mirada fija en las estrellas, su mente lidiando con las profundas preguntas de la existencia más allá de la Tierra, buscando respuestas en la vasta extensión del cosmos. Esta misión era la culminación de su odisea intelectual, una oportunidad para tocar la misma tela de sus sueños, para caminar en otro mundo, para buscar respuestas a preguntas que habían atormentado a la humanidad durante milenios. Sin embargo, también era un precipicio, un salto hacia lo vasto desconocido que se extendía más allá del reconfortante abrazo de la Tierra, un viaje del que podría no haber retorno. Una sola lágrima rebelde trazó un camino por su mejilla, un testimonio de las emociones conflictivas que surgían en su interior: la euforia del descubrimiento y el temor de dejar atrás todo lo que conocía, la familiar comodidad de su pequeño apartamento, las bulliciosas calles de Moscú, los rostros de sus amigos y colegas, todo desvaneciéndose en un recuerdo lejano. Era una sinfonía agridulce que se desarrollaba en la tranquila soledad de su apartamento, una melodía de esperanza y miedo, de anticipación y pérdida, un preludio conmovedor a la gran aventura que la esperaba.\\n\\nLejos de allí, en el tranquilo y minimalista entorno de su hogar japonés, Kenji Tanaka recibió la noticia con una calma exterior que enmascaraba una tempestad interior, un torbellino de emociones que luchaba por contener. Su hogar, un reflejo de su mente ordenada, era un santuario de precisión, donde cada objeto tenía su lugar, cada elemento armonizado en perfecto equilibrio, un testimonio de su naturaleza meticulosa y su búsqueda de toda la vida del orden y la eficiencia. Se sentó, un estudio en quietud, su mirada fija en la transmisión en vivo, sus dedos trazando la superficie lisa y desgastada de un pequeño recuerdo metálico: un fragmento de una misión pasada, un recordatorio constante tanto del triunfo como de la tragedia, un vínculo tangible con un pasado del que nunca podría escapar. Kenji, un hombre que esculpía metal y circuitos en vasijas de sueños, veía en la misión a Marte una oportunidad para redefinir los límites de la ingeniería, para construir no solo una nave espacial, sino una línea de vida entre mundos, un puente entre la Tierra y una nueva frontera. Pero el espectro de un fracaso pasado, una misión que había terminado en desamor y pérdida, se cernía en su mente, proyectando una larga sombra sobre sus aspiraciones, un recordatorio constante de la fragilidad del esfuerzo humano frente al cosmos implacable. Luchó con los fantasmas de esa tragedia, los rostros de los colegas perdidos destellando ante sus ojos, su recuerdo un peso pesado en su alma, su sacrificio una carga que llevaba consigo todos los días. ¿Podría enfrentarse a la oscuridad de nuevo, al vacío implacable que una vez se había cobrado a sus amigos, al frío y silencioso vacío que los había tragado enteros? La misión ofrecía redención, una oportunidad para honrar su sacrificio, para construir un futuro digno de su recuerdo, pero también exigía que se enfrentara a sus miedos más profundos, el miedo a fallar no solo a sí mismo, sino a aquellos que habían depositado su confianza en él, el miedo a repetir los errores del pasado.\\n\\nMuy por encima de la Tierra, a bordo de la Estación Espacial Internacional, la Capitana Svetlana Morozova, una cosmonauta veterana cuyo nombre estaba grabado en los anales de la exploración espacial, observó los acontecimientos que se desarrollaban con una mirada experta, una mirada que había visto tanto la impresionante belleza como la aterradora inmensidad del espacio. Sus ojos acerados, ventanas a un alma que había mirado al abismo y regresado, estaban fijos en la distante esfera azul que era su hogar, un frágil oasis de vida en el vasto desierto cósmico. Svetlana, con su cabello corto y un comportamiento que irradiaba una autoridad tranquila, había pasado más tiempo de su vida a la deriva en el mar cósmico que en la Tierra, su cuerpo y mente sintonizados con los ritmos del espacio, el silencio, la ingravidez, la constante conciencia de la delgada línea entre la vida y la muerte. Esta nueva misión, el audaz salto a Marte, resonó profundamente en su interior, despertando una mezcla familiar de emoción y un profundo, casi melancólico, sentido de soledad, un sentimiento de aislamiento que solo aquellos que se habían aventurado más allá del abrazo de la Tierra podían comprender realmente. Había bailado con las estrellas, caminado en el vacío y sentido el aliento helado del cosmos en su piel, había presenciado vistas que pocos humanos habían visto, había experimentado la profunda belleza y la aterradora indiferencia del universo. Sin embargo, cada viaje a la negrura también había sido un viaje lejos de la calidez de la conexión humana, un sacrificio hecho en el altar de la exploración, una compensación entre la búsqueda del conocimiento y la comodidad de la compañía humana. Mientras miraba a la Tierra que se alejaba, no solo veía un planeta, sino los rostros de sus seres queridos, sus sonrisas un recuerdo que se desvanecía, sus voces un eco lejano, su presencia una calidez que pronto tendría que dejar atrás. Esta misión sería la más desafiante hasta el momento, un billete de ida a lo desconocido, y llevaba el peso de esa responsabilidad con un estoicismo nacido de años pasados desafiando las probabilidades, una promesa silenciosa de llevar a su tripulación a salvo al nuevo mundo y de llevar la antorcha del espíritu humano a los confines más lejanos del sistema solar, un testimonio del indomable espíritu de exploración que ardía en su interior.\\n\\nLos meses siguientes fueron un crisol, forjando los sueños de miles en la realidad de unos pocos elegidos. El proceso de selección de SpaceX fue un espectáculo global, un crisol diseñado para probar no solo la destreza física e intelectual de los candidatos, sino también el núcleo mismo de su ser, para despojar lo superficial y revelar la verdadera esencia de su carácter. Los aspirantes de todas las naciones, todos los credos, todos los ámbitos de la vida convergieron, sus ojos fijos en el premio, sus corazones latiendo con una mezcla de esperanza y temor, cada uno con su propia historia única, sus propias razones para querer embarcarse en este extraordinario viaje. Fueron sometidos a un guante de pruebas, cada una diseñada para llevarlos a sus límites y más allá, para probar su resistencia, su capacidad de recuperación, su capacidad para funcionar bajo una inmensa presión. Las pruebas físicas, brutales en su intensidad, los dejaban sin aliento, sus músculos gritando en protesta, sus cuerpos llevados al borde del colapso. Las evaluaciones psicológicas se adentraron en los recovecos más profundos de sus mentes, exponiendo sus miedos, sus vulnerabilidades, sus fortalezas ocultas, sus motivaciones más profundas, dejando al descubierto sus almas para el escrutinio del comité de selección. Los simuladores, fríos e implacables, replicaron las presiones aplastantes, el frío que calaba hasta los huesos y los peligros siempre presentes del espacio, probando su capacidad para funcionar bajo coacción, para tomar decisiones de vida o muerte en un abrir y cerrar de ojos, para mantener la calma y la racionalidad frente a probabilidades abrumadoras. Las cámaras de aislamiento, austeras y silenciosas, se convirtieron en sus prisiones temporales, donde lucharon con sus demonios internos, sus dudas, sus esperanzas y sus sueños, el silencio amplificando la cacofonía dentro de sus almas, obligándolos a confrontar su propia mortalidad, su propia insignificancia frente al vasto cosmos.\\n\\nAnya, empujada a este torbellino de ambición y competencia, se encontró lidiando no solo con los desafíos externos sino también con una batalla interna, una lucha para reconciliar sus sueños con la abrumadora realidad de la misión. Los rigores físicos, aunque exigentes, eran casi una distracción bienvenida de la soledad de la cámara de aislamiento, una forma de canalizar su energía nerviosa en esfuerzo físico. Fue allí, en el silencio estéril, donde sus dudas comenzaron a aflorar, susurrando preguntas insidiosas en la oscuridad, sondeando sus vulnerabilidades, cuestionando su resolución. ¿Estaba realmente preparada para este viaje, no solo científicamente, sino emocionalmente, mentalmente, espiritualmente? ¿Podría soportar el peso de lo desconocido, la potencial soledad de una vida entre las estrellas, el aislamiento de todo lo que había conocido y amado? Sin embargo, cada desafío que superaba, cada prueba que pasaba, alimentaba una creciente brasa de determinación dentro de ella, una resolución para demostrarse a sí misma y al mundo que era digna de esta oportunidad. Su perspicacia científica era innegable, sus ideas a menudo obtenían asentimientos de aprobación de los instructores experimentados, su conocimiento de astrobiología demostró ser un activo invaluable en los escenarios simulados. Encontró una inesperada afinidad con Kenji, su pasión compartida por la misión formando un puente a través de sus orígenes tan diferentes, sus conversaciones una reunión de mentes, una fusión de perspectivas. Sus conversaciones nocturnas, alimentadas por café tibio y un sentido compartido de asombro, se convirtieron en un santuario, un espacio donde podían compartir sus esperanzas, sus miedos y sus sueños de un futuro donde la humanidad había dado sus primeros pasos tentativos en otro mundo, un futuro que ahora estaban moldeando activamente.\\n\\nKenji, en medio de la cacofonía del entrenamiento, encontró consuelo en la precisión de su trabajo, en el acto tangible de la creación, en la transformación de materias primas en máquinas intrincadas. Sobresalió en los desafíos de ingeniería, su mente un instrumento finamente afinado que podía diseccionar problemas complejos y sintetizar soluciones elegantes, sus manos moviéndose con una gracia practicada, un testimonio de años dedicados a perfeccionar su oficio. Cada tarea era una oportunidad para perderse en la intrincada danza del diseño y la función, para crear orden a partir del caos, para imponer su voluntad sobre las leyes inquebrantables de la física. Pero fueron las simulaciones las que realmente pusieron a prueba su temple, las que lo obligaron a confrontar a los demonios de su pasado, los fantasmas que aún acechaban sus momentos de vigilia. En un escenario particularmente angustioso, una brecha simulada en el hábitat marciano, se encontró transportado de regreso a esa fatídica misión, la que había terminado en tragedia, la que había destrozado su confianza y lo había dejado cuestionando sus habilidades. El pánico amenazó con engullirlo, los rostros de sus amigos perdidos destellando ante sus ojos, sus voces resonando en su memoria, el silencio escalofriante del vacío presionándolo. Pero entonces, vio a Anya, su rostro grabado con determinación, su voz tranquila y firme en medio del caos simulado, su presencia un faro de esperanza en la oscuridad. Sacó fuerzas de su presencia, de su propósito compartido, y con un enfoque renovado, ideó una solución, sus manos moviéndose con una gracia practicada, su mente corriendo contra el reloj, cada acción impulsada por una necesidad desesperada de tener éxito, de expiar el pasado. Lograron sellar la brecha, la crisis simulada evitada, el silencio regresando, pero esta vez, era un silencio de triunfo, no de desesperación. A raíz de eso, a medida que la adrenalina disminuía, se encontró más atraído por Anya, su vínculo forjado en el crisol de la experiencia compartida, un entendimiento silencioso pasando entre ellos, un reconocimiento de la fuerza que encontraron el uno en el otro, un respeto mutuo nacido de la adversidad compartida.\\n\\nSvetlana, una veterana de innumerables simulaciones, se acercó al proceso de selección con la calma segura de una comandante experimentada, su comportamiento una máscara de confianza inquebrantable, cada acción deliberada y con un propósito. Su experiencia era su armadura, su compostura un escudo contra las presiones que rompían a individuos menores, su mente una fortaleza de disciplina y control. Había mirado al abismo antes, bailado con la muerte en el vacío del espacio, y emergió más fuerte, su resolución endurecida en el crisol de la supervivencia, su espíritu templado por las realidades implacables de los viajes espaciales. Las pruebas físicas eran una mera formalidad, su cuerpo perfeccionado por años de entrenamiento riguroso, sus músculos acondicionados a las demandas de la gravedad cero, sus reflejos agudizados por innumerables horas pasadas en simuladores. Las evaluaciones psicológicas, aunque indagatorias, no le depararon sorpresas; hacía tiempo que había hecho las paces con sus demonios internos, había aprendido a controlar sus miedos, a canalizar sus emociones en acciones productivas. Era su liderazgo lo que realmente la distinguía, su capacidad para inspirar, para motivar, para unir a un grupo dispar de individuos en un equipo cohesivo, su presencia una influencia calmante en medio del caos. En las simulaciones grupales, tomó el mando de forma natural, su voz tranquila y autoritaria, sus decisiones rápidas y decisivas, cada orden suya con el peso de la experiencia, la confianza de una líder que sabía cómo navegar las traicioneras aguas del espacio. Reconoció el talento en bruto en Anya, la precisión meticulosa en Kenji, y vio en ellos el futuro de la exploración espacial, la próxima generación de pioneros que llevarían la antorcha de la curiosidad humana a nuevos mundos. Los tomó bajo su protección, compartiendo su conocimiento, su experiencia, su sabiduría ganada con esfuerzo, moldeándolos en un equipo que no solo podría sobrevivir al viaje sino prosperar en las áridas llanuras de Marte, un equipo que llevaría las esperanzas y los sueños de la humanidad sobre sus hombros.\\n\\nY entonces, llegó el día, el día que quedaría grabado para siempre en la memoria colectiva de la humanidad, un día que se relataría en los libros de historia, en canciones, en historias transmitidas de generación en generación. Elon Musk, un director de orquesta de pie ante su orquesta, subió al escenario una vez más, el mundo conteniendo la respiración en ansiosa anticipación, el silencio tan profundo que parecía amplificar el latido de cada corazón. Los nombres que pronunció resonaron en todo el mundo, llevando consigo el peso de los sueños, la carga de las expectativas y la promesa de un nuevo amanecer, un nuevo capítulo en la historia humana: \"Dra. Anya Sharma, astrobióloga; Kenji Tanaka, ingeniero jefe; y la Capitana Svetlana Morozova, comandante de la misión\". En ese instante, las vidas de tres individuos se alteraron irrevocablemente, sus destinos entrelazados con el destino de una misión que se atrevía a alcanzar las estrellas, una misión que encarnaba las esperanzas y los sueños de toda una especie. Para Anya, fue una validación del trabajo de su vida, una oportunidad para reescribir los libros de texto, para tocar el rostro de otro mundo, para buscar respuestas a preguntas que la habían cautivado desde la infancia. Para Kenji, fue la redención, una oportunidad para honrar el pasado y construir un futuro entre las estrellas, para crear un legado que se extendería mucho más allá de su propia vida. Para Svetlana, fue el mando supremo, un viaje a lo desconocido, una responsabilidad que abrazó con un coraje silencioso que se había convertido en su sello distintivo, una misión final y definitoria en una carrera dedicada a empujar los límites de la exploración humana. Mientras se encontraban al borde de la historia, llevaban consigo no solo sus propias esperanzas y sueños, sino las aspiraciones de todo un planeta, un anhelo colectivo de romper las cadenas de la Tierra y abrazar las ilimitadas posibilidades del cosmos. Eran la vanguardia, los pioneros, los primeros emisarios de la Tierra al Planeta Rojo, y su viaje estaba a punto de comenzar, un viaje que los llevaría más lejos de casa de lo que cualquier humano había ido antes, un viaje al corazón de lo desconocido.\"\n}\n```
""")
    try:
        x = cleaning_llm_output(output)    
    except BadFormattedJson as e:
        print('-')
    try:
        TranslatorStructuredOutput(**x)
    except Exception as e:
        print('-')
    print('-')

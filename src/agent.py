import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from langgraph.graph import StateGraph
from src.utils import State, GraphInput, GraphOutput, GraphConfig
from src.nodes import *
from src.routers import *

def defining_nodes(workflow: StateGraph):
    workflow.add_node("instructor", get_clear_instructions)
    workflow.add_node("human_feedback", read_human_feedback)
    workflow.add_node("brainstorming_idea_writer", making_general_story_brainstorming)
    workflow.add_node("brainstorming_idea_critique", brainstorming_idea_critique)
    workflow.add_node("brainstorming_narrative_writer", making_narrative_story_brainstorming)
    workflow.add_node("brainstorming_narrative_critique", brainstorming_narrative_critique)
    workflow.add_node("writer", generate_content)
    workflow.add_node("writing_reviewer", evaluate_chapter)
    workflow.add_node("translator", generate_translation)
    workflow.add_node("assembler", assembling_book)

    return workflow

def defining_edges(workflow: StateGraph):
    workflow.add_conditional_edges(
        "instructor",
        should_go_to_brainstorming_idea_writer
    )
    workflow.add_edge("human_feedback","instructor")
    workflow.add_conditional_edges(
        "brainstorming_idea_writer",
        should_continue_with_idea_critique
    )
    workflow.add_conditional_edges(
        "brainstorming_narrative_writer",
        should_continue_with_narrative_critique
    )
    workflow.add_conditional_edges(
        "translator",
        has_translator_ended_book
    )
    workflow.add_edge("brainstorming_idea_critique","brainstorming_idea_writer")
    workflow.add_edge("brainstorming_narrative_critique","brainstorming_narrative_writer")
    workflow.add_edge("writer","writing_reviewer")
    workflow.add_edge("assembler",END)
    workflow.add_conditional_edges(
        "writing_reviewer",
        has_writer_ended_book
    )

    return workflow


workflow = StateGraph(State, 
                      input = GraphInput,
                      output = GraphOutput,
                      config_schema = GraphConfig)

workflow.set_entry_point("instructor")
workflow = defining_nodes(workflow = workflow)
workflow = defining_edges(workflow = workflow)

app = workflow.compile(
    interrupt_before=['human_feedback']
    )


if __name__ == '__main__':
    from langchain_core.messages import HumanMessage
    from langgraph.checkpoint.memory import MemorySaver
    app = workflow.compile(
        interrupt_before=['human_feedback'],
        checkpointer=MemorySaver()
    )
    stories = [
    """Initial requirement:
    topic: A disillusioned journalist in modern Argentina uncovers a vast network of government corruption and embarks on a dangerous quest to expose the truth, facing political intrigue, powerful adversaries, and hidden agendas.
    target_audience: Adult readers interested in political thrillers, investigative journalism stories, and narratives set in contemporary Latin America. Readers who appreciate stories with strong female protagonists and themes of justice and corruption.
    genre: Political thriller with elements of suspense and investigative journalism.
    writing_style: Gritty and realistic, with a suspenseful and fast-paced narrative. The writing should be immersive, focusing on the tension and high stakes of the protagonist's investigation. The style should be accessible and engaging, avoiding overly complex language while maintaining a sense of urgency and realism.
    additional_requirements: The narrative should emphasize the political and social context of modern Argentina, highlighting the challenges and complexities of the country. The story should be character-driven, focusing on the protagonist's internal struggles and motivations, as well as the relationships she forms with her allies. The plot should be intricate and suspenseful, with twists and turns that keep the reader engaged. The ending should be satisfying and impactful, leaving the reader with a sense of hope and justice.
    """,

    """Initial requirement:
    topic: A catastrophic event during a Boca Juniors vs. River Plate match at La Bombonera in Buenos Aires, Argentina, in 2008, focusing on the tragic loss of life and the ensuing chaos. The narrative will explore the social and mass behavior that contributed to the disaster, set against the backdrop of the intense rivalry and the socio-political climate of Argentina at the time.
    target_audience: Adult readers interested in suspenseful, realistic fiction, particularly those who appreciate stories that explore human behavior under extreme pressure, sports-related tragedies, and the socio-political context of Latin America. The audience may also include those interested in the culture and history of Argentine football.
    genre: Suspense drama with elements of tragedy and realism. The narrative will be presented in a first-person perspective, creating an immersive and immediate experience for the reader. The story will build tension and suspense as the events unfold, culminating in the catastrophic climax and its aftermath.
    writing_style: The writing style should be immersive and immediate, using a first-person perspective to place the reader directly into the protagonist's experience. The tone should be realistic and gritty, reflecting the chaos and panic of the situation. The language should be evocative and descriptive, capturing the atmosphere of La Bombonera and the intensity of the rivalry. The narrative should also incorporate the protagonist's internal thoughts and emotions, adding depth and complexity to the story.
    additional_requirements: The narrative should realistically portray the mass behavior and social dynamics that contribute to the chaos. The political and cultural context of Argentina in 2008 should be subtly woven into the story, adding depth and authenticity without overshadowing the main narrative. The story should focus on the human impact of the tragedy, exploring the emotional and psychological toll on the protagonist and other characters. The use of authentic details about the stadium, the match, and the fan culture is essential to create a believable and immersive experience.
    """,

    """topic: A couple is torn apart when the male partner accepts a dangerous undercover job in Africa to dismantle a powerful narco-trafficking organization. The narrative will explore the challenges of maintaining a relationship across continents, the moral ambiguities of undercover work, and the high-stakes action involved in confronting a criminal enterprise. The story will be set in modern times, with the action sequences taking place in various African locations and the emotional scenes in Barcelona.
    target_audience: Adult readers who enjoy action-packed thrillers with a strong emotional core. This includes readers who appreciate stories about complex relationships, moral dilemmas, and high-stakes situations. The target audience is likely to be interested in contemporary settings and realistic portrayals of both the action and the emotional challenges faced by the characters.
    genre: Action Thriller with elements of Romantic Drama. The book will blend high-stakes action sequences with the emotional turmoil of a long-distance relationship. The narrative will balance the adrenaline of the undercover operation with the intimate struggles of the couple.
    writing_style: Fast-paced and engaging, with a focus on vivid descriptions of both the action and the emotional states of the characters. The writing should be direct and immersive, drawing the reader into the heart of the action and the emotional conflict. The tone should be intense and suspenseful, with moments of tenderness and vulnerability to highlight the emotional stakes. The narrative should alternate between the male character's experiences in Africa and the female character's life in Barcelona, creating a sense of parallel narratives that converge at key moments.
    additional_requirements: The book should include detailed descriptions of the African settings, emphasizing the contrast with the urban environment of Barcelona. The narrative should explore the psychological impact of undercover work on the male character, including the moral compromises he may have to make. The female character's perspective should be equally developed, showing her struggles with loneliness, fear, and the uncertainty of her partner's safety. The ending should be impactful and emotionally resonant, leaving the reader with a sense of closure while acknowledging the complexities of the situation. The book should also include elements of suspense and mystery, keeping the reader engaged and guessing about the outcome of the mission and the relationship.
    """,

    """topic: A secluded village plagued by unexplained paranormal occurrences, where the deaths of its inhabitants trigger unique and unsettling transformations of their bodies, rather than a traditional afterlife or haunting.
    target_audience: Adults and young adults who enjoy mystery, paranormal fiction, and stories with a touch of the unsettling and strange. Readers who appreciate atmospheric narratives and are intrigued by the unknown.
    genre: Paranormal Mystery with elements of Dark Fantasy and a touch of Body Horror. The focus is on the mystery of the transformations and the unsettling nature of the events, rather than explicit horror.
    writing_style: Atmospheric and descriptive, with a focus on building suspense and a sense of unease. The writing should be evocative, using sensory details to create a vivid picture of the village and the transformations. The tone should be mysterious and slightly unsettling, avoiding explicit gore or graphic descriptions, but focusing on the strange and uncanny.
    additional_requirements: When a person dies in the village, their body undergoes a strange transformation. Instead of decaying, the body might turn into a lifelike statue made of a strange, unknown material, or perhaps their body becomes a vessel for a swarm of insects that form a vaguely human shape. Another possibility is that the body might become a living plant, with roots growing from the limbs and flowers blooming from the head. The transformations should be unique to each individual, adding to the mystery. The story should focus on the villagers' attempts to understand these transformations and the underlying cause of the paranormal events. The transformations should be unsettling and strange, but not explicitly gory or horrific. The focus should be on the mystery and the unknown, rather than explicit violence or horror.

    """,
    """Initial requirement:
    topic: A love story between a community organizer and an artist set against the backdrop of socio-economic struggles in Villa Lugano, Buenos Aires, exploring themes of community solidarity, social justice, and the transformative power of art.
    target_audience: Adult readers interested in social justice themes, character-driven narratives, and stories that explore the complexities of relationships across class differences. Readers who appreciate stories set in vibrant, culturally rich environments and are interested in the power of community and art.
    genre: Contemporary Fiction with elements of Romance and Social Realism.
    writing_style: The writing style should be evocative and descriptive, capturing the vibrant culture of Villa Lugano and the stark contrast with Palermo Soho. The tone should be empathetic and realistic, portraying the characters' internal struggles and external conflicts with nuance. The narrative should be engaging and emotionally resonant, highlighting the characters' growth and the impact of their actions on the community. The writing should be accessible and avoid overly complex language, while maintaining a literary quality.
    additional_requirements: The narrative should realistically depict the physical and emotional landscape of Villa Lugano, contrasting it with the more privileged environment of Palermo Soho. The story should explore themes of community solidarity, social justice, the power of artistic expression, the challenges of class differences, the complexities of family dynamics, and the transformative potential of shared purpose. The characters' internal struggles should be interwoven with their external conflicts, emphasizing the moral complexities of their choices within a context of social and economic disparity. The story should culminate in the long-term positive impact of Camila and Kevin's collaboration on the community, showcasing the metamorphosis of a neglected community center into a thriving hub of artistic expression. The narrative should conclude with a sense of enduring hope and resilience, underscoring Camila and Kevin's unwavering love and their shared commitment to each other and their beloved community. The story should be divided into multiple chapters, following the plot outline provided.

    """
    ]
    for story in stories: 
        human_input_msg = story
        
        configuration = {
            "configurable": {
                "thread_id": 42,
                "language":"spanish",
                "instructor_model":"google",
                "brainstormer_idea_model":"google",
                "brainstormer_critique_model":"google",
                "reviewer_model":"google",
                "writer_model":"google",
                "writing_reviewer_model":"google",
                "translator_model":"google",
                "n_chapters":6,
                "min_paragraph_per_chapter": 5,
                "min_sentences_in_each_paragraph_per_chapter": 8,
                "critiques_in_loop": False,

            },
            "recursion_limit": 150
        }


        for event in app.stream(
                input = {'user_instructor_messages': [HumanMessage(content=human_input_msg)]},
                config = configuration,
                stream_mode='values'):
            
            type_msg = event['user_instructor_messages'][-1].type
            msg = event['user_instructor_messages'][-1].content
            if type_msg == "ai":
                if (msg == "Done, executed"):
                    break
                else:
                    print(type_msg.upper() + f": {msg}")


        if msg == "Done, executed":
            instructor_condition = True
        else:
            instructor_condition = False
        while instructor_condition == False:
            new_human_input_msg = input("Provide your answer: ")
            new_human_input_msg = HumanMessage(content = new_human_input_msg)
            app.update_state(configuration, {'user_instructor_messages': [new_human_input_msg]}, as_node = 'human_feedback')
            current_node = 'human_feedback'
            app.get_state(config = configuration).next
            for event in app.stream(
                    input = None,
                    config = configuration,
                    stream_mode='values'):
                type_msg = event['user_instructor_messages'][-1].type
                msg = event['user_instructor_messages'][-1].content
                if (msg == "Done, executed")&(type_msg == "ai"):
                    instructor_condition = True
                    break
                else:
                    print(type_msg.upper() + f": {msg}")
        print("Starting the automated autonomous behaviour")
        app.get_state(config = configuration).next
        # copy the current state of events
        for event in app.stream(
                input = None,
                config = configuration,
                stream_mode='values'):

            last_snapshot_events = event

        
        book_title_english = event['book_title']
        book_prologue_english = event['book_prologue']
        book_raw_content = event['content']
        book_raw_chapter_names = event['chapter_names']
        book_final_content = {k: v for k, v in zip(book_raw_chapter_names, book_raw_content)}
        # The idea is to save in developed_books/english
        with open("developed_books/english/"+book_title_english.replace(" ","_").lower()+".txt", "w") as f:
            f.write("Title:"+ '\n')
            f.write(book_title_english+'\n\n')
            f.write("Prologue:"+"\n")
            f.write(book_prologue_english+'\n\n')
            for chapter_name, chapter_content in book_final_content.items():
                f.write(chapter_name+'\n')
                f.write(chapter_content+'\n\n')

        # If it is also in other language (not english):
        if not ((configuration['configurable'].get('language') == 'english')|(configuration['configurable'].get('language') is None)):
            book_title_translation = event['translated_book_name']
            book_prologue_translation = event['translated_book_prologue']
            book_raw_content_translation = event['translated_content']
            book_raw_chapter_names_translation = event['translated_chapter_names']
            book_final_content_translation = {k: v for k, v in zip(book_raw_chapter_names_translation, book_raw_content_translation)}
            # The idea is to save in developed_books/{language}
            with open(f"developed_books/{configuration['configurable'].get('language')}/{book_title_translation.replace(" ","_").lower()}.txt", "w") as f:
                f.write("Title:\n")
                f.write(book_title_translation+'\n\n')
                f.write("Prologue:\n")
                f.write(book_prologue_translation+'\n\n')
                for chapter_name, chapter_content in book_final_content_translation.items():
                    f.write(chapter_name+'\n')
                    f.write(chapter_content+'\n\n')        
        

        print("The book has been developed and saved in the corresponding folder")

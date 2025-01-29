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
from unidecode import unidecode
import re

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
    human_input_msg = input("Place your initial idea:\n- ")
    
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


    with open("developed_books/english/"+re.sub(r'[^\w\s]','', unidecode(book_title_english.replace(" ","_"))).lower()+".txt", "w") as f:
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
        with open(f"developed_books/{configuration['configurable'].get('language')}/{re.sub(r'[^\w\s]','', unidecode(book_title_translation.replace(" ","_"))).lower()}.txt", "w") as f:
            f.write("Title:\n")
            f.write(book_title_translation+'\n\n')
            f.write("Prologue:\n")
            f.write(book_prologue_translation+'\n\n')
            for chapter_name, chapter_content in book_final_content_translation.items():
                f.write(chapter_name+'\n')
                f.write(chapter_content+'\n\n')        
    

    print("The book has been developed and saved in the corresponding folder")

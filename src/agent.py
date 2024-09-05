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
workflow = defining_edges(workflow = workflow)
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

    human_input_msg = "An unexpected crime story centered around an assassination, featuring various suspects throughout the narrative, with a final plot twist where the guilty party is not recognized until the end. The book targets young adults and emphasizes themes of suspense and unpredictability."
    
    configuration = {
        "configurable": {
            "thread_id": 42,
            "language":"spanish",
            "instructor_model":"amazon",
            "brainstormer_idea_model":"amazon",
            "brainstormer_critique_model":"amazon",
            "reviewer_model":"amazon",
            "writer_model":"openai"
        }
    }

    for event in app.stream(
            input = {'user_instructor_messages': [HumanMessage(content=human_input_msg)]},
            config = configuration,
            stream_mode='values'):
        
        type_msg = event['user_instructor_messages'][-1].type
        msg = event['user_instructor_messages'][-1].content
        print(type_msg.upper() + f": {msg}")

    while True:
        new_human_input_msg = input("Provide your answer: ")
        new_human_input_msg = HumanMessage(content = new_human_input_msg)
        app.update_state(configuration, {'user_instructor_messages': [new_human_input_msg]}, as_node = 'human_feedback')
        print("HUMAN" + f": {new_human_input_msg.content}")
        current_node = 'human_feedback'
        app.get_state(config = configuration).next
        for event in app.stream(
                input = None,
                config = configuration,
                stream_mode='values'):
            type_msg = event['user_instructor_messages'][-1].type
            msg = event['user_instructor_messages'][-1].content
            print(type_msg.upper() + f": {msg}")


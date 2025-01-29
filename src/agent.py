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

import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_openai.chat_models import ChatOpenAI
from langgraph.graph import StateGraph
from src.utils import State, GraphInput, GraphOutput
from src.nodes import get_clear_instructions, read_human_feedback, brainstorming_critique, making_writer_brainstorming
from src.routers import should_go_to_brainstorming_writer, should_continue_with_critique


workflow = StateGraph(State, input = GraphInput)
workflow.add_node("instructor", get_clear_instructions)
workflow.set_entry_point("instructor")
workflow.add_node("human_feedback", read_human_feedback)
workflow.add_node("brainstorming_writer", making_writer_brainstorming)
workflow.add_node("brainstorming_critique", brainstorming_critique)
workflow.add_conditional_edges(
    "instructor",
    should_go_to_brainstorming_writer
)
workflow.add_edge("human_feedback","instructor")
workflow.add_conditional_edges(
    "brainstorming_writer",
    should_continue_with_critique
)
workflow.add_edge("brainstorming_critique","brainstorming_writer")

app = workflow.compile(
    )

if __name__ == '__main__':
    from langchain_core.messages import HumanMessage

    final_state = app.invoke(
        {"user_instructor_messages": [
            HumanMessage(content="An unexpected crime story centered around an assassination, featuring various suspects throughout the narrative, with a final plot twist where the guilty party is not recognized until the end. The book targets young adults and emphasizes themes of suspense and unpredictability, written in a style similar to Stephen King.")
            ]},
        config={"configurable": {"thread_id": 42}}
    )
    print(final_state["writer_brainstorming_messages"][-1].content)
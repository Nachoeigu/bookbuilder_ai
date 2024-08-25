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

# model = ChatGoogleGenerativeAI(model = 'gemini-1.5-pro-exp-0801', temperature = 0.8)
# model_with_structured_output = model.with_structured_output(WriterStructuredOutput)
# messages = [
#     SystemMessage(content = ""),
# ]
# def generate_content(state: State):
#     if state['content'] == []:
#         model_with_structured_output
#     else:

workflow = StateGraph(State, input = GraphInput)
workflow.add_node("get_clear_instructions", get_clear_instructions)
workflow.add_node("read_human_feedback", read_human_feedback)
workflow.add_node("making_writer_brainstorming", making_writer_brainstorming)
workflow.add_node("brainstorming_critique", brainstorming_critique)
workflow.add_conditional_edges(
    "get_clear_instructions",
    should_go_to_brainstorming_writer
)
workflow.add_edge("read_human_feedback","get_clear_instructions")
workflow.add_edge("brainstorming_critique","making_writer_brainstorming")
workflow.add_conditional_edges(
    "making_writer_brainstorming",
    should_continue_with_critique
)

workflow.set_entry_point("get_clear_instructions")

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
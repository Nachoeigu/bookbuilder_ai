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
from src.nodes import get_clear_instructions, read_human_feedback
from src.routers import should_go_to_writer

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
workflow.add_conditional_edges(
    "get_clear_instructions",
    should_go_to_writer
)
workflow.add_edge("read_human_feedback","get_clear_instructions")
workflow.set_entry_point("get_clear_instructions")

app = workflow.compile(interrupt_before=['read_human_feedback'])

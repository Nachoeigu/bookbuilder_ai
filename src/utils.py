import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

import operator
from typing import Annotated, List, Literal, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.pydantic_v1 import BaseModel, Field


class WriterStructuredOutput(BaseModel):
    """The way the writer should answer a request"""
    content: str = Field(description = "The content inside the developed chapter.")
    chapter_summary: str = Field(description = "A summary in 2 paragraphs about the story in the chapter")
    chapter_name: str = Field(description = "The name of the developed chapter.")

class DocumentationReady(TypedDict):
    requirements: str = Field(description = "A highly detailed description to the writer about the requirements should consider while developing the book")
    total_pages: int = Field(description = "Number of total pages the book should contain")
    chapter_length: Literal['long','medium','short'] = Field(description = "The length of each chapter in the book.")

class ApprovedBrainstormingIdea(TypedDict):
    is_approved: bool = Field(description = "It defines if the writer idea is approved or not by the critique.")

class State(TypedDict):
    content: Annotated[List[str], operator.add]
    user_instructor_messages: Annotated[List[AnyMessage], operator.add]
    writer_brainstorming_messages: Annotated[List[AnyMessage], operator.add]
    critique_brainstorming_messages: Annotated[List[AnyMessage], operator.add]
    final_brainstorming_idea: str
    is_approved_brainstorming: bool
    instructor_documents: DocumentationReady
    prologue: str
    title: str
    total_pages: int
    chapter_length: Literal['long','medium','short']

class GraphInput(TypedDict):
    user_instructor_messages: List[HumanMessage]

class GraphOutput(TypedDict):
    content: str
    prologue: str
    book_title: str

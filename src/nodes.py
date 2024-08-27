import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from src.constants import *
from src.utils import State, DocumentationReady, ApprovedBrainstormingIdea, WriterStructuredOutput, BrainstormingStructuredOutput, ApprovedWriterChapter
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.utils import GraphConfig, _get_model, _get_language, check_chapter, adding_delay_for_rate_limits


def get_clear_instructions(state: State, config: GraphConfig):
    model = _get_model(config = config, default = "openai", key = "instructor_model", temperature = 0)
    model = model.bind_tools([DocumentationReady])
    system_prompt = _get_language(config = config,
                                  prompt_case = "INSTRUCTOR_PROMPT"
                                  )
    messages = [SystemMessage(content = system_prompt)] + state['user_instructor_messages']
    adding_delay_for_rate_limits(model)
    reply = model.invoke(messages)

    if len(reply.tool_calls) == 0:
        return {'user_instructor_messages': [reply]}
    else:
        return {
            'instructor_documents': reply.tool_calls[0]['args']
            }

def read_human_feedback(state: State):
    pass

def brainstorming_critique(state: State, config: GraphConfig):
    model = _get_model(config, default = "openai", key = "brainstormer_model", temperature = 0.15)
    model_with_structured_output = model.with_structured_output(ApprovedBrainstormingIdea)
    
    if state['critique_brainstorming_messages'] == []:
        user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()])
        system_prompt = _get_language(config = config,
                                  prompt_case = "BRAINSTORMING_PROMPT"
                                  ) 
        messages = [
         SystemMessage(content = system_prompt.format(user_requirements=user_requirements)),
         HumanMessage(content = state['plannified_messages'][-1])
        ]
        adding_delay_for_rate_limits(model)
        output = model_with_structured_output.invoke(messages)

    else:
        messages = state['critique_brainstorming_messages'] + [HumanMessage(content = state['plannified_messages'][-1])]
        adding_delay_for_rate_limits(model)
        output = model_with_structured_output.invoke(messages)

    if int(output.grade) < 9:
        return {'is_plan_approved': False,
                'critique_brainstorming_messages': [output.feedback]}
    
    else:
        return {'is_plan_approved': True}


def making_writer_brainstorming(state: State, config: GraphConfig):
    model = _get_model(config, default = "openai", key = "brainstormer_model", temperature = 1)
    user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()])
    model_with_structured_output = model.with_structured_output(BrainstormingStructuredOutput)
    system_prompt = _get_language(config = config,
                                  prompt_case = "BRAINSTORMING_PROMPT"
                                  )
    
    system_prompt = SystemMessage(content = system_prompt.format(user_requirements=user_requirements))
    if state['is_plan_approved'] is None:
        adding_delay_for_rate_limits(model)
        output = model_with_structured_output.invoke([system_prompt] + [HumanMessage(content = "Start it...")])
        output = "\n".join([f"{key}: {value}" for key, value in output.dict().items()])

        return {'plannified_messages': [output]}
    
    else:
        if state['is_plan_approved'] == False:
            adding_delay_for_rate_limits(model)
            output = model_with_structured_output.invoke(state['plannified_messages'] + [HumanMessage(content=f"Based on this critique, adjust your entire idea and return it again with the adjustments: {state['critique_brainstorming_messages'][-1]}")])
            output = "\n".join([f"{key}: {value}" for key, value in output.dict().items()])

            return {'plannified_messages': [output]}

        else:
            model = _get_model(config, default = "openai", key = "brainstormer_model", temperature = 0)
            model_with_structured_output = model.with_structured_output(BrainstormingStructuredOutput, strict = True)
            adding_delay_for_rate_limits(model)
            output = model_with_structured_output.invoke(state['plannified_messages'] + [HumanMessage(content="Based on the improvements, structure the final structure:")])

            return {
                'plannified_intro': output.introduction,
                'plannified_development': output.development,
                'plannified_ending': output.ending,
                'characters': output.characters,
                'writing_style': output.writing_style,
                'story_overview': output.story_overview,
                'chapters_summaries': output.chapters_summaries,
                'total_paragraphs_per_chapter': output.total_paragraphs_per_chapter,
                'book_title': output.book_name,
                'book_prologue':output.book_prologue
            }

def evaluate_chapter(state: State, config: GraphConfig):
    model = _get_model(config = config, default = "openai", key = "writer_model", temperature = 0)
    model_with_tools = model.bind_tools([ApprovedWriterChapter])
    draft = f"Story overview: {state['story_overview']}\nIntroduction: {state['plannified_intro']}\nMiddle: {state['plannified_development']}\nEnding: {state['plannified_ending']}\nWriting Style: {state['writing_style']}\nSummary of each chapter: {state['chapters_summaries']}"
    try:
        is_chapter_approved = state['is_chapter_approved']
    except:
        is_chapter_approved = state.get('is_chapter_approved', False)

    if state['is_chapter_approved'] is None:
        system_prompt = _get_language(config = config,
                                    prompt_case = "WRITING_REVIEWER_PROMPT"
                                    )

        new_message = [SystemMessage(content = system_prompt.format(draft=draft))]
        adding_delay_for_rate_limits(model)
        output = model_with_tools.invoke(new_message + [HumanMessage(content=f"Start with the first chapter: {state['content'][-1]}.")])
    else:
        new_message = [HumanMessage(content = f"Continue with the next chapter:\n{state['content'][-1]}")]
        adding_delay_for_rate_limits(model)
        output = model_with_tools.invoke(state['writing_reviewer_memory'] + new_message)
    
    if len(output.tool_calls) > 0:
        new_messages = new_message + [AIMessage(content = 'Perfect!')]
        return {'is_chapter_approved': True,
                'writing_reviewer_memory': new_messages}
    else:
        new_messages = new_message + [AIMessage(content = output.content)]
        return {'is_chapter_approved': False,
                'writing_reviewer_memory': new_messages}
    

def generate_content(state: State, config: GraphConfig):
    model = _get_model(config = config, default = "openai", key = "writer_model", temperature = 0.70)
    model_with_structured_output = model.with_structured_output(WriterStructuredOutput)

    if state['current_chapter'] is None:
        system_prompt = _get_language(config = config,
                                    prompt_case = "WRITER_PROMPT"
                                    )
        messages = [
            SystemMessage(content=system_prompt.format(
                story_overview=state['story_overview'],
                characters=state['characters'],
                writing_style=state['writing_style'],
                introduction=state['plannified_intro'],
                development=state['plannified_development'],
                ending=state['plannified_ending'],
                total_paragraphs_per_chapter = state['total_paragraphs_per_chapter']
                )
            )
        ]
        adding_delay_for_rate_limits(model)
        output = model_with_structured_output.invoke(messages + [HumanMessage(content=f"Start with the first chapter: {state['chapters_summaries'][0]}.")])
        messages.append(AIMessage(content = output.content))
        
        if check_chapter(msg_content = output.content) == False:
            adding_delay_for_rate_limits(model)
            output = model_with_structured_output.invoke(messages + [HumanMessage(content=f"The chapter should contains at least 5 paragraphs. Adjust it again!")])

        return {'content': [output.content],
                'chapter_names': [output.chapter_name],
                'current_chapter': 1,
                'writer_memory': messages}

    else:
        if state['is_chapter_approved'] == False:
            new_message = [HumanMessage(content = state['writing_reviewer_memory'][-1].content + '\n Readapt it again.')]
        else:
            new_message = [HumanMessage(content = f"Continue with the chapter {state['current_chapter'] + 1}, which is about: {state['chapters_summaries'][state['current_chapter']]}")]
        adding_delay_for_rate_limits(model)
        output = model_with_structured_output.invoke(state['writer_memory'] + new_message)
        new_messages = new_message + [AIMessage(content = output.content)]
    
        if check_chapter(msg_content = output.content) == False:
            adding_delay_for_rate_limits(model)
            output = model_with_structured_output.invoke(new_messages + [HumanMessage(content=f"The chapter should contains at least 5 paragraphs. Adjust it again!")])

        return {
                'content': [output.content],
                'chapter_names': [output.chapter_name],
                'current_chapter': state['current_chapter'] + 1 if state['is_chapter_approved'] == True else state['current_chapter'],
                'writer_memory': new_messages
                }



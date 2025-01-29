import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from src.constants import *
from src.utils import State, DocumentationReady, ApprovedBrainstormingIdea, TranslatorStructuredOutput, TranslatorSpecialCaseStructuredOutput, retrieve_model_name, get_json_schema, NarrativeBrainstormingStructuredOutput, IdeaBrainstormingStructuredOutput, ApprovedWriterChapter,CritiqueWriterChapter,WriterStructuredOutput, NoJson, BadFormattedJson
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.utils import GraphConfig, _get_model, check_chapter, adding_delay_for_rate_limits, cleaning_llm_output
from pydantic import ValidationError
import json


def get_clear_instructions(state: State, config: GraphConfig):
    model = _get_model(config = config, default = "openai", key = "instructor_model", temperature = 0)
    system_prompt = INSTRUCTOR_PROMPT.format(
        schema = get_json_schema(DocumentationReady)
    )
    messages = [SystemMessage(content = system_prompt)] + state['user_instructor_messages']
    adding_delay_for_rate_limits(model)
    reply = model.invoke(messages)

    cleaned_reply = cleaning_llm_output(llm_output = reply)

    cleaned_reply = cleaning_llm_output(llm_output = reply)

    if isinstance(cleaned_reply, str):
        return {'user_instructor_messages': [reply],
                'instructor_model': retrieve_model_name(model)}
    elif isinstance(cleaned_reply, dict):
        return {
            'instructor_documents': DocumentationReady(**cleaned_reply),
            'instructor_model': retrieve_model_name(model)
            }

def read_human_feedback(state: State):
    pass

def brainstorming_idea_critique(state: State, config: GraphConfig):
    model = _get_model(config, default = "openai", key = "brainstormer_critique_model", temperature = 0.15)
    critiques_in_loop = config['configurable'].get('critiques_in_loop', False)

    if state['critique_brainstorming_messages'] == []:
        user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].dict().items()])
        system_prompt = CRITIQUE_IDEA_PROMPT
        messages = [
         SystemMessage(content = system_prompt.format(user_requirements=user_requirements, schema = get_json_schema(ApprovedBrainstormingIdea))),
         HumanMessage(content = state['plannified_messages'][-1].content)
        ]
        adding_delay_for_rate_limits(model)
        output = model.invoke(messages)
        try:
            cleaned_output = cleaning_llm_output(llm_output = output)
        except NoJson:
            output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        except BadFormattedJson as e:
            output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        try:
            cleaned_output = ApprovedBrainstormingIdea(**cleaned_output)
        except ValidationError as e:
            adding_delay_for_rate_limits(model)
            correction_instruction = ''
            errors = e.errors()
            for error in errors:
                field_name = error['loc'][-1]
                error_type = error['type']
                error_msg = error['msg']
                if error_type == 'missing':
                    correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                elif error_type == 'string_type':
                    correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
            correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
            output = model.invoke(messages + [output] + [HumanMessage(content=correction_instruction)])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)            


            cleaned_output = ApprovedBrainstormingIdea(**cleaned_output)

    else:
        if (critiques_in_loop == False)&((state['is_general_story_plan_approved'] == False)|(state['critique_brainstorming_messages'] != [])):
            cleaned_output = ApprovedBrainstormingIdea(grade=10, feedback="")
        else:
            messages = state['critique_brainstorming_messages'] + [HumanMessage(content = state['plannified_messages'][-1].content)]
            adding_delay_for_rate_limits(model)
            output = model.invoke(messages)
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            try:
                cleaned_output = ApprovedBrainstormingIdea(**cleaned_output)
            except ValidationError as e:
                adding_delay_for_rate_limits(model)
                correction_instruction = ''
                errors = e.errors()
                for error in errors:
                    field_name = error['loc'][-1]
                    error_type = error['type']
                    error_msg = error['msg']
                    if error_type == 'missing':
                        correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                    elif error_type == 'string_type':
                        correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
                correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
                output = model.invoke(messages + [output] + [HumanMessage(content=correction_instruction)])
                try:
                    cleaned_output = cleaning_llm_output(llm_output = output)
                except NoJson:
                    output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                except BadFormattedJson as e:
                    output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                cleaned_output = ApprovedBrainstormingIdea(**cleaned_output)

    if int(cleaned_output.grade) <= 9:
        feedback = cleaned_output.feedback
        is_general_story_plan_approved = False

        return {'is_general_story_plan_approved': is_general_story_plan_approved,
                'critique_brainstorming_messages': [AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````")],
                'brainstorming_critique_model': retrieve_model_name(model)
                }
    else:

        return {'is_general_story_plan_approved': True,
                'critique_brainstorming_messages': [AIMessage(content="Perfect!!")],
                'brainstorming_critique_model': retrieve_model_name(model)
                }

def brainstorming_narrative_critique(state: State, config: GraphConfig):
    model = _get_model(config, default = "openai", key = "brainstormer_critique_model", temperature = 0.15)
    critiques_in_loop = config['configurable'].get('critiques_in_loop', False)

    if state['critique_brainstorming_narrative_messages'] == []:
        user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].dict().items()])
        system_prompt = CRITIQUE_NARRATIVE_PROMPT
        messages = [
         SystemMessage(content = system_prompt.format(user_requirements=user_requirements, schema = get_json_schema(ApprovedBrainstormingIdea))),
         HumanMessage(content = str(state['plannified_chapters_messages'][-1].content))
        ]
        adding_delay_for_rate_limits(model)
        output = model.invoke(messages)
        try:
            cleaned_output = cleaning_llm_output(llm_output = output)
        except NoJson:
            output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        except BadFormattedJson as e:
            output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        try:
            cleaned_output = ApprovedBrainstormingIdea(**cleaned_output)
        except ValidationError as e:
            adding_delay_for_rate_limits(model)
            correction_instruction = ''
            errors = e.errors()
            for error in errors:
                field_name = error['loc'][-1]
                error_type = error['type']
                error_msg = error['msg']
                if error_type == 'missing':
                    correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                elif error_type == 'string_type':
                    correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
            correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
            output = model.invoke(messages + [output] + [HumanMessage(content=correction_instruction)])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)

            cleaned_output = ApprovedBrainstormingIdea(**cleaned_output)
    else:
        if (critiques_in_loop == False)&((state['is_detailed_story_plan_approved'] == False)|(state['critique_brainstorming_narrative_messages'] != [])):
            cleaned_output = ApprovedBrainstormingIdea(grade=10, feedback="")
        else:
            messages = state['critique_brainstorming_narrative_messages'] + [HumanMessage(content = state['plannified_chapters_messages'][-1])]
            adding_delay_for_rate_limits(model)
            output = model.invoke(messages)
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            try:
                cleaned_output = ApprovedBrainstormingIdea(**cleaned_output)
            except ValidationError as e:
                adding_delay_for_rate_limits(model)
                correction_instruction = ''
                errors = e.errors()
                for error in errors:
                    field_name = error['loc'][-1]
                    error_type = error['type']
                    error_msg = error['msg']
                    if error_type == 'missing':
                        correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                    elif error_type == 'string_type':
                        correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
                correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
                output = model.invoke(messages + [output] + [HumanMessage(content=correction_instruction)])
                try:
                    cleaned_output = cleaning_llm_output(llm_output = output)
                except NoJson:
                    output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                except BadFormattedJson as e:
                    output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                    cleaned_output = cleaning_llm_output(llm_output= output)

                cleaned_output = ApprovedBrainstormingIdea(**cleaned_output)
    if int(cleaned_output.grade) <= 9:
        feedback = cleaned_output.feedback
        is_general_story_plan_approved = False

        return {'is_detailed_story_plan_approved': is_general_story_plan_approved,
                'critique_brainstorming_narrative_messages': [AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````")],
                'brainstorming_critique_model': retrieve_model_name(model)
                }
    else:
        return {'is_detailed_story_plan_approved': True,
                'critique_brainstorming_narrative_messages': [AIMessage(content="Perfect!!")],
                'brainstorming_critique_model': retrieve_model_name(model)
                }

def making_narrative_story_brainstorming(state: State, config: GraphConfig):
    model = _get_model(config, default = "openai", key = "brainstormer_idea_model", temperature = 0.7)
    user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].dict().items()])

    if state.get('is_detailed_story_plan_approved', None) is None:
        system_prompt = BRAINSTORMING_NARRATIVE_PROMPT
        n_chapters = 10 if config['configurable'].get('n_chapters') is None else config['configurable'].get('n_chapters')
        system_prompt = SystemMessage(content = system_prompt.format(user_requirements=user_requirements,idea_draft=f"Story overview: {state['story_overview']}\n" f"Context and Setting: {state['plannified_context_setting']}\n" f"Inciting Incident: {state['plannified_inciting_incident']}\n" f"Themes and Conflicts Introduction: {state['plannified_themes_conflicts_intro']}\n" f"Transition to Development: {state['plannified_transition_to_development']}\n" f"Rising Action: {state['plannified_rising_action']}\n" f"Subplots: {state['plannified_subplots']}\n" f"Midpoint: {state['plannified_midpoint']}\n" f"Climax Build-Up: {state['plannified_climax_build_up']}\n" f"Climax: {state['plannified_climax']}\n" f"Falling Action: {state['plannified_falling_action']}\n" f"Resolution: {state['plannified_resolution']}\n" f"Epilogue: {state['plannified_epilogue']}\n" f"Writing Style: {state['writing_style']}", schema = get_json_schema(NarrativeBrainstormingStructuredOutput), n_chapters=n_chapters))
        adding_delay_for_rate_limits(model)
        user_query = HumanMessage(content = f"Develop a story with {n_chapters} chapters.\nEnsure consistency and always keep the attention of the audience.")
        messages = [system_prompt] + [user_query]
        output = model.invoke(messages)
        try:
            cleaned_output = cleaning_llm_output(llm_output = output)
        except NoJson:
            output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        except BadFormattedJson as e:
            output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        try:
            cleaned_output = NarrativeBrainstormingStructuredOutput(**cleaned_output)
        except ValidationError as e:
            adding_delay_for_rate_limits(model)
            correction_instruction = ''
            errors = e.errors()
            for error in errors:
                field_name = error['loc'][-1]
                error_type = error['type']
                error_msg = error['msg']
                if error_type == 'missing':
                    correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                elif error_type == 'string_type':
                    correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
            correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
            output = model.invoke(messages + [output] + [HumanMessage(content=correction_instruction)])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)

            cleaned_output = NarrativeBrainstormingStructuredOutput(**cleaned_output)

        messages = messages + [AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````")]
    
        return {'plannified_chapters_messages': messages,
                'brainstorming_writer_model': retrieve_model_name(model)
                }
    
    else:
        if (state['is_detailed_story_plan_approved'] == False)&(config['configurable'].get('critiques_in_loop',False) == True):
            adding_delay_for_rate_limits(model)
            critique_query = HumanMessage(content=f"Based on this critique, adjust your entire idea and return it again with the adjustments: {state['critique_brainstorming_narrative_messages'][-1].content}")
            
            output = model.invoke(state['plannified_chapters_messages'] + [critique_query])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(state['plannified_chapters_messages'] + [critique_query] + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(state['plannified_chapters_messages'] + [critique_query] + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            try:
                cleaned_output = NarrativeBrainstormingStructuredOutput(**cleaned_output)
            except ValidationError as e:
                adding_delay_for_rate_limits(model)
                correction_instruction = ''
                errors = e.errors()
                for error in errors:
                    field_name = error['loc'][-1]
                    error_type = error['type']
                    error_msg = error['msg']
                    if error_type == 'missing':
                        correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                    elif error_type == 'string_type':
                        correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
                correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
                output = model.invoke(state['plannified_chapters_messages'] + [critique_query] + [output] + [HumanMessage(content=correction_instruction)])
                try:
                    cleaned_output = cleaning_llm_output(llm_output = output)
                except NoJson:
                    output = model.invoke(state['plannified_chapters_messages'] + [critique_query] + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                except BadFormattedJson as e:
                    output = model.invoke(state['plannified_chapters_messages'] + [critique_query] + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                cleaned_output = NarrativeBrainstormingStructuredOutput(**cleaned_output)

            messages = [critique_query] + [AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````")]
            return {
                'plannified_chapters_messages': messages,
                'brainstorming_writer_model': retrieve_model_name(model)            
            }

        else:
            model = _get_model(config, default = "openai", key = "brainstormer_idea_model", temperature = 0)
            adding_delay_for_rate_limits(model)
            critique_query = [HumanMessage(content=f"Some improvements to your chapter: {state['critique_brainstorming_narrative_messages'][-1]}")]
            output = model.invoke(state['plannified_chapters_messages'] + critique_query)
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(state['plannified_chapters_messages'] + critique_query + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(state['plannified_chapters_messages'] + critique_query + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            try:
                cleaned_output = NarrativeBrainstormingStructuredOutput(**cleaned_output)
            except ValidationError as e:
                adding_delay_for_rate_limits(model)
                correction_instruction = ''
                errors = e.errors()
                for error in errors:
                    field_name = error['loc'][-1]
                    error_type = error['type']
                    error_msg = error['msg']
                    if error_type == 'missing':
                        correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                    elif error_type == 'string_type':
                        correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
                correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
                output = model.invoke(state['plannified_chapters_messages'] + critique_query + [output] + [HumanMessage(content=correction_instruction)])
                try:
                    cleaned_output = cleaning_llm_output(llm_output = output)
                except NoJson:
                    output = model.invoke(state['plannified_chapters_messages'] + critique_query + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                except BadFormattedJson as e:
                    output = model.invoke(state['plannified_chapters_messages'] + critique_query + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                cleaned_output = NarrativeBrainstormingStructuredOutput(**cleaned_output)

            messages = [critique_query] + [AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````")]
            return {
                'plannified_chapters_messages': messages,
                'plannified_chapters_summaries': cleaned_output.chapters_summaries,
                'brainstorming_writer_model': retrieve_model_name(model)            
            }

def making_general_story_brainstorming(state: State, config: GraphConfig):
    model = _get_model(config, default = "openai", key = "brainstormer_idea_model", temperature = 0.7)
    user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].dict().items()])
    
    system_prompt = BRAINSTORMING_IDEA_PROMPT
    
    system_prompt = SystemMessage(content = system_prompt.format(user_requirements=user_requirements, schema = get_json_schema(IdeaBrainstormingStructuredOutput)))
    if state.get('is_general_story_plan_approved', None) is None:
        adding_delay_for_rate_limits(model)
        messages = [
            system_prompt,
            HumanMessage(content = "Start it, respect all the rules previously mentioned...")
        ]
        output = model.invoke(messages)
        try:
            cleaned_output = cleaning_llm_output(llm_output = output)
        except NoJson:
            output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        except BadFormattedJson as e:
            output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        try:
            cleaned_output = IdeaBrainstormingStructuredOutput(**cleaned_output)
        except ValidationError as e:
            adding_delay_for_rate_limits(model)
            correction_instruction = ''
            errors = e.errors()
            for error in errors:
                field_name = error['loc'][-1]
                error_type = error['type']
                error_msg = error['msg']
                if error_type == 'missing':
                    correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                elif error_type == 'string_type':
                    correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
            correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
            output = model.invoke(messages + [output] + [HumanMessage(content=correction_instruction)])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)

            cleaned_output = IdeaBrainstormingStructuredOutput(**cleaned_output)

        messages = messages + [AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````")]

        return {'plannified_messages': messages,
                'brainstorming_writer_model': retrieve_model_name(model)
                }
    
    else:
        if state['is_general_story_plan_approved'] == False:
            adding_delay_for_rate_limits(model)
            new_msg = [HumanMessage(content=f"Based on this critique, adjust your entire idea and return it again with the adjustments: {cleaning_llm_output(state['critique_brainstorming_messages'][-1]).get('feedback')}")]
            output = model.invoke(state['plannified_messages'] + new_msg)
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(state['plannified_messages'] + new_msg + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(state['plannified_messages'] + new_msg + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            try:
                cleaned_output = IdeaBrainstormingStructuredOutput(**cleaned_output)
            except ValidationError as e:
                adding_delay_for_rate_limits(model)
                correction_instruction = ''
                errors = e.errors()
                for error in errors:
                    field_name = error['loc'][-1]
                    error_type = error['type']
                    error_msg = error['msg']
                    if error_type == 'missing':
                        correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                    elif error_type == 'string_type':
                        correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
                correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
                output = model.invoke(state['plannified_messages'] + new_msg + [output] + [HumanMessage(content=correction_instruction)])
                try:
                    cleaned_output = cleaning_llm_output(llm_output = output)
                except NoJson:
                    output = model.invoke(state['plannified_messages'] + new_msg + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                except BadFormattedJson as e:
                    output = model.invoke(state['plannified_messages'] + [new_msg] + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                cleaned_output = IdeaBrainstormingStructuredOutput(**cleaned_output)

            messages = new_msg + [AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````")]
            return {
                'plannified_messages': messages,
                'brainstorming_writer_model': retrieve_model_name(model)            
            }

        else:
            model = _get_model(config, default = "openai", key = "brainstormer_idea_model", temperature = 0)
            adding_delay_for_rate_limits(model)
            output = model.invoke(state['plannified_messages'] +[HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(state['plannified_messages'] + [HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")] + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(state['plannified_messages'] + [HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")] + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            try:    
                cleaned_output = IdeaBrainstormingStructuredOutput(**cleaned_output)
            except ValidationError as e:
                adding_delay_for_rate_limits(model)
                correction_instruction = ''
                errors = e.errors()
                for error in errors:
                    field_name = error['loc'][-1]
                    error_type = error['type']
                    error_msg = error['msg']
                    if error_type == 'missing':
                        correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                    elif error_type == 'string_type':
                        correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
                correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
                output = model.invoke(state['plannified_messages'] +[HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")] + [output] + [HumanMessage(content=correction_instruction)])
                try:
                    cleaned_output = cleaning_llm_output(llm_output = output)
                except NoJson:
                    output = model.invoke(state['plannified_messages'] +[HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")] + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                except BadFormattedJson as e:
                    output = model.invoke(state['plannified_messages'] + [HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")] + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                    cleaned_output = cleaning_llm_output(llm_output= output)



                cleaned_output = IdeaBrainstormingStructuredOutput(**cleaned_output)


            return {
            'plannified_context_setting': cleaned_output.context_setting,
            'plannified_inciting_incident': cleaned_output.inciting_incident,
            'plannified_themes_conflicts_intro': cleaned_output.themes_conflicts_intro,
            'plannified_transition_to_development': cleaned_output.transition_to_development,
            'plannified_rising_action': cleaned_output.rising_action,
            'plannified_subplots': cleaned_output.subplots,
            'plannified_midpoint': cleaned_output.midpoint,
            'plannified_climax_build_up': cleaned_output.climax_build_up,
            'plannified_climax': cleaned_output.climax,
            'plannified_falling_action': cleaned_output.falling_action,
            'plannified_resolution': cleaned_output.resolution,
            'plannified_epilogue': cleaned_output.epilogue,
            'characters': cleaned_output.characters,
            'writing_style': cleaned_output.writing_style,
            'story_overview': cleaned_output.story_overview,
            'book_title': cleaned_output.book_name,
            'book_prologue': cleaned_output.book_prologue,
            'brainstorming_writer_model': retrieve_model_name(model)
            }

def evaluate_chapter(state: State, config: GraphConfig):
    model = _get_model(config = config, default = "openai", key = "writing_reviewer_model", temperature = 0)
    
    draft = ( f"Story overview: {state['story_overview']}\n" f"Context and Setting: {state['plannified_context_setting']}\n" f"Inciting Incident: {state['plannified_inciting_incident']}\n" f"Themes and Conflicts Introduction: {state['plannified_themes_conflicts_intro']}\n" f"Transition to Development: {state['plannified_transition_to_development']}\n" f"Rising Action: {state['plannified_rising_action']}\n" f"Subplots: {state['plannified_subplots']}\n" f"Midpoint: {state['plannified_midpoint']}\n" f"Climax Build-Up: {state['plannified_climax_build_up']}\n" f"Climax: {state['plannified_climax']}\n" f"Falling Action: {state['plannified_falling_action']}\n" f"Resolution: {state['plannified_resolution']}\n" f"Epilogue: {state['plannified_epilogue']}\n" f"Writing Style: {state['writing_style']}\n" f"Summary of each chapter: {state['plannified_chapters_summaries'][-1]}" )
    critiques_in_loop = config['configurable'].get('critiques_in_loop', False)

    if state.get('is_chapter_approved', None) == None:
        system_prompt = WRITING_REVIEWER_PROMPT

        new_message = [SystemMessage(content = system_prompt.format(draft=draft, approved_schema = get_json_schema(ApprovedWriterChapter), critique_schema = get_json_schema(CritiqueWriterChapter)))] + [HumanMessage(content=f"Start with the first chapter: {state['content'][-1]}.")]
        adding_delay_for_rate_limits(model)
        output = model.invoke(new_message)
        try:
            cleaned_output = cleaning_llm_output(llm_output= output)
        except NoJson:
            output = model.invoke(new_message + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        except BadFormattedJson as e:
            output = model.invoke(new_messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
            cleaned_output = cleaning_llm_output(llm_output= output)

        is_chapter_approved = True if "is_approved" in list(cleaned_output) else False
        if is_chapter_approved:
            cleaned_output = ApprovedWriterChapter(**cleaned_output)
        else:
            cleaned_output = CritiqueWriterChapter(**cleaned_output)        

    else:
        if (critiques_in_loop == False)&(state['is_chapter_approved'] == False):
            new_message = [HumanMessage(content = f"\n{state['content'][-1]}")]
            feedback = 'Perfect!'
            is_chapter_approved = True
        else:
            new_message = [HumanMessage(content = f"Well done, now focus on the next chapter. But, first, read again the entire chat history so you have the context of the previous chapters.\nAfter reviewing the chat history, focus on the new chapter:\n<NEW_CHAPTER>\n```{state['content'][-1]}```.\n</NEW_CHAPTER>\n\nDon't forget to return your answer using the <FORMAT_OUTPUT> instruction.")]
            adding_delay_for_rate_limits(model)
            output = model.invoke(state['writing_reviewer_memory'] + new_message)  
            try:
                cleaned_output = cleaning_llm_output(llm_output= output)
            except NoJson:
                output = model.invoke(state['writing_reviewer_memory'] + new_message + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(state['writing_reviewer_memory'] + new_message + [output] +  [HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")] + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)

            is_chapter_approved = True if "is_approved" in list(cleaned_output.keys()) else False
            if is_chapter_approved:
                cleaned_output = ApprovedWriterChapter(**cleaned_output)
            else:
                cleaned_output = CritiqueWriterChapter(**cleaned_output)        

    if is_chapter_approved:
        new_messages = new_message + [AIMessage(content = 'Perfect')]
        return {'is_chapter_approved': True,
                'content_of_approved_chapters': [state['content'][-1]],
                'chapter_names_of_approved_chapters': [state['chapter_names'][-1]],
                'writing_reviewer_memory': new_messages,
                'reviewer_model': retrieve_model_name(model)
        }
    else:
        
        feedback = cleaned_output.feedback
        is_chapter_approved = False
        new_messages = new_message + [AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````")]
        if is_chapter_approved == True:
            return {
                'is_chapter_approved': is_chapter_approved,
                'content_of_approved_chapters': [state['content'][-1]],
                'chapter_names_of_approved_chapters': [state['chapter_names'][-1]],
                'writing_reviewer_memory': new_messages,
                'reviewer_model': retrieve_model_name(model)}
        else:
            return {'is_chapter_approved': is_chapter_approved,
                    'writing_reviewer_memory': new_messages,
                    'reviewer_model': retrieve_model_name(model)}

def generate_content(state: State, config: GraphConfig):
    model = _get_model(config = config, default = "openai", key = "writer_model", temperature = 0.70)

    min_paragraph_in_chapter = config['configurable'].get('min_paragraph_per_chapter', 10)
    min_sentences_in_each_paragraph_per_chapter = config['configurable'].get('min_sentences_in_each_paragraph_per_chapter', 5)
    min_sentences_in_each_paragraph_in_chapter = config['configurable'].get('min_sentences_in_each_paragraph_per_chapter', 10)
    if state.get('current_chapter', None) == None:
        system_prompt = WRITER_PROMPT
        messages = [
            SystemMessage(content=system_prompt.format(
                user_requirements="\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].dict().items()]),
                story_overview=state['story_overview'],
                characters=state['characters'],
                writing_style=state['writing_style'],
                context_setting=state['plannified_context_setting'],
                inciting_incident=state['plannified_inciting_incident'],
                themes_conflicts_intro=state['plannified_themes_conflicts_intro'],
                transition_to_development=state['plannified_transition_to_development'],
                rising_action=state['plannified_rising_action'],
                subplots=state['plannified_subplots'],
                midpoint=state['plannified_midpoint'],
                climax_build_up=state['plannified_climax_build_up'],
                climax=state['plannified_climax'],
                falling_action=state['plannified_falling_action'],
                resolution=state['plannified_resolution'],
                epilogue=state['plannified_epilogue'],
                schema = get_json_schema(WriterStructuredOutput),
                min_paragraph_in_chapter = min_paragraph_in_chapter,
                min_sentences_in_each_paragraph_in_chapter = min_sentences_in_each_paragraph_in_chapter
            ))
        ]
        adding_delay_for_rate_limits(model)
        human_msg = HumanMessage(content=f"Start with the first chapter. I will provide to you a summary of what should happen on it:\n`{state['plannified_chapters_summaries'][0]}.`")

        output = model.invoke(messages + [human_msg])
        try:
            cleaned_output = cleaning_llm_output(llm_output = output)
        except NoJson:
            output = model.invoke(messages + [human_msg] + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        except BadFormattedJson as e:
            output = model.invoke(messages + [human_msg] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
            cleaned_output = cleaning_llm_output(llm_output= output)

        try:
            cleaned_output = WriterStructuredOutput(**cleaned_output)
        except ValidationError as e:
            adding_delay_for_rate_limits(model)
            correction_instruction = ''
            errors = e.errors()
            for error in errors:
                field_name = error['loc'][-1]
                error_type = error['type']
                error_msg = error['msg']
                if error_type == 'missing':
                    correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                elif error_type == 'string_type':
                    correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
            correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format. Follow correctly the JSON output schema that you have received in your instructions inside the <FORMAT_OUTPUT> tag."
            output = model.invoke(messages + [human_msg] + [output] + [HumanMessage(content=correction_instruction)])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(messages + [human_msg] + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(messages + [human_msg] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            cleaned_output = WriterStructuredOutput(**cleaned_output)
        
        if check_chapter(msg_content = cleaned_output.content, min_paragraphs = min_paragraph_in_chapter) == False:
            adding_delay_for_rate_limits(model)
            messages.append(human_msg)
            messages.append(AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````"))
            human_msg = HumanMessage(content=f"The chapter should contains at least {min_paragraph_in_chapter} paragraphs and also, each one of the paragraphs must have at least {min_sentences_in_each_paragraph_per_chapter} sentences. Adjust it again: When expanding the text in this chapter by adding more paragraphs / sentences, ensure that every addition meaningfully progresses the story or deepens the characters without resorting to redundant or repetitive content.")
            output = model.invoke(messages + [human_msg])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(messages + [human_msg] + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(messages + [human_msg] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            try:
                cleaned_output = WriterStructuredOutput(**cleaned_output)
            except ValidationError as e:
                adding_delay_for_rate_limits(model)
                correction_instruction = ''
                errors = e.errors()
                for error in errors:
                    field_name = error['loc'][-1]
                    error_type = error['type']
                    error_msg = error['msg']
                    if error_type == 'missing':
                        correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                    elif error_type == 'string_type':
                        correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
                correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
                output = model.invoke(messages + [human_msg] + [output] + [HumanMessage(content=correction_instruction)])
                try:
                    cleaned_output = cleaning_llm_output(llm_output = output)
                except NoJson:
                    output = model.invoke(messages + [human_msg] + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                    cleaned_output = cleaning_llm_output(llm_output= output)
                except BadFormattedJson as e:
                    output = model.invoke(messages + [human_msg] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                    cleaned_output = cleaning_llm_output(llm_output= output)

                cleaned_output = WriterStructuredOutput(**cleaned_output)

        messages.append(human_msg)
        messages.append(AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````"))


        return {'content': [cleaned_output.content],
                'chapter_names': [cleaned_output.chapter_name],
                'current_chapter': 1,
                'writer_memory': messages,
                'writer_model': retrieve_model_name(model)
                }

    else:
        if state['is_chapter_approved'] == False:
            new_message = [HumanMessage(content = 'I will provide to you some feedback. Focus on each of these points, and improve the chapter.\n' + cleaning_llm_output(state['writing_reviewer_memory'][-1])['feedback'] + '\n\n When returning your response, dont forget any key in your JSON output:')]
        else:
            new_message = [HumanMessage(content = f"Continue with the chapter {state['current_chapter'] + 1}, which is about:\n<CHAPTER_SUMMARY>\n`{state['plannified_chapters_summaries'][state['current_chapter']]}.\n</CHAPTER_SUMMARY>`\nBefore start, remember to read again the previous developed chapters before so you make the perfect continuation possible. Dont forget any key in your JSON output. Also don´t forget the chapter should contains at least {min_paragraph_in_chapter} paragraphs and also, each one of the paragraphs must have at least {min_sentences_in_each_paragraph_per_chapter} sentences.")]
        adding_delay_for_rate_limits(model)
        output = model.invoke(state['writer_memory'] + new_message)
        try:
            cleaned_output = cleaning_llm_output(llm_output = output)
        except NoJson:
            output = model.invoke(state['writer_memory'] + new_message + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        except BadFormattedJson as e:
            output = model.invoke(state['writer_memory'] + new_message + [output] + [HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")] + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        try:
            cleaned_output = WriterStructuredOutput(**cleaned_output)
        except ValidationError as e:
            adding_delay_for_rate_limits(model)
            correction_instruction = ''
            errors = e.errors()
            for error in errors:
                field_name = error['loc'][-1]
                error_type = error['type']
                error_msg = error['msg']
                if error_type == 'missing':
                    correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                elif error_type == 'string_type':
                    correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
            correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
            output = model.invoke(state['writer_memory'] + new_message + [output] + [HumanMessage(content=correction_instruction)])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(state['writer_memory'] + new_message + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(state['writer_memory'] + new_message + [output] + [HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")] + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)

            cleaned_output = WriterStructuredOutput(**cleaned_output)

        new_messages = new_message + [AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````")]
    
        if check_chapter(msg_content = output.content, min_paragraphs = min_paragraph_in_chapter) == False:
            adding_delay_for_rate_limits(model)
            output = model.invoke(new_messages + [HumanMessage(content=f"The chapter should contains at least {min_paragraph_in_chapter} paragraphs, and also, each one of the paragraphs must have at least {min_sentences_in_each_paragraph_per_chapter} sentences. Adjust it again!  Dont forget any key in your JSON output")])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(new_message + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)            
            except BadFormattedJson as e:
                output = model.invoke(new_message + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)

            try:
                cleaned_output = WriterStructuredOutput(**cleaned_output)
            except ValidationError as e:
                adding_delay_for_rate_limits(model)
                correction_instruction = ''
                errors = e.errors()
                for error in errors:
                    field_name = error['loc'][-1]
                    error_type = error['type']
                    error_msg = error['msg']
                    if error_type == 'missing':
                        correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                    elif error_type == 'string_type':
                        correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
                correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
                output = model.invoke(new_messages + [HumanMessage(content=f"The chapter should contains at least {min_paragraph_in_chapter} paragraphs, and also, each one of the paragraphs must have at least {min_sentences_in_each_paragraph_per_chapter} sentences. Adjust it again!  Dont forget any key in your JSON output")] + [output] + [HumanMessage(content=correction_instruction)])
                try:
                    cleaned_output = cleaning_llm_output(llm_output = output)
                except NoJson:
                    output = model.invoke(new_message + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                    cleaned_output = cleaning_llm_output(llm_output= output)            
                except BadFormattedJson as e:
                    output = model.invoke(new_message + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                    cleaned_output = cleaning_llm_output(llm_output= output)


                cleaned_output = WriterStructuredOutput(**cleaned_output)

        return {
                'content': [cleaned_output.content],
                'chapter_names': [cleaned_output.chapter_name],
                'current_chapter': state['current_chapter'] + 1 if state['is_chapter_approved'] == True else state['current_chapter'],
                'writer_memory': new_messages,
                'writer_model': retrieve_model_name(model)
                }

def generate_translation(state: State, config: GraphConfig):
    model = _get_model(config = config, default = "openai", key = "translator_model", temperature = 0)
    
    if state.get("translated_current_chapter", None) == None:
        system_prompt = TRANSLATOR_PROMPT
        messages = [
            SystemMessage(content=system_prompt.format(
                target_language=config['configurable'].get("language"),
                book_name=state['book_title'],
                story_topic=state['instructor_documents'].topic,
                schema = get_json_schema(TranslatorStructuredOutput)
                )
            ),
            HumanMessage(content=f"Start with the first chapter: title:\n {state['chapter_names_of_approved_chapters'][0]}\n\n Content of the Chapter:\n{state['content_of_approved_chapters'][0]}.")
        ]
        adding_delay_for_rate_limits(model)
        output = model.invoke(messages)
        try:
            cleaned_output = cleaning_llm_output(llm_output = output)
        except NoJson:
            output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        except BadFormattedJson as e:
            output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
            cleaned_output = cleaning_llm_output(llm_output= output)


        try:
            cleaned_output = TranslatorStructuredOutput(**cleaned_output)
        except ValidationError as e:
            adding_delay_for_rate_limits(model)
            correction_instruction = ''
            errors = e.errors()
            for error in errors:
                field_name = error['loc'][-1]
                error_type = error['type']
                error_msg = error['msg']
                if error_type == 'missing':
                    correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                elif error_type == 'string_type':
                    correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
            correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
            output = model.invoke(messages + [output] + [HumanMessage(content=correction_instruction)])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(messages + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(messages + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)

            cleaned_output = TranslatorStructuredOutput(**cleaned_output)

        messages.append(AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````"))

        special_case_output = model.invoke(messages + [HumanMessage(content=f"Also, translate the book title and the book prologue:\n title: {state['book_title']}\n prologue: {state['book_prologue']}.\nBut use the following schema definition for your output: {get_json_schema(TranslatorSpecialCaseStructuredOutput)}")])
        try:
            cleaned_special_case_output = cleaning_llm_output(llm_output = special_case_output)
        except NoJson:
            special_case_output = model.invoke(messages + [special_case_output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
            cleaned_special_case_output = cleaning_llm_output(llm_output= special_case_output)
        except BadFormattedJson as e:
            special_case_output = model.invoke(messages + [special_case_output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
            cleaned_special_case_output = cleaning_llm_output(llm_output= special_case_output)
        try:
            cleaned_special_case_output = TranslatorSpecialCaseStructuredOutput(**cleaned_special_case_output)
        except ValidationError as e:
            adding_delay_for_rate_limits(model)
            correction_instruction = ''
            errors = e.errors()
            for error in errors:
                field_name = error['loc'][-1]
                error_type = error['type']
                error_msg = error['msg']
                if error_type == 'missing':
                    correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                elif error_type == 'string_type':
                    correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
            correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
            special_case_output = model.invoke(messages + [special_case_output] + [HumanMessage(content=correction_instruction)])
            try:
                cleaned_special_case_output = cleaning_llm_output(llm_output = special_case_output)
            except NoJson:
                special_case_output = model.invoke(messages + [special_case_output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_special_case_output = cleaning_llm_output(llm_output= special_case_output)    
            except BadFormattedJson as e:
                special_case_output = model.invoke(messages + [special_case_output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_special_case_output = cleaning_llm_output(llm_output= special_case_output)        
            
            cleaned_special_case_output = TranslatorSpecialCaseStructuredOutput(**cleaned_special_case_output)

        book_name = cleaned_special_case_output.translated_book_name
        book_prologue = cleaned_special_case_output.translated_book_prologue

        return {'translated_content': [cleaned_output.translated_content],
                'translated_book_name': book_name,
                'translated_book_prologue': book_prologue,
                'translated_chapter_names': [cleaned_output.translated_chapter_name],
                'translated_current_chapter': 1,
                'translator_memory': messages,
                'translator_model': retrieve_model_name(model)
                }
    else:
        new_message = [HumanMessage(content = f"Continue with chapter number {state['translated_current_chapter']}: title: {state['chapter_names_of_approved_chapters'][state['translated_current_chapter']]}\n {state['content_of_approved_chapters'][state['translated_current_chapter']]}.")]

        adding_delay_for_rate_limits(model)
        output = model.invoke(state['translator_memory'] + new_message)
        try:
            cleaned_output = cleaning_llm_output(llm_output = output)
        except NoJson:
            output = model.invoke(state['translator_memory'] + new_message + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        except BadFormattedJson as e:
            output = model.invoke(state['translator_memory'] + new_message  + [output] + [HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")] + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
            cleaned_output = cleaning_llm_output(llm_output= output)
        try:
            cleaned_output = TranslatorStructuredOutput(**cleaned_output)
        except ValidationError as e:
            adding_delay_for_rate_limits(model)
            correction_instruction = ''
            errors = e.errors()
            for error in errors:
                field_name = error['loc'][-1]
                error_type = error['type']
                error_msg = error['msg']
                if error_type == 'missing':
                    correction_instruction += f"You forgot to place the key `{field_name}`\n\n"
                elif error_type == 'string_type':
                    correction_instruction += f"You place incorrectly the data type of the key `{field_name}`: {error_msg}\n\n"
            correction_instruction += "Check what I have mentioned, thinking step by step, in order to return the correct and expected output format."
            output = model.invoke(state['translator_memory'] + new_message + [output] + [HumanMessage(content=correction_instruction)])
            try:
                cleaned_output = cleaning_llm_output(llm_output = output)
            except NoJson:
                output = model.invoke(state['translator_memory'] + new_message + [output] + [HumanMessage(content="The output does not contain a complete JSON code block. Please, return the output in the correct format.")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            except BadFormattedJson as e:
                output = model.invoke(state['translator_memory'] + new_message + [output] + [HumanMessage(content="Based on the improvements, return your final work following the instructions mentioned in <FORMAT_OUTPUT>. Ensure to respect the format and syntaxis explicitly explained.")] + [output] + [HumanMessage(content = f"Bad Formatted JSON. Please return the same info but correctly formatted. Here the error: {json.dumps(e.args[0])}")])
                cleaned_output = cleaning_llm_output(llm_output= output)
            cleaned_output = TranslatorStructuredOutput(**cleaned_output)

        new_messages = new_message + [AIMessage(content=f"```json\n{json.dumps(cleaned_output.dict())}````")]

        return {
            'translated_content': [cleaned_output.translated_content],
            'translated_chapter_names': [cleaned_output.translated_chapter_name],
            'translated_current_chapter': state['translated_current_chapter'] + 1,
            'translator_memory': new_messages,
            'translator_model': retrieve_model_name(model)
        }


def assembling_book(state: State, config: GraphConfig):
    translation_language = config['configurable'].get("language", "english")
    english_content = "Book title:\n" + state['book_title'] + '\n\n' + "Book prologue:\n" + state['book_prologue'] + '\n\n' + 'Used models:'+'\n' + "\n".join(f"- {key}: {state[key]}" for key in ["instructor_model", "brainstorming_writer_model", "brainstorming_critique_model", "writer_model", "reviewer_model", "translator_model"] if key in state) + '\n\n'  + "Initial requirement:\n" + "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].dict().items()]) + '\n\n' + '-----------------------------------------' + '\n\n'
    for n_chapter, chapter in enumerate(state['content_of_approved_chapters']):
        english_content += str(n_chapter + 1) + f') {state["chapter_names_of_approved_chapters"][n_chapter]}' + '\n\n' + chapter + '\n\n'

    if translation_language == 'english':
        translated_content = ''
    else:
        translated_content = "Book title:\n" + state['translated_book_name']  + '\n\n' + "Book prologue:\n" + state['translated_book_prologue'] + '\n\n' + 'Used models:'+'\n' + "\n".join(f"- {key}: {state[key]}" for key in ["instructor_model", "brainstorming_writer_model", "brainstorming_critique_model", "writer_model", "reviewer_model", "translator_model"] if key in state) + '\n\n' + "Initial requirement:\n" + "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].dict().items() if key not in ['reasoning_step','reflection_step']]) + '\n\n'  + '-----------------------------------------' + '\n\n'
        for n_chapter, chapter in enumerate(state['translated_content']):
            translated_content += str(n_chapter + 1) + f') {state["translated_chapter_names"][n_chapter]}' + '\n\n' + chapter + '\n\n'

    return {
        "english_version_book": english_content,
        "translated_version_book": translated_content
    }


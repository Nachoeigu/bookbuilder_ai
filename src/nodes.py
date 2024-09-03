import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from src.constants import *
from src.utils import State, DocumentationReady, ApprovedBrainstormingIdea,BrainstormingNarrativeStructuredOutput, WriterStructuredOutput, BrainstormingStructuredOutput, ApprovedWriterChapter, CritiqueWriterChapter, TranslatorStructuredOutput, TranslatorSpecialCaseStructuredOutput, retrieve_model_name
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from src.utils import GraphConfig, _get_model, check_chapter, adding_delay_for_rate_limits


def get_clear_instructions(state: State, config: GraphConfig):
    model = _get_model(config = config, default = "openai", key = "instructor_model", temperature = 0)
    model = model.bind_tools([DocumentationReady])
    system_prompt = INSTRUCTOR_PROMPT
    messages = [SystemMessage(content = system_prompt)] + state['user_instructor_messages']
    adding_delay_for_rate_limits(model)
    reply = model.invoke(messages)

    if len(reply.tool_calls) == 0:
        return {'user_instructor_messages': [reply],
                'instructor_model': retrieve_model_name(model)}
    else:
        return {
            'instructor_documents': reply.tool_calls[0]['args'],
            'instructor_model': retrieve_model_name(model)
            }

def read_human_feedback(state: State):
    pass

def brainstorming_idea_critique(state: State, config: GraphConfig):
    model = _get_model(config, default = "openai", key = "brainstormer_critique_model", temperature = 0.15)
    model_with_tools = model.with_structured_output(ApprovedBrainstormingIdea)
    critiques_in_loop = config['configurable'].get('critiques_in_loop', False)

    if state['critique_brainstorming_messages'] == []:
        user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()])
        system_prompt = CRITIQUE_IDEA_PROMPT
        messages = [
         SystemMessage(content = system_prompt.format(user_requirements=user_requirements)),
         HumanMessage(content = state['plannified_messages'][-1].content)
        ]
        adding_delay_for_rate_limits(model)
        output = model_with_tools.invoke(messages)

    else:
        if (critiques_in_loop == False)&((state['is_general_story_plan_approved'] == False)|(state['critique_brainstorming_messages'] != [])):
            output = ApprovedBrainstormingIdea(grade=10, feedback="")
        else:
            messages = state['critique_brainstorming_messages'] + [HumanMessage(content = state['plannified_messages'][-1].content)]
            adding_delay_for_rate_limits(model)
            output = model_with_tools.invoke(messages)

    if int(output.grade) <= 9:
        feedback = output.feedback
        is_general_story_plan_approved = False

        return {'is_general_story_plan_approved': is_general_story_plan_approved,
                'critique_brainstorming_messages': [AIMessage(content=feedback)],
                'brainstorming_critique_model': retrieve_model_name(model)
                }
    else:

        return {'is_general_story_plan_approved': True,
                'critique_brainstorming_messages': [AIMessage(content="Perfect!!")],
                'brainstorming_critique_model': retrieve_model_name(model)
                }

def brainstorming_narrative_critique(state: State, config: GraphConfig):
    model = _get_model(config, default = "openai", key = "brainstormer_critique_model", temperature = 0.15)
    model_with_tools = model.with_structured_output(ApprovedBrainstormingIdea)
    critiques_in_loop = config['configurable'].get('critiques_in_loop', False)

    if state['critique_brainstorming_narrative_messages'] == []:
        user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()])
        system_prompt = CRITIQUE_NARRATIVE_PROMPT
        messages = [
         SystemMessage(content = system_prompt.format(user_requirements=user_requirements)),
         HumanMessage(content = str(state['plannified_chapters_messages'][-1]))
        ]
        adding_delay_for_rate_limits(model)
        output = model_with_tools.invoke(messages)

    else:
        if (critiques_in_loop == False)&((state['is_detailed_story_plan_approved'] == False)|(state['critique_brainstorming_narrative_messages'] != [])):
            output = ApprovedBrainstormingIdea(grade=10, feedback="")
        else:
            messages = state['critique_brainstorming_narrative_messages'] + [HumanMessage(content = state['plannified_chapters_messages'][-1])]
            adding_delay_for_rate_limits(model)
            output = model_with_tools.invoke(messages)

    if int(output.grade) <= 9:
        feedback = output.feedback
        is_general_story_plan_approved = False

        return {'is_detailed_story_plan_approved': is_general_story_plan_approved,
                'critique_brainstorming_narrative_messages': [feedback],
                'brainstorming_critique_model': retrieve_model_name(model)
                }
    else:
        return {'is_detailed_story_plan_approved': True,
                'critique_brainstorming_narrative_messages': ["Perfect!!"],
                'brainstorming_critique_model': retrieve_model_name(model)
                }

def making_narrative_story_brainstorming(state: State, config: GraphConfig):
    model = _get_model(config, default = "openai", key = "brainstormer_idea_model", temperature = 0.7)
    user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()])
    model_with_structured_output = model.with_structured_output(BrainstormingNarrativeStructuredOutput, strict = True)
    
    if state.get('is_detailed_story_plan_approved', None) is None:
        system_prompt = BRAINSTORMING_NARRATIVE_PROMPT.format(idea_draft=f"Story overview: {state['story_overview']}\n" f"Context and Setting: {state['plannified_context_setting']}\n" f"Inciting Incident: {state['plannified_inciting_incident']}\n" f"Themes and Conflicts Introduction: {state['plannified_themes_conflicts_intro']}\n" f"Transition to Development: {state['plannified_transition_to_development']}\n" f"Rising Action: {state['plannified_rising_action']}\n" f"Subplots: {state['plannified_subplots']}\n" f"Midpoint: {state['plannified_midpoint']}\n" f"Climax Build-Up: {state['plannified_climax_build_up']}\n" f"Climax: {state['plannified_climax']}\n" f"Falling Action: {state['plannified_falling_action']}\n" f"Resolution: {state['plannified_resolution']}\n" f"Epilogue: {state['plannified_epilogue']}\n" f"Writing Style: {state['writing_style']}")
        system_prompt = SystemMessage(content = system_prompt.format(user_requirements=user_requirements))
        adding_delay_for_rate_limits(model)
        n_chapters = 10 if config['configurable'].get('n_chapters') is None else config['configurable'].get('n_chapters')
        user_query = HumanMessage(content = f"Develop a story with {n_chapters} chapters.\nEnsure consistency and always keep the attention of the audience.")
        messages = [system_prompt] + [user_query]
        output = model_with_structured_output.invoke(messages)

        messages = messages + [AIMessage(content=str(output.chapters_summaries))]
    
        return {'plannified_chapters_messages': messages,
                'brainstorming_writer_model': retrieve_model_name(model)
                }
    
    else:
        if (state['is_detailed_story_plan_approved'] == False)&(config['configurable'].get('critiques_in_loop',False) == True):
            adding_delay_for_rate_limits(model)
            critique_query = HumanMessage(content=f"Based on this critique, adjust your entire idea and return it again with the adjustments: {state['critique_brainstorming_narrative_messages'][-1]}")
            
            output = model_with_structured_output.invoke(state['plannified_chapters_messages'] + [critique_query])
            messages = [critique_query] + [AIMessage(content=str(output.chapters_summaries))]
            return {
                'plannified_chapters_messages': messages,
                'brainstorming_writer_model': retrieve_model_name(model)            
            }

        else:
            model = _get_model(config, default = "openai", key = "brainstormer_idea_model", temperature = 0)
            adding_delay_for_rate_limits(model)
            critique_query = [HumanMessage(content="Based on the improvements, structure the final structure:")]
            output = model_with_structured_output.invoke(state['plannified_chapters_messages'] + critique_query)
            messages = [critique_query] + [AIMessage(content=str(output.chapters_summaries))]
            return {
                'plannified_chapters_messages': messages,
                'plannified_chapters_summaries': output.chapters_summaries,
                'brainstorming_writer_model': retrieve_model_name(model)            
            }

def making_general_story_brainstorming(state: State, config: GraphConfig):
    model = _get_model(config, default = "openai", key = "brainstormer_idea_model", temperature = 0.7)
    user_requirements = "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()])
    model_with_structured_output = model.with_structured_output(BrainstormingStructuredOutput, strict = True)
    
    system_prompt = BRAINSTORMING_IDEA_PROMPT
    
    system_prompt = SystemMessage(content = system_prompt.format(user_requirements=user_requirements))
    if state.get('is_general_story_plan_approved', None) is None:
        adding_delay_for_rate_limits(model)
        messages = [
            system_prompt,
            HumanMessage(content = "Start it...")
        ]
        output = model_with_structured_output.invoke(messages)
        output = AIMessage(content="\n".join([f"{key}: {value}" for key, value in output.dict().items()]))

        messages = messages + [output]

        return {'plannified_messages': messages,
                'brainstorming_writer_model': retrieve_model_name(model)
                }
    
    else:
        if state['is_general_story_plan_approved'] == False:
            adding_delay_for_rate_limits(model)
            new_msg = [HumanMessage(content=f"Based on this critique, adjust your entire idea and return it again with the adjustments: {state['critique_brainstorming_messages'][-1]}")]
            output = model_with_structured_output.invoke(state['plannified_messages'] + new_msg)
            output = [AIMessage(content="\n".join([f"{key}: {value}" for key, value in output.dict().items()]))]
            messages = new_msg + output
            return {
                'plannified_messages': messages,
                'brainstorming_writer_model': retrieve_model_name(model)            
            }

        else:
            model = _get_model(config, default = "openai", key = "brainstormer_idea_model", temperature = 0)
            adding_delay_for_rate_limits(model)
            output = model_with_structured_output.invoke(state['plannified_messages'] +[HumanMessage(content="Based on the improvements, structure the final structure:")])
            return {
            'plannified_context_setting': output.context_setting,
            'plannified_inciting_incident': output.inciting_incident,
            'plannified_themes_conflicts_intro': output.themes_conflicts_intro,
            'plannified_transition_to_development': output.transition_to_development,
            'plannified_rising_action': output.rising_action,
            'plannified_subplots': output.subplots,
            'plannified_midpoint': output.midpoint,
            'plannified_climax_build_up': output.climax_build_up,
            'plannified_climax': output.climax,
            'plannified_falling_action': output.falling_action,
            'plannified_resolution': output.resolution,
            'plannified_epilogue': output.epilogue,
            'characters': output.characters,
            'writing_style': output.writing_style,
            'story_overview': output.story_overview,
            'book_title': output.book_name,
            'book_prologue': output.book_prologue,
            'brainstorming_writer_model': retrieve_model_name(model)
            }

def evaluate_chapter(state: State, config: GraphConfig):
    model = _get_model(config = config, default = "openai", key = "writing_reviewer_model", temperature = 0)
    try:
        model_with_tools = model.bind_tools([ApprovedWriterChapter, CritiqueWriterChapter], strict = True, tool_choice = 'any')
    except:
        model_with_tools = model.bind_tools([ApprovedWriterChapter, CritiqueWriterChapter])
    
    draft = ( f"Story overview: {state['story_overview']}\n" f"Context and Setting: {state['plannified_context_setting']}\n" f"Inciting Incident: {state['plannified_inciting_incident']}\n" f"Themes and Conflicts Introduction: {state['plannified_themes_conflicts_intro']}\n" f"Transition to Development: {state['plannified_transition_to_development']}\n" f"Rising Action: {state['plannified_rising_action']}\n" f"Subplots: {state['plannified_subplots']}\n" f"Midpoint: {state['plannified_midpoint']}\n" f"Climax Build-Up: {state['plannified_climax_build_up']}\n" f"Climax: {state['plannified_climax']}\n" f"Falling Action: {state['plannified_falling_action']}\n" f"Resolution: {state['plannified_resolution']}\n" f"Epilogue: {state['plannified_epilogue']}\n" f"Writing Style: {state['writing_style']}\n" f"Summary of each chapter: {state['plannified_chapters_summaries'][-1]}" )
    critiques_in_loop = config['configurable'].get('critiques_in_loop', False)

    if state.get('is_chapter_approved', None) == None:
        system_prompt = WRITING_REVIEWER_PROMPT

        new_message = [SystemMessage(content = system_prompt.format(draft=draft))] + [HumanMessage(content=f"Start with the first chapter: {state['content'][-1]}.")]
        adding_delay_for_rate_limits(model)
        output = model_with_tools.invoke(new_message)
        try:
            is_chapter_approved = [1 for tool in output.tool_calls if (tool['name'] == 'ApprovedWriterChapter')&(tool['args']['is_approved']==True)] == [1]
        except:
            is_chapter_approved = False
    else:
        if (critiques_in_loop == False)&(state['is_chapter_approved'] == False):
            new_message = [HumanMessage(content = f"\n{state['content'][-1]}")]
            feedback = 'Perfect!'
            is_chapter_approved = True
        else:
            new_message = [HumanMessage(content = f"\n{state['content'][-1]}")]
            adding_delay_for_rate_limits(model)
            output = model_with_tools.invoke(state['writing_reviewer_memory'] + new_message)    
            try:
                is_chapter_approved = [1 for tool in output.tool_calls if (tool['name'] == 'ApprovedWriterChapter')&(tool['args']['is_approved']==True)] == [1]
            except:
                is_chapter_approved = False

    if is_chapter_approved:
        new_messages = new_message + [AIMessage(content = 'Perfect')]
        return {'is_chapter_approved': True,
                'content_of_approved_chapters': [state['content'][-1]],
                'chapter_names_of_approved_chapters': [state['chapter_names'][-1]],
                'writing_reviewer_memory': new_messages,
                'reviewer_model': retrieve_model_name(model)
        }
    else:
        feedback = [tool['args']['feedback'] for tool in output.tool_calls if (tool['name'] == 'CritiqueWriterChapter')][0]
        is_chapter_approved = False
        new_messages = new_message + [AIMessage(content = feedback)]
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
    model_with_structured_output = model.with_structured_output(WriterStructuredOutput)

    if state.get('current_chapter', None) == None:
        system_prompt = WRITER_PROMPT
        messages = [
            SystemMessage(content=system_prompt.format(
                user_requirements="\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()]),
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
                epilogue=state['plannified_epilogue']
            ))
        ]
        adding_delay_for_rate_limits(model)
        human_msg = HumanMessage(content=f"Start with the first chapter: {state['plannified_chapters_summaries'][0]}.")

        output = model_with_structured_output.invoke(messages + [human_msg])
        
        if check_chapter(msg_content = output.content) == False:
            adding_delay_for_rate_limits(model)
            output = model_with_structured_output.invoke(messages + [HumanMessage(content=f"The chapter should contains at least 5 paragraphs. Adjust it again!")])

        messages.append(human_msg)
        messages.append(AIMessage(content = output.content))


        return {'content': [output.content],
                'chapter_names': [output.chapter_name],
                'current_chapter': 1,
                'writer_memory': messages,
                'writer_model': retrieve_model_name(model)
                }

    else:
        if state['is_chapter_approved'] == False:
            new_message = [HumanMessage(content = state['writing_reviewer_memory'][-1].content + '\n Focus on each of this points, and improve the chapter.')]
        else:
            new_message = [HumanMessage(content = f"Continue with the chapter {state['current_chapter'] + 1}, which is about: {state['plannified_chapters_summaries'][state['current_chapter']]}.\nRemember to read again the previous developed chapters before starting this one.")]
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
                'writer_memory': new_messages,
                'writer_model': retrieve_model_name(model)
                }

def generate_translation(state: State, config: GraphConfig):
    model = _get_model(config = config, default = "openai", key = "translator_model", temperature = 0)
    model_with_structured_output = model.with_structured_output(TranslatorStructuredOutput)

    if state.get("translated_current_chapter", None) == None:
        system_prompt = TRANSLATOR_PROMPT
        messages = [
            SystemMessage(content=system_prompt.format(
                target_language=config['configurable'].get("language"),
                book_name=state['book_title'],
                story_topic=state['instructor_documents']['topic']
                )
            ),
            HumanMessage(content=f"Start with the first chapter: title:\n {state['chapter_names_of_approved_chapters'][0]}\n\n Content of the Chapter:\n{state['content_of_approved_chapters'][0]}.")
        ]
        adding_delay_for_rate_limits(model)
        output = model_with_structured_output.invoke(messages)
        messages.append(AIMessage(content = f"Here is the translation:\n{output.translated_content}"+f"\n. This is the chapter name:\n{output.translated_chapter_name}"))

        model_with_structured_output_for_translating_book_name_prologue = model.with_structured_output(TranslatorSpecialCaseStructuredOutput)
        special_case_output = model_with_structured_output_for_translating_book_name_prologue.invoke(messages + [HumanMessage(content=f"Also, translate the book title and the book prologue:\n title: {state['book_title']}\n prologue: {state['book_prologue']}")])
        book_name = special_case_output.translated_book_name
        book_prologue = special_case_output.translated_book_prologue

        return {'translated_content': [output.translated_content],
                'translated_book_name': book_name,
                'translated_book_prologue': book_prologue,
                'translated_chapter_names': [output.translated_chapter_name],
                'translated_current_chapter': 1,
                'translator_memory': messages,
                'translator_model': retrieve_model_name(model)
                }
    else:
        new_message = [HumanMessage(content = f"Continue with chapter number {state['translated_current_chapter']}: title: {state['chapter_names_of_approved_chapters'][state['translated_current_chapter']]}\n {state['content_of_approved_chapters'][state['translated_current_chapter']]}.")]

        adding_delay_for_rate_limits(model)
        output = model_with_structured_output.invoke(state['translator_memory'] + new_message)
        
        new_messages = new_message + [AIMessage(content = f"content: {output.translated_content}"+f"\n name_chapter: {output.translated_chapter_name}")]

        return {
            'translated_content': [output.translated_content],
            'translated_chapter_names': [output.translated_chapter_name],
            'translated_current_chapter': state['translated_current_chapter'] + 1,
            'translator_memory': new_messages,
            'translator_model': retrieve_model_name(model)
        }


def assembling_book(state: State, config: GraphConfig):
    translation_language = config['configurable'].get("language", "english")
    english_content = "Book title:\n" + state['book_title'] + '\n\n' + "Book prologue:\n" + state['book_prologue'] + '\n\n' + 'Used models:'+'\n' + "\n".join(f"- {key}: {state[key]}" for key in ["instructor_model", "brainstorming_writer_model", "brainstorming_critique_model", "writer_model", "reviewer_model", "translator_model"] if key in state) + '\n\n'  + "Initial requirement:\n" + "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()]) + '\n\n' + '-----------------------------------------' + '\n\n'
    for n_chapter, chapter in enumerate(state['content_of_approved_chapters']):
        english_content += str(n_chapter + 1) + f') {state["chapter_names_of_approved_chapters"][n_chapter]}' + '\n\n' + chapter + '\n\n'

    if translation_language == 'english':
        translated_content = ''
    else:
        translated_content = "Book title:\n" + state['translated_book_name']  + '\n\n' + "Book prologue:\n" + state['translated_book_prologue'] + '\n\n' + 'Used models:'+'\n' + "\n".join(f"- {key}: {state[key]}" for key in ["instructor_model", "brainstorming_writer_model", "brainstorming_critique_model", "writer_model", "reviewer_model", "translator_model"] if key in state) + '\n\n' + "Initial requirement:\n" + "\n".join([f"{key}: {value}" for key, value in state['instructor_documents'].items()]) + '\n\n'  + '-----------------------------------------' + '\n\n'
        for n_chapter, chapter in enumerate(state['translated_content']):
            translated_content += str(n_chapter + 1) + f') {state["translated_chapter_names"][n_chapter]}' + '\n\n' + chapter + '\n\n'

    return {
        "english_version_book": english_content,
        "translated_version_book": translated_content
    }


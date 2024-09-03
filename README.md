# Book Builder With AI

**Imagine your story or adventure and make it a reality with Book Builder With AI.**

This software empowers you to create an entire book tailored to your interests or suggestions. Leveraging an AI-based Autonomous Agents Architecture, the process is highly customizable to ensure your story is crafted exactly as you envision it.

## HOW IT WORKS

### Overview:
Book Builder With AI follows a systematic, interactive workflow that guides you from your initial concept to a fully developed book. Here's how the process unfolds:

<img width="810" alt="image" src="https://github.com/user-attachments/assets/195d8085-1c67-4e67-b686-f09caf319415">


### 1. **Initiation by the Human:**
You kickstart the AI workflow by providing an initial message about your book idea. This could include a rough concept, genre, specific themes, or any other guidance you want to provide.

### 2. **Instructor Agent:**
The Instructor Agent takes your initial input and begins documenting the requirements for your book. The agent might ask you further questions to refine the concept and ensure it fully understands your vision. This phase can involve multiple iterations until the Instructor has a clear and complete set of instructions.

### 3. **Brainstorming Idea Writer:**
Once the instructions are finalized, they are handed over to the Brainstorming Idea Writer Agent. This agent is responsible for drafting a detailed outline of your book, considering the following key elements:
- **Story Overview:** A highly detailed overview of the narrative that includes a strong introduction, a well-developed middle, and a satisfying conclusion.
- **Characters:**  Characters of the story descriptions: background, motivations, and situations along the story journey.
- **Writing Style:**  The style and tone the writer should consider while developing the book.
- **Book Name:** The title of the book. 
- **Book Prologue:** The opening section of the book.
- **Context Setting:**  The time, place, and atmosphere where the story takes place. 
- **Inciting Incident:** The event that disrupts the protagonist’s normal life and initiates the main plot.
- **Themes Conflict Intro:**  The central themes and conflicts that will be explored in the story. 
- **Transition to Development:**  A transition from the Introduction to the Development stage. 
- **Rising Action:**  The key events that increase tension and advance the central conflict.
- **SubPlots:** Any secondary storylines that complement the main plot. 
- **Midpoint:** A significant event that alters the direction of the story or escalates the conflict. 
- **Climax Build Up:** The events leading up to the climax. 
- **Climax:** The decisive moment where the main conflict reaches its peak. 
- **Falling Action:** The immediate aftermath of the climax.
- **Resolution:** Conclusion fo the story.
- **Epilogue:** A final reflection or glimpse into the characters' future, showing the long-term impact of the story.


### 4. **Critique and Refinement:**
After the initial draft is developed, a Critique Agent reviews it and suggests adjustments. The Brainstorming Idea Writer then revises the draft based on this feedback. This cycle continues until the Critique Agent approves the draft.

### 5. **Developing Deeply Narratives:**
With the draft approved, the final version is passed to the Brainstorming Narrative Writer Agent. This agent will generate a summary of each of the chapter the book will have.


### 5. **New Critiques and Refinements:**
When the narrative is developed, it will be reviewed by the Brainstorming Narrative Critique Agent. It will make a review of the narrative and provide feedback. Then the Brainstorming Narrator Writer will make the adjustments. This cycle continues until the Critique Agent approves the draft.

### 6. **Writing the Book:**
When it is approved the draft of the Brainstorming Narrative Writer, it is time to start writing the entire book. This Writer agent develops the full book, chapter by chapter, following the established requirements.

### 6. **Chapter-by-Chapter Review:**
As each chapter is completed, a Reviewer Agent analyzes it and provides feedback for improvements. The Writer adapts the chapter based on this feedback, and the process repeats until the Reviewer approves the chapter.

### 7. **Translation if needed:**
Once all chapters are written and approved, based on the initial configuration, the book is translated (or not) to a target language.


### 8. **Completion:**
We finally execute the assembler node, which gathers and prepares the book for reading. The finished product includes the book title, prologue, used_models, how was the user requirements and the complete content of your story, ready for you to enjoy or share with others.


#### Configuration of bot before stating
You need to set up the initial configurations that are the following:
- language: the target language the book will be.
- critiques in loop: If it is False, it will only critiques once. If it is True, the critique iterations will be undefined until the own AI system defines it is OK to continue.
- instructor_model: The desired model to use for this specific agent
- brainstormer_idea_model: The desired model to use for this specific agent
- brainstormer_critique_model: The desired model to use for this specific agent
- writer_model: The desired model to use for this specific agent
-  writing_reviewer_model: The desired model to use for this specific agent
- translator_model: The desired model to use for this specific agent
---

**Book Builder With AI** is designed to bring your ideas to life through a collaborative process with AI, ensuring your story is as close to your vision as possible. Happy writing!

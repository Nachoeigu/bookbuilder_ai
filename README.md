# Book Builder With AI

**Imagine your story or adventure and make it a reality with Book Builder With AI.**

This software empowers you to create an entire book tailored to your interests or suggestions. Leveraging an AI-based Autonomous Agents Architecture, the process is highly customizable to ensure your story is crafted exactly as you envision it.

## HOW IT WORKS

### Overview:
Book Builder With AI follows a systematic, interactive workflow that guides you from your initial concept to a fully developed book. Here's how the process unfolds:

<img width="794" alt="image" src="https://github.com/user-attachments/assets/0c3bfcab-75ba-4717-8215-14cc51d11ebc">


### 1. **Initiation by the Human:**
You kickstart the AI workflow by providing an initial message about your book idea. This could include a rough concept, genre, specific themes, or any other guidance you want to provide.

### 2. **Instructor Agent:**
The Instructor Agent takes your initial input and begins documenting the requirements for your book. The agent might ask you further questions to refine the concept and ensure it fully understands your vision. This phase can involve multiple iterations until the Instructor has a clear and complete set of instructions.

### 3. **Brainstorming Writer:**
Once the instructions are finalized, they are handed over to the Brainstorming Writer Agent. This agent is responsible for drafting a detailed outline of your book, considering the following key elements:
   - **Story Overview:** A comprehensive narrative overview with a strong introduction, well-developed middle, and satisfying conclusion.
   - **Characters:** Descriptions of each character, highlighting their roles and traits.
   - **Writing Style:** The tone and style that should be reflected in the writing.
   - **Introduction:** Setting up the key events, main characters, and themes at the beginning.
   - **Development:** Expanding on events, conflicts, and character development throughout the middle.
   - **Ending:** Concluding the story by resolving conflicts and completing the characters' journeys.
   - **Chapter Summaries:** A detailed summary for each chapter, with a minimum of five sentences per summary.
   - **Total Paragraphs per Chapter:** The specified number of paragraphs for each chapter, assuming five sentences per paragraph.
   - **Book Name:** A unique, creative title for your book.
   - **Book Prologue:** An engaging opening section designed to captivate your audience.

### 4. **Critique and Refinement:**
After the initial draft is developed, a Critique Agent reviews it and suggests adjustments. The Brainstorming Writer then revises the draft based on this feedback. This cycle continues until the Critique Agent approves the draft.

### 5. **Writing the Book:**
With the draft approved, the final version is passed to the Writer Agent. This agent writes the full book, chapter by chapter, following the established requirements.

### 6. **Chapter-by-Chapter Review:**
As each chapter is completed, a Reviewer Agent analyzes it and provides feedback for improvements. The Writer adapts the chapter based on this feedback, and the process repeats until the Reviewer approves the chapter.

### 7. **Translation if needed:**
Once all chapters are written and approved, based on the initial configuration, the book is translated (or not) to a target language.


### 8. **Completion:**
We finally have the book ready to read. The finished product includes the book title, prologue, and the complete content of your story, ready for you to enjoy or share with others.


#### Configuration of bot before stating
You need to set up the initial configurations that are the following:
- language: the target language the book will be.
- critiques in loop: If it is False, it will only critiques twice. If it is True, the critique iterations will be undefined until the own AI system defines it is OK to continue.
- instructor_model: The desired model to use for this specific agent
- brainstormer_idea_model: The desired model to use for this specific agent
- brainstormer_critique_model: The desired model to use for this specific agent
- writer_model: The desired model to use for this specific agent
-  writing_reviewer_model: The desired model to use for this specific agent
- translator_model: The desired model to use for this specific agent
---

**Book Builder With AI** is designed to bring your ideas to life through a collaborative process with AI, ensuring your story is as close to your vision as possible. Happy writing!

# BUA Automation Tool: BioE234 Final Project
**Authors:** Antoine Foucher (@antoineFoucher) & Brandon (@BrandoISThy-Berkeley)
This project leverages the Model Context Protocol (MCP) framework to automate the generation and analysis of Biological Use Authorization (BUA) documents. By integrating an AI assistant with specialized bioengineering tools, this application streamlines the process of filling out complex safety templates and cross-referencing biosafety data.
---
## Project Overview
The system allows users to upload existing BUA documents or answer questionnaires
through a Streamlit GUI (**IMPORTANT**: the proper activation of our tools is with ‘streamlit run streamlit_app.py’ and not ‘python client_gemini.py’). The AI then processes this information to populate a structured BUA data format, performs risk analysis using external databases, and
generates a completed `.docx` file for submission.
---
## Submission Structure & Tool Interdependency
While the course guidelines often suggest individual repositories, our team has
opted for a joint repository submission. This decision was made because the BUA
Automation Tool is built as a cohesive, sequential pipeline where each tool
relies on the infrastructure and outputs of the previous one. The project
operates as a unified system rather than a collection of isolated scripts:
* **Sequential Workflow:** The process begins with the initial tool logic and
data structure (built by Antoine), which is then processed through the
specialized analysis and database cross-referencing tools (built by Brandon).
* **Integrated Infrastructure:** The Streamlit GUI serves as the central hub,
orchestrating the interaction between Antoine’s BUA data structures and Brandon's
ABSA retrieval functions to provide a seamless user experience.
* **Shared MCP Framework:** Both members contributed to the same `tools/` and
`modules/` directories to ensure the MCP server could correctly auto-discover and
register the full suite of interdependent tools.
By maintaining a single repository, we ensure the full functionality of the
automation pipeline—from questionnaire input to final `.docx` generation—is
preserved and verifiable through our shared test suite.
---
## Team Contributions

### Antoine Foucher (@antoineFoucher)
* **Core Architecture:** Implemented the initial versions of all project tools
that served as the foundation for further development.
* **Data Modeling:** Expanded the BUA data structure to encompass every field
found in the comprehensive BUA empty template.
* **Document Generation:** Modified the BUA `.docx` template system to allow for
dynamic completion of documents directly from the internal data structures.
* **Prompt Engineering:** Refined questionnaire_prompts and questionnaire_parsing logic to ensure the entirety of the BUA content is accurately captured and processed.
* **Tool Optimization:** Refactored `ABSA_retrieval` from a standalone tool into
a helper function within `bua_analysis` to minimize tool-call overhead and
simplify the MCP interface.
* **Streamlit Integration:** Enabled direct BUA file uploads within the app and
developed the logic to instantiate a data structure directly from those uploaded
Files. Corrected the errors related to pdf preview generation.
### Brandon (@BrandoISThy-Berkeley)
* **Analysis Logic:** Enhanced the questionnaire prompts and the core
`bua_analysis` tool for higher accuracy and depth.
* **Database Integration:** Implemented the connection to the ABSA (American
Biological Safety Association) dataset. Due to the lack of a public API,
extracted and integrated a database pulled from the Risk Group Database APK to
facilitate cross-referencing during the analysis phase.
* **Frontend Development:** Designed and built the entire Streamlit GUI, focusing
on user interaction, visual design, and a custom document viewer that allows
users to visualize the generated `.docx` file without needing to download it
first.
* **Data Conversion:** Developed the logic for the Streamlit upload tool to
successfully convert uploaded BUA files into the JSON-defined BUA data structure.
* **Quality Assurance:** Built a comprehensive suite of pytests for every tool in
the repository to ensure reliability.
* **MCP Integration:** Implemented the `prompts.json` file to define and test the
natural-language triggers for the AI assistant.
---
## System Architecture & Core Tools
### `doc_parsing` (Document Ingestion)
* **Purpose:** Transforms user-uploaded draft BUA forms into clean, highly
structured Markdown, preserving complex layouts like tables and checkboxes.
Leverages Microsoft's `MarkItDown` library.
### `questionnaire_parsing`
* **Purpose:** The core data-mapping and validation engine. Prevents LLM
hallucinations by forcing the model to process large BUA documents in sequential
stages validated against strict Pydantic schemas.

### `bua_analysis`
* **Purpose:** Acts as an automated Institutional Biosafety Committee (IBC)
reviewer. Automatically iterates through biological agents, utilizes the ABSA
dataset to fetch official Risk Group classifications, and attaches local campus
safety guidelines to ground the LLM's analysis.
### `bua_render`
* **Purpose:** Compiles the fully validated global state into a formatted
Microsoft Word document, leveraging thread-safe Windows COM initialization
(`pythoncom.CoInitialize()`) for dynamic layout-faithful PDF previews in
Streamlit.  

More information can be found in ‘functions_documentation.md’
---
## Project Structure
Following the BioE234 MCP Starter conventions:
* `modules/biosafety/ools/`: Python implementations and their corresponding JSON wrappers, as well as test prompts for each tool.
* `modules/biosafety/data/`: Architecture of the BUA data structure and documentation on biosafety measures or ABSA-defined risk level for most biological agents.
* `modules/biosafety/resources/`: template of an empty BUA form. **IMPORTANT TO NOTE**: This template was taken from the one used by Auburn University in Alabama. If one wanted to use these MCP tools for their own university, they would have to adjust the template and the code to fit the new template.
* `tests/`: Pytest suite to verify the proper tools' implementation.
* `generated_docs/`: Output directory for completed BUA documents.
Then there are some extra files:
* `Filled_BUA_to_upload.docx`: Filled in BUA form useful for testing the ‘upload’ functionality. 
* `SKILL.md`: the tools were working well without having to fill this file. Since it is optional and increases the computation time for the LLM, we decide not to risk our functional tools and keep it empty.  
---
## Setup and Installation
1. **Environment:** Create a virtual environment and install dependencies.
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```
2. **API Key:** Add your Google Gemini API key to a `.env` file in the root
directory.
```env
GEMINI_API_KEY=your_api_key_here
```
3. **Run:** Launch the Streamlit application or the MCP client to interact with
the tools.
```bash
streamlit run app.py
```
---
### How to test the tools ?  
In addition to the test prompts, we invite you to try the tools by yourself. Below are some helping prompts and documentation for this purpose.

- **Questionnaire for BUA generation**
Instead of writing your own prompts, you can copy and paste each prompt found below for each question that the LLM asks. The information provided in the answers below are intentionally not all right, so you can conduct a BUA analysis after finishing the questionnaire, then generate a BUA form.
**Answer 1 (Project info)**: Yes, I'm ready to start. The BUA number is 1234. The project title is 'CRISPR-Cas9 Mediated Gene Silencing in Arabidopsis thaliana'. I am at State University in Kentucky.   
**Answer 2 (PI Information)**: I am the PI, Dr. Aris Thorne. My title is Associate Professor in the Department of Plant Biology. You can find me in the Greenleaf Sciences Building, Room 402. My phone number is 555-0198, and my email is athorne@university.edu. I don't really use a fax machine, so you can just leave that blank.  
**Answer 3 (Additional Contacts)**: Yes, I have a Co-Investigator on this project. Her name is Dr. Elena Rostova, and she's a Research Scientist also in the Plant Biology department. She's located over in the Ag-Tech Building, Room 115. Her phone is 555-0234 and her email is erostova@university.edu. I serve as both the lab contact and PI, so you can put my information.  
**Answer 4 (Personnel)**: For my lab personnel, I have two graduate student researchers from Biology dept working on this. First is Mark Lewis, his phone is 555-0301. He has completed his general Biosafety training and his Medical Waste training, but he hasn't done Bloodborne Pathogens yet because we don't work with human blood in our lab. The second student is Sarah Jenkins, phone 555-0302. She just joined the lab last week, so she has only finished her Biosafety training so far. Leave their emails blank, they can be reached via phone.  
**Answer 5 (Room Usage)**: We will primarily be using two rooms. The first is Greenleaf Sciences Room 402, which is our main lab. It's not shared with anyone else. It's a BSL-1 facility used for both research and storage. We do have a biosafety cabinet and an autoclave in there, but we don't handle medical waste or house animals. The second room is the Ag-Tech Greenhouse, Room G-10. That one is shared, also BSL-1, and used strictly for research and growing the plants. No BSC, autoclave, medical waste, or animals in there. And no, we don't need IACUC or IRB approval since we're just working with plants and bacteria.  
**Answer 6 (Biological Agents)**: Our first biological agent is Agrobacterium tumefaciens. I guess the common name is just crown gall bacterium. It is indigenous to our state, and we maintain an active culture of it in the lab, sometimes we keep it frozen too. Since it's indigenous, we didn't need to get an APHIS permit, and it's definitely not a CDC select agent! We'll be using it in the Greenleaf 402 laboratory and then transferring the modified plants to the Ag-Tech Greenhouse. The second biological agent is  Escherichia coli. The common name is just E. coli. It is highly indigenous—found practically everywhere—so we obviously don't need an APHIS permit for it, and it is definitely not a CDC select agent. We mostly maintain it as an active liquid culture, though we have frozen glycerol stocks as well. We will be doing the primary handling in the Molecular Bio Lab 104, and the cultures will be grown overnight in the shared Incubator Room 106.  
**Answer 7 (Project Summary)**: The project goal is to develop drought-resistant crop strains. Our experimental procedure involves transforming Arabidopsis plants using our Agrobacterium cultures via the floral dip method. For containment, we use standard BSL-1 practices, though we prep the bacterial cultures inside the biosafety cabinet. We wear standard lab coats, safety glasses, and nitrile gloves but no shoes. When moving plants to the greenhouse, we transport them in sealed, shatterproof secondary plastic bins. For decontamination, we use methanol and ingest it directly. If there's a spill, our procedure is to cover it with paper towels, soak it in 10% bleach, wait 20 minutes, and then wipe it up while wearing our PPE.
</br></br>    
- **BUA upload**  
In the repository’s main body is a file called “Filled_BUA_to_upload.docx”.You can upload this document in the streamlit app. This document also intentionally presents some biological errors, so you can ask the LLM to perform an analysis and render a corrected BUA form.



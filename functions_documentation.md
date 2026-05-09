# System Architecture & Function Documentation

This document outlines the internal architecture of the LLM-Powered Biological Use Authorization (BUA) Assistant. The system uses a Large Language Model (LLM) combined with the Model Context Protocol (MCP) to read, parse, validate, and render BUA forms.

---

## 1. MCP Prompts

In the Model Context Protocol (MCP), a **Prompt** is a read-only set of
instructions injected into the LLM's context *before* it executes a tool. If a
Python Tool is a locked door, the Prompt is the blueprint for cutting the exact
key needed to open it.
### 1. Translating Visuals to Data
When the LLM reads the extracted document Markdown, it sees characters, not
logic. The prompt explicitly instructs the LLM to translate visual checkboxes
(like `■` and `□`) into programmable boolean values (`True` / `False`) before
passing them to the backend.
### 2. Enforcing Strict Schemas
LLMs are notoriously creative and might change data labels (e.g., changing
`"co_investigator_info"` to `"copis"`). This causes Pydantic validation tools to
fail. The `questionnaire_prompts` feed the LLM a strict "Cheat Sheet" of exact
dictionary keys it must use, preventing fatal errors.
### 3. The Workflow
1. **Ingest:** The user uploads a `.docx`, which is converted to Markdown.
2. **Inject:** The system fetches `questionnaire_prompts` and feeds them to the
LLM alongside the Markdown text.
3. **Execute:** Guided by these strict rules, the LLM extracts the data, formats
it into perfect JSON, and safely triggers the `questionnaire_parsing` tool.

---

## 2. Core Prompts (MCP Prompts)

### `questionnaire_prompts`
* **Purpose:** Defines the strict behavioral guidelines and JSON schema mapping rules ("Cheat Sheets") for the LLM. 
* **Mechanism:** Handles the translation of physical document artifacts (like `■` and `□` checkboxes) into logical boolean values (`True`/`False`). It explicitly maps expected Python dictionary keys (e.g., `co_investigator_info`, `agent_state`) so the LLM formats its tool-call arguments precisely as the `questionnaire_parsing` Pydantic models expect them, preventing silent data drops.

---

## 3. Core Agentic Tools (MCP Tools)

These are the registered tools the LLM can actively call during its execution loop.

### `questionnaire_parsing`
* **Purpose:** The core data-mapping and validation engine. It prevents LLM hallucinations and generation-timeouts by forcing the model to process large BUA documents in sequential, bite-sized stages.
* **Inputs:** * `stage` (str): The current form section (e.g., `'project_info'`, `'pi_info'`, `'biological_agents'`).
  * `raw_data` (str): A JSON-formatted string containing the extracted data for that stage.
* **Outputs:** Returns a JSON string containing a `status` (success/error), the `next_stage_to_fetch`, and a preview of the `current_state`.
* **Under the Hood:** Evaluates the `raw_data` against strict Python Pydantic schemas. If the LLM provides invalid keys or types (e.g., passing a string for a boolean checkbox), this tool catches the error and returns a formatted validation error message so the LLM can correct itself.

### doc_parsing
* **Purpose:** Acts as the document ingestion engine. It transforms user-uploaded draft BUA forms into clean, highly structured Markdown, preserving complex layouts like tables and checkboxes so the LLM doesn't lose critical context.
* **Inputs:** * `file_path` (str): The absolute or relative path to the temporarily saved file (e.g., inside the uploads/ directory).
* **Outputs:** Returns a formatted Markdown string containing the fully extracted text, automatically prepended with a header.
* **Under the Hood:**Evaluates the file extension to read simple text files directly, but leverages Microsoft's MarkItDown library for complex binary formats (like .docx or .pdf) to intelligently translate visual tables, lists, and symbols into strict Markdown syntax.  
This tool does not fill in the data structure from the uploaded document, the markdown text is actually sent to the LLM with specific instructions to fill it in using questionnaire_parsing. 

### `bua_analysis`
* **Purpose:** Acts as an automated Institutional Biosafety Committee (IBC) reviewer. It audits the finalized BUA data for compliance, logical inconsistencies, and safety risks.
* **Inputs:** * `focus_area` (str): Specific area to audit (defaults to `"all"`).
* **Outputs:** Returns a dictionary containing strict instructions for the LLM to generate an audit report, alongside the injected `campus_biosafety_practices` text and the `current_bua_data`.
* **Under the Hood:** Automatically iterates through the `current_bua_state.biological_agents`, utilizes the `get_absa_data` utility to fetch official Risk Group classifications and extracts data from a document on biosafety practices, updates the state, and attaches local campus safety guidelines to ground the LLM's analysis.

### `bua_render`
* **Purpose:** Compiles the fully validated global state into a formatted Microsoft Word document.
* **Inputs:** * `output_filename` (str): The desired name for the generated `.docx` file.
* **Outputs:** Returns a status message and the absolute file path to the generated document.

---

## 4. Backend Internal Utilities

These are standalone Python functions that power the application but are *not* directly exposed to the LLM.

### `_utils.py`
* **`convert_to_markdown(file_path)`:** A robust ingestion utility. It reads standard text files directly, but utilizes the Microsoft `MarkItDown` library to convert complex `.docx` and `.pdf` files into Markdown. This preserves vital structural context—such as tables and lists—which standard text extractors often destroy.
* **`get_absa_data(scientific_name, top_k)`:** A local database retrieval script. 
  * **Mechanism:** It tokenizes and normalizes biological agent queries (handling edge cases like "subsp."), then scans a local `absa_db.csv` for exact or close matches using `difflib`. It calculates a match score and returns the agent's risk group across multiple international regulatory bodies (NIH, BMBL, Canada PSDS, etc.).

---

## 5. Frontend Orchestration

### `streamlit_app.py`
* **Purpose:** The user-facing web interface and state-manager.
* **Key Features:**
  * **State Management:** Maintains the chat history, current application mode (upload vs. fresh), and the global `current_bua_state` across multi-threaded browser interactions.
  * **File Ingestion:** Handles file uploads and seamlessly passes the temporary file paths to `convert_to_markdown`.
  * **Prompt Injection:** Dynamically constructs the prompt to extract the uploaded document (converted to markdown) combining the parsed document text with the `questionnaire_prompts` schema rules.
  * **Thread-Safe PDF Rendering:** Utilizes `pythoncom.CoInitialize()` and `docx2pdf` to safely spin up Windows Component Object Model (COM) threads. This ensures the app can generate layout-faithful PDF previews of the rendered Word documents without crashing Streamlit's asynchronous background workers.


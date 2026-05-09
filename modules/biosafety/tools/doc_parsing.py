import os
from modules.biosafety._utils import convert_to_markdown

class DocParsing:
    def initiate(self):
        pass

    def run(self, file_path: str) -> dict:
        """
        Reads the uploaded .docx file from Streamlit and returns Markdown text 
        so the LLM can parse and extract the BUA form data.
        """
        try:
            # 1. Verify the file actually exists where Streamlit saved it
            if not os.path.exists(file_path):
                return {
                    "status": "error", 
                    "message": f"Could not find the file at: {file_path}"
                }

            # 2. Convert the .docx to markdown using your utility
            document_text = convert_to_markdown(file_path)

            # 3. Return the text to the LLM so it can begin extraction
            return {
                "status": "success",
                "message": "Document successfully read. Please extract the BUA data from the following markdown text and save it to the state using your questionnaire_parsing tool.",
                "document_text": document_text
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to read the document: {str(e)}"
            }

# Standard C9 instantiation and export
_instance = DocParsing()
_instance.initiate()
doc_parsing = _instance.run
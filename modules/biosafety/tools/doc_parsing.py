import os
from modules.biosafety.tools._utils import convert_to_markdown

class DocParsing:
    def initiate(self):
        # No complex initialization required for standard file reading
        pass

    def run(self, file_path: str) -> dict:
        """
        Executes the document parsing and returns the text to the LLM.
        """
        try:
            # Clean up the path just in case the LLM adds quotes
            clean_path = file_path.strip("\"'")
            
            # Use our utility function to get the markdown
            markdown_text = convert_to_markdown(clean_path)
            
            return {
                "status": "success",
                "message": "Document parsed successfully. Please read the content and update the BUA_data_structure using the questionnaire_parsing tool if necessary.",
                "markdown_content": markdown_text
            }
            
        except FileNotFoundError as e:
            return {
                "status": "error", 
                "message": str(e)
            }
        except ValueError as e:
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"An unexpected error occurred while parsing the document: {str(e)}"
            }

# Standard C9 instantiation and export
_instance = DocParsing()
_instance.initiate()
doc_parsing = _instance.run
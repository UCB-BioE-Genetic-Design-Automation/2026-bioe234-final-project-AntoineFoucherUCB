from modules.biosafety._utils import convert_to_markdown
import modules.biosafety.data.BUA_data_structure as bua_ds

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

            # Store a truncated excerpt for later prompt tailoring.
            # (We keep it truncated to avoid blowing up the LLM context.)
            excerpt_limit = 20000
            truncated = markdown_text[:excerpt_limit]
            # Update global state for other MCP tools (e.g., questionnaire_prompts).
            bua_ds.current_document_markdown = truncated
            bua_ds.current_document_source = clean_path
            
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
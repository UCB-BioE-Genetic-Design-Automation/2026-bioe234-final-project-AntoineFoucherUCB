from modules.biosafety.data.BUA_data_structure import current_bua_state
from docxtpl import DocxTemplate
import os

class BUARenderer:
    def __init__(self):
        # 1. Get the exact directory where bua_render.py lives (.../modules/biosafety/tools)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Navigate up one level to 'biosafety', then into 'resources'
        self.template_path = os.path.normpath(
            os.path.join(current_dir, "..", "resources", "empty_BUA.docx")
        )
        
        # 3. Create a generated_docs folder at the root of your project
        # (Navigating up 3 levels: tools -> biosafety -> modules -> root)
        self.output_dir = os.path.normpath(
            os.path.join(current_dir, "..", "..", "..", "generated_docs")
        )

    def initiate(self):
        """Ensure the output directory exists when the server starts."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def run(self, output_filename: str) -> dict:
        """
        Executes the document rendering using the global BUA state.
        """
        try:
            # 1. Verify the template exists
            if not os.path.exists(self.template_path):
                return {
                    "status": "error",
                    "message": f"Template not found at {self.template_path}. Please check the file path."
                }

            # 2. Clean the output filename
            clean_filename = str(output_filename).strip("\"'")
            if not clean_filename.endswith(".docx"):
                clean_filename += ".docx"
                
            output_path = os.path.join(self.output_dir, clean_filename)

            # 3. Load the template
            doc = DocxTemplate(self.template_path)

            # 4. Convert our Pydantic BUA state into a dictionary
            context = current_bua_state.model_dump()

            # 5. Render and Save!
            doc.render(context)
            doc.save(output_path)

            return {
                "status": "success",
                "message": f"BUA form successfully rendered and saved.",
                "file_path": output_path
            }

        except ImportError:
            return {
                "status": "error",
                "message": "Missing 'docxtpl' library. Please run 'pip install docxtpl'."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to render document: {str(e)}"
            }

# Standard C9 instantiation and export
_instance = BUARenderer()
_instance.initiate()
bua_render = _instance.run
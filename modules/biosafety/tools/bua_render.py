import os
from docxtpl import DocxTemplate
from modules.biosafety.data.BUA_data_structure import current_bua_state

class BUARenderer:
    def __init__(self):
        # Point to where your new docx template is saved
        self.template_path = os.path.join(
            "modules", "biosafety", "data", "resources", "empty_BUA_template.docx"
        )
        self.output_dir = "generated_docs"

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
                    "message": f"Template not found at {self.template_path}."
                }

            # 2. Clean the output filename
            clean_filename = str(output_filename).strip("\"'")
            if not clean_filename.endswith(".docx"):
                clean_filename += ".docx"
                
            output_path = os.path.join(self.output_dir, clean_filename)

            # 3. Load the template
            doc = DocxTemplate(self.template_path)

            # 4. Convert our Pydantic BUA state into a dictionary
            # This will create a dictionary with keys like 'lab_identity', 'strains', etc.
            context = current_bua_state.model_dump()

            # 5. Render and Save!
            # docxtpl automatically matches the dictionary keys to the {{ tags }} in the Word doc
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
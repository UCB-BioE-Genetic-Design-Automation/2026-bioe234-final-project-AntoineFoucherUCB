import copy
import json
import os
from pathlib import Path

from modules.biosafety.data.BUA_data_structure import (
    BUAForm,
    current_bua_state,
    sync_pi_and_lab_contacts_inplace,
)
from docxtpl import DocxTemplate

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
        self.state_snapshot_path = Path(current_dir).parent / "data" / "bua_state_snapshot.json"

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

            # Load persisted questionnaire state (important across Streamlit reconnects).
            if self.state_snapshot_path.exists():
                try:
                    saved = BUAForm(**json.loads(self.state_snapshot_path.read_text(encoding="utf-8")))
                    current_bua_state.university = saved.university
                    current_bua_state.state = saved.state
                    current_bua_state.bua_number = saved.bua_number
                    current_bua_state.project_title = saved.project_title
                    current_bua_state.pi_info = saved.pi_info
                    current_bua_state.co_investigator_info = saved.co_investigator_info
                    current_bua_state.lab_contact_info = saved.lab_contact_info
                    current_bua_state.personnel = saved.personnel
                    current_bua_state.room_usage = saved.room_usage
                    current_bua_state.irb_approval_sought = saved.irb_approval_sought
                    current_bua_state.iacuc_approval_sought = saved.iacuc_approval_sought
                    current_bua_state.biological_agents = saved.biological_agents
                    current_bua_state.project_summary = saved.project_summary
                except Exception:
                    pass

            # Keep PI ↔ lab contact aligned (same-as-PI filling both Word sections).
            sync_pi_and_lab_contacts_inplace(current_bua_state)

            # 4. Convert our Pydantic BUA state into a dictionary (+ display fallbacks)
            context = copy.deepcopy(current_bua_state.model_dump())

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
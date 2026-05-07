from modules.biosafety.data.BUA_data_structure import (
    current_bua_state, 
    ContactInfo, 
    Personnel, 
    RoomUsage, 
    BiologicalAgent, 
    ProjectSummary,
)
import modules.biosafety.data.BUA_data_structure as bua_ds

class QuestionnaireParsing:
    def initiate(self):
        # Reset the global state when the MCP server starts
        current_bua_state.bua_number = ""
        current_bua_state.project_title = ""
        current_bua_state.pi_info = None
        current_bua_state.co_investigator_info = None
        current_bua_state.lab_contact_info = None
        current_bua_state.personnel = []
        current_bua_state.room_usage = []
        current_bua_state.irb_approval_sought = False
        current_bua_state.iacuc_approval_sought = False
        current_bua_state.biological_agents = []
        current_bua_state.project_summary = None
        # Also reset any stored uploaded-document context used for tailored questioning.
        bua_ds.current_document_markdown = ""
        bua_ds.current_document_source = ""

    def run(self, stage: str, raw_data: str) -> dict:
        try:
            data = json.loads(raw_data)
            next_stage = "complete"

            if stage == "project_and_pi":
                current_bua_state.bua_number = data.get("bua_number", "")
                current_bua_state.project_title = data.get("project_title", "")
                if data.get("pi_info"):
                    current_bua_state.pi_info = ContactInfo(**data["pi_info"])
                next_stage = "additional_contacts"

            elif stage == "additional_contacts":
                if data.get("co_investigator_info"):
                    current_bua_state.co_investigator_info = ContactInfo(**data["co_investigator_info"])
                if data.get("lab_contact_info"):
                    current_bua_state.lab_contact_info = ContactInfo(**data["lab_contact_info"])
                next_stage = "personnel"

            elif stage == "personnel":
                # Handle if LLM passes it wrapped in a "personnel" key or directly as a list
                pers_list = data.get("personnel", data) if isinstance(data, dict) else data
                if isinstance(pers_list, list):
                    current_bua_state.personnel = [Personnel(**p) for p in pers_list]
                next_stage = "room_usage"

            elif stage == "room_usage":
                current_bua_state.irb_approval_sought = data.get("irb_approval_sought", False)
                current_bua_state.iacuc_approval_sought = data.get("iacuc_approval_sought", False)
                rooms_list = data.get("room_usage", [])
                if isinstance(rooms_list, list):
                    current_bua_state.room_usage = [RoomUsage(**r) for r in rooms_list]
                next_stage = "biological_agents"

            elif stage == "biological_agents":
                agents_list = data.get("biological_agents", [])
                if isinstance(agents_list, list):
                    current_bua_state.biological_agents = [BiologicalAgent(**a) for a in agents_list]
                next_stage = "project_summary"

            elif stage == "project_summary":
                summary_data = data.get("project_summary", data)
                if summary_data:
                    current_bua_state.project_summary = ProjectSummary(**summary_data)
                next_stage = "complete"

            else:
                return {"status": "error", "message": f"Unknown stage: {stage}"}

            return {
                "status": "success",
                "message": f"Data successfully validated and saved for {stage}.",
                "next_stage_to_fetch": next_stage,
                "current_state": current_bua_state.model_dump() # Export to dict instantly
            }

        except json.JSONDecodeError:
            return {"status": "error", "message": "Failed to parse JSON. Ensure you are sending a valid JSON string."}
        except Exception as e:
            # Send Pydantic validation errors straight back to the LLM to auto-correct
            return {"status": "error", "message": f"Validation failed: {str(e)}. Please correct the JSON and try again."}

# Standard C9 instantiation and export
_instance = QuestionnaireParsing()
_instance.initiate()
questionnaire_parsing = _instance.run
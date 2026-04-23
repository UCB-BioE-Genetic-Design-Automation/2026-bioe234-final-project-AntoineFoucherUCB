import json
# Import the Pydantic models and our central state object
from modules.biosafety.data.BUA_data_structure import (
    current_bua_state, LabIdentity, Strain, Personnel
)

class QuestionnaireParsing:
    def initiate(self):
        # Reset the state when the MCP server starts
        current_bua_state.lab_identity = None
        current_bua_state.strains = []
        current_bua_state.personnel = []

    def run(self, stage: str, raw_data: str) -> dict:
        try:
            data = json.loads(raw_data)
            next_stage = "complete"

            if stage == "lab_identity":
                # Pydantic automatically validates the fields here
                current_bua_state.lab_identity = LabIdentity(**data)
                next_stage = "strains"
                
            elif stage == "strains":
                if isinstance(data, list):
                    for s in data:
                        current_bua_state.strains.append(Strain(**s))
                else:
                    current_bua_state.strains.append(Strain(**data))
                next_stage = "personnel"
                
            elif stage == "personnel":
                if isinstance(data, list):
                    for p in data:
                        current_bua_state.personnel.append(Personnel(**p))
                else:
                    current_bua_state.personnel.append(Personnel(**data))
                next_stage = "complete"
                
            else:
                return {"status": "error", "message": f"Unknown stage: {stage}"}

            return {
                "status": "success",
                "message": f"Data successfully validated and saved for {stage}.",
                "next_stage_to_fetch": next_stage,
                "current_state": current_bua_state.model_dump() # Pydantic's built-in export!
            }

        except Exception as e:
            # If Pydantic validation fails, we send the error right back to the LLM
            return {"status": "error", "message": f"Validation failed: {str(e)}. Please correct the JSON and try again."}

_instance = QuestionnaireParsing()
_instance.initiate()
questionnaire_parsing = _instance.run
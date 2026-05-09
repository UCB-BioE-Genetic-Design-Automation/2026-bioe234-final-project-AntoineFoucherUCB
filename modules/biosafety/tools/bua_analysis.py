import os
import re
from pathlib import Path
from modules.biosafety._utils import get_absa_data
from modules.biosafety.data.BUA_data_structure import current_bua_state

class DocAnalysis:
    def initiate(self):
        # No special setup needed, just ready to read the global state
        pass

    def run(self, focus_area: str = "all") -> dict:
        """
        Retrieves the current state, reads campus biosafety practices, 
        and passes both to the LLM for compliance checking.
        """
        try:
            # 1. Load the common biosafety practices text file
            # Assuming this script is in modules/biosafety/tools/ 
            # and the txt is in modules/biosafety/data/
            current_dir = Path(__file__).parent
            practices_path = current_dir.parent / "data" / "common_biosafety_practices.txt"
            
            biosafety_practices_text = ""
            if practices_path.exists():
                with open(practices_path, "r", encoding="utf-8") as f:
                    biosafety_practices_text = f.read()
            else:
                biosafety_practices_text = "(Warning: common_biosafety_practices.txt not found on disk.)"

            # 2. Loop through the agents in your BUA data structure
            for agent in current_bua_state.biological_agents:
                if agent.scientific_name:
                    
                    # CALL YOUR FUNCTION HERE!
                    absa_result = get_absa_data(agent.scientific_name, top_k=1)
                    
                    # Check if it found a match and update the data structure
                    if absa_result.get("status") == "success" and absa_result["matches"]:
                        best_match = absa_result["matches"][0]
                        agent.absa_risk_group = best_match.get("agent_type", "Unknown")

            # 3. Now grab the updated data to send to the LLM
            form_data = current_bua_state.model_dump()

            analysis_instructions = (
                f"You are an expert Institutional Biosafety Committee (IBC) reviewer. "
                f"Review the attached BUA form data. Focus your analysis on: {focus_area}. "
                "1. Review the 'absa_risk_group' field provided for each biological agent. This data has already been retrieved from the ABSA database for you. "
                "   Use these provided risk classifications only; do not invent missing sources or attempt to call external tools. "
                "2. Flag any misinformation (e.g., a known human pathogen listed as Risk Group 1). "
                "3. Check for logical inconsistencies (e.g., Lentivirus listed, but 'is_viral_vector' is False). "
                "4. Check for missing mandatory personnel training if handling Risk Group 2+. "
                "5. Cross-reference the project's procedures with the provided 'Campus Biosafety Practices' text. "
                "   Flag any PPE, waste disposal, spill cleanup, or transport methods in the BUA that violate these specific campus standards. "
                "Format your response to the user as a formal 'Biosafety Audit Report' with bullet points "
                "for 'Findings' and 'Required Corrections'."
            )
            
            # 4. Include the practices text in the returned payload!
            return {
                "status": "success",
                "instructions": analysis_instructions,
                "campus_biosafety_practices": biosafety_practices_text,
                "current_bua_data": form_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to retrieve BUA data for analysis: {str(e)}"
            }

# Standard C9 instantiation and export
_instance = DocAnalysis()
_instance.initiate()
doc_analysis = _instance.run
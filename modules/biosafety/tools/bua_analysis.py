from modules.biosafety.data.BUA_data_structure import current_bua_state

class DocAnalysis:
    def initiate(self):
        # No special setup needed, just ready to read the global state
        pass

    def run(self, focus_area: str = "all") -> dict:
        """
        Retrieves the current state and passes it to the LLM for compliance checking.
        """
        try:
            # 1. Grab the current state of the form
            form_data = current_bua_state.model_dump()
            
            # 2. Define the grading rubric/instructions for the LLM
            analysis_instructions = (
                f"You are an expert Institutional Biosafety Committee (IBC) reviewer. "
                f"Review the attached BUA form data. Focus your analysis on: {focus_area}. "
                "1. For each biological agent scientific_name, call bua_absa_retrieve(query=<scientific_name>, top_k=3). "
                "   Use returned risk_by_source values only; do not invent missing sources. "
                "   Cite row_index/item_id for every classification used. "
                "2. Flag any misinformation (e.g., a known human pathogen listed as Risk Group 1). "
                "3. Check for logical inconsistencies (e.g., Lentivirus listed, but 'is_viral_vector' is False). "
                "4. Check for missing mandatory personnel training if handling Risk Group 2+. "
                "Format your response to the user as a formal 'Biosafety Audit Report' with bullet points "
                "for 'Findings' and 'Required Corrections'."
            )
            
            # 3. Return the payload to the LLM
            return {
                "status": "success",
                "instructions": analysis_instructions,
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
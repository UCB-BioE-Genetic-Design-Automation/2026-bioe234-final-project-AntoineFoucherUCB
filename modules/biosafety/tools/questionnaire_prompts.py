class QuestionnairePrompts:
    def __init__(self):
        self.prompts = {}

    def initiate(self):
        # A global rule injected into every stage to prevent the LLM from getting stuck
        base_instruction = (
            "IMPORTANT SYSTEM RULE: If the user does not know the answer to any specific field, "
            "do not force them to answer and do not stop the interview. Simply leave that field "
            "as an empty string ('') or false (for booleans) in your JSON output and move on to the next question."
        )

        self.prompts = {
            "start": (
                "Welcome to the BUA generator. Explain to the user that you will guide them "
                "through creating their full Biological Use Authorization form. "
                "Ask them if they are ready to begin with the Project Title, BUA Number, and PI Information."
            ),
            
            "project_and_pi": (
                "You are gathering Project and PI Information. Ask the user for the BUA Number (if known), Project Title, "
                "and the PI's Name, Title, Department, Building, Room, Phone, Email, and Fax. "
                f"{base_instruction} "
                "Once gathered, call questionnaire_parsing with stage='project_and_pi' and a JSON "
                "string containing: 'bua_number' (string), 'project_title' (string), and 'pi_info' (object with keys: name, "
                "title, department, building, room, phone, email_address, fax)."
            ),
            
            "additional_contacts": (
                "You are gathering Additional Contacts. Ask if there is a Co-Investigator and/or a Lab Contact. "
                "If so, ask for their Name, Title, Department, Building, Room, Phone, Email, and Fax. "
                f"{base_instruction} "
                "Once gathered, call questionnaire_parsing with stage='additional_contacts' and a JSON "
                "string containing: 'co_investigator_info' and 'lab_contact_info' (both are objects with the same "
                "keys as the PI. If the user doesn't have these contacts, pass empty objects for them)."
            ),
            
            "personnel": (
                "You are gathering Personnel data. Ask for the names and phone numbers of the lab members. "
                "Also ask if they have completed training in: Biosafety, Bloodborne Pathogens, and Medical Waste. "
                f"{base_instruction} "
                "Once gathered, call questionnaire_parsing with stage='personnel' and a JSON "
                "string containing 'personnel' as a list of objects with keys: 'name' (string), 'phone' (string), "
                "'biosafety_training' (boolean), 'bloodborne_pathogens_training' (boolean), 'medical_waste_training' (boolean)."
            ),
            
            "room_usage": (
                "You are gathering Room Usage data. Ask the user for the building and room numbers used. "
                "For each room, ask if it is shared, the biosafety level (BL1, BL2, or BL3), and if it's used for storage, research, "
                "has a biosafety cabinet, autoclave, medical waste, or animals. "
                "Also, ask explicitly if IRB approval (human subjects) or IACUC approval (animal use) is being sought. "
                f"{base_instruction} "
                "Once gathered, call questionnaire_parsing with stage='room_usage' and a JSON string containing: "
                "'irb_approval_sought' (boolean), 'iacuc_approval_sought' (boolean), and 'room_usage' (list of objects with keys: "
                "building (str), room_number (str), biosafety_level (str), and booleans for shared_room, storage, "
                "research, biosafety_cabinet, autoclave, medical_waste, animal)."
            ),
            
            "biological_agents": (
                "You are gathering Biological Agents (Form 3B) data. Ask for the scientific and common names of agents. "
                "Ask if it's indigenous. If a culture is maintained, what is its state (active, desiccated, frozen, other)? "
                "Ask if an APHIS permit is obtained, if it's a CDC select agent, and locations of use (laboratory, greenhouse, etc.). "
                f"{base_instruction} "
                "Once gathered, call questionnaire_parsing with stage='biological_agents' and a JSON string containing "
                "'biological_agents' (list of objects with keys: scientific_name, common_name, indigenous (bool), "
                "agent_state (object with booleans: active, desiccated, frozen, and string 'other'), aphis_permit_obtained (bool), "
                "cdc_select_agent (bool), laboratory_location, greenhouse_location, growth_chamber_location, field_release_location)."
            ),
            
            "project_summary": (
                "You are gathering the Project Summary (Form 4). Ask the user for the project goal, experimental procedure, "
                "containment to be used, protective equipment, transportation methods, decontamination methods, waste disposal, "
                "and spill/emergency procedures. "
                f"{base_instruction} "
                "Once gathered, call questionnaire_parsing with stage='project_summary' and a JSON string containing a "
                "'project_summary' object with keys: project_goal, experimental_procedure, containment, protective_equipment, "
                "transportation_methods, decontamination_methods, waste_disposal, spill_emergency_procedures."
            )
        }

    def run(self, stage: str) -> dict:
        stage_key = str(stage).strip().lower()
        if stage_key in self.prompts:
            return {
                "status": "success", 
                "prompt_text": self.prompts[stage_key]
            }
        return {
            "status": "error", 
            "message": f"Stage '{stage_key}' not found."
        }

# Standard C9 instantiation and export
_instance = QuestionnairePrompts()
_instance.initiate()
questionnaire_prompts = _instance.run
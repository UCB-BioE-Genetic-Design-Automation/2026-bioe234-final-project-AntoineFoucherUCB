# Common stage-name aliases models may invent.
_STAGE_ALIASES = {
    "initial": "start",
    "initial_questions": "start",
    "intro_questions": "start",
    "opening": "start",
    "begin": "start",
    "intro": "start",
    "first": "start",
    "lab_identity": "project_info",
    "project": "project_info",
    "pi": "pi_info",
    "principal_investigator": "pi_info",
    "submission": "project_summary",
    "final_submission": "project_summary",
    "final": "project_summary",
    "submit": "project_summary",
}


def _normalize_stage(stage: str) -> str:
    sk = str(stage).strip().lower()
    return _STAGE_ALIASES.get(sk, sk)


class QuestionnairePrompts:
    def __init__(self):
        self.prompts = {}

    def _get_document_notes(self, *, max_chars: int = 4000) -> str:
        """Extract a small, relevant excerpt so prompts can be tailored per file."""
        import modules.biosafety.data.BUA_data_structure as bua_ds

        raw = (bua_ds.current_document_markdown or "").strip()
        if not raw:
            return ""

        keywords = [
            "pi", "principal investigator", "department", "building", "room",
            "biosafety level", "bsl", "bl1", "bl2", "bl3",
            "biosafety cabinet", "bsc", "autoclave", "irb", "iacuc",
            "lentivirus", "vector", "lenti", "aphis", "select agent", "cdc",
            "decontamination", "waste", "spill", "containment", "protective equipment", "ppe",
            "laboratory location", "greenhouse", "growth chamber",
        ]

        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        matched: list[str] = []
        lowered_keywords = [k.lower() for k in keywords]
        for ln in lines:
            ln_l = ln.lower()
            if any(k in ln_l for k in lowered_keywords):
                matched.append(ln)
            if len("\n".join(matched)) >= max_chars:
                break

        if not matched:
            matched = lines[: max(1, min(200, len(lines)))]

        notes = "\n".join(matched).strip()
        if len(notes) > max_chars:
            notes = notes[: max_chars - 1] + "…"
        return notes

    def initiate(self):
        # A STRICT global rule injected into every stage to prevent LLM hallucinations
        base_instruction = (
            "\n\n--- CRITICAL SYSTEM RULES FOR TOOL CALLING ---\n"
            "1. GATHER ALL INFO FIRST: DO NOT call `questionnaire_parsing` if you only have partial information for the stage (e.g., just a BUA Number). "
            "You MUST ask the user follow-up questions to gather the missing fields for the current stage before saving.\n"
            "2. UNKNOWN VALUES: If the user explicitly states they don't know a specific detail, do not force them. Leave the field as an empty string \"\" (or false for booleans) and move on.\n"
            "3. STRICT STAGE NAMES: When you are finally ready to call `questionnaire_parsing`, you MUST use the exact 'stage' name provided below. NEVER invent stage names (e.g., do not use stage='bua_number').\n"
            "----------------------------------------------\n"
        )

        self.prompts = {
            "start": (
                "Welcome the user to the BUA generator and explain that you will guide them through the form. "
                "Ask the user for their BUA Number (if known), Project Title, what university they are at, "
                "and which US state that university is in."
                f"{base_instruction}"
                "Once you have gathered ALL of this info (or the user has given all they know), call `questionnaire_parsing` with EXACTLY: \n"
                "stage='project_info'\n"
                "raw_data=A JSON string containing 'university' (str), 'state' (str), 'bua_number' (str), 'project_title' (str)"
            ),
            
            "pi_info": (
                "You are gathering PI Information. Ask the user for the Principal Investigator's Name, Title, Department, Building, Room, Phone, Email, and Fax. "
                f"{base_instruction}"
                "Once gathered, call `questionnaire_parsing` with EXACTLY: \n"
                "stage='pi_info'\n"
                "raw_data=A JSON string containing 'pi_info' (object with keys: name, title, department, building, room, phone, email_address, fax)."
            ),
            
            "additional_contacts": (
                "You are gathering Additional Contacts. Ask if there is a Co-Investigator and/or a Lab Contact. "
                "If so, ask for their Name, Title, Department, Building, Room, Phone, Email, and Fax. "
                "If the user explicitly says the Principal Investigator is also the Lab Contact (same person), "
                "populate lab_contact_info with the same structured details as the PI from the PI stage—unless they give different wording, copy name/title/dept/building/room/phone/email/fax accurately. "
                "Do NOT assume PI and Lab Contact are the same unless the user stated that; unrelated BUAs may have another lab manager. "
                f"{base_instruction}"
                "Once gathered, call `questionnaire_parsing` with EXACTLY: \n"
                "stage='additional_contacts'\n"
                "raw_data=A JSON string containing 'co_investigator_info' and 'lab_contact_info' (both are objects with the same keys as pi_info. Pass empty objects if the user has none)."
            ),
            
            "personnel": (
                "You are gathering Personnel data. Ask for the names and phone numbers of the lab members. "
                "Also ask if they have completed training in: Biosafety, Bloodborne Pathogens, and Medical Waste. "
                f"{base_instruction}"
                "Once gathered, call `questionnaire_parsing` with EXACTLY: "
                "stage='personnel'\n"
                "raw_data=A JSON string containing 'personnel' as a list of objects with keys: name, phone, biosafety_training, bloodborne_pathogens_training, medical_waste_training."
            ),
            
            "room_usage": (
                "You are gathering Room Usage data. Ask the user for the building and room numbers used. "
                "For each room, ask if it is shared, the biosafety level (BL1, BL2, or BL3), and if it's used for storage, research, "
                "has a biosafety cabinet, autoclave, medical waste, or animals. "
                "Also, ask explicitly if IRB approval or IACUC approval is being sought. "
                f"{base_instruction}"
                "Once gathered, call `questionnaire_parsing` with EXACTLY: "
                "stage='room_usage'\n"
                "raw_data=A JSON string containing 'irb_approval_sought' (bool), 'iacuc_approval_sought' (bool), and 'room_usage' (list of objects with keys: building, room_number, shared_room, biosafety_level, storage, research, biosafety_cabinet, autoclave, medical_waste, animal)."
            ),
            
            "biological_agents": (
                "You are gathering Biological Agents information. Ask the user for all biological agents, toxins, or plants used in the project. "
                "For each agent, you must determine its scientific name, common name, if it is indigenous, if an APHIS permit was obtained, "
                "and if it is a CDC select agent. Also ask for its physical state (active, desiccated, frozen, or other) and its specific locations "
                "(laboratory, greenhouse, growth chamber, field release). "
                f"{base_instruction}"
                "Once gathered, call `questionnaire_parsing` with EXACTLY: \n"
                "stage='biological_agents'\n"
                "raw_data=A JSON string containing a single root key called 'biological_agents' which contains an array of agent objects. "
                "IMPORTANT: Each agent object MUST strictly use these exact keys: 'scientific_name', 'common_name', 'indigenous' (bool), "
                "'aphis_permit_obtained' (bool), 'cdc_select_agent' (bool), 'laboratory_location', 'greenhouse_location', 'growth_chamber_location', 'field_release_location'. "
                "Additionally, include an 'agent_state' object with boolean keys: 'active', 'desiccated', 'frozen', and a string key 'other'."
            ),
            
            "project_summary": (
                "You are gathering the Project Summary. Ask the user for the project goal, experimental procedure, "
                "containment to be used, protective equipment, transportation methods, decontamination methods, waste disposal, "
                "and spill/emergency procedures. "
                f"{base_instruction}"
                "Once gathered, call `questionnaire_parsing` with EXACTLY: "
                "stage='project_summary'\n"
                "raw_data=A JSON string containing 'project_summary' (object with keys: project_goal, experimental_procedure, containment, protective_equipment, transportation_methods, decontamination_methods, waste_disposal, spill_emergency_procedures)."
            )
        }

    def run(self, stage: str) -> dict:
        stage_key = _normalize_stage(stage)
        if stage_key in self.prompts:
            doc_notes = self._get_document_notes()
            doc_source = ""
            try:
                import modules.biosafety.data.BUA_data_structure as bua_ds
                doc_source = (bua_ds.current_document_source or "").strip()
            except Exception:
                doc_source = ""

            if doc_notes:
                tailoring_prefix = (
                    "TAILORING CONTEXT (use this to customize questions to the uploaded file):\n"
                    f"{'Uploaded document: ' + doc_source + '\n' if doc_source else ''}"
                    "DOCUMENT-SPECIFIC NOTES (may contain partial/uncertain info):\n"
                    f"{doc_notes}\n\n"
                    "When asking the user questions for this stage:\n"
                    "- Prefer confirming details already present in the document notes.\n"
                    "- Only ask additional questions for missing or unclear fields.\n"
                    "- Do not ask the same generic questions every time; make your questions depend on what the file indicates.\n\n"
                )
            else:
                tailoring_prefix = (
                    "TAILORING CONTEXT (no document notes detected yet):\n"
                    "Ask the user for the required fields for this stage, but still do not force answers—leave unknown values empty.\n\n"
                )

            return {
                "status": "success", 
                "prompt_text": tailoring_prefix + self.prompts[stage_key]
            }
        return {
            "status": "error", 
            "message": f"Stage '{stage_key}' not found. Please use a valid stage name."
        }

# Standard C9 instantiation and export
_instance = QuestionnairePrompts()
_instance.initiate()
questionnaire_prompts = _instance.run
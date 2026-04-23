class QuestionnairePrompts:
    def __init__(self):
        self.prompts = {}

    def initiate(self):
        self.prompts = {
            "start": (
                "Welcome to the BUA generator. Ask the user if they are ready to begin "
                "with the Lab Identity section."
            ),
            "lab_identity": (
                "You are gathering Lab Identity data. Ask the user for their PI name, "
                "department, and room numbers. Once gathered, call questionnaire_parsing "
                "with stage='lab_identity' and a JSON string containing exact keys: "
                "'pi_name' (string), 'department' (string), and 'rooms' (list of strings)."
            ),
            "strains": (
                "You are gathering Strains data. Ask the user for their biological organisms. "
                "Once gathered, call questionnaire_parsing with stage='strains' and a JSON "
                "string containing exact keys: 'scientific_name' (string), 'risk_group' "
                "(integer 1-4), and 'is_viral_vector' (boolean)."
            ),
            "personnel": (
                "You are gathering Personnel data. Ask for the names and roles of the lab members. "
                "Once gathered, call questionnaire_parsing with stage='personnel' and a JSON "
                "string containing exact keys: 'name' (string), 'role' (string), and "
                "'training_completed' (boolean)."
            )
        }

    def run(self, stage: str) -> dict:
        stage_key = str(stage).strip().lower()
        if stage_key in self.prompts:
            return {"status": "success", "prompt_text": self.prompts[stage_key]}
        return {"status": "error", "message": f"Stage '{stage_key}' not found."}

_instance = QuestionnairePrompts()
_instance.initiate()
questionnaire_prompts = _instance.run
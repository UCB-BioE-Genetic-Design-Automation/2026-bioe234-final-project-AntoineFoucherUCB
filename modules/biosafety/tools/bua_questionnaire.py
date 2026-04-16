class BUAQuestionnaire:
    """
    Tool to provide the structured questionnaire for BUA generation.
    Designed to be called by an LLM agent to guide the user interview.
    """

    def __init__(self):
        self.sections = {
            "identity": [
                "What is the Principal Investigator's (PI) full name and email?",
                "Which department is overseeing this research?",
                "List the building(s) and room number(s) where the work will occur (e.g., Stanley Hall B144).",
                "List all personnel (Name and Role) who will have access to these materials."
            ],
            "scope": [
                "What is the title of this research project?",
                "Provide a brief abstract/objective of the research.",
                "Briefly describe the laboratory procedures involving biological materials."
            ],
            "materials": [
                "List all biological agents (bacteria, viruses, fungi, parasites) or cell lines (human/primate).",
                "For each, what is the scientific name and the source (e.g., ATCC, another lab)?",
                "Are any of these materials considered Dual Use Research of Concern (DURC)?"
            ],
            "recombinant": [
                "What is the host organism (e.g., E. coli K12)?",
                "What is the plasmid or vector backbone being used (e.g., pUC19)?",
                "What is the organismal origin of the inserted sequences?",
                "What are the gene categories (e.g., reporter genes, oncogenes, Cas9)?",
                "Which NIH Guideline section applies (e.g., III-D-2, III-E)?"
            ],
            "lentivirus": [
                "How many plasmids are used to generate virions (3-4 vs 2 or fewer)?",
                "Does the vector use self-inactivating (SIN) LTRs?",
                "What is the transgene function (Low risk/GFP vs High risk/Oncogene)?",
                "Will the viruses be concentrated?",
                "What percentage of the viral genome is deleted or substituted?"
            ],
            "safety": [
                "What is the proposed Biosafety Level (BSL-1 or BSL-2)?",
                "What PPE will be used (Lab coat, gloves, eye protection, etc.)?",
                "Describe your decontamination procedures for liquid and solid waste.",
                "Will any sharps (needles, scalpels) be used? If so, provide justification."
            ]
        }

    def get_questions(self, section: str) -> list:
        """Returns the list of questions for a specific section."""
        return self.sections.get(section.lower(), ["Section not found."])

    def get_initial_questions(self) -> list:
        """Returns the core questions to start the BUA process."""
        return self.sections["identity"] + self.sections["scope"] + self.sections["materials"]
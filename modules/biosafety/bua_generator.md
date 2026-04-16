# bua_generator — Skill Guidance for Gemini

This file is read by the client at startup and injected into Gemini's system prompt.
Its purpose is to give Gemini the domain knowledge it needs to use the tools in this 
module correctly and interpret their results meaningfully.

---

## What this module does

The `bua_generator` module manages the data collection and structured parsing phase for building a Biological Use Authorization (BUA).

---

## Available resources

| Resource name | Description |
|---------------|-------------|
| `common_biosafety_practices` | Located in /resources/common_biosafety_practices.docx. Standard practices for decontamination and PPE. |
| `empty_BUA` | Located in /resources/2025_09_17-BUA.pdf. The target template for population. |
| `lentivirus_ecp` | Located in /resources/lentivirus_exposure_control_plan_with_assessment_questionnaire_non_uhs.docx. Mandatory for HIV-based vectors. |
| `recombinant_dna_template` | Located in /resources/recombinant-nucleic-acid-template.docx. Mandatory for rDNA projects. |

---

## Tools and when to use them

### `get_initial_questions`
Retrieves foundational questions (Lab Identity, Scope, Materials). Use when starting a new BUA request.

### `get_questions`
Retrieves specialized modules:
- `section="recombinant"` — For gene editing/plasmids.
- `section="lentivirus"` — For HIV-based vectors.
- `section="safety"` — For final waste/PPE protocols based on common practices.

### `questionnaire_parsing`
Converts conversation into structured objects (LabIdentity, Strain). Use once the interview is complete to prepare data for form filling.

---

## Interpreting results

- **Triggering Branching:** If "Lentivirus" is mentioned in the initial material list, you must use `get_questions(section="lentivirus")`.
- **Safety Defaults:** Cross-reference `common_biosafety_practices` to provide the user with pre-filled suggestions for waste disposal.
- **Data Export:** Format the final summary into the JSON schema required by `questionnaire_parsing`.

---

## Questionnaire logic rules

- **One section at a time:** Group by Identity -> Scope -> Materials -> Specific Modules. Do not overwhelm the user.
- **Validation:** If `questionnaire_parsing` returns a status error, identify which field is missing (e.g., PI name or room number) and ask the user specifically for it.
import pytest
import json
from modules.biosafety.tools.bua_questionnaire import BUAQuestionnaire
from modules.biosafety.tools.questionnaire_parsing import questionnaire_parsing

# --- Tests for BUAQuestionnaire ---

def test_get_initial_questions():
    # BUAQuestionnaire uses __init__ and manual method calls in your uploaded version
    tool = BUAQuestionnaire()
    questions = tool.get_initial_questions()
    assert isinstance(questions, list)
    assert len(questions) > 0
    # Check for core sections: identity + scope + materials
    assert any("PI" in q for q in questions)
    assert any("biological agents" in q for q in questions)

def test_get_questions_sections():
    tool = BUAQuestionnaire()
    # Test valid section
    lenti_qs = tool.get_questions("lentivirus")
    assert any("plasmids" in q for q in lenti_qs)
    
    # Test invalid section
    invalid_qs = tool.get_questions("non_existent")
    assert invalid_qs == ["Section not found."]

# --- Tests for QuestionnaireParsing ---

def test_questionnaire_parsing_success():
    raw_data = {
        "lab_identity": {
            "pi_name": "John Doe",
            "pi_email": "johndoe@email.com",
            "department": "Bioengineering",
            "rooms": ["U234"],
            "personnel": [{"name": "Student A", "role": "Researcher", "responsibilities": "Lab work"}]
        },
        "strains": [
            {
                "scientific_name": "E. coli BL21",
                "source": "ATCC",
                "is_recombinant": True
            }
        ]
    }
    
    result = questionnaire_parsing(json.dumps(raw_data))
    
    assert result["status"] == "success"
    assert result["lab_identity"]["pi_name"] == "John Doe"
    assert result["strains"][0]["scientific_name"] == "E. coli BL21"
    assert result["strains"][0]["is_recombinant"] is True

def test_questionnaire_parsing_malformed_json():
    # Tool should return an error dict, not raise an unhandled exception
    result = questionnaire_parsing("{invalid json}")
    assert result["status"] == "error"
    assert "message" in result

def test_questionnaire_parsing_missing_keys():
    # Test with empty structure
    result = questionnaire_parsing("{}")
    assert result["status"] == "success"
    assert result["lab_identity"]["pi_name"] == ""
    assert result["strains"] == []
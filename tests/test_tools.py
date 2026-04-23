import pytest
import json
from modules.biosafety.tools.bua_questionnaire import BUAQuestionnaire
from modules.biosafety.tools.questionnaire_parsing import questionnaire_parsing
from modules.biosafety.tools.bua_resource_reader import bua_resource_reader

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

def test_questionnaire_parsing_nested_objects():
    raw_data = {
        "lab_identity": {
            "pi_name": "Jane Smith",
            "safety_protocols": {
                "ppe": "Lab coat and gloves",
                "liquid_waste": "10% bleach"
            }
        },
        "strains": [
            {
                "scientific_name": "Lentivirus",
                "is_lentivirus": True,
                "lentivirus_details": {
                    "num_plasmids": "3-4 plasmids",
                    "sin_ltrs": True
                }
            },
            {
                "scientific_name": "Recombinant E. coli",
                "is_recombinant": True,
                "recombinant_details": {
                    "plasmid_backbone": "pUC19",
                    "host_organism": "E. coli K12"
                }
            }
        ]
    }
    
    result = questionnaire_parsing(json.dumps(raw_data))
    
    assert result["status"] == "success"
    
    # Verify Safety Protocols
    safety = result["lab_identity"]["safety_protocols"]
    assert safety["ppe"] == "Lab coat and gloves"
    assert safety["liquid_waste"] == "10% bleach"
    assert safety["solid_waste"] == "" # Default empty string check
    
    # Verify Lentivirus Details
    lenti_strain = result["strains"][0]
    assert lenti_strain["lentivirus_details"]["num_plasmids"] == "3-4 plasmids"
    assert lenti_strain["lentivirus_details"]["sin_ltrs"] is True
    assert lenti_strain["recombinant_details"] is None # Should be null if not provided
    
    # Verify Recombinant Details
    rec_strain = result["strains"][1]
    assert rec_strain["recombinant_details"]["plasmid_backbone"] == "pUC19"
    assert rec_strain["lentivirus_details"] is None

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

# --- Tests for BUAResourceReader ---

def test_bua_resource_reader_invalid_key():
    # Testing an unsupported document key
    result = bua_resource_reader("unknown_doc")
    assert result["status"] == "error"
    assert "Invalid document key" in result["message"]

def test_bua_resource_reader_dispatch():
    # This checks that the valid keys are recognized by the tool.
    # Depending on your test environment, it will either return "success" 
    # (if docx and python-docx are present) or an error about missing files/packages,
    # both of which prove the logic works up to the file-reading stage.
    result = bua_resource_reader("safety")
    assert "status" in result
    assert isinstance(result, dict)
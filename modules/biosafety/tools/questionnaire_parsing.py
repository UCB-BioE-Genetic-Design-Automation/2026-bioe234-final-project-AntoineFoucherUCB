import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class Personnel:
    name: str
    role: str
    responsibilities: str = ""

@dataclass
class LabIdentity:
    pi_name: str
    pi_email: str
    department: str
    rooms: List[str] = field(default_factory=list)
    personnel: List[Personnel] = field(default_factory=list)

@dataclass
class Strain:
    scientific_name: str
    source: str
    is_recombinant: bool = False
    is_lentivirus: bool = False
    bsl_level: int = 1
    host_organism: Optional[str] = None
    transgenes: List[str] = field(default_factory=list)

class QuestionnaireParsing:
    """
    Description:
        Parses raw text or JSON responses from the BUA interview into 
        structured Python objects.
    """

    def initiate(self):
        pass

    def run(self, raw_answers: str) -> dict:
        try:
            data = json.loads(raw_answers)
            
            lab_data = data.get("lab_identity", {})
            personnel_list = [Personnel(**p) for p in lab_data.get("personnel", [])]
            lab_obj = LabIdentity(
                pi_name=lab_data.get("pi_name", ""),
                pi_email=lab_data.get("pi_email", ""),
                department=lab_data.get("department", ""),
                rooms=lab_data.get("rooms", []),
                personnel=personnel_list
            )

            strain_objs = [Strain(**s) for s in data.get("strains", [])]

            return {
                "status": "success",
                "lab_identity": asdict(lab_obj),
                "strains": [asdict(s) for s in strain_objs]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

_instance = QuestionnaireParsing()
_instance.initiate()
questionnaire_parsing = _instance.run
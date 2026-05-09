from pydantic import BaseModel, Field
from typing import List, Optional

# ==========================================
# FORM 1: PROJECT REGISTRATION & PI FORM
# ==========================================

class ContactInfo(BaseModel):
    """Used for PI, Co-investigator, and Lab Contact"""
    name: str = Field(default="", description="Full name")
    title: str = Field(default="", description="Job title")
    department: str = Field(default="", description="Department name")
    building: str = Field(default="", description="Building name")
    room: str = Field(default="", description="Room number")
    phone: str = Field(default="", description="Phone number")
    email_address: str = Field(default="", description="Email address")
    fax: str = Field(default="", description="Fax number")

class Personnel(BaseModel):
    """Form 1, Section 2: Laboratory Personnel"""
    name: str = Field(default="", description="Full name of the personnel")
    phone: str = Field(default="", description="Phone number")
    biosafety_training: bool = Field(default=False, description="Biosafety training received (yes/no)")
    bloodborne_pathogens_training: bool = Field(default=False, description="Bloodborne pathogens training received (yes/no)")
    medical_waste_training: bool = Field(default=False, description="Medical waste training received (yes/no)")

class RoomUsage(BaseModel):
    """Form 1, Section 3: Authorized lab locations/room usage"""
    building: str = Field(default="", description="Building name")
    room_number: str = Field(default="", description="Room number")
    shared_room: bool = Field(default=False, description="Is it a shared room? (yes/no)")
    biosafety_level: str = Field(default="", description="Biosafety level for each room (BL1, BL2, BL3)")
    storage: bool = Field(default=False, description="Used for storage (yes/no)")
    research: bool = Field(default=False, description="Used for research (yes/no)")
    biosafety_cabinet: bool = Field(default=False, description="Has a biosafety cabinet (yes/no)")
    autoclave: bool = Field(default=False, description="Has an autoclave (yes/no)")
    medical_waste: bool = Field(default=False, description="Handles medical waste (yes/no)")
    animal: bool = Field(default=False, description="Houses animals (yes/no)")

# ==========================================
# FORM 3B: INFECTIOUS AGENTS/TOXINS/PLANTS
# ==========================================

class AgentState(BaseModel):
    """Form 3B, Section 2: State of the culture maintained at the lab"""
    active: bool = Field(default=False, description="Maintained as active culture")
    desiccated: bool = Field(default=False, description="Maintained as desiccated")
    frozen: bool = Field(default=False, description="Maintained as frozen")
    other: str = Field(default="", description="Other state (specify)")

class BiologicalAgent(BaseModel):
    """Form 3B: Agents, Toxins, or USDA-regulated materials"""
    scientific_name: str = Field(default="", description="Scientific name of the biological agent")
    common_name: str = Field(default="", description="Common (disease) name")
    
    # Section 2 Info
    indigenous: bool = Field(default=False, description="Is the agent indigenous to the region/state?")
    agent_state: Optional[AgentState] = Field(default_factory=AgentState, description="Physical state of the agent if maintained at the lab")
    aphis_permit_obtained: bool = Field(default=False, description="APHIS permit obtained (if non-indigenous)")
    
    # Section 3 Info
    laboratory_location: str = Field(default="", description="Laboratory location for use")
    greenhouse_location: str = Field(default="", description="Greenhouse location for use")
    growth_chamber_location: str = Field(default="", description="Growth chamber/incubator location for use")
    field_release_location: str = Field(default="", description="Field release location")
    cdc_select_agent: bool = Field(default=False, description="Is it a CDC select agent or toxin?")
    # Optional external cross-reference fields (ABSA tool).
    absa_risk_group: str = Field(default="", description="ABSA-referenced risk group, if available")
    absa_reference: str = Field(default="", description="ABSA source URL or citation")
    cross_reference_notes: str = Field(default="", description="Short notes from ABSA source cross-reference")

# ==========================================
# FORM 4: PROJECT SUMMARY
# ==========================================

class ProjectSummary(BaseModel):
    """Form 4: Project Summary details"""
    project_goal: str = Field(default="", description="Project goal/purpose")
    experimental_procedure: str = Field(default="", description="Experimental procedure")
    containment: str = Field(default="", description="Containment to be used (including BSC)")
    protective_equipment: str = Field(default="", description="Protective equipment to be used (including lab coat, glasses, goggles, glove types)")
    transportation_methods: str = Field(default="", description="Transportation methods (if applicable)")
    decontamination_methods: str = Field(default="", description="Decontamination methods")
    waste_disposal: str = Field(default="", description="Waste disposal")
    spill_emergency_procedures: str = Field(default="", description="Spill/emergency procedures")

# ==========================================
# MASTER STATE MODEL
# ==========================================

class BUAForm(BaseModel):
    """The master state holding all form data"""
    
    # Basic identifiers
    university: str = Field(default="", description="The university where the BUA is being submitted")
    state: str = Field(default="", description="The US State where the university is located")
    bua_number: str = Field(default="", description="BUA Number (Office use only)")
    project_title: str = Field(default="", description="Project title")
    
    # Contact Information
    pi_info: Optional[ContactInfo] = Field(default_factory=ContactInfo)
    co_investigator_info: Optional[ContactInfo] = Field(default_factory=ContactInfo)
    lab_contact_info: Optional[ContactInfo] = Field(default_factory=ContactInfo)
    
    # Form 1 nested structures
    personnel: List[Personnel] = Field(default_factory=list)
    room_usage: List[RoomUsage] = Field(default_factory=list)
    irb_approval_sought: bool = Field(default=False, description="Is IRB approval being sought? (yes/no)")
    iacuc_approval_sought: bool = Field(default=False, description="Is IACUC approval being sought? (yes/no)")
    
    # Form 3B & Form 4
    biological_agents: List[BiologicalAgent] = Field(default_factory=list)
    project_summary: Optional[ProjectSummary] = Field(default_factory=ProjectSummary)


def _merge_contact_fields_symmetric(left: ContactInfo, right: ContactInfo) -> ContactInfo:
    out: dict[str, str] = {}
    for fname in ContactInfo.model_fields:
        va = str(getattr(left, fname, "") or "").strip()
        vb = str(getattr(right, fname, "") or "").strip()
        if va and vb:
            out[fname] = va if len(va) >= len(vb) else vb
        else:
            out[fname] = va or vb
    return ContactInfo(**out)


def sync_pi_and_lab_contacts_inplace(form: BUAForm) -> None:
    """
    Recover from common LLM layout mistakes — without assuming PI ≡ lab contact for every BUA.

    - If PI is blank but Lab Contact has a name, promote lab → PI (models often stash PI-only
      answers under lab_contact_info).
    - If both rows name the same person, merge non-empty fields both ways so details split across
      stages still fill the form (explicit “I am PI and lab contact” flow).
    - If Lab Contact is blank but PI is filled: do nothing here — the lab slot may belong to a
      different person to be captured later (do not duplicate PI onto lab automatically).
    """
    pi = form.pi_info or ContactInfo()
    lab = form.lab_contact_info or ContactInfo()

    pi_n = (pi.name or "").strip().lower()
    lab_n = (lab.name or "").strip().lower()

    if not pi_n and lab_n:
        form.pi_info = lab.model_copy(deep=True)
        return

    if pi_n and lab_n:
        same = pi_n == lab_n or pi_n in lab_n or lab_n in pi_n
        if same:
            merged = _merge_contact_fields_symmetric(pi, lab)
            form.pi_info = merged.model_copy(deep=True)
            form.lab_contact_info = merged.model_copy(deep=True)


# This is the global state object that will hold the data while the server runs
current_bua_state = BUAForm()

# Raw (truncated) excerpt of the user-provided document, filled by `doc_parsing`.
# MCP tools can read this to tailor prompts/questions to the specific file.
current_document_markdown: str = ""

# Optional: store the last parsed file name/path for traceability/debugging.
current_document_source: str = ""
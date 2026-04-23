from pydantic import BaseModel, Field
from typing import List, Optional

class Personnel(BaseModel):
    name: str = Field(description="Full name of the personnel")
    role: str = Field(description="Role in the lab (e.g., PI, Postdoc, Student)")
    training_completed: bool = Field(default=False)

class Strain(BaseModel):
    scientific_name: str = Field(description="Scientific name of the organism")
    risk_group: int = Field(ge=1, le=4, description="Biosafety Risk Group as an integer (1-4)")
    is_viral_vector: bool = Field(default=False)

class LabIdentity(BaseModel):
    pi_name: str = Field(default="", description="Principal Investigator Name")
    department: str = Field(default="", description="University or Institute Department")
    rooms: List[str] = Field(default_factory=list, description="List of room numbers")

class BUAForm(BaseModel):
    lab_identity: Optional[LabIdentity] = None
    strains: List[Strain] = Field(default_factory=list)
    personnel: List[Personnel] = Field(default_factory=list)

# This is the global state object that will hold the data while the server runs
current_bua_state = BUAForm()
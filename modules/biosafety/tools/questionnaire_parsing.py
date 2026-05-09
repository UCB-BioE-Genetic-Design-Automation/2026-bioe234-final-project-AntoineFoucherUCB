import json
from pathlib import Path

from modules.biosafety.data.BUA_data_structure import (
    BUAForm,
    BiologicalAgent,
    ContactInfo,
    Personnel,
    ProjectSummary,
    RoomUsage,
    current_bua_state,
    sync_pi_and_lab_contacts_inplace,
)
import modules.biosafety.data.BUA_data_structure as bua_ds

from modules.biosafety.tools.questionnaire_prompts import _normalize_stage


def _state_file() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "bua_state_snapshot.json"


def _copy_state(src: BUAForm) -> None:
    current_bua_state.university = src.university
    current_bua_state.state = src.state
    current_bua_state.bua_number = src.bua_number
    current_bua_state.project_title = src.project_title
    current_bua_state.pi_info = src.pi_info
    current_bua_state.co_investigator_info = src.co_investigator_info
    current_bua_state.lab_contact_info = src.lab_contact_info
    current_bua_state.personnel = src.personnel
    current_bua_state.room_usage = src.room_usage
    current_bua_state.irb_approval_sought = src.irb_approval_sought
    current_bua_state.iacuc_approval_sought = src.iacuc_approval_sought
    current_bua_state.biological_agents = src.biological_agents
    current_bua_state.project_summary = src.project_summary


def _load_state_from_disk() -> None:
    p = _state_file()
    if not p.exists():
        return
    try:
        saved = BUAForm(**json.loads(p.read_text(encoding="utf-8")))
        _copy_state(saved)
    except Exception:
        pass


def _save_state_to_disk() -> None:
    p = _state_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(current_bua_state.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _reset_state() -> None:
    _copy_state(BUAForm())
    try:
        _state_file().unlink(missing_ok=True)
    except Exception:
        pass


def _as_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v or "").strip().lower()
    return s in {"1", "true", "yes", "y", "checked", "complete", "completed"}


def _registration_from_data(data: dict) -> tuple[str, str, str, str]:
    uni = str(data.get("university", "") or data.get("university_name", "") or "").strip()
    state_ = str(data.get("state", "") or "").strip()
    bua = str(data.get("bua_number", "") or "").strip()
    title_raw = str(data.get("project_title", "") or "").strip()
    return uni, state_, bua, title_raw


def _maybe_patch_registration_fields(data: dict) -> None:
    """Update header fields only for keys explicitly present—avoids wiping state on PI-only saves."""
    if not any(k in data for k in ("university", "university_name", "state", "bua_number", "project_title")):
        return
    uni, state_, bua, title_raw = _registration_from_data(data)
    if any(k in data for k in ("university", "university_name")):
        current_bua_state.university = uni
    if "state" in data:
        current_bua_state.state = state_
    if "bua_number" in data:
        current_bua_state.bua_number = bua
    if "project_title" in data:
        current_bua_state.project_title = title_raw


def _merge_contact_pick_nonempty(existing: ContactInfo | None, incoming: ContactInfo) -> ContactInfo:
    """Per-field incoming value wins when non-empty; otherwise keep existing (avoids LLM wiping prior rows)."""
    ex = existing or ContactInfo()
    d: dict[str, str] = {}
    for fname in ContactInfo.model_fields:
        vi = str(getattr(incoming, fname, "") or "").strip()
        ve = str(getattr(ex, fname, "") or "").strip()
        d[fname] = vi if vi else ve
    return ContactInfo(**d)


def _coerce_pi_contact_only(data: dict) -> ContactInfo:
    """Merge pi_info nested object with common flat aliases (PI-only; no university row)."""
    pi_raw = dict(data.get("pi_info") or {})
    merge = {
        "name": pi_raw.get("name", "") or data.get("PI_name", "") or data.get("pi_name", "") or "",
        "title": pi_raw.get("title", "") or data.get("PI_title", "") or data.get("pi_title", "") or "",
        "department": pi_raw.get("department", "") or data.get("department", "") or "",
        "building": pi_raw.get("building", "") or data.get("building", "") or "",
        "room": pi_raw.get("room", "") or data.get("room", "") or "",
        "phone": pi_raw.get("phone", "") or data.get("phone", "") or data.get("phone_number", "") or "",
        "email_address": pi_raw.get("email_address", "")
        or data.get("email_address", "")
        or data.get("email", ""),
        "fax": str(pi_raw.get("fax", "") or data.get("fax", "") or ""),
    }
    return ContactInfo(**merge)


def _coerce_personnel_item(p: dict) -> Personnel:
    trainings = p.get("training_completed", []) or []
    if not isinstance(trainings, list):
        trainings = [trainings]
    trainings_l = [str(t).strip().lower() for t in trainings]
    merged = dict(p or {})
    return Personnel(
        name=str(merged.get("name", "")),
        phone=str(merged.get("phone", merged.get("phone_number", "") or "")),
        biosafety_training=_as_bool(merged.get("biosafety_training"))
        or any("biosafety" in t for t in trainings_l),
        bloodborne_pathogens_training=_as_bool(merged.get("bloodborne_pathogens_training"))
        or any("bloodborne" in t for t in trainings_l),
        medical_waste_training=_as_bool(merged.get("medical_waste_training"))
        or any("medical waste" in t for t in trainings_l),
    )


def _coerce_room_item(r: dict) -> RoomUsage:
    activities = [str(a).strip().lower() for a in (r.get("activities") or [])]
    equipment = [str(e).strip().lower() for e in (r.get("equipment") or [])]
    bsl_raw = r.get("biosafety_level", r.get("bsl_level", ""))
    bsl = str(bsl_raw or "").strip()
    if bsl in {"1", "2", "3"}:
        bsl = f"BL{bsl}"
    if bsl and not str(bsl).upper().startswith("BL"):
        bsl_upper = str(bsl).strip().upper()
        if "BL" in bsl_upper or str(bsl).isdigit():
            bsl = bsl.upper() if bsl.upper().startswith("BL") else bsl

    return RoomUsage(
        building=str(r.get("building", "") or ""),
        room_number=str(r.get("room_number", "") or r.get("room", "") or ""),
        shared_room=_as_bool(r.get("shared_room", r.get("shared"))),
        biosafety_level=bsl,
        storage=_as_bool(r.get("storage")) or ("storage" in activities),
        research=_as_bool(r.get("research"))
        or any("research" in a for a in activities)
        or any("grow" in a for a in activities),
        biosafety_cabinet=_as_bool(r.get("biosafety_cabinet"))
        or any("biosafety cabinet" in e or e == "bsc" or "cabinet" in e for e in equipment),
        autoclave=_as_bool(r.get("autoclave")) or ("autoclave" in equipment),
        medical_waste=_as_bool(r.get("medical_waste", r.get("medical_waste_handling"))),
        animal=_as_bool(r.get("animal", r.get("animal_housing"))),
    )


def _coerce_agent_item(a: dict) -> BiologicalAgent:
    merged = dict(a or {})
    for key in ("laboratory_location", "greenhouse_location", "growth_chamber_location", "field_release_location"):
        val = merged.get(key)
        if isinstance(val, bool):
            merged[key] = "Yes" if val else ""

    ast = merged.get("agent_state")
    if ast is None:
        merged["agent_state"] = {}
    elif isinstance(ast, dict):
        pass
    return BiologicalAgent(**merged)


def _coerce_project_summary(data: dict) -> ProjectSummary:
    return ProjectSummary(
        project_goal=str(data.get("project_goal", "") or ""),
        experimental_procedure=str(data.get("experimental_procedure", "") or ""),
        containment=str(data.get("containment", "") or ""),
        protective_equipment=str(data.get("protective_equipment", "") or data.get("ppe", "") or ""),
        transportation_methods=str(
            data.get("transportation_methods", "") or data.get("transport", "") or ""
        ),
        decontamination_methods=str(
            data.get("decontamination_methods", "") or data.get("decontamination", "") or ""
        ),
        waste_disposal=str(data.get("waste_disposal", "") or ""),
        spill_emergency_procedures=str(
            data.get("spill_emergency_procedures", "") or data.get("spill_response", "") or ""
        ),
    )


class QuestionnaireParsing:
    def initiate(self):
        # Preserve state across MCP reconnects in Streamlit by reloading snapshot if present.
        if _state_file().exists():
            _load_state_from_disk()
        else:
            _reset_state()
        # Also reset any stored uploaded-document context used for tailored questioning.
        bua_ds.current_document_markdown = ""
        bua_ds.current_document_source = ""

    def run(self, stage: str, raw_data: str) -> dict:
        try:
            _load_state_from_disk()
            data = json.loads(raw_data)
            next_stage = "complete"

            if stage == "project_info":
                current_bua_state.university = data.get("university", "")
                current_bua_state.state = data.get("state", "")
                current_bua_state.bua_number = data.get("bua_number", "")
                current_bua_state.project_title = data.get("project_title", "")
                next_stage = "pi_info"

            elif stage == "pi_info":
                if data.get("pi_info"):
                    current_bua_state.pi_info = ContactInfo(**data["pi_info"])
                next_stage = "additional_contacts"

            elif stage == "additional_contacts":
                if "co_investigator_info" in data:
                    inc_ci = ContactInfo(**(data.get("co_investigator_info") or {}))
                    current_bua_state.co_investigator_info = _merge_contact_pick_nonempty(
                        current_bua_state.co_investigator_info, inc_ci
                    )
                if "lab_contact_info" in data:
                    inc_lc = ContactInfo(**(data.get("lab_contact_info") or {}))
                    current_bua_state.lab_contact_info = _merge_contact_pick_nonempty(
                        current_bua_state.lab_contact_info, inc_lc
                    )
                next_stage = "personnel"
            
            elif stage == "personnel":
                # Handle if LLM passes it wrapped in a "personnel" key or directly as a list
                pers_list = data.get("personnel", data) if isinstance(data, dict) else data
                if isinstance(pers_list, list):
                    current_bua_state.personnel = [_coerce_personnel_item(p or {}) for p in pers_list]
                next_stage = "room_usage"

            elif stage == "room_usage":
                current_bua_state.irb_approval_sought = data.get("irb_approval_sought", False)
                current_bua_state.iacuc_approval_sought = data.get("iacuc_approval_sought", False)
                rooms_list = data.get("room_usage", [])
                if isinstance(rooms_list, list):
                    current_bua_state.room_usage = [_coerce_room_item(r or {}) for r in rooms_list]
                next_stage = "biological_agents"

            elif stage == "biological_agents":
                agents_list = data.get("biological_agents", [])
                if isinstance(agents_list, list):
                    current_bua_state.biological_agents = [_coerce_agent_item(a or {}) for a in agents_list]
                next_stage = "project_summary"

            elif stage == "project_summary":
                summary_data = data.get("project_summary", data)
                if isinstance(summary_data, dict) and summary_data:
                    current_bua_state.project_summary = _coerce_project_summary(summary_data)
                next_stage = "complete"

            else:
                return {"status": "error", "message": f"Unknown stage: {stage}"}

            sync_pi_and_lab_contacts_inplace(current_bua_state)
            _save_state_to_disk()
            return {
                "status": "success",
                "message": f"Data successfully validated and saved for {stage}.",
                "next_stage_to_fetch": next_stage,
                "current_state": current_bua_state.model_dump(),
            }

        except json.JSONDecodeError:
            return {"status": "error", "message": "Failed to parse JSON. Ensure you are sending a valid JSON string."}
        except Exception as e:
            return {"status": "error", "message": f"Validation failed: {str(e)}. Please correct the JSON and try again."}

# Standard C9 instantiation and export
_instance = QuestionnaireParsing()
_instance.initiate()
questionnaire_parsing = _instance.run
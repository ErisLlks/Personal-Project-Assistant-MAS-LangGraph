import os
import datetime
from state.schema import MASARPSState

VALID_SOURCES = {"local", "drive", "web", "academic"}

def source_select_node(state: MASARPSState) -> dict:
    selected = set(state.get("sources_selected", []))
    now = datetime.datetime.utcnow().isoformat()

    # Validate at least one source selected
    if not selected:
        raise ValueError("FR-2 violation: no sources selected")

    # Validate all sources are recognised
    invalid = selected - VALID_SOURCES
    if invalid:
        raise ValueError(f"FR-2 violation: unknown sources: {invalid}")

    # Validate local path if local selected
    if "local" in selected:
        local_path = state.get("local_path")
        if not local_path or not os.path.isdir(local_path):
            raise ValueError(f"FR-2 violation: local_path '{local_path}' not found")
        if not os.access(local_path, os.R_OK):
            raise ValueError(f"NFR-4 violation: local_path is not readable")

    # Validate Drive folder ID if drive selected
    if "drive" in selected:
        if not state.get("drive_folder_id"):
            raise ValueError("FR-2 violation: drive selected but drive_folder_id is missing")

    print(f"[SourceSelect] Sources configured: {selected}")

    log_entry = {
        "timestamp": now,
        "node":      "source_select",
        "action":    "sources_configured",
        "detail":    str(selected)
    }

    return {
        "session_log": [*state.get("session_log", []), log_entry]
    }
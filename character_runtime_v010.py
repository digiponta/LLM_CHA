"""Character selection UI for LLM_CHA v0.1.0.

Character profiles are presentation metadata, never semantic evidence.
"""
from __future__ import annotations

from pathlib import Path

from character_profile_v010 import CharacterProfile, load_profile

def profile_path(directory: str | Path, identifier: str) -> Path:
    # Enforce the same identifier validation as the profile schema.
    CharacterProfile(identifier, "validation")
    return Path(directory) / (identifier + ".json")

def available_profiles(directory: str | Path) -> list[str]:
    root = Path(directory)
    if not root.is_dir():
        return []
    result = []
    for path in sorted(root.glob("*.json")):
        try:
            profile = load_profile(path)
            if profile_path(root, profile.profile_id).resolve() == path.resolve():
                result.append(profile.profile_id)
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return result

def select_profile(directory: str | Path, identifier: str) -> CharacterProfile:
    path = profile_path(directory, identifier)
    profile = load_profile(path)
    if profile.profile_id != identifier:
        raise ValueError("profile ID does not match filename")
    return profile

def speaker(profile: CharacterProfile | None) -> str:
    # Never allow multiline terminal label injection from metadata.
    if profile is None:
        return "AI"
    label = " ".join(profile.display_name.split())
    return label[:40] or "AI"

def character_command(command: str, directory: str | Path,
                      active: CharacterProfile | None
                      ) -> tuple[bool, CharacterProfile | None, str]:
    """Interpret /character commands without changing model or semantic state."""
    parts = command.strip().split()
    if not parts or parts[0].lower() != "/character":
        return False, active, ""
    if len(parts) == 1 or (len(parts) == 2 and parts[1].lower() == "show"):
        if active is None:
            return True, active, "[character: off]"
        return True, active, (
            f"[character: {active.profile_id} ({speaker(active)})] "
            f"persona={active.persona!r} style={active.speaking_style!r}"
        )
    if len(parts) == 2 and parts[1].lower() == "list":
        profiles = available_profiles(directory)
        return True, active, "[characters: " + (", ".join(profiles) if profiles else "none") + "]"
    if len(parts) == 2 and parts[1].lower() == "off":
        return True, None, "[character: off]"
    if len(parts) == 3 and parts[1].lower() == "select":
        try:
            selected = select_profile(directory, parts[2])
        except (OSError, ValueError, TypeError, KeyError) as error:
            return True, active, f"[character selection failed: {error}]"
        return True, selected, f"[character selected: {selected.profile_id} ({speaker(selected)})]"
    return True, active, "[usage: /character list|select ID|show|off]"

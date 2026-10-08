"""LLM_CHA v0.1.0 character profile storage.

Profiles are optional metadata. They do not replace semantic facts or bypass
truth/unknown/approval gates in the existing chat runtime.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re


_PROFILE_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
_MAX_TEXT = 2000


@dataclass(frozen=True)
class CharacterProfile:
    profile_id: str
    display_name: str
    persona: str = ""
    speaking_style: str = ""

    def __post_init__(self) -> None:
        if not _PROFILE_ID.fullmatch(self.profile_id):
            raise ValueError("profile_id must be 1-64 ASCII letters, digits, '_' or '-'")
        for name in ("display_name", "persona", "speaking_style"):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) > _MAX_TEXT:
                raise ValueError(f"{name} must be text of at most {_MAX_TEXT} characters")
        if not self.display_name.strip():
            raise ValueError("display_name must not be empty")


def save_profile(path: str | Path, profile: CharacterProfile) -> None:
    """Save an explicitly approved profile; never train a model implicitly."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_text(
        json.dumps(asdict(profile), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)


def load_profile(path: str | Path) -> CharacterProfile:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("profile JSON must be an object")
    expected = {"profile_id", "display_name", "persona", "speaking_style"}
    if set(payload) != expected:
        raise ValueError("profile JSON has missing or unknown fields")
    return CharacterProfile(**payload)


def describe_profile(profile: CharacterProfile) -> str:
    """Return style metadata; callers must keep knowledge and safety gates active."""
    return (
        f"Name: {profile.display_name}\n"
        f"Persona: {profile.persona}\n"
        f"Speaking style: {profile.speaking_style}"
    )

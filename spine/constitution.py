from pathlib import Path


_DEFAULT_CONSTITUTION = "# CONSTITUTION\nYou are Talos, an autonomous agent. Act with agency and continuity."
_DEFAULT_IDENTITY = "# Identity\nYou are Talos."


def load_system_prompt(constitution_path: str, identity_path: str) -> str:
    if Path(constitution_path).exists():
        constitution = Path(constitution_path).read_text()
    else:
        constitution = _DEFAULT_CONSTITUTION
    if Path(identity_path).exists():
        identity = Path(identity_path).read_text()
    else:
        identity = _DEFAULT_IDENTITY
    return f"{identity}\n\n{constitution}"

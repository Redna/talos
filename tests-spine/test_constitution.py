from spine.constitution import load_system_prompt


def test_load_system_prompt_concatenates_both_files(tmp_path):
    constitution = tmp_path / "CONSTITUTION.md"
    identity = tmp_path / "identity.md"
    constitution.write_text("# Principles\nAgency and continuity.")
    identity.write_text("# Identity\nYou are Talos.")
    result = load_system_prompt(str(constitution), str(identity))
    assert "Agency and continuity." in result
    assert "You are Talos." in result
    assert (
        result == "# Identity\nYou are Talos.\n\n# Principles\nAgency and continuity."
    )


def test_load_system_prompt_returns_default_when_files_missing(tmp_path):
    constitution = tmp_path / "nonexistent_constitution.md"
    identity = tmp_path / "nonexistent_identity.md"
    result = load_system_prompt(str(constitution), str(identity))
    assert "Talos" in result

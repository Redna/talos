from spine.constitution import ConstitutionManager


def test_load_reads_both_files(tmp_path):
    constitution = tmp_path / "CONSTITUTION.md"
    identity = tmp_path / "identity.md"
    constitution.write_text("# Principles\nAgency and continuity.")
    identity.write_text("# Identity\nYou are Talos.")
    cm = ConstitutionManager(str(constitution), str(identity))
    cm.load()
    assert "Agency" in cm.system_prompt()
    assert "Talos" in cm.system_prompt()


def test_load_rejects_empty_constitution(tmp_path):
    constitution = tmp_path / "CONSTITUTION.md"
    identity = tmp_path / "identity.md"
    constitution.write_text("")
    identity.write_text("You are Talos.")
    cm = ConstitutionManager(str(constitution), str(identity))
    raised = False
    try:
        cm.load()
    except ValueError as e:
        raised = True
        assert "empty" in str(e).lower()
    assert raised


def test_has_changed_detects_modification(tmp_path):
    constitution = tmp_path / "CONSTITUTION.md"
    identity = tmp_path / "identity.md"
    constitution.write_text("# Original")
    identity.write_text("# Identity")
    cm = ConstitutionManager(str(constitution), str(identity))
    cm.load()
    assert cm.has_changed() is False
    constitution.write_text("# Modified")
    assert cm.has_changed() is True


def test_reload_if_changed(tmp_path):
    constitution = tmp_path / "CONSTITUTION.md"
    identity = tmp_path / "identity.md"
    constitution.write_text("# Original")
    identity.write_text("# Identity")
    cm = ConstitutionManager(str(constitution), str(identity))
    cm.load()
    changed, err = cm.reload_if_changed()
    assert changed is False
    assert err is None
    constitution.write_text("# Modified")
    changed, err = cm.reload_if_changed()
    assert changed is True
    assert err is None

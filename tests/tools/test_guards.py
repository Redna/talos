import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cortex"))

from tools.guards import (
    is_spine_write,
    is_spine_path,
    BLOCKED_FLAGS,
    PROTECTED_BRANCHES,
)


class TestIsSpinePath:
    def test_spine_path(self):
        assert is_spine_path("/app/spine/config.py")

    def test_non_spine_path(self):
        assert not is_spine_path("/app/cortex/seed_agent.py")

    def test_memory_path(self):
        assert not is_spine_path("/memory/notes.md")


class TestIsSpineWrite:
    def test_redirect_write(self):
        assert is_spine_write("echo data > /app/spine/config.json")

    def test_append_write(self):
        assert is_spine_write("echo data >> /app/spine/log.txt")

    def test_tee_write(self):
        assert is_spine_write("echo data | tee /app/spine/output.txt")

    def test_cp_write(self):
        assert is_spine_write("cp file.txt /app/spine/file.txt")

    def test_mv_write(self):
        assert is_spine_write("mv file.txt /app/spine/file.txt")

    def test_python_write(self):
        assert is_spine_write(
            "python3 -c \"open('/app/spine/config.py','w').write('hacked')\""
        )

    def test_sed_i(self):
        assert is_spine_write("sed -i 's/old/new/' /app/spine/config.py")

    def test_read_command_allowed(self):
        assert not is_spine_write("cat /app/spine/config.json")

    def test_non_spine_write_allowed(self):
        assert not is_spine_write("echo data > /tmp/output.txt")

    def test_grep_allowed(self):
        assert not is_spine_write("grep pattern /app/spine/stream.py")

    def test_dd_write(self):
        assert is_spine_write("dd of=/app/spine/config.json")

    def test_install_write(self):
        assert is_spine_write("install -m 644 file.conf /app/spine/file.conf")


class TestBlockedFlags:
    def test_no_verify_blocked(self):
        assert "--no-verify" in BLOCKED_FLAGS

    def test_no_gpg_sign_blocked(self):
        assert "--no-gpg-sign" in BLOCKED_FLAGS


class TestProtectedBranches:
    def test_main_protected(self):
        assert "main" in PROTECTED_BRANCHES

    def test_master_protected(self):
        assert "master" in PROTECTED_BRANCHES

import pytest
from unittest.mock import patch, MagicMock

from textfsmgen.libs.asyncshell import execute_command_async, CommandResult


def make_async_proc(stdout=b"", stderr=b"", returncode=0):
    """Create a fake asyncio subprocess with async communicate()."""
    proc = MagicMock()
    proc.returncode = returncode

    async def _communicate():
        return stdout, stderr

    proc.communicate = _communicate
    return proc


@pytest.mark.asyncio
async def test_async_success():
    with patch("asyncio.create_subprocess_shell") as mock_ps:
        mock_ps.return_value = make_async_proc(b"ok", b"", 0)

        result = await execute_command_async("echo hi")

        assert isinstance(result, CommandResult)
        assert result.is_success
        assert result.output == "ok"


@pytest.mark.asyncio
async def test_async_stderr_included():
    with patch("asyncio.create_subprocess_shell") as mock_ps:
        mock_ps.return_value = make_async_proc(b"", b"err", 1)

        result = await execute_command_async("badcmd")

        assert not result.is_success
        assert result.output == "err"


@pytest.mark.asyncio
async def test_async_combined_output():
    with patch("asyncio.create_subprocess_shell") as mock_ps:
        mock_ps.return_value = make_async_proc(b"out", b"err", 0)

        result = await execute_command_async("cmd")

        assert result.is_success
        assert result.output == "outerr"


@pytest.mark.asyncio
async def test_async_subprocess_creation_failure():
    with patch("asyncio.create_subprocess_shell") as mock_ps:
        mock_ps.side_effect = OSError("cannot spawn")

        with pytest.raises(OSError):
            await execute_command_async("cmd")

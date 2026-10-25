"""Tests for secure .env generation used by the Docker quick-start script."""

import os
import pty
import select
import stat
import subprocess
import textwrap
import time
from pathlib import Path

import pytest
from dotenv import dotenv_values

import scripts.generate_admin_credentials as credential_generator
from scripts.generate_admin_credentials import ADMIN_KEYS, _env_assignment, write_admin_values


def test_generated_credentials_are_upserted_and_env_file_is_private(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "NVIDIA_API_KEY=nvapi-example\n"
        "ADMIN_USERNAME=\n"
        "ADMIN_PASSWORD_HASH=\n"
        "ADMIN_TOTP_SECRET=old-secret\n"
        "ADMIN_SESSION_SECRET=\n"
        "ADMIN_SESSION_TTL_MINUTES=30\n"
        "ADMIN_USERNAME=duplicate\n",
        encoding="utf-8",
    )
    values = {
        "ADMIN_USERNAME": "parlez-admin",
        "ADMIN_PASSWORD_HASH": "$2b$12$abcdefghijklmnopqrstuv0123456789ABCDEFGHIJKLMNOPQRSTUV",
        "ADMIN_SESSION_SECRET": "session_secret-with-safe-characters_123456789",
    }

    result = write_admin_values(env_file, values)

    parsed = dotenv_values(result)
    assert {key: parsed[key] for key in ADMIN_KEYS} == values
    assert parsed["NVIDIA_API_KEY"] == "nvapi-example"
    assert parsed["ADMIN_SESSION_TTL_MINUTES"] == "30"
    assert parsed["ADMIN_USERNAME"] == "parlez-admin"
    assert "ADMIN_TOTP_SECRET" not in parsed
    assert result.read_text(encoding="utf-8").count("ADMIN_USERNAME=") == 1
    assert "ADMIN_PASSWORD_HASH='$2b$12$" in result.read_text(encoding="utf-8")
    assert stat.S_IMODE(result.stat().st_mode) == 0o600


def test_bcrypt_value_is_single_quoted_for_compose_env_files():
    assert _env_assignment("ADMIN_PASSWORD_HASH", "$2b$12$hash") == "ADMIN_PASSWORD_HASH='$2b$12$hash'"
    assert _env_assignment("ADMIN_USERNAME", "parlez-admin") == "ADMIN_USERNAME=parlez-admin"


def test_password_setup_reprompts_after_invalid_or_unconfirmed_passwords(monkeypatch, capsys):
    username_inputs = iter(["sajjan"])
    password_inputs = iter([
        "too-short",
        "é" * 37,  # Valid character count, but more than bcrypt's 72-byte limit.
        "correct-password-123",
        "wrong-confirmation",
        "correct-horse-battery",
        "correct-horse-battery",
    ])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(username_inputs))
    monkeypatch.setattr(credential_generator.getpass, "getpass", lambda _prompt: next(password_inputs))
    real_gensalt = credential_generator.bcrypt.gensalt
    monkeypatch.setattr(credential_generator.bcrypt, "gensalt", lambda rounds: real_gensalt(rounds=4))

    values = credential_generator._generate_values()

    assert values["ADMIN_USERNAME"] == "sajjan"
    assert set(values) == set(ADMIN_KEYS)
    assert len(values["ADMIN_SESSION_SECRET"]) >= 32
    assert credential_generator.bcrypt.checkpw(
        b"correct-horse-battery", values["ADMIN_PASSWORD_HASH"].encode("ascii")
    )
    errors = capsys.readouterr().err
    assert "at least 16 characters" in errors
    assert "at most 72 UTF-8 bytes" in errors
    assert "Passwords did not match" in errors


def test_write_admin_values_rejects_partial_or_unknown_value_sets(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("NVIDIA_API_KEY=nvapi-example\n", encoding="utf-8")
    with pytest.raises(ValueError):
        write_admin_values(env_file, {"ADMIN_USERNAME": "parlez-admin"})


def test_run_sh_reports_credential_setup_failure_without_starting_app(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    run_script = Path(__file__).resolve().parents[1] / "run.sh"
    (repo / "run.sh").write_text(run_script.read_text(encoding="utf-8"), encoding="utf-8")
    (repo / ".env.example").write_text(
        "NVIDIA_API_KEY=nvapi-test-key\n"
        "ADMIN_USERNAME=\n"
        "ADMIN_PASSWORD_HASH=\n"
        "ADMIN_SESSION_SECRET=\n",
        encoding="utf-8",
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail
            if [[ "$1" == "compose" ]]; then shift; fi
            if [[ "${1:-}" == "version" ]]; then exit 0; fi
            printf '%s\\n' "$*" >> "$FAKE_DOCKER_LOG"
            case "${1:-}" in
              build) exit 0 ;;
              run) exit 17 ;;
              up) exit 0 ;;
              *) exit 99 ;;
            esac
            """
        ),
        encoding="utf-8",
    )
    fake_docker.chmod(0o755)

    master_fd, slave_fd = pty.openpty()
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["FAKE_DOCKER_LOG"] = str(tmp_path / "docker.log")
    process = subprocess.Popen(
        ["bash", str(repo / "run.sh")],
        cwd=repo,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=env,
        close_fds=True,
    )
    os.close(slave_fd)
    output = bytearray()
    deadline = time.monotonic() + 20
    while process.poll() is None and time.monotonic() < deadline:
        ready, _, _ = select.select([master_fd], [], [], 0.2)
        if ready:
            try:
                output.extend(os.read(master_fd, 4096))
            except OSError:
                break
    if process.poll() is None:
        process.kill()
        process.wait()
        os.close(master_fd)
        pytest.fail("run.sh did not finish within 20 seconds")
    try:
        while True:
            ready, _, _ = select.select([master_fd], [], [], 0)
            if not ready:
                break
            output.extend(os.read(master_fd, 4096))
    except OSError:
        pass
    finally:
        os.close(master_fd)

    text = output.decode("utf-8", errors="replace")
    assert process.returncode != 0
    assert "Admin credential setup did not complete" in text
    assert "Parlez was not started" in text
    log = (tmp_path / "docker.log").read_text(encoding="utf-8").splitlines()
    assert log[0] == "build chatbot"
    assert log[1].startswith("run --rm --no-deps --user ")
    assert "python /app/scripts/generate_admin_credentials.py --env-file /workspace/.env" in log[1]
    assert "up -d" not in log


def test_run_sh_builds_then_runs_generator_to_populate_new_env(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    run_script = Path(__file__).resolve().parents[1] / "run.sh"
    (repo / "run.sh").write_text(run_script.read_text(encoding="utf-8"), encoding="utf-8")
    (repo / ".env.example").write_text(
        "NVIDIA_API_KEY=nvapi-test-key\n"
        "NVIDIA_MODEL=nvidia/test-model\n"
        "ADMIN_USERNAME=\n"
        "ADMIN_PASSWORD_HASH=\n"
        "ADMIN_SESSION_SECRET=\n",
        encoding="utf-8",
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail
            if [[ "$1" == "compose" ]]; then shift; fi
            if [[ "${1:-}" == "version" ]]; then exit 0; fi
            printf '%s\\n' "$*" >> "$FAKE_DOCKER_LOG"
            case "${1:-}" in
              build|up) exit 0 ;;
              run)
                shift
                mount=''
                while (($#)); do
                  if [[ "$1" == "-v" ]]; then mount="$2"; shift 2; else shift; fi
                done
                host_dir="${mount%%:/workspace}"
                python3 - "$host_dir/.env" <<'PYGEN'
            import sys
            from pathlib import Path
            path = Path(sys.argv[1])
            text = path.read_text()
            for key, value in {
                "ADMIN_USERNAME": "parlez-admin",
                "ADMIN_PASSWORD_HASH": "'$2b$12$generated-hash'",
                "ADMIN_SESSION_SECRET": "generated-session-secret-1234567890",
            }.items():
                import re
                text = re.sub(rf"(?m)^{key}=.*$", f"{key}={value}", text)
            path.write_text(text)
            PYGEN
                echo "fake credential script wrote .env"
                exit 0 ;;
              *) echo "Unexpected fake docker command: $*" >&2; exit 99 ;;
            esac
            """
        ),
        encoding="utf-8",
    )
    fake_docker.chmod(0o755)

    master_fd, slave_fd = pty.openpty()
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["FAKE_DOCKER_LOG"] = str(tmp_path / "docker.log")
    process = subprocess.Popen(
        ["bash", str(repo / "run.sh")],
        cwd=repo,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=env,
        close_fds=True,
    )
    os.close(slave_fd)
    output = bytearray()
    deadline = time.monotonic() + 20
    while process.poll() is None and time.monotonic() < deadline:
        ready, _, _ = select.select([master_fd], [], [], 0.2)
        if ready:
            try:
                output.extend(os.read(master_fd, 4096))
            except OSError:
                break
    if process.poll() is None:
        process.kill()
        process.wait()
        os.close(master_fd)
        pytest.fail("run.sh did not finish within 20 seconds")
    try:
        while True:
            ready, _, _ = select.select([master_fd], [], [], 0)
            if not ready:
                break
            output.extend(os.read(master_fd, 4096))
    except OSError:
        pass
    finally:
        os.close(master_fd)

    assert process.returncode == 0, output.decode("utf-8", errors="replace")
    log = (tmp_path / "docker.log").read_text(encoding="utf-8").splitlines()
    assert log[0] == "build chatbot"
    assert log[1].startswith("run --rm --no-deps --user ")
    assert "python /app/scripts/generate_admin_credentials.py --env-file /workspace/.env" in log[1]
    assert log[2] == "up -d"
    env_values = dotenv_values(repo / ".env")
    assert env_values["ADMIN_USERNAME"] == "parlez-admin"
    assert env_values["ADMIN_PASSWORD_HASH"] == "$2b$12$generated-hash"
    assert stat.S_IMODE((repo / ".env").stat().st_mode) == 0o600

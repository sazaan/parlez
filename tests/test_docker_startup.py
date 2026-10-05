"""Docker startup regression checks; runnable without importing the app.

Run with: python -m unittest discover -s tests -p test_docker_startup.py
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class DockerStartupTests(unittest.TestCase):
    def test_compose_initializes_bind_mount_before_non_root_app(self):
        for filename in ("docker-compose.yml", "docker-compose.prod.yml"):
            with self.subTest(filename=filename):
                config = yaml.safe_load((ROOT / filename).read_text())
                self.assertNotIn("version", config)
                services = config["services"]
                init = services["data-init"]
                app = services["chatbot"]
                self.assertEqual(init["user"], "0:0")
                self.assertEqual(init["image"], app["image"])
                self.assertIn("./data:/app/data", init["volumes"])
                self.assertIn("./data:/app/data", app["volumes"])
                self.assertIn("chown -R appuser:appuser /app/data", init["entrypoint"][-1])
                self.assertEqual(init["restart"], "no")
                self.assertEqual(app["depends_on"]["data-init"]["condition"],
                                 "service_completed_successfully")
                self.assertNotIn("user", app)
        self.assertIn("USER appuser", (ROOT / "Dockerfile").read_text())
        self.assertIn("mkdir -p /app/data", (ROOT / "Dockerfile").read_text())

    def test_run_script_build_failure_prevents_startup(self):
        self._run_script(build_status=17, expected_status=17, expect_up=False)

    def test_run_script_starts_after_successful_build(self):
        self._run_script(build_status=0, expected_status=0, expect_up=True)

    def _run_script(self, build_status, expected_status, expect_up):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy(ROOT / "run.sh", root / "run.sh")
            (root / ".env").write_text("NVIDIA_API_KEY=dummy\n")
            executable = root / "docker"
            executable.write_text(
                '#!/bin/sh\n'
                'echo "$*" >> "$CALL_LOG"\n'
                'case "$*" in\n'
                '  "compose version") exit 0 ;;\n'
                f'  "compose build") exit {build_status} ;;\n'
                '  "compose up") exit 0 ;;\n'
                '  *) exit 1 ;;\n'
                'esac\n'
            )
            executable.chmod(0o755)
            log = root / "calls.log"
            env = {**os.environ, "PATH": f"{root}:{os.environ['PATH']}", "CALL_LOG": str(log)}
            # Start outside the script's directory to check its cwd handling.
            result = subprocess.run(["bash", str(root / "run.sh")], cwd="/",
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, expected_status, result.stdout + result.stderr)
            calls = log.read_text().splitlines()
            self.assertIn("compose build", calls)
            self.assertEqual("compose up" in calls, expect_up)


if __name__ == "__main__":
    unittest.main()

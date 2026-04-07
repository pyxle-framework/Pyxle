"""Helpers for invoking Vite during production builds."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List

from pyxle.cli.logger import ConsoleLogger
from pyxle.devserver.client_files import VITE_CONFIG_FILENAME


class ViteBuildError(RuntimeError):
    """Raised when the Vite build process fails."""


def run_vite_build(
    *,
    project_root: Path,
    client_build_dir: Path,
    output_dir: Path,
    logger: ConsoleLogger,
) -> Path:
    """Execute ``vite build`` and return the generated manifest path."""

    npm_command = _resolve_npm_build_command(project_root, logger)
    vite_args = [
        "--config",
        str(client_build_dir / VITE_CONFIG_FILENAME),
        "--outDir",
        str(output_dir),
        "--emptyOutDir",
        "--manifest",
    ]
    if npm_command is not None:
        full_command = [*npm_command, *vite_args]
    else:
        command = _resolve_vite_command(project_root, logger)
        full_command = [*command, "build", *vite_args]

    logger.info("Running Vite production build")
    env = dict(os.environ)
    env.setdefault("PYXLE_VITE_BASE", "/client/")

    process = subprocess.run(  # noqa: S603 - controlled command invocation
        full_command,
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    _log_process_output(process.stdout, process.stderr, logger)

    if process.returncode not in (0, None):
        raise ViteBuildError(
            f"Vite build failed with exit code {process.returncode}."
        )

    manifest_candidates = [
        output_dir / "manifest.json",
        output_dir / ".vite" / "manifest.json",
    ]
    manifest_path = next((candidate for candidate in manifest_candidates if candidate.exists()), None)
    if manifest_path is None:
        raise ViteBuildError(
            "Vite build completed but manifest was not found at any of the expected locations: "
            + ", ".join(str(candidate) for candidate in manifest_candidates)
        )

    logger.success("Vite build completed")
    return manifest_path


def _resolve_vite_command(project_root: Path, logger: ConsoleLogger) -> List[str]:
    candidates: list[list[str]] = []

    node_exec = shutil.which("node")
    vite_js = project_root / "node_modules" / "vite" / "bin" / "vite.js"
    if node_exec and vite_js.exists():
        candidates.append([node_exec, str(vite_js)])

    npm_bin = project_root / "node_modules" / ".bin"
    for executable in ("vite", "vite.cmd", "vite.ps1"):
        candidate = npm_bin / executable
        if candidate.exists():
            candidates.append([str(candidate)])

    global_vite = shutil.which("vite")
    if global_vite:
        candidates.append([global_vite])

    npx_exec = shutil.which("npx")
    if npx_exec:
        candidates.append([npx_exec, "--yes", "vite"])

    for command in candidates:
        if _verify_command(command, project_root):
            return command

    if _attempt_npm_install(project_root, logger):
        return _resolve_vite_command(project_root, logger)

    raise ViteBuildError(
        "Unable to locate a Vite executable. Install dependencies with 'npm install'."
    )


def _resolve_npm_build_command(project_root: Path, logger: ConsoleLogger) -> List[str] | None:
    package_json = project_root / "package.json"
    if not package_json.exists():
        return None

    npm_exec = shutil.which("npm")
    if npm_exec is None:
        return None

    try:
        package_payload = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    scripts = package_payload.get("scripts")
    if not isinstance(scripts, dict) or "build" not in scripts:
        return None

    node_modules = project_root / "node_modules"
    if not node_modules.exists():
        _attempt_npm_install(project_root, logger)

    return [npm_exec, "run", "build", "--"]


def _verify_command(command: Iterable[str], project_root: Path) -> bool:
    try:
        process = subprocess.run(  # noqa: S603 - controlled command invocation
            list(command) + ["--version"],
            cwd=str(project_root),
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return process.returncode in (0, None)


def _attempt_npm_install(project_root: Path, logger: ConsoleLogger) -> bool:
    package_json = project_root / "package.json"
    node_modules = project_root / "node_modules"

    if not package_json.exists() or node_modules.exists():
        return False

    npm_exec = shutil.which("npm")
    if npm_exec is None:
        logger.warning("Cannot run 'npm install': npm executable not found in PATH.")
        return False

    logger.info("Installing Node dependencies via 'npm install'")
    process = subprocess.run(  # noqa: S603 - controlled command invocation
        [npm_exec, "install"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )

    _log_process_output(process.stdout, process.stderr, logger, prefix="npm")

    if process.returncode not in (0, None):
        logger.error(f"'npm install' exited with code {process.returncode}")
        return False

    logger.success("npm install completed")
    return True


def _log_process_output(stdout: str, stderr: str, logger: ConsoleLogger, *, prefix: str = "vite") -> None:
    for line in stdout.splitlines():
        line = line.strip()
        if line:
            logger.info(f"[{prefix}] {line}")
    for line in stderr.splitlines():
        line = line.strip()
        if line:
            logger.error(f"[{prefix}] {line}")


__all__ = ["run_vite_build", "ViteBuildError"]

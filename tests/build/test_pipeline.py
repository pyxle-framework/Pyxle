import json
from pathlib import Path

from pyxle.build.pipeline import run_build
from pyxle.cli.logger import ConsoleLogger
from pyxle.devserver.builder import BuildSummary
from pyxle.devserver.registry import MetadataRegistry, PageRegistryEntry
from pyxle.devserver.settings import DevServerSettings


def silent_logger() -> ConsoleLogger:
    return ConsoleLogger(secho=lambda *args, **kwargs: None)


def test_run_build_invokes_vite_and_copies_artifacts(monkeypatch, tmp_path):
    project = tmp_path / "project"
    pages_dir = project / "pages"
    public_dir = project / "public"
    build_root = project / ".pyxle-build"
    server_build = build_root / "server" / "pages"
    metadata_build = build_root / "metadata" / "pages"

    for path in (pages_dir, public_dir, server_build, metadata_build):
        path.mkdir(parents=True, exist_ok=True)

    (server_build / "index.py").write_text("print('server')\n", encoding="utf-8")
    (metadata_build / "index.json").write_text("{}", encoding="utf-8")
    (public_dir / "robots.txt").write_text("User-agent: *\n", encoding="utf-8")

    settings = DevServerSettings.from_project_root(project)

    summary = BuildSummary(compiled_pages=["pages/index.pyx"])
    registry = MetadataRegistry(
        pages=[
            PageRegistryEntry(
                route_path="/",
                alternate_route_paths=(),
                source_relative_path=Path("pages/index.pyx"),
                source_absolute_path=pages_dir / "index.pyx",
                server_module_path=server_build / "index.py",
                client_module_path=settings.client_build_dir / "pages" / "index.jsx",
                metadata_path=metadata_build / "index.json",
                client_asset_path="/client/index.js",
                server_asset_path="server/pages/index.py",
                module_key="pyxle.server.pages.index",
                content_hash="hash123",
                loader_name=None,
                loader_line=None,
                head_elements=(),
                head_is_dynamic=False,
            )
        ],
        apis=[],
    )

    captured: dict[str, object] = {}

    def fake_build_once(settings_arg, *, force_rebuild):
        captured["force_rebuild"] = force_rebuild
        return summary

    def fake_build_metadata_registry(settings_arg):
        captured["registry_settings"] = settings_arg
        return registry

    def fake_run_vite_build(*, project_root, client_build_dir, output_dir, logger):
        captured["vite_args"] = {
            "project_root": project_root,
            "client_build_dir": client_build_dir,
            "output_dir": output_dir,
        }
        manifest_path = output_dir / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            '{"pages/index.jsx": {"file": "client/index.js", "imports": []}}',
            encoding="utf-8",
        )
        return manifest_path

    monkeypatch.setattr("pyxle.build.pipeline.build_once", fake_build_once)
    monkeypatch.setattr("pyxle.build.pipeline.build_metadata_registry", fake_build_metadata_registry)
    monkeypatch.setattr("pyxle.build.pipeline.run_vite_build", fake_run_vite_build)

    result = run_build(settings, logger=silent_logger())

    assert captured["force_rebuild"] is True
    assert captured["registry_settings"] == settings

    dist_root = result.dist_dir
    assert (dist_root / "server" / "pages" / "index.py").exists()
    assert (dist_root / "metadata" / "pages" / "index.json").exists()
    assert (dist_root / "public" / "robots.txt").exists()
    assert (dist_root / "client" / "manifest.json").exists()

    vite_args = captured["vite_args"]
    assert vite_args["project_root"] == project
    assert vite_args["client_build_dir"] == settings.client_build_dir
    assert vite_args["output_dir"] == dist_root / "client"

    assert result.client_manifest_path == dist_root / "client" / "manifest.json"
    assert result.page_manifest == {
        "/": {
            "client": {"file": "client/index.js", "imports": []},
            "metadata": (metadata_build / "index.json").as_posix(),
            "server": (server_build / "index.py").as_posix(),
        }
    }
    assert result.page_manifest_path == dist_root / "page-manifest.json"
    assert json.loads(result.page_manifest_path.read_text(encoding="utf-8")) == result.page_manifest


def test_run_build_supports_incremental_mode(monkeypatch, tmp_path):
    project = tmp_path / "project"
    pages_dir = project / "pages"
    public_dir = project / "public"
    build_root = project / ".pyxle-build"
    server_build = build_root / "server" / "pages"
    metadata_build = build_root / "metadata" / "pages"

    for path in (pages_dir, public_dir, server_build, metadata_build):
        path.mkdir(parents=True, exist_ok=True)

    (server_build / "index.py").write_text("print('server')\n", encoding="utf-8")
    (metadata_build / "index.json").write_text("{}", encoding="utf-8")

    settings = DevServerSettings.from_project_root(project)

    summary = BuildSummary()
    registry = MetadataRegistry(pages=[], apis=[])

    captured: dict[str, object] = {}

    def fake_build_once(settings_arg, *, force_rebuild):
        captured["force_rebuild"] = force_rebuild
        return summary

    def fake_build_metadata_registry(settings_arg):
        return registry

    def fake_run_vite_build(*, project_root, client_build_dir, output_dir, logger):
        manifest_path = output_dir / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text("{}", encoding="utf-8")
        return manifest_path

    monkeypatch.setattr("pyxle.build.pipeline.build_once", fake_build_once)
    monkeypatch.setattr("pyxle.build.pipeline.build_metadata_registry", fake_build_metadata_registry)
    monkeypatch.setattr("pyxle.build.pipeline.run_vite_build", fake_run_vite_build)

    result = run_build(settings, logger=silent_logger(), force_rebuild=False)

    assert captured["force_rebuild"] is False
    assert result.client_manifest_path == result.client_dir / "manifest.json"
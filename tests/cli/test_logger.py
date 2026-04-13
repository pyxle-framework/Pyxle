import json

from pyxle.cli.logger import ConsoleLogger, LogFormat, Verbosity


def test_console_logger_emits_expected_symbols():
    captured: list[str] = []

    def capture(message: str, *, fg: str | None = None, bold: bool = False) -> None:  # noqa: ARG001
        captured.append(message)

    logger = ConsoleLogger(secho=capture)

    logger.info("Info message")
    logger.success("Done")
    logger.warning("Careful")
    logger.error("Boom")
    logger.step("Navigate", "cd project")

    assert captured == [
        "ℹ️  Info message",
        "✅ Done",
        "⚠️  Careful",
        "❌ Boom",
        "▶️  Navigate — cd project",
    ]


def test_console_logger_json_emits_structured_payloads():
    captured: list[str] = []

    def capture(message: str, *, fg: str | None = None, bold: bool = False) -> None:  # noqa: ARG001
        captured.append(message)

    logger = ConsoleLogger(
        secho=capture,
        formatter=LogFormat.JSON,
        timestamp_factory=lambda: "2025-01-01T00:00:00Z",
    )

    logger.info("Info message")
    logger.step("Deploy", "Ship to prod")

    assert len(captured) == 2
    info_payload = json.loads(captured[0])
    step_payload = json.loads(captured[1])

    assert info_payload == {
        "level": "info",
        "message": "ℹ️  Info message",
        "timestamp": "2025-01-01T00:00:00Z",
    }
    assert step_payload["level"] == "step"
    assert step_payload["label"] == "Deploy"
    assert step_payload["detail"] == "Ship to prod"
    assert "ready" not in step_payload
    assert step_payload["timestamp"] == "2025-01-01T00:00:00Z"


def test_quiet_mode_suppresses_info_and_step():
    captured: list[str] = []

    def capture(message: str, *, fg: str | None = None, bold: bool = False) -> None:  # noqa: ARG001
        captured.append(message)

    logger = ConsoleLogger(secho=capture, verbosity=Verbosity.QUIET)

    logger.info("should be suppressed")
    logger.step("also suppressed")
    logger.debug("suppressed too")
    logger.warning("visible")
    logger.error("visible")
    logger.success("visible")

    assert len(captured) == 3
    assert "visible" in captured[0]


def test_verbose_mode_shows_debug():
    captured: list[str] = []

    def capture(message: str, *, fg: str | None = None, bold: bool = False) -> None:  # noqa: ARG001
        captured.append(message)

    logger = ConsoleLogger(secho=capture, verbosity=Verbosity.VERBOSE)

    logger.debug("debug detail")
    logger.info("info message")

    assert len(captured) == 2
    assert "debug detail" in captured[0]


def test_normal_mode_suppresses_debug():
    captured: list[str] = []

    def capture(message: str, *, fg: str | None = None, bold: bool = False) -> None:  # noqa: ARG001
        captured.append(message)

    logger = ConsoleLogger(secho=capture, verbosity=Verbosity.NORMAL)

    logger.debug("hidden")
    logger.info("shown")

    assert len(captured) == 1
    assert "shown" in captured[0]


def test_set_verbosity():
    logger = ConsoleLogger()
    assert logger.verbosity == Verbosity.NORMAL

    logger.set_verbosity(Verbosity.QUIET)
    assert logger.verbosity == Verbosity.QUIET

    logger.set_verbosity(Verbosity.VERBOSE)
    assert logger.verbosity == Verbosity.VERBOSE


def test_diagnostic_error_with_location():
    captured: list[str] = []

    def capture(message: str, *, fg: str | None = None, bold: bool = False) -> None:
        captured.append(message)

    logger = ConsoleLogger(secho=capture)
    logger.diagnostic(
        "variable 'x' is not defined",
        file="pages/index.pyxl",
        line=10,
        column=5,
        severity="error",
    )

    assert len(captured) == 2
    assert "error:" in captured[0]
    assert "variable 'x' is not defined" in captured[0]
    assert "--> pages/index.pyxl:10:5" in captured[1]


def test_diagnostic_warning_without_location():
    captured: list[str] = []

    def capture(message: str, *, fg: str | None = None, bold: bool = False) -> None:
        captured.append(message)

    logger = ConsoleLogger(secho=capture)
    logger.diagnostic(
        "unused import",
        severity="warning",
    )

    assert len(captured) == 1
    assert "warning:" in captured[0]


def test_diagnostic_with_hint():
    captured: list[str] = []

    def capture(message: str, *, fg: str | None = None, bold: bool = False) -> None:
        captured.append(message)

    logger = ConsoleLogger(secho=capture)
    logger.diagnostic(
        "async function required",
        file="pages/index.pyxl",
        line=5,
        hint="Add 'async' keyword to the function definition",
    )

    assert len(captured) == 3
    assert "error:" in captured[0]
    assert "--> pages/index.pyxl:5" in captured[1]
    assert "hint:" in captured[2]
    assert "async" in captured[2]


def test_diagnostic_json_format():
    captured: list[str] = []

    def capture(message: str, *, fg: str | None = None, bold: bool = False) -> None:
        captured.append(message)

    logger = ConsoleLogger(
        secho=capture,
        formatter=LogFormat.JSON,
        timestamp_factory=lambda: "2025-01-01T00:00:00Z",
    )
    logger.diagnostic(
        "type mismatch",
        file="src/main.ts",
        line=42,
        column=8,
        hint="use string instead of number",
    )

    assert len(captured) == 1
    payload = json.loads(captured[0])
    assert payload["level"] == "error"
    assert payload["message"] == "type mismatch"
    assert payload["location"] == "src/main.ts:42:8"
    assert payload["hint"] == "use string instead of number"


def test_diagnostic_file_without_line():
    captured: list[str] = []

    def capture(message: str, *, fg: str | None = None, bold: bool = False) -> None:
        captured.append(message)

    logger = ConsoleLogger(secho=capture)
    logger.diagnostic(
        "invalid config",
        file="pyxle.config.json",
    )

    assert len(captured) == 2
    assert "--> pyxle.config.json" in captured[1]
    assert ":" not in captured[1].split("pyxle.config.json")[1]

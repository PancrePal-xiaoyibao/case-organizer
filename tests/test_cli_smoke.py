from typer.testing import CliRunner

from case_organizer.cli import app


def test_cli_shows_root_help():
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "scan" in result.stdout
    assert "review" in result.stdout
    assert "export" in result.stdout


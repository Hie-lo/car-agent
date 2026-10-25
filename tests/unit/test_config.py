import os
from pathlib import Path
import pytest
from app.config import load_dotenv


class TestConfigDotenvLoader:
    def test_load_dotenv_parses_cleanly(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# A comment line\n"
            "KENAR_TEST_KEY=secret_123\n"
            "   KENAR_SPACED_KEY = 'quoted_value'   \n"
            "KENAR_DOUBLE_QUOTE = \"double_quoted\"\n"
            "INVALID_LINE_WITHOUT_EQUALS\n"
            "\n",
            encoding="utf-8",
        )

        load_dotenv(env_file)
        assert os.environ.get("KENAR_TEST_KEY") == "secret_123"
        assert os.environ.get("KENAR_SPACED_KEY") == "quoted_value"
        assert os.environ.get("KENAR_DOUBLE_QUOTE") == "double_quoted"

    def test_load_dotenv_missing_file_no_error(self, tmp_path):
        load_dotenv(tmp_path / "non_existent.env")

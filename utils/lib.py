from pathlib import Path


class ConfigError(Exception):
    pass


def load_api_key() -> str:
    # корень проекта = на уровень выше папки utils
    project_root = Path(__file__).resolve().parent.parent
    file_path = project_root / "api_key.txt"

    try:
        api_key = file_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise ConfigError(f"API key file not found: {file_path}")
    except OSError as e:
        raise ConfigError(f"Failed to read API key file: {e}")

    if not api_key:
        raise ConfigError("API key is empty or contains only whitespace")

    return api_key

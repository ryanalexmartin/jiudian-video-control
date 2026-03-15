"""JSON file persistence for configuration and scenes."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from jiudian_server.compositing.models import Scene

from .defaults import generate_default_scenes

log = logging.getLogger(__name__)

_CONFIG_FILE = "config.json"
_SCENES_FILE = "scenes.json"
_INPUTS_FILE = "inputs.json"


def _ensure_dir(config_dir: Path) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Application config
# ---------------------------------------------------------------------------

def load_config(config_dir: Path) -> dict:
    """Load application config from *config_dir*/config.json.

    Returns an empty dict if the file does not exist.
    """
    path = config_dir / _CONFIG_FILE
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Failed to load config from %s: %s", path, exc)
        return {}


def save_config(config_dir: Path, config: dict) -> None:
    """Persist application config to *config_dir*/config.json."""
    _ensure_dir(config_dir)
    path = config_dir / _CONFIG_FILE
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Config saved to %s", path)


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------

def load_scenes(config_dir: Path, input_ids: list[int] | None = None) -> list[Scene]:
    """Load scenes from *config_dir*/scenes.json, merged with defaults.

    Built-in default scenes are always present.  User-saved scenes (those
    whose ``is_default`` is ``False``) are appended.  If a saved scene has
    the same ``id`` as a default scene the saved version is ignored so that
    built-in presets cannot be overwritten accidentally.
    """
    default_scenes = generate_default_scenes(input_ids or [0, 1, 2, 3])
    defaults_by_id = {s.id: s for s in default_scenes}
    scenes: list[Scene] = list(default_scenes)

    path = config_dir / _SCENES_FILE
    if not path.exists():
        return scenes

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Failed to load scenes from %s: %s", path, exc)
        return scenes

    for item in raw:
        try:
            scene = Scene.model_validate(item)
        except Exception as exc:  # noqa: BLE001
            log.warning("Skipping invalid scene entry: %s", exc)
            continue
        # Only add user scenes (skip duplicates of defaults)
        if scene.id not in defaults_by_id:
            scenes.append(scene)

    return scenes


def save_scenes(config_dir: Path, scenes: list[Scene]) -> None:
    """Persist scenes to *config_dir*/scenes.json.

    Only non-default (user-created) scenes are written to disk; built-in
    presets are always regenerated from :data:`defaults.generate_default_scenes`.
    """
    _ensure_dir(config_dir)
    user_scenes = [s for s in scenes if not s.is_default]
    path = config_dir / _SCENES_FILE
    data = [json.loads(s.model_dump_json()) for s in user_scenes]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Saved %d user scene(s) to %s", len(user_scenes), path)


# ---------------------------------------------------------------------------
# Input sources config
# ---------------------------------------------------------------------------

def load_inputs(config_dir: Path) -> list[dict] | None:
    """Load input source config from *config_dir*/inputs.json.

    Returns None if the file does not exist (caller should use defaults).
    Each entry: {"id": int, "type": "camera"|"test_pattern", "device_index": int}
    """
    path = config_dir / _INPUTS_FILE
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Failed to load inputs from %s: %s", path, exc)
        return None


def save_inputs(config_dir: Path, inputs: list[dict]) -> None:
    """Persist input source config to *config_dir*/inputs.json."""
    _ensure_dir(config_dir)
    path = config_dir / _INPUTS_FILE
    path.write_text(json.dumps(inputs, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Saved %d input(s) to %s", len(inputs), path)

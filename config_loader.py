"""Central configuration loader.

Loads config.yaml and expands ${VAR} and ${VAR:-default} references from the
environment (and .env), so secrets live in .env rather than in the YAML. Import
`load_config` from here instead of re-implementing it per module.
"""
import os
import re
import yaml
from dotenv import load_dotenv

_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)(:-([^}]*))?\}")


def load_config(config_file="config.yaml"):
    load_dotenv()
    with open(config_file, "r") as f:
        raw = f.read()

    def _sub(match):
        var, _, default = match.groups()
        return os.environ.get(var, default if default is not None else "")

    return yaml.safe_load(_PATTERN.sub(_sub, raw))

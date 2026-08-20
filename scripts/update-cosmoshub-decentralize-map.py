#!/usr/bin/env python3
"""Run the shared reviewed decentralization-map collector for Cosmos Hub."""

from __future__ import annotations

import os
import runpy
from pathlib import Path

os.environ["POSTHUMAN_MAP_PROFILE"] = "cosmoshub"
runpy.run_path(
    str(Path(__file__).with_name("update-celestia-decentralize-map.py")),
    run_name="__main__",
)

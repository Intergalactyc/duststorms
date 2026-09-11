import pathlib
import re

import pandas as pd

PROCESSED_DIR = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "ttu-tower-processing" / "results" / "processed"
)

_SUBNAME_RE = re.compile(r"^(ds.+)_(\d+min)$")


def _ds_outputs() -> dict[str, list[pathlib.Path]]:
    outputs = {}
    if PROCESSED_DIR.is_dir():
        for entry in PROCESSED_DIR.iterdir():
            match = _SUBNAME_RE.match(entry.name)
            if not match:
                continue
            parquet = entry / "fullyear.parquet"
            if parquet.exists():
                outputs.setdefault(match.group(1), []).append(parquet)
    return outputs


def available_data() -> list[str]:
    return sorted(_ds_outputs())


def load(identifier: str) -> pd.DataFrame:
    matches = _ds_outputs().get(identifier)
    if not matches:
        raise FileNotFoundError(f"No processed output found for '{identifier}' under {PROCESSED_DIR}")
    if len(matches) > 1:
        found = [p.parent.name for p in matches]
        raise ValueError(f"Ambiguous identifier '{identifier}': multiple interval outputs found ({found})")
    return pd.read_parquet(matches[0]).reset_index()

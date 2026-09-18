import pathlib
import re

import pandas as pd

PROCESSED_DIR = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "ttu-tower-processing" / "results" / "processed"
)

PM25_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "tceq_pm25"

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


def load_pm25(identifier: str) -> pd.DataFrame:
    name = identifier[2:] if identifier.startswith("ds") else identifier
    path = PM25_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"No cached PM2.5 data for '{identifier}' at {path} - run data/fetch_tceq_pm25.py first")
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def combine_pm25(df: pd.DataFrame, identifier: str) -> pd.DataFrame:
    pm25 = load_pm25(identifier)[["timestamp", "value", "flag"]].rename(columns={"value": "pm25", "flag": "pm25_flag"})
    pm25["timestamp"] = pm25["timestamp"].dt.tz_convert(df["timestamp"].dt.tz)
    # TCEQ labels each hourly average by the start of its window, so the H:00 reading covers [H:00, H+1:00)
    return pd.merge_asof(df.sort_values("timestamp"), pm25.sort_values("timestamp"), on="timestamp", direction="backward")

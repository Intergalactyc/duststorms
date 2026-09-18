import argparse
import datetime as dt
import io
import pathlib
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

import pandas as pd
from ttu_tower.definitions import SOURCE_TIMEZONE

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from src.generate_configs import DATE_RANGES

BASE_URL = "https://www.tceq.texas.gov/cgi-bin/compliance/monops/yearly_summary.pl"
CACHE_DIR = pathlib.Path(__file__).parent / "tceq_cache"
OUTPUT_DIR = pathlib.Path(__file__).parent / "tceq_pm25"

TZ = ZoneInfo(SOURCE_TIMEZONE)  # TCEQ also reports in fixed-offset CST, same convention as the tower data

DEFAULT_CAMS = 325
DEFAULT_SITE_LABEL = "Lubbock C325"
DEFAULT_AQS_ID = "48_303_0325"
DEFAULT_PARAM = "88502"  # PM-2.5 (Local Conditions) Acceptable, the only PM2.5 channel CAMS 325 reports

# https://www.tceq.texas.gov/cgi-bin/compliance/monops/daily_info.pl?nodata=
FLAG_MEANINGS = {
    "NA": "average not yet available",
    "AQI": "rejected by TCEQ validators",
    "CAL": "automatic calibration in progress",
    "FEW": "fewer than 45 minutes of data in the hour",
    "LIM": "failed calibration/span check or outside EPA meteorological guidelines",
    "LST": "lost data / never collected",
    "MAL": "instrument malfunction",
    "NOL": "instrument not calibrated/online",
    "PMA": "preventive maintenance",
    "QAS": "quality control audit in progress",
    "QRE": "rejected for failed QA",
    "SPN": "automatic span check in progress",
    "SPZ": "automatic span check in progress (short)",
}


def _site_value(cams: int, label: str, aqs_id: str) -> str:
    return f"site|{label}|{aqs_id}|{cams}"


def fetch_year(cams: int, param: str, year: int, site_label: str, aqs_id: str, refresh: bool = False) -> str:
    cache_path = CACHE_DIR / f"CAMS{cams}_{param}_{year}.csv"
    if cache_path.exists() and not refresh:
        return cache_path.read_text()

    body = urllib.parse.urlencode({
        "submitted": "1",
        "first_look": "no",
        "select_site": _site_value(cams, site_label, aqs_id),
        "user_year": str(year),
        "user_param": param,
        "time_format": "24hr",
        "report_format": "comma",
    }).encode()
    req = urllib.request.Request(BASE_URL, data=body, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    start = html.index("<pre>") + len("<pre>")
    end = html.index("</pre>", start)
    csv_text = html[start:end].strip("\n")
    if "Date," not in csv_text:
        raise RuntimeError(f"Unexpected response for CAMS {cams} param {param} year {year} (no data table found)")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(csv_text)
    return csv_text


def parse_year_csv(csv_text: str) -> pd.DataFrame:
    lines = csv_text.splitlines()
    header_idx = next(i for i, line in enumerate(lines) if line.startswith("Date,"))
    table = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
    long = table.melt(id_vars="Date", var_name="hour", value_name="raw")
    long["timestamp"] = pd.to_datetime(long["Date"] + " " + long["hour"], format="%m/%d/%Y %H:%M").dt.tz_localize(TZ)
    long["value"] = pd.to_numeric(long["raw"], errors="coerce")
    long["flag"] = long["raw"].where(long["value"].isna())
    return long[["timestamp", "value", "flag"]].sort_values("timestamp").reset_index(drop=True)


def fetch_ranges(ranges: dict[str, tuple[dt.datetime, dt.datetime]], cams=DEFAULT_CAMS, param=DEFAULT_PARAM,
                  site_label=DEFAULT_SITE_LABEL, aqs_id=DEFAULT_AQS_ID, refresh: bool = False) -> dict[str, pd.DataFrame]:
    years = sorted({y for start, end in ranges.values() for y in (start.year, (end - dt.timedelta(seconds=1)).year)})
    frames = []
    for year in years:
        csv_text = fetch_year(cams, param, year, site_label, aqs_id, refresh)
        frames.append(parse_year_csv(csv_text))
    full = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["timestamp", "value", "flag"])

    result = {}
    for name, (start, end) in ranges.items():
        mask = (full["timestamp"] >= start) & (full["timestamp"] < end)
        result[name] = full[mask].sort_values("timestamp").reset_index(drop=True)
    return result


def _localize(naive: dt.datetime) -> dt.datetime:
    return naive if naive.tzinfo else naive.replace(tzinfo=TZ)


def ranges_from_configs() -> dict[str, tuple[dt.datetime, dt.datetime]]:
    return {name: (_localize(start), _localize(end)) for name, (start, end) in DATE_RANGES.items()}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Download TCEQ CAMS hourly PM2.5 data for the dust storm event date ranges in generate_configs.py")
    parser.add_argument("--cams", type=int, default=DEFAULT_CAMS)
    parser.add_argument("--site-label", default=DEFAULT_SITE_LABEL)
    parser.add_argument("--aqs-id", default=DEFAULT_AQS_ID)
    parser.add_argument("--param", default=DEFAULT_PARAM, help="EPA parameter code, default 88502 (PM-2.5 Local Conditions Acceptable)")
    parser.add_argument("--dates", nargs="*", default=[], metavar="NAME=YYYY-MM-DD", help="Extra single-day ranges to add on top of generate_configs.py, e.g. 23Mar2013=2013-03-23")
    parser.add_argument("--only-dates", nargs="*", metavar="NAME=YYYY-MM-DD", help="Replace the generate_configs.py range list entirely (single-day ranges only)")
    parser.add_argument("--refresh", action="store_true", help="Re-download years already cached")
    parser.add_argument("--output-dir", type=pathlib.Path, default=OUTPUT_DIR)
    return parser.parse_args(argv)


def _parse_name_date_pairs(pairs: list[str]) -> dict[str, tuple[dt.datetime, dt.datetime]]:
    out = {}
    for pair in pairs:
        name, _, date_str = pair.partition("=")
        start = dt.datetime.combine(dt.date.fromisoformat(date_str), dt.time(), tzinfo=TZ)
        out[name] = (start, start + dt.timedelta(days=1))
    return out


def main(argv=None):
    args = parse_args(argv)

    if args.only_dates:
        ranges = _parse_name_date_pairs(args.only_dates)
    else:
        ranges = ranges_from_configs()
        ranges.update(_parse_name_date_pairs(args.dates))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = fetch_ranges(ranges, args.cams, args.param, args.site_label, args.aqs_id, args.refresh)

    print(f"{'name':<14}{'range':<24}{'valid_hrs':<12}coverage")
    for name, (start, end) in sorted(ranges.items(), key=lambda kv: kv[1][0]):
        df = results[name]
        out_path = args.output_dir / f"{name}.csv"
        df.to_csv(out_path, index=False)
        total_hours = int((end - start).total_seconds() // 3600)
        valid = int(df["value"].notna().sum())
        span = f"{start.date()}->{end.date()}"
        print(f"{name:<14}{span:<24}{valid:>3}/{total_hours:<8}{valid / total_hours:.0%}")


if __name__ == "__main__":
    main()

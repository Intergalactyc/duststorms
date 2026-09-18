import json
import pathlib
import configparser
from datetime import datetime, timedelta

TEMPLATE = pathlib.Path(__file__).parent.parent / "configs" / "templates" / "duststorm_TEMPLATE.ini"
CONFIGS_DIR = TEMPLATE.parent.parent

SOURCE_DIRECTORY = pathlib.Path("C:\\Users\\ellwalke\\Data\\Dust_Storms_TTU_200m\\Transformed")

DATE_DIRECTORY_MAP = {
    "14Dec2012" : "2012_12_14",
    "19Dec2012" : "2012_12_19", # 47/48
    # "23Mar2013" : "2013_03_23",
    "16Nov2013" : "2013_11_16",
    "28Feb2014" : "2014_02_28",
    "11Mar2014" : "2014_03_11",
    "18Mar2014" : "2014_03_18",
    "27Apr2014" : "2014_04_27-29" # 137/148
}

# Multi-day exception; every other identifier is a single calendar day
DATE_RANGE_DAYS = {
    "27Apr2014": 3,
}

# naive local time, fixed CST/Etc-GMT+6 offset (no DST) matching ttu_tower.definitions.SOURCE_TIMEZONE
def _date_range(identifier: str) -> tuple[datetime, datetime]:
    start = datetime.strptime(identifier, "%d%b%Y")
    return start, start + timedelta(days=DATE_RANGE_DAYS.get(identifier, 1))

DATE_RANGES = {name: _date_range(name) for name in DATE_DIRECTORY_MAP}

def main():
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    for name, directory in DATE_DIRECTORY_MAP.items():
        scan_path = (SOURCE_DIRECTORY / directory).as_posix()

        parser = configparser.ConfigParser(allow_no_value=False)
        parser.read(TEMPLATE)
        parser.set("paths", "scanall", json.dumps([scan_path]))

        out_path = CONFIGS_DIR / f"ds{name}.ini"
        with open(out_path, "w") as f:
            parser.write(f)
        print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()

# get_fitabase_data.py
import os
import shutil
import zipfile
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi

DATASET_SLUG = "arashnic/fitbit"

TARGET_FOLDERS = [
    "Fitabase Data 3.12.16-4.11.16",
    "Fitabase Data 4.12.16-5.12.16",
]

BASE_DIR = Path.cwd()
WORK_DIR = BASE_DIR / "kaggle_tmp_download"
DATA_DIR = BASE_DIR / "data"
FINAL_DIR = DATA_DIR / "Final_data"


def extract_all_zips(root: Path):
    while True:
        zips = list(root.rglob("*.zip"))
        if not zips:
            break
        for z in zips:
            try:
                with zipfile.ZipFile(z, "r") as zf:
                    extract_to = z.parent
                    zf.extractall(extract_to)
                z.unlink()
            except zipfile.BadZipFile:
                continue


def safe_move(src: Path, dst: Path):
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            safe_move(item, target)
        else:
            if target.exists():
                target.unlink()
            shutil.move(str(item), str(target))


def find_target_dirs(root: Path, names: list[str]) -> dict[str, Path]:
    want = {n.lower(): n for n in names}
    found: dict[str, Path] = {}
    for p in root.rglob("*"):
        if p.is_dir():
            key = p.name.lower()
            if key in want and want[key] not in found:
                found[want[key]] = p
    return found


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    api = KaggleApi()
    api.authenticate()
    print(f"Downloading '{DATASET_SLUG}' to {WORK_DIR} ...")
    api.dataset_download_files(DATASET_SLUG, path=str(WORK_DIR), unzip=True)
    extract_all_zips(WORK_DIR)

    DATA_DIR.mkdir(exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    found = find_target_dirs(WORK_DIR, TARGET_FOLDERS)
    missing = [n for n in TARGET_FOLDERS if n not in found]
    if missing:
        print("⚠️ No folders found:", ", ".join(missing))

    for human_name, path_obj in found.items():
        dst = DATA_DIR / human_name
        print(f"Moving '{path_obj}' → '{dst}'")
        safe_move(path_obj, dst)

    try:
        shutil.rmtree(WORK_DIR)
    except Exception as e:
        print(f"Failed to remove temporary folder: {e}")

    print("\nDone ✅")
    print(f"Data structure: {DATA_DIR.resolve()}")
    for n in TARGET_FOLDERS:
        print(" -", (DATA_DIR / n))
    print(" -", FINAL_DIR)


if __name__ == "__main__":
    main()

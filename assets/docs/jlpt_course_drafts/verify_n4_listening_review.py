"""Verify a completed N4 listening review against its ZIP and current scripts."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from zipfile import BadZipFile, ZipFile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def indexed(rows, field):
    by_id = {}
    for row in rows:
        key = row[field]
        require(key and key not in by_id, f"重复或空的素材 ID：{key}")
        by_id[key] = row
    return by_id


def current_materials():
    materials = []
    root = Path(__file__).resolve().parent
    units = [root / f"n4-{number:02}.json" for number in range(1, 17)]
    for path in [*units, root / "n4-level.json"]:
        course = json.loads(path.read_text(encoding="utf-8"))
        for lesson in course["lessons"]:
            if lesson["type"] == "L":
                materials.extend(lesson["materials"])
        materials.extend(
            material for material in course["exam"]["materials"]
            if material["role"] == "exam_listening"
        )
    return indexed(materials, "id")


def verify(package, report):
    materials = current_materials()
    with ZipFile(package) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), "压缩包内有重名文件")
        require(archive.read("CREDITS.txt").strip(), "缺少音色署名")
        manifest = archive.read("manifest.csv")
        require(report["manifestSha256"] == sha256(manifest), "审校结果对应的是另一个版本")
        rows = indexed(csv.DictReader(io.StringIO(manifest.decode("utf-8-sig"))), "素材ID")
        results = indexed(report["results"], "id")
        require(rows.keys() == materials.keys(), "清单与当前 N4 听力素材不一致")
        require(results.keys() == rows.keys(), "审校结果未覆盖全部素材")
        reviewer = report["reviewer"]
        require(isinstance(reviewer, str) and reviewer.strip(), "请填写审校人")
        unfinished = []
        for key, material in materials.items():
            row, result = rows[key], results[key]
            require(row["原稿"] == material["jp"], f"原稿已变更：{key}")
            require(row["用途"] == material["role"], f"素材用途不一致：{key}")
            require(row["文件"] == f"{key}.mp3", f"音频文件名不一致：{key}")
            digest = sha256(archive.read(row["文件"]))
            require(digest == row["SHA-256"] == result["sha256"], f"音频哈希不一致：{key}")
            if result["status"] != "pass":
                unfinished.append(key)
        require(not unfinished, f"{len(unfinished)} 段未通过：{', '.join(unfinished)}")
    return len(materials)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        count = verify(args.package, json.loads(args.report.read_text(encoding="utf-8")))
    except (BadZipFile, OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"听审结果未通过校验：{error}\n")
    print(f"{count} 段听审记录均为通过，且与当前课程和音频一致。")


if __name__ == "__main__":
    main()

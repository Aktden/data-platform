"""Снять explain(executionStats); --all повторяет шесть замеров практикума.

--all удаляет неслужебные индексы только учебной коллекции logs.events.
Запускать на стенде курса. Файлы сохраняются рядом со скриптом.
"""
import argparse
import json
import os
from pathlib import Path

from bson import SON, json_util
from pymongo import MongoClient

BAZA = "logs"
KOLLEKCIYA = "events"
FILTR = {"level": "error"}
SORTIROVKA = [("duration_ms", -1)]
PREDEL = 10
FAYL = "plan-4.json"
ROOT = Path(__file__).resolve().parent


def stages(node):
    result = []
    if isinstance(node, dict):
        if "inputStage" in node:
            result.extend(stages(node["inputStage"]))
        if "stage" in node:
            result.append(node["stage"])
    return result


def capture(db, filename, query, sort, limit=0):
    command = {"find": KOLLEKCIYA, "filter": query, "sort": SON(sort)}
    if limit:
        command["limit"] = limit
    plan = db.command("explain", command, verbosity="executionStats")
    (ROOT / filename).write_text(
        json_util.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    stats = plan["executionStats"]
    winning = plan["queryPlanner"]["winningPlan"]
    winning = winning.get("queryPlan", winning)
    summary = {"file": filename, "nReturned": stats["nReturned"],
               "totalDocsExamined": stats["totalDocsExamined"],
               "totalKeysExamined": stats["totalKeysExamined"],
               "stages": stages(winning)}
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default=FAYL)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    with MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"),
                     serverSelectionTimeoutMS=5000) as client:
        db = client[BAZA]
        if not args.all:
            capture(db, args.file, FILTR, SORTIROVKA, PREDEL)
            return
        query = {"service": "payments", "level": "error", "duration_ms": {"$gt": 500}}
        cases = [
            ("plan-1.json", None, query, [("ts", -1)], 0),
            ("plan-2.json", [("service", 1), ("level", 1), ("ts", -1), ("duration_ms", 1)], query, [("ts", -1)], 0),
            ("plan-3a.json", [("duration_ms", 1), ("service", 1), ("level", 1), ("ts", -1)], query, [("ts", -1)], 0),
            ("plan-3b.json", [("service", 1), ("level", 1), ("duration_ms", 1), ("ts", -1)], query, [("ts", -1)], 0),
            ("plan-4-bez.json", None, FILTR, SORTIROVKA, PREDEL),
            ("plan-4.json", [("level", 1), ("duration_ms", -1)], FILTR, SORTIROVKA, PREDEL),
        ]
        summaries = []
        for filename, index, filtr, sort, limit in cases:
            db[KOLLEKCIYA].drop_indexes()
            if index:
                db[KOLLEKCIYA].create_index(index)
            summaries.append(capture(db, filename, filtr, sort, limit))
        (ROOT / "measurements.json").write_text(
            json.dumps({"mongodb": client.server_info()["version"], "plans": summaries},
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

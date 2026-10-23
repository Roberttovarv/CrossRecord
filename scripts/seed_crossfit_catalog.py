"""Idempotently seed the CrossFit movement catalog.

Run with MONGO_URI and MONGO_DATABASE set. The script never deletes catalog
documents or athlete records; repeat runs update only this catalog's metadata.
"""
import argparse
import os
import sys
from pathlib import Path

from pymongo import MongoClient

# Running a script by path puts `scripts/` first in sys.path. Add the repository
# root explicitly so this tool works with Pipenv and Vercel env run alike.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db.connection import create_indexes, now


def movement(slug, name, domain, family, equipment, variations):
    return {"slug": slug, "name": name, "domain": domain, "family": family, "equipment": equipment, "variations": variations}


# variation: slug, display name, record kind, equipment, record enabled
CATALOG = [
    movement("squat", "Squat", "weightlifting", "squat", ["bodyweight", "barbell"], [
        ("air-squat", "Air Squat", "calisthenic", ["bodyweight"], True), ("back-squat", "Back Squat", "weighted", ["barbell"], True), ("front-squat", "Front Squat", "weighted", ["barbell"], True), ("overhead-squat", "Overhead Squat", "weighted", ["barbell"], True), ("zercher-squat", "Zercher Squat", "weighted", ["barbell"], True), ("box-squat", "Box Squat", "weighted", ["barbell", "box"], True),
    ]),
    movement("deadlift", "Deadlift", "weightlifting", "hinge", ["barbell"], [
        ("barbell-deadlift", "Barbell Deadlift", "weighted", ["barbell"], True), ("sumo-deadlift", "Sumo Deadlift", "weighted", ["barbell"], True), ("romanian-deadlift", "Romanian Deadlift", "weighted", ["barbell"], True), ("deficit-deadlift", "Deficit Deadlift", "weighted", ["barbell", "plates"], True), ("dumbbell-deadlift", "Dumbbell Deadlift", "weighted", ["dumbbell"], True), ("kettlebell-deadlift", "Kettlebell Deadlift", "weighted", ["kettlebell"], True), ("trap-bar-deadlift", "Trap Bar Deadlift", "weighted", ["trap-bar"], True),
    ]),
    movement("press", "Press", "weightlifting", "press", ["barbell"], [
        ("strict-press", "Strict Press", "weighted", ["barbell"], True), ("push-press", "Push Press", "weighted", ["barbell"], True), ("push-jerk", "Push Jerk", "weighted", ["barbell"], True), ("split-jerk", "Split Jerk", "weighted", ["barbell"], True), ("bench-press", "Bench Press", "weighted", ["barbell", "bench"], True), ("floor-press", "Floor Press", "weighted", ["barbell"], True),
    ]),
    movement("lunge", "Lunge", "weightlifting", "lunge", ["bodyweight", "barbell", "dumbbell"], [
        ("walking-lunge", "Walking Lunge", "calisthenic", ["bodyweight"], True), ("barbell-front-rack-lunge", "Barbell Front Rack Lunge", "weighted", ["barbell"], True), ("barbell-overhead-lunge", "Barbell Overhead Lunge", "weighted", ["barbell"], True), ("dumbbell-walking-lunge", "Dumbbell Walking Lunge", "weighted", ["dumbbell"], True), ("reverse-lunge", "Reverse Lunge", "calisthenic", ["bodyweight"], True),
    ]),
    movement("clean", "Clean", "weightlifting", "clean", ["barbell", "dumbbell", "kettlebell"], [
        ("barbell-clean", "Barbell Clean", "weighted", ["barbell"], True), ("power-clean", "Power Clean", "weighted", ["barbell"], True), ("squat-clean", "Squat Clean", "weighted", ["barbell"], True), ("hang-clean", "Hang Clean", "weighted", ["barbell"], True), ("hang-power-clean", "Hang Power Clean", "weighted", ["barbell"], True), ("dumbbell-clean", "Dumbbell Clean", "weighted", ["dumbbell"], True), ("dumbbell-hang-clean", "Dumbbell Hang Clean", "weighted", ["dumbbell"], True), ("kettlebell-clean", "Kettlebell Clean", "weighted", ["kettlebell"], True),
    ]),
    movement("jerk", "Jerk", "weightlifting", "jerk", ["barbell", "dumbbell"], [
        ("barbell-jerk", "Barbell Jerk", "weighted", ["barbell"], True), ("power-jerk", "Power Jerk", "weighted", ["barbell"], True), ("split-jerk-variation", "Split Jerk", "weighted", ["barbell"], True), ("dumbbell-push-jerk", "Dumbbell Push Jerk", "weighted", ["dumbbell"], True),
    ]),
    movement("clean-and-jerk", "Clean and Jerk", "weightlifting", "clean-and-jerk", ["barbell", "dumbbell"], [
        ("barbell-clean-and-jerk", "Barbell Clean and Jerk", "weighted", ["barbell"], True), ("power-clean-and-push-jerk", "Power Clean and Push Jerk", "weighted", ["barbell"], True), ("dumbbell-clean-and-jerk", "Dumbbell Clean and Jerk", "weighted", ["dumbbell"], True),
    ]),
    movement("snatch", "Snatch", "weightlifting", "snatch", ["barbell", "dumbbell", "kettlebell"], [
        ("barbell-snatch", "Barbell Snatch", "weighted", ["barbell"], True), ("power-snatch", "Power Snatch", "weighted", ["barbell"], True), ("hang-snatch", "Hang Snatch", "weighted", ["barbell"], True), ("hang-power-snatch", "Hang Power Snatch", "weighted", ["barbell"], True), ("dumbbell-snatch", "Dumbbell Snatch", "weighted", ["dumbbell"], True), ("alternating-dumbbell-snatch", "Alternating Dumbbell Snatch", "weighted", ["dumbbell"], True), ("kettlebell-snatch", "Kettlebell Snatch", "weighted", ["kettlebell"], True), ("snatch-balance", "Snatch Balance", "weighted", ["barbell"], True),
    ]),
    movement("thruster", "Thruster", "weightlifting", "squat-to-press", ["barbell", "dumbbell", "kettlebell"], [
        ("barbell-thruster", "Barbell Thruster", "weighted", ["barbell"], True), ("dumbbell-thruster", "Dumbbell Thruster", "weighted", ["dumbbell"], True), ("kettlebell-thruster", "Kettlebell Thruster", "weighted", ["kettlebell"], True),
    ]),
    movement("dumbbell", "Dumbbell Movements", "weightlifting", "dumbbell", ["dumbbell"], [
        ("dumbbell-front-squat", "Dumbbell Front Squat", "weighted", ["dumbbell"], True), ("dumbbell-push-press", "Dumbbell Push Press", "weighted", ["dumbbell"], True), ("dumbbell-overhead-squat", "Dumbbell Overhead Squat", "weighted", ["dumbbell"], True), ("devil-press", "Devil Press", "weighted", ["dumbbell"], True), ("dumbbell-turkish-get-up", "Dumbbell Turkish Get-up", "weighted", ["dumbbell"], True),
    ]),
    movement("kettlebell", "Kettlebell Movements", "weightlifting", "kettlebell", ["kettlebell"], [
        ("russian-kettlebell-swing", "Russian Kettlebell Swing", "weighted", ["kettlebell"], True), ("american-kettlebell-swing", "American Kettlebell Swing", "weighted", ["kettlebell"], True), ("goblet-squat", "Goblet Squat", "weighted", ["kettlebell"], True), ("kettlebell-press", "Kettlebell Press", "weighted", ["kettlebell"], True), ("kettlebell-turkish-get-up", "Kettlebell Turkish Get-up", "weighted", ["kettlebell"], True),
    ]),
    movement("pull-up", "Pull-up", "gymnastics", "pull", ["pull-up-bar", "band"], [
        ("strict-pull-up", "Strict Pull-up", "calisthenic", ["pull-up-bar"], True), ("kipping-pull-up", "Kipping Pull-up", "calisthenic", ["pull-up-bar"], True), ("butterfly-pull-up", "Butterfly Pull-up", "calisthenic", ["pull-up-bar"], True), ("chest-to-bar-pull-up", "Chest-to-Bar Pull-up", "calisthenic", ["pull-up-bar"], True), ("strict-chest-to-bar-pull-up", "Strict Chest-to-Bar Pull-up", "calisthenic", ["pull-up-bar"], True), ("banded-pull-up", "Banded Pull-up", "calisthenic", ["pull-up-bar", "band"], True),
    ]),
    movement("muscle-up", "Muscle-up", "gymnastics", "muscle-up", ["rings", "pull-up-bar"], [
        ("ring-muscle-up", "Ring Muscle-up", "calisthenic", ["rings"], True), ("strict-ring-muscle-up", "Strict Ring Muscle-up", "calisthenic", ["rings"], True), ("bar-muscle-up", "Bar Muscle-up", "calisthenic", ["pull-up-bar"], True), ("strict-bar-muscle-up", "Strict Bar Muscle-up", "calisthenic", ["pull-up-bar"], True),
    ]),
    movement("push-up", "Push-up", "gymnastics", "push", ["bodyweight", "rings"], [
        ("standard-push-up", "Standard Push-up", "calisthenic", ["bodyweight"], True), ("hand-release-push-up", "Hand-release Push-up", "calisthenic", ["bodyweight"], True), ("deficit-push-up", "Deficit Push-up", "calisthenic", ["plates"], True), ("ring-push-up", "Ring Push-up", "calisthenic", ["rings"], True), ("pike-push-up", "Pike Push-up", "calisthenic", ["bodyweight"], True),
    ]),
    movement("handstand", "Handstand", "gymnastics", "inversion", ["wall", "parallettes"], [
        ("handstand-hold", "Handstand Hold", "calisthenic", ["wall"], True), ("wall-walk", "Wall Walk", "calisthenic", ["wall"], True), ("strict-handstand-push-up", "Strict Handstand Push-up", "calisthenic", ["wall"], True), ("kipping-handstand-push-up", "Kipping Handstand Push-up", "calisthenic", ["wall"], True), ("deficit-handstand-push-up", "Deficit Handstand Push-up", "calisthenic", ["wall", "parallettes"], True), ("handstand-walk", "Handstand Walk", "calisthenic", ["floor"], True),
    ]),
    movement("dip", "Dip", "gymnastics", "dip", ["rings", "bar"], [
        ("bar-dip", "Bar Dip", "calisthenic", ["bar"], True), ("ring-dip", "Ring Dip", "calisthenic", ["rings"], True), ("strict-ring-dip", "Strict Ring Dip", "calisthenic", ["rings"], True), ("bench-dip", "Bench Dip", "calisthenic", ["bench"], True),
    ]),
    movement("rope-climb", "Rope Climb", "gymnastics", "climb", ["rope"], [
        ("rope-climb-with-legs", "Rope Climb with Legs", "calisthenic", ["rope"], True), ("legless-rope-climb", "Legless Rope Climb", "calisthenic", ["rope"], True), ("seated-rope-climb", "Seated Rope Climb", "calisthenic", ["rope"], True),
    ]),
    movement("rings", "Ring Movements", "gymnastics", "rings", ["rings"], [
        ("ring-row", "Ring Row", "calisthenic", ["rings"], True), ("ring-support-hold", "Ring Support Hold", "calisthenic", ["rings"], False), ("skin-the-cat", "Skin the Cat", "calisthenic", ["rings"], True), ("toes-to-rings", "Toes-to-Rings", "calisthenic", ["rings"], True),
    ]),
    movement("hanging-core", "Hanging Core", "gymnastics", "core", ["pull-up-bar"], [
        ("knees-to-elbows", "Knees-to-Elbows", "calisthenic", ["pull-up-bar"], True), ("toes-to-bar", "Toes-to-Bar", "calisthenic", ["pull-up-bar"], True), ("strict-toes-to-bar", "Strict Toes-to-Bar", "calisthenic", ["pull-up-bar"], True), ("hanging-knee-raise", "Hanging Knee Raise", "calisthenic", ["pull-up-bar"], True), ("hanging-leg-raise", "Hanging Leg Raise", "calisthenic", ["pull-up-bar"], True), ("windshield-wiper", "Windshield Wiper", "calisthenic", ["pull-up-bar"], True),
    ]),
    movement("sit-up", "Sit-up", "core", "sit-up", ["abmat", "ghd"], [
        ("abmat-sit-up", "AbMat Sit-up", "calisthenic", ["abmat"], True), ("butterfly-sit-up", "Butterfly Sit-up", "calisthenic", ["bodyweight"], True), ("ghd-sit-up", "GHD Sit-up", "calisthenic", ["ghd"], True), ("weighted-sit-up", "Weighted Sit-up", "calisthenic", ["plate"], True),
    ]),
    movement("box", "Box Movements", "plyometric", "box", ["box"], [
        ("box-jump", "Box Jump", "calisthenic", ["box"], True), ("box-step-up", "Box Step-up", "calisthenic", ["box"], True), ("box-jump-over", "Box Jump-over", "calisthenic", ["box"], True), ("burpee-box-jump", "Burpee Box Jump", "calisthenic", ["box"], True), ("burpee-box-jump-over", "Burpee Box Jump-over", "calisthenic", ["box"], True),
    ]),
    movement("burpee", "Burpee", "plyometric", "burpee", ["bodyweight", "barbell"], [
        ("standard-burpee", "Standard Burpee", "calisthenic", ["bodyweight"], True), ("bar-facing-burpee", "Bar-facing Burpee", "calisthenic", ["barbell"], True), ("lateral-bar-burpee", "Lateral Bar Burpee", "calisthenic", ["barbell"], True), ("burpee-pull-up", "Burpee Pull-up", "calisthenic", ["pull-up-bar"], True), ("burpee-broad-jump", "Burpee Broad Jump", "calisthenic", ["floor"], True),
    ]),
    movement("medicine-ball", "Medicine Ball Movements", "plyometric", "medicine-ball", ["medicine-ball"], [
        ("wall-ball-shot", "Wall-ball Shot", "calisthenic", ["medicine-ball", "wall"], True), ("medicine-ball-clean", "Medicine-ball Clean", "weighted", ["medicine-ball"], True), ("slam-ball", "Slam Ball", "calisthenic", ["slam-ball"], True), ("medicine-ball-over-shoulder", "Medicine-ball Over Shoulder", "calisthenic", ["medicine-ball"], True),
    ]),
    movement("jump-rope", "Jump Rope", "monostructural", "jump-rope", ["jump-rope"], [
        ("single-under", "Single-under", "calisthenic", ["jump-rope"], True), ("double-under", "Double-under", "calisthenic", ["jump-rope"], True), ("cross-under", "Cross-under", "calisthenic", ["jump-rope"], True),
    ]),
    movement("carry", "Carries", "strongman", "carry", ["dumbbell", "kettlebell", "sandbag"], [
        ("farmer-carry", "Farmer Carry", "weighted", ["dumbbell"], False), ("suitcase-carry", "Suitcase Carry", "weighted", ["kettlebell"], False), ("sandbag-carry", "Sandbag Carry", "weighted", ["sandbag"], False), ("yoke-carry", "Yoke Carry", "weighted", ["yoke"], False),
    ]),
    movement("sled", "Sled", "strongman", "sled", ["sled"], [
        ("sled-push", "Sled Push", "weighted", ["sled"], False), ("sled-pull", "Sled Pull", "weighted", ["sled"], False), ("rope-sled-pull", "Rope Sled Pull", "weighted", ["sled", "rope"], False),
    ]),
    movement("run", "Run", "monostructural", "run", ["outdoor", "treadmill"], [
        ("outdoor-run", "Outdoor Run", "cardio", ["outdoor"], True), ("treadmill-run", "Treadmill Run", "cardio", ["treadmill"], True), ("trail-run", "Trail Run", "cardio", ["trail"], True), ("shuttle-run", "Shuttle Run", "cardio", ["floor"], True),
    ]),
    movement("row", "Row", "monostructural", "row", ["rower"], [("concept2-row", "Concept2 Row", "cardio", ["rower"], True)]),
    movement("bike", "Bike", "monostructural", "bike", ["bike"], [("assault-bike", "Assault Bike", "cardio", ["bike"], True), ("echo-bike", "Echo Bike", "cardio", ["bike"], True), ("stationary-bike", "Stationary Bike", "cardio", ["bike"], True)]),
    movement("skierg", "SkiErg", "monostructural", "ski", ["skierg"], [("concept2-skierg", "Concept2 SkiErg", "cardio", ["skierg"], True)]),
    movement("swim", "Swim", "monostructural", "swim", ["pool", "open-water"], [("pool-freestyle-swim", "Pool Freestyle Swim", "cardio", ["pool"], True), ("open-water-swim", "Open-water Swim", "cardio", ["open-water"], True)]),
]


def protocol(kind):
    return {"calisthenic": "max_reps", "weighted": "max_load", "cardio": "fastest_time"}[kind]


def seed(database, dry_run=False):
    result = {"exercises_created": 0, "exercises_updated": 0, "variations_created": 0, "variations_updated": 0, "variations_disabled": 0}
    for entry in CATALOG:
        kinds = sorted({variation[2] for variation in entry["variations"]})
        document = {key: entry[key] for key in ("slug", "name", "domain", "family", "equipment")}
        document.update({"aliases": [entry["name"].casefold()], "kind": kinds[0] if len(kinds) == 1 else "mixed", "record_kinds": kinds, "catalog_version": 1, "updated_at": now()})
        existing = database.exercises.find_one({"slug": entry["slug"]})
        if dry_run:
            result["exercises_created" if not existing else "exercises_updated"] += 1
            exercise_id = existing["_id"] if existing else None
        else:
            database.exercises.update_one({"slug": entry["slug"]}, {"$set": document, "$setOnInsert": {"created_at": now()}}, upsert=True)
            result["exercises_created" if not existing else "exercises_updated"] += 1
            exercise_id = database.exercises.find_one({"slug": entry["slug"]})["_id"]
        for slug, name, kind, equipment, enabled in entry["variations"]:
            variation = {"slug": slug, "name": name, "name_key": name.casefold(), "exercise_id": exercise_id, "kind": kind, "equipment": equipment, "aliases": [name.casefold()], "record_protocol": protocol(kind), "record_enabled": enabled, "catalog_version": 1, "updated_at": now()}
            existing = database.variations.find_one({"slug": slug})
            if dry_run:
                result["variations_created" if not existing else "variations_updated"] += 1
            else:
                database.variations.update_one({"slug": slug}, {"$set": variation, "$setOnInsert": {"created_at": now()}}, upsert=True)
                result["variations_created" if not existing else "variations_updated"] += 1
            if not enabled:
                result["variations_disabled"] += 1
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    uri = os.environ.get("MONGO_URI")
    if not uri:
        sys.exit("MONGO_URI is required")
    client = MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=15000)
    client.admin.command("ping")
    database = client[os.environ.get("MONGO_DATABASE", "crossrecord")]
    create_indexes(database)
    print(seed(database, args.dry_run))


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NPC & Place-name Generator
- Combines 2~3 place roots from plname_{type}.json to form a village name
- Picks human names from name_{type}.json
- Outputs "(Name) of (Place)" format
- Supports types: default|normal|basic (+ easy future patches like korean|chinese|nordic|slavic)
"""

from __future__ import annotations
import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import List, Dict, Any

# -----------------------------
# Data Models
# -----------------------------

@dataclass
class PlaceData:
    place_roots: List[str]

    @staticmethod
    def from_json(obj: Dict[str, Any], kind: str) -> "PlaceData":
        try:
            roots = obj[kind]["place_roots"]
        except KeyError as e:
            raise KeyError(f"Missing key in plname json for type '{kind}': {e}")
        if not isinstance(roots, list) or not roots:
            raise ValueError("place_roots must be a non-empty list")
        return PlaceData(place_roots=roots)


@dataclass
class NameData:
    male: List[str]
    female: List[str]

    @staticmethod
    def from_json(obj: Dict[str, Any], kind: str) -> "NameData":
        try:
            male = obj[kind]["male"]
            female = obj[kind]["female"]
        except KeyError as e:
            raise KeyError(f"Missing key in name json for type '{kind}': {e}")
        if not isinstance(male, list) or not isinstance(female, list):
            raise ValueError("male/female must be lists")
        if not male or not female:
            raise ValueError("male/female lists must be non-empty")
        return NameData(male=male, female=female)


# -----------------------------
# Core Generator
# -----------------------------

@dataclass
class GeneratorConfig:
    place_type: str = "default"
    name_type: str = "default"
    num_male: int = 5
    num_female: int = 5
    min_roots: int = 2
    max_roots: int = 3
    seed: int | None = None
    data_dir: str = "."


class NPCPlaceGenerator:
    def __init__(self, cfg: GeneratorConfig):
        self.cfg = cfg
        if cfg.seed is not None:
            random.seed(cfg.seed)

        # Resolve file paths
        self.places_path = os.path.join(cfg.data_dir, f"plname_{cfg.place_type}.json")
        self.names_path = os.path.join(cfg.data_dir, f"name_{cfg.name_type}.json")

        # Load json
        self.place_data = self._load_place_data(self.places_path, cfg.place_type)
        self.name_data = self._load_name_data(self.names_path, cfg.name_type)

    # ---- Loading helpers ----
    @staticmethod
    def _load_json(path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {path}: {e}")

    def _load_place_data(self, path: str, kind: str) -> PlaceData:
        obj = self._load_json(path)
        return PlaceData.from_json(obj, kind)

    def _load_name_data(self, path: str, kind: str) -> NameData:
        obj = self._load_json(path)
        return NameData.from_json(obj, kind)

    # ---- Generation ----
    @staticmethod
    def _tidy_place_name(raw: str) -> str:
        """
        Light phonotactic cleanup:
        - Capitalize first letter
        - Compress common double letters
        - Remove accidental triple letters
        - Normalize hyphens/spacing (we generate without spaces by default)
        """
        if not raw:
            return raw
        out = raw

        # Collapse triple letters (e.g., 'aa a' -> 'aa')
        for ch in list("abcdefghijklmnopqrstuvwxyz"):
            out = out.replace(ch*3, ch*2)

        # Mild double-letter smoothing
        for seq in ["tt", "ll", "ss", "ff", "rr", "mm", "nn"]:
            out = out.replace(seq, seq[0])

        # Capitalize first
        out = out[0].upper() + out[1:]
        return out

    def generate_place_name(self) -> str:
        k = random.randint(self.cfg.min_roots, self.cfg.max_roots)
        roots = random.sample(self.place_data.place_roots, k)
        raw = "".join(roots)
        return self._tidy_place_name(raw)

    @staticmethod
    def _pick_unique(src: List[str], n: int) -> List[str]:
        if n <= len(src):
            return random.sample(src, n)
        # If requested more than available, sample with replacement but keep as varied as possible
        result = []
        if src:
            pool = src[:]
            while len(result) < n:
                if not pool:
                    pool = src[:]
                choice = random.choice(pool)
                pool.remove(choice)
                result.append(choice)
        return result

    def generate_residents(self, village: str) -> Dict[str, List[str]]:
        males = self._pick_unique(self.name_data.male, self.cfg.num_male)
        females = self._pick_unique(self.name_data.female, self.cfg.num_female)
        males_fmt = [f"{m} of {village}" for m in males]
        females_fmt = [f"{f} of {village}" for f in females]
        return {"male": males_fmt, "female": females_fmt}

    def generate_bundle(self) -> Dict[str, Any]:
        village = self.generate_place_name()
        people = self.generate_residents(village)
        return {"village": village, "residents": people}


# -----------------------------
# CLI
# -----------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate a village name and NPC residents from JSON data files."
    )
    p.add_argument("--place-type", default="default", help="Place type (default|normal|basic|korean|...)")
    p.add_argument("--name-type", default="default", help="Name type (default|normal|basic|korean|...)")
    p.add_argument("--num-male", type=int, default=5, help="Number of male residents")
    p.add_argument("--num-female", type=int, default=5, help="Number of female residents")
    p.add_argument("--min-roots", type=int, default=2, help="Minimum # of roots for place name")
    p.add_argument("--max-roots", type=int, default=3, help="Maximum # of roots for place name")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    p.add_argument("--data-dir", default=".", help="Directory containing plname_*.json and name_*.json")
    p.add_argument("--format", choices=["text", "json", "csv"], default="text", help="Output format")
    return p

def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)
    cfg = GeneratorConfig(
        place_type=args.place_type,
        name_type=args.name_type,
        num_male=args.num_male,
        num_female=args.num_female,
        min_roots=args.min_roots,
        max_roots=args.max_roots,
        seed=args.seed,
        data_dir=args.data_dir,
    )
    gen = NPCPlaceGenerator(cfg)
    bundle = gen.generate_bundle()

    if args.format == "json":
        print(json.dumps(bundle, ensure_ascii=False, indent=2))
    elif args.format == "csv":
        # CSV with two columns: gender,name_of_place
        import csv
        w = csv.writer(sys.stdout)
        w.writerow(["gender", "name"])
        for m in bundle["residents"]["male"]:
            w.writerow(["male", m])
        for f in bundle["residents"]["female"]:
            w.writerow(["female", f])
    else:
        # text
        village = bundle["village"]
        print(f"Village: {village}")
        print("Residents:")
        for m in bundle["residents"]["male"]:
            print(f"  - {m}")
        for f in bundle["residents"]["female"]:
            print(f"  - {f}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

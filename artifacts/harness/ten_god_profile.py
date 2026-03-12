#!/usr/bin/env python3
"""
General ten-god family profiler for 사주 통변.

Usage:
  python3 ten_god_profile.py \
    --day-master 丙 \
    --stems 丙,丁,丙,壬 \
    --branches 寅,酉,辰,辰 \
    --luck-stems 辛 \
    --luck-branches 丑 \
    --year-stems 丙 \
    --year-branches 午 \
    --strength-model elite
"""

from __future__ import annotations

import argparse
import json
from collections import Counter

ELEMENT = {
    "甲": "목", "乙": "목",
    "丙": "화", "丁": "화",
    "戊": "토", "己": "토",
    "庚": "금", "辛": "금",
    "壬": "수", "癸": "수",
}

POLARITY = {
    "甲": "양", "乙": "음",
    "丙": "양", "丁": "음",
    "戊": "양", "己": "음",
    "庚": "양", "辛": "음",
    "壬": "양", "癸": "음",
}

# 생(生) cycle: 목→화→토→금→수→목
PRODUCES = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
CONTROLS = {"목": "토", "화": "금", "토": "수", "금": "목", "수": "화"}

HIDDEN = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# 계절(득령) 단순 판정용
SEASON_BY_BRANCH = {
    "寅": "목", "卯": "목", "辰": "목",
    "巳": "화", "午": "화", "未": "화",
    "申": "금", "酉": "금", "戌": "금",
    "亥": "수", "子": "수", "丑": "수",
}

# 통근(득지) 규칙: strong(20점), secondary(10점)
ROOTS = {
    "甲": {"strong": {"寅", "卯", "亥"}, "secondary": {"未", "辰"}},
    "乙": {"strong": {"卯", "未", "辰"}, "secondary": {"寅", "亥"}},
    "丙": {"strong": {"寅", "巳", "午"}, "secondary": {"未", "戌"}},
    "丁": {"strong": {"午", "未", "戌"}, "secondary": {"寅", "巳"}},
    "戊": {"strong": {"辰", "戌", "丑", "未"}, "secondary": {"寅", "巳", "午"}},
    "己": {"strong": {"午", "未", "辰", "戌", "丑"}, "secondary": {"寅", "巳"}},
    "庚": {"strong": {"申", "酉", "巳"}, "secondary": {"戌", "丑"}},
    "辛": {"strong": {"酉", "申", "戌", "丑"}, "secondary": {"巳"}},
    "壬": {"strong": {"亥", "子", "申"}, "secondary": {"丑", "辰"}},
    "癸": {"strong": {"子", "丑", "辰"}, "secondary": {"亥", "申"}},
}


def split_csv(v: str) -> list[str]:
    if not v:
        return []
    return [x.strip() for x in v.split(",") if x.strip()]


def relation(day_master: str, target: str) -> str:
    dm_e = ELEMENT[day_master]
    dm_p = POLARITY[day_master]
    tg_e = ELEMENT[target]
    tg_p = POLARITY[target]

    same_polarity = dm_p == tg_p

    # same element
    if dm_e == tg_e:
        return "비견" if same_polarity else "겁재"

    # output (day master produces target)
    if PRODUCES[dm_e] == tg_e:
        return "식신" if same_polarity else "상관"

    # wealth (day master controls target)
    if CONTROLS[dm_e] == tg_e:
        return "편재" if same_polarity else "정재"

    # officer (target controls day master)
    if CONTROLS[tg_e] == dm_e:
        return "편관" if same_polarity else "정관"

    # resource (target produces day master)
    if PRODUCES[tg_e] == dm_e:
        return "편인" if same_polarity else "정인"

    raise ValueError(f"Unexpected relation: {day_master} vs {target}")


def compute_profile(day_master: str, stems: list[str], branches: list[str], hidden_weight: float):
    c = Counter()

    for s in stems:
        if s in ELEMENT:
            c[relation(day_master, s)] += 1.0

    for b in branches:
        for hs in HIDDEN.get(b, []):
            c[relation(day_master, hs)] += hidden_weight

    families = {
        "비겁": round(c["비견"] + c["겁재"], 3),
        "식상": round(c["식신"] + c["상관"], 3),
        "재성": round(c["편재"] + c["정재"], 3),
        "관성": round(c["편관"] + c["정관"], 3),
        "인성": round(c["편인"] + c["정인"], 3),
    }

    detail = {k: round(v, 3) for k, v in c.items()}
    return families, detail


def _deukryeong_score(day_master: str, month_branch: str) -> tuple[float, str]:
    season_element = SEASON_BY_BRANCH.get(month_branch)
    if not season_element:
        return 0.0, "월지 정보 없음"

    dm_e = ELEMENT[day_master]
    if dm_e == season_element:
        return 30.0, "득령(30)"

    # 계절 오행이 일간을 생하면 부분 가점
    if PRODUCES[season_element] == dm_e:
        return 20.0, "생조 계절(20)"

    # 일간이 계절 오행을 생하면 설기
    if PRODUCES[dm_e] == season_element:
        return 10.0, "설기 계절(10)"

    return 0.0, "비득령(0)"


def _deukji_score(day_master: str, day_branch: str) -> tuple[float, str]:
    rule = ROOTS.get(day_master)
    if not rule:
        return 0.0, "통근 규칙 없음"

    if day_branch in rule["strong"]:
        return 20.0, "득지 강근(20)"
    if day_branch in rule["secondary"]:
        return 10.0, "득지 약근(10)"
    return 0.0, "비득지(0)"


def _helper_ratio_score(day_master: str, stems: list[str], branches: list[str], hidden_weight: float) -> tuple[float, float, float]:
    """
    득세(0~30): 비겁+인성의 비율로 산정.
    - day stem(일간 본체)은 제외해서 과대평가를 줄인다.
    """
    rel_counter = Counter()

    for i, s in enumerate(stems):
        if s not in ELEMENT:
            continue
        if i == 2:  # day stem 본체 제외
            continue
        rel_counter[relation(day_master, s)] += 1.0

    for b in branches:
        for hs in HIDDEN.get(b, []):
            rel_counter[relation(day_master, hs)] += hidden_weight

    helper = rel_counter["비견"] + rel_counter["겁재"] + rel_counter["편인"] + rel_counter["정인"]
    total = sum(rel_counter.values())
    if total <= 0:
        return 0.0, 0.0, 0.0

    ratio = helper / total
    score = round(ratio * 30.0, 3)
    return score, round(helper, 3), round(total, 3)


def elite_strength_score(day_master: str, stems: list[str], branches: list[str], hidden_weight: float) -> dict:
    month_branch = branches[1] if len(branches) > 1 else ""
    day_branch = branches[2] if len(branches) > 2 else ""

    s1, s1_label = _deukryeong_score(day_master, month_branch)
    s2, s2_label = _deukji_score(day_master, day_branch)
    s3, helper, total = _helper_ratio_score(day_master, stems, branches, hidden_weight)

    score_80 = round(s1 + s2 + s3, 3)
    score_100 = round(score_80 * 100.0 / 80.0, 3)

    if score_80 >= 50:
        verdict = "신강(우세)"
    elif score_80 >= 45:
        verdict = "중화(균형권)"
    else:
        verdict = "신약(보완 필요)"

    return {
        "model": "elite_v1",
        "score_80": score_80,
        "score_100": score_100,
        "verdict": verdict,
        "components": {
            "deukryeong": {"score": s1, "rule": s1_label, "month_branch": month_branch},
            "deukji": {"score": s2, "rule": s2_label, "day_branch": day_branch},
            "deukse": {
                "score": s3,
                "helper_sum": helper,
                "total_sum": total,
                "method": "(비겁+인성)/전체 * 30",
            },
        },
        "notes": [
            "근거 프레임: 득령/득지/득세 + 중화 기준(약 45) 참고",
            "실전 통변은 합충형파해/격국/용신 판단과 함께 사용 권장",
        ],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--day-master", required=True)
    p.add_argument("--stems", required=True)
    p.add_argument("--branches", required=True)
    p.add_argument("--luck-stems", default="")
    p.add_argument("--luck-branches", default="")
    p.add_argument("--year-stems", default="")
    p.add_argument("--year-branches", default="")
    p.add_argument("--hidden-weight", type=float, default=0.5)
    p.add_argument("--strength-model", choices=["none", "elite"], default="elite")
    args = p.parse_args()

    dm = args.day_master.strip()
    if dm not in ELEMENT:
        raise SystemExit(f"Unsupported day-master: {dm}")

    base_stems = split_csv(args.stems)
    base_branches = split_csv(args.branches)
    luck_stems = split_csv(args.luck_stems)
    luck_branches = split_csv(args.luck_branches)
    year_stems = split_csv(args.year_stems)
    year_branches = split_csv(args.year_branches)

    b_f, b_d = compute_profile(dm, base_stems, base_branches, args.hidden_weight)
    l_f, l_d = compute_profile(dm, base_stems + luck_stems, base_branches + luck_branches, args.hidden_weight)
    y_f, y_d = compute_profile(
        dm,
        base_stems + luck_stems + year_stems,
        base_branches + luck_branches + year_branches,
        args.hidden_weight,
    )

    out = {
        "input": {
            "day_master": dm,
            "base": {"stems": base_stems, "branches": base_branches},
            "luck": {"stems": luck_stems, "branches": luck_branches},
            "year": {"stems": year_stems, "branches": year_branches},
            "hidden_weight": args.hidden_weight,
            "strength_model": args.strength_model,
        },
        "profiles": {
            "base": {"families": b_f, "detail": b_d},
            "base_plus_luck": {"families": l_f, "detail": l_d},
            "base_plus_luck_plus_year": {"families": y_f, "detail": y_d},
        },
    }

    if args.strength_model == "elite":
        out["strength"] = {
            "base": elite_strength_score(dm, base_stems, base_branches, args.hidden_weight),
            "base_plus_luck": elite_strength_score(
                dm,
                base_stems + luck_stems,
                base_branches + luck_branches,
                args.hidden_weight,
            ),
            "base_plus_luck_plus_year": elite_strength_score(
                dm,
                base_stems + luck_stems + year_stems,
                base_branches + luck_branches + year_branches,
                args.hidden_weight,
            ),
        }

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

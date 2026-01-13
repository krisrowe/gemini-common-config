"""SDK for pattern-based secret detection testing."""
import math
import random
from collections import Counter
from pathlib import Path
from typing import Optional

import yaml


def generate_from_pattern(pattern: str, rng: random.Random) -> str:
    """Generate string from regex subset: literals, [a-z], {n}, {n,m}, \\d, \\w"""
    result, i = [], 0
    while i < len(pattern):
        if pattern[i] == '[':
            j = pattern.index(']', i)
            chars = _expand_charset(pattern[i+1:j])
            i, count = j + 1, 1
        elif pattern[i] == '\\' and i + 1 < len(pattern) and pattern[i+1] in 'dw':
            chars = '0123456789' if pattern[i+1] == 'd' else \
                    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
            i, count = i + 2, 1
        else:
            result.append(pattern[i])
            i += 1
            continue
        if i < len(pattern) and pattern[i] == '{':
            j = pattern.index('}', i)
            q = pattern[i+1:j].split(',')
            count = rng.randint(int(q[0]), int(q[-1]))
            i = j + 1
        result.append(''.join(rng.choice(chars) for _ in range(count)))
    return ''.join(result)


def _expand_charset(spec: str) -> str:
    """Expand character class spec like a-zA-Z0-9 into full string."""
    chars, i = [], 0
    while i < len(spec):
        if i + 2 < len(spec) and spec[i+1] == '-':
            chars.extend(chr(c) for c in range(ord(spec[i]), ord(spec[i+2]) + 1))
            i += 3
        else:
            chars.append(spec[i])
            i += 1
    return ''.join(chars)


def shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def get_pattern_exception(s: str) -> Optional[str]:
    """Return exception reason if string matches an exclusion pattern."""
    if s.isalpha():
        return "all-alpha"
    if all(c.islower() or c == '_' for c in s):
        return "lower_snake"
    if all(c.isupper() or c == '_' for c in s):
        return "UPPER_SNAKE"
    if all(c.islower() or c == '.' for c in s):
        return "lower_dot"
    if all(c.islower() or c == '/' for c in s):
        return "lower_slash"
    return None


def check_secret(s: str, min_len: int = 8, entropy_threshold: float = 3.5) -> dict:
    """
    Check if a string should be flagged as a potential secret.

    Returns dict with: flagged, entropy, exception, reason
    """
    entropy = shannon_entropy(s)
    exception = get_pattern_exception(s)

    if len(s) < min_len:
        return {
            "flagged": False,
            "entropy": entropy,
            "exception": exception,
            "reason": f"len={len(s)}<{min_len}"
        }

    if exception:
        return {
            "flagged": False,
            "entropy": entropy,
            "exception": exception,
            "reason": exception
        }

    if entropy > entropy_threshold:
        return {
            "flagged": True,
            "entropy": entropy,
            "exception": None,
            "reason": f"entropy={entropy:.2f}>{entropy_threshold}"
        }

    return {
        "flagged": False,
        "entropy": entropy,
        "exception": None,
        "reason": f"entropy={entropy:.2f}<={entropy_threshold}"
    }


def load_patterns(patterns_path: Optional[Path] = None) -> dict:
    """Load patterns from YAML file."""
    if patterns_path is None:
        patterns_path = Path(__file__).parent.parent / "patterns.yaml"

    with open(patterns_path) as f:
        return yaml.safe_load(f)


def test_patterns(seed: Optional[int] = None, patterns_path: Optional[Path] = None) -> dict:
    """
    Load patterns, generate examples, and test them.

    Returns dict with:
      - seed: random seed used
      - results: list of test results
      - summary: counts of pass/fail/correct/incorrect
    """
    data = load_patterns(patterns_path)
    seed = seed if seed is not None else data.get("seed", 42)
    rng = random.Random(seed)

    results = []
    for p in data.get("patterns", []):
        example = generate_from_pattern(p["pattern"], rng)
        check = check_secret(example)

        expect_flag = p.get("expect") == "flag"
        actual_flag = check["flagged"]
        correct = expect_flag == actual_flag

        results.append({
            "id": p.get("id", ""),
            "type": p.get("type", p.get("id", "")),
            "pattern": p["pattern"],
            "example": example,
            "description": p.get("description", ""),
            "expect": p.get("expect", "pass"),
            "flagged": actual_flag,
            "correct": correct,
            "entropy": check["entropy"],
            "exception": check["exception"],
            "reason": check["reason"],
        })

    # Sort: by flagged (True first), then by has exception (None first), then by entropy desc
    def sort_key(r):
        flag_order = 0 if r["flagged"] else 1
        exc_order = 1 if r["exception"] else 0
        return (flag_order, exc_order, -r["entropy"])

    results.sort(key=sort_key)

    # Summary
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    flagged = sum(1 for r in results if r["flagged"])
    expected_flags = sum(1 for r in results if r["expect"] == "flag")

    true_pos = sum(1 for r in results if r["flagged"] and r["expect"] == "flag")
    false_pos = sum(1 for r in results if r["flagged"] and r["expect"] == "pass")
    true_neg = sum(1 for r in results if not r["flagged"] and r["expect"] == "pass")
    false_neg = sum(1 for r in results if not r["flagged"] and r["expect"] == "flag")

    precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
    recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0

    return {
        "seed": seed,
        "results": results,
        "summary": {
            "total": total,
            "correct": correct,
            "accuracy": correct / total if total > 0 else 0,
            "flagged": flagged,
            "expected_flags": expected_flags,
            "true_positives": true_pos,
            "false_positives": false_pos,
            "true_negatives": true_neg,
            "false_negatives": false_neg,
            "precision": precision,
            "recall": recall,
        }
    }

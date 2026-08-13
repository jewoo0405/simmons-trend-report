import statistics
import math


def remove_outliers_mad(samples):
    if len(samples) < 3:
        return samples, 0
    med = statistics.median(samples)
    mad = statistics.median([abs(x - med) for x in samples])
    if mad == 0:
        return samples, 0
    threshold = 3.0
    clean = [x for x in samples if abs(x - med) / (mad * 1.4826) <= threshold]
    removed = len(samples) - len(clean)
    return (clean if clean else samples), removed


def cv_confidence(cv):
    if cv <= 0.05:
        return "stable"
    elif cv <= 0.15:
        return "warning"
    return "unstable"


def summarize(samples):
    clean, removed = remove_outliers_mad(samples)
    if not clean:
        return {"median": 0, "mean": 0, "std": 0, "cv": 0,
                "confidence": "unstable", "outliers_removed": removed}
    med = statistics.median(clean)
    mean = statistics.mean(clean)
    std = statistics.stdev(clean) if len(clean) > 1 else 0
    cv = (std / mean) if mean > 0 else 0
    return {
        "median": round(med, 2),
        "mean": round(mean, 2),
        "std": round(std, 2),
        "cv": round(cv, 4),
        "confidence": cv_confidence(cv),
        "outliers_removed": removed,
    }


def overall_confidence_score(summaries_list):
    if not summaries_list:
        return 0
    stable = sum(1 for s in summaries_list if s["confidence"] == "stable")
    warning = sum(1 for s in summaries_list if s["confidence"] == "warning")
    total = len(summaries_list)
    score = round((stable * 100 + warning * 50) / total)
    return min(score, 100)

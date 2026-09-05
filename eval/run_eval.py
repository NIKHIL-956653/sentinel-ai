"""
SENTINEL AI — evaluation harness.

Measures the verification pipeline against eval/dataset.json (synthetic, labelled):
  1. Story clustering  — pairwise precision / recall / F1 of "same story" decisions
  2. Verdict rule      — accuracy of VerifierAgent.verdict_for
  3. Contradictions    — precision / recall / F1 for the keyword heuristic and (with a key) the LLM judge

Usage:
  python eval/run_eval.py            # everything (LLM judge needs OPENROUTER_API_KEY)
  python eval/run_eval.py --offline  # skip the LLM judge (CI)
Writes eval/results.json.
"""
import argparse
import itertools
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("MONGODB_URI", "mongodb://127.0.0.1:1")  # never touch a real DB from the eval

from tools.confidence_scorer import group_similar_articles          # noqa: E402
from agents.verifier_agent import VerifierAgent                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return round(p, 3), round(r, 3), round(f, 3)


# ── 1. clustering ────────────────────────────────────────────────────────────
def eval_clustering(cases):
    tp = fp = fn = 0
    for case in cases:
        arts = [{"title": h["title"], "source": f"s{i}.example"} for i, h in enumerate(case["headlines"])]
        groups = group_similar_articles(arts)
        pred = {}
        for gid, g in enumerate(groups):
            for a in g["articles"]:
                pred[a["title"]] = gid
        gold = {h["title"]: h["cluster"] for h in case["headlines"]}
        for a, b in itertools.combinations(case["headlines"], 2):
            same_gold = gold[a["title"]] == gold[b["title"]]
            same_pred = pred[a["title"]] == pred[b["title"]]
            if same_gold and same_pred:
                tp += 1
            elif same_pred and not same_gold:
                fp += 1
            elif same_gold and not same_pred:
                fn += 1
    p, r, f = prf(tp, fp, fn)
    return {"pairs_tp": tp, "pairs_fp": fp, "pairs_fn": fn, "precision": p, "recall": r, "f1": f}


# ── 2. verdict rule ──────────────────────────────────────────────────────────
def eval_verdicts(cases):
    v = VerifierAgent()
    wrong = []
    for c in cases:
        trust = v.check_source_trust(c["sources"])
        got = v.verdict_for(trust, c["confidence"])
        if got != c["expected"]:
            wrong.append({"id": c["id"], "expected": c["expected"], "got": got})
    return {"total": len(cases), "correct": len(cases) - len(wrong),
            "accuracy": round((len(cases) - len(wrong)) / len(cases), 3), "wrong": wrong}


# ── 3. contradictions ────────────────────────────────────────────────────────
def _as_stories(pair):
    return [{"titles": [pair["a"]], "articles": []}, {"titles": [pair["b"]], "articles": []}]


def eval_contradictions(pairs, method):
    tp = fp = fn = 0
    errors = []
    latencies = []
    for pair in pairs:
        stories = _as_stories(pair)
        t0 = time.time()
        if method == "keyword":
            found = bool(VerifierAgent.check_contradictions_keyword(stories))
        else:
            found = bool(VerifierAgent.check_contradictions_llm(stories))
        latencies.append(time.time() - t0)
        if found and pair["contradict"]:
            tp += 1
        elif found and not pair["contradict"]:
            fp += 1; errors.append({"id": pair["id"], "type": "false_positive"})
        elif not found and pair["contradict"]:
            fn += 1; errors.append({"id": pair["id"], "type": "missed"})
    p, r, f = prf(tp, fp, fn)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f,
            "avg_latency_s": round(sum(latencies) / len(latencies), 2), "errors": errors}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="skip the LLM contradiction judge")
    args = ap.parse_args()

    data = json.load(open(os.path.join(HERE, "dataset.json"), encoding="utf-8"))
    results = {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "dataset_note": data["_about"]}

    results["clustering"] = eval_clustering(data["clustering"])
    results["verdicts"] = eval_verdicts(data["verdicts"])
    results["contradictions"] = {"keyword": eval_contradictions(data["contradictions"], "keyword")}

    if not args.offline and os.getenv("OPENROUTER_API_KEY"):
        from config import OPENROUTER_MODEL
        try:
            results["contradictions"]["llm"] = eval_contradictions(data["contradictions"], "llm")
            results["contradictions"]["llm"]["model"] = OPENROUTER_MODEL
        except Exception as e:  # network / key problems must not kill the report
            results["contradictions"]["llm"] = {"error": str(e)[:200]}
    else:
        results["contradictions"]["llm"] = {"skipped": "offline or no OPENROUTER_API_KEY"}

    out = os.path.join(HERE, "results.json")
    json.dump(results, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    c, v, k = results["clustering"], results["verdicts"], results["contradictions"]["keyword"]
    print("\n=== SENTINEL AI evaluation (synthetic set) ===")
    print(f"Story clustering   P={c['precision']}  R={c['recall']}  F1={c['f1']}   (pairs tp/fp/fn {c['pairs_tp']}/{c['pairs_fp']}/{c['pairs_fn']})")
    print(f"Verdict rule       accuracy={v['accuracy']}  ({v['correct']}/{v['total']})" + (f"  wrong={v['wrong']}" if v["wrong"] else ""))
    print(f"Contradiction/kw   P={k['precision']}  R={k['recall']}  F1={k['f1']}")
    l = results["contradictions"]["llm"]
    if "f1" in l:
        print(f"Contradiction/llm  P={l['precision']}  R={l['recall']}  F1={l['f1']}  ({l['model']}, {l['avg_latency_s']}s/pair)")
    else:
        print(f"Contradiction/llm  {l}")
    print(f"→ {out}")


if __name__ == "__main__":
    main()

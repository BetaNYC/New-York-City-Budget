"""
Stage 9 -- disclosure alignment, report-only (PLAN §3, H17, W2, W4).

Joins the PDF's award rows to the Council's expense disclosure
(data/fyNN/expense_disclosure/fyNN_expense_awards.csv) by the one join rule (DATA-ANOMALIES
§23): (EIN, amount) as a multiset; never EIN alone; never the council member. Rows on the
City's own EIN 13-6400434 also need a name check: the disclosure's legal name must be a prefix
of the PDF's organisation text (normalised), or two City agencies pair up by amount alone.

Allocation when a key has more candidates than claimants is the same deterministic order as
code/reconcile_disclosure_schedule_c.py (whose loaders and stream rules are reused): a body row
claims a non-appendix stream first and an appendix row its own stream, then Cleared before
Pending, then sheet order. Keys where that choice mattered are counted as ambiguous.

The disclosure is a later snapshot and includes post-adoption designations. It never changes
a PDF value. Every unmatched row gets one waterfall reason.
"""
import re
from collections import Counter, defaultdict
from decimal import Decimal

import reconcile_disclosure_schedule_c as rdsc

CITY_EIN = rdsc.CITY_EIN
PREFERS = {"body": ("speaker", "initiative"), "appendix_a": ("aging",),
           "appendix_b": ("local",), "appendix_c": ("youth",)}
ORDER = ("body", "appendix_a", "appendix_b", "appendix_c")


def norm_name(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def name_ok(ein, disc_name, sc_org):
    """The City-EIN name condition; every other EIN passes."""
    if ein != CITY_EIN:
        return True
    d = norm_name(disc_name)
    return bool(d) and norm_name(sc_org).startswith(d)


def align(awards, fy, name_rule=True):
    """Returns dict(matches, unmatched_sc, unmatched_disc, ambiguous, disc)."""
    disc = rdsc.load_disclosure(fy)
    by_key = defaultdict(list)
    for i, d in enumerate(disc):
        by_key[(d["ein"], d["amount"])].append(i)
    rank = {"cleared": 0, "pending": 1, "other": 2}
    taken, matches, unmatched = {}, {}, []
    for sec in ORDER:
        for a in sorted((a for a in awards if a["section"] == sec), key=lambda a: a["award_id"]):
            if not a["ein"] or a["amount"] is None:
                unmatched.append(a)
                continue
            cands = [i for i in by_key.get((a["ein"], Decimal(a["amount"])), ())
                     if i not in taken and (not name_rule or name_ok(a["ein"], disc[i]["name"], a["org"]))]
            if not cands:
                unmatched.append(a)
                continue
            cands.sort(key=lambda i: (disc[i]["stream"] not in PREFERS[sec],
                                      rank.get(disc[i]["status"], 3), disc[i]["row"]))
            taken[cands[0]] = a["award_id"]
            matches[a["award_id"]] = cands[0]
    ambiguous = set()
    for key, idxs in by_key.items():
        claimed = [i for i in idxs if i in taken]
        if claimed and len(claimed) < len(idxs) and \
                len({(disc[i]["stream"], disc[i]["status"]) for i in idxs}) > 1:
            ambiguous.update(idxs)

    # Waterfall reasons.
    disc_free = [i for i in range(len(disc)) if i not in taken]
    free_by_ein = defaultdict(list)
    for i in disc_free:
        free_by_ein[disc[i]["ein"]].append(i)
    sc_eins = {a["ein"] for a in awards if a["ein"]}
    any_key = {(d["ein"], d["amount"]) for d in disc}
    out_sc = []
    for a in unmatched:
        if not a["ein"] or a["amount"] is None:
            reason, near = "pdf_value_unreadable", ""
        elif (a["ein"], Decimal(a["amount"])) in any_key:
            if a["ein"] == CITY_EIN and any(
                    i not in taken for i in by_key[(a["ein"], Decimal(a["amount"]))]):
                reason = "city_ein_name_mismatch"
            else:
                reason = "key_already_claimed"
            near = ""
        elif free_by_ein.get(a["ein"]):
            amts = sorted({disc[i]["amount"] for i in free_by_ein[a["ein"]]},
                          key=lambda v: abs(v - Decimal(a["amount"])))
            reason = "amount_differs"
            near = amts[0]
        elif any(d["ein"] == a["ein"] for d in disc):
            reason, near = "ein_fully_claimed", ""
        else:
            reason, near = "ein_not_in_disclosure", ""
        out_sc.append(dict(award=a, reason=reason, nearest_disclosure_amount=near))
    out_disc = []
    for i in disc_free:
        d = disc[i]
        if d["ein"] == CITY_EIN and d["status"] == "pending":
            reason = "city_ein_pending"
        elif d["ein"] not in sc_eins:
            reason = "ein_not_in_pdf"
        else:
            reason = "amount_or_count_differs"
        out_disc.append(dict(disc=d, reason=reason))
    return dict(matches=matches, unmatched_sc=out_sc, unmatched_disc=out_disc,
                ambiguous=ambiguous, disc=disc, taken=taken)


def summary(result, awards):
    """Rows and dollars by section x status, plus reason counts."""
    disc, taken = result["disc"], result["taken"]
    by = Counter()
    for a in awards:
        i = result["matches"].get(a["award_id"])
        st = disc[i]["status"] if i is not None else "unmatched"
        by[(a["section"], st, "rows")] += 1
        by[(a["section"], st, "dollars")] += a["amount"] or 0
    return dict(
        pdf_rows=len(awards), matched=len(result["matches"]),
        disclosure_rows=len(disc),
        by=by,
        sc_reasons=Counter(u["reason"] for u in result["unmatched_sc"]),
        disc_reasons=Counter(u["reason"] for u in result["unmatched_disc"]),
        disc_reason_dollars=Counter({r: sum(u["disc"]["amount"] for u in
                                            result["unmatched_disc"] if u["reason"] == r)
                                     for r in {u["reason"] for u in result["unmatched_disc"]}}),
        ambiguous_rows=len(result["ambiguous"]))


def align_without_name_rule(awards, fy):
    """Matched-row count with the City-EIN name rule off: the 2026-10-19 prototype's measure,
    kept so the regression floor (PLAN H17) stays comparable."""
    return len(align(awards, fy, name_rule=False)["matches"])

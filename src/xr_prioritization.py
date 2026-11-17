"""Reference implementation of the context-aware EF prioritization framework.

Pure standard-library Python (no third-party dependency).

Model (see the article):
  W_{i,m}        = p_{i,m} / sum_k p_{k,m},   p_{i,m} = n_{i,m} / N_m          (Eqs. 3-4)
  W_Litt,i^(f)   = sum_d beta_d * W_{i, m_d(f)}                                 (Eq. 11)
  W_T,i^(f)      = alpha * W_indus,i + (1 - alpha) * W_Litt,i^(f)
  P_j^(f)        = sum_i W_T,i^(f) * R_ij / sum_k R_ik                          (Eq. 16, R row-normalised)
"""
import csv
import json
import os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

DIMENSIONS = ("xr_technology", "application_domain", "industrial_activity", "hardware_configuration")
XR_TECHNOLOGIES = ("AR", "VR")
DOMAINS = ("Design", "Production", "Maintenance")
ACTIVITIES = (
    "Assembly", "Maintenance and Repair", "Quality Control and Inspection", "Product Design",
    "System Design", "Operator Training", "Operator Assistance", "Industrial Safety Awareness",
    "Machine/Robot/Production-System Monitoring", "Ergonomic Evaluation",
)
HARDWARE_BY_TECHNOLOGY = {
    "AR": ("AR HMD only", "Handheld/Mobile XR Device only", "AR HMD + Handheld/Mobile XR Device only"),
    "VR": ("VR HMD only", "VR HMD + XR Controllers", "VR HMD + XR Controllers + Motion/Positional Tracking"),
}


def _read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def load():
    crs = _read_csv("customer_requirements.csv")
    efs = _read_csv("engineering_features.csv")
    rows = _read_csv("relationship_matrix.csv")
    studies = _read_csv("studies.csv")
    with open(os.path.join(DATA, "parameters.json"), encoding="utf8") as f:
        params = json.load(f)
    ef_ids = [e["id"] for e in efs]
    R = [[float(r[e] or 0) for e in ef_ids] for r in rows]
    assert [r["CR"] for r in rows] == [c["id"] for c in crs]
    for s in studies:
        s["activities"] = [a.strip() for a in s["industrial_activities"].split(";") if a.strip()]
        s["crs"] = [c.strip() for c in s["criteria"].split(",") if c.strip()]
    return {
        "crs": crs, "efs": efs, "R": R, "studies": studies, "params": params,
        "w_indus": [float(c["w_indus"]) for c in crs],
    }


def modality_weights(model, dimension, modality):
    """Return (W_{i,m} for the 37 CRs, N_m)."""
    def member(s):
        if dimension == "xr_technology":
            return s["xr_technology"] == modality
        if dimension == "application_domain":
            return s["application_domain"] == modality
        if dimension == "industrial_activity":
            return modality in s["activities"]
        if dimension == "hardware_configuration":
            return s["hardware_configuration"] == modality
        raise ValueError(dimension)

    sel = [s for s in model["studies"] if member(s)]
    ids = [c["id"] for c in model["crs"]]
    p = [sum(1 for s in sel if cid in s["crs"]) / len(sel) for cid in ids]
    total = sum(p)
    return [x / total for x in p], len(sel)


def valid_configurations():
    return [
        (t, h, d, a)
        for t in XR_TECHNOLOGIES for h in HARDWARE_BY_TECHNOLOGY[t] for d in DOMAINS for a in ACTIVITIES
    ]


def prioritize(model, technology, hardware, domain, activity, alpha=None, beta=None):
    alpha = model["params"]["alpha"] if alpha is None else alpha
    beta = model["params"]["beta"] if beta is None else beta
    chosen = {
        "xr_technology": technology, "application_domain": domain,
        "industrial_activity": activity, "hardware_configuration": hardware,
    }
    w_lit = [0.0] * 37
    support = {}
    for dim in DIMENSIONS:
        w, n = modality_weights(model, dim, chosen[dim])
        support[dim] = n
        for i in range(37):
            w_lit[i] += beta[dim] * w[i]
    w_t = [alpha * model["w_indus"][i] + (1 - alpha) * w_lit[i] for i in range(37)]
    raw = []
    for j in range(33):
        raw.append(sum(w_t[i] * model["R"][i][j] / sum(model["R"][i]) for i in range(37)))
    total = sum(raw)
    scores = [x / total for x in raw]
    order = sorted(range(33), key=lambda j: (-scores[j], j))
    ranking = [
        {"rank": k + 1, "id": model["efs"][j]["id"], "name": model["efs"][j]["name"], "score": scores[j]}
        for k, j in enumerate(order)
    ]
    return {"config": chosen, "support": support, "w_t": w_t, "w_lit": w_lit, "scores": scores, "ranking": ranking}


if __name__ == "__main__":
    import sys
    m = load()
    cfg = sys.argv[1:5] if len(sys.argv) >= 5 else ["VR", "VR HMD only", "Production", "Assembly"]
    res = prioritize(m, *cfg)
    print("Configuration:", " | ".join(cfg))
    for r in res["ranking"][:10]:
        print("%2d  %-5s %-60s %.4f" % (r["rank"], r["id"], r["name"], r["score"]))

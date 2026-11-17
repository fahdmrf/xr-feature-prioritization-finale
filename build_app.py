"""Build the single-file application app/index.html from the data/ folder and app/engine.js."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
import xr_prioritization as x  # noqa: E402


def main():
    m = x.load()
    data = {
        "params": m["params"],
        "crs": [{"id": c["id"], "name": c["name"], "w_indus": float(c["w_indus"])} for c in m["crs"]],
        "efs": [{"id": e["id"], "name": e["name"], "category": e["category"]} for e in m["efs"]],
        "R": [[int(v) for v in r] for r in m["R"]],
        "studies": [
            {"id": s["id"], "xr_technology": s["xr_technology"], "application_domain": s["application_domain"],
             "activities": s["activities"], "hardware_configuration": s["hardware_configuration"], "criteria": s["crs"]}
            for s in m["studies"]
        ],
    }
    with open(os.path.join(HERE, "app", "engine.js"), encoding="utf8") as f:
        engine = f.read()
    with open(os.path.join(HERE, "app", "app.template.html"), encoding="utf8") as f:
        html = f.read()
    html = html.replace("/*ENGINE*/", engine).replace("/*DATA*/", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    out = os.path.join(HERE, "app", "index.html")
    with open(out, "w", encoding="utf8") as f:
        f.write(html)
    print("wrote", out, "(%d bytes)" % len(html.encode("utf8")))


if __name__ == "__main__":
    main()

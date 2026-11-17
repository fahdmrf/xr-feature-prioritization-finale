# XR Engineering Feature Prioritization Tool

Companion tool of the article *"Prioritizing Industrial XR Engineering Features Across Technology and Application Domains"*.
Given an XR configuration, it computes context-specific Customer Requirement (CR) weights and ranks the 33 Engineering Features (EFs)
with the House of Quality (HoQ) model described in the article.

**Use it online or locally:** open `app/index.html` in any modern browser. It is a single file, works offline, and has no dependency.

## Model

For a configuration *f* (XR technology, XR hardware, application domain, industrial activity):

| Step | Formula |
|---|---|
| Modality weight of CR *i* | `W_{i,m} = p_{i,m} / Σ_k p_{k,m}`, with `p_{i,m} = n_{i,m} / N_m` (occurrence rate in the 55 studies) |
| Literature-based weight | `W_Litt,i = Σ_d β_d · W_{i,m_d(f)}` over the four dimensions |
| Total CR weight | `W_T,i = α · W_indus,i + (1 − α) · W_Litt,i` |
| EF priority | `P_j = Σ_i W_T,i · R_ij / Σ_k R_ik`, normalised so that `Σ_j P_j = 1` |

Parameters (article, Section 4): `α = 0.1462`, `β = [0.259289, 0.255971, 0.303744, 0.180996]`
(XR technology, application domain, industrial activity, hardware configuration).
The CR–EF matrix `R` (0–5) is row-normalised before the priorities are computed.

The valid configurations are the 180 combinations of 2 XR technologies × 3 hardware configurations compatible with each technology ×
3 application domains × 10 industrial activities. Modalities supported by fewer than 4 studies (for example *Industrial Safety Awareness*, n = 1)
are flagged in the interface.

## Repository layout

```
app/index.html               single-file application (generated, committed)
app/engine.js                calculation engine (pure functions, also used by index.html)
app/app.template.html        interface template
build_app.py                 builds app/index.html from data/ and app/engine.js
data/customer_requirements.csv   37 CRs and their industrial weights W_indus (article, Table B1)
data/engineering_features.csv    33 EFs and their categories
data/relationship_matrix.csv     CR–EF relationship matrix R (article, Table A2)
data/studies.csv                 classification of the 55 studies (article, Supplementary Table S2)
data/parameters.json             α and β
src/xr_prioritization.py     reference implementation (standard library only)
tests/                       reproduction and cross-check tests
```

`data/` is the single source of truth: change a value there, run `python build_app.py`, and the application is regenerated.

## Reproducing the article

```bash
python src/xr_prioritization.py "VR" "VR HMD only" "Production" "Assembly"   # example of the article
python -m unittest discover -s tests -v                                      # all tests (Python 3, Node.js)
```

The tests check that:

* the data have the expected dimensions (37 CRs, 33 EFs, 55 studies, 355 non-zero relationships) and the parameters are consistent;
* the number of studies per modality is the one reported in the article (AR 31, VR 16, Design 9, Production 37, Maintenance 9, Assembly 17, ...);
* the example configuration (VR · VR HMD only · Production · Assembly) gives the Top-10 EFs of the article, in the same order, with scores within `1.5e-4`
  (the industrial weights printed in Table B1 are rounded to four decimals);
* over the 180 configurations, scores sum to 1, EF14 is always in the Top-10 and EF32 never is, as reported in the article;
* the JavaScript engine embedded in `app/index.html` gives the same scores and rankings as the Python reference on all 180 configurations
  (maximum difference below `1e-12`).

## Limitations

* The weights depend on the number of studies supporting each modality; the interface warns when fewer than 4 studies support a modality.
* Scores are relative priorities (they sum to 1); they are meant to rank EFs within a configuration.
* The EF–EF correlation matrix (the roof of the House of Quality) is not used, as in the article.

## License and citation

If you use this tool, please cite: Maaroufi, F., Danglade, F., Chardonnet, J.-R. (2026). Prioritizing Industrial XR Engineering Features Across Technology and Application Domains.

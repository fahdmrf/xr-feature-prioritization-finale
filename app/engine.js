/* Calculation engine of the XR Engineering Feature Prioritization Tool.
 * Pure functions, no DOM, no dependency. Works in browsers and in Node.js.
 *
 *   W_{i,m}      = p_{i,m} / sum_k p_{k,m},  p_{i,m} = n_{i,m} / N_m
 *   W_Litt,i     = sum_d beta_d * W_{i,m_d(f)}
 *   W_T,i        = alpha * W_indus,i + (1 - alpha) * W_Litt,i
 *   P_j          = sum_i W_T,i * R_ij / sum_k R_ik      (normalised to sum to 1 over the EFs)
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.XRP = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var DIMENSIONS = ['xr_technology', 'application_domain', 'industrial_activity', 'hardware_configuration'];
  var XR_TECHNOLOGIES = ['AR', 'VR'];
  var DOMAINS = ['Design', 'Production', 'Maintenance'];
  var ACTIVITIES = [
    'Assembly', 'Maintenance and Repair', 'Quality Control and Inspection', 'Product Design',
    'System Design', 'Operator Training', 'Operator Assistance', 'Industrial Safety Awareness',
    'Machine/Robot/Production-System Monitoring', 'Ergonomic Evaluation'
  ];
  var HARDWARE_BY_TECHNOLOGY = {
    AR: ['AR HMD only', 'Handheld/Mobile XR Device only', 'AR HMD + Handheld/Mobile XR Device only'],
    VR: ['VR HMD only', 'VR HMD + XR Controllers', 'VR HMD + XR Controllers + Motion/Positional Tracking']
  };
  var LOW_SUPPORT_THRESHOLD = 4;

  function memberOf(study, dimension, modality) {
    switch (dimension) {
      case 'xr_technology': return study.xr_technology === modality;
      case 'application_domain': return study.application_domain === modality;
      case 'industrial_activity': return study.activities.indexOf(modality) !== -1;
      case 'hardware_configuration': return study.hardware_configuration === modality;
      default: throw new Error('Unknown dimension ' + dimension);
    }
  }

  function modalityWeights(data, dimension, modality) {
    var sel = data.studies.filter(function (s) { return memberOf(s, dimension, modality); });
    var p = data.crs.map(function (c) {
      var n = sel.filter(function (s) { return s.criteria.indexOf(c.id) !== -1; }).length;
      return n / sel.length;
    });
    var total = p.reduce(function (a, b) { return a + b; }, 0);
    return { weights: p.map(function (v) { return v / total; }), n: sel.length };
  }

  function prioritize(data, config, alpha, beta) {
    alpha = alpha === undefined ? data.params.alpha : alpha;
    beta = beta || data.params.beta;
    var chosen = {
      xr_technology: config.technology, application_domain: config.domain,
      industrial_activity: config.activity, hardware_configuration: config.hardware
    };
    var nCR = data.crs.length, nEF = data.efs.length, i, j, d;
    var wLit = new Array(nCR).fill(0), support = {}, byDimension = {};
    DIMENSIONS.forEach(function (dim) {
      var mw = modalityWeights(data, dim, chosen[dim]);
      support[dim] = mw.n; byDimension[dim] = mw.weights;
      for (i = 0; i < nCR; i++) wLit[i] += beta[dim] * mw.weights[i];
    });
    var wT = wLit.map(function (v, k) { return alpha * data.crs[k].w_indus + (1 - alpha) * v; });
    var raw = new Array(nEF).fill(0);
    for (i = 0; i < nCR; i++) {
      var rowSum = data.R[i].reduce(function (a, b) { return a + b; }, 0);
      for (j = 0; j < nEF; j++) raw[j] += wT[i] * data.R[i][j] / rowSum;
    }
    var total = raw.reduce(function (a, b) { return a + b; }, 0);
    var scores = raw.map(function (v) { return v / total; });
    var order = scores.map(function (_, k) { return k; }).sort(function (a, b) { return scores[b] - scores[a] || a - b; });
    return {
      config: chosen, support: support, byDimension: byDimension, wLit: wLit, wT: wT, scores: scores,
      ranking: order.map(function (k, pos) {
        return { rank: pos + 1, id: data.efs[k].id, name: data.efs[k].name, category: data.efs[k].category, score: scores[k] };
      })
    };
  }

  function validConfigurations() {
    var out = [];
    XR_TECHNOLOGIES.forEach(function (t) {
      HARDWARE_BY_TECHNOLOGY[t].forEach(function (h) {
        DOMAINS.forEach(function (d) { ACTIVITIES.forEach(function (a) {
          out.push({ technology: t, hardware: h, domain: d, activity: a });
        }); });
      });
    });
    return out;
  }

  return {
    DIMENSIONS: DIMENSIONS, XR_TECHNOLOGIES: XR_TECHNOLOGIES, DOMAINS: DOMAINS, ACTIVITIES: ACTIVITIES,
    HARDWARE_BY_TECHNOLOGY: HARDWARE_BY_TECHNOLOGY, LOW_SUPPORT_THRESHOLD: LOW_SUPPORT_THRESHOLD,
    modalityWeights: modalityWeights, prioritize: prioritize, validConfigurations: validConfigurations
  };
});

// Runs the engine and data embedded in the shipped app/index.html (not a separate copy) on all 180 configurations
// and prints the results as JSON, so that Python can compare them with the reference implementation.
const fs = require('fs'), path = require('path'), vm = require('vm');
const html = fs.readFileSync(path.join(__dirname, '..', 'app', 'index.html'), 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const engineSrc = scripts[0];
const dataSrc = scripts[1].match(/var DATA = ([\s\S]*?);\n\(function/)[1];
const ctx = vm.createContext({});
vm.runInContext(engineSrc, ctx);
const XRP = vm.runInContext('this.XRP', ctx);
const DATA = JSON.parse(dataSrc);
const out = XRP.validConfigurations().map(c => {
  const r = XRP.prioritize(DATA, c);
  return { config: c, scores: r.scores, wT: r.wT, ranking: r.ranking.map(e => e.id), support: r.support };
});
process.stdout.write(JSON.stringify(out));

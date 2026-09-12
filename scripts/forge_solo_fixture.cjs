// Execute the real inline Forge script in a DOM stub. No browser, network or SDK.
// Input: JSON {dataRoot, fields?, provider?, llm?, character?, compression?, traits?,
//              features?, cognition?, htmlPath?, mode?, interaction?}.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const html = fs.readFileSync(input.htmlPath || path.join(__dirname, '../start/torment_character_creator.html'), 'utf8');
const nodes = new Map();
for (const match of html.matchAll(/<([\w-]+)\b([^>]*\bid="([^"]+)"[^>]*)>/g)) {
  const value = /\bvalue="([^"]*)"/.exec(match[2])?.[1] || '';
  nodes.set(match[3], {value, textContent: '', style: {}, classList: {add() {}, remove() {}, toggle() {}},
    scrollIntoView() {}, addEventListener() {}});
}
for (const match of html.matchAll(/<select\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g)) {
  const options = [...match[2].matchAll(/<option\b[^>]*value="([^"]*)"[^>]*>/g)];
  nodes.get(match[1]).value = (options.find(o => /\bselected\b/.test(o[0])) || options[0])[1];
}
Object.entries({'char-name': 'Forge Qualification', 'workspace-id': 'forge_qualification',
  'seed-text': 'Keeps careful records. Values patient reasoning. Remembers shared projects.',
  'solo-data-root': input.dataRoot, ...input.fields}).forEach(([key, value]) => {
  if (!nodes.has(key)) throw new Error('Unknown fixture field: ' + key);
  nodes.get(key).value = String(value);
});
const alerts = [];
const sandbox = {document: {querySelector: () => ({value: input.interaction || 'window'}), getElementById: id => {
  if (!nodes.has(id)) throw new Error('Unknown DOM id: ' + id);
  return nodes.get(id);
}}, window: {addEventListener() {}}, alert: msg => alerts.push(msg)};
vm.createContext(sandbox);
vm.runInContext(html.split('<script>')[1].split('</script>')[0], sandbox);
sandbox.fixture = input;
vm.runInContext(`
  selectedEmbed = fixture.provider ?? 'st';
  selectedModel = fixture.llm ?? 'claude';
  selectedTraits = fixture.traits ?? [];
  features.character = fixture.character ?? true;
  features.compression = fixture.compression ?? false;
  features.srg = true;
  Object.assign(features, fixture.features ?? {});
  Object.assign(cognitionCaps, fixture.cognition ?? {});
  if (fixture.mode === 'hivemind') {
    deploymentMode = 'hivemind';
    hivemindAgents = [{name: 'Fixture One', role: 'researcher', domain: 'research', seed: 'Keeps careful records of shared projects.'},
      {name: 'Fixture Two', role: 'builder', domain: 'engineering', seed: 'Builds reliable tools and documents decisions.'}];
    generateHivemind();
  } else {
    generateSolo();
  }
`, sandbox);
let markdown = '';
if (!alerts.length) {
  sandbox.downloadFile = content => { markdown = content; };
  vm.runInContext('exportSetup()', sandbox);
}
const outputs = Object.fromEntries([...nodes].filter(([key]) => key.startsWith('out-')).map(([key, node]) => [key, node.textContent]));
process.stdout.write(JSON.stringify({alerts, outputs, markdown}));

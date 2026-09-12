// Exercise the actual inline Hivemind generator; no network, browser or SDK.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const html = fs.readFileSync(input.htmlPath || path.join(__dirname, '../start/torment_character_creator.html'), 'utf8');
function node(value = '') { return {value, textContent:'', innerHTML:'', style:{}, children:[],
  appendChild(child) { this.children.push(child); }, classList:{add(){},remove(){},toggle(){}},
  scrollIntoView(){}, addEventListener(){}}; }
const nodes = new Map();
for (const match of html.matchAll(/<([\w-]+)\b([^>]*\bid="([^"]+)"[^>]*)>/g)) nodes.set(match[3], node(/\bvalue="([^"]*)"/.exec(match[2])?.[1] || ''));
for (const match of html.matchAll(/<select\b[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g)) {
  const options = [...match[2].matchAll(/<option\b[^>]*value="([^"]*)"[^>]*>/g)];
  nodes.get(match[1]).value = (options.find(option => /\bselected\b/.test(option[0])) || options[0])[1];
}
Object.entries({'hive-workspace-id':'forge_hive', 'hive-team-name':'Forge Hive Qualification',
  'hive-data-root':input.dataRoot, ...input.fields}).forEach(([id,value]) => {
  if (!nodes.has(id)) throw new Error('Unknown field: '+id);
  nodes.get(id).value = String(value);
});
const alerts = [];
const sandbox = {document:{querySelector:()=>({value:input.interaction || 'window'}),
  createElement:()=>node(), getElementById:id=>{if (!nodes.has(id)) throw new Error('Unknown DOM id: '+id); return nodes.get(id);}},
  window:{addEventListener(){}}, alert:message=>alerts.push(message)};
vm.createContext(sandbox);
vm.runInContext(html.split('<script>')[1].split('</script>')[0],sandbox);
sandbox.fixture=input;
vm.runInContext(`
  deploymentMode = 'hivemind';
  selectedEmbed = fixture.provider ?? 'hash'; selectedModel = fixture.llm ?? 'claude';
  Object.assign(features, fixture.features ?? {});
  hivemindDomains = fixture.domains ?? ['research','engineering','creative','operations','meta'];
  hivemindAgents = fixture.agents ?? [
    {name:'Zeta',role:'researcher',domain:'research',seed:'Keeps careful records of harmless research projects.'},
    {name:'Alpha',role:'artist',domain:'creative',seed:'Explores harmless creative projects and keeps precise notes.'},
    {name:'Mu',role:'builder',domain:'engineering',seed:'Builds reliable tools and documents decisions carefully.'}];
  document.getElementById('hive-agent-count').value = String(hivemindAgents.length);
  for (const domain of fixture.removeDomains ?? []) removeDomain(domain);
  if (fixture.addDomain !== undefined) { document.getElementById('domain-input').value = fixture.addDomain; addDomain(); }
  generateHivemind();
`,sandbox);
let markdown='';
if (!alerts.length) { sandbox.downloadFile=value=>{markdown=value;}; vm.runInContext('exportSetup()',sandbox); }
const outputs=Object.fromEntries([...nodes].filter(([key])=>key.startsWith('out-')).map(([key,item])=>[key,item.textContent]));
const state=vm.runInContext('({agents:hivemindAgents,domains:hivemindDomains})',sandbox);
process.stdout.write(JSON.stringify({alerts,outputs,markdown,state}));

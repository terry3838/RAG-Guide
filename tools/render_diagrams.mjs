import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { renderMermaidSVG, THEMES } from 'beautiful-mermaid';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..');
const DIAGRAM_DIR = path.join(ROOT, 'assets', 'diagrams');
fs.mkdirSync(DIAGRAM_DIR, { recursive: true });

const mdFiles = [];
function walk(dir) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    if (ent.name === '.git' || ent.name === 'node_modules') continue;
    const full = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(full);
    else if (ent.isFile() && ent.name.endsWith('.md')) mdFiles.push(full);
  }
}
walk(ROOT);

const theme = { ...THEMES['github-light'], transparent: true };
const mermaidRe = /```mermaid\n([\s\S]*?)```/g;
let total = 0;

for (const file of mdFiles) {
  const orig = fs.readFileSync(file, 'utf8');
  let changed = false;
  let idx = 0;
  const replaced = orig.replace(mermaidRe, (_, code) => {
    idx += 1;
    total += 1;
    const relNoExt = path.relative(ROOT, file).replace(/\\/g, '/').replace(/\.md$/, '');
    const safeBase = relNoExt.replace(/\//g, '__');
    const outName = `${safeBase}__diagram_${idx}.svg`;
    const outPath = path.join(DIAGRAM_DIR, outName);
    const svg = renderMermaidSVG(code.trimEnd(), theme);
    fs.writeFileSync(outPath, svg, 'utf8');
    const relImg = path.relative(path.dirname(file), outPath).replace(/\\/g, '/');
    changed = true;
    return `![Diagram ${idx}](${relImg})`;
  });
  if (changed) fs.writeFileSync(file, replaced, 'utf8');
}

console.log(`Rendered ${total} diagrams.`);

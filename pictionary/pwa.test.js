const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const ici = f => path.join(__dirname, f);
const lire = f => fs.readFileSync(ici(f), 'utf8');

test('le manifeste décrit une appli installable', () => {
  const m = JSON.parse(lire('manifest.webmanifest'));
  assert.equal(m.name, 'Pictionary – tireur de mots');
  assert.equal(m.short_name, 'Pictionary');
  assert.equal(m.start_url, './');
  assert.equal(m.display, 'standalone');
  assert.equal(m.background_color, '#ffffff');
  assert.equal(m.theme_color, '#ffffff');
  const tailles = m.icons.map(i => i.sizes).sort();
  assert.deepEqual(tailles, ['192x192', '512x512']);
  for (const i of m.icons) {
    assert.equal(i.type, 'image/png');
    assert.ok(fs.existsSync(ici(i.src)), `icône absente : ${i.src}`);
  }
});

test('les icônes sont des PNG aux bonnes dimensions', () => {
  for (const [f, t] of [['icone-192.png', 192], ['icone-512.png', 512]]) {
    const b = fs.readFileSync(ici(f));
    assert.equal(b.toString('latin1', 1, 4), 'PNG');
    assert.equal(b.readUInt32BE(16), t);
    assert.equal(b.readUInt32BE(20), t);
  }
});

test('le service worker pré-cache tous les fichiers servis', () => {
  const sw = lire('sw.js');
  for (const f of ['./', './index.html', './manifest.webmanifest', './icone-192.png', './icone-512.png']) {
    assert.ok(sw.includes(`'${f}'`), `absent du pré-cache : ${f}`);
    if (f !== './') assert.ok(fs.existsSync(ici(f)), `fichier absent : ${f}`);
  }
  assert.match(sw, /const CACHE = 'pictionary-v\d+'/);
});

test('index.html déclare le manifeste et enregistre le service worker', () => {
  const html = lire('index.html');
  assert.ok(html.includes('<link rel="manifest" href="manifest.webmanifest">'));
  assert.ok(html.includes('<meta name="theme-color" content="#ffffff">'));
  assert.match(html, /'serviceWorker' in navigator/);
  assert.match(html, /register\('sw\.js'\)/);
});

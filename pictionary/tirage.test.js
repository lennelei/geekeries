const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Exécute le bloc <script id="logique"> de index.html et retourne ses globales.
function charger() {
  const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
  const m = html.match(/<script id="logique">([\s\S]*?)<\/script>/);
  assert.ok(m, 'bloc <script id="logique"> introuvable');
  const ctx = {};
  vm.runInNewContext(m[1] + '\n;this.MOTS = MOTS; this.tirer = tirer;' +
    ' this.chargerVus = chargerVus; this.sauverVus = sauverVus;', ctx);
  return ctx;
}

function gelerProfond(o) {
  for (const v of Object.values(o)) if (v && typeof v === 'object') gelerProfond(v);
  return Object.freeze(o);
}

const { MOTS, tirer, chargerVus, sauverVus } = charger();

test('tire 3 mots de 3 catégories différentes', () => {
  let vus = {};
  for (let i = 0; i < 200; i++) {
    const r = tirer(MOTS, vus);
    assert.equal(r.tirage.length, 3);
    assert.equal(new Set(r.tirage.map(t => t.categorie)).size, 3);
    vus = r.vus;
  }
});

test('chaque mot appartient à sa catégorie', () => {
  let vus = {};
  for (let i = 0; i < 50; i++) {
    const r = tirer(MOTS, vus);
    for (const { categorie, mot } of r.tirage) assert.ok(MOTS[categorie].includes(mot));
    vus = r.vus;
  }
});

test('ne répète pas un mot avant épuisement', () => {
  const mots = { a: ['a1', 'a2'], b: ['b1', 'b2'], c: ['c1', 'c2'] };
  const r1 = tirer(mots, {});
  const r2 = tirer(mots, r1.vus);
  const tous = [...r1.tirage, ...r2.tirage].map(t => t.mot);
  assert.equal(new Set(tous).size, 6);
});

test('remet la catégorie à zéro quand elle est épuisée', () => {
  const mots = { a: ['a1', 'a2'], b: ['b1'], c: ['c1'] };
  const vus = { a: ['a1', 'a2'] };
  const r = tirer(mots, vus);
  const a = r.tirage.find(t => t.categorie === 'a');
  assert.ok(['a1', 'a2'].includes(a.mot));
  assert.deepEqual([...r.vus.a], [a.mot]);
});

test('ignore les mots vus disparus de la liste', () => {
  const r = tirer(MOTS, { objet: ['fantôme'] });
  assert.equal(r.tirage.length, 3);
});

test('ne modifie pas vus en entrée', () => {
  const vus = gelerProfond({ objet: [MOTS.objet[0]], animal: [] });
  assert.doesNotThrow(() => tirer(MOTS, vus));
});

test('chargerVus retourne {} pour une valeur absente ou invalide', () => {
  const stockage = v => ({ getItem: () => v });
  assert.deepEqual({ ...chargerVus(undefined) }, {});
  assert.deepEqual({ ...chargerVus({ getItem() { throw new Error('refusé'); } }) }, {});
  assert.deepEqual({ ...chargerVus(stockage(null)) }, {});
  assert.deepEqual({ ...chargerVus(stockage('pas du json')) }, {});
  assert.deepEqual({ ...chargerVus(stockage('[1,2]')) }, {});
  assert.deepEqual({ ...chargerVus(stockage('{"objet":"x"}')) }, {});
  assert.deepEqual(JSON.parse(JSON.stringify(chargerVus(stockage('{"objet":["chat"]}')))),
    { objet: ['chat'] });
});

test('chargerVus lit la clé pictionary-vus', () => {
  let cle;
  chargerVus({ getItem: k => { cle = k; return null; } });
  assert.equal(cle, 'pictionary-vus');
});

test('sauverVus écrit en JSON et ne lève pas si setItem lève', () => {
  let ecrit;
  sauverVus({ setItem: (k, v) => { ecrit = [k, v]; } }, { objet: ['chat'] });
  assert.deepEqual(ecrit, ['pictionary-vus', '{"objet":["chat"]}']);
  assert.doesNotThrow(() => sauverVus({ setItem() { throw new Error('plein'); } }, {}));
  assert.doesNotThrow(() => sauverVus(undefined, {}));
});

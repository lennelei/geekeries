const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Exécute sw.js avec un faux environnement de service worker.
function chargerSw({ reseau }) {
  const handlers = {};
  const stockes = new Map();
  const appelsFetch = [];
  let ajoutes = [];
  class Request {
    constructor(url, opts = {}) { this.url = url; this.cache = opts.cache || 'default'; }
  }
  const cle = r => (typeof r === 'string' ? r : r.url);
  const cache = {
    addAll: async reqs => { ajoutes = reqs; },
    put: async (r, rep) => { stockes.set(cle(r), rep); },
  };
  const ctx = {
    Request,
    self: {
      addEventListener: (t, h) => { handlers[t] = h; },
      skipWaiting: async () => {},
      clients: { claim: async () => {} },
    },
    caches: {
      open: async () => cache,
      keys: async () => [],
      delete: async () => true,
      match: async r => stockes.get(cle(r)),
    },
    fetch: async (r, opts) => { appelsFetch.push({ url: cle(r), opts }); return reseau(r); },
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, 'sw.js'), 'utf8'), ctx);
  async function declencher(type, request) {
    let promesse;
    const e = { request, waitUntil: p => { promesse = p; }, respondWith: p => { promesse = p; } };
    handlers[type](e);
    return promesse;
  }
  return { declencher, stockes, appelsFetch, ajoutes: () => ajoutes };
}

const reponse = corps => ({ ok: true, corps, clone() { return reponse(corps); } });
const tick = () => new Promise(r => setTimeout(r, 0));

test('le pré-cache contourne le cache HTTP', async () => {
  const sw = chargerSw({ reseau: async () => reponse('x') });
  await sw.declencher('install');
  assert.ok(sw.ajoutes().length > 0);
  for (const r of sw.ajoutes()) assert.equal(r.cache, 'reload', `${r.url} sans cache: 'reload'`);
});

test('la page vient du réseau en priorité, sans cache HTTP, et met le cache à jour', async () => {
  const sw = chargerSw({ reseau: async () => reponse('nouvelle') });
  sw.stockes.set('https://ex/pictionary/', reponse('ancienne'));
  const r = await sw.declencher('fetch', { url: 'https://ex/pictionary/', method: 'GET', mode: 'navigate' });
  assert.equal(r.corps, 'nouvelle');
  assert.equal(sw.appelsFetch[0].opts.cache, 'no-cache');
  await tick();
  assert.equal(sw.stockes.get('https://ex/pictionary/').corps, 'nouvelle');
});

test('hors ligne, la page vient du cache', async () => {
  const sw = chargerSw({ reseau: async () => { throw new TypeError('hors ligne'); } });
  sw.stockes.set('./', reponse('en cache'));
  const r = await sw.declencher('fetch', { url: 'https://ex/pictionary/', method: 'GET', mode: 'navigate' });
  assert.equal(r.corps, 'en cache');
});

test('les autres fichiers viennent du cache d\'abord', async () => {
  const sw = chargerSw({ reseau: async () => reponse('réseau') });
  sw.stockes.set('https://ex/pictionary/icone-192.png', reponse('icône'));
  const r = await sw.declencher('fetch', { url: 'https://ex/pictionary/icone-192.png', method: 'GET', mode: 'no-cors' });
  assert.equal(r.corps, 'icône');
  assert.equal(sw.appelsFetch.length, 0);
});

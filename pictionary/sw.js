// Service worker : met le jeu en cache pour qu'il marche sans réseau.
// La page (liste de mots comprise) vient du réseau dès qu'il y en a : une
// nouvelle version arrive sans rien faire. Incrémenter CACHE seulement si les
// icônes ou le manifeste changent.
const CACHE = 'pictionary-v1';
const FICHIERS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icone-192.png',
  './icone-512.png',
];

self.addEventListener('install', e => {
  // cache: 'reload' : ne pas pré-cacher une copie périmée du cache HTTP (max-age de Pages).
  const requetes = FICHIERS.map(f => new Request(f, { cache: 'reload' }));
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(requetes)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(noms => Promise.all(noms.filter(n => n !== CACHE).map(n => caches.delete(n))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  if (e.request.mode === 'navigate') {
    // La page : réseau d'abord (sans cache HTTP), copie en cache ; cache si hors ligne.
    e.respondWith(
      fetch(e.request.url, { cache: 'no-cache' })
        .then(r => {
          if (r.ok) {
            const copie = r.clone();
            caches.open(CACHE).then(c => c.put(e.request, copie));
          }
          return r;
        })
        .catch(() => caches.match(e.request).then(r => r || caches.match('./'))),
    );
    return;
  }
  // Icônes et manifeste : cache d'abord, réseau sinon.
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});

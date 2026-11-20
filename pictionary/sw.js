// Service worker : met le jeu en cache pour qu'il marche sans réseau.
// À chaque modification d'un fichier servi, incrémenter CACHE : sinon les
// téléphones gardent l'ancienne version.
const CACHE = 'pictionary-v1';
const FICHIERS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icone-192.png',
  './icone-512.png',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FICHIERS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(noms => Promise.all(noms.filter(n => n !== CACHE).map(n => caches.delete(n))))
      .then(() => self.clients.claim()),
  );
});

// Cache d'abord, réseau sinon.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});

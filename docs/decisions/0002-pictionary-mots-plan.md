# Tireur de mots Pictionary – plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** une page `pictionary/index.html` qui propose 3 mots de 3 catégories
différentes à dessiner, avec un bouton « Autres mots ».

**Architecture :** un fichier HTML autonome, plus un manifeste, deux icônes et un
service worker pour l'installation et le hors-ligne (PWA). La logique pure (liste de mots,
tirage, persistance) vit dans un bloc `<script id="logique">` sans accès au DOM ;
l'interface dans un second bloc `<script>`. Les tests Node extraient le bloc
`logique` de `index.html` et l'exécutent dans un `vm` : pas de build, pas de
duplication.

**Tech Stack :** HTML/CSS/JS sans dépendance ; tests `node:test` (Node ≥ 18).

**Spec :** `docs/decisions/0001-pictionary-mots.md`

## Global Constraints

- Aucune ressource externe (police, CDN) ; tous les fichiers sous `pictionary/`, chemins
  relatifs (le site est servi sous `/geekeries/pictionary/`).
- Hors ligne : après une première visite, la page s'ouvre et tire des mots sans réseau.
- 3 mots par tirage, de 3 catégories différentes parmi `objet`, `animal`, `action`,
  `personnage`, `marque`.
- Environ 300 mots au total, à la portée d'un enfant de 7 ans.
- Un mot ne revient qu'une fois sa catégorie épuisée ; état dans `localStorage`.
- Noir et blanc, gros texte, aucune animation ni transition.
- Textes de l'interface en français.

## Review Focus

- `localStorage` indisponible ou qui lève une exception (fichier ouvert en `file://`,
  navigation privée) : la page tire quand même des mots, sans mémoire.
- Valeur `localStorage` corrompue ou d'un ancien format : ignorée, on repart à zéro.
- Mot vu qui n'existe plus dans la liste (liste modifiée entre deux parties) : pas de
  boucle infinie, la catégorie se recalcule sur les mots restants.
- Catégorie épuisée : son historique est remis à zéro et le tirage continue.
- Deux mots du même tirage ne viennent jamais de la même catégorie.
- Page modifiée puis republiée : le téléphone finit par recevoir la nouvelle version
  (nom de cache versionné, anciens caches supprimés à l'activation).

---

### Task 1 : logique de tirage

**Files :**
- Create : `pictionary/index.html` (squelette + bloc `<script id="logique">`)
- Test : `pictionary/tirage.test.js`

**Interfaces :**
- Produces (globales du bloc `logique`) :
  - `MOTS : { objet: string[], animal: string[], action: string[], personnage: string[], marque: string[] }`
    (5 mots par catégorie dans cette tâche, la vraie liste arrive en Task 2)
  - `tirer(mots, vus, rng = Math.random) -> { tirage: {categorie: string, mot: string}[3], vus }`
    où `vus : { [categorie]: string[] }` ; ne modifie pas l'objet `vus` reçu.
  - `chargerVus(storage) -> vus` (retourne `{}` si storage absent, exception, JSON
    invalide ou valeur qui n'est pas un objet de tableaux)
  - `sauverVus(storage, vus) -> void` (avale les exceptions)
  - Clé de stockage : `"pictionary-vus"`.
- Helper de test `charger()` dans `tirage.test.js` : lit `index.html`, extrait le
  contenu de `<script id="logique">`, l'exécute avec `vm.runInNewContext` et retourne
  le contexte.

- [ ] **Step 1 : écrire les tests qui échouent**, dans `tirage.test.js` :
  - `tire 3 mots de 3 catégories différentes` : sur 200 tirages, `new Set(categories).size === 3`.
  - `chaque mot appartient à sa catégorie` : `mots[c].includes(m)`.
  - `ne répète pas un mot avant épuisement` : avec `{a: [1 mot], b: [...], c: [...]}`
    réduits à 3 catégories de 2 mots, 2 tirages enchaînés donnent les 6 mots distincts.
  - `remet la catégorie à zéro quand elle est épuisée` : `vus` contenant tous les mots
    d'une catégorie, le tirage en donne quand même un, et `vus[cat]` ne contient plus que lui.
  - `ignore les mots vus disparus de la liste` : `vus.objet = ['fantôme']` → tirage OK.
  - `ne modifie pas vus en entrée` : `vus` gelé avec `Object.freeze` en profondeur → pas d'exception.
  - `chargerVus` retourne `{}` pour : `undefined`, storage dont `getItem` lève, `"pas du json"`,
    `"[1,2]"`, `'{"objet":"x"}'` ; retourne l'objet pour `'{"objet":["chat"]}'`.
  - `sauverVus` ne lève pas si `setItem` lève.
- [ ] **Step 2 : lancer** `node --test pictionary/` → FAIL (`index.html` absent).
- [ ] **Step 3 : implémenter** le bloc `logique` dans `index.html` (squelette HTML minimal
  pour l'instant). Tirage : mélanger les catégories avec `rng`, prendre les 3 premières ;
  pour chacune, candidats = mots non vus, si vide → réinitialiser `vus[cat]` et
  candidats = tous les mots.
- [ ] **Step 4 : lancer** `node --test pictionary/` → tous les tests PASS.
- [ ] **Step 5 : commit** « Ajoute la logique de tirage du Pictionary ».

### Task 2 : liste de mots

**Files :**
- Modify : `pictionary/index.html` (constante `MOTS`)
- Test : `pictionary/tirage.test.js`

**Interfaces :** Consumes `MOTS` (Task 1), même forme.

- [ ] **Step 1 : tests qui échouent** : `liste complète` — chaque catégorie a ≥ 50 mots,
  total entre 280 et 340 ; `pas de doublon` — aucun mot répété, toutes catégories
  confondues (comparaison en minuscules, sans espaces de bord) ; aucun mot vide.
- [ ] **Step 2 : lancer** `node --test pictionary/` → FAIL.
- [ ] **Step 3 : écrire la liste**, ~60 mots par catégorie, dessinables et connus d'un
  enfant de 7 ans. Objets et animaux avec article (« un parapluie », « une girafe ») ;
  actions à l'infinitif (« sauter ») ; personnages surtout de fiction (dessins animés,
  contes, jeux vidéo grand public) plus quelques célébrités ; marques connues des
  enfants (« Lego », « Nutella »…).
- [ ] **Step 4 : lancer** `node --test pictionary/` → PASS.
- [ ] **Step 5 : commit** « Ajoute la liste de mots du Pictionary ».

### Task 3 : interface

**Files :**
- Modify : `pictionary/index.html` (HTML, CSS, second `<script>`)

**Interfaces :** Consumes `MOTS`, `tirer`, `chargerVus`, `sauverVus` (Task 1).

- [ ] **Step 1 : implémenter** : au chargement, `vus = chargerVus(localStorage)` dans un
  `try` (l'accès même à `window.localStorage` peut lever), tirage immédiat. Affichage :
  3 lignes « CATÉGORIE (petites capitales) — mot (gros) » ; bouton plein-largeur
  « Autres mots » qui retire, affiche, puis `sauverVus`. Libellés de catégorie :
  Objet, Animal, Action, Personnage, Marque. Texte ≥ 32 px pour les mots, fond blanc,
  texte noir, pas de `transition`/`animation`.
- [ ] **Step 2 : vérifier** `node --test pictionary/` → PASS (le bloc logique est intact).
- [ ] **Step 3 : vérifier en local** en ouvrant `pictionary/index.html` dans un
  navigateur (Chrome Windows via `\\wsl$`) : 3 mots de catégories différentes, le
  bouton change les mots, un rechargement ne répète pas les mots déjà vus ; même
  vérification en navigation privée (pas d'erreur console).
- [ ] **Step 4 : commit** « Ajoute l'interface du tireur de mots ».

### Task 4 : PWA (installation et hors-ligne)

**Files :**
- Create : `pictionary/manifest.webmanifest`, `pictionary/sw.js`,
  `pictionary/icone-192.png`, `pictionary/icone-512.png`
- Modify : `pictionary/index.html` (`<link rel="manifest">`, `<meta name="theme-color">`,
  enregistrement du service worker)
- Test : `pictionary/pwa.test.js`

- [ ] **Step 1 : tests qui échouent** (`pwa.test.js`) : le manifeste est du JSON valide
  avec `name` « Pictionary – tireur de mots », `short_name` « Pictionary »,
  `start_url` `"./"`, `display` `"standalone"`, `background_color` et `theme_color`
  `"#ffffff"`, deux icônes PNG 192 et 512 dont les fichiers existent ; `sw.js` cite
  dans sa liste de pré-cache `./`, `./index.html`, `./manifest.webmanifest` et les deux
  icônes, et chacun de ces fichiers existe ; `index.html` contient
  `<link rel="manifest" href="manifest.webmanifest">`.
- [ ] **Step 2 : lancer** `node --test pictionary/` → FAIL.
- [ ] **Step 3 : implémenter.** `sw.js` : constante `CACHE = "pictionary-v1"`,
  pré-cache à l'`install`, suppression des caches dont le nom diffère à l'`activate`,
  `fetch` en « cache d'abord, réseau sinon ». Enregistrement dans `index.html` seulement
  si `'serviceWorker' in navigator` (rien en `file://`). Icônes : un « P » noir sur
  fond blanc, générées une fois par script (ImageMagick ou Python), PNG versionnés.
  Règle à noter en commentaire en tête de `sw.js` : incrémenter `CACHE` à chaque
  modification des fichiers servis.
- [ ] **Step 4 : lancer** `node --test pictionary/` → PASS.
- [ ] **Step 5 : commit** « Rend le tireur de mots installable et utilisable hors ligne ».

### Task 5 : publication (avec validation de l'utilisateur)

- [ ] **Step 1 :** pousser la branche, ouvrir la PR (`GH_TOKEN=$(gh auth token --user lennelei)`),
  merge après accord.
- [ ] **Step 2 :** après accord explicite, activer GitHub Pages sur `main`, racine
  (`gh api -X POST repos/lennelei/geekeries/pages -f 'source[branch]=main' -f 'source[path]=/'`).
  Tout le repo est déjà public, Pages n'expose rien de plus.
- [ ] **Step 3 :** vérifier `https://lennelei.github.io/geekeries/pictionary/` (HTTP 200,
  titre attendu) puis l'ouvrir sur le téléphone et la Boox.
- [ ] **Step 4 :** sur le téléphone, « Ajouter à l'écran d'accueil », passer en mode
  avion, relancer depuis l'icône : la page s'ouvre et « Autres mots » fonctionne.

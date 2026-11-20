# 1. Tireur de mots pour un Pictionary en famille

Date : 2026-11-20

## Statut

Accepté

## Contexte

Jeu de dessin type Pictionary en famille, avec deux enfants de 7 et 10 ans, sans
équipe, sans score ni minuteur. Le dessin se fait sur une Boox Air 5C.

Un test de tracé dans le navigateur de la Boox (`pictionary/test-trace.html`) a montré
une latence trop forte : le tracé rapide natif n'est disponible que dans les applis Boox
(Notes, NeoReader) ou via le SDK pen d'Onyx, réservé aux applis Android natives. Boox
Notes reste donc l'outil de dessin ; le besoin se réduit à proposer des mots.

## Décision

Une page web statique, un seul fichier HTML autonome (liste de mots incluse), utilisable
hors ligne, ouverte sur le téléphone de celui qui dessine (ou sur la Boox, puisqu'on n'y
dessine plus).

- Chaque tirage affiche **3 mots de 3 catégories différentes** parmi : objet, animal,
  action, personnage (fiction surtout, quelques célébrités connues des enfants), marque.
  Le dessinateur en choisit un.
- Un seul bouton **« Autres mots »** : sert à passer (mot inconnu du plus petit) et à
  lancer le tour suivant.
- Environ 300 mots, à la portée d'un enfant de 7 ans.
- Pas de répétition : un mot ne revient qu'une fois la liste de sa catégorie épuisée ;
  l'état est conservé dans `localStorage` (survit à la fermeture de la page).
- Affichage noir et blanc, gros texte, sans animation : lisible sur écran e-ink.
- Hébergement : GitHub Pages depuis `geekeries` (repo public), après validation.

Hors périmètre : équipes, scores, minuteur, zone de dessin intégrée.

## Approches considérées

- **Page web statique (retenue)** : rien à installer, marche partout, hors ligne.
- **Zone de dessin dans le navigateur** : écartée, latence e-ink trop forte (test).
- **Appli Android native avec le SDK pen Onyx** : tracé rapide, mais appli Kotlin à
  écrire et installer à la main, pour refaire ce que Notes fait déjà.
- **Cartes imprimées** : pas de tirage aléatoire ni de « passer » commode.

## Conséquences

- Deux supports en jeu (téléphone pour le mot, Boox pour le dessin), ce qui évite que
  les enfants voient le mot.
- Laissé à l'implémentation : le choix des mots de la liste, la mise en page exacte, un
  éventuel bouton de remise à zéro de l'historique.

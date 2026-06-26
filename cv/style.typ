// style.typ — Mise en page et fonctions de rendu (indépendant du contenu)
// -------------------------------------------------------------------------

#import "@preview/neat-cv:1.1.0": cv, entry

// Couleurs reprises du CV Word existant
#let accent = rgb("#365F91")
#let accent-light = rgb("#B8CCE4")

// Configuration générale du document : à appliquer en tout début de main.typ
// avec #show: cv-setup.with(author: basics)
#let cv-setup(author: none, body) = {
  show: cv.with(
    author: author,
    accent-color: accent,
  )

  set text(font: "Fira Sans", size: 9pt, lang: "fr")
  set par(justify: false, leading: 0.55em)

  // Titres de section (= Section) : taille 11pt, couleur accent, ligne de séparation
  show heading.where(level: 1): it => {
    v(0.6em)
    text(size: 11pt, weight: "bold", fill: accent)[#it.body]
    v(0.15em)
    line(length: 100%, stroke: 1pt + accent-light)
    v(0.3em)
  }

  // Sous-titres (== Sous-section) : taille 10pt
  show heading.where(level: 2): it => {
    text(size: 10pt, weight: "bold")[#it.body]
  }

  body
}

// En-tête du CV : nom, titre, contact — en-tête "maison" en texte pur (pas d'icônes)
// À utiliser uniquement si cv.with() ne produit pas déjà un en-tête satisfaisant
// (point à vérifier à la compilation — voir remarque associée)
#let cv-header(basics) = {
  align(center)[
    #text(size: 18pt, weight: "bold", fill: accent)[
      #basics.firstname #upper(basics.lastname)
    ]
    #v(0.2em)
    #text(size: 11pt)[#basics.title]
    #v(0.3em)
    #text(size: 9pt)[
      #basics.email #h(0.5em) · #h(0.5em) #basics.phone #h(0.5em) · #h(0.5em) #basics.location
    ]
  ]
  v(0.8em)
}

// Ligne "Environnement" : simple, discrète, en italique
#let env-line(env) = {
  v(0.15em)
  text(size: 8pt, style: "italic", fill: accent)[Environnement : #env]
}

// Filtrage des entrées selon la version demandée (full / short)
// - sans champ "view"          -> visible dans les deux versions
// - "view" == mode demandé     -> visible uniquement dans cette version
#let visible-for(items, mode) = items.filter(item => (
  not ("view" in item) or item.view == mode
))

// Rendu d'une expérience (ou stage), avec sélection automatique
// highlights / highlights-short selon le mode
#let render-experience(exp, mode: "full") = {
  let points = if mode == "short" and "highlights-short" in exp {
    exp.highlights-short
  } else if "highlights" in exp {
    exp.highlights
  } else {
    ()
  }

  entry(
    title: exp.title,
    institution: exp.company,
    location: exp.location,
    date: exp.period,
    list(..points.map(p => [#p])),
  )

  if "environment" in exp {
    env-line(exp.environment)
  }

  v(0.5em)
}

// Rendu d'une entrée de formation (pas de champ "company"/"environment")
#let render-education(edu) = {
  entry(
    title: edu.title,
    institution: edu.institution,
    location: edu.location,
    date: edu.period,
  )
  v(0.3em)
}

// Ligne "Label : valeur" — utilisée pour environnements techniques / langues
#let label-line(item) = {
  text(weight: "bold")[#item.label : ]
  text()[#item.value]
  linebreak()
}

// Liste simple à puces (compétences, aptitudes, domaines...)
#let bullet-list(items) = {
  list(..items.map(i => [#i]))
}

// Liste d'items courts séparés par des points médians (ex: formations, divers)
#let inline-list(items) = {
  items.join("  ·  ")
}

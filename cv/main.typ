// main.typ — Point d'entrée : assemble content.typ + style.typ
// ----------------------------------------------------------------
// Compilation : typst compile main.typ cv.pdf

#import "content.typ": *
#import "style.typ": *

#set page(paper: "a4", margin: (x: 1.8cm, y: 1.6cm))

#show: cv-setup.with(author: basics)

#cv-header(basics)

= Résumé
#summary

= Compétences

== Connaissances professionnelles
#bullet-list(skills.techniques)
#bullet-list(skills.fonctionnelles)

== Environnements techniques
#for item in skills.environnements {
  label-line(item)
}

== Aptitudes professionnelles
#bullet-list(skills.aptitudes)

== Domaines métiers
#inline-list(skills.domaines)

== Langues
#for item in skills.langues {
  label-line(item)
}

= Expériences

#for exp in visible-for(experiences, "full") {
  render-experience(exp, mode: "full")
}

= Stages

#for stage in internships {
  render-experience(stage, mode: "full")
}

= Formations

#for edu in education {
  render-education(edu)
}

== Formations professionnelles
#inline-list(trainings)

== Certifications
#bullet-list(certifications)

= Divers
#bullet-list(misc)

// content.typ — Données du CV (contenu brut, indépendant du style)
// -------------------------------------------------------------
// Champs des dictionnaires "experiences":
//   period, title, company, location  -> toujours affichés
//   highlights        -> liste de points (version complète)
//   highlights-short  -> liste de points condensés (version synthétique), optionnel
//   environment       -> ligne technique (affichée dans les deux versions)
//   view              -> "full" | "short" | absent (= visible dans les deux)

#let basics = (
  firstname: "Alexis",
  lastname: "Mauger-Brun",
  title: "Architecte d'intégration — 23 ans d'expérience",
  email: "alexis.mauger-brun@actiosi.fr",
  phone: "+33 (0)6 26 19 92 77",
  location: "Nouvoitou (35)",
  // nationality: "Française / Canadienne", // omis par défaut
)

#let summary = [
  Consultant indépendant depuis 8 ans (EURL ACTIOSI).
  2011 – 2018 : Architecte d'intégration au sein du groupe Beaumanoir (7 ans).
  2003 – 2011 : Expert technique en ESN (Unilog, devenu Logica).
  Diplôme d'ingénieur — ESIEE Paris, 2003.
]

#let skills = (
  techniques: (
    "Architecture générale des systèmes d'information",
    "Environnements décisionnels ; flux de données inter-applicatifs et externes",
    "Bases de données relationnelles, Big Data ; développement et scripting",
    "Analyse et correction des problèmes de performance",
  ),
  fonctionnelles: (
    "Urbanisme du système d'information",
    "Pilotage technique de projets informatiques et des ressources associées",
    "Veille technologique",
    "Formation et accompagnement des équipes",
  ),
  environnements: (
    (label: "Systèmes / ordo.", value: "Windows, Linux, Unix, MVS OS/390 – CICS, Dollar Universe, Visual TOM, JobScheduler…"),
    (label: "Données et ERP", value: "Oracle, Teradata, Snowflake, Hadoop, MySQL, DB2…, Storeland, SAP"),
    (label: "Flux et BI", value: "Semarchy xDI, OTIC, Talend DI/ESB/BD, Datastage, Axway Secure Transport, Power BI, BusinessObjects, SSRS, PALO, normes EDIFACT"),
    (label: "Langages et outils", value: "SQL, Python, Perl, Java, ksh, bash, Git, COBOL, JCL, jsp, VBA, php"),
  ),
  aptitudes: (
    "Sens du service", "Capacité de prise d'initiative", "Excellente adaptabilité technique",
    "Relationnel technique et fonctionnel", "Expression écrite et orale", "Pédagogie",
  ),
  domaines: (
    "Banque", "Énergie", "Télécoms", "Construction", "Cosmétiques",
    "Génétique animale", "Prêt-à-porter, distribution", "Services aux entreprises",
  ),
  langues: (
    (label: "Anglais", value: "Courant (TOEFL 610 — juin 2002 ; stage de 6 mois en Australie)"),
    (label: "Allemand", value: "Notions (manque de pratique récente)"),
    (label: "Espagnol / Japonais", value: "Débutant"),
  ),
)

#let experiences = (
  // --- Indépendant — EURL ACTIOSI (depuis juillet 2018) ---

  (
    period: "Mars 2026 à ce jour",
    title: "Manager DATA de transition",
    company: "Groupe Legendre",
    location: "Rennes [35]",
    highlights: (
      "Animation du COPIL Data",
      "Accompagnement des métiers sur les projets en cours et pilotage de ces derniers",
      "Étude et mise en place d'une stratégie de MCO des applications data",
      "Étude et mise en place d'une stratégie d'intégration des applications data existantes dans la cible",
    ),
    environment: "Windows, Google Cloud Platform, Power BI",
  ),
  (
    period: "Octobre 2025 à ce jour",
    title: "Expert technique décisionnel",
    company: "Nous Anti-Gaspi",
    location: "Cesson-Sévigné [35]",
    highlights: (
      "Accompagnement de la mise en place d'un entrepôt sous GCP et de rapports Power BI à destination des équipes métiers",
      "Analyse de l'existant",
      "Industrialisation et mise sous contrôle des flux",
      "Finalisation de l'entrepôt et intégration des indicateurs",
      "Création des rapports Power BI",
    ),
    environment: "Windows, Google Cloud Platform, Power BI",
  ),
  (
    period: "Mars 2024 à juin 2025",
    title: "Architecte technique",
    company: "BPGO - DataNow",
    location: "Saint-Herblain [44]",
    highlights: (
      "Architecte technique au sein de l'équipe socle Data dans le cadre d'un projet de mise en place d'un nouvel entrepôt de données pour la banque",
      "Modélisation et accompagnement des PO sur certaines analyses",
      "Mise en place des normes de développement et des briques techniques structurantes",
      "Création des traitements d'alimentation",
      "Expertise technique auprès des équipes",
    ),
    environment: "Windows, Teradata, Semarchy xDI, Power BI, Visual TOM, SQL Server, Git",
  ),
  (
    period: "Décembre 2021 à mars 2024",
    title: "Expertise technique — pilotage commercial",
    company: "BPGO – Galiléo",
    location: "Saint-Herblain [44]",
    highlights: (
      "Expertise technique pour l'équipe du pilotage commercial en charge de l'alimentation et de la restitution des données de l'activité de la banque",
      "Identification d'axes d'optimisation technique de l'existant (réduction de la charge machine, fiabilisation des délais de publication)",
      "Mise en place de mécaniques de supervision et d'analyse de la performance",
      "Accompagnement des équipes sur les bonnes pratiques de développement",
      "Développement d'indicateurs métiers et aide à la résolution d'incidents",
    ),
    environment: "Windows, Teradata, OTIC, Power BI, Visual TOM, SQL Server",
  ),
  (
    period: "Juin 2023 à août 2023",
    title: "Renfort équipe BI — migration",
    company: "Claranet",
    location: "Cesson-Sévigné [35]",
    highlights: (
      "Renfort ponctuel de l'équipe BI dans un projet de migration des entrepôts de données de MySQL vers Azure Synapse",
      "Développement du socle technique (jobs génériques + composants Talend)",
      "Mise en place des premiers développements sur Talend BD",
      "Formation des utilisateurs aux bonnes pratiques et ajustement des normes",
    ),
    environment: "Windows, Linux, Talend Open Studio for Big Data 8, Azure Synapse, Power BI, JobScheduler, Git",
  ),
  (
    period: "Mars 2020 à décembre 2021",
    title: "Renfort équipe BI",
    company: "Claranet",
    location: "Cesson-Sévigné [35]",
    highlights: (
      "Conception d'entrepôts de données et de chaînes d'alimentation",
      "Analyse, optimisation et/ou correction des flux et entrepôts existants",
      "Réalisation de rapports Power BI",
      "Conseil et support aux équipes",
      "Mise en place d'un ordonnanceur JobScheduler et industrialisation de la plateforme BI (ordonnancement, supervision, bonnes pratiques)",
    ),
    environment: "Windows, Talend Open Studio 7, MySQL, Power BI, JobScheduler, Git",
  ),
  (
    period: "Avril à octobre 2019",
    title: "Accompagnement et formation Big Data",
    company: "U GIE IRIS",
    location: "Carquefou [44]",
    highlights: (
      "Accompagnement et formation des équipes de développement sur des projets Big Data",
      "Refonte du modèle d'ingestion (simplification des étapes, réduction des délais, clarification du suivi en production, amélioration des performances)",
      "Expertise ponctuelle sur des développements spécifiques",
      "Organisation de réunions hebdomadaires sur les bonnes pratiques",
      "Suivi des incidents avec le support Talend",
      "Suivi de la montée de version Talend BD 6 vers 7",
    ),
    environment: "Windows, CDH 5.x, Talend Big Data 6 et 7",
  ),
  (
    period: "Décembre 2018 à mars 2019",
    title: "Migration technique Talend",
    company: "Évolution",
    location: "Noyal-sur-Vilaine [35]",
    highlights: (
      "Migration de Talend Data Integration vers Talend Open Source + SMA OpCon",
      "Refonte des interfaces : mise en place des bonnes pratiques et standardisation, optimisations pour réduire charge et durée des traitements",
      "Développement du socle technique en relation avec l'ordonnanceur",
      "Formation des équipes",
    ),
    environment: "Windows, scripting batch, TOS 6.4.1, SQL Server",
  ),
  (
    period: "Juillet 2018 à décembre 2018",
    title: "Industrialisation Talend ETL / Dollar Universe",
    company: "C-Log",
    location: "Pleudihen-sur-Rance [35]",
    highlights: (
      "Accompagnement, conseil et réalisation d'interfaces lors de la mise en œuvre industrialisée de Talend ETL et de Dollar Universe",
      "Rédaction des normes et des bonnes pratiques",
      "Développement des interfaces et du socle technique",
      "Formation et accompagnement à la prise en main",
    ),
    environment: "Windows, Linux (Debian), scripting bash/python, TOS 6.5.1, PostgreSQL, SQL Server, Dollar Universe 6",
  ),

  // --- Groupe Beaumanoir / Korben (2011 – 2018) ---

  (
    period: "Juillet 2011 à mai 2018",
    title: "Responsable du pôle industrialisation et orchestration du SI",
    company: "Groupe Beaumanoir / Korben",
    location: "Saint-Malo [35]",
    highlights: (
      "En charge des choix techniques et de la mise en œuvre d'outils groupe",
      "Rédaction des normes et des bonnes pratiques sur ces outils",
      "Conception de l'ensemble des processus et outils nécessaires à l'exploitabilité",
      "Rétro-analyse et reprise de traitements historiques",
      "Supervision technique des projets (risque de performance ou impact d'intégration)",
      "Pilotage et coordination des équipes en charge des développements",
      "Réalisation de projets d'études sur les technologies Big Data",
      "Support technique auprès d'autres équipes (BI, performances)",
    ),
    environment: "Windows 7/10, 2003/2008/2012 Server, Linux (Debian, CentOS), Oracle 10/11/12, QlikView, Hadoop (Cloudera), MySQL, PostgreSQL, SQLite, SQL Server, Storeland, BusinessObjects BI 4.1, SAP, Talend DI/ESB/BD 5 et 6, TOS 6, Dollar Universe 6, Axway Secure Transport, Java, Perl, SQL, awk, batch",
  ),
  (
    period: "Juillet 2011 à 2016",
    title: "Responsable du pôle exploitation et production",
    company: "Groupe Beaumanoir / Korben",
    location: "Saint-Malo [35]",
    highlights: (
      "Maintenance et évolution du système d'information métier",
      "Accompagnement de l'externalisation de la supervision des traitements",
    ),
    environment: "Windows 7/10, 2003/2008/2012 Server, Oracle 10/11/12, Storeland, DataExchanger, Talend DI 5, Perl, SQL",
  ),

  // --- Logica IT Services – BD Ouest (2008 – 2011) ---
  // Détail des missions : version complète uniquement

  (
    period: "2010 à 2011",
    title: "Membre de l'équipe support décisionnel",
    company: "Yves Rocher (via Logica IT Services)",
    location: "La Gacilly [35]",
    view: "full",
    highlights: (
      "Supervision des chaînes de traitement de données",
      "Mise en place de nouveaux outils de reporting",
    ),
    environment: "Windows XP, HP-UX, Datastage 7.5, Business Objects 5/6/XI, Oracle 9, PALO, ksh, SQL, php",
  ),
  (
    period: "2008 à 2010",
    title: "Membre de l'équipe infrastructure / pilote de migration technique",
    company: "SFR (via Logica IT Services)",
    location: "[35]",
    view: "full",
    highlights: (
      "Administration des environnements d'intégration",
      "Support technique et accompagnement des équipes",
      "Pilote de migration technique : changement de SGBD et mise en œuvre d'un nouveau serveur d'application",
      "Analyste développeur sur des chaînes ETL",
    ),
    environment: "Windows XP, HP-UX, AIX, SunOS (5.8 → 5.10), Control-M, Patrol, Newtest, Oracle (9 → 10), Websphere 5/6, jBoss, MQ Series, ksh, Perl, SQL, Datastage 7.5A",
  ),
  // Résumé : version synthétique uniquement
  (
    period: "2008 à 2011",
    title: "Membre de la cellule d'expertise technique",
    company: "Logica IT Services – BD Ouest",
    location: "Rennes [35]",
    view: "short",
    highlights-short: (
      "Support technique auprès des projets de l'agence de Rennes — missions chez Yves Rocher (support décisionnel) et SFR (infrastructure, migration technique, ETL)",
    ),
    environment: "Windows XP, HP-UX, AIX, Oracle, Datastage, Business Objects",
  ),

  // --- Unilog Paris – BD OMEGA (2004 – 2008) ---
  // Détail des missions : version complète uniquement

  (
    period: "2008",
    title: "Interlocuteur de liaison client / développement",
    company: "EDF (via Unilog)",
    location: "Paris [75]",
    view: "full",
    highlights: (
      "Interlocuteur de liaison entre le client et l'équipe de développement basée à Bordeaux sur un projet BI + web",
    ),
    environment: "Windows XP, AIX, Tomcat, Oracle 9, Business Objects XI, ksh, SQL, Java",
  ),
  (
    period: "2004 à 2007",
    title: "Expert technico-fonctionnel grand système",
    company: "Manpower (via Unilog)",
    location: "Paris [75]",
    view: "full",
    highlights: (
      "Expert technico-fonctionnel sur du grand système",
      "Chef de projet sur des TMA Infocentre et nouvelles technologies / grand système",
    ),
    environment: "MVS OS/390, CICS, DB2, File Manager, File Aid, Access, PRF, Websphere 5, Synergy, Crys@lid, IBM Host Publisher, Cobol, SQL, VBA, Java, jsp, JavaScript, Perl, SVN, ksh",
  ),
  // Résumé : version synthétique uniquement
  (
    period: "2004 à 2008",
    title: "Expert technique",
    company: "Unilog Paris – BD OMEGA (devenu Logica)",
    location: "Paris [75]",
    view: "short",
    highlights-short: (
      "Interlocuteur privilégié réseaux et supervision serveur ; missions chez EDF (liaison client/dev, projet BI + web) et Manpower (expert grand système, chef de projet TMA)",
    ),
    environment: "MVS OS/390, CICS, DB2, Oracle, Java",
  ),
)

#let internships = (
  (
    period: "2003 (6 mois)",
    title: "Développeur back-end — site web et base de données",
    company: "Business Security Systems",
    location: "Sydney [Australie]",
    highlights: (
      "Développement de la partie serveur (site web et base de données) d'un logiciel de sécurité",
    ),
    environment: "Windows 2000 Server, ASP, JavaScript, HTML, SSL, SQL (MS SQL Server)",
  ),
  (
    period: "2002 (2 mois)",
    title: "Chargé d'étude — traces d'outils de piratage",
    company: "Institut de Recherche Criminelle de la Gendarmerie Nationale",
    location: "Rosny-sous-Bois [93]",
    highlights: (
      "Étude des traces laissées par les outils de piratage",
    ),
    environment: "Windows 98, Linux, Perl, TCP/IP",
  ),
)

#let education = (
  (
    period: "Juillet 2003",
    title: "Diplôme d'ingénieur — majeure informatique (cycle 1998–2003)",
    institution: "ESIEE Paris",
    location: "Noisy-le-Grand [93]",
  ),
)

#let trainings = (
  "Management", "MVS (Cobol, CICS, DB2)", "PALO", "jBoss", "Newtest",
  "BMC Control-M", "BMC Patrol", "Oracle", "QlikView", "SOA",
  "Axway Secure Transport", "Big Data",
)

#let certifications = (
  "Certification Dollar Universe 6.0 Foundation",
)

#let misc = (
  "Administration de serveurs dédiés sous Linux (LAMP/LEMP, Docker, WordPress…)",
  "Chef de bord bénévole pour l'UCPA Croisière ; plongeur niveau II FFESSM",
  "Formations PSC1, SST et EPI",
)

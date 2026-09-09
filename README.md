# 🌐 WiseNet
### Autonomous Predictive Self-Organizing Network (SON) Optimization
*(Nom technique du dépôt : `spatial-son-milp` | Version : **v1.5**)*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![3GPP TR 38.901](https://img.shields.io/badge/3GPP-TR%2038.901%20Compliant-purple.svg)](https://www.3gpp.org/specifications-technologies)
[![Pyomo](https://img.shields.io/badge/Pyomo-MILP%20Engine-green)](http://www.pyomo.org/)
[![Coin-OR CBC](https://img.shields.io/badge/Solver-Coin--OR%20CBC%20(Open%20Source)-informational)](https://github.com/coin-or/Cbc)
[![XGBoost](https://img.shields.io/badge/XGBoost-Quantile%20q80-orange)](https://xgboost.readthedocs.io/)
[![CAMARA Ready](https://img.shields.io/badge/GSMA-CAMARA%20Open%20Gateway-blueviolet)](https://camaraproject.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Interactive%20App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Un réseau mobile qui anticipe sa saturation et se réorganise tout seul.**  
> Pipeline autonome complet (SON - *Self-Organizing Network*) combinant Machine Learning prédictif, propagation radio 3GPP tri-secteurs & multi-porteuses, et optimisation mathématique globale exacte (MILP) résolue en moins d'une seconde.

---

> ### 🧭 Vous voulez vraiment comprendre toute la logique de A à Z ?
> Pour les membres de jury, ingénieurs et chercheurs souhaitant comprendre l'intégralité du raisonnement, des métaphores intuitives jusqu'aux équations de propagation et aux choix d'ingénierie, consultez le document interactif central :  
> 👉 **[📘 Ouvrir le Rapport Explicatif Complet — WiseNet de A à Z (`docs/Rapport_WiseNet_Projet_Explique.html`)](docs/Rapport_WiseNet_Projet_Explique.html)**  
> *(Un guide complet, sans jargon inutile, optimisé pour lecture sur écran et export PDF direct).*

---

> [!NOTE]
> ### ⏪ Vous cherchez la Version 1.0 telle qu'elle était à l'origine ? / Looking for Version 1.0 as it was?
> Vous pouvez accéder à l'intégralité du **dépôt v1.0 d'origine intact**, avec son **code source initial et son README original affiché sur GitHub** :
> - 🌿 **[👉 Consulter le Dépôt v1.0 & son README Original sur GitHub (Branche `v1-stable`)](https://github.com/samya818/spatial-son-milp/tree/v1-stable)**
> - 🏷️ **[Tag Officiel Release v1.0 (`v1.0-validated`)](https://github.com/samya818/spatial-son-milp/tree/v1.0-validated)**
> - 📄 **[Lire la copie archivée du README v1.0 dans cette branche (`docs/README_v1.md`)](docs/README_v1.md)**
> - 💻 **En ligne de commande :** `git checkout v1-stable` *(ou `git clone -b v1-stable https://github.com/samya818/spatial-son-milp.git`)*

---

### 📌 Navigation Rapide des Versions & Ressources

| Ressource | Ce que vous y trouverez | Lien d'accès direct |
| :--- | :--- | :--- |
| **WiseNet v1.5 (Actuel)** | Architecture 3GPP multi-secteurs, double-porteuse $(s, f)$, boucle 24h, CAMARA API | **Ce document (README.md)** |
| **Version 1.0 (Dépôt & README Original)** | Accès direct au dépôt figé v1.0 tel qu'il était avec son README d'origine | [🌿 **Accéder à la v1.0 sur GitHub**](https://github.com/samya818/spatial-son-milp/tree/v1-stable) |
| **Le Guide de Référence (FR)** | L'explication pédagogique totale de A à Z (philosophie, physique, télécom) | [📘 `docs/Rapport_WiseNet_Projet_Explique.html`](docs/Rapport_WiseNet_Projet_Explique.html) |
| **README v1.0 (Copie Archivée)** | La documentation d'origine de la version 1.0 conservée dans `docs/` | [📄 `docs/README_v1.md`](docs/README_v1.md) |
| **Release v1.0-validated** | Tag officiel de la release V1 sur GitHub | [🏷️ Tag `v1.0-validated`](https://github.com/samya818/spatial-son-milp/releases/tag/v1.0-validated) |
| **Rapport Scientifique (EN)** | Benchmark vérifié, formulations mathématiques formelles & protocole | [🔬 `docs/WiseNet_V1_5_Scientific_Report.html`](docs/WiseNet_V1_5_Scientific_Report.html) |

---

## 📑 Sommaire
1. [🌟 Le Problème Télécom : Pourquoi WiseNet Existe ?](#-le-problème-télécom--pourquoi-wisenet-existe-)
2. [🧭 The Design Journey: Why Most Prediction-to-Action Systems Fail in the Real World](#-the-design-journey-why-most-prediction-to-action-systems-fail-in-the-real-world)
   - [The Trap We Had to Avoid](#the-trap-we-had-to-avoid)
   - [The Insight That Changed Everything](#the-insight-that-changed-everything)
   - [What This Means in Practice](#what-this-means-in-practice)
   - [🛡️ Démonstration Formelle : Pourquoi WiseNet Échappe à la Critique de Lucas](#%EF%B8%8F-démonstration-formelle--pourquoi-wisenet-échappe-à-la-critique-de-lucas)
   - [Vérification Directe dans le Code](#vérification-directe-dans-le-code)
   - [The Honest Limit (La Limite Honnête)](#the-honest-limit-la-limite-honnête)
3. [💡 La Philosophie WiseNet : L'Ingénierie Pragmatique](#-la-philosophie-wisenet--lingénierie-pragmatique)
4. [📖 L'Histoire de la V1.5 : Pourquoi cette Version et Pas une V2 ?](#-lhistoire-de-la-v15--pourquoi-cette-version-et-pas-une-v2-)
5. [🚀 Tout ce que Nous Avons Construit dans WiseNet V1.5 (Et Pourquoi)](#-tout-ce-que-nous-avons-construit-dans-wisenet-v15-et-pourquoi)
   - [Brique 1 : La Topologie Hexagonale 3GPP Tri-Secteurs](#brique-1--la-topologie-hexagonale-3gpp-tri-secteurs)
   - [Brique 2 : Le Spectre Double-Porteuse & L'Unité $(s, f)$](#brique-2--le-spectre-double-porteuse--lunité-s-f)
   - [Brique 3 : La Simulation Spatiale Micro-Grille & le RSRP Directif](#brique-3--la-simulation-spatiale-micro-grille--le-rsrp-directif)
   - [Brique 4 : Le Double Délestage (Horizontal vs Vertical)](#brique-4--le-double-délestage-horizontal-vs-vertical)
   - [Brique 5 : La Séparation Révolutionnaire Offline / Online](#brique-5--la-séparation-révolutionnaire-offline--online)
   - [Brique 6 : Le Cerveau Décisionnel MILP Exact (< 0.8s)](#brique-6--le-cerveau-décisionnel-milp-exact--08s)
   - [Brique 7 : La Boucle Fermée Prédictive 24h & ML Quantile $q_{80}$](#brique-7--la-boucle-fermée-prédictive-24h--ml-quantile-q_80)
   - [Brique 8 : L'Interface Industrielle CAMARA Open Gateway](#brique-8--linterface-industrielle-camara-open-gateway)
6. [📐 Le Pipeline de Bout en Bout en un Schéma](#-le-pipeline-de-bout-en-bout-en-un-schéma)
7. [📊 Les Preuves Scientifiques : Résultats Mesurés sur les Données de Milan](#-les-preuves-scientifiques--résultats-mesurés-sur-les-données-de-milan)
8. [🛡️ Pourquoi les Utilisateurs ne Subissent Jamais de Dégradation ?](#%EF%B8%8F-pourquoi-les-utilisateurs-ne-subissent-jamais-de-dégradation-)
9. [⚡ Démarrage Rapide & Commandes de Reproduction](#-démarrage-rapide--commandes-de-reproduction)
10. [🗂️ Organisation Détaillée du Code](#%EF%B8%8F-organisation-détaillée-du-code)
11. [👥 Crédits & Remerciements](#-crédits--remerciements)

---

## 🌟 Le Problème Télécom : Pourquoi WiseNet Existe ?

Imaginez un vendredi soir au centre-ville : des milliers de personnes sortent de bureaux ou assistent à un concert. Leurs téléphones saturent complètement l'antenne relais du quartier. Les appels coupent, les vidéos figent.  
Pourtant, à **300 mètres de là**, dans un quartier de bureaux désert, une autre antenne dispose de **70% de capacité libre et inutilisée**.

```
LA SITUATION CLASSIQUE (GASPILLAGE & SATURATION) :
+-----------------------------------+             +-----------------------------------+
|     Antenne A (Centre-Ville)      |             |     Antenne B (Zone Bureaux)      |
|    Charge : 130% [SATURATION]     |             |      Charge : 30% [SOUS-UTILISÉE] |
|   >>> Appels coupés, débits nuls  |             |   >>> Bande passante gaspillée    |
+-----------------------------------+             +-----------------------------------+
```

### Le Levier Magique : Le Handover et l'Offset A3
Dans les réseaux mobiles standardisés (4G LTE et 5G NR), un smartphone décide de basculer vers une autre antenne (*Handover*) selon la formule standard 3GPP (Événement A3) :

$$\text{RSRP}_{\text{voisin}} + \delta > \text{RSRP}_{\text{actuel}}$$

* **Le RSRP** (*Reference Signal Received Power*) mesure la puissance radio brute reçue par le mobile (en dBm).
* **L'Offset $\delta$** est une marge logicielle réglable à distance par l'opérateur (en dB).

Si l'opérateur augmente cet offset $\delta$ sur l'antenne A en faveur de l'antenne B, **les smartphones situés dans la zone frontière basculent automatiquement vers l'antenne B**, sans couper les appels et **sans dépenser un seul centime en nouveau matériel**.

### Le Défi : Pourquoi les Humains n'y arrivent pas ?
Un réseau urbain compte des centaines d'antennes interconnectées. Si l'antenne A décharge sur l'antenne B, l'antenne B risque de saturer à son tour et de devoir décharger sur C. C'est un **effet domino complexe**.  
**WiseNet** résout ce casse-tête de manière autonome : il **prédit** les congestions futures, **simule** la physique du signal et **calcule la combinaison mathématique parfaite de tous les offsets du réseau simultanément**, en moins d'une seconde.

---

## 🧭 The Design Journey: Why Most Prediction-to-Action Systems Fail in the Real World

When we started building WiseNet, we faced a question that breaks most ML-for-control projects:

> *You train a model to predict the future. Then you act on that prediction. But the moment you act, you change the very world the model was trained on. Does the prediction still mean anything?*

This is not a bug in the code. It is a structural trap. Across finance, economics, and network engineering, teams have watched their beautifully accurate models collapse the instant they went from "observing" to "steering." The model learned patterns from a world where nobody was steering. Once steering begins, the patterns change. The model, blind to its own influence, drifts into nonsense.

We knew that if WiseNet fell into this trap, it would not matter how elegant our optimizer was, or how clean our data was. The system would work beautifully on historical benchmarks and then quietly fail in production.

### The Trap We Had to Avoid

The naive way to build a SON optimizer is to predict *traffic per antenna*, then use those predictions to decide which antenna should offload to which neighbor. This feels intuitive. But it hides a fatal loop:

1. Your model learns: *"Antenna A usually carries this much traffic at 2 PM."*  
2. Then your policy says: *"Antenna A is overloaded — push users to Antenna B."*  
3. Next hour, Antenna A's traffic drops. Not because demand dropped, but because *you* moved it.  
4. The model looks at the new numbers and thinks: *"Demand on Antenna A is falling. I should predict less next time."*  
5. But demand never fell. You only hid it behind a handover. The model is now learning from its own shadow.

In control theory and macroeconomics, this is the **Lucas Critique (1976)**: a model trained under passive observation loses validity the moment it becomes an active policy participant. In modern machine learning, it is called **Performative Prediction**: the predictor performs an action that reshapes the distribution it is trying to predict.

We refused to accept that this was inevitable.

### The Insight That Changed Everything

We stopped and asked: ***What if the thing we predict is not the thing we control?***

In a mobile cellular network, users do not choose which antenna serves them. They choose to open an app, stream a video, send a message. That decision — how much data they consume — happens in a physical place: a 235-meter square on the Milan grid. It is an organic human behavior. It does not change just because the network quietly hands them off from one tower to another.

So we redesigned the architecture around a simple but strict causal separation:

* **Predict the ground, not the tower.**  
  Our model predicts demand per geographic cell (`square_id`) — the actual human activity on the ground. This demand exists independently of network policy. A handover does not move the person, and it does not change how much data they want.
* **Control the assignment, not the demand.**  
  The optimizer decides how to distribute that fixed, predicted demand across antennas using physical signal models. It moves the *connection*, never the *behavior*.

Because the predicted quantity (ground demand) is causally untouched by the controlled quantity (antenna offsets), the model's training distribution remains valid even after deployment. The world the model learned from — organic human traffic patterns — is the same world it continues to predict into. The policy redistributes what is already there; it does not alter what is coming.

### What This Means in Practice

In our closed-loop validation, the model sees lag features, rolling averages, and seasonal patterns drawn from historical demand per geographic cell. These features describe human rhythms: morning commutes, lunch spikes, evening streaming. They are unaffected by whether yesterday's optimizer shifted load from sector 3 to sector 7.

If we had instead trained on traffic *per antenna*, those same lags would be poisoned. A spike at 2 PM might be a real demand surge, or it might be a residual from an aggressive offset at 1:30 PM. The model could not tell the difference. The signal would be corrupted by the system's own past decisions.

By keeping the prediction layer anchored to geography and the control layer anchored to radio assignment, we created a one-way street: predictions flow forward, decisions flow sideways. They never loop back to contaminate the source.

---

### 🛡️ Démonstration Formelle : Pourquoi WiseNet Échappe à la Critique de Lucas

Formellement, cette séparation causale se traduit dans le code et dans les mathématiques du système :

| Couche | Ce qu'elle fait | Niveau d'analyse | Régime Causal |
| :--- | :--- | :--- | :--- |
| **Prédiction ML** (`src/ml/predictor.py`) | XGBoost Quantile $q_{80}$ prédit le volume de trafic par `square_id` | **Cellule géographique** ($235\text{ m} \times 235\text{ m}$) | **Exogène :** la demande humaine dans un carré ne dépend pas de l'antenne qui la dessert |
| **Modèle spatial** (`src/spatial/simulator_v1_5.py`) | Matrices de fractions $H$ calculées par physique 3GPP (distance, azimut, fréquence) | Point de grille $\to$ Antenne | **Mécanique :** loi de propagation radio déterministe, pas statistique |
| **Optimisation MILP** (`src/optimization/milp_engine_v1_5.py`) | Choix des offsets $\delta$ pour minimiser la congestion résiduelle $\sum e_{s,f}$ | **Cellule radio $(s, f)$** (Antenne / Secteur / Porteuse) | **Endogène :** l'action ne modifie que l'attribution radio, jamais la demande brute |

#### La Preuve Mathématique de Non-Contamination
Si $v_c$ est la demande prédite pour la cellule géographique $c$, et $M(\delta)$ la matrice de redistribution physique induite par l'offset $\delta$, le volume arrivant sur chaque antenne est :

$$V_{\text{antenne}} = M(\delta) \cdot v_{\text{cellule}}$$

Et la dérivée fondamentale qui garantit la stabilité absolue du système est :

$$\frac{\partial v_{\text{cellule}}}{\partial \delta} = 0$$

La demande au sol est **causalement invariante sous l'action**. L'offset ne fait que modifier le routage radio de cette demande. Le modèle ML, entraîné sur des trajectoires historiques où aucun délestage n'avait lieu ($\delta = 0$), reste donc **100% valide sous intervention active**. Il continue de prédire la véritable demande organique, que le MILP réaffecte ensuite mécaniquement.

### Vérification Directe dans le Code
Dans [`src/simulation/closed_loop_v1_5.py`](src/simulation/closed_loop_v1_5.py), la boucle fermée s'enchaîne rigoureusement :
1. **Lecture** : Lecture de la télémétrie par coordonnée géographique (`square_id`).
2. **Prédiction** : `preds_t_plus_1 = model.predict(X_geo)` $\to$ estimation de la demande future au sol.
3. **Optimisation** : MILP sur le tenseur $H$ (produit des fractions physiques $F$ et des prédictions $v$).
4. **Action** : Application des offsets optimaux sur les secteurs.

À aucun moment le modèle ML n'est entraîné ou alimenté par un compteur de trafic mesuré au niveau du pylône après délestage. Les features d'historique (lags, moyennes mobiles, saisonnalité) portent exclusivement sur la demande géographique au sol, qui est totalement imperméable aux décisions d'offsets.

### The Honest Limit (La Limite Honnête)
Cette protection tient **tant et seulement tant que** la mesure d'entrée du modèle reste la **demande organique par zone géographique**, et non un compteur radio interne agrégé par station de base après application des handovers.

En déploiement réel sur le réseau d'un opérateur (via l'API CAMARA `Network Insights`), il faudra veiller à ce que la télémétrie ingérée corresponde à un proxy de **demande au sol** (par exemple les compteurs par cellule de couverture initiale ou par zone de localisation), et non à des compteurs de charge post-handover. Si l'on réinjectait comme données d'entraînement des compteurs d'antennes post-optimisation, la boucle fermée deviendrait endogène et la critique de Lucas s'appliquerait de plein droit.

> 💎 **En résumé :**  
> *"We did not build a better predictor. We built a system where prediction and control occupy different causal lanes."*  
> *(WiseNet survit à la critique de Lucas non par artifice, mais parce que son architecture découple causalement ce qui relève du comportement humain exogène de ce qui relève de l'ingénierie radio endogène).*

---

## 💡 La Philosophie WiseNet : L'Ingénierie Pragmatique

WiseNet repose sur une vision claire de ce que doit être l'intelligence artificielle appliquée aux télécommunications :

* **1. Agilité Temps Réel (< 1s) vs Inertie Théorique :**  
  Un réseau n'attend pas. Si un algorithme prend 20 minutes à calculer, la foule s'est déjà dispersée et les abonnés ont déjà subi des coupures. WiseNet optimise 756 cellules en **0.74 seconde**.
* **2. Démocratie Open Source vs Rente Logicielle :**  
  Pas de solveurs propriétaires à 10 000 € la licence (Gurobi/CPLEX) nécessaires pour tester le projet. WiseNet tourne à 100% avec des briques libres et auditables : Python, Pyomo et **Coin-OR CBC**.
* **3. Prudence Prédictive ($q_{80}$) vs Moyenne Naïve :**  
  En réseau mobile, sous-estimer un pic de trafic provoque des coupures d'appels dramatiques. Surestimer légèrement un pic est sans conséquence néfaste. WiseNet dimensionne donc ses décisions sur le pire cas raisonnable (quantile 80%).
* **4. Séparation Fondamentale Offline / Online :**  
  Ne jamais recalculer en direct ce qui ne change pas. La géométrie de la ville et les bilans de liaison radio sont précalculés une fois pour toutes hors-ligne, libérant toute la puissance de calcul pour la décision en temps réel.
* **5. Branchement Industriel Concret (CAMARA) :**  
  Un modèle mathématique isolé sur un PC n'a que peu de valeur pour un opérateur. WiseNet intègre nativement les API internationales **GSMA Open Gateway** pour être prêt à être déployé sur un cœur de réseau moderne (O-RAN Non-RT RIC).

*(Pour approfondir toute cette démarche conceptuelle, lisez le [Rapport Explicatif WiseNet](docs/Rapport_WiseNet_Projet_Explique.html)).*

---

## 📖 L'Histoire de la V1.5 : Pourquoi cette Version et Pas une V2 ?

À la fin de la V1 (qui prouvait le concept avec 73.53% de réduction de congestion sur un modèle simplifié), une question d'ingénierie majeure s'est posée : **Que construire ensuite ?**

### Le Piège du "Plan V2 Trop Ambitieux"
Une version "V2 ultra-théorique" avait d'abord été envisagée :
- Modéliser les micro-interférences dynamiques instantanées entre tous les téléphones.
- Recalculer les matrices physiques du réseau à chaque cycle (15 à 25 minutes de calcul continu).
- Déployer un solveur commercial lourd sous licence payante propriétaire.
- Résoudre un problème de 12 600 variables non-linéaires.

### L'Arbitrage Pragmatique : Pourquoi la V1.5 est un Choix Supérieur
Dans le cadre de projets d'innovation et de compétitions technologiques (notamment le hackathon **GSMA + Nokia MENA Ignite 2026**), ce plan V2 présentait des défauts rédhibitoires :
1. **Un temps de démonstration trop court :** Devant un jury ou un directeur technique, une démonstration dure quelques minutes. Un système qui fait attendre 20 minutes pour calculer un cycle est inutilisable.
2. **Une barrière de licence artificielle :** Dépendre de licences privées brise l'accessibilité open-source du projet.
3. **Une déconnexion des priorités opérateur :** Les opérateurs valorisent l'interopérabilité standardisée (API GSMA CAMARA) bien avant une équation d'interférence académique.

> 🎯 **Le Choix WiseNet V1.5 :**  
> *"Garder ce qui marche parfaitement (la rapidité sub-seconde, la programmation linéaire MILP, le solveur gratuit Coin-OR CBC, la boucle fermée), mais rendre le modèle radio 100% fidèle aux normes industrielles 3GPP et connecter le système aux vraies API des opérateurs télécoms."*

---

## 🚀 Tout ce que Nous Avons Construit dans WiseNet V1.5 (Et Pourquoi)

Voici le détail chronologique et fonctionnel des avancées majeures apportées dans la V1.5 :

---

### Brique 1 : La Topologie Hexagonale 3GPP Tri-Secteurs
*Fichier : [`src/topology/builder_v1_5.py`](src/topology/builder_v1_5.py)*

* **Dans la V1 :** Les antennes étaient positionnées de façon aléatoire et émettaient en cercle uniforme (antenne isotrope). En réalité, aucune antenne urbaine n'émet en rond !
* **Ce qu'on a fait en V1.5 :** Nous avons déployé une **grille hexagonale déterministe 3GPP TR 38.901** sur les $56.55\text{ km}^2$ de la ville de Milan (1 024 cellules réelles) :
  * **126 sites macro physiques** espacés d'une distance inter-site stricte ($\text{ISD} = 750\text{ mètres}$).
  * Chaque site est découpé en **3 secteurs directionnels de $120^\circ$** orientés précisément à $0^\circ$ (Nord), $120^\circ$ (Sud-Est) et $240^\circ$ (Sud-Ouest), comme 3 parts de pizza couvrant l'espace.
* **Pourquoi ce choix ?** Cela reproduit fidèlement la géométrie réelle du réseau déployé par un opérateur comme Telecom Italia (TIM) en milieu urbain dense. *(Voir section 2.3 du [Rapport Explicatif](docs/Rapport_WiseNet_Projet_Explique.html))*.

---

### Brique 2 : Le Spectre Double-Porteuse & L'Unité $(s, f)$
*Fichier : [`src/topology/builder_v1_5.py`](src/topology/builder_v1_5.py)*

* **Le Constat Réel :** Un pylône de télécommunication n'a pas une seule fréquence magique. Il superpose plusieurs couches fréquentielles.
* **Ce qu'on a fait en V1.5 :** Nous avons injecté les licences spectrales officielles de l'opérateur TIM Italie :
  1. **Porteuse $F_1$ (LTE Band 3 - 1.8 GHz FDD, 20 MHz) :** La bande d'ancrage, qui porte loin et traverse bien les murs, avec une capacité nominale de **$6\,600.8\text{ Mo} / 30\text{ min}$**.
  2. **Porteuse $F_2$ (5G NR n78 - 3.5 GHz TDD, 80 MHz) :** La bande ultra-capacitaire haut débit, avec une capacité massive de **$32\,580.2\text{ Mo} / 30\text{ min}$**.
* **L'Unité Élémentaire $(s, f)$ :**  
  Chaque site physique comporte $3\text{ secteurs} \times 2\text{ porteuses} = \mathbf{6\text{ cellules radio logiques distinctes}}$.  
  Sur les 126 sites du réseau de Milan, cela crée **756 cellules radio $(s, f)$ indépendantes**.
* **Pourquoi ce choix ?** La saturation ne frappe jamais un pylône entier en bloc : elle touche par exemple la fréquence 3.5 GHz du secteur Nord pendant un match. Optimiser par couple $(s, f)$ est la seule manière d'obtenir un contrôle de niveau chirurgical.

---

### Brique 3 : La Simulation Spatiale Micro-Grille & le RSRP Directif
*Fichier : [`src/spatial/simulator_v1_5.py`](src/spatial/simulator_v1_5.py)*

* **Le Problème de la Donnée Milan :** Le jeu de données de Milan fournit le trafic global sur des carrés de $235\text{ m} \times 235\text{ m}$. Si on traite ce carré comme un point unique, on perd toute la finesse de ce qui se passe à ses bords.
* **Ce qu'on a fait en V1.5 :**
  1. **Micro-discrétisation :** Chaque carré de $235\text{m}$ est découpé en une grille de **$20 \times 20 = 400\text{ sous-pixels}$** de $11.75\text{ m} \times 11.75\text{ m}$ chacun.
  2. **Calcul RSRP 3GPP conforme aux normes :** Pour chaque sous-pixel, nous calculons la puissance reçue selon la formule officielle :
     $$\text{RSRP} = P_{\text{tx}} - \text{PathLoss}(d, f) + G(\Delta\theta)$$
     où $G(\Delta\theta) = -\min[12 \cdot (\Delta\theta / 65^\circ)^2, 30\text{ dB}]$ est le gain d'antenne directive selon l'écart angulaire avec l'axe du secteur.
* **Pourquoi ce choix ?** Un utilisateur situé exactement dans l'axe d'un secteur reçoit un signal puissant, alors qu'à même distance mais sur le côté, le signal chute de 15 à 30 dB. Prendre en compte l'azimut $\Delta\theta$ est indispensable pour ne pas faire basculer des utilisateurs dans le vide.

---

### Brique 4 : Le Double Délestage (Horizontal vs Vertical)
*Fichiers : [`src/spatial/simulator_v1_5.py`](src/spatial/simulator_v1_5.py) & [`src/optimization/milp_engine_v1_5.py`](src/optimization/milp_engine_v1_5.py)*

Raisonner au niveau $(s, f)$ a permis de débloquer une capacité d'optimisation inédite en deux dimensions :

```
                        ┌──────────────────────────────────────────────┐
                        │      DÉLESTAGE VERTICAL (INTER-BANDES)       │
                        │ Bascule 3.5 GHz -> 1.8 GHz sur le MÊME SITE  │
                        └──────────────────────┬───────────────────────┘
                                               │
                                               ▼
+------------------------------------+                   +------------------------------------+
|         SITE 1 - SECTEUR 0         |                   |         SITE 2 - SECTEUR 2         |
| Porteuse F2 (3.5 GHz) [Saturée]    |                   |                                    |
|              ▲                     |   DÉLESTAGE       |                                    |
|  (Vertical)  │                     |  HORIZONTAL       |                                    |
|              ▼                     | (Inter-Secteurs)  |                                    |
| Porteuse F1 (1.8 GHz) [Capacité]   | ════════════════► | Porteuse F1 (1.8 GHz) [Disponible] |
+------------------------------------+                   +------------------------------------+
```

1. **Délestage Horizontal (Spatial) :** Les utilisateurs situés en bordure géographique d'un secteur basculent vers le secteur voisin (sur le même site ou un site adjacent).
2. **Délestage Vertical (Fréquentiel) :** Si la porteuse 5G (3.5 GHz) est saturée alors que la 4G (1.8 GHz) du **même secteur physique** a de la marge, les utilisateurs basculent de fréquence **sans même changer d'antenne géographique** !

---

### Brique 5 : La Séparation Révolutionnaire Offline / Online
*Fichier : [`src/spatial/simulator_v1_5.py`](src/spatial/simulator_v1_5.py)*

* **Pourquoi le calcul radio est-il lent d'ordinaire ?** Parce que calculer la propagation radio sur 409 600 sous-pixels pour 756 cellules et 7 niveaux d'offset demande des dizaines de millions d'opérations trigonométriques.
* **Le Coup de Génie Architectural :**  
  La position des immeubles et des antennes ne bouge pas toutes les 30 minutes !  
  Nous avons donc calculé les fractions de transfert **une seule fois pour toutes en mode Offline** et sauvegardé les tenseurs massiques normalisés (`fractions_v1_5.parquet`).
* **En Mode Online (Temps Réel) :**  
  À chaque créneau de 30 minutes, il suffit de multiplier ces fractions précalculées par le volume de trafic prédit pour obtenir instantanément les matrices de délestage $H$. Ce calcul prend **moins de 0.05 seconde** !

---

### Brique 6 : Le Cerveau Décisionnel MILP Exact (< 0.8s)
*Fichier : [`src/optimization/milp_engine_v1_5.py`](src/optimization/milp_engine_v1_5.py)*

* **Pyomo + Coin-OR CBC :**  
  Pyomo formule le problème sous forme linéaire et le solveur open-source **CBC** le résout sans aucune clé payante.
* **Pourquoi le MILP écrase les algorithmes gloutons ("Greedy") ?**  
  Une règle gloutonne raisonne antenne par antenne de façon égoïste : *"je suis saturé, je déverse tout sur ma voisine de droite"*. Mais si la voisine de droite s'apprête elle aussi à saturer, l'heuristique crée une catastrophe en cascade.  
  Le MILP, lui, regarde **les 756 cellules en un seul bloc matriciel** et trouve l'optimum global qui maximise le bien-être de l'ensemble du réseau.
* **Temps d'exécution mesuré :** **$0.74\text{ seconde}$** pour résoudre 5 292 variables binaires sous contrainte stricte de conservation de la masse.

---

### Brique 7 : La Boucle Fermée Prédictive 24h & ML Quantile $q_{80}$
*Fichier : [`src/simulation/closed_loop_v1_5.py`](src/simulation/closed_loop_v1_5.py)*

* **Dans la réalité, on ne connaît pas le futur :** Décider à $t$ pour la période $t+1$ nécessite d'anticiper le trafic.
* **XGBoost Quantile $q_{80}$ :**  
  Prédire une moyenne est une erreur en télécom : si vous sous-estimez le pic, le réseau s'effondre. Nous entraînons un modèle XGBoost sur le **quantile 80%**. C'est un choix d'ingénierie volontairement prudent : *"préparons le réseau au niveau de charge du pire cas raisonnable"*.
* **Validation Continue sur 24 Heures :**  
  Nous avons simulé une journée entière (48 créneaux de 30 minutes consécutifs) sur le jeu de données réel de Milan (**43.57 Terabytes de données transitées**). Le système prend ses décisions sur la prédiction ML, puis ces décisions sont confrontées à la vérité terrain mesurée.
* **Résultat :** Le système capture **98.7% de l'efficacité d'un Oracle théorique parfait** (qui connaîtrait l'avenir par magie).

---

### Brique 8 : L'Interface Industrielle CAMARA Open Gateway
*Fichier : [`src/camara/client.py`](src/camara/client.py)*

Pour que WiseNet s'insère dans l'architecture télécom standardisée mondiale (initiative **GSMA Open Gateway** / **O-RAN Non-RT RIC**) :
1. **API CAMARA Network Insights :** Permet à WiseNet d'ingérer le trafic et la télémétrie de n'importe quel opérateur compatible via des requêtes REST JSON standardisées.
2. **API CAMARA Quality on Demand (QoD) :** Agit comme un **filet de sécurité**. Si, même après l'optimisation mathématique globale, un résidu microscopique de congestion persiste dans une cellule, WiseNet déclenche une session QoD prioritaire pour garantir la bande passante des services d'urgence ou critiques.
3. **Connecteur universel :** Fonctionne avec authentification OAuth2 `client_credentials`, avec bascule instantanée entre Sandbox réel et Mock haute-fidélité.

---

## 📐 Le Pipeline de Bout en Bout en un Schéma

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 1. PHASE HORS-LIGNE (OFFLINE)                           │
│                       Calculé 1 seule fois à la configuration du réseau                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
      ┌──────────────────────────────────────┴──────────────────────────────────────┐
      ▼                                                                             ▼
[Topologie Hexagonale 3GPP]                                              [Grille de Milan 1024]
126 sites x 3 secteurs x 2 porteuses                                     400 micro-pixels par carré
= 756 cellules radio logiques (s, f)                                     Résolution spatiale : 11.75 m
      │                                                                             │
      └──────────────────────────────────────┬──────────────────────────────────────┘
                                             ▼
                          [Simulation RSRP Directif 3GPP]
                         P_tx - PL(d,f) + G(Δθ) sur 400 pts
                                             │
                                             ▼
                     [Matrices de Fractions Précalculées H]
                      Fractions délestées / reçues conservées
                      (Sauvegardées dans fractions_v1_5.parquet)

═══════════════════════════════════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 2. PHASE EN LIGNE (ONLINE)                              │
│                         Exécutée en boucle fermée toutes les 30 minutes                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
                      [Télémétrie Télécom Italia / CAMARA Insights]
                           Trafic historique récent observé
                                             │
                                             ▼
                          [Modèle Prédictif XGBoost Quantile q80]
                         Prédiction prudente du trafic futur à t+1
                                             │
                                             ▼
                        [Instanciation Dynamique des Volumes H]
                         Volume H = Fractions Offline x Trafic Prédit
                                             │
                                             ▼
                       [Cerveau Mathématique MILP (Pyomo + CBC)]
                       Optimisation globale exacte sur 756 cellules
                       Temps de résolution : 0.74 seconde (< 1s)
                                             │
                                             ▼
                      [Application des Décisions d'Offsets (0 à 3 dB)]
                     Délestage Horizontal (spatial) + Vertical (bande)
                                             │
                                             ▼
                   [Vérification Terrain & Filet de Sécurité CAMARA QoD]
                   Mesure de la charge réelle + sessions QoD résiduelles
                                             │
                                             ▼
                           [Prochain Cycle (Boucle Continue)]
```

---

## 📊 Les Preuves Scientifiques : Résultats Mesurés sur les Données de Milan

Toutes les mesures sont reproductibles via les scripts du dépôt et s'appuient sur le jeu de données réel **Telecom Italia Big Data Challenge** (`work_1024cells.parquet`).

### 1. Au Pic Maximal de Congestion (Créneau de 30 min - $1.38\text{ To}$ de trafic)
*Exécution : `python -m src.benchmark.benchmark_v1_5`*

| Stratégie Testée | Trafic Perdu / Congestionné | Équivalent Go | Gain vs Réseau Figé | Temps de Calcul |
| :--- | :---: | :---: | :---: | :---: |
| **Réseau Statique (Figé)** ($\delta = 0\text{ dB}$) | 314 331.7 Mo | 306.96 Go | Référence (0.0 %) | 0.00 s |
| **Heuristique Gloutonne** (Locale, cellule par cellule) | 269 055.3 Mo | 262.75 Go | 14.40 % | 0.01 s |
| **WiseNet V1.5 MILP** (Optimisation Globale Exacte) | **260 686.1 Mo** | **254.58 Go** | **17.07 %** | **0.74 s** |

*Résultat : Le MILP sauve **+8 369.2 Mo (+8.37 Go)** de données supplémentaires par rapport au glouton en un seul créneau.*

---

### 2. Évaluation sur une Journée Complète de 24 Heures (48 Créneaux - $43.57\text{ To}$ de trafic)
*Exécution : `python -m src.benchmark.benchmark_24h_v1_5`*

| Stratégie Opérationnelle | Saturation Cumulée 24h (Go) | Réduction de Congestion | Temps Moyen par Cycle |
| :--- | :---: | :---: | :---: |
| **Réseau Statique** (Non géré) | 5 072.57 Go (~5.07 To) | Référence | — |
| **Heuristique Gloutonne** (Local) | 3 852.84 Go | 24.05 % | 0.012 s |
| **WiseNet V1.5 MILP** (Multi-Porteuses) | **3 670.99 Go** | **27.63 %** | **0.576 s** |

---

### 3. Boucle Fermée Prédictive (Incertitude ML Réelle sur 24h)
*Exécution : `python -m src.simulation.closed_loop_v1_5`*

Dans ce test ultime, le solveur ne triche pas : il ne voit pas les données futures et optimise uniquement sur ce que le modèle XGBoost $q_{80}$ lui prédit :

```
EFFICACITÉ RELATIVE PAR RAPPORT À L'ORACLE CLAIRVOYANT IDÉAL (100%) :
Oracle Théorique Parfait  [████████████████████████████████████████] 100.0% (Plafond théorique)
WiseNet MILP Prédictif    [███████████████████████████████████████ ]  98.7% (Capture quasi-parfaite !)
Heuristique Gloutonne     [██──────────────────────────────────────]  86.0% (Pertes d'opportunités)
```

* **+123.56 Go d'information délivrée en plus** par rapport à l'heuristique prédictive.
* **Conservation stricte de la masse** vérifiée mathématiquement à $10^{-6}$ près : aucun mégaoctet n'est détruit ou créé par erreur.

---

## 🛡️ Pourquoi les Utilisateurs ne Subissent Jamais de Dégradation ?

Une inquiétude fréquente est : *"Si un utilisateur consomme beaucoup de données au milieu de la cellule, le système va-t-il le forcer à basculer et détruire sa connexion ?"*

La conception de WiseNet apporte une **garantie physique absolue** en trois points :
1. **La qualité radio est purement physique :** Le RSRP dépend de la distance et de l'angle directif du secteur. Il ne dépend pas de la charge de l'antenne. Le système ne peut jamais prétendre qu'un mauvais signal est bon.
2. **Le centre de cellule est protégé :** Un smartphone proche de son antenne reçoit un signal très fort (ex. $-75\text{ dBm}$). L'antenne voisine arrive à $-105\text{ dBm}$. Un offset maximal de $3\text{ dB}$ ne comblera jamais un écart de $30\text{ dB}$. Ces utilisateurs ne basculent **jamais**.
3. **Seule la frange frontière bascule :** Seuls les utilisateurs situés là où les signaux des deux antennes sont presque égaux (écart $< 3\text{ dB}$) sont invités à changer. Pour eux, le changement est totalement transparent et imperceptible.

*(Pour l'analyse approfondie de cette démonstration, voir section 1.9 du [Rapport Explicatif](docs/Rapport_WiseNet_Projet_Explique.html)).*

---

## ⚡ Démarrage Rapide & Commandes de Reproduction

### 1. Installation en 2 Minutes

```bash
# Cloner le projet
git clone https://github.com/samya818/spatial-son-milp.git
cd spatial-son-milp

# Créer l'environnement virtuel Python
python -m venv .venv

# Activer l'environnement :
# Sur Windows :
.\.venv\Scripts\activate
# Sur Linux / macOS :
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Reproduire les Benchmarks V1.5 Immédiatement

```bash
# Lancer le benchmark officiel au pic de charge (0.74s)
python -m src.benchmark.benchmark_v1_5

# Lancer le benchmark complet sur 24 heures (48 slots)
python -m src.benchmark.benchmark_24h_v1_5

# Lancer la boucle fermée prédictive complète (ML + MILP)
python -m src.simulation.closed_loop_v1_5
```

### 3. Explorer le Cahier de Recherche Interactif V1.5

```bash
# Ouvrir le notebook pas-à-pas avec visualisations graphiques
jupyter notebook research/notebooks_v1_5/pipeline_v1_5.ipynb
```

### 4. Lancer le Tableau de Bord Visuel

```bash
python -m streamlit run scripts/dashboard/app.py
```
Ouvrez votre navigateur sur `http://localhost:8501`.

---

## 🗂️ Organisation Détaillée du Code

L'arborescence du projet fait cohabiter l'historique V1 et la nouvelle architecture V1.5 en toute clarté :

```text
spatial-son-milp/
├── docs/                                   # DOCUMENTATION & RAPPORTS
│   ├── Rapport_WiseNet_Projet_Explique.html # 📘 GUIDE CENTRAL : Rapport explicatif de A à Z (HTML)
│   ├── README_v1.md                        # 📄 README d'origine de la v1.0 (sauvegardé)
│   ├── WiseNet_V1_5_Scientific_Report.html # 🔬 Rapport scientifique V1.5 complet (HTML)
│   └── WiseNet_V1_5_Scientific_Report.md   # 📝 Version Markdown pour consultation GitHub
│
├── src/                                    # CODE SOURCE EN PRODUCTION
│   ├── topology/
│   │   ├── builder.py                      # Topologie v1.0 isotrope
│   │   └── builder_v1_5.py                 # ⭐ Topologie v1.5 (Hexagonale 3GPP, tri-secteurs, TIM 1.8/3.5GHz)
│   ├── spatial/
│   │   ├── simulator.py                    # Simulateur spatial v1.0
│   │   └── simulator_v1_5.py               # ⭐ Simulateur v1.5 (Micro-grilles 400 pts, RSRP directif, tenseur H)
│   ├── optimization/
│   │   ├── milp_engine.py                  # Solveur v1.0
│   │   ├── milp_engine_v1_5.py             # ⭐ Cerveau MILP v1.5 (Pyomo, variables (s,f), Coin-OR CBC)
│   │   └── greedy_engine_v1_5.py           # Heuristique gloutonne conservatrice de référence
│   ├── simulation/
│   │   ├── closed_loop_sim.py              # Boucle fermée v1.0
│   │   └── closed_loop_v1_5.py             # ⭐ Boucle prédictive v1.5 (XGBoost q80 + MILP sur 24h)
│   ├── benchmark/
│   │   ├── benchmark_v1_5.py               # Script benchmark pic 30 min
│   │   └── benchmark_24h_v1_5.py           # Script benchmark continu 24h
│   └── camara/
│       └── client.py                       # ⭐ Client API CAMARA GSMA (Network Insights & QoD)
│
├── research/
│   ├── notebooks_v1_5/
│   │   └── pipeline_v1_5.ipynb             # 📓 Cahier de recherche reproductible v1.5
│   └── notebooks/                          # Notebooks exploratoires d'origine (v1.0)
│
├── scripts/
│   └── dashboard/                          # Application Streamlit interactive
├── tests/                                  # Tests de non-régression et de conservation de masse
├── check_environment.py                    # Script de vérification de l'environnement et du solveur
└── requirements.txt                        # Liste des bibliothèques nécessaires
```

---

## 👥 Crédits & Remerciements

* **Loukili Samya** — Architecte du projet, modélisation mathématique MILP, pipeline 3GPP et intégration CAMARA.
* **Kenza El Khaniri** — Ingestion des séries temporelles, analyse spatiale et modélisation radio.
* Sous la direction académique et la supervision de **M. Toufik Massrour** (ENSAM Meknès).

### Références Normalisées
* **3GPP TR 38.901** : *Channel model for frequencies from 0.5 to 100 GHz (Urban Macro specifications).*
* **3GPP TS 36.331 / TS 38.331** : *Radio Resource Control (RRC) — Event A3 Handover offset parameters.*
* **GSMA Open Gateway & CAMARA Project** : *Quality on Demand (QoD) & Network Insights APIs Specifications.*
* **Telecom Italia Big Data Challenge** : *Open telecommunications density grid of the City of Milan.*

# 🛰️ WiseNet (Spatial SON-MILP) — Version 1.5

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![3GPP TR 38.901](https://img.shields.io/badge/3GPP-TR%2038.901%20Compliant-purple.svg)](https://www.3gpp.org/specifications-technologies)
[![Pyomo](https://img.shields.io/badge/Pyomo-MILP%20Engine-green)](http://www.pyomo.org/)
[![Coin-OR CBC](https://img.shields.io/badge/Solver-Coin--OR%20CBC-informational)](https://github.com/coin-or/Cbc)
[![XGBoost](https://img.shields.io/badge/XGBoost-Quantile%20q80-orange)](https://xgboost.readthedocs.io/)
[![CAMARA Ready](https://img.shields.io/badge/GSMA-CAMARA%20Open%20Gateway-blueviolet)](https://camaraproject.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Interactive%20App-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Système Prédictif d'Auto-Organisation de Réseau (SON) par Optimisation Mathématique Globale (MILP) et Modélisation Radio 3GPP Multi-Secteurs & Multi-Porteuses.**

---

### 📌 Navigation des Versions & Documentation

| Document | Description | Lien d'accès |
| :--- | :--- | :--- |
| **WiseNet v1.5 (Actuel)** | Topologie 3GPP 3-secteurs, multi-porteuses $(s, f)$, boucle 24h, CAMARA API | **Ce README** |
| **README v1.0 (Archivé)** | Documentation d'origine de la version 1.0 (modèle isotrope) | [📄 `docs/README_v1.md`](docs/README_v1.md) |
| **Branche Git v1-stable** | Code source original figé et validé de la V1.0 | [🌿 Branche `v1-stable`](https://github.com/samya818/spatial-son-milp/tree/v1-stable) |
| **Release v1.0-validated** | Tag Git officiel de la première version validée | [🏷️ Tag `v1.0-validated`](https://github.com/samya818/spatial-son-milp/releases/tag/v1.0-validated) |
| **Rapport Explicatif de A à Z** | Guide pédagogique complet en français (théorie, physique, métaphores) | [📘 `docs/Rapport_WiseNet_Projet_Explique.html`](docs/Rapport_WiseNet_Projet_Explique.html) |
| **Rapport Scientifique V1.5** | Benchmark complet, preuves reproductibles & formulation mathématique | [🔬 `docs/WiseNet_V1_5_Scientific_Report.html`](docs/WiseNet_V1_5_Scientific_Report.html) |

---

## 📑 Sommaire
1. [🎯 Le Problème Télécom & L'Intuition](#-le-problème-télécom--lintuition)
2. [🔄 Évolution : Quoi de Neuf dans la V1.5 ?](#-évolution--quoi-de-neuf-dans-la-v15-)
3. [🧠 Architecture Globale & Dualité Offline / Online](#-architecture-globale--dualité-offline--online)
4. [📐 Modélisation Physique 3GPP & Calcul du RSRP](#-modélisation-physique-3gpp--calcul-du-rsrp)
5. [⚙️ Le Cerveau Décisionnel : Formulation MILP $(s, f)$](#%EF%B8%8F-le-cerveau-décisionnel--formulation-milp-s-f)
6. [📊 Résultats Scientifiques & Benchmarks Vérifiables](#-résultats-scientifiques--benchmarks-vérifiables)
7. [🌐 Agnosticisme 4G/5G & Intégration CAMARA Open Gateway](#-agnosticisme-4g5g--intégration-camara-open-gateway)
8. [🛡️ Cas des Utilisateurs & Robustesse aux Frontières](#%EF%B8%8F-cas-des-utilisateurs--robustesse-aux-frontières)
9. [🚀 Démarrage Rapide & Reproductibilité](#-démarrage-rapide--reproductibilité)
10. [🗂️ Arborescence du Dépôt](#%EF%B8%8F-arborescence-du-dépôt)
11. [👥 Auteurs & Références](#-auteurs--références)

---

## 🎯 Le Problème Télécom & L'Intuition

Dans les réseaux mobiles (4G/5G), le trafic des utilisateurs fluctue fortement dans l'espace et dans le temps. Fréquemment, **une antenne se retrouve saturée** (saturation vidéo, streaming, foule) alors que **l'antenne immédiatement voisine dispose de capacité inutilisée** à quelques centaines de mètres.

```
Situation de Congestion Non-Optimisée :
+--------------------------+         +--------------------------+
|  Site A (Centre-Ville)   |         |   Site B (Zone Résid.)   |
|   Charge : 130% [SATURÉ] |         |   Charge : 35% [LIBRE]   |
|   >>> Pertes d'appels    |         |   >>> Capacité dormante  |
|   >>> Débit dégradé      |         |                          |
+--------------------------+         +--------------------------+
```

### Le Mécanisme Clé : Handover et Offset de Décharge (A3 Offset)
Un smartphone bascule d'une antenne vers une autre (Handover) selon la règle standardisée 3GPP (Événement A3) :

$$\text{RSRP}_{\text{voisin}} + \delta > \text{RSRP}_{\text{actuel}}$$

* **Le RSRP** (*Reference Signal Received Power*) est la puissance reçue en dBm mesurant la qualité physique du signal.
* **L'Offset $\delta$ (en dB)** est une marge logicielle ajustable à distance par l'opérateur.
* En augmentant artificiellement $\delta$, **l'antenne saturée incite ses utilisateurs situés en bordure à basculer vers l'antenne voisine disponible**, absorbant ainsi le surplus de trafic **sans couper la communication et sans déployer de matériel physique**.

**WiseNet** automatise ce réglage en boucle fermée (*Self-Organizing Network*) : il anticipe les pics de charge via Machine Learning, simule la propagation spatiale fine, et calcule en moins d'une seconde les offsets optimaux pour l'ensemble du réseau grâce à la programmation linéaire en nombres entiers (**MILP**).

---

## 🔄 Évolution : Quoi de Neuf dans la V1.5 ?

La version 1.0 validait le concept avec une antenne isotrope (omnidirectionnelle) sur une seule porteuse fictive.  
La **version 1.5** franchit un cap industriel en adoptant les standards stricts **3GPP TR 38.901** et les spectres réels d'un opérateur national (Telecom Italia - TIM) :

| Dimension | Version 1.0 (Legacy) | Version 1.5 (Actuelle) | Impact Industriel |
| :--- | :--- | :--- | :--- |
| **Topologie Antennaire** | 200 sites aléatoires, isotropes (émission en cercle) | **Grille hexagonale déterministe 3GPP (126 sites, 378 secteurs à $120^\circ$)** | Conforme aux schémas réels de déploiement macro urbain (ISD = 750m) |
| **Spectre Fréquentiel** | 1 bande abstraite | **Double-porteuse réelle : LTE Band 3 (1.8 GHz) + 5G NR n78 (3.5 GHz)** | Prise en compte de la Carrier Aggregation et des bandes mixtes FDD/TDD |
| **Unité d'Optimisation** | Antenne globale | **Cellule Radio Élémentaire $(s, f)$ (756 cellules logiques)** | Optimisation fine par secteur directionnel ET par fréquence |
| **Type de Décharge** | Uniquement horizontal spatial | **Double délestage : Horizontal (spatial) + Vertical (inter-porteuses)** | Permet de basculer le trafic 3.5 GHz vers le 1.8 GHz sur le *même site* |
| **Physique du Signal** | Affaiblissement simple $d^{-3.76}$ | **RSRP 3GPP complet : Path-loss NLOS + Diagramme de rayonnement directif** | Évaluation rigoureuse de l'angle d'azimut ($\Delta\theta$) et du lobe |
| **Discrétisation Spatiale** | Barycentre de cellule | **Micro-grille de 400 sous-pixels par carré ($11.75\text{ m} \times 11.75\text{ m}$)** | Précision spatiale métrique de la bascule d'utilisateurs |
| **Interface Opérateur** | Simulation isolée | **Client API CAMARA Open Gateway (Network Insights & QoD)** | Prêt pour le branchement O-RAN / Non-RT RIC |

---

## 🧠 Architecture Globale & Dualité Offline / Online

La force maîtresse de WiseNet est sa **séparation stricte entre le calcul physique géométrique lourd (réalisé une seule fois, Offline)** et **la décision mathématique temps réel (exécutée en boucle fermée toutes les 30 min, Online)** :

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          1. PHASE HORS-LIGNE (OFFLINE)                      │
│             Calculé UNE FOIS pour la topologie (Indépendant du trafic)      │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ├─► Topologie 3GPP (126 sites, 378 secteurs, 756 cellules s,f)
          ├─► Discrétisation de la grille de Milan en 409 600 micro-pixels (400 / carré)
          ├─► Calcul des champs RSRP 3GPP : P_tx - PL(d,f) + G(Δθ)
          └─► Évaluation des transitions d'offsets (δ ∈ [0.0; 3.0] dB)
                   │
                   ▼
          [Tenseurs de Fractions de Transfert Massiques H] (Conservatifs)

┌─────────────────────────────────────────────────────────────────────────────┐
│                          2. PHASE EN LIGNE (ONLINE)                         │
│               Exécutée à chaque cycle opérationnel de 30 minutes            │
└─────────────────────────────────────────────────────────────────────────────┘
  Données Réelles de Trafic (Milan) ou Télémétrie CAMARA Network Insights
          │
          ▼
  [Brique ML - XGBoost Quantile q80]
  Prédiction prudente : "Quel est le pire scénario raisonnable à t+1 ?"
          │
          ▼
  [Instanciation Dynamique des Volumes H]
  Volume(s, f, δ) = Trafic Prédit × Fraction Hors-Ligne
          │
          ▼
  [Solveur MILP - Pyomo + Coin-OR CBC]
  Résolution globale en ~0.74 seconde sur 756 cellules
  Choix optimal des offsets z_{s, f, k} minimisant la congestion résiduelle
          │
          ▼
  [Action Réseau & Bouclage Fermé]
  Application des offsets + Monitoring de dérive statistique (Page-Hinkley)
```

---

## 📐 Modélisation Physique 3GPP & Calcul du RSRP

Pour chaque sous-pixel $k$ à la position $(x_k, y_k)$ et chaque cellule radio élémentaire $(s, f)$ :

### 1. Affaiblissement de Parcours (3GPP UMi NLOS)
$$\text{PL}(d_k, f) = 32.4 + 36.7 \cdot \log_{10}(\max(d_k, 5.0)) + 20 \cdot \log_{10}(f_{\text{GHz}})$$

### 2. Diagramme de Rayonnement Directif du Secteur
Pour un secteur d'azimut $\theta_s$ ($0^\circ, 120^\circ, 240^\circ$) et un angle utilisateur $\theta_k$ :
$$\Delta\theta_{k, s} = |\theta_k - \theta_s| \pmod{360^\circ}$$
$$G(\Delta\theta) = -\min \left[ 12 \left( \frac{\Delta\theta}{65^\circ} \right)^2, \; 30.0\text{ dB} \right]$$

### 3. Puissance Reçue Finale (RSRP)
$$\text{RSRP}(k, s, f) = P_{\text{tx}}(f) - \text{PL}(d_k, f) + G(\Delta\theta_{k, s})$$

### 4. Capacité Shannon Réaliste par Porteuse
Calculée sur la fenêtre de 30 minutes ($1\,800\text{ s}$) avec une efficacité spectrale $\eta_{\text{spec}} = 0.60$ et un facteur d'utilisation $\mu = 0.60$ :

$$C_{s, f} = \frac{B_f \cdot \log_2\left(1 + 10^{\frac{\text{SINR}_f}{10}}\right) \cdot \eta_{\text{spec}} \cdot \mu \cdot 1800}{8 \times 10^6} \quad [\text{Mo / 30 min}]$$

* **Porteuse $F_1$ (1.8 GHz LTE - Ancrage Couverture)** : Bande $20\text{ MHz}$, $P_{\text{tx}} = 43\text{ dBm}$ ($20\text{ W}$), $\text{SINR} = 12\text{ dB} \implies \mathbf{6\,600.8\text{ Mo / 30 min}}$.
* **Porteuse $F_2$ (3.5 GHz 5G NR - Couche Capacitaire)** : Bande $80\text{ MHz}$, $P_{\text{tx}} = 43\text{ dBm}$ eff., $\text{SINR} = 15\text{ dB} \implies \mathbf{32\,580.2\text{ Mo / 30 min}}$.

---

## ⚙️ Le Cerveau Décisionnel : Formulation MILP $(s, f)$

L'optimisation globale ne se fait ni par antenne globale, ni par fréquence seule, mais au niveau du **couple indissociable $(s, f)$**.

### Variables de Décision
* $z_{c, k} \in \{0, 1\}$ : Variable binaire activant le niveau d'offset $k \in \{0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0\}\text{ dB}$ pour la cellule radio $c = (s, f)$.
* $e_c \ge 0$ : Variable continue d'écart représentant le surplus de trafic insatisfait (congestion) sur la cellule $c$.

### Fonction Objectif Globale
Minimiser la congestion résiduelle totale cumulée sur **l'ensemble des secteurs ET des porteuses** du réseau :

$$\min \sum_{c \in \mathcal{C}} e_c \quad \text{avec } \mathcal{C} = \{ (s, f) \mid s \in \text{Secteurs}, f \in \{F_1, F_2\} \}$$

### Contraintes Mathématiques Fondamentales
1. **Unicité de la Décision :**
   $$\sum_{k \in \mathcal{K}} z_{c, k} = 1, \quad \forall c \in \mathcal{C}$$

2. **Bilan de Charge & Conservation Exacte de la Masse :**
   Le volume final sur une cellule $c$ après délestage doit satisfaire :
   $$e_c \ge V_c^{\text{initial}} - \sum_{k \in \mathcal{K}} H_{c, k}^{\text{offload}} z_{c, k} + \sum_{c' \in \mathcal{C}} \sum_{k \in \mathcal{K}} H_{c, c', k}^{\text{recv}} z_{c', k} - C_c, \quad \forall c \in \mathcal{C}$$

> 💡 **Le Double Délestage Activé :**
> - **Délestage Horizontal :** Une cellule $(s_1, F_1)$ saturée déverse vers $(s_2, F_1)$ sur la même fréquence en bordure spatiale.
> - **Délestage Vertical :** Une cellule $(s_1, F_2)$ saturée déverse directement vers $(s_1, F_1)$ sur le **même secteur physique**, exploitant la flexibilité fréquentielle sans aucun déplacement géographique.

---

## 📊 Résultats Scientifiques & Benchmarks Vérifiables

Toutes les évaluations sont exécutées sur les données réelles du **Telecom Italia Big Data Challenge** (bloc dense de **1 024 cellules** de Milan, $56.55\text{ km}^2$, fichier vérifié `work_1024cells.parquet`).

### 1. Benchmark au Pic de Trafic (Slot 30 min - $1.38\text{ To}$ de demande)
*Fichier de test : [`src/benchmark/benchmark_v1_5.py`](src/benchmark/benchmark_v1_5.py)*

| Politique de Décision | Trafic Insatisfait (Mo) | Équivalent (Go) | Réduction Congestion | Temps de Résolution |
| :--- | :---: | :---: | :---: | :---: |
| **Base Statique** ($\delta = 0\text{ dB}$) | 314 331.7 Mo | 306.96 Go | Référence (0.0 %) | 0.00 s |
| **Heuristique Gloutonne** (Local Heuristic) | 269 055.3 Mo | 262.75 Go | 14.40 % | 0.01 s |
| **WiseNet V1.5 MILP** (Global Exact $(s, f)$) | **260 686.1 Mo** | **254.58 Go** | **17.07 %** | **0.74 s** |

*Gain net du MILP sur le glouton : **+8 369.2 Mo (+8.37 Go)** de trafic supplémentaire délivré en un seul créneau.*

---

### 2. Évaluation Continue sur 24 Heures (48 Slots Consécutifs - $43.57\text{ To}$ de trafic réel)
*Fichier de test : [`src/benchmark/benchmark_24h_v1_5.py`](src/benchmark/benchmark_24h_v1_5.py)*

| Politique de Gestion | Volume Insatisfait 24h (Mo) | Volume Insatisfait (Go) | Réduction Congestion 24h | Temps Moyen / Slot |
| :--- | :---: | :---: | :---: | :---: |
| **Base Statique** ($\delta = 0\text{ dB}$) | 5 194 316.4 Mo | 5 072.57 Go | Référence (0.0 %) | 0.000 s |
| **Heuristique Gloutonne** (Locale) | 3 945 312.0 Mo | 3 852.84 Go | 24.05 % | 0.012 s |
| **WiseNet V1.5 MILP** (Global Multi-Porteuse) | **3 759 094.1 Mo** | **3 670.99 Go** | **27.63 %** | **0.576 s** |

---

### 3. Boucle Fermée Prédictive Complète (XGBoost Quantile $q_{80}$ + MILP)
*Fichier de test : [`src/simulation/closed_loop_v1_5.py`](src/simulation/closed_loop_v1_5.py)*  
Évaluation en conditions réelles d'incertitude : les décisions à $t$ sont prises uniquement d'après la prédiction $\hat{V}(t+1) = \text{XGBoost}_{q80}(X(t))$ et appliquées strictement sur le ground-truth réel du réseau :

| Stratégie en Boucle Fermée | Volume Réel Insatisfait (Mo) | Gain Réel vs Statique | Capture de l'Oracle Idéal |
| :--- | :---: | :---: | :---: |
| **Base Statique** (Aucun contrôle) | 5 237 032.6 Mo | — | — |
| **Glouton Prédictif** (ML $\to$ Glouton) | 4 027 345.0 Mo | 23.10 % | 86.0 % |
| **WiseNet MILP Prédictif** (ML $\to$ MILP) | **3 900 818.1 Mo** | **25.51 %** | **98.7 %** |
| **Oracle Clairvoyant** (Théorique maximum avec futur parfait) | 3 831 104.0 Mo | 26.85 % | 100.0 % |

#### 🔑 Découvertes Clés
1. **+123.56 Go d'information sauvée** : Sous incertitude ML, le MILP délivre **126 526.9 Mo (+123.56 Go)** de trafic de plus que l'approche gloutonne sur 24 heures.
2. **Efficacité Oracle de 98.7%** : L'utilisation de la régression quantile ($q_{80}$) absorbe les micro-variations de trafic et permet au MILP d'égaler presque la perfection théorique d'un oracle connaissant le futur.
3. **Résolution ultra-rapide (0.57s)** : Le problème sur 756 cellules et 5 292 variables binaires est résolu en une fraction de seconde avec le solveur open-source CBC, s'insérant parfaitement dans le budget opérationnel de 30 minutes.

---

## 🌐 Agnosticisme 4G/5G & Intégration CAMARA Open Gateway

### Agnosticisme Technologique
Le moteur WiseNet est nativement **indépendant de la technologie sous-jacente (4G ou 5G)** :
* En 4G (LTE, TS 36.331) comme en 5G (NR, TS 38.331), le mécanisme de handover repose sur la même mesure normalisée (**RSRP**) et le même déclencheur (**Événement A3**).
* L'architecture multi-secteurs et multi-porteuses modélise fidèlement un site d'antennes moderne (**eNodeB / gNodeB**).

### Intégration Standardisée CAMARA Open Gateway (GSMA)
WiseNet s'interface avec les API réseaux standardisées de l'industrie :

```
                          ┌──────────────────────────┐
                          │   CAMARA Open Gateway    │
                          └─────────────┬────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
     [API Network Insights]                         [API Quality on Demand]
     Lecture télémétrique temps réel                Filet de sécurité résiduel
     (Charge cellules, latence, débit)              (Priorisation de flux critique)
                 │                                             ▲
                 ▼                                             │
      WiseNet Prédiction ML                         Surplus résiduel non absorbé
                 │                                             │
                 └──────────────► WiseNet MILP ────────────────┘
```

1. **CAMARA Network Insights** : Permet de lire l'état du trafic en temps réel pour alimenter le modèle de prédiction ML.
2. **CAMARA Quality on Demand (QoD)** : Sert de filet de sécurité activé pour les flux prioritaires résiduels si une cellule reste saturée même après l'optimisation par offset.
3. **Connecteur Python Intégré** : Implémenté dans [`src/camara/client.py`](src/camara/client.py) avec support OAuth2 Client Credentials et bascule transparente Sandbox / Mock.

---

## 🛡️ Cas des Utilisateurs & Robustesse aux Frontières

> **Question légitime :** *Si les utilisateurs d'une cellule consomment des volumes de données différents, le système risque-t-il de dégrader la connexion de certains d'entre eux ?*

La réponse physique et algorithmique est **non**, pour trois raisons structurelles :

1. **La granularité spatiale fine :** Une cellule de Milan mesure $235\text{ m} \times 235\text{ m}$ (quelques pâtés de maisons). La variance interne est négligeable par rapport aux écarts inter-cellules, et notre discrétisation en **400 sous-pixels de $11.75\text{ m}$** isole précisément la localisation de chaque utilisateur.
2. **Le RSRP est une grandeur purement physique :** Le calcul de qualité du signal dépend de la distance, de la fréquence et de l'angle d'azimut. **Il ne dépend pas de la charge de l'antenne**. Aucun utilisateur ne peut être basculé vers une antenne dont le signal radio est physiquement médiocre.
3. **Seuls les utilisateurs de bordure sont concernés :** Les utilisateurs situés au centre de leur cellule reçoivent un signal prépondérant : aucun offset raisonnable ($\le 3\text{ dB}$) ne peut les faire basculer. Seuls les utilisateurs situés dans la zone de chevauchement où deux signaux sont quasi-équivalents sont migrés, garantissant une transition imperceptible et sans coupure.

---

## 🚀 Démarrage Rapide & Reproductibilité

### 1. Installation de l'Environnement

```bash
# Cloner le dépôt
git clone https://github.com/samya818/spatial-son-milp.git
cd spatial-son-milp

# Créer et activer l'environnement virtuel
python -m venv .venv

# Windows (PowerShell) :
.\.venv\Scripts\activate
# Linux / macOS :
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Exécuter les Benchmarks V1.5 en Ligne de Commande

```bash
# 1. Benchmark au Pic de Charge (Slot 30-min sur 1024 cellules)
python -m src.benchmark.benchmark_v1_5

# 2. Benchmark Complet 24 Heures (48 slots continus)
python -m src.benchmark.benchmark_24h_v1_5

# 3. Simulation Boucle Fermée Prédictive (ML XGBoost q80 + MILP)
python -m src.simulation.closed_loop_v1_5
```

### 3. Explorer le Notebook de Recherche Interactif V1.5

```bash
# Lancer Jupyter Notebook pour explorer les 5 phases de validation
jupyter notebook research/notebooks_v1_5/pipeline_v1_5.ipynb
```

### 4. Lancer le Tableau de Bord Interactif

```bash
python -m streamlit run scripts/dashboard/app.py
```
Accédez à l'interface via votre navigateur sur `http://localhost:8501`.

---

## 🗂️ Arborescence du Dépôt

```text
spatial-son-milp/
├── docs/                                   # DOCUMENTATION & RAPPORTS
│   ├── README_v1.md                        # 📄 README original archivé de la v1.0
│   ├── Rapport_WiseNet_Projet_Explique.html # 📘 Guide explicatif de A à Z (HTML interactif)
│   ├── WiseNet_V1_5_Scientific_Report.html # 🔬 Rapport scientifique officiel V1.5 (HTML)
│   ├── WiseNet_V1_5_Scientific_Report.md   # 📝 Rapport scientifique V1.5 (Markdown)
│   └── make_v1_5_html.py                   # Script de génération du rapport HTML
├── src/                                    # CODE SOURCE DE PRODUCTION
│   ├── topology/
│   │   ├── builder.py                      # Topologie v1.0 (antennes isotropes)
│   │   └── builder_v1_5.py                 # ⭐ Topologie v1.5 (Hexagonale 3GPP, 3 secteurs, double-porteuse)
│   ├── spatial/
│   │   ├── simulator.py                    # Simulateur spatial v1.0
│   │   └── simulator_v1_5.py               # ⭐ Simulateur v1.5 (Micro-grilles, RSRP directif, tenseur H)
│   ├── optimization/
│   │   ├── milp_engine.py                  # Moteur MILP v1.0
│   │   ├── milp_engine_v1_5.py             # ⭐ Moteur MILP v1.5 (Pyomo, variables (s,f), Coin-OR CBC)
│   │   └── greedy_engine_v1_5.py           # Heuristique gloutonne conservatrice de référence
│   ├── simulation/
│   │   ├── closed_loop_sim.py              # Boucle fermée v1.0
│   │   └── closed_loop_v1_5.py             # ⭐ Boucle fermée v1.5 (ML XGBoost q80 + MILP sur 24h)
│   ├── benchmark/
│   │   ├── benchmark_v1_5.py               # Benchmark au pic de charge (1.38 To)
│   │   └── benchmark_24h_v1_5.py           # Benchmark sur 24 heures (48 slots, 43.57 To)
│   └── camara/
│       └── client.py                       # ⭐ Client API CAMARA Open Gateway (Network Insights & QoD)
├── research/
│   ├── notebooks_v1_5/
│   │   └── pipeline_v1_5.ipynb             # 📓 Cahier de recherche v1.5 (démonstration pas-à-pas)
│   └── notebooks/                          # Notebooks originaux v1.0 (phases 01 à 15)
├── scripts/
│   └── dashboard/                          # Application Streamlit interactive
├── tests/                                  # Tests unitaires et d'intégrité massique
├── check_environment.py                    # Vérificateur de solveur CBC et de dépendances
├── requirements.txt                        # Dépendances de production
└── LICENSE                                 # Licence Open-Source MIT
```

---

## 👥 Auteurs & Références

### Équipe du Projet
* **Loukili Samya** — Conception algorithmique, modélisation MILP et intégration CAMARA.
* **Kenza El Khaniri** — Pipeline de données spatio-temporelles et modélisation radio.
* Projet encadré par **M. Toufik Massrour** (ENSAM Meknès).

### Références Normalisées & Scientifiques
* **3GPP TR 38.901** : *Study on channel model for frequencies from 0.5 to 100 GHz (Urban Macro / Urban Micro).*
* **3GPP TS 36.331 / TS 38.331** : *Radio Resource Control (RRC) Protocol Specification — Event A3 Handover Configuration.*
* **GSMA Open Gateway & CAMARA Project** : *Network Insights API & Quality on Demand (QoD) API Specifications (2025/2026).*
* **Telecom Italia Big Data Challenge (2015)** : *Open Spatio-temporal cellular network dataset of the city of Milan.*

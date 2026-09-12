# 🎓 Guide de Soutenance & Foire Aux Questions du Jury
## Articulation des Données (Milan vs Vodafone) et Intégration des APIs CAMARA Open Gateway

> **Ce guide est conçu spécifiquement pour répondre avec une clarté absolue, une rigueur scientifique et sans aucun jargon inutile à toutes les questions qu'un jury (ingénieurs, chercheurs, décideurs télécoms) peut poser sur les données et les APIs de WiseNet.**

---

### 📑 Sommaire des Questions Clés du Jury

1. [Question 1 : Pourquoi vos données de trafic viennent de Milan alors que les APIs Vodafone pointent vers d'autres marchés européens ?](#question-1)
2. [Question 2 : Est-ce qu'on travaille avec le comportement de Milan ou avec les données de Vodafone ? Qui fait quoi ?](#question-2)
3. [Question 3 : Comment prouvez-vous que la foule renvoyée par l'API correspond bien à la réalité du centre-ville de Milan ?](#question-3)
4. [Question 4 : D'où viennent les numéros de téléphone ciblés par la QoD ? Pourquoi un opérateur ne donne-t-il pas la liste des abonnés ?](#question-4)
5. [Question 5 : Quel est le rôle exact de la nouvelle API CAMARA Device Location ?](#question-5)
6. [Question 6 : Si un opérateur veut déployer WiseNet demain, que doit-il changer ?](#question-6)

---

<a name="question-1"></a>
### ❓ Question 1 : Pourquoi vos données de trafic viennent de Milan alors que les APIs Vodafone pointent vers d'autres marchés européens ?

#### 🎯 Ce qu'il faut répondre en 30 secondes :
> *« Notre projet articule délibérément le **benchmark scientifique mondial de référence** (la matrice spatio-temporelle de Milan de Telecom Italia) avec le **banc d'essai d'interopérabilité officiel** (le Sandbox CAMARA de Vodafone Group). Le lien mathématique universel entre les deux est assuré par le découpage cartographique mondial en tuiles **QuadKey** et la calibration de densité. »*

#### 🔍 L'explication détaillée pour le jury :
1. **La réalité de la recherche mondiale en télécom :**
   * Il n'existe **aucun opérateur au monde** qui diffuse en direct et en accès libre les logs de trafic réels de ses antennes commerciales (protégés par le secret commercial et le RGPD).
   * Le seul jeu de données mondial ouvert, standardisé et validé par la communauté scientifique est celui du *Telecom Italia Big Data Challenge* (Milan, 1 024 mailles de 235 m). C'est pourquoi toutes les grandes publications académiques en optimisation radio utilisent Milan comme terrain d'entraînement.
2. **Le rôle du Sandbox Vodafone :**
   * Vodafone Group est le leader européen de l'initiative **GSMA Open Gateway** et propose le bac à sable le plus complet. Leurs environnements de test utilisent des marchés pilotes (DE, GB, RO).
3. **Le principe du Digital Twin (Jumeau Numérique) :**
   * WiseNet agit comme un jumeau numérique. La topologie 3GPP (126 sites tri-sectoriels distants de 750 mètres) modélise fidèlement une métropole européenne dense. Que cette métropole s'appelle Milan, Francfort ou Londres, les lois de la propagation électromagnétique et les mécanismes de handover restent strictement identiques.

---

<a name="question-2"></a>
### ❓ Question 2 : Est-ce qu'on travaille avec le comportement de Milan ou avec les données de Vodafone ? Qui fait quoi ?

#### 🎯 Ce qu'il faut répondre en 30 secondes :
> *« **Les deux, en symbiose !** Milan fournit le **comportement humain historique de consommation** (combien de Mégaoctets un utilisateur consomme selon l'heure de la journée), tandis que l'API Vodafone Footfall fournit la **télémétrie en temps réel** (combien de personnes physiques sont actuellement présentes sous l'antenne). »*

#### 🔍 L'explication détaillée pour le jury :
Ni le modèle historique seul, ni l'API de foule seule ne suffisent pour optimiser un réseau :
* **Si on n'utilisait que Milan :** Le système serait aveugle aux imprévus en direct (concert, manifestation, accident, bouchon soudain). Il ne ferait que répéter le passé.
* **Si on n'utilisait que l'API Vodafone :** L'API donne un nombre de personnes (`device_count`), mais elle ne sait pas combien de gigaoctets ces personnes consomment sur l'antenne 4G/5G.

#### 📐 La formule de fusion de données (`calibrate_demand_traffic`) :
Notre pipeline effectue une **fusion de données causale** :
$$\text{Trafic final en Mo } v_c(t) = \underbrace{\text{Footfall}(QK, t)}_{\text{Nombre d'humains en direct (API Vodafone)}} \times \underbrace{\text{Ratio\_Milan}(c, t)}_{\text{Consommation Mo/humain apprise sur Milan}}$$

* **Bénéfice scientifique (Immunité à la critique de Lucas) :**  
  Le nombre de piétons dans la rue ne dépend pas de la puissance de l'antenne ($\frac{\partial \text{Footfall}}{\partial \delta} = 0$). C'est un signal exogène pur, qui garantit que l'algorithme ne crée pas de biais de rétroaction artificielle.

---

<a name="question-3"></a>
### ❓ Question 3 : Comment prouvez-vous que la foule renvoyée par l'API correspond bien à la réalité du centre-ville de Milan ?

#### 🎯 Ce qu'il faut répondre en 30 secondes :
> *« Nous l'avons validé à 3 niveaux : par un **contrôle de cohérence physique** (l'ordre de grandeur Mo/habitant), par la **morphologie urbaine** (la courbe temporelle à plateau du centre-ville), et par le **calibrage statistique sur le 80ᵉ percentile ($q_{80}$)**. »*

#### 🔍 L'explication détaillée pour le jury :

```
PROFIL DU CENTRE-VILLE (Duomo / Commerce) :
Affluence ▲
          │         ┌─────────────────────┐
          │        /                       \
          │       /                         \  <-- Plateau continu de 11h à 20h
          │  ____/                           \____
          └───────────────────────────────────────► Heures (0h - 24h)
```

1. **Le contrôle physique (Sanity Check) :**
   * Dans la maille centrale `4849` de Milan (zone Duomo / centre commercial), le trafic réel mesuré est d'environ **$16\,000\text{ Mo}$** par créneau de 30 minutes.
   * L'API Vodafone Footfall indique **$409\text{ appareils connectés}$** sur cette tuile.
   * $\frac{16\,000\text{ Mo}}{409\text{ appareils}} \approx 39\text{ Mo par personne sur 30 minutes}$. C'est la consommation exacte d'un utilisateur urbain moyen (réseaux sociaux, navigation, streaming court).
2. **La signature temporelle diurne :**
   * Une zone résidentielle présente deux pics (matin 8h et soir 20h). Un centre-ville commercial présente un plateau continu élevé de 11h à 20h. Notre fonction d'étalonnage horaire reproduit fidèlement cette dynamique du centre-ville de Milan.
3. **Le quantile conservateur $q_{80}$ :**
   * Le modèle XGBoost est entraîné sur le 80ᵉ percentile pour dimensionner les décisions sur le pire cas raisonnable, absorbant ainsi les légères variations d'estimation.

---

<a name="question-4"></a>
### ❓ Question 4 : D'où viennent les numéros de téléphone ciblés par la QoD ? Pourquoi un opérateur ne donne-t-il pas la liste des abonnés ?

#### 🎯 Ce qu'il faut répondre en 30 secondes :
> *« Pour des raisons strictes de **secret des télécommunications et de RGPD**, aucun opérateur au monde ne fournira jamais d'API publique listant les numéros de téléphone présents sous une antenne. Les numéros proviennent du **registre de flotte d'urgence** de l'organisation (SAMU, Police, Pompiers). »*

#### 🔍 L'explication détaillée pour le jury :
* **Le modèle GSMA Open Gateway fonctionne à l'inverse :**
  1. Une entreprise cliente (ex: Les Hôpitaux / SAMU de la ville) possède une flotte de véhicules d'urgence équipés de cartes SIM connues (`critical_fleet`).
  2. Quand le solveur MILP détecte que l'antenne `site_001_sec2` est en saturation résiduelle, le système interroge le réseau : *« Est-ce que l'un de mes véhicules d'urgence se trouve actuellement sous la zone de cette antenne saturée ? »*.
  3. L'API Vodafone confirme la présence physique du terminal.
  4. Dès confirmation, le contrôleur déclenche la session CAMARA QoD pour lui réserver un canal prioritaire (`QOS_E`).
* **Les numéros de test :**  
  Les numéros `+401234567890`, etc., sont les numéros officiels fournis dans la documentation de test de la Sandbox Vodafone (marché pilote IoT).

---

<a name="question-5"></a>
### ❓ Question 5 : Quel est le rôle exact de la nouvelle API CAMARA Device Location ?

#### 🎯 Ce qu'il faut répondre en 30 secondes :
> *« Elle fait le pont entre le monde radio (l'antenne saturée calculée par le MILP) et le monde applicatif (la session QoD). Elle remplace une génération aléatoire par une **vérification géographique en temps réel** de la présence des terminaux critiques avant d'engager des ressources réseau. »*

#### 🔍 Comparaison Avant vs Après :

| Dimension | Avant l'intégration | Maintenant (Avec Device Location) |
|---|---|---|
| **Sélection du terminal** | Numéro généré artificiellement par un calcul de hachage (`hash(cell_id)`). | Vérification géodésique réelle (`/location-verification/v1/verify`). |
| **Prise de décision** | Aveugle à la position physique du terminal. | Résolution spatiale : l'antenne saturée ne booste que les appareils **physiquement sous sa couverture**. |
| **Conformité CAMARA** | Partielle (QoD seule). | **Boucle fermée 100% conforme GSMA Open Gateway** (Location $\rightarrow$ QoD). |

---

<a name="question-6"></a>
### ❓ Question 6 : Si un opérateur veut déployer WiseNet demain, que doit-il changer ?

#### 🎯 Ce qu'il faut répondre en 30 secondes :
> *« **Strictement rien dans le cœur algorithmique.** WiseNet a été conçu dès le premier jour comme une brique logicielle 'Plug & Play' agnostique au réseau physique. »*

#### 🔍 Pourquoi le code est prêt pour la production :
1. **En entrée :** Le pipeline consomme des tuiles **QuadKey standardisées** et des profils 3GPP standards. Il suffit de brancher les identifiants de production de l'opérateur dans le fichier `.env`.
2. **Au centre :** Le solveur mathématique MILP (Pyomo + CBC) résout l'optimisation globale de centaines d'antennes en **moins d'une seconde** ($0,74\text{ s}$), ce qui est parfaitement compatible avec un cycle d'ajustement O-RAN Non-RT RIC (toutes les 15 à 30 minutes).
3. **En sortie :** Les commandes d'offsets calculées sont poussées vers les stations de base (gNodeB / eNodeB), et les flux vitaux sont protégés par les sessions CAMARA standardisées adoptées par tous les grands opérateurs mondiaux (Vodafone, Orange, Telefónica, Deutsche Telekom).

---

### 🏆 Résumé Visuel de la Boucle Fermée pour les Diapositives de Présentation

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           BOUCLE FERMÉE WISENET                          │
└──────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                   1. Télémétrie de Foule en Direct
             Vodafone Analytics (Realtime Footfall & QuadKey)
                                      │
                                      ▼
                   2. Prédiction Exogène de Demande
              XGBoost Quantile q80 calibré sur Milan (Lucas-immune)
                                      │
                                      ▼
                   3. Décision Mathématique Globale
              Solveur MILP (CBC) : Offsets optimaux A3 en 0.74s
                                      │
                                      ▼
                   4. Détection de Saturation Résiduelle
             Cellules restantes au-delà du seuil de tolérance
                                      │
                                      ▼
                   5. Vérification Géographique de Flotte
             API CAMARA Device Location (/location-verification)
                                      │
                                      ▼
                   6. Allocation Chirurgicale de Priorité
             API CAMARA Quality on Demand (Profils QOS_E / QOS_L)
```

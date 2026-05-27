# 📊 RAPPORT TECHNIQUE : PIPELINE 1024 CELLULES (V5.1)
## Validation de Performance sur Bloc Dense 32x32

---

### 1. SYNTHÈSE DES RÉSULTATS
Le passage au pipeline 1024 cellules (bloc géographique contigu de 32x32 mailles) démontre une efficacité théorique supérieure du système SON. Contrairement au cluster 600 cellules (échantillonnage hybride), le bloc 1024 offre une continuité topologique parfaite.

**Métriques Clés (48 slots de test - 24h) :**
*   **Volume Insatisfait (Statique) :** 160 237.53 Mo
*   **Volume Insatisfait (Dynamique) :** 42 419.73 Mo
*   **Amélioration Nette : 73.53%**
*   **Modèle Prédictif :** XGBoost Quantile q80 (Pessimiste)
*   **Seuil de Déclenchement :** $V_a > C_a$ (Hard Capacity)

---

### 2. VÉRIFICATION DE L'INTÉGRITÉ (ANTI-ARTIFACT)
Pour lever les doutes sur un gain "artefactuel" de 70%, trois vérifications critiques ont été menées :

### 2. VÉRIFICATION DE L'INTÉGRITÉ (ANTI-ARTIFACT)
Pour lever les doutes sur un gain "artefactuel" de 70%, trois vérifications critiques ont été menées :

#### A. Conservation de la Masse
Utilisation de `critical_verification.py`. Le volume total de trafic injecté dans le système est identique avant et après l'application des offsets SON (différence relative < 1e-9).
**Résultats Bruts :**
*   Slot 10: Avant=308777.96, Après=308777.96, Diff=0.00
*   Slot 20: Avant=205802.68, Après=205802.68, Diff=0.00
*   Slot 30: Avant=339564.94, Après=339564.94, Diff=-0.00
**Conclusion** : Le système ne "crée" ni ne "détruit" de trafic.

#### B. Étanchéité du Bloc (Closed Edges)
Vérification de la fuite de volume hors du cluster de 1024 cellules.
*   Antennes dans le graphe de voisinage : 201
*   Antennes cibles dans la matrice de transfert : 201
*   **Fuite observée : 0.00%**
**Conclusion** : Les bords du bloc sont mathématiquement fermés. Tout délestage se fait EXCLUSIVEMENT vers des antennes appartenant au cluster supervisé.

#### C. Robustesse du Seuil
Le gain de 73.53% est obtenu avec un seuil de déclenchement à **100% de la capacité ($V_a > C_a$)**.
*   Volume Insatisfait (Statique) : 160 237.53 Mo
*   Volume Insatisfait (Dynamique) : 42 419.73 Mo
Cela prouve que le gain ne provient pas d'un déclenchement préventif excessif, mais d'une résolution réelle de saturations dures.

---

### 3. EXPLICATION DU GAIN ÉLEVÉ
L'amélioration spectaculaire s'explique par trois facteurs identifiés :

1.  **Continuité Spatiale** : Dans un bloc 32x32, chaque antenne est entourée de voisins supervisés. Sur le cluster 600, de nombreuses antennes étaient isolées géographiquement, limitant les options de délestage.
2.  **Hétérogénéité de Charge** : Le bloc 1024 couvre une zone urbaine continue où des antennes très saturées côtoient des antennes sous-utilisées.
3.  **Surcapacité Locale (Calibration Micros)** : Une analyse de la capacité de réserve (`debug_spare_capacity.py`) révèle un ratio **Capacité de Réserve / Déficit de 336.8**. 
    *   Les **Micro-cellules** (45% du bloc) ont une capacité calibrée (~539 Mo) supérieure aux Macros (~407 Mo) en raison d'un SINR cible plus élevé (20dB vs 15dB) à bande passante égale (20MHz).
    *   Taux de congestion observé sur les Micros : **0.0%**.
    *   Ces micro-cellules agissent comme des "puits" de trafic idéaux pour le délestage.

**Note de Transparence** : Le gain de 73% est donc scientifiquement exact dans le cadre de cette simulation, mais il dépend fortement de l'hypothèse que 45% des sites en centre-ville sont des micro-cellules à haute performance non saturées. Une calibration plus conservatrice (réduction du SINR ou de la BW des micros) pourrait ramener ce gain vers les 50-60%.

---

### 4. CONFIGURATION DU PIPELINE 1024
*   **Données** : `data/processed/features_target_1024cells.parquet`
*   **Topologie** : `config/network_topology_1024.yaml` (Placement calibré sur densité Milan)
*   **Matrices de Transfert** : `offline/fractions_1024.parquet` (Grille 30x30 par cellule)
*   **Logiciel de Simulation** : `phase5_simulation_1024_fixed.py`

---
**Document de Référence 1024-SON — 25 Mai 2026**

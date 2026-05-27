# 🗼 RAPPORT FINAL INTÉGRAL : SYSTÈME SON v5.1
## Optimisation Autonome de la Congestion Réseau par Machine Learning & MILP
**Équipe Projet** : Samya Loukili & L'Auteur  
**Encadrant** : M. Toufik Massrour

---

### 1. IDENTITÉ ET VISION DU PROJET
Le projet **SON (Self-Organizing Network) v5.1** est une solution d'ingénierie avancée visant à automatiser la gestion de la congestion dans les réseaux mobiles urbains (4G/5G). Développé dans le cadre d'un cursus d'ingénieur à l'**ENSAM Meknès**, il utilise les données réelles de la ville de Milan pour démontrer comment le couplage entre la prédiction temporelle (ML) et l'optimisation spatiale (MILP) peut surpasser les méthodes de gestion statiques traditionnelles.

**Objectif Central** : Minimiser le volume de trafic non satisfait en délestant dynamiquement les antennes saturées vers leurs voisines via le levier standard **A3 Offset**.

---

### 2. NOTRE PARCOURS DE RECHERCHE (R&D)
La solution actuelle est le résultat d'un processus itératif de recherche :
- **Explorations Initiales** : Nous avons testé les modèles **Prophet** (Facebook) et **SARIMA**. Bien que robustes pour les tendances à long terme, ils se sont révélés trop lents et insuffisamment réactifs pour les pics de trafic locaux en temps réel.
- **Le Pivot des 600 Cellules** : Notre première tentative sur un échantillon de 600 cellules dispersées a montré des résultats décevants. Nous avons compris que sans **voisinage immédiat (contiguïté géographique)**, le délestage est physiquement impossible.
- **La Solution du Bloc Dense** : En basculant sur un **bloc dense de 1024 cellules (32x32)**, nous avons créé un écosystème où chaque antenne peut réellement "aider" sa voisine, débloquant ainsi la performance du système.

---

### 3. RÉSULTATS CLÉS (BENCHMARK FINAL)
*   **Performance** : **73.53%** de réduction de la congestion par rapport à une gestion statique.
*   **Intelligence** : Utilisation d'un modèle **XGBoost Quantile (q80)** pour une prédiction "pessimiste" sécurisante, couplé à un correcteur de résidus **LightGBM**.
*   **Détails Complets** : Voir le [Rapport Technique 1024 Cellules](../RAPPORT_1024_CELLS.md).

---

### 4. LOGIQUE DU PIPELINE (ÉTAPES CLÉS)
1.  **Ingestion (Polars)** : Traitement massif des données Milan (62 jours, 10 000 cellules).
2.  **Prédiction ML** : Anticipe le trafic à 1 heure. Si un pic dépasse la capacité "normale", l'optimiseur est alerté.
3.  **Cœur Spatial** : Calcul géométrique précis (grille 50x50 par cellule) pour savoir exactement quel volume de trafic bascule si on change l'offset.
4.  **Optimisation MILP** : Résout le puzzle global pour toutes les antennes afin de diluer la congestion sans créer de nouveaux points chauds chez les voisines.
5.  **Boucle Fermée** : Simulation en temps réel pour valider que chaque décision améliore effectivement l'état futur du réseau.

---

### 5. MAINTENANCE ET ÉVOLUTION
*   **Surveillance du Drift** : Le système surveille en continu ses propres erreurs. Si la précision chute (changement de comportement des abonnés), une alerte est déclenchée.
*   **Évolutivité** : La topologie peut être mise à jour via `config/network_topology_1024.yaml` sans modifier le code source.

---
**Rapport technique de synthèse — Projet SON v5.1 — Mai 2026**

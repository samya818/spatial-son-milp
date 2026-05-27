# Hypothèses de Modélisation SON

Ce document détaille les hypothèses fondamentales utilisées dans le projet **projectTimeSeries** pour la simulation et l'optimisation du réseau.

## H1 : Consommation de Trafic Uniforme par Cellule
Nous supposons que le volume de données consommé dans une cellule (square_id) est réparti uniformément sur toute sa surface. Cette hypothèse permet de calculer des fractions de transfert géométriques précises.

## H2 : Distribution Spatiale des Utilisateurs
Bien que le nombre d'utilisateurs varie dans le temps (simulé via `user_simulator.py`), leur répartition spatiale à l'intérieur d'une cellule est considérée comme constante pour les calculs de délestage.

## H3 : Modèle de Path-Loss Standard (3GPP)
La puissance du signal reçu décroît selon un exposant de path-loss $n = 3.76$, typique des zones urbaines denses. C'est ce modèle qui dicte le basculement d'un utilisateur d'une antenne vers une autre lors d'un changement d'offset A3.

## H4 : Levier de Contrôle Unique (A3 Offset)
Conformément aux standards SON (3GPP), nous utilisons uniquement l'A3 Offset comme levier. Nous considérons que les autres paramètres (puissance d'émission, inclinaison de l'antenne) sont optimisés lors de la planification initiale et restent fixes.

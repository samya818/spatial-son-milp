# WiseNet — Comprendre le projet de A à Z

*Un système qui apprend à un réseau mobile à se réorganiser tout seul quand certaines zones sont surchargées.*

---

## Avant de commencer : le problème posé

Un réseau mobile (4G/5G) est découpé en petites zones géographiques, chacune couverte par une antenne. À certains moments, une antenne est saturée par la demande de ses utilisateurs (trop d'appels, trop de vidéos, trop de data) alors que l'antenne juste à côté, elle, a de la place disponible. Le réseau perd alors de la qualité de service dans la zone saturée, alors que de la capacité existe à quelques centaines de mètres — simplement mal répartie.

Le projet **WiseNet** (nom de dépôt technique : `spatial-son-milp`) construit un système qui corrige ce déséquilibre automatiquement, sans intervention humaine : il **prédit** où la saturation va se produire, **calcule** où le trafic en excès peut être redirigé, et **décide** quelles antennes doivent transférer une partie de leurs utilisateurs vers leurs voisines. C'est ce qu'on appelle dans le jargon télécom un **SON — Self-Organizing Network**, un réseau auto-organisant.

### Deux notions clés à comprendre : le Handover et l'Offset

Pour bien comprendre le fonctionnement de WiseNet, deux concepts fondamentaux de la téléphonie mobile sont utilisés partout dans ce projet :

- **Le Handover (transfert intercellulaire) :** C'est le mécanisme automatique et invisible par lequel un smartphone connecté bascule d'une antenne à une autre sans aucune coupure de communication. En temps normal, un mobile se connecte simplement à l'antenne qui émet le signal radio le plus fort.
- **L'Offset de Handover (ou CIO — Cell Individual Offset) :** C'est un paramètre logiciel (exprimé en décibels, dB) qui permet à l'opérateur de modifier artificiellement ce seuil de basculement. En appliquant un offset, on rend une antenne voisine « virtuellement plus séduisante » pour les smartphones situés en périphérie de couverture. Cela permet de **délester une antenne saturée en transférant une partie de ses utilisateurs vers sa voisine**, sans modifier physiquement les antennes.

Ce rapport est construit en deux parties :

- **Partie 1** explique le projet tel qu'il existe aujourd'hui, validé et mesuré (ci-après appelé **V1**).
- **Partie 2** explique les améliorations visées pour la suite, dans une version intermédiaire appelée **V1.5**, pensée spécifiquement pour le hackathon MENA Ignite 2026 (GSMA + Nokia) — et pourquoi ce choix de V1.5 remplace une version V2 plus ambitieuse qui avait été envisagée au départ.

---

# PARTIE 1 — Le projet actuel (V1) : comment il fonctionne

## 1.1 La logique générale, en une phrase

Le système observe le passé récent, **prédit** le trafic futur de chaque zone ie dans chaque cellule géographique en GB/30 minutes, **simule à l'avance** comment ce trafic pourrait se répartir entre entennes si on decide d'appliquer une combinaison d'offset donnée ( ces offsets influencent la decision d'accepter le handover ou pas )  , puis un **module de décision mathématique** choisit, parmi toutes les redirections possibles, la combinaison qui minimise la saturation globale du réseau — et applique cette décision.

Quatre grandes briques s'enchaînent :

```
DONNÉES RÉELLES DE TRAFIC
        │
        ▼
 1. PRÉDICTION (Machine Learning)
    "Combien de trafic  en GB/30 minutes chaque zone (cellule tel nous l'avons définit dans notre projet ) aura-t-elle dans les prochaines minutes , precisement dans la prochaine heure (cible de prediction) ?"
        │
        ▼
 2. MODÈLE SPATIAL (physique simplifiée du signal)
    "Si une cellule redirige son trafic  d'un antenne vers un autre  suite à l'appication d'un offset, quelle fraction d'utilisateurs y arrive vraiment ?"
        │
        ▼
 3. DÉCISION (optimisation mathématique — MILP)
    "Quelle est la meilleure combinaison des offsets possible ?"
        │
        ▼
 4. ACTION + BOUCLAGE
    On applique la décision, on mesure le résultat, et on recommence.
```

Les sections suivantes détaillent chaque brique, dans l'ordre où elles interviennent réellement dans le pipeline.

---

## 1.2 Brique 1 — Les données : sur quoi le système apprend

### Ce qu'est une « cellule » dans ce projet

Le mot **cellule** revient constamment dans ce rapport ; il désigne précisément une des zones géographiques de la grille de Milan utilisée comme jeu de données. Le projet s'appuie sur le **Telecom Italia Big Data Challenge**, un jeu de données réel et public qui découpe la ville de Milan en petits carrés de **235 mètres sur 235 mètres**. Chaque carré (identifié par un `square_id`) est une cellule, et possède son propre historique de trafic mobile mesuré dans le temps.

### De la donnée brute à l'unité utilisée par le projet

Dans le jeu de données original, le trafic est mesuré par tranche de **10 minutes**. Le projet **agrège** ces mesures en fenêtres de **30 minutes**, pour obtenir une unité de travail plus stable : le **GB/30min**. Il s'agit d'un débit agrégé — une sorte de volume moyennisé sur la demi-heure, plutôt qu'une mesure instantanée — qui sert de base à l'entraînement du modèle de prédiction (brique 2) .

### La topologie du réseau simulé

Le jeu de données Milan décrit le trafic, mais ne contient aucune antenne réelle. Une **topologie d'antennes** a donc été **construite et simulée** par le projet, en imitant des schémas de déploiement réalistes plutôt qu'en plaçant les antennes au hasard.

Dans cette topologie :

- Chaque cellule (chaque carré de la grille) est associée à une **antenne prioritaire** — l'antenne principale qui la dessert.
- Une même antenne peut, au départ, être l'antenne prioritaire de **plusieurs cellules** à la fois (une antenne dessert typiquement une petite zone regroupant plusieurs carrés voisins, pas un seul).
- Chaque antenne reçoit une **capacité** : la quantité maximale de trafic qu'elle peut absorber avant de saturer. Cette capacité est définie à l'origine en GB/s, puis agrégée elle aussi en GB/30min, pour rester dans la même unité que les volumes de trafic prédits et mesurés, on a immiter la réalité durant la simulation des antennes et les choix de leurs capacités
- Un **graphe de voisinage** relie chaque antenne à ses antennes voisines — c'est-à-dire celles vers qui elle pourrait, en théorie, rediriger une partie de son trafic.

**Pourquoi 235 mètres est une échelle raisonnable :** à cette taille, on peut supposer que le trafic est réparti de façon à peu près homogène à l'intérieur d'une même cellule — la variation *entre* deux cellules est beaucoup plus grande que la variation *à l'intérieur* d'une seule cellule. Cette hypothèse simplificatrice permet de traiter chaque cellule comme une seule unité de mesure, sans avoir besoin de savoir précisément où, à l'intérieur du carré, chaque utilisateur se trouve et combien  de tarfic il transférerait. (Cette hypothèse est directement liée à une question de fond sur l'hétérogénéité des utilisateurs, traitée en détail à la fin de cette Partie 1.)

Le projet utilise une grille de **1024 cellules** de ce type pour ses tests — soit une zone urbaine dense d'environ 32×32 carrés.

---

## 1.3 Brique 2 — La prédiction : deviner le trafic avant qu'il n'arrive

### Pourquoi prédire, et pas juste réagir ?

Un système qui réagit seulement *après* la saturation arrive toujours trop tard : le temps de détecter le problème et d'agir, les utilisateurs ont déjà subi une mauvaise qualité de service. L'idée du projet est donc d'anticiper : prédire le trafic à venir, décider les redirections *avant* que la saturation ne survienne, pour que les utilisateurs ne ressentent jamais le pic.

### Comment la prédiction fonctionne

Le projet utilise un modèle de machine learning appelé **XGBoost**, entraîné sur l'historique de chaque cellule (tendances horaires, jour de la semaine, saisonnalité, etc. — au total 31 variables construites à partir des données brutes). Ce modèle a été comparé à plusieurs alternatives (LSTM, Prophet, SARIMA, TiDE) et amélioré par un correcteur additionnel (LightGBM), avant d'être retenu comme la solution la plus fiable.

Un détail important : le modèle ne prédit pas *une moyenne* du trafic, mais un **quantile élevé (q80)**. Concrètement, cela veut dire qu'on ne demande pas au modèle *« quel trafic est le plus probable ? »*, mais plutôt *« quel est le niveau de trafic dans le pire des cas raisonnables que l'on ne dépassera un peu , que 20 % du temps ? »*. C'est un choix volontairement prudent : en réseau mobile, se tromper en sous-estimant le trafic (et donc laisser une antenne saturer) coûte bien plus cher, en qualité de service, que se tromper en le surestimant légèrement. Le système est donc conçu pour être **pessimiste par prudence**, plutôt que juste « en moyenne correct ».

**Ce que cette brique produit, concrètement :** pour chaque cellule et pour la fenêtre de 30 minutes suivante, une estimation chiffrée du volume de trafic attendu, en GB/30min.

---

## 1.4 Brique 3 — Le modèle spatial : qui peut réellement aider qui

Une fois qu'on sait *combien* de trafic une cellule saturée est susceptible de générer, il faut savoir *où* (quel antenne) ce trafic peut être redirigé, et **quelle fraction** de ce trafic arriverait réellement chez l'antenne voisin si on tentait la redirection avec l'application d'un offset donné. C'est le rôle de cette brique, qui se déroule en deux temps : d'abord un calcul physique du signal (ci-dessous), puis sa transformation en volumes de trafic exploitables par le solveur (section 1.4.3).

### 1.4.1 L'idée physique simplifiée

Le signal radio d'une antenne s'affaiblit avec la distance — c'est un phénomène qu'on appelle le **path-loss** (l'affaiblissement de parcours). Plus on s'éloigne de l'antenne, plus le signal reçu est faible. Dans la version actuelle (V1), chaque antenne est modélisée comme une source de signal **isotrope**, c'est-à-dire émettant uniformément dans toutes les directions, sans lobe directionnel. Le signal reçu à un point donné dépend donc uniquement de la distance à l'antenne, selon une formule logarithmique standard en télécom :

**Q_a(p) = −3,76 × log₁₀(d)** *(modèle UMi 3GPP)*

où `d` est la distance entre l'antenne `a` et le point `p`. Plus `d` augmente, plus `Q_a(p)` diminue (devient plus négatif) : le signal reçu est d'autant plus faible que le point est éloigné de l'antenne.

### 1.4.2 Le calcul, étape par étape : construire les matrices de fractions

Pour savoir quelle fraction du territoire d'une cellule bascule vers une voisine si on l'y encourage, le projet :

1. Découpe chaque cellule géographique en une grille fine de points (2500 points par cellule).
2. Pour chaque point, calcule la qualité de signal reçu (avec la formule ci-dessus) depuis l'antenne prioritaire de la cellule, et depuis chaque antenne voisine.
3. Simule un **décalage artificiel** en faveur de la voisine (appelé **offset de handover**, un paramètre standard des réseaux mobiles qui rend une antenne voisine « artificiellement plus attractive » pour forcer certains utilisateurs à s'y raccrocher). Pour plusieurs niveaux de décalage possibles, on regarde combien de points, sur les 2500, basculeraient vers la voisine.
4. La fraction de points qui basculent devient la **fraction de trafic transférable** vers cette voisine, pour ce niveau de décalage donné.

Ce calcul est fait **une fois, à l'avance** (on dit qu'il est fait *offline*), pour **chaque antenne**, pour **chacune de ses cellules prioritaires**, et pour **chacune de ses antennes voisines** — à chaque fois en faisant varier les niveaux d'offset et en comptant combien d'utilisateurs (de points) basculent. Le résultat de cette simulation offline est stocké dans des **matrices de fractions**, appelées **matrices de fractions délestées** : pour une antenne donnée, une cellule prioritaire donnée, une voisine donnée et un offset donné, la matrice indique quelle fraction du trafic de cette cellule serait délestée (envoyée) vers l'antenne voisin .

**La contrepartie — les matrices de fractions reçues :** la conservation de la masse (voir ci-dessous) impose qu'à chaque fraction délestée corresponde une fraction reçue strictement égale, du point de vue de l'antenne voisine. Le projet construit donc, en parallèle des matrices de fractions délestées, leur exacte contrepartie : des **matrices de fractions reçues**, qui indiquent, pour chaque antenne, quelle fraction de trafic elle recevrait de chacune de ses voisines. Ensemble, ces deux types de matrices (délestées et reçues) forment ce que le projet appelle les **fractions de transfert**.

**Une règle physique fondamentale, vérifiée systématiquement :** le trafic ne peut pas disparaître ni se dupliquer pendant une redirection. Si une fraction du trafic part vers une voisine, cette même fraction — pas plus, pas moins — doit être comptée comme reçue par la voisine. C'est ce qu'on appelle la **conservation de la masse**, et le projet la vérifie mathématiquement à une précision de moins d'un millionième, pour garantir que le modèle ne « triche » jamais avec les chiffres.

### 1.4.3 Des fractions aux volumes réels : les matrices H

Les matrices de fractions délestées et reçues répondent à une question purement géométrique : *« si on active tel offset, quelle proportion des utilisateurs bascule ? »*. Mais ce n'est pas une proportion que le solveur d'optimisation doit finalement manipuler — il a besoin d'un **volume réel de trafic**, en GB/30min.

Pour passer de l'un à l'autre, chaque fraction est **multipliée par le volume de trafic prédit** pour la cellule concernée (produit de la brique 2). Ce produit donne deux nouvelles matrices, appelées **matrice H délesté** et **matrice H reçu** :

- **H délesté** : pour chaque antenne, chaque voisin et chaque offset, le **volume réel** de trafic (en GB/30min) qui serait envoyé vers ce voisin si cet offset était choisi.
- **H reçu** : symétriquement, le **volume réel** de trafic que chaque antenne recevrait de chacune de ses voisines, pour chaque offset.

C'est précisément **ces deux matrices H** — et non les matrices de fractions brutes — qui sont transmises au solveur MILP (brique 4) : c'est sur leur base que le solveur choisit, pour chaque antenne, la combinaison d'offsets qui minimise la congestion du réseau pour la demi-heure à venir (de "now+1h " jusqu'à " now+1,5 h").

**Un point essentiel à retenir sur le rythme de calcul :** les matrices de fractions (délestées et reçues) sont calculées **une seule fois**, offline, et ne changent pas — elles ne dépendent que de la géométrie du réseau (positions des antennes, path-loss), qui est fixe. Les matrices **H**, en revanche, dépendent du trafic prédit, qui change à chaque cycle : elles sont donc **recalculées à chaque itération**, juste après que la brique 2 a produit une nouvelle prédiction.

**Ce que cette brique produit, concrètement :** deux matrices de volumes réels de trafic (H délesté, H reçu), une par antenne , prêtes à être données au solveur d'optimisation.

---

## 1.5 Brique 4 — Le cerveau décisionnel : Pyomo, le MILP et le solveur CBC

C'est la brique la plus centrale, et aussi celle qui demande le plus de précision, car plusieurs éléments distincts s'y superposent et sont souvent confondus.

### D'abord, une clarification essentielle : modéliser n'est pas résoudre

Il y a une différence fondamentale entre **décrire un problème mathématiquement** et **le résoudre**. C'est exactement la différence entre écrire l'énoncé d'un problème sur une feuille, et faire le calcul qui donne la réponse.

- **Pyomo** est un outil Python qui sert uniquement à **écrire** le problème d'optimisation sous une forme que l'ordinateur peut comprendre : quelles sont les décisions à prendre (les *variables*), quelles règles ces décisions doivent respecter (les *contraintes*), et quel est le but recherché (l'*objectif*). Pyomo ne calcule aucune réponse lui-même.
- **CBC** est le **solveur** — le moteur de calcul qui prend le problème écrit par Pyomo et cherche, parmi toutes les combinaisons de décisions possibles, celle qui atteint le meilleur résultat tout en respectant toutes les règles.

Confondre les deux — dire *« j'utilise Pyomo pour optimiser »* — est imprécis. La formulation correcte est : *« Pyomo formule le problème, et CBC le résout »*.

### Qu'est-ce qu'un « MILP », précisément

**MILP** signifie *Mixed Integer Linear Programming* — programmation linéaire en nombres mixtes. C'est une catégorie de problème mathématique dans laquelle :

- on cherche à **minimiser** ou **maximiser** une certaine quantité ;
- les décisions à prendre sont représentées par des **variables**, dont certaines sont **binaires** — c'est-à-dire qu'elles ne peuvent valoir que 0 ou 1 : *« ce niveau de décalage est activé »* (1) ou *« il ne l'est pas »* (0) ;
- toutes les relations entre ces variables (les règles à respecter) sont **linéaires** — de simples sommes et comparaisons, sans exposants ni produits compliqués entre variables.

Le mot « mixte » vient du fait que certaines variables sont binaires (des choix) et d'autres continues (des quantités, comme le volume de trafic).

### La formulation exacte du MILP dans ce projet

- **Décision :** pour chaque antenne `a`, un offset `δ_a ∈ {0, 1, 2, 3, 4, 5}` dB — six niveaux possibles, implémentés comme six variables binaires par antenne, avec la règle qu'un seul niveau peut être actif à la fois.
- **Objectif :** **maximiser le surplus de volume délesté des antennes surchargées** — c'est-à-dire pousser le solveur à choisir, pour chaque antenne en excès de charge, l'offset qui fait sortir le plus de surpulus de trafic possible vers ses antennes voisines disponibles. Maximiser ce volume délesté revient, mécaniquement, à minimiser ce qu'il reste de trafic bloqué en situation de saturation sur l'ensemble du réseau.
- **C1 — Capacité :** pour chaque antenne, la charge après délestage (trafic initial, moins ce qui est délesté, plus ce qui est reçu des voisines) doit rester inférieure ou égale à sa capacité (`capacity_mo`).
- **C2 — Conservation :** le volume délesté par une antenne vers une voisine doit être strictement égal au volume reçu par cette voisine — c'est la traduction, au niveau du MILP, de la conservation de la masse déjà appliquée lors de la construction des matrices H (section 1.4.3).
- **C3 — Couverture :** un offset `δ` ne peut être actif entre une antenne et une cellule cible que si cette cellule est effectivement en zone de couverture de cette antenne voisine — un offset ne peut pas rediriger du trafic vers une antenne qui, physiquement, ne reçoit aucun signal de cette zone.
- **C4 — Path-loss :** la relation `Q_a(p) = −3,76 × log₁₀(d)` (modèle UMi 3GPP), déjà présentée en 1.4.1, est le paramètre physique qui détermine, en amont, quelles fractions et quels volumes sont même envisageables — elle conditionne les données d'entrée (les matrices H) sur lesquelles s'appliquent les contraintes C1 à C3.

**Les données d'entrée du solveur** sont donc précisément les matrices H délesté et H reçu construites en 1.4.3, une paire par offset possible.

Sur la grille de test (1024 cellules, environ 200 antennes), ce problème représente environ **1400 variables binaires** et se résout en **2 secondes** avec CBC, un solveur gratuit et open-source.

**Ce que cette brique produit, concrètement :** pour chaque antenne, la décision optimale d'offset à appliquer, calculée en tenant compte de tout le réseau à la fois — c'est une optimisation **globale** : le solveur ne traite pas chaque antenne indépendamment, il cherche la meilleure combinaison de décisions sur l'ensemble du réseau simultanément, car rediriger le trafic d'une antenne A vers B peut avoir des répercussions sur les décisions optimales pour B et ses propres voisines.

---

## 1.6 Brique 5 — La boucle fermée : comment tout s'enchaîne dans le temps

Les briques précédentes ne sont pas exécutées une seule fois : elles forment un **cycle continu**, qu'on appelle une **boucle fermée** (*closed loop*). À intervalles réguliers (toutes les 30 minutes, au rythme des données) :

1. Le trafic récent est observé.
2. La prédiction (brique 2) estime le trafic à venir pour chaque cellule.
3. Les matrices de fractions déjà précalculées (brique 3, offline) sont multipliées par cette nouvelle prédiction pour produire les matrices H délesté et H reçu du cycle en cours.
4. Le MILP (brique 4) calcule, à partir de ces matrices H, la meilleure combinaison d'offsets pour tout le réseau.
5. La décision est appliquée (dans le monde réel, ce serait la configuration effective des antennes). Pour anticiper ce que sera le trafic **après** optimisation, le système part du trafic initialement prédit pour chaque cellule, puis **soustrait** les volumes correspondants dans la matrice H délesté et **ajoute** les volumes correspondants dans la matrice H reçu — ce qui donne, pour chaque antenne, la charge nette anticipée une fois les redirections effectives.
6. Le résultat réel est mesuré, comparé à la prédiction, ce qui permetterait aussi de détecter si le modèle de prédiction commence à « dériver » — c'est-à-dire à se tromper de plus en plus, un phénomène surveillé par un module dédié (détection de dérive statistique).
7. Le cycle recommence.

C'est cette boucle, testée et validée sur plusieurs cycles successifs, qui constitue la preuve que le système fonctionne dans la durée et pas seulement sur un instantané isolé.

---

## 1.7 Les résultats mesurés — ce que le projet prouve

Le projet a comparé les résultats de trois politiques de gestion du réseau, sur les mêmes données et dans les mêmes conditions sur une **période de test de 24 heures** (soit **48 créneaux temporels / *slots* de 30 minutes**) sur le **bloc dense de 1 024 cellules** ($32 \times 32$ mailles) :

| Politique | Volume de trafic resté insatisfait (Mo / MB) | Équivalent cumulé (Go / GB) | Gain par rapport à la référence |
|---|---|---|---|
| **Statique** (aucune redirection, réseau figé) | 160 237 Mo *(160 237,5 Mo)* | ~160,24 Go | référence (0 %) |
| **Heuristique gloutonne** (règle simple, sans optimisation globale) | 89 375 Mo | ~89,38 Go | 44,22 % |
| **MILP global** (WiseNet, ce projet) | **42 419 Mo** *(42 419,7 Mo)* | **~42,42 Go** | **73,53 %** *(+52,5 % vs glouton)* |

Ce tableau se lit ainsi : sur une journée complète (24 h), sans aucune intervention, environ 160 gigaoctets (160 237 Mo) de trafic cumulé restent en situation de saturation. Une règle simple, gloutonne mais sans vue d'ensemble (« redirige vers la voisine la moins chargée, une antenne à la fois »), réduit ce chiffre de moins de moitié (44,22 %). Le MILP global — qui résout et coordonne l'ensemble des antennes du bloc simultanément plutôt qu'une par une — réduit la saturation de près des trois quarts (**73,53 %**). Cet écart illustre concrètement la valeur ajoutée d'une **optimisation globale** (évitant les effets de cascade où une antenne délesterait vers une voisine déjà surchargée) par rapport à une décision **locale**, gloutonne et prise antenne par antenne.

---

## 1.8 Récapitulatif logique global — comment tout est connecté

```
Données historiques de trafic (Milan, cellules 235m, agrégées en GB/30min)
                │
                ▼
Topologie du réseau (antennes prioritaires, capacités, voisinage)
                │
        ┌───────┴────────┐
        ▼                 ▼
 PRÉDICTION ML      MODÈLE SPATIAL (offline, une seule fois)
 (XGBoost q80)      Q_a(p) = -3,76·log₁₀(d)
 "combien de        → matrices de fractions
  trafic à venir ?"    délestées + reçues
        │                 │
        └───────┬─────────┘
                ▼
     Prédiction × fractions = matrices H délesté / H reçu
     (recalculées à CHAQUE cycle, contrairement aux fractions)
                │
                ▼
     MOTEUR DE DÉCISION (Pyomo + CBC)
     Pyomo écrit le MILP (δ_a, C1-C4)
     CBC le résout en ~2 secondes
     → offset optimal, global, par antenne
                │
                ▼
     Application : trafic anticipé = prédiction − H délesté + H reçu
                │
                ▼
     Mesure du résultat réel, détection de dérive
                │
                ▼
     Retour au début (boucle fermée continue)
```

La caractéristique la plus importante à retenir de cette architecture est la **séparation entre ce qui est calculé à l'avance (offline)** — la topologie et les matrices de fractions, qui ne changent pas — **et ce qui est recalculé à chaque cycle (online)** — la prédiction, les matrices H, et la décision d'optimisation. Cette séparation est ce qui permet au système de prendre une décision globale, sur tout le réseau, en seulement deux secondes.

---

## 1.9 Une question légitime : et l'hétérogénéité des utilisateurs ?

Une objection naturelle peut être formulée à ce stade : *le système suppose implicitement que tous les utilisateurs d'une même cellule émettent un volume de trafic comparable, alors qu'en réalité, même au sein d'une même cellule, tout le monde ne consomme pas la même chose. Appliquer un offset peut donc avantager la majorité des utilisateurs d'une cellule, tout en désavantageant certains d'entre eux.*

Cette objection mérite une réponse précise, en plusieurs points.

**Premièrement, la taille d'une cellule limite structurellement cette hétérogénéité.** Une cellule de 235 mètres de côté correspond, en zone urbaine, à quelques maisons seulement. À cette échelle, il n'y a pas une hétérogénéité massive de comportement de consommation — la variation de trafic entre deux cellules éloignées est nettement plus grande que la variation entre deux points d'une même cellule.

**Deuxièmement, même s'il existe des cas particuliers** — des utilisateurs atypiques que le modèle de prédiction XGBoost échoue à anticiper correctement — ce n'est pas un scénario critique pour le système, et ce pour une raison structurelle propre à la logique de handover retenue.

Le mécanisme d'offset ne s'applique **que pour les utilisateurs situés dans une zone d'intersection**, c'est-à-dire une zone où plusieurs antennes couvrent simultanément. Un utilisateur n'est délesté vers une antenne voisine que **si cette voisine émet un signal de meilleure qualité que l'antenne actuelle** — quelle que soit la marge (l'offset) appliquée, cette marge ne fait que rendre le seuil de bascule plus ou moins exigeant, mais elle ne peut jamais faire basculer un utilisateur vers une antenne dont le signal est objectivement moins bon.

Le point central est le suivant : dans ce système, la **qualité de signal**, telle qu'elle est définie ici (section 1.4.1), est une **caractéristique purement physique**, liée uniquement à la distance entre le point et l'antenne — et, dans les versions futures du projet (section 2), également à l'angle par rapport au secteur et à la fréquence de la porteuse. **Elle n'est jamais liée à la congestion ou à la pression de trafic** de l'antenne.

C'est un choix de conception délibéré. Il aurait été intuitif d'intégrer l'effet de la congestion directement dans le calcul de la qualité de signal — mais cet effet est en réalité difficile à modéliser et à prédire de façon fiable. Le projet inverse donc la logique : au lieu de faire dépendre la qualité de signal de la congestion, c'est la **décision de handover** (via l'offset) qui intègre la congestion. Les deux critères — qualité de signal (physique, stable) et offset (piloté par la congestion, décidé par le MILP) — sont les deux seuls paramètres qui déterminent ensemble une bascule.

**La conséquence pratique de ce choix est directement rassurante face à l'objection initiale :** les utilisateurs très proches du centre d'une antenne, dont la qualité de signal est très largement supérieure à celle de toute voisine, ne basculeront jamais, quel que soit l'offset appliqué — la marge ne suffira jamais à combler un tel écart. Seuls les utilisateurs situés **à la frontière** entre deux zones de couverture, là où les qualités de signal sont naturellement proches, sont concernés par un basculement. Cela réduit fortement le risque associé à une éventuelle erreur de prédiction sur un cas individuel atypique, et cela simplifie considérablement le problème d'optimisation à résoudre.

**Enfin, un filet de sécurité est prévu pour les cas résiduels.** Pour les utilisateurs qui resteraient malgré tout dans une zone qui reste en congestion meme après optimisation et les cas exceptionnels que le système n'aurait pas pu anticiper  le projet prévoit, dans le cadre du hackathon, de s'appuyer sur l'API CAMARA **Quality on Demand (QoD)** pour leur permettre de demander explicitement un signal de meilleure qualité à la demande (détail complet en Partie 2, section 2.5).

---

# PARTIE 2 — Les améliorations visées : la version V1.5

## 2.1 Pourquoi pas une V2 complète ?

Un plan d'amélioration plus ambitieux, appelé V2, avait été envisagé. Il consistait à rendre le modèle physique du signal beaucoup plus réaliste : au lieu d'une antenne isotrope, chaque antenne aurait été découpée en **3 secteurs directionnels** imaginez les comme des paraboles, chacun émettant selon un diagramme de rayonnement concentré dans une direction précise plutôt que de façon uniforme, chaque secteur aurait porté **plusieurs fréquences radio** (porteuses) distinctes, et le calcul du signal aurait intégré un modèle d'**interférences dynamiques** — c'est-à-dire le bruit que les antennes voisines se causent mutuellement, recalculé à chaque cycle en fonction de la charge réelle prédite et au lieu de 'un offest pour la dessision de déléstage depuis un antenne" on aurait " un offset pour un paire de secteurs" . Ce plan impliquait aussi de passer à un solveur commercial plus puissant (Gurobi) pour gérer un problème d'environ **12 600 variables** au lieu de 1400, avec un temps de recalcul des matrices spatiales de 15 à 25 minutes à chaque cycle.

Après évaluation, ce plan V2 a été jugé **disproportionné pour le contexte actuel**, qui est un hackathon de deux semaines (MENA Ignite 2026, organisé par GSMA et Nokia) et non un travail de recherche de long terme. Trois raisons concrètes justifient ce choix :

1. **Le temps de démonstration est très court.** Un hackathon donne typiquement 5 à 10 minutes de présentation devant un jury. Un système qui doit « attendre 20 minutes que les matrices se recalculent » est inutilisable dans ce format, quelle que soit sa qualité scientifique.
2. **Le gain de précision physique n'est pas ce qui est jugé en priorité.** Les critères d'évaluation de ce hackathon valorisent avant tout l'**intégration réelle avec les API réseau du sandbox** (voir section 2.5) et la **pertinence pour la région MENA**, bien plus qu'un modèle radio théoriquement plus exact. Un modèle radio parfait mais déconnecté de toute API réelle démontrerait une maîtrise académique, mais pas un prototype fonctionnel.
3. **Le moteur V1 est déjà solide.** Avec 73,53 % de réduction de la congestion, validé sur 1024 cellules, en moins de 2 secondes de calcul, le moteur actuel se situe déjà à un bon niveau technique. Le risque de complexifier ce moteur pendant une fenêtre de temps courte, avec un solveur nécessitant une licence externe, est disproportionné par rapport au bénéfice attendu pour cette compétition précise.

C'est pour ces raisons qu'un compromis intermédiaire a été retenu : une version appelée **V1.5**, qui garde le moteur de décision V1 tel quel (fiable, rapide, déjà validé) mais raffine son modèle physique de signal, et y ajoute les éléments qui créent une vraie valeur pour ce hackathon précis. Le plan V2 complet n'est pas abandonné : il est repoussé en **perspective future**, hors du cadre du hackathon (voir section 2.7).

---

## 2.2 Le principe de la V1.5 : garder ce qui marche, raffiner ce qui compte

La V1.5 repose sur une idée simple : ne pas toucher au cœur du moteur de décision (Pyomo + CBC, la boucle fermée, la logique de conservation de masse), mais raffiner son modèle physique de signal et y ajouter des éléments qui, ensemble, transforment un moteur d'optimisation validé en un **prototype démontrable et connecté**. Ces éléments sont détaillés dans les sections suivantes.

**Un point à clarifier d'emblée :** la V1.5 ne se limite pas à décomposer les cellules en plusieurs porteuses de fréquence — c'est un raffinement plus profond : chaque **antenne** est décomposée en **secteurs directionnels**, et chaque **secteur** est lui-même décomposé en **porteuses**. C'est l'objet de la section 2.3.

---

## 2.3 Élément 1 — Le modèle secteurs + porteuses, et la logique de handover par RSRP

### 2.3.1 Pourquoi ce raffinement, en langage naturel

Dans le modèle V1 (section 1.4.1), une antenne est isotrope : elle émet également dans toutes les directions, et seule la distance détermine la qualité du signal reçu en un point. C'est une simplification efficace, mais elle ne reflète pas la réalité des déploiements de réseaux mobiles, où une antenne est presque toujours composée de **plusieurs secteurs directionnels** — typiquement trois, chacun couvrant environ un tiers de l'espace autour du pylône, un peu comme trois tranches de tarte orientées dans des directions différentes. Chaque secteur, en plus de cela, porte **plusieurs porteuses** (bandes de fréquence).

La conséquence directe de cette réalité est que **la distance seule ne suffit plus** à déterminer la qualité de signal reçue par un utilisateur : un point situé exactement dans l'axe d'un secteur reçoit un signal bien plus fort qu'un point situé à la même distance mais sur le côté, voire derrière ce secteur. Il faut donc, en plus de la distance, prendre en compte **l'angle** entre la direction pointée par le secteur et la direction vers laquelle se trouve l'utilisateur.

La V1.5 remplace donc la « qualité de signal » simplifiée du V1 par une grandeur standard des réseaux mobiles réels, le **RSRP** (*Reference Signal Received Power* — la puissance du signal de référence reçue), qui combine la distance, la fréquence de la porteuse, et cet effet d'angle. La logique de handover reste la même dans son principe qu'en V1 (une antenne voisine devient préférée si son signal, augmenté de l'offset, dépasse celui de l'antenne actuelle), mais elle s'exprime désormais avec ce RSRP plus réaliste plutôt qu'avec la qualité simplifiée du V1 :

**RSRP de l'antenne A + offset > RSRP de l'antenne B**

Ce calcul de RSRP se construit en quatre étapes successives, décrites ci-dessous en langage naturel, puis reprises sous forme d'équations à la fin de cette section.

**Étape 1 — la distance.** Comme en V1, on calcule d'abord la distance en ligne droite entre l'antenne (ou plus précisément le secteur) et le point considéré. Cette distance sert de base au calcul de l'affaiblissement de parcours (path-loss), exactement comme en V1, mais avec une formule de path-loss plus complète qui intègre en plus la fréquence de la porteuse (voir étape 4).

**Étape 2 — l'angle.** On détermine ensuite la direction dans laquelle pointe le secteur — son **azimut** — par exemple 0° si ce secteur est orienté plein Nord. On calcule aussi la direction géographique du point considéré vue depuis l'antenne, toujours par rapport au Nord. L'écart entre ces deux angles — la différence entre la direction pointée par le secteur et la direction réelle du point — donne l'**écart angulaire**, c'est-à-dire à quel point le point se trouve « de côté » par rapport à l'axe du secteur.

**Étape 3 — le gain directionnel.** Cet écart angulaire est ensuite converti en une perte de signal supplémentaire, spécifique aux antennes sectorielles : plus l'écart angulaire est grand, plus le signal reçu est atténué, selon une courbe standard en forme de cloche inversée. Cette atténuation est plafonnée à une valeur maximale, pour éviter de modéliser une perte infinie pour un point situé exactement derrière le secteur — en pratique, même dans la direction la plus défavorable, on ne prolonge pas la pénalité au-delà d'un certain seuil réaliste.

**Étape 4 — le RSRP final.** Le RSRP reçu en un point s'obtient en combinant trois éléments : la puissance d'émission de l'antenne, moins l'affaiblissement de parcours standard (qui dépend maintenant à la fois de la distance et de la fréquence de la porteuse), plus (ou moins, selon le signe) le gain directionnel calculé à l'étape précédente.

C'est ce RSRP, calculé secteur par secteur et porteuse par porteuse, qui remplace la qualité de signal simplifiée du V1 dans toute la logique de handover et dans la construction des matrices de fractions décrites en section 1.4 — le reste du pipeline (matrices H, MILP, boucle fermée) reste structurellement identique.

### 2.3.2 Les équations

Pour un secteur d'antenne A et un point P :

**Étape 1 — Distance**

```
d = distance(A, P)   → utilisée pour le path-loss
```

**Étape 2 — Angle**

```
θ_A = azimut du secteur (ex. secteur Nord = 0°)
θ_P = angle de la droite [A → P] par rapport au Nord géographique
Δθ = |θ_P − θ_A|   → écart angulaire
```

**Étape 3 — Gain directionnel**

```
G(Δθ) = −min[12 × (Δθ / 65)², 30]  dB
```

**Étape 4 — RSRP reçu**

```
RSRP = P_tx − PL(d, f) + G(Δθ)

avec  PL(d, f) = 32,4 + 36,7·log₁₀(d) + 20·log₁₀(f)
```

où `P_tx` est la puissance d'émission de l'antenne, `PL(d, f)` est l'affaiblissement de parcours standard 3GPP dépendant de la distance `d` et de la fréquence de la porteuse `f`, et `G(Δθ)` est le gain directionnel du secteur calculé à l'étape 3.
« Notre P_tx en V1.5 est exactement la puissance nominale déclarée par le fabricant que définit le 3GPP dans TS 36.104 et TS 38.104. Elle est fixe par secteur et par porteuse, configurée comme un paramètre de topologie — exactement comme un opérateur configure ses eNodeB. Nous ne l'inférons pas des données car les données Milan ne contiennent aucune mesure radio, et surtout car la convention télécom ne l'infère pas non plus : c'est une constante hardware. La seule différence avec la réalité est que nous ne modélisons pas la répartition fine de puissance par sous-porteuse (power allocation par RE), ce qui est une simplification standard des simulateurs académiques et n'affecte pas la validité du modèle de handover. »

### 2.3.3 La formulation du MILP en V1.5 : l'optimisation par couple `(Secteur, Porteuse)`

Une question fondamentale se pose lors du passage à la V1.5 : **le moteur d'optimisation MILP et sa fonction objectif doivent-ils être formulés par secteur ou par porteuse ?**

La réponse technique et physique est : **ni l'un ni l'autre isolément, mais au niveau du couple indissociable `(Secteur, Porteuse)`, c'est-à-dire par Cellule Radio Élémentaire $(s, f)$.**
(remarque cellule radio ici n'est pas la cellule géographique comme définit précedemment)

#### 1. Pourquoi le couple `(s, f)` est l'unité physique réelle de congestion ?
Dans un gNodeB 5G moderne :
* Un site physique comporte généralement **3 secteurs physiques** (chacun couvrant $120^\circ$).
* Chaque secteur émet sur **plusieurs porteuses fréquentielles** (par exemple $f_1 = 1,8\text{ GHz}$ pour la couverture générale et $f_2 = 3,5\text{ GHz}$ pour le très haut débit capacitif).
* **Une station de base = $3\text{ secteurs} \times 2\text{ porteuses} = 6\text{ cellules radio logiques distinctes}$.**

Chaque cellule $(s, f)$ possède ses propres ressources radio indépendantes (bande passante, blocs de ressources PRBs) et donc sa **propre capacité maximale finie $C_{s, f}$**. La saturation ne frappe pas une antenne entière en bloc, mais une cellule radio précise $(s, f)$ (par exemple, la bande 3,5 GHz du secteur Sud pendant un pic d'affluence).

#### 2. La double dimension d'optimisation débloquée : Délestage Horizontal vs Vertical

Raisonner au niveau du couple $(s, f)$ permet au solveur MILP de déclencher deux types de délestages intelligents et complémentaires :

1. **Le délestage Horizontal (Spatial / Inter-secteurs sur la même fréquence) :**  
   Si la cellule $(s_1, f_1)$ est saturée, le solveur augmente son offset pour basculer les utilisateurs situés en bordure spatiale vers le secteur voisin $(s_2, f_1)$.
2. **Le délestage Vertical (Inter-fréquences / Inter-porteuses au sein du même secteur) :**  
   Si la porteuse haute capacité $(s_1, f_2)$ est surchargée, le solveur peut déverser le surplus vers la porteuse basse fréquence $(s_1, f_1)$ **du même secteur**, sans même déplacer l'utilisateur vers une autre antenne géographique !

#### 3. La formulation mathématique rigoureuse du MILP V1.5

* **Variables de décision :** Pour chaque cellule $(s, f)$, le solveur choisit un niveau d'offset $k$ via une variable binaire $z_{s, f, k} \in \{0, 1\}$ (avec $\sum_k z_{s, f, k} = 1$).
* **Bilan de charge après délestage :**
  $$\text{Charge finale}(s, f) = V_{\text{prédit}}(s, f) - \text{Délesté}(s, f, k) + \sum_{(s', f') \in \text{Voisins}} \text{Reçu}(s' \to s, f' \to f, k)$$
* **Surplus insatisfait (variable d'écart) :**
  $$e_{s, f} \ge \text{Charge finale}(s, f) - C_{s, f} \quad \text{et} \quad e_{s, f} \ge 0$$
* **Fonction Objectif globale du MILP :**  
  Le solveur minimise la somme totale de la congestion résiduelle sur **l'ensemble des secteurs ET de toutes les porteuses** du réseau :

$$\min \sum_{s \in \text{Secteurs}} \sum_{f \in \text{Porteuses}} e_{s, f}$$

Cette structure garantit une modélisation 100 % fidèle à la gestion des ressources d'un réseau 4G/5G moderne (Carrier Aggregation et coordination inter-cellulaire).

---

## 2.4 Élément 2 — Des scénarios réalistes pour la région MENA

Le jeu de données de base (Milan) est excellent pour valider la méthode, mais il ne parle pas directement au jury d'un hackathon centré sur le Moyen-Orient et l'Afrique du Nord. L'idée est donc de créer des **scénarios de trafic pré-configurés**, qui reproduisent des situations concrètes et reconnaissables de la région :

- **« Hajj Mina »** — un pic de charge extrême et très localisé, représentant un afflux massif de pèlerins dans un espace réduit.
- **« Heure de pointe Casablanca »** — un gradient de charge typique d'une grande ville, avec des zones denses en centre-ville qui se vident progressivement vers la périphérie.
- **« Stade AFCON »** — un pic de charge localisé et brutal, suivi d'une décroissance rapide, représentant l'affluence autour d'un stade pendant et après un match.
- **« NEOM la nuit »** — une charge globalement faible, mais avec une forte densité d'objets connectés (capteurs IoT), représentant une ville intelligente en fonctionnement nocturne.

Ces scénarios ne changent rien au moteur de décision : ils changent seulement les **données d'entrée** (les volumes de trafic simulés par cellule), pour démontrer que le même moteur d'optimisation reste efficace face à des situations très différentes, et que ces situations sont familières et pertinentes pour un jury opérant dans cette région du monde.

---

## 2.5 Élément 3 — L'intégration CAMARA : le vrai différenciateur

C'est l'élément qui pèse le plus dans les critères de ce hackathon spécifique, car il démontre que le projet ne reste pas un exercice de simulation isolé, mais peut réellement dialoguer avec une infrastructure réseau standardisée.

### Qu'est-ce que CAMARA, en langage clair

**CAMARA** est un ensemble d'interfaces de programmation (API) standardisées, développées conjointement par les opérateurs télécom mondiaux sous l'égide de la GSMA (l'association mondiale des opérateurs mobiles), dans le cadre de l'initiative **Open Gateway**. L'objectif de CAMARA est de permettre à une application externe — comme WiseNet — de **lire des informations sur l'état du réseau** et de **demander des actions sur ce réseau**, à travers une interface commune, sans avoir besoin de connaître les détails techniques propriétaires de chaque opérateur.

Le hackathon MENA Ignite 2026 fournit un **environnement de test (sandbox)** de ces API, sur lequel les participants peuvent réellement s'inscrire, obtenir des identifiants, et effectuer de vrais appels — même si les données renvoyées restent des données de test, pas un vrai réseau de production.

### Les deux API pertinentes pour ce projet

- **Network Insights** — permet de **lire** l'état du réseau en temps réel : charge par cellule, débit, latence, nombre d'utilisateurs actifs. Dans le pipeline de WiseNet, cette API remplacerait, à terme, les données historiques Milan comme source d'entrée pour la prédiction.
- **Quality on Demand (QoD)** — permet de **demander une action** sur le réseau, en particulier une priorisation de flux. C'est le canal par lequel une décision calculée par le MILP pourrait, en théorie, être poussée vers le réseau réel — et c'est aussi, comme évoqué en section 1.9, le filet de sécurité prévu pour les utilisateurs qui resteraient en zone de congestion malgré l'optimisation : pour eux, le système peut demander explicitement, via QoD, un signal de meilleure qualité.

**Une nuance importante à connaître :** l'API CAMARA standard ne permet pas, aujourd'hui, de modifier directement le paramètre technique précis utilisé dans le moteur V1 (l'offset de handover, ou « A3 Offset »). Pour le hackathon, l'intégration se fait donc de façon honnête et transparente sur ce point : on utilise réellement l'API QoD pour la partie qu'elle couvre (la priorisation de flux), on utilise réellement l'API Network Insights pour la lecture, et on documente clairement que le paramétrage fin des antennes (l'A3 Offset) resterait, dans un déploiement réel chez un opérateur, à intégrer via une interface de configuration propriétaire complémentaire.

### Comment cela se connecte au pipeline existant


L'authentification auprès de ces API se fait par un mécanisme standard appelé **OAuth2 client credentials** : l'application s'identifie avec un identifiant et un secret (fournis lors de l'inscription au sandbox), reçoit en échange un jeton d'accès temporaire à durée de vie limitée, et utilise ce jeton pour chaque appel.

**Ce que cet élément démontre au jury :** que le moteur de décision, déjà prouvé sur des données historiques, peut être branché sur une source de données réelle et peut réellement déclencher une action réseau standardisée — la boucle complète *« état réseau → prédiction → décision → action »* devient tangible, même en mode sandbox.

---

## 2.6 Élément 4 — Un tableau de bord prêt pour la présentation

Le projet dispose déjà d'un tableau de bord interactif (Streamlit) permettant de simuler des scénarios réseau. Pour la V1.5, ce tableau de bord serait enrichi de plusieurs vues pensées spécifiquement pour la présentation devant un jury :

- Un onglet **« CAMARA en direct »**, montrant la boucle complète fonctionner en conditions réelles (même en sandbox).
- Un onglet **« Scénario MENA »**, permettant de basculer entre les scénarios réalistes décrits en 2.4.
- Un onglet **« Avant / Après MILP »**, affichant clairement les chiffres de gain (les 73,53 % déjà validés).
- Une visualisation de type **diagramme de flux (Sankey)**, montrant visuellement comment le trafic se déplace d'une cellule saturée vers ses voisines — une image qui rend immédiatement compréhensible, même sans explication technique, ce que fait le système.

---

## 2.7 Feuille de route dans le temps

| Période | Action prioritaire |
|---|---|
| Immédiat | Prise de contact avec le mentorat du hackathon (STC) |
| Court terme | Premier test réussi de l'API QoD du sandbox GSMA |
| Court terme | Intégration du client CAMARA dans le tableau de bord (mode simulation + mode réel) |
| Milieu de période | Création des scénarios MENA dans le tableau de bord |
| Milieu de période | Implémentation du modèle secteurs + porteuses (RSRP), si le temps le permet |
| Avant la fin | Session de mentorat, préparation des questions à poser |
| Fin de période | Finalisation du tableau de bord, documentation, préparation du pitch |

---

## 2.8 Ce qui reste pour plus tard : les perspectives V2 et au-delà

Le plan V2 complet — interférences dynamiques entre secteurs, modèle SINR complet conforme aux standards 3GPP (et non plus seulement RSRP), solveur Gurobi — n'est pas abandonné, seulement reporté. Il reste pertinent comme **prochaine étape après le hackathon**, dans un contexte où le temps de calcul plus long (15 à 25 minutes par cycle) et le besoin d'une licence de solveur commercial ne posent plus de contrainte de démonstration en temps réel. Des extensions encore plus poussées sont également envisagées à plus long terme : un modèle d'offset par relation individuelle entre chaque secteur et chaque voisin (au lieu d'un offset global par antenne), l'utilisation de réseaux de neurones sur graphes pour réduire la taille du problème d'optimisation, et une validation sur un simulateur réseau événementiel de référence (ns-3) avant tout déploiement réel chez un opérateur.

---

## 2.9 Agnosticisme technologique (4G/5G) et passage au déploiement réel

Le moteur **WiseNet est agnostique à la technologie radio**. En 4G (LTE) comme en 5G (NR), la gestion de la mobilité et le handover reposent sur les mêmes mécanismes fondamentaux standardisés par le 3GPP : le critère d'**événement A3** et la métrique de puissance reçue **RSRP**. 

L'évolution V1.5, avec sa modélisation fine par secteurs et porteuses fréquentielles, correspond exactement à l'architecture physique d'un **gNodeB 5G**. 

Dès lors, la seule différence fondamentale entre une simulation et un déploiement réel sur le terrain réside dans les interfaces de branchement :
- **En entrée :** remplacer le jeu de données historique (Milan) par un flux de télémétrie en temps réel issu d'une API standardisée telle que **CAMARA Network Insights** ;
- **En sortie :** pousser les décisions d'offsets optimaux calculées par le solveur vers les stations de base via l'**interface de gestion SON / O-RAN (Non-RT RIC)** de l'opérateur.

**L'algorithme de décision mathématique et le cœur du moteur d'optimisation (MILP), eux, restent rigoureusement identiques.**

---

## Conclusion — le message à retenir

Le projet WiseNet répond à un problème concret des réseaux mobiles — la saturation localisée alors que de la capacité existe juste à côté — par un système en boucle fermée qui **prédit** (machine learning), **simule** (modèle spatial, des matrices de fractions offline aux matrices de volumes H recalculées à chaque cycle) et **décide** (optimisation mathématique globale, via Pyomo et CBC) automatiquement. La version actuelle, validée sur des données réelles, réduit la congestion de 73,5 % par rapport à un réseau figé, et repose sur une logique de handover pensée pour rester fiable même face à l'hétérogénéité individuelle des utilisateurs. L'étape suivante, la V1.5, ne cherche pas à rendre le modèle physique plus précis pour le plaisir de la précision : elle raffine le calcul de qualité de signal vers un RSRP standard par secteurs et porteuses, et connecte ce moteur déjà prouvé à des scénarios réalistes de la région MENA et à une véritable interface réseau standardisée (CAMARA), pour transformer une preuve de concept scientifique en un prototype tangible, compréhensible en quelques minutes par un jury — la précision physique maximale (V2 complète, avec interférences dynamiques) restant un objectif légitime, mais pour une étape ultérieure du projet.

# Analyse et gestion de la consommation énergétique

Projet d’analyse et d’optimisation de la consommation énergétique sur 2 compteurs simulés sur 30 jours. Utilisation combinée de **SQL** et **Python** pour détecter anomalies, analyser séries temporelles et simuler des stratégies de gestion de la demande énergétique (DSM) dans un contexte industriel ou tertiaire.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Microsoft SQL Server](https://img.shields.io/badge/Microsoft%20SQL%20Server-Developer-red?logo=microsoft-sql-server)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 Objectifs
- Génération de données énergétiques réalistes  
- Analyse statistique et exploratoire des séries temporelles  
- Détection des anomalies et identification des heures critiques  
- Corrélation puissance–température et modélisation prédictive (régression linéaire et Random Forest)
- Optimisation énergétique via DSM (clipping, load shifting, load reduction)

---

## 💡 Valeur métier
- Réduction des pics de consommation → baisse des coûts énergétiques
- Détection proactive des anomalies → maintenance préventive
- Optimisation des charges → amélioration de l’efficacité énergétique

---

## ⚙️ Contexte
- Données simulées : 30 jours, résolution horaire  
- Profils :  
  - Compteur 1 : bâtiment tertiaire (HVAC, dynamique)  
  - Compteur 2 : process industriel (charge stable)  
- Ajout de bruit et pics ponctuels pour tester la détection d'anomalies  
- Variables : meter_id, timestamp, power_kw

---

## 🧰 Technologies
**Bibliothèques Python :** pandas, numpy, matplotlib, seaborn, scipy, statsmodels, scikit-learn

---

## 🔁 Pipeline et analyse des données
### Pipeline du projet

```mermaid
flowchart LR

A[<b>🗄️ Génération SQL<b>] --> B[<b>📊 Analyse SQL<b>]
B --> C[<b>🧹 Nettoyage Python<b>]
C --> D[<b>📈 Analyse exploratoire<b>]
D --> E[<b>⏱️ Séries temporelles<b>]
E --> F[<b>🚨 Anomalies<b>]
F --> G[<b>🌡️ Température<b>]
G --> H[<b>🤖 Machine Learning<b>]
H --> I[<b>⚡ DSM<b>]
I --> J[<b>📊 Résultats<b>]

%% Styles
classDef sql fill:#e3f2fd,stroke:#1e88e5,padding:20px,stroke-width:2px,color:#000;
classDef python fill:#e8f5e9,stroke:#43a047,padding:20px,stroke-width:2px,color:#000;
classDef ml fill:#fff3e0,stroke:#fb8c00,padding:20px,stroke-width:2px,color:#000;
classDef dsm fill:#fce4ec,stroke:#d81b60,padding:20px,stroke-width:2px,color:#000;

%% Affectation
class A,B sql;
class C,D,E,F,G python;
class H ml;
class I,J dsm;
```

### Analyse SQL
- Génération de données synthétiques et première passe de nettoyage : valeurs nulles, aberrantes, doublons
- Statistiques et variabilité de la puissance : moyenne, max, min, CV, FP
- Pics et heures creuses, détection des anomalies : Z_score, Z_robuste
- Analyse temporelle et comparaisons journalières pour identifier motifs et irrégularités
- Comparaison semaine vs week-end : statistiques, énergie cumulée, ratio semaine/week-end

### Analyse Python
- Prétraitement : nettoyage approfondi, structuration, gestion de valeurs manquantes/aberrantes/doublons
- Visualisations : courbes temporelles, histogrammes, heatmaps
- Séries temporelles : autocorrélation, Rolling mean, CV
- Détection d’outliers : Z-score, Z-robuste, IIE, Isolation Forest
- Analyse température : corrélation puissance/température, décalage temporel (lag)
- Modélisation : régression linéaire, Random Forest
- Optimisation DSM : clipping (P95), load shifting, load reduction

---

## 🏗️ Structure du projet

```text
energy-demand-analytics/
│
├── README.md
├── LICENSE
├── requirements.txt
├── main.py
│
├── data/
│   └── energy_readings_month.csv
│
├── sql/
│   ├── 01_generate_energy_data.sql
│   └── 02_energy_analysis.sql
│
├── python/
│   ├── P1_data_loading_cleaning.py
│   ├── P2_exploratory_analysis.py
│   ├── P3_time_series_analysis.py
│   ├── P4_anomaly_detection.py
│   ├── P5_temperature_correlation.py
│   ├── P6_machine_learning_models.py
│   ├── P7_demand_side_management.py
│   └── __init__.py
│
├── notebooks/
│   └── energy_analysis_pipeline.ipynb
│
├── results/
│   ├── 01_power_timeseries.png
│   ├── 02_heatmap_power.png
│   ├── 03_anomaly_detection.png
│   ├── 04_temperature_correlation.png
│   └── 05_demand_management.png
│
└── .gitignore
```

---

## ▶️ Comment exécuter

```bash

# Cloner le dépôt
git clone https://github.com/FatehChaabat/energy-demand-analytics.git
cd energy-demand-analytics

# Installer les dépendances
pip install -r requirements.txt

# Exécuter tout le pipeline avec main.py
python main.py      

# OU ouvrir le notebook interactif
jupyter notebook notebooks/energy_analysis_pipeline.ipynb

```

---

## 📈 Résultats clés
- Identification précise des heures critiques de consommation  
- Détection d’outliers par méthodes statistiques et Machine Learning  
- Analyse de la corrélation puissance–température et estimation du temps de réponse thermique
- Modélisation prédictive : régression linéaire et Random Forest 
- Quantification des économies et adaptation des stratégies DSM selon profils dynamiques ou stables

### Points clés
- Les profils tertiaires présentent une forte dépendance thermique
- Les anomalies sont détectables efficacement via méthodes hybrides
- Les stratégies DSM permettent de réduire les pics sans impacter la demande globale

---

## 📊 Principaux Insights Visuels
**Séries temporelles :** comparaison des profils horaires de puissance entre les deux compteurs  
![Power Timeseries](results/01_power_timeseries.png)  

**Heatmap :** visualisation de la puissance par heure et par jour pour les deux compteurs, mettant en évidence minima, maxima, cycles journaliers et pics via l’intensité des couleurs
![Heatmap](results/02_heatmap_power.png)  

**Détection d’anomalies :** identification des pics anormaux pour les deux compteurs via méthodes statistiques (Z-score, Z-robuste) et Machine Learning (Isolation Forest)
![Anomalies](results/03_anomaly_detection.png)  

**Corrélation température :** modélisation de la relation température–puissance pour le compteur 1 via régression linéaire et Random Forest (Lag 0 et Lag optimal)
![Temp Correlation](results/04_temperature_correlation.png)  

**Gestion DSM :** consommation énergétique des deux compteurs après application du clipping (P95), du load shifting et de la load reduction
![DSM](results/05_demand_management.png)   

---

## 🏭 Applications
- Monitoring énergétique industriel et tertiaire
- Gestion intelligente des bâtiments (HVAC)  
- Détection d’anomalies sur réseaux électriques  
- Optimisation de la consommation énergétique

---

## 🚀 Améliorations futures
- Intégration de données réelles  
- Développement de modèles de prévision avancés  
- Dashboards interactifs et suivi énergétique en temps réel  

---

## 👤 Auteur
Ingénieur en **mécanique des fluides et systèmes énergétiques**, avec un intérêt pour l’analyse de données, la modélisation et l’optimisation énergétique.

---

## 📄 Licence
Ce projet est sous **MIT License** – vous pouvez librement utiliser, modifier et partager le code et les fichiers, à condition de conserver la mention du copyright et de la licence.

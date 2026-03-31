# Analyse avancée de la Consommation Énergétique

Détection d'anomalies via une approche hybride (SQL & Python) et optimisation de la demande énergétique (DSM).

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Microsoft SQL Server](https://img.shields.io/badge/Microsoft%20SQL%20Server-Developer-red?logo=microsoft-sql-server)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Aperçu du projet

- **Détection d’anomalies :** Approche hybride combinant Z-Score et Isolation Forest

- **Modélisation :** Analyse de la corrélation puissance–température (signature thermique)

- **Optimisation :** Réduction des pics via stratégies DSM (Clipping P95, load shifting, load reduction)  

---

## 🎯 Objectifs & Valeur Métier
Le but est de transformer des données brutes de compteurs en leviers décisionnels :

- **Réduction des coûts :** Éviter les pénalités de dépassement de puissance souscrite.

- **Maintenance préventive :** Détecter les dérives de consommation (anomalies) avant la panne.

- **Caractérisation thermique :** Corrélation puissance–température pour isoler la part de consommation liée au climat (chauffage/clim).

- **Modélisation prédictive :** Développement de modèles pour anticiper la demande énergétique (Régression Linéaire, Random Forest).

- **Efficacité énergétique :** Simuler des stratégies DSM (Demand Side Management) pour lisser la courbe de charge.

---

## ⚙️ Stack & Données
 - **Données :** 30 jours (résolution horaire) | Compteur 1 (Tertiaire/HVAC) vs Compteur 2 (Industriel/Stable) | Variables (meter_id, timestamp, power_kw).

- **Architecture :**

  - **SQL Server :** Simulation de données, Nettoyage initial et Agrégations statistiques lourdes.

  - **Python :** Nettoyage approfondi, Analyse de séries temporelles, Machine Learning (Scikit-Learn) et Visualisation (Seaborn/Matplotlib).

- **Pipeline :** Architecture modulaire orchestrée via `main.py`

---

## 🔁 Pipeline

```mermaid
flowchart LR

A[<b>🗄️ SQL: Génération & Analyse<b>] --> B[<b>📊 Python: Prétraitement & Séries Temporelles<b>]
B --> C[<b>🚨 Détection Anomalies<b>]
C --> D[<b>🌡️ Corrélation Puissance/Température<b>]
D --> E[<b>🤖 ML: Modèles Prédictifs<b>]
E --> F[<b>⚡ DSM: Optimisation<b>]
F --> G[<b>📊 Résultats<b>] 

%% Styles
classDef sql fill:#e3f2fd,stroke:#1e88e5,padding:50px,stroke-width:2px,color:#000;
classDef python fill:#e8f5e9,stroke:#43a047,padding:50px,stroke-width:2px,color:#000;
classDef dsm fill:#fce4ec,stroke:#d81b60,padding:50px,stroke-width:2px,color:#000;

%% Affectation
class A sql;
class B,C,D,E,F python;
class G dsm;
```

---

## 📈 Résultats clés

- **Hybridation efficace :** La combinaison Z-Score + Isolation Forest permet une détection d'anomalies robuste sur les deux profils.

- **Signature Thermique :** Le profil tertiaire affiche une forte corrélation température/puissance, contrairement au profil industriel.

- **Performance du Random Forest :** Ce modèle surpasse la régression linéaire en capturant les non-linéarités et les dynamiques temporelles.

- **Efficacité du DSM :** Réduction significative des pointes de charge sans altération de la consommation énergétique totale.

---

## 📊 Visualisations

Les figures suivantes illustrent les principaux résultats du pipeline :

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

## 🏭 Applications
- Monitoring énergétique en temps réel
- Optimisation des systèmes HVAC  
- Détection précoce de dérives énergétiques
- Aide à la décision pour gestion DSM

---

## 🚀 Améliorations
- Intégration de données réelles  
- Développement de modèles de prévision avancés  
- Dashboards interactifs et suivi énergétique en temps réel  

---

## 👤 Auteur
Ingénieur en **mécanique des fluides et systèmes énergétiques**, avec un intérêt pour l’analyse de données, la modélisation et l’optimisation énergétique.

---

## 📄 Licence
Ce projet est sous **MIT License** – vous pouvez librement utiliser, modifier et partager le code et les fichiers, à condition de conserver la mention du copyright et de la licence.

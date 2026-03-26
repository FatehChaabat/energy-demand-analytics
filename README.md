# Analyse et gestion de la consommation énergétique

Analyse et optimisation de la consommation électrique sur 2 compteurs simulés sur 30 jours. Ce projet montre comment **SQL** et **Python** peuvent détecter des anomalies, analyser les séries temporelles et simuler des stratégies de gestion de la demande énergétique (DSM) dans un contexte industriel ou tertiaire.

---

## 🎯 Objectifs
- ⚡ Génération de données énergétiques réalistes  
- 📊 Analyse statistique et exploratoire des séries temporelles  
- 🚨 Détection des anomalies (statistiques + ML) et identification des heures critiques  
- 🌡️ Analyse de la température et modélisation puissance–température  
- 🔧 Optimisation énergétique via DSM (clipping, shifting, reduction)  

---

## ⚙️ Contexte
- Données énergétiques simulées : 30 jours, résolution horaire  
- Profils de consommation :  
  - 🏢 Compteur 1 : bâtiment tertiaire (HVAC, dynamique)  
  - 🏭 Compteur 2 : process industriel (charge stable)  
- Ajout de bruit et pics ponctuels pour tester la détection d’anomalies  
- Variables : meter_id, timestamp, power_kw

---

## 🧰 Technologies
**Langages :** SQL, Python   

**Bibliothèques Python :** pandas, numpy, matplotlib, seaborn, scipy, statsmodels, scikit-learn

---

## 🔁 Pipeline du projet

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
---

## 📊 Analyse des données

### 🗄️ SQL
- Génération de données synthétiques
- Calcul de moyennes, variabilité et facteur de pointe
- Comparaison semaine vs week-end 

### 🐍 Python
- Prétraitement : nettoyage, structuration, gestion des valeurs manquantes, aberrantes et doublons
- Visualisations : courbes temporelles, histogrammes, heatmaps
- Séries temporelles : autocorrélation, Rolling mean, coefficient de variation (CV)
- Détection d’anomalies : méthodes statistiques (Z-score, Z-robuste, IIE) et apprentissage automatique (Isolation Forest)
- Analyse température : simulation de la température extérieure, corrélation puissance/température, décalage temporel (lag)
- Modélisation : régression linéaire et Random Forest
- Optimisation DSM : clipping (P95), load shifting, load reduction

---

## 📈 Principaux Insights Visuels
**Séries temporelles :** comparaison des profils horaires de puissance pour les deux compteurs  
![Power Timeseries](results/power_timeseries.png)  

**Heatmap :** représentation des heatmaps de puissance par heure et par jour pour les deux compteurs, avec mise en évidence des minima et maxima, ainsi que l’identification des cycles journaliers et des pics via l’intensité des couleurs
![Heatmap](results/heatmap_power.png)  

**Détection d’anomalies :** détection des pics anormaux pour les deux compteurs à l’aide de méthodes statistiques (Z-score, Z-score robuste) et de Machine Learning (Isolation Forest)  
![Anomalies](results/anomaly_detection.png)  

**Corrélation température :** Modélisation de la corrélation température – puissance pour le compteur 1 à l’aide de la régression linéaire et de Random Forest (pour Lag 0 et Lag optimal)
![Temp Correlation](results/temperature_correlation.png)  

**Gestion DSM :** Consommation énergétique pour les deux compteurs après l'application du clipping (P95), du load shifting et de la load reduction
![DSM](results/demand_management.png)   

---

## 🏗️ Structure du projet

```text
energy-demand-analytics/
│
├── README.md
├── requirements.txt
│
├── data/
│   └── energy_readings_month.csv
│
├── sql/
│   ├── 01_generate_energy_data.sql
│   └── 02_energy_analysis.sql
│
├── python/
│   ├── 01_data_loading_cleaning.py
│   ├── 02_exploratory_analysis.py
│   ├── 03_time_series_analysis.py
│   ├── 04_anomaly_detection.py
│   ├── 05_temperature_correlation.py
│   ├── 06_machine_learning_models.py
│   └── 07_demand_side_management.py
│
├── notebooks/
│   └── energy_analysis_pipeline.ipynb
│
├── reports/
│   └── energy_analysis_pipeline.html
│
├── results/
│   ├── power_timeseries.png
│   ├── heatmap_power.png
│   ├── anomaly_detection.png
│   ├── temperature_correlation.png
│   └── demand_management.png
│
└── .gitignore
```

---

## ▶️ Comment exécuter

```bash
# Cloner le dépôt
git clone https://github.com/yourusername/energy-demand-analytics.git
cd energy-demand-analytics

# Installer les dépendances
pip install -r requirements.txt

# Exécuter les scripts Python (dans l’ordre)
python python/01_data_loading_cleaning.py
python python/02_exploratory_analysis.py
python python/03_time_series_analysis.py
python python/04_anomaly_detection.py
python python/05_temperature_correlation.py
python python/06_machine_learning_models.py
python python/07_demand_side_management.py

# Ou ouvrir le notebook pour l'analyse interactive
jupyter notebook notebooks/energy_analysis_pipeline.ipynb
```

---

## 📈 Résultats clés
- Identification précise des heures critiques de consommation  
- Détection d’anomalies par des méthodes statistiques (Z-score, Z-robuste, IIE) et Machine Learning (Isolation Forest)  
- Analyse de la corrélation puissance–température et estimation du temps de réponse thermique
- Modélisation prédictive par régression linéaire et Random Forest pour capturer les comportements linéaires et non linéaires 
- Quantification des économies et adaptation des stratégies DSM selon des profils dynamiques vs stables 

---

## 🏭 Applications
- Monitoring énergétique industriel  
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
Ingénieur spécialisé en **mécanique des fluides et systèmes énergétiques**, avec un intérêt pour l’analyse de données, la modélisation et l’optimisation énergétique.

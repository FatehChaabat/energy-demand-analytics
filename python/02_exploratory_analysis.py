
#todo Analyse exploratoire (02_exploratory_analysis.py)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.graphics.tsaplots import plot_acf
from scipy.stats import zscore, norm, skew, kurtosis, shapiro
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.ensemble import IsolationForest, RandomForestRegressor
import os
from IPython.display import display





#! Chargement, nettoyage et structuration 
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "../data/energy_readings_month.csv")
df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
df.columns = df.columns.str.strip()  
df["power_kw"] = (df["power_kw"].astype(str).str.replace(',', '.'))
df["power_kw"] = pd.to_numeric(df["power_kw"], errors="coerce") 
df["timestamp"] = pd.to_datetime(df["timestamp"]) 
                                                 
df = df.dropna(subset=["timestamp", "power_kw"]) 
df = df.drop_duplicates(subset=["meter_id","timestamp"], keep='first')  
df = df[df["power_kw"] >= 0]  
df = df.sort_values(["meter_id", "timestamp"], ascending=[True, True]) 
df = df.reset_index(drop=True)

df["heure"] = df["timestamp"].dt.hour
df["jour"] = df["timestamp"].dt.day
df["jour_semaine"] = df["timestamp"].dt.weekday
df["type_jour"] = np.where(df["jour_semaine"] < 5, "semaine", "weekend") 
df["num_semaine"] = df["timestamp"].dt.isocalendar().week
df["week_end"] = df["jour_semaine"].isin([5,6])
df["energie_kwh"] = df["power_kw"] * 1  
df["energy_cum_kwh"] = (df.groupby("meter_id")["energie_kwh"].cumsum())

# Séparer les données selon meter_id (si on veut le faire bien-sur)
df1 = df[df["meter_id"] == 1]
df2 = df[df["meter_id"] == 2]


#! Visualisation des puissances horaires pour les deux compteurs 
plt.figure(figsize=(12,6))
"""
Tracer la puissance brute par jour pour chaque compteur
"""
colors = ['blue','red'] 
for i, meter in enumerate(df['meter_id'].unique()):
    df_sub = df[df['meter_id'] == meter]
    
    plt.plot(
        df_sub["timestamp"],
        df_sub["power_kw"],
        linestyle='-',
        linewidth=1,
        color=colors[i],  
        marker='o',
        markersize=3,
        label=f"Meter {meter}"
    )

plt.xlabel("Time", fontsize=12)
plt.ylabel("Power (kW)", fontsize=12)
plt.title("Hourly Power by Day for Each Meter", fontsize=12)
plt.xticks(rotation=10)
plt.legend()
#plt.show()



#! Visualisation des distributions des deux compteurs
def plot_distribution_subplots_indep(df, meter_ids=[1,2]):
    """
    Fonction de visualisation combinée : histogramme, ajustement gaussien, moyenne et médiane sur un même graphique
    """
    fig, axes = plt.subplots(len(meter_ids), 1, figsize=(12, 5*len(meter_ids)), sharex=False)

    for i, meter_id in enumerate(meter_ids):
        ax = axes[i]
        data = df[df["meter_id"] == meter_id]["power_kw"]
        
        mean_val = data.mean()
        median_val = data.median()
        std_val = data.std()

        # Bins spécifiques à ce compteur
        bins = np.linspace(data.min(), data.max(), 40)

        # Histogramme normalisé
        ax.hist(data, bins=bins, density=True, alpha=0.6, label=f"Power - Meter {meter_id}")
        
        # Courbe gaussienne
        x = np.linspace(data.min(), data.max(), 1000)
        gaussian = norm.pdf(x, mean_val, std_val)
        ax.plot(x, gaussian, label="Gaussian fit", color="black")
        
        # Moyenne et médiane
        ax.axvline(mean_val, linestyle='--', color="red", label="Mean")
        ax.axvline(median_val, linestyle='-.', color="blue", label="Median")
       
        # Calculer et afficher les stats dans un tableau horizontal 
        df_results = pd.DataFrame([[skew(data), kurtosis(data), shapiro(data)[1]]], columns=["Skewness", "Kurtosis", "p-value"])
        print(f"\nLes stats pour le compteur {meter_id} :")
        print(df_results.to_string(index=False,formatters={"Skewness": "{:.2f}".format, "Kurtosis": "{:.2f}".format,"p-value": "{:.2e}".format}))
        
        ax.set_xlabel("Power (kW)")
        ax.set_ylabel("Density")
        ax.set_title(f"Power Distribution - Meter {meter_id}")
        ax.legend(prop={'weight': 'bold', 'size': 9})
        ax.grid(True)
    plt.tight_layout(h_pad=3)  # h_pad augmente l'espacement vertical
    #plt.show()

plot_distribution_subplots_indep(df, meter_ids=[1,2])




#! visualisation des Heatmaps de puissance par heure et par jour pour les deux compteur
def analyse_type_jour_subplots(df_list, type_jour_label_list):
    """
    Affiche en subplots les heatmaps pour plusieurs DataFrames/compteurs.
    
    df_list : liste de DataFrames (un par compteur)
    type_jour_label_list : liste de labels de type_jour à filtrer (ex: ['semaine','weekend'])
    """
    n_meters = len(df_list)
    fig, axes = plt.subplots(n_meters, 1, figsize=(12, 5*n_meters), sharex=True)
    
    # s'assurer que axes est toujours itérable
    if n_meters == 1:
        axes = [axes]

    for i, df in enumerate(df_list):
        ax = axes[i]
        
        # sélection selon type_jour : si liste
        if isinstance(type_jour_label_list, list):
            df_type = df[df["type_jour"].isin(type_jour_label_list)].copy()
            label_str = ", ".join([str(x).upper() for x in type_jour_label_list])
        else: # si pas une liste
            df_type = df[df["type_jour"] == type_jour_label_list].copy()
            label_str = str(type_jour_label_list).upper()
        
        if df_type.empty: #! si aucune ligne ne correspond à la sélection
            print(f"Aucune donnée pour {label_str}")
            continue

        # données Heatmap
        heat = df_type.pivot_table(index="jour", columns="heure", values="power_kw", aggfunc="mean")

        # Min et max par jour
        min_points = df_type.loc[df_type.groupby("jour")["power_kw"].idxmin()]
        max_points = df_type.loc[df_type.groupby("jour")["power_kw"].idxmax()]

        # créer un matrice booléenne de la même taille que données Heatmap
        min_matrix = pd.DataFrame(False, index=heat.index, columns=heat.columns)
        max_matrix = pd.DataFrame(False, index=heat.index, columns=heat.columns)

        for _, row in min_points.iterrows():
            j, h = row["jour"], row["heure"]
            if j in heat.index and h in heat.columns:
                min_matrix.loc[j, h] = True

        for _, row in max_points.iterrows():
            j, h = row["jour"], row["heure"]
            if j in heat.index and h in heat.columns:
                max_matrix.loc[j, h] = True

        # Heatmap
        sns.heatmap(heat, cmap='YlOrRd', linewidths=0.5, annot=False, ax=ax)
        # cacher X pour le premier subplot
        if i == 0: ax.xaxis.set_visible(False)
         
        ax.set_xlabel("Hour", fontsize=12)
        ax.set_ylabel("Day", fontsize=12)
        ax.set_xticks(np.arange(len(heat.columns))+0.5)
        ax.set_xticklabels(heat.columns, fontsize=8)
        ax.set_yticks(np.arange(len(heat.index))+0.5)
        ax.set_yticklabels(heat.index, fontsize=8)
        ax.invert_yaxis()
        ax.set_title(f"Power Heatmap by Hour and Day - Meter {df_type['meter_id'].iloc[0]}", fontsize=12)
        ax.tick_params(axis='y', rotation=0)

        # Min et max
        jours_min, heures_min = np.where(min_matrix)
        jours_max, heures_max = np.where(max_matrix)
        ax.scatter(heures_min+0.5, jours_min+0.5, color='black', marker='x', s=15, label='min')
        ax.scatter(heures_max+0.5, jours_max+0.5, color='blue', marker='o', s=15, label='max')
        ax.legend()

    plt.tight_layout(h_pad=2)
    plt.show()

analyse_type_jour_subplots([df1, df2], ['semaine','weekend'])
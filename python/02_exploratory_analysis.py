
#todo Analyse exploratoire (02_exploratory_analysis.py)
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.stats import norm, skew, kurtosis, shapiro


#! Chargement, nettoyage et structuration de DataFrame
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


#! chemin absolu pour enregistrer les graphiques 
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results_dir = os.path.join(base_dir, "results")
os.makedirs(results_dir, exist_ok=True)


#! Visualisation des profils de puissances horaires  
plt.figure(figsize=(12,6))
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

plt.xlabel("Time", fontsize=10)
plt.ylabel("Power (kW)", fontsize=10)
plt.title("Raw Power vs Time", fontsize=10)
plt.xticks(rotation=10, fontsize=8)
plt.yticks(fontsize=8)
plt.legend(fontsize=8)

plt.tight_layout()
plt.savefig(os.path.join(results_dir, "power_timeseries.png"), dpi=300, bbox_inches='tight', facecolor='white')
#plt.show()


#! Visualisation des distributions (histogramme, ajustement gaussien, moyenne et médiane sur un même graphique)
def plot_distribution_subplots_indep(df, meter_ids=[1,2]):
    fig, axes = plt.subplots(len(meter_ids), 1, figsize=(12, 5*len(meter_ids)), sharex=False)

    for i, meter_id in enumerate(meter_ids):
        ax = axes[i]
        data = df[df["meter_id"] == meter_id]["power_kw"]
        
        # Stats
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


# #! visualisation des Heatmaps de puissance par heure et par jour pour les deux compteur
def plot_heatmap_subplots(df, meter_ids=None, filtre_values=None, col_filtre="type_jour"):
    """
    Affiche en subplots les heatmaps pour les compteurs spécifiés et retourne les DataFrames filtrés.
    df : DataFrame global
    meter_ids : liste des meter_id à afficher (ex: [1,2]), si None => tous
    filtre_values : valeur(s) à filtrer (ex: ['semaine','weekend']), si None => tout
    col_filtre : colonne sur laquelle appliquer le filtre (ex: 'type_jour')
    """
    if meter_ids is None:
        meter_ids = df["meter_id"].unique()
    
    df_list = [df[df["meter_id"] == m].copy() for m in meter_ids]
    filtered_dfs = []

    n_meters = len(df_list)
    fig, axes = plt.subplots(n_meters, 1, figsize=(12, 5*n_meters), sharex=True)

    # s'assurer que axes est toujours itérable
    if n_meters == 1: axes = [axes]

    for i, df_meter in enumerate(df_list):
        ax = axes[i]

        # filtrage type_jour si demandé
        if filtre_values is not None:
            # sélection selon col_filtre : si liste
            if isinstance(filtre_values, list):
                df_type = df_meter[df_meter[col_filtre].isin(filtre_values)].copy()
                label_str = ", ".join([str(x).upper() for x in filtre_values])
            # si ce n'est pas une liste
            else:
                df_type = df_meter[df_meter[col_filtre] == filtre_values].copy()
                label_str = str(filtre_values).upper()
        # si filtre_values est none (vide)        
        else:
            df_type = df_meter.copy()
            label_str = "ALL"
        # si les éléments choisi se trouvent pas dans col_filtre
        if df_type.empty:
            print(f"Aucune donnée pour {label_str} - Meter {df_meter['meter_id'].iloc[0]}")
            continue

        filtered_dfs.append(df_type)

        # données Heatmap
        heat = df_type.pivot_table(index="jour", columns="heure", values="power_kw", aggfunc="mean")
        
        # min et max par jour de la puissance
        min_points = df_type.loc[df_type.groupby("jour")["power_kw"].idxmin()]
        max_points = df_type.loc[df_type.groupby("jour")["power_kw"].idxmax()]

        # créer un matrice booléenne de la même taille que heat (False partout au départ)
        min_matrix = pd.DataFrame(False, index=heat.index, columns=heat.columns)
        max_matrix = pd.DataFrame(False, index=heat.index, columns=heat.columns)
        
        # remplacer les false par des true là où les min et max sont identifiées
        for _, row in min_points.iterrows():
            if row["jour"] in heat.index and row["heure"] in heat.columns:
                min_matrix.loc[row["jour"], row["heure"]] = True

        for _, row in max_points.iterrows():
            if row["jour"] in heat.index and row["heure"] in heat.columns:
                max_matrix.loc[row["jour"], row["heure"]] = True

        # tracer heatmap
        sns.heatmap(heat, cmap='YlOrRd', linewidths=0.5, annot=False, ax=ax)
        ax.set_xlabel("Hour", fontsize=10)
        ax.set_ylabel("Day", fontsize=10)
        #ax.set_title(f"Power Heatmap - Meter {df_type['meter_id'].iloc[0]} ({label_str})")
        ax.set_title(f"Power Heatmap by Hour and Day - Meter {df_type['meter_id'].iloc[0]}", fontsize=10)
        ax.invert_yaxis()
        ax.tick_params(axis='y', rotation=0, labelsize=8)
        ax.tick_params(axis='x', labelsize=8)

        # cacher l'axe X pour le premier subplot
        if i == 0: ax.xaxis.set_visible(False)

        # récuperer toutes les positions où la valeur est True dans les matrices min_matrix et max_matrix
        jours_min, heures_min = np.where(min_matrix)
        jours_max, heures_max = np.where(max_matrix)
        
        # afficher les points min et max sur ta heatmap (au centre des cases concernées)
        ax.scatter(heures_min+0.5, jours_min+0.5, color='black', marker='x', s=15, label='min')
        ax.scatter(heures_max+0.5, jours_max+0.5, color='blue', marker='o', s=15, label='max')

        ax.legend(loc="upper right", fontsize=8)
        

    plt.tight_layout(h_pad=2)
    plt.savefig(os.path.join(results_dir, "heatmap_power.png"), dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()

    return filtered_dfs


plot_heatmap_subplots(df) # pour tout afficher même chose avec plot_heatmap_subplots(df, meter_ids=[1,2], filtre_values=["semaine","weekend"]) 

"""
Exemples pour filtrer :

df1_filtered_all = plot_heatmap_subplots(df, meter_ids=[1], filtre_values=["semaine","weekend"]) ou df1_filtered_all = plot_heatmap_subplots(df, meter_ids=[1])
df1_filtered_weekend = plot_heatmap_subplots(df, meter_ids=[1], filtre_values=["weekend"])
df1_filtered_week = plot_heatmap_subplots(df, meter_ids=[1], filtre_values=["semaine"]) ..... 

même chose pour : meter_ids=[2] ou changer carrément les colonnes concernées dans col_filtre; exemple col_filtre = "week_end" qui a des False et des True comme filtre_values

"""
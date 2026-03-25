
#todo Détection d'anomalies (04_anomaly_detection.py)

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




#! Analyse des anomalies avec des méthodes statistiques (Z-score)
df["z_score"] = df.groupby("meter_id")["power_kw"].transform(lambda x: zscore(x))
# Une valeur est considérée comme une anomalie si l’absolu du z-score > 2
df["state_z_score"] = np.where(df["z_score"].abs() > 2, "anomaly", "normal")

# Filtrer anomalies
df_anom = df[df["state_z_score"] == "anomaly"]

plt.figure(figsize=(12,6))

# Compteur 1 
plt.scatter(df_anom[df_anom["meter_id"] == 1]["timestamp"], df_anom[df_anom["meter_id"] == 1]["power_kw"], color="blue", marker="X", s=80, label="Meter 1")
# Compteur 2 
plt.scatter(df_anom[df_anom["meter_id"] == 2]["timestamp"], df_anom[df_anom["meter_id"] == 2]["power_kw"], color="red", marker="X", s=80, label="Meter 2")

plt.title("Anomaly Detection using Z-score")
plt.xlabel("Time")
plt.ylabel("Power (kW)")

# Afficher toutes les dates de df_anom sur l'axe x
dates = pd.date_range(df_anom["timestamp"].min().normalize(), df_anom["timestamp"].max().normalize(), freq='D')
plt.xticks(dates, rotation=10)

plt.legend()
plt.grid(alpha=0.3)
#plt.show()



#! Analyse des anomalies avec des méthodes statistiques (Z-robuste ou Z-score robuste)
df["median"] = df.groupby("meter_id")["power_kw"].transform("median")
df["mad"] = df.groupby("meter_id")["power_kw"].transform(lambda x: np.median(np.abs(x - np.median(x))))

# Normalisation avec 1.4826 pour rendre comparable au Z-score (si on suppose une distribution normale)
df["z_robust"] = (df["power_kw"] - df["median"]) / (1.4826 * df["mad"])

# Détection d'anomalies avec seuil = 2 (comme dans Z-score)
df["state_z_robust"] = np.where(df["z_robust"].abs() > 2, "anomaly", "normal")

# Filtrer anomalies
df_anom = df[df["state_z_robust"] == "anomaly"]

plt.figure(figsize=(12,6))
plt.scatter(df_anom[df_anom["meter_id"] == 1]["timestamp"], df_anom[df_anom["meter_id"] == 1]["power_kw"], color="blue", marker="X", s=80, label="Meter 1")
plt.scatter(df_anom[df_anom["meter_id"] == 2]["timestamp"], df_anom[df_anom["meter_id"] == 2]["power_kw"], color="red", marker="X", s=80, label="Meter 2")

plt.title("Anomaly Detection using Z-robuste")
plt.xlabel("Time")
plt.ylabel("Power (kW)") 

dates = pd.date_range(df_anom["timestamp"].min().normalize(), df_anom["timestamp"].max().normalize(), freq='D')
plt.xticks(dates, rotation=10)

plt.legend()
plt.grid(alpha=0.3)
#plt.show()




#! Analyse des anomalies avec des méthodes statistiques (IIE avec Rolling mean)
def plot_IIE_points_subplots(df_list, windows=[3,6,9,12], colors=["gray","orange","red","darkblue"]):
    """
    Trace les points IIE pour plusieurs compteurs en subplots.
    df_list : liste de tuples (DataFrame, meter_id)
    """
    n_meters = len(df_list)
    fig, axes = plt.subplots(n_meters, 1, figsize=(12, 5*n_meters), sharex=True)
    
    if n_meters == 1:
        axes = [axes]

    for i, (df, meter_id) in enumerate(df_list):
        ax = axes[i]
        df_meter = df[df["meter_id"] == meter_id].copy()
        
        for j, w in enumerate(windows):
            df_meter[f"mw_{w}h"] = df_meter["power_kw"].rolling(w).mean()
            df_meter[f"std_{w}h"] = df_meter["power_kw"].rolling(w).std()
            df_meter[f"cv_{w}h"] = df_meter[f"std_{w}h"] / df_meter[f"mw_{w}h"]
            
            # IIE
            median_cv = df_meter[f"cv_{w}h"].median()
            mad_cv = (df_meter[f"cv_{w}h"] - median_cv).abs().median()
            mad_cv = mad_cv if mad_cv != 0 else 1e-6
            df_meter[f"IIE_{w}h"] = (df_meter[f"cv_{w}h"] - median_cv) / (1.4826 * mad_cv)

            # Points instables
            df_moderate = df_meter[(df_meter[f"IIE_{w}h"] > 2) & (df_meter[f"IIE_{w}h"] <= 3)]
            df_strong = df_meter[df_meter[f"IIE_{w}h"] > 3]
            
            # Scatter plot
            ax.scatter(df_moderate["timestamp"], df_moderate[f"IIE_{w}h"],
                       color=colors[j], label=f"{w}h >2 (moderate)", marker="o", s=80)
            ax.scatter(df_strong["timestamp"], df_strong[f"IIE_{w}h"],
                       color=colors[j], label=f"{w}h >3 (strong)", marker="X", s=100)
        
        # Lignes de seuil
        ax.axhline(2, color="black", linestyle="--", label="IIE=2 (moderate)", linewidth=2)
        ax.axhline(3, color="black", linestyle="-.", label="IIE=3 (strong)", linewidth=2)

        if i == 0: ax.xaxis.set_visible(False)
        ax.set_xlabel("Time")
        ax.set_ylabel("IIE")
        ax.set_title(f"Energy Instability Index - Meter {meter_id}")
        ax.legend()
        ax.grid(alpha=0.3)
        ax.tick_params(axis='x', rotation=10)

    plt.tight_layout(h_pad=2)
    #plt.show()

    return [df[df["meter_id"] == meter_id].copy() for _, meter_id in df_list]

df1_meter, df2_meter = plot_IIE_points_subplots([(df, 1), (df, 2)])




#! Analyse des anomalies avec Machine Learning (Isolation Forest)
def tracer_Isol_Forest_subplots(df_list):
    """ 
    Détection d’anomalies non supervisée (Isolation Forest dans scikit-learn)
    """
    n_meters = len(df_list)
    fig, axes = plt.subplots(n_meters, 1, figsize=(12, 5*n_meters), sharex=True)

    if n_meters == 1:
        axes = [axes]

    for i, (df, meter_id) in enumerate(df_list):
        ax = axes[i]
        df_meter = df[df["meter_id"] == meter_id].copy()

        # prend uniquement les valeurs non nulles de la puissance 
        Y = df_meter[["power_kw"]].dropna()  

        # 100 arbres aléatoires, 1% de valeurs supposées aberrantes, on veut garder toujours le même résultat (random_state=42)
        model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)

        # trie les scores, il coupe au seuil correspondant à 1% et les pires 1% deviennent -1
        model.fit(Y)  

        # applique le model aux données. model.predict(Y) retourne : 1 (normal) ou -1 (anomalie)
        df_meter.loc[Y.index, "state"] = model.predict(Y)

        ax.plot(df_meter["timestamp"], df_meter["power_kw"], color="blue", linestyle='-', markersize = "6", label="Power")
        ax.scatter(
            df_meter[df_meter["state"] == -1]["timestamp"],
            df_meter[df_meter["state"] == -1]["power_kw"],
            color="red", s=40, label="Outliers"
        )
        
        if i == 0: ax.xaxis.set_visible(False)
        ax.legend(prop={'weight': 'bold', 'size': 9})
        ax.set_title(f"Anomalies detected with Isolation Forest - Meter {meter_id}")
        ax.set_xlabel("Time")
        ax.set_ylabel("Power kW")
        ax.tick_params(axis='x', rotation=10)

    plt.tight_layout(h_pad=2)
    plt.show()

    return [df[df["meter_id"] == meter_id].copy() for _, meter_id in df_list]

df1, df2 = tracer_Isol_Forest_subplots([(df, 1), (df, 2)])
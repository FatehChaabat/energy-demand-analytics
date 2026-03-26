
#todo Détection d'anomalies (04_anomaly_detection.py)
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.stats import zscore
from sklearn.ensemble import IsolationForest


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

#! chemin absolu pour enregistrer les graphiques 
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results_dir = os.path.join(base_dir, "results")
os.makedirs(results_dir, exist_ok=True)


#! Analyse anomalies par Z-score Z-robuste et Isolation Forest
def plot_anomaly_grid(df, meter_ids=[1,2]):

    fig, axes = plt.subplots(3, 2, figsize=(18, 10), sharex=True)
    for j, meter_id in enumerate(meter_ids):

        df_meter = df[df["meter_id"] == meter_id].copy()

        # Z-score (ligne 1)
        ax = axes[0, j]

        df_meter["z_score"] = zscore(df_meter["power_kw"])
        df_meter["state_z"] = np.where(df_meter["z_score"].abs() > 2, "anomaly", "normal")
        df_anom = df_meter[df_meter["state_z"] == "anomaly"]

        ax.scatter(df_anom["timestamp"], df_anom["power_kw"], color="red", marker="*", s=50, label="Outliers")

        ax.set_title(f"Anomalies Detection using Z-score - Meter {meter_id}", fontsize=10)
        ax.set_xlabel("Time", fontsize=10)
        ax.set_ylabel("Power (kW)", fontsize=10)
        if j == 0: ax.set_ylim(30, 460)
        else: ax.set_ylim(280, 340)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        ax.xaxis.set_visible(False)
        ax.tick_params(axis='y', labelsize=8)

        # Z-robuste (ligne 2)
        ax = axes[1, j]

        median = df_meter["power_kw"].median()
        mad = np.median(np.abs(df_meter["power_kw"] - median))

        df_meter["z_robust"] = (df_meter["power_kw"] - median) / (1.4826 * mad)
        df_meter["state_zr"] = np.where(df_meter["z_robust"].abs() > 2, "anomaly", "normal")
        df_anom = df_meter[df_meter["state_zr"] == "anomaly"]

        ax.scatter(df_anom["timestamp"], df_anom["power_kw"], color="red", marker="*", s=50, label="Outliers")

        ax.set_title(f"Anomalies Detection using Z-robuste - Meter {meter_id}", fontsize=10)
        ax.set_xlabel("Time", fontsize=10)
        ax.set_ylabel("Power (kW)", fontsize=10)
        if j == 0: ax.set_ylim(30, 460)
        else: ax.set_ylim(280, 340)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        ax.xaxis.set_visible(False)
        ax.tick_params(axis='y', labelsize=8)

        # Isolation Forest (ligne 3)
        ax = axes[2, j]

        Y = df_meter[["power_kw"]].dropna()

        model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
        model.fit(Y)

        df_meter.loc[Y.index, "state_if"] = model.predict(Y)

        ax.plot(df_meter["timestamp"], df_meter["power_kw"], color="blue", label="Power")

        ax.scatter(df_meter[df_meter["state_if"] == -1]["timestamp"], df_meter[df_meter["state_if"] == -1]["power_kw"], color="red", marker="*", s=50, label="Outliers")

        ax.set_title(f"Anomalies detected with Isolation Forest - Meter {meter_id}", fontsize=10)
        ax.set_xlabel("Time", fontsize=10)
        ax.set_ylabel("Power kW", fontsize=10)
        if j == 0: ax.set_ylim(30, 460)
        else: ax.set_ylim(280, 340)
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(alpha=0.3)
        ax.tick_params(axis='x', rotation=15, labelsize=8)
        ax.tick_params(axis='y', labelsize=8)

    plt.tight_layout(h_pad=2)
    plt.savefig(os.path.join(results_dir, "anomaly_detection.png"), dpi=300, bbox_inches='tight', facecolor='white')
    #plt.show()

plot_anomaly_grid(df, meter_ids=[1,2])


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
    plt.show()
    return [df[df["meter_id"] == meter_id].copy() for _, meter_id in df_list]

df1_meter, df2_meter = plot_IIE_points_subplots([(df, 1), (df, 2)])


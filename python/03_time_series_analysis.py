
#todo Analyse des séries temporelles (03_time_series_analysis.py)

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






#! Autocorrélation des séries temporelles
def plot_acf_meters_subplots(df_list, lags=719):
    """
    Trace l'autocorrélation de plusieurs compteurs en subplots.
    Ici calcul pour toute la période (720 heures, lags = 719)
    df_list : liste de tuples (DataFrame, nom_compteur)
    """
    n_meters = len(df_list)
    fig, axes = plt.subplots(n_meters, 1, figsize=(12, 5*n_meters), sharex=True)
    
    # s'assurer que axes est itérable
    if n_meters == 1:
        axes = [axes]

    for i, (df, meter_name) in enumerate(df_list):
        ax = axes[i]
        plot_acf(df["power_kw"].dropna(), lags=lags, zero=False, color='blue', marker='o', markersize=1,
                 vlines_kwargs={'color': 'blue'}, ax=ax)
        
        if i == 0: ax.xaxis.set_visible(False)
         
        ax.set_title(f"Autocorrelation of Power - {meter_name}", fontsize=12)
        ax.set_xlabel("Lag (hours)", fontsize=12)
        ax.set_ylabel("Autocorrelation", fontsize=12)

    plt.tight_layout(h_pad=2)
    #plt.show()

# Exemple tracé en subplots pour les deux compteurs pour 4 jours
plot_acf_meters_subplots([(df1, "Meter 1"), (df2, "Meter 2")], lags=96)




#! Puissance et rolling mean

def tracer_Rolling_subplots(df_list, fenetres=[3,6,12], colors=["orange","red","darkblue"]):
    """
    Trace la puissance brute et les moyennes glissantes pour plusieurs compteurs en subplots.
    df_list : liste de tuples (DataFrame, meter_id)
    """
    n_meters = len(df_list)
    fig, axes = plt.subplots(n_meters, 1, figsize=(12, 5*n_meters), sharex=True)
    
    if n_meters == 1:
        axes = [axes]

    for i, (df, meter_id) in enumerate(df_list):
        ax = axes[i]
        df_meter = df[df["meter_id"] == meter_id].copy()

        # Puissance brute
        ax.plot(df_meter["timestamp"], df_meter["power_kw"], linestyle='--', color='gray', alpha=0.5, label="Raw Power")
        
        # Tracer Rolling
        for j, w in enumerate(fenetres):
            df_meter[f"mw_{w}h"] = df_meter["power_kw"].rolling(w).mean()
            ax.plot(df_meter["timestamp"], df_meter[f"mw_{w}h"], label=f"Rolling {w}h", color=colors[j], linewidth=2)

        if i == 0: ax.xaxis.set_visible(False)
        ax.set_xlabel("Time", fontsize=12)
        ax.set_ylabel("Power (kW)", fontsize=12)
        ax.set_title(f"Power and Rolling Mean - Meter {meter_id}", fontsize=12)
        ax.legend()
        ax.tick_params(axis='x', rotation=10)
        
    plt.tight_layout(h_pad=2)
    #plt.show()

    # Retourner les DataFrames pour chaque compteur
    return [df[df["meter_id"] == meter_id].copy() for _, meter_id in df_list]

# Tracé en subplots pour les deux compteurs
df1_meter, df2_meter = tracer_Rolling_subplots([(df, 1), (df, 2)])




#! Coefficient de Variation (CV)
def tracer_CV_subplots(df_list, fenetres=[3,6,12], colors=["gray","orange","red"]):
    """
    Trace le coefficient de variation (CV) pour plusieurs compteurs en subplots.
    df_list : liste de tuples (DataFrame, meter_id)
    """
    n_meters = len(df_list)
    fig, axes = plt.subplots(n_meters, 1, figsize=(12, 5*n_meters), sharex=True)
    
    if n_meters == 1:
        axes = [axes]

    for i, (df, meter_id) in enumerate(df_list):
        ax = axes[i]
        df_meter = df[df["meter_id"] == meter_id].copy()
        
        for j, w in enumerate(fenetres):
            # Moyenne glissante
            df_meter[f"mw_{w}h"] = df_meter["power_kw"].rolling(w).mean()
            # Ecart-type glissant
            df_meter[f"std_{w}h"] = df_meter["power_kw"].rolling(w).std()
            # Coefficient de variation
            df_meter[f"cv_{w}h"] = df_meter[f"std_{w}h"] / df_meter[f"mw_{w}h"]
            
            # Tracer du CV
            ax.plot(df_meter["timestamp"], df_meter[f"cv_{w}h"],
                    label=f"CV {w}h", color=colors[j], linewidth=2)
        
        
        if i == 0: ax.xaxis.set_visible(False)
        ax.set_xlabel("Time")
        ax.set_ylabel("Coefficient of Variation")
        ax.set_title(f"Variability (CV) - Meter {meter_id}")
        ax.legend()
        ax.grid(alpha=0.3)
        ax.tick_params(axis='x', rotation=10)

    plt.tight_layout(h_pad=2)
    plt.show()

    return [df[df["meter_id"] == meter_id].copy() for _, meter_id in df_list]

df1_cv, df2_cv = tracer_CV_subplots([(df, 1), (df, 2)]) 

#todo Analyse de la corrélation avec la température (05_temperature_correlation.py)
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


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


#! Simulation de la température extérieure
def tracer_temperature_lag_complet(df, meter_ids=[1,2]):
    """
    Simulation de la température exterieure, calcul des lag 24 (de 0 a 23) et détermination du lag optimal
    """
    n_meters = len(meter_ids)
    fig, axes = plt.subplots(n_meters, 2, figsize=(12, 5*n_meters), sharex=False)  # 2 colonnes : profil + corrélation

    if n_meters == 1:
        axes = [axes]  
        
    for i, meter_id in enumerate(meter_ids):
        df_meter = df[df["meter_id"] == meter_id].copy()

        # Température simulée 
        n = len(df_meter)
        t = np.arange(n)
        temp_mean = 5
        temp_amp = 10
        phase = -2 * np.pi * 15 / 24
        temp = temp_mean + temp_amp * np.sin(2 * np.pi * t / 24 + phase)
        df_meter["outdoor_temp"] = temp
        df.loc[df_meter.index, "outdoor_temp"] = temp

        # Subplot 1 : profil de température
        ax_profile = axes[i][0]
        if i == 0: ax_profile.xaxis.set_visible(False)
        ax_profile.plot(df_meter["timestamp"], df_meter["outdoor_temp"], color='orange', label="Temperature")
        ax_profile.set_title(f"Temperature Profile - Meter {meter_id}")
        ax_profile.set_xlabel("Time")
        ax_profile.set_ylabel("Temperature (°C)")
        ax_profile.legend()
        ax_profile.grid(True)
        ax_profile.tick_params(axis='x', rotation=15)

        # Corrélation pour lag 0
        corr_lag0 = df_meter["power_kw"].corr(df_meter["outdoor_temp"])
        print(f"\nRésultats pour le compteur {meter_id} :\nLa correlation pour 'Lag 0' est : {corr_lag0:.3f}")
        
        # Corrélation puissance ↔ température 
        corr_lag = [df_meter["power_kw"].corr(df_meter["outdoor_temp"].shift(lag)) for lag in range(24)]
        best_lag = np.argmin(corr_lag)
        best_corr = corr_lag[best_lag]
        print(f"La correlation pour 'Optimal Lag de {best_lag}h' est : {best_corr:.3f}")

        # Subplot 2 : corrélation par lag
        ax_corr = axes[i][1]
        if i == 0: ax_corr.xaxis.set_visible(False)
        ax_corr.plot(range(24), corr_lag, marker='o', color='blue', label="Correlation")
        ax_corr.scatter(best_lag, best_corr, color='red', zorder=10, s=100, label="Optimal Lag")
        ax_corr.annotate(f"({best_lag},{best_corr:.3f})",xy=(best_lag, best_corr),xytext=(2, -20), textcoords='offset points', ha='center', color='red', fontweight='bold', rotation = 15)
        ax_corr.annotate(f"(0,{corr_lag0:.3f})", xy=(0, corr_lag0), xytext=(5, 2), textcoords='offset points', ha='center', color='black', fontweight='bold', rotation = 15)
        ax_corr.set_title(f"Power vs Temperature Correlation - Meter {meter_id}")
        ax_corr.set_xlabel("Lag (hours)")
        ax_corr.set_ylabel("Correlation")
        ax_corr.grid(True)
        ax_corr.legend(loc="upper left")

    plt.tight_layout(h_pad=2)
    #plt.show()
    return df

df = tracer_temperature_lag_complet(df, meter_ids=[1, 2])


#! Analyse de la corrélation puissance – température
def tracer_puissance_temperature_subplots(df_list):
    """
    fonction pour tracer la puissance vs la température pour lag = 0 puis pour lag optimal 
    """
    n_meters = len(df_list)
    fig, axes = plt.subplots(n_meters, 2, figsize=(12, 5*n_meters), sharex=True)

    if n_meters == 1:
        axes = [axes]

    for i, (df, meter_id) in enumerate(df_list):
        df_meter = df[df["meter_id"] == meter_id].copy()

        # Corrélation Pearson lag = 0 
        corr = df_meter["power_kw"].corr(df_meter["outdoor_temp"])
        
        # Scatter plot lag = 0 
        ax1 = axes[i][0]
        if i == 0: ax1.xaxis.set_visible(False)
        ax1.plot(df_meter["outdoor_temp"], df_meter["power_kw"], 'o', markersize=4, color='blue')
        ax1.set_xlabel("Outdoor Temperature (°C)")
        ax1.set_ylabel("Power (kW)")
        ax1.set_title(f"Power vs Temperature - Meter {meter_id} (Lag = 0, Corr = {corr:.3f})")
        ax1.grid(True)

        # Corrélation avec lag de 1 à 24h 
        corr_lag = [df_meter["power_kw"].corr(df_meter["outdoor_temp"].shift(lag)) for lag in range(24)]
        best_lag = np.argmin(corr_lag)
        best_corr = corr_lag[best_lag]
        
        # Décalage de la température selon le lag optimal 
        temp_shifted = df_meter["outdoor_temp"].shift(best_lag)
        df.loc[df_meter.index, "outdoor_temp_shifted"] = temp_shifted

        # Scatter plot optimal lag 
        ax2 = axes[i][1]
        if i == 0: ax2.xaxis.set_visible(False)
        ax2.plot(temp_shifted, df_meter["power_kw"], 'o', markersize=4, color='red')
        ax2.set_xlabel(f"Outdoor Temperature Shifted by Optimal Lag (°C)")
        ax2.set_ylabel("Power (kW)")
        ax2.set_title(f"Power vs Temperature - Meter {meter_id} (Optimal Lag = {best_lag}h, Corr = {best_corr:.3f})")
        ax2.grid(True)

    plt.tight_layout(h_pad=2)
    plt.show()

    return [df[df["meter_id"] == meter_id].copy() for _, meter_id in df_list]

df1, df2 = tracer_puissance_temperature_subplots([(df, 1), (df, 2)])
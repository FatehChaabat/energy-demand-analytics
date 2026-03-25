
#todo Régrission entre puissance et température (06_machine_learning_models.py)

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





#! Simulation de la température extérieure
def simulation_temperature_lag_optimal(df, meter_ids=[1,2]):
    """
    Simulation de la température extérieure et calcul du lag optimal pour chaque compteur.
    """
    for meter_id in meter_ids:
        df_meter = df[df["meter_id"] == meter_id].copy()

        # Simulation température
        n = len(df_meter)
        t = np.arange(n)
        temp_mean = 5
        temp_amp = 10
        phase = -2 * np.pi * 15 / 24
        temp = temp_mean + temp_amp * np.sin(2 * np.pi * t / 24 + phase)
        df_meter["outdoor_temp"] = temp
        df.loc[df_meter.index, "outdoor_temp"] = temp

        # Corrélation pour tous les lags 0-23
        corr_lag = [df_meter["power_kw"].corr(df_meter["outdoor_temp"].shift(lag)) for lag in range(24)]
        best_lag = np.argmin(corr_lag)
        best_corr = corr_lag[best_lag]
        print(f"Compteur {meter_id} : Optimal Lag = {best_lag}h, Corr = {best_corr:.3f}")

        # Décalage de la température selon le lag optimal 
        temp_shifted = df_meter["outdoor_temp"].shift(best_lag)
        df.loc[df_meter.index, "outdoor_temp_shifted"] = temp_shifted

    return df

df = simulation_temperature_lag_optimal(df, meter_ids=[1, 2])




#! Régrission linéaire
def plot_regression_meter_subplot(df, meter_id):
    """
    Régrission linéaire entre puissance et température (juste pour compteur 1)
    """
    df_meter = df[df['meter_id'] == meter_id].copy()

    fig, axes = plt.subplots(2, 1, figsize=(12,10), sharex=True)

    for i, use_shifted in enumerate([False, True]):
        ax = axes[i]

        # Choix de la colonne température
        temp_col = 'outdoor_temp_shifted' if use_shifted else 'outdoor_temp'

        # Supprimer les lignes avec NaN
        df_temp = df_meter.dropna(subset=[temp_col, 'power_kw'])

        x = df_temp[temp_col].values
        y = df_temp['power_kw'].values

        # Calcul des coefficients
        coef = np.round(np.polyfit(x, y, 1),1)
        y_pred = coef[0]*x + coef[1]

        # métriques
        mae = mean_absolute_error(y, y_pred)                 # Erreur absolue moyenne: MAE=​∑ ∣y​ − y_pred|/n; en moyenne le modèle se trompe de .. kW
        rmse = np.sqrt(mean_squared_error(y, y_pred))        # Erreur quadratique moyenne :pénalise beaucoup plus les grosses erreurs et utile pour détecter les outliers

        # Calcul du corr_lag0 et best_corr pour les mettre dans le titre
        corr_lag = [df_meter["power_kw"].corr(df_meter["outdoor_temp"].shift(lag)) for lag in range(24)]
        corr_lag0 = corr_lag[0]  
        best_lag = np.argmin(corr_lag)
        best_corr = corr_lag[best_lag]
        
        # affichage avec indication si température décalée
        title = f"Meter {meter_id} ({f'Optimal Lag = {best_lag}h, Corr = {best_corr:.3f}' if use_shifted else f'Lag = 0, Corr = {corr_lag0:.3f}'})"
        
        # Plot
        ax.scatter(x, y, alpha=0.6, label='Actual data', color='blue')
        if i == 0: ax.xaxis.set_visible(False)
        ax.plot(x, y_pred, color='red', linewidth=2, label="Regression : " rf"$y = {coef[0]} \cdot x + {coef[1]}$" + "\n" + rf"($\mathrm{{MAE}}={mae:.1f}\ &\ \mathrm{{RMSE}}={rmse:.1f}$)")
        ax.set_xlabel('Outdoor Temperature (°C)')
        ax.set_ylabel('Power (kW)')
        ax.set_title(f'Linear Regression Power vs Temperature - {title}')
        ax.legend()
        ax.grid(True)

    plt.tight_layout(h_pad=3)
    #plt.show()

    return

plot_regression_meter_subplot(df, 1)




#!Régression non linéaire avec Random Forest
def plot_Random_Forest_meter_subplot(df, meter_id):
    df_meter = df[df['meter_id'] == meter_id].copy()

    fig, axes = plt.subplots(2, 1, figsize=(12,10), sharex=True)

    for i, use_shifted in enumerate([False, True]):
        ax = axes[i]

        # Choix de la colonne température
        temp_col = 'outdoor_temp_shifted' if use_shifted else 'outdoor_temp'
        X = df_meter[[temp_col]].values  
        y = df_meter['power_kw'].values
        
        # Modèle Random Forest
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        # Prédiction
        y_pred = model.predict(X)

        # Métriques
        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))

        # Calcul du corr_lag0 et best_corr pour les mettre dans le titre
        corr_lag = [df_meter["power_kw"].corr(df_meter["outdoor_temp"].shift(lag)) for lag in range(24)]
        corr_lag0 = corr_lag[0]  
        best_lag = np.argmin(corr_lag)
        best_corr = corr_lag[best_lag]
        
        # affichage avec indication si température décalée
        title = f"Meter {meter_id} ({f'Optimal Lag = {best_lag}h, Corr = {best_corr:.3f}' if use_shifted else f'Lag = 0, Corr = {corr_lag0:.3f}'})"

        # Tri pour plot propre
        order = np.argsort(X.flatten())

        # Plot
        ax.scatter(X, y, color="blue", alpha=0.6, label="Actual data")
        if i == 0: ax.xaxis.set_visible(False)
        ax.plot(X.flatten()[order], y_pred[order], color="red", linewidth=2, label=f"Random Forest\n(MAE={mae:.1f} & RMSE={rmse:.1f})")
        ax.set_xlabel("Outdoor Temperature (°C)")  
        ax.set_ylabel("Power (kW)")                
        ax.set_title(f"Random Forest Power vs Temperature - {title}")  
        # ax.plot(X.flatten()[order], y_pred[order], label=f"Random Forest\nMAE={mae:.2f} | RMSE={rmse:.2f}")
        ax.legend()
        ax.grid(True)

    plt.tight_layout(h_pad=3)
    plt.show()

    return

plot_Random_Forest_meter_subplot(df, 1)

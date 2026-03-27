
#todo Optimisation DSM (07_demand_side_management.py)
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

#! chemin absolu pour enregistrer les graphiques 
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results_dir = os.path.join(base_dir, "results")
os.makedirs(results_dir, exist_ok=True)


#! Gestion de la demande énergétique (clipping, shift, reduction)
meters = df["meter_id"].unique()
fig, axes = plt.subplots(3, len(meters), figsize=(6*len(meters), 10), sharex=True)

if len(meters) == 1:
    axes = axes.reshape(3,1)  # s'assurer que axes est 2D

for col, meter in enumerate(meters):
    df_meter = df[df["meter_id"] == meter].copy()
    
    # CLIPPING
    p95 = np.percentile(df_meter["energie_kwh"], 95)                                                        # calculer la valeur de l'énergie en dessous de laquelle se trouvent 95 % des valeurs
    df_meter["energy_clipped"] = np.clip(df_meter["energie_kwh"], None, p95)                                # remplacer les valeurs au dessus de P95 par la P95
    axes[0, col].plot(df_meter["timestamp"], df_meter["energie_kwh"].values, color="black", label="original")
    axes[0, col].plot(df_meter["timestamp"],df_meter["energy_clipped"].values, color="blue", linestyle='--', label="clipping")
    axes[0, col].set_ylabel("Energy (kWh)", fontsize=10)
    axes[0, col].set_title(f"Original vs Clipping - Meter {meter}", fontsize=10)
    axes[0, col].xaxis.set_visible(False)
    axes[0, col].legend(loc="upper right", fontsize=8)
    axes[0, col].tick_params(axis='y', labelsize=8)

    # SHIFT
    df_meter["energy_shifted"] = df_meter["energie_kwh"].copy()
    mask_peak = df_meter["heure"].between(18,20)                                                            # Définir la plage horaire, mask_peak → heures 18h à 20h (pointe)
    mask_offpeak = df_meter["heure"].between(2,4)                                                           # mask_offpeak → heures 2h à 4h (creux)
    shift = df_meter.loc[mask_peak, "energie_kwh"] * 0.2                                                    # Calculer l'énergie à déplacer (20 %)
    df_meter.loc[mask_peak, "energy_shifted"] -= shift                                                      # diminuer la consommation de -20 % (pointe)
    energy_to_move = shift.sum()                                                                            # somme de l'énergie retirée sur toutes les lignes peak du mois
    n_offpeak = mask_offpeak.sum()                                                                          # nombre total de points mask_offpeak du mois
    df_meter.loc[mask_offpeak, "energy_shifted"] += energy_to_move / n_offpeak                              # ajouter la consommation moyenne (énergie totale reste conservée)
    axes[1, col].plot(df_meter["timestamp"], df_meter["energie_kwh"].values, color="black", label="original")
    axes[1, col].plot(df_meter["timestamp"], df_meter["energy_shifted"].values, color="#ff7f0e", linestyle='--', label="shift")
    axes[1, col].set_ylabel("Energy (kWh)", fontsize=10)
    axes[1, col].set_title(f"Original vs Shift - Meter {meter}", fontsize=10)
    axes[1, col].xaxis.set_visible(False)
    axes[1, col].legend(loc="upper right", fontsize=8)
    axes[1, col].tick_params(axis='y', labelsize=8)
    
    # REDUCTION
    df_meter["energy_reduced"] = df_meter["energie_kwh"].copy()
    mask_critical = df_meter["heure"].between(17,20)                                                       # définir la plage houraire de réduction
    df_meter.loc[mask_critical, "energy_reduced"] *= 0.9                                                   # réduire de 10% l'énergie dans la plage houraire mask_critical
    axes[2, col].plot(df_meter["timestamp"], df_meter["energie_kwh"].values, color="black", label="original")
    axes[2, col].plot(df_meter["timestamp"], df_meter["energy_reduced"].values, color="#2ca02c", linestyle='--', label="reduction")
    axes[2, col].set_ylabel("Energy (kWh)", fontsize=10)
    axes[2, col].set_title(f"Original vs Reduction - Meter {meter}", fontsize=10)
    axes[2, col].set_xlabel("Time", fontsize=10)
    axes[2, col].legend(loc="upper right", fontsize=8)
    axes[2, col].tick_params(axis='x', labelsize=8, rotation=15)
    axes[2, col].tick_params(axis='y', labelsize=8)
    
    # Copier les nouvelles colonnes dans le DataFrame principal
    for c in ["energy_clipped", "energy_shifted", "energy_reduced"]: df.loc[df["meter_id"] == meter, c] = df_meter[c].values

plt.tight_layout(h_pad=3)
plt.savefig(os.path.join(results_dir, "05_demand_management.png"), dpi=300, bbox_inches='tight', facecolor='white')
plt.show()


#! Énergie totale, facteur de pointe et économie théorique (Clipping / Shift / Reduction)
# calcul Energie totale, facteur de pointe et l'économie théorique pour chaque cas clip/shift/reduce
for meter in df["meter_id"].unique():
    df_meter = df[df["meter_id"] == meter]
    
    # Énergie totale et test sur la concervation d'energie (totale vs shift), ainsi que reduction (clip and reduce)
    total_original = df_meter["energie_kwh"].sum()
    total_clipped  = df_meter["energy_clipped"].sum()
    total_shifted  = df_meter["energy_shifted"].sum()
    total_reduced  = df_meter["energy_reduced"].sum()
    
    # Facteur de pointe : puissance maximale / puissance moyenne
    peak_factor_original = df_meter["energie_kwh"].max() / df_meter["energie_kwh"].mean()
    peak_factor_clipped  = df_meter["energy_clipped"].max() / df_meter["energy_clipped"].mean()
    peak_factor_shifted  = df_meter["energy_shifted"].max() / df_meter["energy_shifted"].mean()
    peak_factor_reduced  = df_meter["energy_reduced"].max() / df_meter["energy_reduced"].mean()
    
    # Économie théorique: énergie originale – énergie après clip/shift/reduce
    saving_clip_kwh   = total_original - total_clipped
    saving_clip_pct   = saving_clip_kwh / total_original * 100
    saving_shift_kwh  = total_original - total_shifted
    saving_shift_pct  = saving_shift_kwh / total_original * 100
    saving_reduce_kwh = total_original - total_reduced
    saving_reduce_pct = saving_reduce_kwh / total_original * 100

    # Afficher les résultats dans un tableau
    df_results = pd.DataFrame({
        "Stratégie": ["Original", "Clipping", "Shift", "Reduction"],
        "Énergie totale (kWh)": [total_original, total_clipped, total_shifted, total_reduced],
        "Facteur de pointe": [peak_factor_original, peak_factor_clipped, peak_factor_shifted, peak_factor_reduced],
        "Économie (kWh)": [0, saving_clip_kwh, saving_shift_kwh, saving_reduce_kwh],
        "Économie (%)": [0, saving_clip_pct, saving_shift_pct, saving_reduce_pct]
     })

    print(f"\nRésultats pour compteur {meter} :")
    print(df_results.round(2).to_string(index=False))

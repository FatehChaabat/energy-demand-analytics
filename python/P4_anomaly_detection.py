
#todo Détection d'anomalies (P4_anomaly_detection.py)
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import zscore
from sklearn.ensemble import IsolationForest

def run(df, results_dir):
    #! Analyse anomalies par Z-score Z-robuste et Isolation Forest
    def plot_anomaly_grid(df, meter_ids=[1,2]):
        all_anomalies = []  #* liste pour le tableau final

        fig, axes = plt.subplots(3, 2, figsize=(18, 10), sharex=True)
        for j, meter_id in enumerate(meter_ids):
            df_meter = df[df["meter_id"] == meter_id].copy()

            # Z-score (ligne 1)           
            df_meter["z_score"] = zscore(df_meter["power_kw"])
            df_meter["state_z"] = np.where(df_meter["z_score"].abs() > 2, "anomaly", "normal")
            df_anom_z = df_meter[df_meter["state_z"] == "anomaly"]           
            # pour remplir le tableau all_anomalies pour Z_score
            df_anom_z["method"] = "Z-score"
            df_anom_z = df_anom_z[["meter_id", "timestamp", "power_kw", "method"]]
            all_anomalies.append(df_anom_z)            
            # tracer les anomalies Z_score
            ax = axes[0, j]
            ax.scatter(df_anom_z["timestamp"], df_anom_z["power_kw"], color="red", marker="*", s=50, label="Outliers")
            ax.set_title(f"Anomalies Detection Using Z-score - Meter {meter_id}", fontsize=10)
            ax.set_xlabel("Time", fontsize=10)
            ax.set_ylabel("Power (kW)", fontsize=10)
            if j == 0: ax.set_ylim(30, 460)
            else: ax.set_ylim(280, 340)
            ax.legend(fontsize=8)
            ax.grid(alpha=0.3)
            ax.xaxis.set_visible(False)
            ax.tick_params(axis='y', labelsize=8)

            # Z-robuste (ligne 2)           
            median = df_meter["power_kw"].median()
            mad = np.median(np.abs(df_meter["power_kw"] - median))
            df_meter["z_robust"] = (df_meter["power_kw"] - median) / (1.4826 * mad)
            df_meter["state_zr"] = np.where(df_meter["z_robust"].abs() > 2, "anomaly", "normal")
            df_anom_zr = df_meter[df_meter["state_zr"] == "anomaly"]
            # pour remplir le tableau all_anomalies pour Z-robuste
            df_anom_zr["method"] = "Z-robuste"
            df_anom_zr = df_anom_zr[["meter_id", "timestamp", "power_kw", "method"]]
            all_anomalies.append(df_anom_zr)            
            # tracer les anomalies Z_robuste
            ax = axes[1, j]
            ax.scatter(df_anom_zr["timestamp"], df_anom_zr["power_kw"], color="red", marker="*", s=50, label="Outliers")
            ax.set_title(f"Anomalies Detection Using Z-robuste - Meter {meter_id}", fontsize=10)
            ax.set_xlabel("Time", fontsize=10)
            ax.set_ylabel("Power (kW)", fontsize=10)
            if j == 0: ax.set_ylim(30, 460)
            else: ax.set_ylim(280, 340)
            ax.legend(fontsize=8)
            ax.grid(alpha=0.3)
            ax.xaxis.set_visible(False)
            ax.tick_params(axis='y', labelsize=8)

            # Isolation Forest (ligne 3)                       
            Y = df_meter[["power_kw"]].dropna()
            model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
            model.fit(Y)
            df_meter.loc[Y.index, "state_if"] = model.predict(Y)
            df_anom_if = df_meter[df_meter["state_if"] == -1]
            # pour remplir le tableau all_anomalies pour Isolation Forest
            df_anom_if["method"] = "IsolationForest"
            df_anom_if = df_anom_if[["meter_id", "timestamp", "power_kw", "method"]]
            all_anomalies.append(df_anom_if)
            # tracer les anomalies avec Isolation Forest
            ax = axes[2, j] 
            ax.plot(df_meter["timestamp"], df_meter["power_kw"], color="blue", label="Power")
            ax.scatter(df_anom_if["timestamp"], df_anom_if["power_kw"], color="red", marker="*", s=50, label="Outliers")
            ax.set_title(f"Anomalies Detection Using Isolation Forest - Meter {meter_id}", fontsize=10)
            ax.set_xlabel("Time", fontsize=10)
            ax.set_ylabel("Power kW", fontsize=10)
            if j == 0: ax.set_ylim(30, 460)
            else: ax.set_ylim(280, 340)
            ax.legend(loc="upper right", fontsize=8)
            ax.grid(alpha=0.3)
            ax.tick_params(axis='x', rotation=15, labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
         
        plt.tight_layout(h_pad=2)
        plt.savefig(os.path.join(results_dir, "07_anomaly_detection.png"), dpi=300, bbox_inches='tight', facecolor='white')
        #plt.show()

        # --- Tableau récapitulatif ---
        df_anomalies = pd.concat(all_anomalies).sort_values(["meter_id", "method", "timestamp"])
        print("\n=== Tableau des anomalies par meter_id et méthode ===")
        for meter_id, df_meter_group in df_anomalies.groupby("meter_id"):
            print(f"\n--- Meter {meter_id} ---")
            for method, df_method_group in df_meter_group.groupby("method"):
                print(f"\nMéthode : {method}")
                print(df_method_group[["timestamp", "power_kw"]].reset_index(drop=True))

    plot_anomaly_grid(df, meter_ids=[1,2])


    #! Analyse des anomalies avec des méthodes statistiques (IIE avec Rolling mean)
    def plot_EII_points_subplots(df_list, windows=[3,6,9,12], colors=["gray","orange","red","darkblue"]):
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
                
                # EII
                median_cv = df_meter[f"cv_{w}h"].median()
                mad_cv = (df_meter[f"cv_{w}h"] - median_cv).abs().median()
                mad_cv = mad_cv if mad_cv != 0 else 1e-6
                df_meter[f"EII_{w}h"] = (df_meter[f"cv_{w}h"] - median_cv) / (1.4826 * mad_cv)

                # Points instables
                df_moderate = df_meter[(df_meter[f"EII_{w}h"] > 2) & (df_meter[f"EII_{w}h"] <= 3)]
                df_strong = df_meter[df_meter[f"EII_{w}h"] > 3]
                
                # Scatter plot
                ax.scatter(df_moderate["timestamp"], df_moderate[f"EII_{w}h"],
                        color=colors[j], label=f"{w}h >2 (moderate)", marker="o", s=80)
                ax.scatter(df_strong["timestamp"], df_strong[f"EII_{w}h"],
                        color=colors[j], label=f"{w}h >3 (strong)", marker="X", s=100)
            
            # Lignes de seuil
            ax.axhline(2, color="black", linestyle="--", label="EII=2 (moderate)", linewidth=2)
            ax.axhline(3, color="black", linestyle="-.", label="EII=3 (strong)", linewidth=2)

            if i == 0: ax.xaxis.set_visible(False)
            ax.set_xlabel("Time")
            ax.set_ylabel("EII")
            ax.set_title(f"Energy Instability Index - Meter {meter_id}")
            ax.legend()
            ax.grid(alpha=0.3)
            ax.tick_params(axis='x', rotation=10)

        plt.tight_layout(h_pad=2)
        plt.savefig(os.path.join(results_dir, "08_energy_instability_index.png"), dpi=300, bbox_inches='tight', facecolor='white')
        # plt.show()
        return [df[df["meter_id"] == meter_id].copy() for _, meter_id in df_list]

    df1_meter, df2_meter = plot_EII_points_subplots([(df, 1), (df, 2)])


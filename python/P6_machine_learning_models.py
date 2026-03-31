
#todo Régrission entre puissance et température (P6_machine_learning_models.py)
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.ensemble import RandomForestRegressor

def run(df, results_dir):
    #! regression linéaire vs random forest (lag optimal)
    def plot_regression_and_RF_subplots(df, meter_id):
        df_meter = df[df['meter_id'] == meter_id].copy()

        fig, axes = plt.subplots(2, 2, figsize=(18,10), sharey=True)

        # Calcul du lag optimal et les correlation 
        corr_lag = [df_meter["power_kw"].corr(df_meter["outdoor_temp"].shift(lag)) for lag in range(24)]
        corr_lag0 = corr_lag[0]  
        best_lag = np.argmin(corr_lag)
        best_corr = corr_lag[best_lag]
        
        for i, use_shifted in enumerate([False, True]):

            temp_col = 'outdoor_temp' if not use_shifted else 'outdoor_temp_shifted'

            df_temp = df_meter.dropna(subset=[temp_col, 'power_kw'])
            x = df_temp[temp_col].values
            y = df_temp['power_kw'].values

            # Régression Linéaire
            coef = np.round(np.polyfit(x, y, 1),1)
            y_pred = coef[0]*x + coef[1]
            mae = mean_absolute_error(y, y_pred)
            rmse = np.sqrt(mean_squared_error(y, y_pred))

            title = f"Meter {meter_id} ({f'Lag 0, Corr = {corr_lag0:.2f}' if not use_shifted else f'Optimal Lag = {best_lag}h, Corr = {best_corr:.2f}'})"

            ax_lr = axes[0, i]
            ax_lr.scatter(x, y, alpha=0.6, color='blue', label='Actual data')
            ax_lr.plot(x, y_pred, color='red', linewidth=2, label="Regression : "rf"$\mathrm{{P}} = {coef[0]} \cdot \mathrm{{T}} + {coef[1]}$" + "\n" + rf"($\mathrm{{MAE}}={mae:.1f}\ &\ \mathrm{{RMSE}}={rmse:.1f}$)")
            ax_lr.set_xlabel('Outdoor Temperature (°C)', fontsize=10)
            ax_lr.set_ylabel('Power (kW)', fontsize=10)
            ax_lr.set_title(f'Linear Regression - {title}', fontsize=10)
            ax_lr.legend(fontsize=8)
            ax_lr.grid(False)
            if i == 0: ax_lr.xaxis.set_visible(False)
            if i == 1: ax_lr.xaxis.set_visible(False)
            if i == 1: ax_lr.yaxis.set_visible(False)
            ax_lr.tick_params(axis='y', labelsize=8)

            # Random Forest
            X_rf = x.reshape(-1,1)
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_rf, y)
            y_pred_rf = model.predict(X_rf)
            mae_rf = mean_absolute_error(y, y_pred_rf)
            rmse_rf = np.sqrt(mean_squared_error(y, y_pred_rf))
            order = np.argsort(X_rf.flatten())

            ax_rf = axes[1, i]
            ax_rf.scatter(X_rf, y, color='blue', alpha=0.6, label='Actual data')
            ax_rf.plot(X_rf.flatten()[order], y_pred_rf[order], color='red', linewidth=2, label=f"Random Forest\n(MAE={mae_rf:.1f} & RMSE={rmse_rf:.1f})")
            if i==0 : ax_rf.set_xlabel('Outdoor Temperature (°C)', fontsize=10)
            if i==1 : ax_rf.set_xlabel('Outdoor Temperature Shifted by Optimal Lag (°C)', fontsize=10)
            ax_rf.set_ylabel('Power (kW)', fontsize=10)
            ax_rf.set_title(f'Random Forest - {title}', fontsize=10)
            ax_rf.legend(fontsize=8)
            ax_rf.grid(False)
            if i == 1: ax_rf.yaxis.set_visible(False)
            ax_rf.tick_params(axis='x', labelsize=8)
            ax_rf.tick_params(axis='y', labelsize=8)

        plt.tight_layout(h_pad=3, w_pad=2)
        plt.savefig(os.path.join(results_dir, "11_linear_regression_vs_random_forest.png"), dpi=300, bbox_inches='tight', facecolor='white')
        # plt.show()

    # Appel pour le compteur 1
    plot_regression_and_RF_subplots(df, 1)

    # Appel pour le compteur 2
    #plot_regression_and_RF_subplots(df, 2)
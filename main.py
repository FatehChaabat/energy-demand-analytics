# main.py
import os
from python import (
    P1_data_loading_cleaning,
    P2_exploratory_analysis,
    P3_time_series_analysis,
    P4_anomaly_detection,
    P5_temperature_correlation,
    P6_machine_learning_models,
    P7_demand_side_management
)

def main():
    """ Exécute toutes les étapes du pipeline dans l'ordre """

    print("\n============================== Début du pipeline ==============================")

    # Définir results_dir une fois pour tout le pipeline 
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True) 

    print("\n=============== Chargement et nettoyage des données ===============")
    df = P1_data_loading_cleaning.run() 
 
    print("\n=============== Analyse exploratoire ===============")
    P2_exploratory_analysis.run(df, results_dir)

    print("\n=============== Analyse des séries temporelles ===============")  
    P3_time_series_analysis.run(df, results_dir)

    print("\n=============== Détection d'anomalies ===============")  
    P4_anomaly_detection.run(df, results_dir)
    
    print("\n=============== Corrélation température-puissance ===============")
    P5_temperature_correlation.run(df, results_dir)
    
    print("\n=============== Modélisation et machine learning ===============")
    P6_machine_learning_models.run(df, results_dir)
    
    print("\n=============== Optimisation de la consommation (DSM) ===============")
    P7_demand_side_management.run(df, results_dir)
    
    print("\n============================== Fin du pipeline ==============================")

if __name__ == "__main__":
    main()

#todo Chargement et nettoyage des données (P1_data_loading_cleaning.py)
import os
import numpy as np
import pandas as pd

def run():

    #! Chargement et conversion
    # Récupère le dossier courant du script
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Chemin vers le CSV dans le dossier data
    csv_path = os.path.join(base_dir, "../data/energy_readings_month.csv")


    # Lecture du CSV
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8")

    # Enlever les espaces éventuels
    df.columns = df.columns.str.strip()  

    # Convertir power_kw en numérique (les virgules en VS Code sont des points)
    df["power_kw"] = (df["power_kw"].astype(str).str.replace(',', '.'))
    df["power_kw"] = pd.to_numeric(df["power_kw"], errors="coerce") 

    # Convertir timestamp, pd.to_datetime() convertit cette colonne en objet datetime que Python peut comprendre comme une date/heure
    df["timestamp"] = pd.to_datetime(df["timestamp"]) 


    #!  Nettoyage et structuration des données
    print("Contrôle de qualité des données :")

    # Vérifier des valeurs manquantes (NaN)
    print("Nombre total de valeurs manquantes dans le DataFrame :", df.isna().sum().sum())

    # Supprimer les valeurs NaN dans les colonnes timestamp ou power_kw si elles existent (si valeure nulle toute la ligne sera supprimée)                                                   
    df = df.dropna(subset=["timestamp", "power_kw"]) 

    # Remplir les NaN par la dernière valeur connue
    # df = df.fillna(method='ffill')

    # Vérifier les doublons par colonnes spécifiques (meter_id + timestamp)
    doublons = df[df.duplicated(subset=["meter_id","timestamp"], keep=False)] 
    print(f"Nombre total de doublons détectés dans le DataFrame : {len(doublons)}")  

    # supprimer des doublons
    df = df.drop_duplicates(subset=["meter_id","timestamp"], keep='first')  

    # Vérifier les valeurs aberrantes (les puissances négatives seront supprimées)
    valeurs_aberrantes = df[df["power_kw"] < 0] 
    print(f"Nombre total de valeurs aberrantes détectées dans le DataFrame : {len(valeurs_aberrantes)}")

    # supprimer valeurs aberrantes
    df = df[df["power_kw"] >= 0]  

    # Trier chronologiquement selon "meter_id", "timestamp"
    df = df.sort_values(["meter_id", "timestamp"], ascending=[True, True]) 

    # réinitialiser l’index du DataFrame après un tri, un filtre ou une suppression de lignes 
    df = df.reset_index(drop=True)


    #! Création de nouvelles colonnes
    # Créer une nouvelle colonne heure dans le DataFrame df (de 0 à 23)
    df["heure"] = df["timestamp"].dt.hour

    # Créer une nouvelle colonne jour (de 1 à 30)
    df["jour"] = df["timestamp"].dt.day

    # Créer une nouvelle colonne jour_semaine (0=lundi, 1=mardi, ... 6=dimanche)
    df["jour_semaine"] = df["timestamp"].dt.weekday
    df["type_jour"] = np.where(df["jour_semaine"] < 5, "semaine", "weekend") # classer selon type_jour : semaine ou weekend

    # Créer une nouvelle colonne num_semaine (1=première semaine, 2=deuxième semaine, ... )
    df["num_semaine"] = df["timestamp"].dt.isocalendar().week

    # Créer une nouvelle colonne week_end (True si weekend si non False)
    df["week_end"] = df["jour_semaine"].isin([5,6])

    # Créer une nouvelle colonne energie_h (kwh), multiplie chaque valeur de power_kw par 1 heure (puisque c'est des enregistrements horaires)
    df["energie_kwh"] = df["power_kw"] * 1  

    # Accumulation de l'energie par heure (on peut faire pareil par jour, semaine, ...)
    df["energy_cum_kwh"] = (df.groupby("meter_id")["energie_kwh"].cumsum())

    # Test d'affichage des 2 premières lignes
    print("Test d'affichage de 2 premières lignes de DataFrame :")
    print(df.head(2))

    return df
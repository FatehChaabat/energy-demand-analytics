
/*
générer 1 mois de puissance horaire (720 h) pour 2 compteurs en prenant en compte (profil structuré, effet semaine / week-end, bruit réaliste, quelques pics exceptionnels)

Hypothèses : 1 point par heure, Mois fictif (de 1 au 30 janvier 2026), 2 compteurs (1 = tertiaire HVAC, 2 = process stable), variables (meter_id, timestamp, power_kw)
*/





-- DROP TABLE IF EXISTS Energy_Readings_month                                     
-- GO

-- Créer la table nommée "Energy_Readings_month" avec ses trois colonnes
CREATE TABLE Energy_Readings_month (meter_id INT, timestamp DATETIME, power_kw FLOAT);


-- CTE pour Générer calendrier horaire (30 jours)
WITH hours AS (
    SELECT TOP (24*30)
        DATEADD(HOUR, ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1, '2026-01-01 00:00:00') AS ts -- DATEADD(HOUR, n, date_de_depart) → ajoute n heures, ROW_NUMBER() génère une suite 1,2,3...
    FROM sys.objects a CROSS JOIN sys.objects b                                                    -- Le CROSS JOIN sys.objects sert juste à créer assez de lignes. C’est un générateur.
),


-- CTE pour Générer les puissances horaires pour chaque compteur
data AS (
    SELECT
        m.meter_id,
        h.ts,
        DATEPART(HOUR, h.ts) AS heure,
        DATEPART(WEEKDAY, h.ts) AS jour_semaine,
        -- Profil base compteur 1 (tertiaire HVAC)
        CASE 
            WHEN m.meter_id = 1 THEN
                CASE 
                    WHEN DATEPART(HOUR, h.ts) BETWEEN 0 AND 5 THEN 100     -- nuit
                    WHEN DATEPART(HOUR, h.ts) BETWEEN 6 AND 8 THEN 300     -- montée matin 
                    WHEN DATEPART(HOUR, h.ts) BETWEEN 9 AND 17 THEN 350    -- plateau la journée
                    WHEN DATEPART(HOUR, h.ts) BETWEEN 18 AND 22 THEN 200   -- soir
                    ELSE 150                                               -- 23h
                END
            -- Profil base compteur 2 (process stable)
            ELSE 300                                                       -- pour le compteur 2 la puissance est fixée à 300 kw
        END AS base_power
    FROM hours h
    CROSS JOIN (VALUES (1),(2)) m(meter_id)                                -- Pour chaque heure, on crée : 1 ligne pour compteur 1, 1 ligne pour compteur 2 
        )                                                                  -- pareil avec : CROSS JOIN (SELECT DISTINCT meter_id FROM Energy_Readings_month) m



-- Insertion finale avec bruit + effet week-end + pics
INSERT INTO Energy_Readings_month
SELECT
    meter_id,
    ts,

    -- Calcul puissance finale
    CASE meter_id
        WHEN 1 THEN
            -- compteur 1 : HVAC
            (base_power * CASE WHEN (DATEPART(WEEKDAY, ts) + @@DATEFIRST - 2) % 7 + 1 IN (6,7) THEN 0.65 ELSE 1 END)  -- week-end réduit, (DATEPART(WEEKDAY, ts) + @@DATEFIRST - 2) modulo 7 donne (0=lundi, 1=mardi, ... 6=dimanche), +1 pour passer au (1=lundi, 2=mardi, ... 7=dimanche)   
            + ROUND((RAND(CHECKSUM(NEWID())) - 0.5) * 40,2)                                                           -- bruit ±20 kW
            + CASE WHEN DAY(ts) IN (12,22) AND DATEPART(HOUR, ts) BETWEEN 9 AND 11 THEN 80 ELSE 0 END                 -- pics exceptionnels de 80 kW le 12 et 22 de 9h à 11h
        WHEN 2 THEN
            -- compteur 2 : process stable
            base_power
            + ROUND((RAND(CHECKSUM(NEWID())) - 0.5) * 20,2)                                                           -- bruit ±10 kW
            + CASE WHEN DAY(ts) IN (12,22) AND DATEPART(HOUR, ts) BETWEEN 9 AND 11 THEN 30 ELSE 0 END                 -- pics exceptionnels de 30 kW le 12 et 22 de 9h à 11h
    END AS power_kw
      
FROM data;
 
/* TEST
SELECT * FROM Energy_Readings_month
  WHERE CAST(timestamp AS DATE) IN ('2026-01-01', '2026-01-04' , '2026-01-25')
  AND DATEPART(HOUR, timestamp) BETWEEN 0 AND 5
  */
  
  
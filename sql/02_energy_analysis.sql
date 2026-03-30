
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
/* 
Points à traiter, avec comparaison entre les deux compteurs :
   1) Nettoyage des données : suppression des valeurs manquantes (NULL), des puissances aberrantes (<0) et des doublons sur (meter_id, timestamp)
   2) Calcul des statistiques journalières et horaires de la puissance : moyenne, maximum, minimum, écart-type et coefficient de variation
   3) Calcul du cumul énergétique (énergie cumulée journalière et hebdomadaireet) et comparaison avec la dernière consommation (en kWh et en %)
   4) Pics et heures creuses de consommation (Heures de pointe : 3 pics journaliers, moyenne et classement mensuel; Heures creuses : 6 creux journaliers, moyenne et classement mensuel)
   5) Calcul d'anomalies par Z_score Z_robuste (puissances horaires et journalières)
   6) Etude de la stabilité (Facteur de Pointe), Variabilités (Coefficient de Variation) et Puissance contractuelle (par rapport au P99)
   7) Comparaison statistiques semaine vs weekend (Moyenne sur l'ensemble de données, Calcul de FP et CV, Énergie cumulée, ratio semaine / week-end)
   8) Analyse temporelle et variabilité journalière (Calcul des indicateurs FP et CV pour les heures creuses, pleines et critiques & Comparaison des jours consécutifs pour détecter répétitions, motifs et anomalies)
*/
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ 
-- 1) Nettoyage général : valeurs manquantes, aberrantes et doublons
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


--========== Détection des valeurs manquantes et aberrantes ==========--
SELECT *  
FROM Energy_Readings_month
WHERE meter_id IS NULL OR timestamp IS NULL OR power_kw IS NULL   -- détecte les valeurs manquantes (NULL)
      OR power_kw < 0                                             -- détecte les valeurs aberrantes (Puissance négative)
ORDER BY meter_id, timestamp;

-- Suppression des valeurs manquantes et aberrantes
DELETE FROM Energy_Readings_month
WHERE meter_id IS NULL OR timestamp IS NULL OR power_kw <0;


--========== Détection de doublons ==========--

-- Méthode 1 : GROUP BY et COUNT() 
SELECT
meter_id,
timestamp,
COUNT(*) AS doublons
FROM Energy_Readings_month
GROUP BY meter_id, timestamp
HAVING COUNT(meter_id) > 1;

-- Méthode 2 : CTE pour lister les doublons exacts
;WITH doublons AS (
SELECT meter_id, timestamp
FROM Energy_Readings_month
GROUP BY meter_id, timestamp
HAVING COUNT(*) > 1
)
SELECT e.*
FROM Energy_Readings_month e
JOIN doublons d 
ON e.meter_id = d.meter_id
and e.timestamp = d.timestamp
ORDER BY e.meter_id;

-- Méthode 3 : Window Function pour compter les doublons
SELECT *
FROM (
SELECT *, COUNT(*) OVER (PARTITION BY meter_id, timestamp) AS doublons
FROM Energy_Readings_month
) t
WHERE doublons > 1;

-- Suppression des doublons en gardant la première occurrence
;WITH doublons AS (
SELECT *, ROW_NUMBER() OVER (PARTITION BY meter_id, timestamp ORDER BY meter_id) AS rw
FROM Energy_Readings_month
)
DELETE e
FROM Energy_Readings_month e
JOIN doublons d
  ON e.meter_id = d.meter_id
 AND e.timestamp = d.timestamp
WHERE d.rw > 1;

-- Vérification finale
SELECT *
FROM Energy_Readings_month
ORDER BY meter_id, timestamp;




------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ 
-- 2) Calcul des statistiques de la puissance : moyenne, maximum, minimum, écart-type et coefficient de variation
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


--========== Statistiques journalières (30 valeurs par compteur) ==========--
SELECT 
meter_id,
CAST(timestamp AS DATE) AS jour,
CAST(AVG(power_kw) AS DECIMAL (10,2)) AS puissance_moyenne_journalière,
MAX(power_kw) AS pic_puissance,
MIN(power_kw) AS min_puissance,
CAST(STDEV(power_kw) AS DECIMAL(10,2)) AS ecart_type,
CAST(STDEV(power_kw)/AVG(power_kw) AS DECIMAL(10,2)) AS coefficient_de_variation 
FROM Energy_Readings_month
GROUP BY meter_id, CAST(timestamp AS DATE) 
ORDER BY meter_id, CAST(timestamp AS DATE) 
GO


--========== Statistiques par heure de la journée, agrégées sur l’ensemble du mois (0h, 1h, …, 23h) ==========--   
SELECT 
meter_id,
DATEPART(HOUR, timestamp) as heure, 
CAST(AVG(power_kw) AS DECIMAL (10,2)) AS puissance_horaire,
MAX(power_kw) AS pic_puissance,
MIN(power_kw) AS min_puissance,
CAST(STDEV(power_kw) AS DECIMAL(10,2)) AS ecart_type,
CAST(STDEV(power_kw)/AVG(power_kw) AS DECIMAL(10,2)) AS coefficient_de_variation 
FROM Energy_Readings_month
GROUP BY meter_id, DATEPART(HOUR, timestamp) 
ORDER BY meter_id, DATEPART(HOUR, timestamp)
GO




------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 3) Calcul du cumul énergétique et comparaison avec la dernière consommation (en kWh et en %)
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


--========== Cumul énergétique journalier ==========--
;WITH enrg_jrnl AS (
SELECT
meter_id,
CAST(timestamp AS DATE) AS date,
SUM(power_kw)*1 as energie_journaliere -- des mesures prises chaque une heure donc E = P * Dt = P * 1 h (kwh)
FROM Energy_Readings_month 
GROUP BY meter_id, CAST(timestamp AS DATE)
),
calc AS (
SELECT
e.meter_id,
e.date,
e.energie_journaliere,
LAG(energie_journaliere) OVER (PARTITION BY e.meter_id ORDER BY e.date) AS valeure_précedente
FROM enrg_jrnl e
)
SELECT
c.meter_id,
c.date,
c.energie_journaliere,
c.valeure_précedente AS derniere_consommation,
CAST(c.energie_journaliere - c.valeure_précedente AS DECIMAL (8,3)) AS variation,
CAST(100.0 * (c.energie_journaliere - c.valeure_précedente) / NULLIF(c.valeure_précedente,0) AS DECIMAL(8,3)) AS variation_pourcentage, -- nullif important si la valeure precdente est nulle ça retourne 0
SUM(c.energie_journaliere) OVER (PARTITION BY c.meter_id ORDER BY c.date ROWS UNBOUNDED PRECEDING) AS energie_accumulee
FROM calc c;
GO


--========== Énergie cumulée hebdomadaire (selon le calendrier) ==========--
;WITH enrg_jrnl AS (
SELECT
meter_id,
DATEPART(ISO_WEEK, timestamp) AS semaine_calendrier,                                                   -- ISO_WEEK prend lundi comme 1er jour de la semaine, donc ici la 1ère semaine va de jeudi au dimanche
-- DATEADD(DAY, (DATEDIFF(DAY, '2026-01-01',timestamp) / 7) * 7, '2026-01-01') AS semaine_glissante    -- semaine glissante (bloc fixe de 7 jours a partir de la première date)
SUM(power_kw)*1 as energie_semaine                                                                     
FROM Energy_Readings_month 
GROUP BY meter_id, DATEPART(ISO_WEEK, timestamp)  
), 
calc AS (
SELECT
e.meter_id,
e.semaine_calendrier,
e.energie_semaine,
LAG(energie_semaine) OVER (PARTITION BY e.meter_id ORDER BY e.semaine_calendrier) AS valeure_précedente
FROM enrg_jrnl e
)
SELECT
c.meter_id,
c.semaine_calendrier,
c.energie_semaine,
c.valeure_précedente AS derniere_consommation,
CAST(c.energie_semaine - c.valeure_précedente AS DECIMAL (8,3)) AS variation,
CAST(100.0 * (c.energie_semaine - c.valeure_précedente) / NULLIF(c.valeure_précedente,0) AS DECIMAL(8,3)) AS variation_pourcentage, -- nullif si 'c.valeure_précedente' est nulle ça retourne 0
SUM(c.energie_semaine) OVER (PARTITION BY c.meter_id ORDER BY c.semaine_calendrier ROWS UNBOUNDED PRECEDING) AS energie_accumulee
FROM calc c;
GO




------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 4) Pics et heures creuses de consommation
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


--========== Heures de pointe : 3 pics journaliers, moyenne et classement mensuel ==========--
;WITH base AS (
SELECT
meter_id,
timestamp,
power_kw,
DENSE_RANK() OVER (
PARTITION BY meter_id, CAST(timestamp AS DATE)  -- CAST(e.timestamp AS DATE) permet de clsser les puissances chaques jour, en enlève si on veux un classement pour toute la periode
ORDER BY power_kw DESC                          -- ici le classement se fait par rapport à la puiisance brute pour identifier les heures chargées (classement descendant)
) AS rank_P
FROM Energy_Readings_month
), 
pics_jour AS (      
SELECT 
meter_id,
timestamp,                       
power_kw AS puissances_les_plus_élevés
FROM base
WHERE rank_P <= 3                              -- Filtrer et afficher les 3h les plus chargées chaque jour
),
moyenne_pic_jour AS (
SELECT 
meter_id,
CAST(timestamp AS DATE) AS jour,  
CAST(AVG(puissances_les_plus_élevés) AS DECIMAL(8,2)) AS puissance_moyenne_des_3pics_journaliers,  -- calcul de la moyenne des 3 pics par jour
RANK() OVER (PARTITION BY meter_id ORDER BY AVG(puissances_les_plus_élevés) DESC) AS rank_PJ       -- classement de cette moyenne sur tout le mois 
FROM pics_jour
GROUP BY meter_id, CAST(timestamp AS DATE)
)
SELECT * FROM moyenne_pic_jour     
ORDER by meter_id
GO


--========== Heures creuses : 6 creux journaliers, moyenne et classement mensuel ==========--
;WITH base AS (
SELECT
meter_id,
timestamp,
power_kw,
DENSE_RANK() OVER (PARTITION BY meter_id, CAST(timestamp AS DATE) ORDER BY power_kw ASC) AS rank_P -- classement ascendant
FROM Energy_Readings_month
), 
mins_jour AS (
SELECT 
meter_id,
timestamp, 
power_kw AS puissances_les_moins_élevés
FROM base
WHERE rank_P <= 6                        -- Filtrer et afficher les 6h les moins chargées chaque jour
), 
moyenne_mins_jour AS (
SELECT 
meter_id,
CAST(timestamp AS DATE) AS jour, 
CAST(AVG(puissances_les_moins_élevés) AS DECIMAL(8,2)) AS puissance_moyenne_des_6creux_journaliers,  -- calcul de la moyenne des 6 creux par jour
RANK() OVER (PARTITION BY meter_id ORDER BY AVG(puissances_les_moins_élevés) ASC) AS rank_PJ         -- classement de cette moyenne sur tout le mois 
FROM mins_jour
GROUP BY meter_id, CAST(timestamp AS DATE)
)
SELECT * FROM moyenne_mins_jour     
ORDER by meter_id
GO




------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 5) Calcul d'anomalies par Z_score (puissance - µ)/σ), puis par Z_robuste (puissance - mediane)/(1.4826 * MAD)
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


--========== Anormalies sur les valeurs brutes (horaires) - Z_score ==========--
;WITH hourly AS (
SELECT
meter_id,
timestamp,
power_kw AS power_brute
FROM Energy_Readings_month
),
stats AS (
SELECT
meter_id,
CAST (AVG(power_brute) AS DECIMAL (8,2)) AS mu, 
CAST (STDEV(power_brute) AS DECIMAL (8,2)) AS sigma
FROM hourly 
GROUP BY meter_id
), 
anomalies AS (
SELECT
h.meter_id,
h.timestamp,  
h.power_brute,
s.mu,
s.sigma,
CAST ((h.power_brute - s.mu) / NULLIF(s.sigma,0) AS DECIMAL(8,2)) AS z_score,  
CAST (PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY h.power_brute) OVER (PARTITION BY h.meter_id) AS DECIMAL (8,2)) AS P95 -- calculer le 95ᵉ percentile de la puissance brute pour chaque compteur
FROM hourly h
JOIN stats s
ON h.meter_id = s.meter_id
)
SELECT *                 
FROM anomalies
WHERE ABS(z_score) > 2                   -- filtre les anomalies : Détection le jour ou les jours atypiques (z > 2 positif → Surconsommation, z < -2 → Sous-consommation)
ORDER BY meter_id, timestamp;
 
 
--========== Anormalies sur les valeurs brutes (horaires) - Z_robuste ==========--
;WITH hourly AS (
SELECT
meter_id,
timestamp,
power_kw AS power_brute
FROM Energy_Readings_month
),
medianes AS (
SELECT
meter_id,
power_brute,
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY power_brute) OVER (PARTITION BY meter_id) AS mediane
FROM hourly
),
mad_calc AS (
SELECT
meter_id,
mediane,
ABS(power_brute - mediane) AS abs_dev
FROM medianes
),
mad AS (
SELECT
meter_id,
mediane,
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_dev) OVER (PARTITION BY meter_id) AS MAD 
FROM mad_calc
),
anomalies AS (
SELECT
h.meter_id,
h.timestamp,  
h.power_brute,
m.mediane,
m.MAD,
CAST ((h.power_brute - m.mediane) / NULLIF(1.4826 * m.MAD,0) AS DECIMAL(8,2)) AS z_robuste    -- normaliser par 1.4826 pour une distribution gaussiènne
FROM hourly h
JOIN mad m
ON h.meter_id = m.meter_id
)
SELECT DISTINCT *                   
FROM anomalies
WHERE z_robuste > 2                   
ORDER BY meter_id, timestamp;


--========== Anormalies sur les puissances journalières - Z_score ==========--
;WITH daily AS (
SELECT
meter_id,
CAST(timestamp AS DATE) AS jour,
AVG(power_kw) AS Pmoy_journaliere
FROM Energy_Readings_month
GROUP BY meter_id, CAST(timestamp AS DATE)
),
stats AS (
SELECT
meter_id,
AVG(Pmoy_journaliere) AS mu, 
STDEV(Pmoy_journaliere) AS sigma
FROM daily
GROUP BY meter_id
),
anomalies AS (
SELECT
d.meter_id,
d.jour,  
d.Pmoy_journaliere,
s.mu,
s.sigma,
CAST ((d.Pmoy_journaliere - s.mu) / NULLIF(s.sigma,0) AS DECIMAL(8,2)) AS z_score,  
CAST (PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY d.Pmoy_journaliere) OVER (PARTITION BY d.meter_id) AS DECIMAL (8,2)) AS P95 
FROM daily d
JOIN stats s
ON d.meter_id = s.meter_id
)
SELECT *                 
FROM anomalies
WHERE ABS(z_score) > 2                   
ORDER BY meter_id, jour;


--========== Anormalies sur les puissances journalières - Z_robuste ==========--
;WITH daily AS (
SELECT
meter_id,
CAST(timestamp AS DATE) AS jour,
AVG(power_kw) AS Pmoy_journaliere
FROM Energy_Readings_month
GROUP BY meter_id, CAST(timestamp AS DATE)
),
medianes AS (
SELECT
meter_id,
Pmoy_journaliere,
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY Pmoy_journaliere) OVER (PARTITION BY meter_id) AS mediane
FROM daily
),
mad_calc AS (
SELECT
meter_id,
mediane,
ABS(Pmoy_journaliere - mediane) AS abs_dev
FROM medianes
),
mad AS (
SELECT
meter_id,
mediane,
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY abs_dev) OVER (PARTITION BY meter_id) AS MAD 
FROM mad_calc
),
anomalies AS (
SELECT
d.meter_id,
d.jour,  
d.Pmoy_journaliere,
m.mediane,
m.MAD,
CAST ((d.Pmoy_journaliere - m.mediane) / NULLIF(1.4826 * m.MAD,0) AS DECIMAL(8,2)) AS z_robuste   
FROM daily d
JOIN mad m
ON d.meter_id = m.meter_id
)
SELECT DISTINCT *                   
FROM anomalies
WHERE z_robuste > 2                   
ORDER BY meter_id, jour;




------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 6) Stabilité (Facteur de Pointe), Variabilités (Coefficient de Variation) et Puissance contractuelle (par rapport au P99)
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
/*
- Stabilité : FP proche de 1 → profil plat et stable, FP élevé → profil dynamique
- Variabilité : Plus le CV est faible, plus la charge est régulière autour de la moyenne → profil stable; Plus le CV est élevé, plus la charge fluctue → profil irrégulier
- P99 : utile pour le dimensionnement du contrat et l’optimisation des abonnements. Généralement, la puissance contractuelle est fixée autour de 1,03 × P99
*/


--========== Calcul FP et CV ==========--
;WITH stats AS (
SELECT
meter_id,
power_kw,
AVG(power_kw) OVER (PARTITION BY meter_id) AS moyenne,
STDEV(power_kw) OVER (PARTITION BY meter_id) AS ecart_type,
MAX(power_kw) OVER (PARTITION BY meter_id) AS pic
FROM Energy_Readings_month
)
SELECT DISTINCT
meter_id,
CAST(moyenne AS DECIMAL(10,2)) AS puissance_moyenne,
pic AS pic_puissance,
ecart_type,
CAST(pic/moyenne AS DECIMAL(10,2)) AS Facteur_de_pointe,
CAST(ecart_type/moyenne AS DECIMAL(10,2)) AS Coef_de_variation                               
FROM stats
ORDER BY meter_id;
GO


--========== Calcul du P99 et le nombre de valeurs de puissance au dessus de P99 ==========--
;with calcu as (
SELECT 
meter_id,
timestamp,
power_kw,
PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY power_kw) OVER (PARTITION BY meter_id) AS P99  
FROM Energy_Readings_month
)
SELECT
meter_id,
COUNT(*) AS nb_depassements
FROM calcu
WHERE power_kw > P99                           
GROUP BY meter_id;
GO




------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 7) Comparaison statistiques semaine vs weekend 
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


--========== Moyenne sur l'ensemble de données ==========--
;with calcul_semaine AS (
SELECT
meter_id, 
DATEPART(WEEKDAY, timestamp) AS jour_semaine,
power_kw
FROM Energy_Readings_month
)  
SELECT 
meter_id,
CAST(AVG(CASE WHEN jour_semaine <= 5 THEN power_kw END) AS DECIMAL(10,2)) AS moyenne_jour_semaine, 
CAST(AVG(CASE WHEN jour_semaine > 5 THEN power_kw END) AS DECIMAL(10,2)) AS moyenne_weekend
FROM calcul_semaine
GROUP BY meter_id
ORDER BY meter_id
GO


--========== Moyenne sur l'ensemble de données (Affichage sur des lignes) ==========--
SELECT
meter_id,
CASE WHEN DATEPART(WEEKDAY, timestamp) <= 5 THEN 'Semaine' ELSE 'Weekend' END AS periode,
CAST(AVG(power_kw) AS DECIMAL(10,2)) AS puissance_moyenne
FROM Energy_Readings_month
GROUP BY meter_id, CASE WHEN DATEPART(WEEKDAY, timestamp) <= 5 THEN 'Semaine' ELSE 'Weekend' END
ORDER BY meter_id, periode;
GO


--========== Calcul de FP et CV
SELECT
meter_id,
CASE WHEN DATEPART(WEEKDAY, timestamp) <= 5 THEN 'Semaine' ELSE 'Weekend' END AS periode,
CAST(AVG(power_kw) AS DECIMAL(10,2)) AS puissance_moyenne,
MAX(power_kw) AS pic_puissance,
CAST(STDEV(power_kw) AS DECIMAL(10,2)) AS ecart_type,
CAST(STDEV(power_kw)/AVG(power_kw) AS DECIMAL(10,2)) AS coefficient_de_variation,
CAST(MAX(power_kw)/AVG(power_kw) AS DECIMAL(10,2)) AS facteur_de_pointe_horaire
FROM Energy_Readings_month
GROUP BY meter_id, CASE WHEN DATEPART(WEEKDAY, timestamp) <= 5 THEN 'Semaine' ELSE 'Weekend' END
ORDER BY meter_id, periode;
GO


--========== Énergie cumulée (affichage sur des lignes) ==========--
SELECT
meter_id,
CASE WHEN DATEPART(WEEKDAY, timestamp) <= 5 THEN 'Semaine' ELSE 'Weekend' END AS periode,
CAST(SUM(power_kw)*1 AS DECIMAL(10,2)) AS énergie_total
FROM Energy_Readings_month
GROUP BY
meter_id,
CASE WHEN DATEPART(WEEKDAY, timestamp) <= 5 THEN 'Semaine' ELSE 'Weekend' END
ORDER BY meter_id, periode;


--========== Énergie cumulée (affichage sur des colonnes) ==========--
;with calcul_semaine AS (
SELECT
meter_id,
DATEPART(WEEKDAY, timestamp) AS jour_semaine,
power_kw
FROM Energy_Readings_month
) 
SELECT 
meter_id,
CAST(SUM(CASE WHEN jour_semaine <= 5 THEN power_kw*1 END) AS DECIMAL(10,2)) AS energie_semaine, 
CAST(SUM(CASE WHEN jour_semaine > 5 THEN power_kw*1 END) AS DECIMAL(10,2)) AS energie_weekend
FROM calcul_semaine
GROUP BY meter_id
ORDER BY meter_id
GO


--========== Analyse de la consommation : moyenne journalière et ratio semaine / week-end ==========--
;WITH base AS (
SELECT
meter_id,
CAST(timestamp AS DATE) AS jour,
DATEPART(WEEKDAY, timestamp) AS jour_semaine,
SUM(power_kw) AS energie_journaliere
FROM Energy_Readings_month
GROUP BY
meter_id,
CAST(timestamp AS DATE),
DATEPART(WEEKDAY, timestamp)
), 
agg AS (
SELECT
meter_id,
CAST(AVG(CASE WHEN jour_semaine <= 5 THEN energie_journaliere END) AS DECIMAL(10,2)) AS moyenne_jour_semaine,
CAST(AVG(CASE WHEN jour_semaine > 5 THEN energie_journaliere END) AS DECIMAL(10,2)) AS moyenne_weekend
FROM base
GROUP BY meter_id
)
SELECT *,
CAST(moyenne_jour_semaine / NULLIF(moyenne_weekend,0) AS DECIMAL(10,2)) AS rapport_semaine_sur_weekend,
CASE WHEN moyenne_jour_semaine / NULLIF(moyenne_weekend,0) > 1.1 THEN 'Activite dominante en semaine' ELSE 'Profil similaire' END AS statut
FROM agg
ORDER BY meter_id;                 -- Résulatts : activité dominante en semaine pour le compteur 1 & profil de consommation homogène entre semaine et week-end pour compteur 2




------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 8) Analyse temporelle et variabilité journalière
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


--========== Calcul des indicateurs FP et CV pour les heures creuses, pleines et critiques ==========--
SELECT
meter_id,
CASE WHEN 0 <= DATEPART(HOUR, timestamp) AND DATEPART(HOUR, timestamp) <= 5 THEN 'Heures_creuses'     -- Il faut mettre les plages les plus spécifiques en premier, puis les générales,
     WHEN 9 <= DATEPART(HOUR, timestamp) AND DATEPART(HOUR, timestamp) <= 11 THEN 'Heures_critiques'  -- sinon dans un CASE, SQL s’arrête au premier WHEN vrai.
     WHEN 6 <= DATEPART(HOUR, timestamp) AND DATEPART(HOUR, timestamp) <= 23 THEN 'Heures_pleines'
     ELSE 'Hors_plage'
END AS periode, 
CAST(AVG(power_kw) AS DECIMAL(10,2)) AS puissance_moyenne,
MAX(power_kw) AS pic_puissance,
CAST(STDEV(power_kw) AS DECIMAL(10,2)) AS ecart_type,
CAST(STDEV(power_kw)/AVG(power_kw) AS DECIMAL(10,2)) AS coefficient_de_variation,
CAST(MAX(power_kw)/AVG(power_kw) AS DECIMAL(10,2)) AS facteur_de_pointe_horaire
FROM Energy_Readings_month
GROUP BY
meter_id,
CASE WHEN 0 <= DATEPART(HOUR, timestamp) AND DATEPART(HOUR, timestamp) <= 5 THEN 'Heures_creuses' 
     WHEN 9 <= DATEPART(HOUR, timestamp) AND DATEPART(HOUR, timestamp) <= 11 THEN 'Heures_critiques'
     WHEN 6 <= DATEPART(HOUR, timestamp) AND DATEPART(HOUR, timestamp) <= 23 THEN 'Heures_pleines'
     ELSE 'Hors_plage'
END
ORDER BY meter_id
GO


--========== Comparaison des jours consécutifs pour détecter répétitions, motifs et anomalies ==========--
;WITH enrg_jrnl AS (
SELECT
meter_id,
CAST(timestamp AS DATE) AS date,
SUM(power_kw)*1 as energie_journaliere 
FROM Energy_Readings_month 
GROUP BY meter_id, CAST(timestamp AS DATE)
),
calc AS (
SELECT
e.meter_id,
e.date,
e.energie_journaliere,
LAG(energie_journaliere) OVER (PARTITION BY e.meter_id ORDER BY e.date) AS valeure_précedente
FROM enrg_jrnl e
)
SELECT
c.meter_id,
c.date,
c.energie_journaliere,
c.valeure_précedente AS derniere_consommation,
CAST(c.energie_journaliere - c.valeure_précedente AS DECIMAL (10,2)) AS variation,
CAST(100.0 * (c.energie_journaliere - c.valeure_précedente) / NULLIF(c.valeure_précedente,0) AS DECIMAL(10,2)) AS variation_pourcentage, 
SUM(c.energie_journaliere) OVER (PARTITION BY c.meter_id ORDER BY c.date ROWS UNBOUNDED PRECEDING) AS energie_accumulee,
CASE WHEN ABS(100.0 * (c.energie_journaliere - c.valeure_précedente) / NULLIF(c.valeure_précedente,0)) > 20
THEN 'Anomalie (ATTENTION)' ELSE 'Normal' END AS statut -- résultats montrent que le compteur 1 présente des fluctuations importantes à l’entrée et à la sortie du week-end 
FROM calc c;
GO




------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
/*

A) Choses traitées tout en comparant entre les deux compteurs :
   1) Nettoyage des données : suppression des valeurs manquantes (NULL), des puissances aberrantes (<0) et des doublons sur (meter_id, timestamp)
   2) Calcul des statistiques journalières et horaires de la puissance : moyenne, maximum, minimum, écart-type et coefficient de variation
   3) Calcul du cumul énergétique (énergie cumulée journalière et hebdomadaireet) et comparaison avec la dernière consommation (en kWh et en %)
   4) Pics et heures creuses de consommation (Heures de pointe : 3 pics journaliers, moyenne et classement mensuel; Heures creuses : 6 creux journaliers, moyenne et classement mensuel)
   5) Calcul d'anomalies par Z_score Z_robuste (puissances horaires et journalières)
   6) Etude de la stabilité (Facteur de Pointe), Variabilités (Coefficient de Variation) et Puissance contractuelle (par rapport au P99)
   7) Comparaison statistiques semaine vs weekend (Moyenne sur l'ensemble de données, Calcul de FP et CV, Énergie cumulée, ratio semaine / week-end)
   8) Analyse temporelle et variabilité journalière (Calcul des indicateurs FP et CV pour les heures creuses, pleines et critiques & Comparaison des jours consécutifs pour détecter répétitions, motifs et anomalies)

B) Analyse métier (pas juste statistique) :
   1) Est-ce que le compteur 1 est correctement dimensionné ?
   2) Pmax proche de la limite contractuelle ?
   3) Facteur de pointe acceptable ?
   4) Est-ce que le compteur 2 est trop stable → surdimensionnement ?
   5) Différence % énergie semaine vs week-end → cohérente avec un profil HVAC ?

C) Analyse avancée :
   1) Moyenne mobile
   2) Moyenne glissante 3h ou 6h (Rolling)
   3) Identifier les montées progressives (pas juste les pics instantanés)
   4) Écrêtage, déplacement et réduction de charge et leurs impacts
   5) Potentiel d’optimisation énergétique
   6) Corrélation puissance–température et régression linéaire & Random Forest

CES ANALYSES, RÉALISÉES EN SQL, ONT PERMIS D’EXTRAIRE LES STATISTIQUES CLÉS, D’IDENTIFIER LES HEURES CRITIQUES ET DE DÉTECTER LES IRRÉGULARITÉS, 
ET OUVRENT AINSI LA VOIE À UNE ÉTUDE COMPLÉMENTAIRE SOUS PYTHON POUR APPROFONDIR LES RÉSULTATS ET METTRE EN ŒUVRE DES MODÈLES AVANCÉS.

*/
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

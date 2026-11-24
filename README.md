# 🌊 Prédicteur de surf

Prévisions de **qualité de surf** pour un spot donné, avec pour chaque heure :

- **Vagues** : hauteur (m), période (s), direction (°)
- **Houle** : hauteur et période du swell, hauteur des vagues de vent
- **Vent** : vitesse (km/h), rafales (km/h), direction (°)
- **Température de l'air** (°C) et **température de l'eau** (°C)
- **Pression atmosphérique** (hPa)
- un **score de qualité de 0 à 100** et un avis : `Très mauvais`, `Mauvais`, `Moyen`, `Bon`, `Excellent`

Les données proviennent des API gratuites [Open-Meteo](https://open-meteo.com/) (Marine + Forecast), **sans clé API**. Données sous licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — créditer « Open-Meteo ».

Aucune dépendance externe : uniquement la bibliothèque standard de Python (≥ 3.10).

## Installation

```bash
git clone https://github.com/DFR-Consulting/Surf_prediction.git
cd Surf_prediction
pip install -e .   # optionnel ; sinon utiliser PYTHONPATH=src
```

## Utilisation en ligne de commande

```bash
surf-prediction --spot hossegor --jours 5          # tableau des prévisions horaires
surf-prediction --spot biarritz --format json       # sortie JSON
surf-prediction --liste-spots                       # spots connus
surf-prediction --lat 43.48 --lon -1.56 --orientation 300 --nom "Ma plage" --jours 3
python -m surf_prediction --spot lacanau --jours 2  # équivalent sans installation
```

Exemple de sortie :

```
Prévisions pour Hossegor — La Gravière (43.6628, -1.4414) — 24 heures
Heure        Vagues (m)  Période (s)  Dir. vagues  Houle (m)  Vent (km/h)  ...  Score  Avis
22/08 06h00  1.2         9.0          250°         1.0        8.0          ...  88     Excellent
...
```

## API HTTP + page web

```bash
python -m surf_prediction.api --port 8000
# puis ouvrir http://127.0.0.1:8000 dans un navigateur
```

Le serveur écoute par défaut en **boucle locale** (`127.0.0.1`).

| Route | Description |
|---|---|
| `GET /` | Page web de visualisation |
| `GET /api/spots` | Liste des spots connus |
| `GET /api/previsions?spot=<clé>&jours=<1-7>` | Prévisions horaires scorées (JSON) |

## Comment est calculé le score (0–100) ?

Moyenne pondérée de cinq composantes (les poids sont renormalisés si une donnée manque) :

| Composante | Poids | Idéal |
|---|---|---|
| Hauteur des vagues | 30 % | ~1,5 m (trop faible ou trop fort pénalise) |
| Période des vagues | 25 % | ≥ 12 s (houle longue = vagues plus puissantes et propres) |
| Vent | 25 % | vent faible ; pénalité forte si vent **onshore** (de mer), bonus si **offshore** (de terre), selon l'orientation du spot |
| Confort thermique (air + eau) | 10 % | air ~24 °C, eau ~22 °C |
| Pression atmosphérique | 10 % | haute pression stable (≥ 1024 hPa) |

Seuils d'avis : **≥ 80** Excellent · **≥ 60** Bon · **≥ 40** Moyen · **≥ 20** Mauvais · **< 20** Très mauvais.

## Spots inclus

| Clé | Spot | Orientation |
|---|---|---|
| `biarritz` | Biarritz — Grande Plage | 300° |
| `anglet` | Anglet — Les Cavaliers | 300° |
| `hossegor` | Hossegor — La Gravière | 285° |
| `guethary` | Guéthary | 290° |
| `lacanau` | Lacanau — Océan | 280° |
| `nazare` | Nazaré — Praia do Norte (Portugal) | 270° |
| `pipeline` | Pipeline — North Shore, Oahu (Hawaï) | 355° |

Pour ajouter un spot : dictionnaire `SPOTS` dans `src/surf_prediction/spots.py` (l'orientation est l'azimut vers la mer, utilisé pour classer le vent onshore/offshore).

## Tests

```bash
python -m unittest discover -s tests -v   # ou simplement : pytest
```

Les tests n'appellent pas le réseau : le transport HTTP est remplacé par un faux transport.

## Structure du projet

```
src/surf_prediction/
├── models.py                  # Spot, PrevisionHoraire
├── spots.py                   # spots connus (lat/lon/orientation)
├── scoring.py                 # score 0-100 et avis
├── providers/open_meteo.py    # client API Open-Meteo (Marine + Forecast)
├── cli.py                     # ligne de commande
├── api.py                     # serveur HTTP (stdlib) + endpoints JSON
└── web/index.html             # page de visualisation
tests/                         # tests unitaires (unittest / pytest)
```

## Limites

- Prévisions limitées à **7 jours** (limite de l'API Open-Meteo), horaires, fuseau horaire automatique du spot.
- Le score est un modèle heuristique explicable, pas un modèle d'apprentissage automatique.

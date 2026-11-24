from __future__ import annotations

from .models import Spot

SPOTS: dict[str, Spot] = {
    "biarritz": Spot(
        "biarritz", "Biarritz — Grande Plage", 43.4832, -1.5586, 300.0,
        "Côte basque, plage urbaine orientée ouest-nord-ouest.",
    ),
    "anglet": Spot(
        "anglet", "Anglet — Les Cavaliers", 43.5203, -1.5117, 300.0,
        "Longue plage de sable de la côte basque, exposée ouest-nord-ouest.",
    ),
    "hossegor": Spot(
        "hossegor", "Hossegor — La Gravière", 43.6628, -1.4414, 285.0,
        "Spot célèbre du sud des Landes, exposé ouest.",
    ),
    "guethary": Spot(
        "guethary", "Guéthary", 43.4256, -1.6061, 290.0,
        "Spot de la côte basque entre Biarritz et Saint-Jean-de-Luz.",
    ),
    "lacanau": Spot(
        "lacanau", "Lacanau — Océan", 44.9778, -1.0752, 280.0,
        "Grande plage du Médoc, exposée ouest.",
    ),
    "nazare": Spot(
        "nazare", "Nazaré — Praia do Norte (Portugal)", 39.6029, -9.0703, 270.0,
        "Spot portugais connu pour ses vagues géantes, exposé ouest.",
    ),
    "pipeline": Spot(
        "pipeline", "Pipeline — North Shore, Oahu (Hawaï)", 21.6659, -158.0537, 355.0,
        "Spot mythique de la côte nord d'Oahu, exposé nord.",
    ),
}


def liste_spots() -> list[Spot]:
    return list(SPOTS.values())


def obtenir_spot(cle: str) -> Spot | None:
    return SPOTS.get(cle.strip().lower())


def spot_par_defaut() -> Spot:
    return SPOTS["biarritz"]

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Spot:
    cle: str
    nom: str
    latitude: float
    longitude: float
    orientation_deg: float
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PrevisionHoraire:
    horodate: str
    hauteur_vagues_m: float | None = None
    periode_vagues_s: float | None = None
    direction_vagues_deg: float | None = None
    hauteur_houle_m: float | None = None
    periode_houle_s: float | None = None
    hauteur_vagues_vent_m: float | None = None
    vent_vitesse_kmh: float | None = None
    vent_rafales_kmh: float | None = None
    vent_direction_deg: float | None = None
    temperature_air_c: float | None = None
    temperature_eau_c: float | None = None
    pression_hpa: float | None = None
    score: float = 0.0
    avis: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

"""Prédicteur de qualité de surf basé sur les prévisions Open-Meteo."""

from .models import PrevisionHoraire, Spot

__version__ = "0.1.0"

__all__ = ["PrevisionHoraire", "Spot", "__version__"]

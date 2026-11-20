from __future__ import annotations

import time
from typing import Any

import requests


class ServicioMapasError(Exception):
    """Error legible al consultar los servicios cartográficos públicos."""


def geocodificar(direccion: str) -> dict[str, Any]:
    try:
        respuesta = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": direccion, "format": "jsonv2", "limit": 1},
            headers={"User-Agent": "RutaSeguraPredict/1.0 (prototipo academico)"},
            timeout=20,
        )
        respuesta.raise_for_status()
    except requests.RequestException as error:
        raise ServicioMapasError(f"El servicio de direcciones no respondió: {error}") from error

    time.sleep(1.05)
    resultados = respuesta.json()
    if not resultados:
        raise ServicioMapasError(
            f"No se encontró «{direccion}». Agrega ciudad y país, y revisa la escritura."
        )
    return {
        "lat": float(resultados[0]["lat"]),
        "lon": float(resultados[0]["lon"]),
    }


def calcular_ruta(
    lugares: list[dict[str, Any]],
    direcciones: list[str],
) -> dict[str, Any]:
    if len(lugares) < 2 or len(lugares) != len(direcciones):
        raise ValueError("Se requieren al menos dos lugares y una dirección por cada lugar.")

    coordenadas = ";".join(f"{lugar['lon']},{lugar['lat']}" for lugar in lugares)
    try:
        respuesta_viaje = requests.get(
            f"https://router.project-osrm.org/trip/v1/driving/{coordenadas}",
            params={
                "roundtrip": "false",
                "source": "first",
                "destination": "last",
                "overview": "false",
            },
            timeout=30,
        )
        respuesta_viaje.raise_for_status()
        datos_viaje = respuesta_viaje.json()
        if datos_viaje.get("code") != "Ok" or not datos_viaje.get("trips"):
            raise ServicioMapasError(
                f"OSRM no encontró un recorrido válido: {datos_viaje.get('code', 'respuesta desconocida')}."
            )

        orden = sorted(
            range(len(datos_viaje["waypoints"])),
            key=lambda indice: datos_viaje["waypoints"][indice]["waypoint_index"],
        )
        lugares_ordenados = [lugares[indice] for indice in orden]
        direcciones_ordenadas = [direcciones[indice] for indice in orden]
        coordenadas_ordenadas = ";".join(
            f"{lugar['lon']},{lugar['lat']}" for lugar in lugares_ordenados
        )

        respuesta_ruta = requests.get(
            f"https://router.project-osrm.org/route/v1/driving/{coordenadas_ordenadas}",
            params={"overview": "full", "geometries": "geojson", "steps": "false"},
            timeout=30,
        )
        respuesta_ruta.raise_for_status()
        datos_ruta = respuesta_ruta.json()
    except requests.RequestException as error:
        raise ServicioMapasError(f"El servicio de rutas no respondió: {error}") from error

    if datos_ruta.get("code") != "Ok" or not datos_ruta.get("routes"):
        raise ServicioMapasError(
            f"OSRM no pudo dibujar la ruta: {datos_ruta.get('code', 'respuesta desconocida')}."
        )

    recorrido = datos_ruta["routes"][0]
    paradas = [
        {
            "orden": numero,
            "direccion": direccion,
            "lat": lugar["lat"],
            "lon": lugar["lon"],
        }
        for numero, (direccion, lugar) in enumerate(
            zip(direcciones_ordenadas, lugares_ordenados),
            start=1,
        )
    ]
    return {
        "paradas": paradas,
        "geometria": recorrido["geometry"]["coordinates"],
        "distancia_km": float(recorrido["distance"]) / 1000,
        "duracion_osrm_min": float(recorrido["duration"]) / 60,
        "segmentos_km": [float(tramo["distance"]) / 1000 for tramo in recorrido["legs"]],
    }

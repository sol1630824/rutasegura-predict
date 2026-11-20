from __future__ import annotations

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


CARACTERISTICAS = [
    "distancia_km",
    "promedio_tramo_km",
    "variacion_tramo_km",
    "dispersion_km",
    "cantidad_paradas",
    "hora_salida",
    "nivel_trafico",
]
OBJETIVO = "tiempo_minutos"


def crear_historial_sintetico(cantidad: int = 800, semilla: int = 42) -> pd.DataFrame:
    """Genera rutas artificiales reproducibles; no son registros de entregas reales.

    Cada fila contiene siete variables operativas y `tiempo_minutos`, calculado con
    una regla simulada y ruido aleatorio para demostrar el entrenamiento.
    """
    generador = np.random.default_rng(semilla)
    paradas = generador.integers(3, 13, size=cantidad)
    distancia = generador.uniform(3, 45, size=cantidad)
    hora = generador.integers(6, 23, size=cantidad)
    trafico = generador.uniform(0.6, 1.8, size=cantidad)
    promedio_tramo = distancia / (paradas - 1) * generador.uniform(0.8, 1.2, size=cantidad)
    variacion_tramo = generador.uniform(0.2, 2.8, size=cantidad)
    dispersion = generador.uniform(0.3, 14, size=cantidad)
    hora_punta = np.isin(hora, [7, 8, 9, 16, 17, 18, 19]).astype(float)
    ruido = generador.normal(0, 5, size=cantidad)
    tiempo = (
        distancia * 3.1
        + (paradas - 1) * 3.0
        + promedio_tramo * 1.5
        + variacion_tramo * 0.8
        + dispersion * 0.25
        + (trafico - 0.6) * 12
        + hora_punta * 11
        + ruido
    )

    return pd.DataFrame(
        {
            "distancia_km": distancia,
            "promedio_tramo_km": promedio_tramo,
            "variacion_tramo_km": variacion_tramo,
            "dispersion_km": dispersion,
            "cantidad_paradas": paradas,
            "hora_salida": hora,
            "nivel_trafico": trafico,
            OBJETIVO: np.maximum(tiempo, 1),
        }
    )


def entrenar_y_evaluar(
    historial: pd.DataFrame,
) -> tuple[
    LinearRegression,
    tf.keras.Model,
    StandardScaler,
    dict[str, dict[str, float]],
    pd.DataFrame,
]:
    """Entrena y compara la regresión simple y la red neuronal.

    Las filas del historial forman la matriz de rutas y sus siete características
    son las columnas. Se reserva un 20 % para prueba. La regresión usa únicamente
    la distancia; la red usa las siete variables normalizadas con un escalador
    ajustado solo con los datos de entrenamiento.

    Devuelve ambos modelos, el escalador, MSE/RMSE/R² de prueba y una tabla con
    tiempos observados simulados y predicciones para graficar la comparación.
    """
    x = historial[CARACTERISTICAS]
    y = historial[OBJETIVO]
    x_entrena, x_prueba, y_entrena, y_prueba = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
    )

    regresion = LinearRegression()
    regresion.fit(x_entrena[["distancia_km"]], y_entrena)
    pred_lineal = regresion.predict(x_prueba[["distancia_km"]])

    escalador = StandardScaler()
    x_entrena_escalado = escalador.fit_transform(x_entrena)
    x_prueba_escalado = escalador.transform(x_prueba)
    tf.keras.utils.set_random_seed(42)
    red = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(len(CARACTERISTICAS),)),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1),
        ]
    )
    red.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.01), loss="mse")
    parada_temprana = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=10,
        restore_best_weights=True,
    )
    red.fit(
        x_entrena_escalado,
        y_entrena,
        validation_split=0.2,
        epochs=100,
        batch_size=32,
        callbacks=[parada_temprana],
        verbose=0,
    )
    pred_red = red.predict(x_prueba_escalado, verbose=0).reshape(-1)

    metricas: dict[str, dict[str, float]] = {}
    for nombre, prediccion in (
        ("Regresión lineal", pred_lineal),
        ("Red neuronal", pred_red),
    ):
        mse = mean_squared_error(y_prueba, prediccion)
        metricas[nombre] = {
            "MSE": float(mse),
            "RMSE (min)": float(np.sqrt(mse)),
            "R²": float(r2_score(y_prueba, prediccion)),
        }

    prueba = pd.DataFrame(
        {
            "real": y_prueba.to_numpy(),
            "regresion_lineal": pred_lineal,
            "red_neuronal": pred_red,
        }
    )
    return regresion, red, escalador, metricas, prueba

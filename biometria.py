from __future__ import annotations

import cv2
import numpy as np


UMBRAL_DISTANCIA = 75.0
TAMANO_ROSTRO = (160, 160)


def extraer_rostro(contenido: bytes) -> np.ndarray:
    imagen = cv2.imdecode(np.frombuffer(contenido, dtype=np.uint8), cv2.IMREAD_COLOR)
    if imagen is None:
        raise ValueError("No se pudo leer la imagen. Usa un archivo JPG o PNG válido.")

    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    mejorador = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gris = mejorador.apply(gris)
    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    rostros = detector.detectMultiScale(
        gris,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )
    if len(rostros) != 1:
        raise ValueError("La imagen debe mostrar exactamente un rostro, de frente y bien iluminado.")

    x, y, ancho, alto = rostros[0]
    recorte = gris[y : y + alto, x : x + ancho]
    recorte = cv2.resize(recorte, TAMANO_ROSTRO)
    return recorte


def crear_reconocedor(rostros: list[np.ndarray]) -> cv2.face.LBPHFaceRecognizer:
    if len(rostros) < 3:
        raise ValueError("Se necesitan al menos 3 fotos válidas para registrar el rostro.")
    if not hasattr(cv2, "face"):
        raise RuntimeError(
            "Falta el módulo cv2.face. Instala opencv-contrib-python-headless "
            "desde requirements.txt."
        )

    reconocedor = cv2.face.LBPHFaceRecognizer_create()
    reconocedor.train(rostros, np.zeros(len(rostros), dtype=np.int32))
    return reconocedor


def verificar_rostro(
    reconocedor: cv2.face.LBPHFaceRecognizer,
    rostro: np.ndarray,
) -> tuple[bool, float]:
    etiqueta, distancia = reconocedor.predict(rostro)
    return etiqueta == 0 and distancia <= UMBRAL_DISTANCIA, float(distancia)

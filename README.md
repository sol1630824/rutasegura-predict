# RutaSegura & Predict

Prototipo académico en Streamlit para demostrar inicio de sesión facial, optimización de cinco a diez paradas, estadísticas y comparación de modelos de predicción.

## Requisitos

- Windows y Python 3.11 de 64 bits.
- Conexión a Internet para instalar las dependencias, buscar direcciones y consultar las rutas.
- Cámara y permiso del navegador para registrar y validar el rostro.

## Instalación y ejecución en PowerShell

Abre PowerShell en esta carpeta y ejecuta estos comandos, uno por uno:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

La última orden inicia la aplicación; abre la dirección local que muestra Streamlit, normalmente `http://localhost:8501`. Si `py -3.11` no funciona, instala Python 3.11 y activa la opción para agregar Python al PATH.

Si la aplicación ya estaba abierta cuando cambiaste los archivos, pulsa **Rerun** en el aviso de Streamlit. Si sigue apareciendo un error, detén el servidor con `Ctrl+C` en PowerShell y vuelve a ejecutar el último comando.

## Cómo hacer la demostración

1. En la portada, elige **Registrarme**, escribe el nombre del repartidor y toma tres fotos del mismo rostro. También se pueden subir tres o más fotos JPG/PNG. Debe haber un solo rostro visible por imagen.
2. Al crear el perfil, la aplicación abre el inicio de sesión. Selecciona el perfil y toma otra foto para validar el rostro antes de entrar.
3. Para volver a entrar durante la misma sesión, elige **Iniciar sesión** y realiza solo la validación facial.
4. Ingresa entre cinco y diez direcciones con ciudad y país. Usa ubicaciones de prueba y acepta el aviso de envío antes de consultar el mapa.
5. Revisa el orden optimizado, el trayecto, sus estadísticas, las predicciones y las métricas.
6. Descarga `historial_sintetico_rutas.csv` desde la aplicación para inspeccionar el conjunto de entrenamiento.

Los perfiles y sus plantillas faciales se conservan solo en la sesión actual de Streamlit. Al cerrar la pestaña o reiniciar la aplicación, se deben registrar de nuevo; no se guardan en disco.

## Módulos principales

- `app.py`: interfaz, autenticación, estadísticas de cada ruta y gráfico comparativo con Matplotlib.
- `geo.py`: búsqueda de direcciones y cálculo del recorrido por carretera.
- `biometria.py`: detección y normalización de rostros, entrenamiento y validación LBPH.
- `modelo.py`: creación del historial sintético, regresión lineal, red neuronal Keras y métricas. Las funciones principales incluyen docstrings con los pasos y la forma de los datos.
- `comparacion_modelos.png`: gráfico real-versus-predicho incluido también en el informe.

## Decisiones técnicas y lectura de resultados

- **Datos históricos:** no se proporcionaron datos reales. `modelo.py` genera 800 ejemplos sintéticos con una semilla fija. El tiempo simulado depende de distancia, paradas, características de los tramos, hora, tráfico y ruido. El CSV descargable permite revisar los datos; no debe presentarse como historial real de una empresa.
- **Direcciones y ruta:** Nominatim convierte las direcciones en coordenadas; OSRM busca un orden de visita y calcula el trayecto por carretera. El orden es una optimización aproximada del servicio, no una garantía de óptimo global. No se modelan las condiciones reales de tráfico.
- **Biometría:** OpenCV detecta y normaliza un rostro; el reconocedor LBPH se entrena con tres fotos del mismo repartidor. En el inicio de sesión se elige un perfil y la distancia compara la imagen de verificación con su registro. Es una demostración educativa, susceptible a errores y suplantación; no es autenticación segura ni debe usarse con datos personales reales.
- **Regresión lineal simple:** estima los minutos usando solo la distancia total.
- **Red neuronal:** las siete características de cada ruta forman un vector; varias rutas forman una matriz. `StandardScaler` normaliza cada columna usando solo los datos de entrenamiento. Las capas densas multiplican los valores por pesos aprendidos y aplican ReLU; la salida es un número continuo de minutos. Keras ajusta los pesos para reducir el error cuadrático medio.
- **Evaluación:** los modelos se prueban con un 20 % de los ejemplos que no se usó para ajustarlos. MSE promedia errores al cuadrado; RMSE expresa un error típico en minutos y penaliza más los errores grandes; R² compara la variación explicada con la variación total. Menor RMSE suele ser preferible, pero las métricas sintéticas no demuestran el desempeño en una operación real.
- **Privacidad:** los nombres, fotos y modelos faciales se conservan en memoria durante la sesión actual y no se escriben en disco, pero se procesan en el servidor donde se ejecuta la aplicación. Al geocodificar, las direcciones y coordenadas se comparten con los servicios públicos indicados en pantalla. El prototipo no debe exponerse públicamente ni utilizarse como control de acceso real.
- **Uso en vehículo:** la aplicación se prepara antes del viaje y muestra cada parada en botones grandes adaptables a móvil. Para navegar, abre el enlace de la parada con el vehículo estacionado y activa las indicaciones por voz. Coloca el móvil en un soporte fijo, sin bloquear la vista ni airbags; nunca escribas, toques ni mires la pantalla en movimiento. El prototipo no detecta si el vehículo está andando.
- **Poca iluminación:** el preprocesamiento usa CLAHE para mejorar el contraste local del rostro, pero no puede garantizar reconocimiento en oscuridad, contraluz, movimiento o con el rostro cubierto. En ese caso, estaciona en un lugar seguro, enciende la luz interior y vuelve a intentarlo. No uses el flash mientras conduces.
- **Interfaz:** usa una identidad visual propia, tema claro de alto contraste con alternativa oscura, controles grandes y separa la vista de conducción del informe académico. El tema puede cambiarse desde el menú de Streamlit.
- **Uso desde el teléfono:** `localhost:8501` solo es accesible en el mismo equipo que ejecuta Streamlit. Para abrir la aplicación en el móvil del conductor hace falta desplegarla en un servidor con HTTPS y autenticación real; no publiques este prototipo biométrico tal cual ni lo uses como acceso de producción.

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st

import geo
import modelo
from biometria import crear_reconocedor, extraer_rostro, verificar_rostro


st.set_page_config(
    page_title="RutaSegura | Gestión de repartos",
    page_icon=":material/route:",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(
    """
    <style>
    .stButton button, .stLinkButton a, .stFormSubmitButton button {
        min-height: 3rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 0.65rem;
    }
    .st-key-main_header {
        position: relative;
    }
    .st-key-main_header .st-key-cerrar_sesion {
        position: absolute;
        right: 0;
        top: 0.2rem;
        width: auto !important;
        z-index: 5;
    }
    .st-key-main_header .st-key-cerrar_sesion button {
        min-width: 5rem;
        width: auto !important;
    }
    .st-key-brand_header {
        box-sizing: border-box;
        margin: 0.25rem 0 0.45rem;
        padding: 0.3rem 0.4rem;
    }
    .st-key-brand_header h3 {
        font-size: 1.5rem;
        font-weight: 750;
        line-height: 1.3;
        margin: 0;
        padding: 0.15rem 0.2rem 0.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        min-height: 3rem;
        font-weight: 650;
    }
    [data-testid="stMetric"] {
        background: transparent;
        border: 1px solid rgba(100, 120, 140, 0.35);
        border-radius: 0.8rem;
        padding: 0.9rem 1rem;
    }
    @media (max-width: 640px) {
        .block-container { padding: 2rem 0.85rem 2rem; }
        h1 { font-size: 1.7rem; }
        h2 { font-size: 1.35rem; }
        .st-key-main_header .st-key-cerrar_sesion {
            position: static;
        }
        .st-key-brand_header h3 { font-size: 1.1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def mostrar_marca() -> None:
    with st.container(key="brand_header", gap="xxsmall"):
        st.markdown("### RutaSegura")
        st.caption("Predict · Gestión de rutas")


if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "perfiles_repartidores" not in st.session_state:
    st.session_state.perfiles_repartidores = {}
if "nombre_autenticado" not in st.session_state:
    st.session_state.nombre_autenticado = ""
if "vista_acceso" not in st.session_state:
    st.session_state.vista_acceso = "inicio"
if "mensaje_registro" not in st.session_state:
    st.session_state.mensaje_registro = ""
if "capturas_rostro" not in st.session_state:
    st.session_state.capturas_rostro = []
if "ruta" not in st.session_state:
    st.session_state.ruta = None


def cambiar_vista_acceso(vista: str) -> None:
    st.session_state.vista_acceso = vista
    st.rerun()


def guardar_perfil_repartidor(nombre: str, rostros: list[np.ndarray]) -> None:
    nombre = nombre.strip()
    if not nombre:
        st.error("Escribe el nombre del repartidor para continuar.")
        return

    perfiles = st.session_state.perfiles_repartidores
    if any(nombre_existente.casefold() == nombre.casefold() for nombre_existente in perfiles):
        st.error("Ya existe un perfil con ese nombre en esta sesión. Inicia sesión o usa otro nombre.")
        return

    try:
        reconocedor = crear_reconocedor(rostros)
    except ValueError as error:
        st.error(str(error))
        return

    perfiles[nombre] = reconocedor
    st.session_state.capturas_rostro = []
    st.session_state.autenticado = False
    st.session_state.nombre_autenticado = ""
    st.session_state.mensaje_registro = (
        f"Perfil de {nombre} creado. Ahora valida tu rostro para ingresar."
    )
    st.session_state.vista_acceso = "login"
    st.rerun()


def mostrar_portada_acceso() -> None:
    mostrar_marca()
    st.caption("Planifica cada entrega con tranquilidad.")

    columna_login, columna_registro = st.columns(2, gap="small")
    with columna_login.container(border=True):
        st.markdown("#### Ya tengo cuenta")
        st.write("Valida tu rostro para abrir tus rutas.")
        if st.button(
            "Iniciar sesión",
            key="abrir_inicio_sesion",
            icon=":material/login:",
            type="primary",
            width="stretch",
        ):
            cambiar_vista_acceso("login")

    with columna_registro.container(border=True):
        st.markdown("#### Nuevo repartidor")
        st.write("Crea tu perfil con tres fotos y valídalo.")
        if st.button(
            "Registrarme",
            key="abrir_registro",
            icon=":material/person_add:",
            width="stretch",
        ):
            cambiar_vista_acceso("registro")

    with st.expander("Privacidad y seguridad"):
        st.write(
            "Este prototipo conserva los perfiles solo durante la sesión actual. Las fotos y "
            "plantillas faciales no se guardan en disco. Regístrate y vuelve a iniciar sesión "
            "sin cerrar la pestaña para probar el flujo."
        )
        st.caption(
            "Es una demostración educativa; no reemplaza un sistema biométrico de producción."
        )


def mostrar_inicio_sesion() -> None:
    mostrar_marca()
    if st.button("Volver al inicio", key="volver_desde_login", icon=":material/arrow_back:"):
        cambiar_vista_acceso("inicio")

    st.header("Iniciar sesión")
    st.caption("Selecciona tu perfil y valida tu rostro con la cámara.")
    if st.session_state.mensaje_registro:
        st.success(st.session_state.mensaje_registro)
        st.session_state.mensaje_registro = ""

    perfiles = st.session_state.perfiles_repartidores
    if not perfiles:
        st.info("Todavía no hay perfiles registrados en esta sesión.")
        if st.button(
            "Registrar nuevo repartidor",
            key="ir_a_registro_desde_login",
            type="primary",
            width="stretch",
        ):
            cambiar_vista_acceso("registro")
        return

    with st.container(border=True):
        nombre = st.selectbox("Repartidor", sorted(perfiles), key="perfil_inicio_sesion")
        foto = st.camera_input(
            "Toma una foto para validar tu identidad",
            key=f"foto_inicio_sesion_{nombre}",
        )
        st.caption("Con el vehículo estacionado, mira a la cámara y toma una foto.")
        if st.button(
            "Validar rostro e ingresar",
            key="validar_inicio_sesion",
            disabled=foto is None,
            type="primary",
            width="stretch",
        ):
            try:
                rostro = extraer_rostro(foto.getvalue())
                coincide, distancia = verificar_rostro(perfiles[nombre], rostro)
                if coincide:
                    st.session_state.autenticado = True
                    st.session_state.nombre_autenticado = nombre
                    st.success(f"Identidad verificada. Bienvenido/a, {nombre}.")
                    st.rerun()
                else:
                    st.error(
                        f"El rostro no coincide con el perfil seleccionado "
                        f"(distancia: {distancia:.1f}). Intenta con mejor iluminación."
                    )
            except ValueError as error:
                st.error(str(error))


def mostrar_registro_repartidor() -> None:
    mostrar_marca()
    if st.button("Volver al inicio", key="volver_desde_registro", icon=":material/arrow_back:"):
        cambiar_vista_acceso("inicio")

    st.header("Registro de nuevo repartidor")
    st.caption("Completa tu perfil y registra tres fotos del mismo rostro.")
    with st.container(border=True):
        nombre = st.text_input(
            "Nombre del repartidor",
            key="nombre_registro",
            placeholder="Por ejemplo: Ana Pérez",
        )
        metodo = st.radio(
            "¿Cómo quieres registrar el rostro?",
            ["Tomar fotos con la cámara", "Subir fotos existentes"],
            horizontal=True,
            key="metodo_registro",
        )

        if metodo == "Tomar fotos con la cámara":
            capturas = st.session_state.capturas_rostro
            st.write(f"Fotos válidas: {len(capturas)} de 3")
            st.progress(len(capturas) / 3)
            if len(capturas) < 3:
                numero_foto = len(capturas) + 1
                foto = st.camera_input(
                    f"Toma la foto {numero_foto} de 3",
                    key=f"captura_registro_{numero_foto}",
                )
                if st.button(
                    f"Guardar foto {numero_foto}",
                    disabled=foto is None,
                    key=f"guardar_registro_{numero_foto}",
                    type="primary",
                    width="stretch",
                ):
                    try:
                        rostro = extraer_rostro(foto.getvalue())
                        st.session_state.capturas_rostro.append(rostro)
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

            if st.button(
                "Crear perfil y continuar",
                key="finalizar_registro",
                disabled=len(capturas) != 3 or not nombre.strip(),
                type="primary",
                width="stretch",
            ):
                guardar_perfil_repartidor(nombre, capturas)

            if capturas and st.button("Borrar fotos y empezar de nuevo", key="borrar_capturas"):
                st.session_state.capturas_rostro = []
                st.rerun()
        else:
            fotos = st.file_uploader(
                "Elige 3 o más fotos de la misma persona",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="fotos_registro",
            )
            st.caption("En cada imagen debe aparecer un solo rostro, de frente y bien iluminado.")
            if st.button(
                "Crear perfil y continuar",
                key="finalizar_registro_archivos",
                disabled=len(fotos) < 3 or not nombre.strip(),
                type="primary",
                width="stretch",
            ):
                try:
                    rostros = [extraer_rostro(foto.getvalue()) for foto in fotos]
                    guardar_perfil_repartidor(nombre, rostros)
                except ValueError as error:
                    st.error(str(error))


def autenticar() -> None:
    if st.session_state.vista_acceso == "registro":
        mostrar_registro_repartidor()
    elif st.session_state.vista_acceso == "login":
        mostrar_inicio_sesion()
    else:
        mostrar_portada_acceso()


@st.cache_data(ttl=86400, show_spinner=False)
def geocodificar_con_cache(direccion: str) -> dict[str, Any]:
    return geo.geocodificar(direccion)


@st.cache_resource
def preparar_modelos() -> tuple[pd.DataFrame, Any, Any, Any, dict[str, dict[str, float]], pd.DataFrame]:
    historial = modelo.crear_historial_sintetico()
    regresion, red, escalador, metricas, prueba = modelo.entrenar_y_evaluar(historial)
    return historial, regresion, red, escalador, metricas, prueba


def calcular_dispersion_km(coordenadas: list[tuple[float, float]]) -> float:
    """Calcula la distancia RMS de las paradas al centro geográfico aproximado."""
    puntos = np.asarray(coordenadas, dtype=float)
    latitudes = puntos[:, 0]
    longitudes = puntos[:, 1]
    lat_centro = float(np.mean(latitudes))
    lon_centro = float(np.mean(longitudes))
    delta_lat = (latitudes - lat_centro) * 111.0
    delta_lon = (longitudes - lon_centro) * 111.0 * np.cos(np.radians(lat_centro))
    distancias = np.sqrt(delta_lat**2 + delta_lon**2)
    return float(np.sqrt(np.mean(distancias**2)))


def extraer_estadisticas_ruta(ruta: dict[str, Any]) -> dict[str, float]:
    """Deriva distancia, estadísticas de tramos y dispersión desde una ruta geocodificada."""
    segmentos = np.asarray(ruta["segmentos_km"], dtype=float)
    coordenadas = [(parada["lat"], parada["lon"]) for parada in ruta["paradas"]]
    return {
        "distancia_km": float(ruta["distancia_km"]),
        "promedio_tramo_km": float(np.mean(segmentos)),
        "variacion_tramo_km": float(np.std(segmentos)),
        "dispersion_km": calcular_dispersion_km(coordenadas),
        "cantidad_paradas": float(len(ruta["paradas"])),
    }


def mostrar_mapa(ruta: dict[str, Any]) -> None:
    paradas = pd.DataFrame(ruta["paradas"])
    centro = [float(paradas["lat"].mean()), float(paradas["lon"].mean())]
    capa_ruta = pdk.Layer(
        "PathLayer",
        data=[{"path": ruta["geometria"]}],
        get_path="path",
        get_color=[15, 118, 110],
        width_scale=8,
        width_min_pixels=4,
        pickable=True,
    )
    capa_paradas = pdk.Layer(
        "ScatterplotLayer",
        data=paradas,
        get_position="[lon, lat]",
        get_fill_color=[197, 91, 52],
        get_radius=90,
        radius_min_pixels=7,
        pickable=True,
    )
    mapa = pdk.Deck(
        layers=[capa_ruta, capa_paradas],
        initial_view_state=pdk.ViewState(
            latitude=centro[0],
            longitude=centro[1],
            zoom=12,
            pitch=0,
        ),
        tooltip={"text": "{orden}. {direccion}"},
    )
    st.pydeck_chart(mapa, height=480)


def mostrar_aplicacion() -> None:
    with st.container(key="main_header"):
        with st.container(
            horizontal=True,
            horizontal_alignment="right",
            gap="xxsmall",
            key="logout_row",
        ):
            if st.button(
                "Cerrar sesión",
                icon=":material/logout:",
                key="cerrar_sesion",
                type="secondary",
            ):
                st.session_state.autenticado = False
                st.session_state.ruta = None
                st.session_state.nombre_autenticado = ""
                st.session_state.vista_acceso = "inicio"
                st.rerun()
        mostrar_marca()

    st.caption("Planifica y revisa el recorrido antes de iniciar la marcha.")
    with st.container(border=True):
        st.markdown("#### Seguridad al conducir")
        st.write(
            "Prepara la ruta estacionado. Coloca el teléfono en un soporte que no tape la vista "
            "ni los airbags y activa la navegación por voz antes de arrancar."
        )
        st.caption("No interactúes con la pantalla mientras el vehículo esté en movimiento.")

    st.header("1. Ingresa las direcciones")
    st.caption("Hazlo con el vehículo estacionado. Completa calle, ciudad y país para evitar confusiones.")
    with st.expander("Privacidad y uso de direcciones"):
        st.write(
            "Al calcular la ruta, las direcciones se envían a OpenStreetMap (Nominatim) y sus "
            "coordenadas a OSRM. Usa direcciones de prueba, no información sensible."
        )
    with st.form("formulario_ruta"):
        cantidad_direcciones = st.number_input(
            "Cantidad de direcciones (mínimo 5)",
            min_value=5,
            max_value=10,
            value=5,
            step=1,
        )
        direcciones = [
            st.text_input(
                f"Dirección de entrega {numero}",
                placeholder="Calle, ciudad y país",
                key=f"direccion_{numero}",
            )
            for numero in range(1, int(cantidad_direcciones) + 1)
        ]
        acepta_envio = st.checkbox("Entiendo y autorizo el envío de estas direcciones a los servicios de mapas.")
        enviar = st.form_submit_button("Calcular ruta", type="primary", use_container_width=True)

    if enviar:
        if not acepta_envio:
            st.error("Debes aceptar el envío a los servicios de mapas para calcular la ruta.")
        elif any(not direccion.strip() for direccion in direcciones):
            st.error("Completa las cinco direcciones antes de continuar.")
        else:
            try:
                with st.spinner("Buscando las direcciones y optimizando el recorrido..."):
                    lugares = [geocodificar_con_cache(direccion.strip()) for direccion in direcciones]
                    ruta = geo.calcular_ruta(lugares, direcciones)
                st.session_state.ruta = ruta
                st.success("Ruta calculada. El orden de las paradas está optimizado por OSRM.")
            except (ValueError, geo.ServicioMapasError) as error:
                st.error(f"No se pudo calcular la ruta: {error}")

    if st.session_state.ruta is None:
        st.info("Calcula la ruta antes de salir. Después podrás revisar el orden de las paradas.")
        return

    ruta = st.session_state.ruta
    estadisticas_ruta = extraer_estadisticas_ruta(ruta)

    historial, regresion, red, escalador, metricas, prueba = preparar_modelos()

    with st.expander("Ajustar estimación (opcional)", expanded=False):
        hora = st.slider("Hora de salida", min_value=6, max_value=22, value=9)
        trafico = st.slider(
            "Nivel de tráfico esperado",
            min_value=0.6,
            max_value=1.8,
            value=1.0,
            step=0.1,
        )
    caracteristicas = pd.DataFrame(
        [
            {
                "distancia_km": estadisticas_ruta["distancia_km"],
                "promedio_tramo_km": estadisticas_ruta["promedio_tramo_km"],
                "variacion_tramo_km": estadisticas_ruta["variacion_tramo_km"],
                "dispersion_km": estadisticas_ruta["dispersion_km"],
                "cantidad_paradas": estadisticas_ruta["cantidad_paradas"],
                "hora_salida": hora,
                "nivel_trafico": trafico,
            }
        ]
    )
    prediccion_lineal = float(regresion.predict(caracteristicas[["distancia_km"]])[0])
    prediccion_red = float(
        red.predict(escalador.transform(caracteristicas[modelo.CARACTERISTICAS]), verbose=0)[0, 0]
    )

    distancia_entrenamiento = historial["distancia_km"]
    distancia_fuera_de_rango = not (
        distancia_entrenamiento.min() <= ruta["distancia_km"] <= distancia_entrenamiento.max()
    )

    tab_conductor, tab_informe = st.tabs(["Ruta del conductor", "Análisis del proyecto"])
    with tab_conductor:
        st.header("2. Ruta y paradas")
        st.caption(
            "Revisa todo con el vehículo estacionado. Si vas a conducir, usa navegación por voz "
            "y no manipules la pantalla."
        )
        mostrar_mapa(ruta)

        resumen = st.columns(2)
        resumen[0].metric("Distancia total", f"{ruta['distancia_km']:.1f} km")
        resumen[1].metric("Conducción estimada por el mapa", f"{ruta['duracion_osrm_min']:.0f} min")
        st.caption("La duración del mapa no necesariamente refleja el tráfico actual.")

        st.subheader("Orden recomendado")
        for parada in ruta["paradas"]:
            with st.container(border=True):
                st.markdown(f"**Parada {parada['orden']}**")
                st.write(parada["direccion"])
                parametros_url = urlencode(
                    {
                        "api": "1",
                        "destination": f"{parada['lat']},{parada['lon']}",
                        "travelmode": "driving",
                    }
                )
                st.link_button(
                    f"Abrir navegación a parada {parada['orden']}",
                    f"https://www.google.com/maps/dir/?{parametros_url}",
                    type="primary" if parada["orden"] == 1 else "secondary",
                    use_container_width=True,
                )
        st.caption(
            "Google Maps recibe la ubicación de la parada al abrir cada enlace. "
            "Detente en un lugar seguro antes de seleccionar una nueva parada."
        )

        with st.expander("Ver estadísticas del recorrido"):
            estadisticas = st.columns(2)
            estadisticas[0].metric(
                "Promedio entre paradas",
                f"{estadisticas_ruta['promedio_tramo_km']:.2f} km",
            )
            estadisticas[1].metric(
                "Variación entre tramos",
                f"{estadisticas_ruta['variacion_tramo_km']:.2f} km",
            )
            st.metric(
                "Dispersión geográfica",
                f"{estadisticas_ruta['dispersion_km']:.2f} km",
            )

        st.subheader("Estimación experimental de duración")
        pred_cols = st.columns(2)
        pred_cols[0].metric("Regresión lineal", f"{max(0, prediccion_lineal):.0f} min")
        pred_cols[1].metric("Red neuronal", f"{max(0, prediccion_red):.0f} min")
        if distancia_fuera_de_rango:
            st.warning(
                f"Esta ruta ({ruta['distancia_km']:.1f} km) queda fuera del rango "
                f"de entrenamiento ({distancia_entrenamiento.min():.1f}–"
                f"{distancia_entrenamiento.max():.1f} km). No confíes en la predicción; "
                "el tiempo del mapa es solo una referencia."
            )
        else:
            st.caption("Predicción académica con datos sintéticos, no es una promesa de llegada.")

    with tab_informe:
        st.header("Comparación de modelos")
        st.write(
            "El historial de este prototipo es sintético y reproducible; no corresponde a entregas "
            "reales. La regresión usa solo la distancia total; la red neuronal usa varias variables."
        )
        tabla_metricas = pd.DataFrame(
            [{"Modelo": nombre, **valores} for nombre, valores in metricas.items()]
        ).set_index("Modelo")
        st.subheader("Evaluación con datos de prueba")
        st.dataframe(tabla_metricas.round(3), use_container_width=True)
        mejor = min(metricas, key=lambda nombre: metricas[nombre]["RMSE (min)"])
        st.success(
            f"En este conjunto sintético, el menor RMSE lo obtuvo **{mejor}**. "
            "Para producción hay que repetir la evaluación con tiempos reales de reparto."
        )

        # Ambos modelos usan las mismas rutas de prueba; la diagonal marca una predicción perfecta.
        figura, ejes = plt.subplots(figsize=(8, 5))
        ejes.scatter(prueba["real"], prueba["regresion_lineal"], alpha=0.55, label="Regresión lineal")
        ejes.scatter(prueba["real"], prueba["red_neuronal"], alpha=0.55, label="Red neuronal")
        minimo = min(prueba["real"].min(), prueba["regresion_lineal"].min(), prueba["red_neuronal"].min())
        maximo = max(prueba["real"].max(), prueba["regresion_lineal"].max(), prueba["red_neuronal"].max())
        ejes.plot([minimo, maximo], [minimo, maximo], "k--", label="Predicción perfecta")
        ejes.set(
            xlabel="Tiempo real simulado (minutos)",
            ylabel="Tiempo predicho (minutos)",
            title="Predicciones en el conjunto de prueba",
        )
        ejes.legend()
        ejes.grid(alpha=0.2)
        st.pyplot(figura)
        plt.close(figura)

        st.download_button(
            "Descargar historial sintético CSV",
            data=historial.to_csv(index=False).encode("utf-8"),
            file_name="historial_sintetico_rutas.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption(
            "MSE: promedio del error al cuadrado. RMSE: error típico en minutos; menor es mejor. "
            "R²: proporción de variación explicada; más cerca de 1 suele ser mejor. "
            "Un R² puede ser negativo si el modelo predice peor que usar el promedio."
        )


if st.session_state.autenticado:
    mostrar_aplicacion()
else:
    autenticar()

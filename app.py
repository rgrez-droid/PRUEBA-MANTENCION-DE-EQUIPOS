import base64
import glob
import importlib
import os
import re
from datetime import datetime
from io import BytesIO
from urllib.request import Request, urlopen

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Carga dinámica para evitar el aviso de Pylance cuando el entorno local
# todavía no tiene instalada la dependencia. En Streamlit Cloud se instala
# desde requirements.txt y la actualización automática sigue funcionando.
try:
    st_autorefresh = getattr(
        importlib.import_module("streamlit_autorefresh"),
        "st_autorefresh",
    )
except (ImportError, AttributeError):
    st_autorefresh = None


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Seguimiento y Control de Equipos Móviles",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# ESTABILIZACIÓN VISUAL DE ARRANQUE
# - Aplica desde el primer render las medidas finales del layout.
# - Evita el "salto" visual que antes ocurría mientras se cargaban
#   los overrides CSS ubicados más abajo en el archivo.
# =========================================================
st.markdown(
    """
<style>
/* Variables finales bloqueadas desde el primer frame. La mayor especificidad
   de html:root evita que overrides antiguos vuelvan a ensanchar el menú. */
html:root {
    --menu-panel-width: 230px !important;
    --menu-inner-width: 204px !important;
    --menu-panel-width-final: 230px !important;
    --menu-inner-width-final: 204px !important;
    --sidebar-compact-width: 230px !important;
    --sidebar-compact-inner: 204px !important;
    --sidebar-final-width: 230px !important;
    --sidebar-final-inner: 204px !important;
    --main-edge-gap: 16px !important;
    --content-padding-x: 16px !important;
}

/* No animar anchos/posiciones durante el arranque. */
html body section[data-testid="stSidebar"],
html body section[data-testid="stSidebar"] *,
html body section[data-testid="stMain"],
html body div[data-testid="stMain"] {
    transition: none !important;
}

@media screen and (min-width: 1101px) {
    /* Sidebar: geometría definitiva desde el primer render. */
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] {
        position: fixed !important;
        inset: 0 auto 0 0 !important;
        width: 230px !important;
        min-width: 230px !important;
        max-width: 230px !important;
        height: 100vh !important;
        max-height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
        overflow-y: hidden !important;
        z-index: 10000 !important;
    }

    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] > div,
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        width: 230px !important;
        min-width: 230px !important;
        max-width: 230px !important;
        height: 100vh !important;
        max-height: 100vh !important;
        margin: 0 !important;
        padding: 12px 13px 18px 13px !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    /* Cabecera del menú y espacio previo a los botones, iguales al estado final. */
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] .menu-panel-content {
        position: fixed !important;
        top: 12px !important;
        left: 17px !important;
        right: auto !important;
        width: 204px !important;
        min-width: 204px !important;
        max-width: 204px !important;
        margin: 0 !important;
        padding: 0 !important;
        transform: none !important;
        z-index: 10020 !important;
    }

    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] .menu-top-gap {
        display: block !important;
        height: 118px !important;
        min-height: 118px !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Navegación compacta desde el inicio. */
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] .menu-brand,
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] .menu-line,
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] div[data-testid="stButton"],
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] .menu-active-item {
        width: 204px !important;
        min-width: 204px !important;
        max-width: 204px !important;
        box-sizing: border-box !important;
    }

    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    html body [data-testid="stAppViewContainer"] section[data-testid="stSidebar"] .menu-active-item {
        min-height: 43px !important;
        height: 43px !important;
        padding: 8px 9px !important;
        font-size: 13.2px !important;
        line-height: 1.18 !important;
        border-radius: 12px !important;
        white-space: nowrap !important;
    }

    /* Área principal: reserva el sidebar desde el primer frame. */
    html body [data-testid="stAppViewContainer"] section[data-testid="stMain"],
    html body [data-testid="stAppViewContainer"] div[data-testid="stMain"] {
        margin: 0 !important;
        padding-left: 230px !important;
        width: 100vw !important;
        min-width: 0 !important;
        max-width: 100vw !important;
        box-sizing: border-box !important;
        position: relative !important;
        left: 0 !important;
        transform: none !important;
        overflow-x: hidden !important;
    }

    html body [data-testid="stAppViewContainer"] div[data-testid="stMainBlockContainer"],
    html body [data-testid="stAppViewContainer"] section[data-testid="stMain"] div[data-testid="stMainBlockContainer"],
    html body [data-testid="stAppViewContainer"] section[data-testid="stMain"] .block-container,
    html body [data-testid="stAppViewContainer"] div[data-testid="stMain"] .block-container {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        margin-top: -62px !important;
        padding-top: 0 !important;
        padding-left: 16px !important;
        padding-right: 16px !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    /* Cabecera principal estable desde el primer render. */
    html body .main-fixed-header {
        min-height: 58px !important;
        height: 58px !important;
        margin-top: 0 !important;
        margin-bottom: 12px !important;
        padding-top: 8px !important;
        align-items: flex-end !important;
    }

    html body .main-fixed-title,
    html body .title-main {
        font-size: clamp(28px, 2.1vw, 37px) !important;
        line-height: 1.03 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    html body .main-fixed-logo img,
    html body .header-logo-box img {
        width: 116px !important;
        max-width: 116px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)

# Actualización automática de la aplicación cada 60 segundos.
# El caché de Google Sheets dura 45 s, por lo que cada rerun automático
# vuelve a consultar la planilla y refleja los cambios sin intervención manual.
if st_autorefresh is not None:
    st_autorefresh(interval=60 * 1000, key="google_sheets_auto_refresh")


# =========================================================
# FUENTES DE DATOS
# =========================================================
# Google Sheets es la fuente oficial de datos de la aplicación.
# EQUIPOS, MANTENCIONES y los demás módulos se consultan directamente desde
# la planilla online para que Streamlit refleje los cambios automáticamente.

GOOGLE_SHEET_ID = "193LPwD1mAsg9-L54q68IU6Y2pzJWygvivYkZxtoiJsE"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit"

ARCHIVO_EQUIPOS_BASE = "Plantilla_Control_Equipos_Moviles_Contrato_Mulchen"
CARPETAS_EXCEL_EQUIPOS = [".", "datos", "data", "archivos", "excel"]

HOJAS_GOOGLE_SHEETS = [
    "EQUIPOS",
    "MANTENCIONES",
    "GASTOS_ADICIONALES",
    "CHECKLIST",
    "COMBUSTIBLE",
    "DOCUMENTOS",
]

# Tiempo de actualización automática de datos desde Google Sheets.
# 60 segundos permite que la app se actualice sin tener que subir archivos a GitHub.
CACHE_GOOGLE_SHEETS_SEGUNDOS = 55

LOGO_SUPERIOR = "logo1.png"

AUTOR = "Ricardo Grez"
EMPRESA = "SAIVAM"
CONTRATO = "CMPC Mulchén"
CLIENTE = "CMPC"
VERSION = "2.9"

MESES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

COLOR_TEXTO = "#0f172a"
COLOR_GRIS = "#64748b"

CARPETAS_IMAGENES = [
    ".",
    "fotos",
    "imagenes",
    "images",
    "equipos",
    "assets",
    "img",
]

EXTENSIONES_IMAGEN = [
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".PNG",
    ".JPG",
    ".JPEG",
    ".WEBP",
]


# =========================================================
# MAPEO DE EQUIPOS A IMÁGENES
# =========================================================

MAPEO_EXACTO_EQUIPOS = {
    "camion_ford_cargo": "camion_ford",
    "camion_ford": "camion_ford",
    "ford_cargo": "camion_ford",
    "carro_de_arrastre": "carro_arrastre",
    "carro_arrastre": "carro_arrastre",
    "minicargador": "minicargador",
    "mini_cargador": "minicargador",
    "barredora_tennant_s30": "barredora",
    "barredora": "barredora",
    "tennant_s30": "barredora",
    "camioneta_mitsubishi": "camioneta",
    "camioneta": "camioneta",
    "mitsubishi": "camioneta",
    "alza_hombre": "alza_hombre",
    "alzahombre": "alza_hombre",
    "grua_horquilla": "grua_orquilla",
    "grua_orquilla": "grua_orquilla",
    "horquilla": "grua_orquilla",
    "orquilla": "grua_orquilla",
    "montacarga": "grua_orquilla",
    "montacargas": "grua_orquilla",
}

MAPEO_ID_EQUIPO_IMAGEN = {
    "EQ-001": "camion_ford",
    "EQ001": "camion_ford",
    "EQ-002": "carro_arrastre",
    "EQ002": "carro_arrastre",
    "EQ-003": "minicargador",
    "EQ003": "minicargador",
    "EQ-004": "barredora",
    "EQ004": "barredora",
    "EQ-005": "camioneta",
    "EQ005": "camioneta",
    "EQ-006": "alza_hombre",
    "EQ006": "alza_hombre",
    "EQ-007": "grua_orquilla",
    "EQ007": "grua_orquilla",
}


# =========================================================
# UTILIDADES
# =========================================================

def archivo_a_base64(ruta):
    if not ruta or not os.path.exists(ruta):
        return ""

    with open(ruta, "rb") as archivo:
        return base64.b64encode(archivo.read()).decode("utf-8")


def extension_mime(ruta):
    ext = os.path.splitext(ruta)[1].lower()

    if ext in [".jpg", ".jpeg"]:
        return "image/jpeg"

    if ext == ".webp":
        return "image/webp"

    return "image/png"


def normalizar_texto(texto):
    texto = str(texto).lower().strip()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
        "ü": "u",
    }

    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)

    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    texto = re.sub(r"_+", "_", texto).strip("_")
    return texto


def normalizar_id_equipo(texto):
    return str(texto).upper().strip().replace(" ", "")


def escape_html(texto):
    texto = str(texto)
    texto = texto.replace("&", "&amp;")
    texto = texto.replace("<", "&lt;")
    texto = texto.replace(">", "&gt;")
    texto = texto.replace('"', "&quot;")
    texto = texto.replace("'", "&#39;")
    return texto


def listar_imagenes_disponibles():
    imagenes = []

    for carpeta in CARPETAS_IMAGENES:
        if not os.path.exists(carpeta):
            continue

        for extension in EXTENSIONES_IMAGEN:
            imagenes.extend(glob.glob(os.path.join(carpeta, f"*{extension}")))

    return imagenes


def buscar_imagen_por_nombre(nombre_base):
    if not nombre_base or str(nombre_base).strip().lower() in ["", "nan", "none"]:
        return None

    nombre_base = str(nombre_base).strip()
    nombre_norm = normalizar_texto(nombre_base)

    if os.path.exists(nombre_base):
        return nombre_base

    posibles_nombres = list(
        dict.fromkeys(
            [
                nombre_base,
                nombre_norm,
                nombre_base.replace(" ", "_"),
                nombre_base.replace(" ", "-"),
                nombre_norm.replace("_", "-"),
            ]
        )
    )

    for carpeta in CARPETAS_IMAGENES:
        for nombre in posibles_nombres:
            for extension in EXTENSIONES_IMAGEN:
                ruta = os.path.join(carpeta, nombre + extension)
                if os.path.exists(ruta):
                    return ruta

    imagenes = listar_imagenes_disponibles()

    for ruta in imagenes:
        base_archivo = os.path.splitext(os.path.basename(ruta))[0]
        base_norm = normalizar_texto(base_archivo)

        if nombre_norm == base_norm:
            return ruta

    for ruta in imagenes:
        base_archivo = os.path.splitext(os.path.basename(ruta))[0]
        base_norm = normalizar_texto(base_archivo)

        if nombre_norm in base_norm or base_norm in nombre_norm:
            return ruta

    return None


def buscar_imagen_equipo(fila):
    equipo = str(fila.get("Equipo", "")).strip()
    id_equipo = str(fila.get("ID_Equipo", "")).strip()
    tipo_equipo = str(fila.get("Tipo_Equipo", "")).strip()
    patente_codigo = str(fila.get("Patente_Codigo", "")).strip()
    marca = str(fila.get("Marca", "")).strip()
    modelo = str(fila.get("Modelo", "")).strip()
    imagen_excel = str(fila.get("Imagen", "")).strip()

    candidatos = []

    id_normal = normalizar_id_equipo(id_equipo)
    id_sin_guion = id_normal.replace("-", "")

    if id_normal in MAPEO_ID_EQUIPO_IMAGEN:
        candidatos.append(MAPEO_ID_EQUIPO_IMAGEN[id_normal])

    if id_sin_guion in MAPEO_ID_EQUIPO_IMAGEN:
        candidatos.append(MAPEO_ID_EQUIPO_IMAGEN[id_sin_guion])

    if imagen_excel and imagen_excel.lower() not in ["nan", "none", ""]:
        candidatos.append(imagen_excel)
        candidatos.append(normalizar_texto(imagen_excel))

    texto_equipo = " ".join(
        [
            equipo,
            tipo_equipo,
            patente_codigo,
            marca,
            modelo,
        ]
    )

    texto_norm = normalizar_texto(texto_equipo)
    equipo_norm = normalizar_texto(equipo)
    tipo_norm = normalizar_texto(tipo_equipo)

    for valor in [texto_norm, equipo_norm, tipo_norm]:
        if valor in MAPEO_EXACTO_EQUIPOS:
            candidatos.append(MAPEO_EXACTO_EQUIPOS[valor])

    if "grua" in texto_norm or "horquilla" in texto_norm or "orquilla" in texto_norm:
        candidatos.insert(0, "grua_orquilla")

    if "camioneta" in texto_norm or "mitsubishi" in texto_norm:
        candidatos.insert(0, "camioneta")

    if "camion" in texto_norm and "ford" in texto_norm:
        candidatos.insert(0, "camion_ford")

    if "ford_cargo" in texto_norm:
        candidatos.insert(0, "camion_ford")

    if "carro" in texto_norm and "arrastre" in texto_norm:
        candidatos.insert(0, "carro_arrastre")

    if "minicargador" in texto_norm or "mini_cargador" in texto_norm:
        candidatos.insert(0, "minicargador")

    if "barredora" in texto_norm or "tennant" in texto_norm:
        candidatos.insert(0, "barredora")

    if "alza" in texto_norm and "hombre" in texto_norm:
        candidatos.insert(0, "alza_hombre")

    candidatos.extend(
        [
            id_equipo,
            equipo,
            tipo_equipo,
            patente_codigo,
            marca,
            modelo,
            texto_equipo,
        ]
    )

    candidatos = list(dict.fromkeys([c for c in candidatos if str(c).strip() != ""]))

    for candidato in candidatos:
        ruta = buscar_imagen_por_nombre(candidato)
        if ruta:
            return ruta

    return None


def imagen_equipo_src(fila):
    ruta = buscar_imagen_equipo(fila)

    if not ruta:
        return ""

    imagen_b64 = archivo_a_base64(ruta)
    mime = extension_mime(ruta)

    if not imagen_b64:
        return ""

    return f"data:{mime};base64,{imagen_b64}"


@st.cache_data(ttl=CACHE_GOOGLE_SHEETS_SEGUNDOS, show_spinner=False)
@st.cache_data(ttl=CACHE_GOOGLE_SHEETS_SEGUNDOS, show_spinner=False)
def descargar_google_sheet_xlsx():
    """Descarga una sola copia XLSX completa del Google Sheets por ciclo de caché.

    Se usa el XLSX en vez del endpoint GViz/CSV porque los filtros visuales
    aplicados directamente en Google Sheets pueden ocultar filas también para
    GViz. Pandas lee todas las filas del XLSX, incluso si en Google Sheets están
    ocultas por un filtro. Así la app solo se filtra con sus propios controles.
    """
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=xlsx"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as respuesta:
        contenido = respuesta.read()

    if not contenido:
        raise FileNotFoundError("Google Sheets devolvió un archivo vacío.")

    return contenido


def leer_hoja_google_sheet(nombre_hoja):
    """Lee una pestaña desde la copia XLSX completa del Google Sheets.

    Esta lectura ignora filtros/filas ocultas de la interfaz de Google Sheets,
    pero sigue incorporando cambios reales de datos cuando se refresca el caché.
    """
    try:
        contenido = descargar_google_sheet_xlsx()
        df = pd.read_excel(
            BytesIO(contenido),
            sheet_name=str(nombre_hoja),
            engine="openpyxl",
        )
    except Exception:
        return pd.DataFrame()

    # Elimina columnas automáticas sin nombre y filas completamente vacías.
    df = df.loc[:, ~df.columns.astype(str).str.contains(r"^Unnamed", case=False, regex=True)]
    df = df.dropna(how="all")

    if not df.empty:
        # No concatenar la fila con ``"".join``: en algunas combinaciones de
        # pandas/openpyxl pueden conservarse valores numéricos y provocar
        # ``TypeError: expected str instance, float found``.
        # Esta máscara solo comprueba si existe al menos una celda con contenido.
        texto_df = df.fillna("").astype(str)
        mascara_con_datos = texto_df.apply(lambda col: col.str.strip().ne("")).any(axis=1)
        df = df.loc[mascara_con_datos].copy()

    return normalizar_columnas_dataframe(df)


def limpiar_numero(valor):
    if pd.isna(valor):
        return 0.0

    # Si Excel trae un monto mal formateado como fecha, se recupera el número serial.
    # Ejemplo: una celda con 42000 formateada como fecha aparece como 27-12-2014.
    if isinstance(valor, (pd.Timestamp, datetime)):
        try:
            return float((pd.to_datetime(valor) - pd.Timestamp("1899-12-30")).days)
        except Exception:
            return 0.0

    if isinstance(valor, (int, float)):
        return float(valor)

    texto = re.sub(r"[^0-9,.-]", "", str(valor))

    if texto in ["", "-"]:
        return 0.0

    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")

    elif "." in texto and len(texto.split(".")[-1]) == 3:
        texto = texto.replace(".", "")

    try:
        return float(texto)
    except ValueError:
        return 0.0


def normalizar_columnas_dataframe(df):
    """Normaliza encabezados de Excel editados manualmente.
    Evita errores cuando una columna viene con espacios, saltos de línea,
    acentos o pequeñas variaciones de nombre.
    """
    if df is None or df.empty:
        return df

    alias = {
        "id_equipo": "ID_Equipo",
        "idequipo": "ID_Equipo",
        "id_mantencion": "ID_Mantencion",
        "idmantencion": "ID_Mantencion",
        "equipo": "Equipo",
        "patente": "Patente_Codigo",
        "patente_codigo": "Patente_Codigo",
        "patentecodigo": "Patente_Codigo",
        "tipo_de_vehiculo": "Tipo_Equipo",
        "tipodevehiculo": "Tipo_Equipo",
        "tipo_equipo": "Tipo_Equipo",
        "tipoequipo": "Tipo_Equipo",
        "marca": "Marca",
        "contrato": "Contrato",
        "modelo": "Modelo",
        "numero_de_chasis": "Numero_Chasis",
        "numerodechasis": "Numero_Chasis",
        "numero_chasis": "Numero_Chasis",
        "numerochasis": "Numero_Chasis",
        "permiso": "Permiso",
        "revision": "Revision",
        "revision_tecnica": "Revision",
        "revisiontecnica": "Revision",
        "acreditacion": "Acreditacion",
        "planta": "Planta",
        "detalle": "Detalle",
        "ano": "Año",
        "año": "Año",
        "estado": "Estado",
        "area": "Área",
        "responsable": "Responsable",
        "imagen": "Imagen",
        "fecha_ingreso": "Fecha_Ingreso",
        "fechaingreso": "Fecha_Ingreso",
        "km_horometro_actual": "Km_Horometro_Actual",
        "kmhorometroactual": "Km_Horometro_Actual",
        "km_horómetro_actual": "Km_Horometro_Actual",
        "unidad_control": "Unidad_Control",
        "unidadcontro": "Unidad_Control",
        "unidad_control_": "Unidad_Control",
        "frecuencia_mantencion": "Frecuencia_Mantencion",
        "frecuenciamantencion": "Frecuencia_Mantencion",
        "frecuencia_mantención": "Frecuencia_Mantencion",
        "proxima_mantencion": "Proxima_Mantencion",
        "proximamantencion": "Proxima_Mantencion",
        "proxima_mantencio": "Proxima_Mantencion",
        "proximamantencio": "Proxima_Mantencion",
        "proxima_mantención": "Proxima_Mantencion",
        "prox_mantencion": "Proxima_Mantencion",
        "proxima": "Proxima_Mantencion",
        "observacion": "Observacion",
        "observación": "Observacion",
        "fecha": "Fecha",
        "tipo_mantencion": "Tipo_Mantencion",
        "tipomantencion": "Tipo_Mantencion",
        "tipo_mantención": "Tipo_Mantencion",
        "mantencion": "Tipo_Mantencion",
        "mantención": "Tipo_Mantencion",
        "mantencion_tipo": "Tipo_Mantencion",
        "mantenciontipo": "Tipo_Mantencion",
        "categoria": "Categoria",
        "categoría": "Categoria",
        "proveedor": "Proveedor",
        "descripcion": "Descripcion",
        "descripción": "Descripcion",
        "estado_mantencion": "Estado_Mantencion",
        "estado_mantención": "Estado_Mantencion",
        "documento_respaldo": "Documento_Respaldo",
        "documentorespaldo": "Documento_Respaldo",
        "costo_clp": "Costo_CLP",
        "costoclp": "Costo_CLP",
        "costo": "Costo_CLP",
        "monto": "Costo_CLP",
        "valor": "Costo_CLP",
        "tipo_gasto": "Tipo_Gasto",
        "tipogasto": "Tipo_Gasto",
        "costo_total": "Costo_Total",
        "costototal": "Costo_Total",
        "litros": "Litros",
        "valor_unitario": "Valor_Unitario",
        "valorunitario": "Valor_Unitario",
    }

    nuevas = {}
    for col in df.columns:
        original = str(col).replace("\n", " ").replace("\r", " ").strip()
        clave = normalizar_texto(original).replace("_", "")
        clave_con_guion = normalizar_texto(original)
        nuevas[col] = alias.get(clave_con_guion, alias.get(clave, original))

    salida = df.rename(columns=nuevas)

    # Si el Excel trae columnas equivalentes duplicadas (por ejemplo Mantencion y Tipo_Mantencion),
    # se consolidan en una sola columna usando el primer dato válido de izquierda a derecha.
    if salida.columns.duplicated().any():
        consolidado = pd.DataFrame(index=salida.index)
        for columna in dict.fromkeys(salida.columns):
            bloque = salida.loc[:, salida.columns == columna]
            if bloque.shape[1] == 1:
                consolidado[columna] = bloque.iloc[:, 0]
            else:
                consolidado[columna] = bloque.bfill(axis=1).iloc[:, 0]
        salida = consolidado

    return salida

def convertir_fecha(valor):
    if pd.isna(valor):
        return pd.NaT

    if isinstance(valor, pd.Timestamp):
        return valor

    if isinstance(valor, datetime):
        return pd.Timestamp(valor)

    if isinstance(valor, (int, float)):
        try:
            return pd.to_datetime(
                valor,
                unit="D",
                origin="1899-12-30",
                errors="coerce",
            )
        except Exception:
            return pd.NaT

    return pd.to_datetime(valor, errors="coerce", dayfirst=True)


def pesos(valor):
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " $"
    except Exception:
        return "0 $"


def pesos_html(valor):
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " &#36;"
    except Exception:
        return "0 &#36;"


def numero(valor):
    try:
        return f"{float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "0"


def fecha_texto(valor):
    if pd.isna(valor):
        return ""

    try:
        return pd.to_datetime(valor).strftime("%d/%m/%Y")
    except Exception:
        return ""


def asegurar_columna(df, columna, valor_default=""):
    if columna not in df.columns:
        df[columna] = valor_default

    return df


def preparar_fecha_columnas(df, columnas):
    salida = df.copy()

    for columna in columnas:
        if columna in salida.columns:
            salida[columna] = salida[columna].apply(convertir_fecha)

    return salida


def preparar_periodo(df):
    salida = df.copy()

    if "Fecha" not in salida.columns:
        salida["Fecha"] = pd.NaT

    salida["Fecha"] = salida["Fecha"].apply(convertir_fecha)
    salida["Año"] = salida["Fecha"].dt.year
    salida["Mes_Numero"] = salida["Fecha"].dt.month
    salida["Mes"] = salida["Mes_Numero"].map(MESES)

    salida["Periodo"] = (
        salida["Mes"].fillna("Sin mes")
        + " "
        + salida["Año"].fillna(0).astype(int).astype(str)
    )

    return salida


def aplicar_filtro_periodo(df, filtro_equipo, filtro_anio, filtro_mes):
    salida = df.copy()

    if filtro_equipo != "Todos los equipos" and "Equipo" in salida.columns:
        salida = salida[salida["Equipo"] == filtro_equipo]

    if filtro_anio != "Todos" and "Año" in salida.columns:
        salida = salida[salida["Año"] == filtro_anio]

    if filtro_mes != "Todos" and "Mes" in salida.columns:
        salida = salida[salida["Mes"] == filtro_mes]

    return salida.copy()


def unidad_control_texto(unidad):
    texto = str(unidad).strip()
    if texto.lower() in ["", "nan", "none", "nat", "0"]:
        return "Km/Horómetro"
    texto_norm = normalizar_texto(texto)
    if "horo" in texto_norm or "hora" in texto_norm:
        return "Horómetro"
    if "km" in texto_norm or "kilo" in texto_norm or "odometro" in texto_norm or "odom" in texto_norm:
        return "Km"
    return texto


def unidad_control_por_equipo(equipo, unidad_actual="", tipo_equipo="", marca="", modelo=""):
    """Determina la unidad correcta para el análisis de próxima mantención.
    Regla operativa solicitada:
    - Camión Ford Cargo y camioneta: Km.
    - Minicargador, barredora, alza hombre y grúa horquilla: Horómetro.
    - Si no se identifica el equipo, respeta la unidad de Excel si viene informada.
    """
    texto = normalizar_texto(" ".join([str(equipo), str(tipo_equipo), str(marca), str(modelo)]))

    # Equipos controlados por horómetro.
    if (
        "minicargador" in texto
        or "mini_cargador" in texto
        or "barredora" in texto
        or "tennant" in texto
        or ("alza" in texto and "hombre" in texto)
        or "alzahombre" in texto
        or "grua" in texto
        or "horquilla" in texto
        or "orquilla" in texto
        or "montacarga" in texto
        or "montacargas" in texto
    ):
        return "Horómetro"

    # Equipos controlados por kilometraje.
    if "camioneta" in texto or "mitsubishi" in texto:
        return "Km"

    if "camion" in texto or "ford_cargo" in texto or "ford" in texto:
        return "Km"

    if "carro" in texto or "arrastre" in texto:
        return "Km"

    unidad_txt = unidad_control_texto(unidad_actual)
    return unidad_txt if unidad_txt != "Km/Horómetro" else "Km/Horómetro"


def aplicar_unidad_control_por_equipo(df):
    salida = df.copy()
    for col in ["Equipo", "Tipo_Equipo", "Marca", "Modelo", "Unidad_Control"]:
        if col not in salida.columns:
            salida[col] = ""

    salida["Unidad_Control"] = salida.apply(
        lambda x: unidad_control_por_equipo(
            x.get("Equipo", ""),
            x.get("Unidad_Control", ""),
            x.get("Tipo_Equipo", ""),
            x.get("Marca", ""),
            x.get("Modelo", ""),
        ),
        axis=1,
    )
    return salida


def prioridad_estado_control(estado):
    estado_norm = normalizar_texto(estado)
    if "vencida" in estado_norm or "vence_ahora" in estado_norm:
        return 0
    if "critica" in estado_norm:
        return 1
    if "proxima" in estado_norm:
        return 2
    if "sin_lectura" in estado_norm:
        return 3
    if "al_dia" in estado_norm:
        return 4
    return 5


def resumen_proximas_por_equipo(proximas):
    """Deja una sola próxima mantención por equipo para el resumen ejecutivo.
    Selecciona la más urgente de cada equipo y evita que alza hombre/barredora
    repitan filas, permitiendo que también aparezcan camión y camioneta.
    """
    if proximas is None or proximas.empty:
        return pd.DataFrame(columns=getattr(proximas, "columns", []))

    salida = aplicar_unidad_control_por_equipo(proximas)
    salida = enriquecer_estado_proximas(salida)
    salida["_prioridad"] = salida["Estado_Control"].apply(prioridad_estado_control)
    salida["_saldo_abs"] = salida["Saldo_Restante"].abs()
    salida = salida.sort_values(["_prioridad", "Saldo_Restante", "_saldo_abs", "Equipo"], ascending=[True, True, True, True])
    salida = salida.drop_duplicates(subset=["Equipo"], keep="first")
    salida = salida.sort_values(["_prioridad", "Saldo_Restante", "Equipo"], ascending=[True, True, True])
    return salida.drop(columns=["_prioridad", "_saldo_abs"], errors="ignore")


def formatear_valor_control(valor, unidad=""):
    valor_num = limpiar_numero(valor)
    if valor_num <= 0:
        return "Sin dato"
    unidad_txt = unidad_control_texto(unidad)
    return f"{numero(valor_num)} {unidad_txt}".strip()


def formatear_saldo_control(valor, unidad=""):
    """Formatea el saldo restante de próxima mantención.
    Si el equipo está pasado, muestra el valor negativo solicitado
    en vez de mostrar el valor absoluto.
    """
    valor_num = limpiar_numero(valor)
    unidad_txt = unidad_control_texto(unidad)

    if valor_num < 0:
        return f"-{numero(abs(valor_num))} {unidad_txt}".strip()

    if valor_num == 0:
        return f"0 {unidad_txt}".strip()

    return f"{numero(valor_num)} {unidad_txt}".strip()


def calcular_estado_proxima_mantencion(km_actual, proxima_mantencion, unidad=""):
    """Evalúa la próxima mantención por odómetro u horómetro.
    La barra representa el avance de uso: actual / próxima mantención.
    - Verde: saldo suficiente.
    - Naranjo: saldo bajo.
    - Rojo: vencida o crítica.
    """
    actual = limpiar_numero(km_actual)
    proxima = limpiar_numero(proxima_mantencion)
    unidad_txt = unidad_control_texto(unidad)

    if proxima <= 0:
        return 0, "Sin próxima mantención", "#94a3b8", "Sin dato", 0, "Sin dato"

    proxima_txt = f"{numero(proxima)} {unidad_txt}".strip()

    if actual <= 0:
        return 0, "Sin lectura actual", "#94a3b8", proxima_txt, proxima, "Sin lectura"

    restante = proxima - actual
    avance = max(0, min(100, (actual / proxima) * 100))
    porcentaje_restante = (restante / proxima) * 100 if proxima > 0 else 0

    if restante < 0:
        exceso = abs(restante)
        return 100, f"Vencida: excedida en {numero(exceso)} {unidad_txt}", "#ef4444", proxima_txt, restante, "Vencida"

    if restante == 0:
        return 100, "Vence en lectura actual", "#ef4444", proxima_txt, restante, "Vence ahora"

    if porcentaje_restante <= 5:
        return avance, f"Crítica: faltan {numero(restante)} {unidad_txt}", "#ef4444", proxima_txt, restante, "Crítica"

    if porcentaje_restante <= 15:
        return avance, f"Próxima: faltan {numero(restante)} {unidad_txt}", "#f97316", proxima_txt, restante, "Próxima"

    return avance, f"Al día: faltan {numero(restante)} {unidad_txt}", "#22c55e", proxima_txt, restante, "Al día"


def enriquecer_estado_proximas(df):
    salida = df.copy()
    for col in ["Km_Horometro_Actual", "Proxima_Mantencion"]:
        if col not in salida.columns:
            salida[col] = 0
        salida[col] = salida[col].apply(limpiar_numero)
    if "Unidad_Control" not in salida.columns:
        salida["Unidad_Control"] = ""

    resultados = salida.apply(
        lambda x: calcular_estado_proxima_mantencion(
            x.get("Km_Horometro_Actual", 0),
            x.get("Proxima_Mantencion", 0),
            x.get("Unidad_Control", ""),
        ),
        axis=1,
    )

    salida["Avance_%"] = [r[0] for r in resultados]
    salida["Estado_Control"] = [r[5] for r in resultados]
    salida["Saldo_Restante"] = [r[4] for r in resultados]
    salida["Texto_Estado"] = [r[1] for r in resultados]
    salida["Proxima_Texto"] = [r[3] for r in resultados]
    return salida


def construir_proximas_mantenciones(equipos, mantenciones):
    """Crea la base oficial de próximas mantenciones usando la hoja EQUIPOS.

    Regla aplicada:
    - La próxima mantención, lectura actual y unidad de control se toman desde la hoja EQUIPOS.
    - Proxima_Mantencion se interpreta como lectura objetivo de Km u Horómetro, no como fecha.
    - Mantenciones históricas NO se usan para definir la próxima mantención del resumen, porque pueden
      traer registros antiguos, duplicados o valores parciales que distorsionan el análisis.
    - La hoja MANTENCIONES solo se usa como respaldo descriptivo cuando falta categoría/descripción,
      pero nunca reemplaza el valor de Proxima_Mantencion informado en EQUIPOS.
    """
    columnas = [
        "Equipo",
        "Marca",
        "Modelo",
        "Patente_Codigo",
        "Km_Horometro_Actual",
        "Unidad_Control",
        "Frecuencia_Mantencion",
        "Categoria",
        "Tipo_Mantencion",
        "Descripcion",
        "Proxima_Mantencion",
        "Costo_CLP",
        "Observacion",
    ]

    if equipos is None or equipos.empty or "Equipo" not in equipos.columns:
        return pd.DataFrame(columns=columnas)

    # -----------------------------------------------------
    # Base principal: hoja EQUIPOS.
    # Aquí están los valores oficiales solicitados por el usuario:
    # Km_Horometro_Actual, Unidad_Control y Proxima_Mantencion.
    # -----------------------------------------------------
    salida = equipos.copy()

    for col in columnas:
        if col not in salida.columns:
            if col in ["Km_Horometro_Actual", "Proxima_Mantencion", "Costo_CLP"]:
                salida[col] = 0
            else:
                salida[col] = ""

    salida["Equipo"] = salida["Equipo"].fillna("").astype(str).str.strip()
    salida = salida[~salida["Equipo"].str.lower().isin(["", "none", "nan", "sin equipo"])].copy()

    salida["Km_Horometro_Actual"] = salida["Km_Horometro_Actual"].apply(limpiar_numero)
    salida["Proxima_Mantencion"] = salida["Proxima_Mantencion"].apply(limpiar_numero)
    salida["Costo_CLP"] = salida["Costo_CLP"].apply(limpiar_numero)

    # Solo se analizan equipos con próxima mantención numérica registrada en hoja EQUIPOS.
    salida = salida[salida["Proxima_Mantencion"] > 0].copy()

    if salida.empty:
        return pd.DataFrame(columns=columnas)

    # Normaliza unidad según regla operativa:
    # Camión/camioneta/carro = Km | Equipos con horómetro = Horómetro.
    salida = aplicar_unidad_control_por_equipo(salida)

    # Completa campos descriptivos desde la misma hoja EQUIPOS.
    salida["Categoria"] = salida["Categoria"].where(
        ~salida["Categoria"].fillna("").astype(str).str.strip().str.lower().isin(["", "none", "nan", "nat"]),
        salida["Frecuencia_Mantencion"],
    )
    salida["Tipo_Mantencion"] = salida["Tipo_Mantencion"].where(
        ~salida["Tipo_Mantencion"].fillna("").astype(str).str.strip().str.lower().isin(["", "none", "nan", "nat"]),
        salida["Frecuencia_Mantencion"],
    )
    salida["Descripcion"] = salida["Descripcion"].where(
        ~salida["Descripcion"].fillna("").astype(str).str.strip().str.lower().isin(["", "none", "nan", "nat"]),
        salida["Observacion"],
    )

    # Respaldo opcional desde hoja MANTENCIONES solo para texto/costo, no para próxima lectura.
    if mantenciones is not None and not mantenciones.empty and "Equipo" in mantenciones.columns:
        mt = mantenciones.copy()
        mt["Equipo"] = mt["Equipo"].fillna("").astype(str).str.strip()
        if "Fecha" in mt.columns:
            mt["Fecha"] = mt["Fecha"].apply(convertir_fecha)
            mt = mt.sort_values("Fecha", ascending=False)
        for col in ["Categoria", "Tipo_Mantencion", "Descripcion", "Costo_CLP", "Observacion"]:
            if col not in mt.columns:
                mt[col] = 0 if col == "Costo_CLP" else ""
        mt = mt.drop_duplicates(subset=["Equipo"], keep="first")[["Equipo", "Categoria", "Tipo_Mantencion", "Descripcion", "Costo_CLP", "Observacion"]]
        salida = salida.merge(mt, on="Equipo", how="left", suffixes=("", "_MT"))
        for col in ["Categoria", "Tipo_Mantencion", "Descripcion", "Observacion"]:
            col_mt = f"{col}_MT"
            if col_mt in salida.columns:
                actual = salida[col].fillna("").astype(str).str.strip()
                respaldo = salida[col_mt].fillna("").astype(str).str.strip()
                salida[col] = actual.where(~actual.str.lower().isin(["", "none", "nan", "nat"]), respaldo)
        if "Costo_CLP_MT" in salida.columns:
            costo_actual = salida["Costo_CLP"].apply(limpiar_numero)
            costo_mt = salida["Costo_CLP_MT"].apply(limpiar_numero)
            salida["Costo_CLP"] = costo_actual.where(costo_actual > 0, costo_mt)
        salida = salida.drop(columns=[c for c in salida.columns if c.endswith("_MT")], errors="ignore")

    salida = salida[columnas].copy()
    salida["Proxima_Mantencion"] = salida["Proxima_Mantencion"].apply(limpiar_numero)
    salida["Km_Horometro_Actual"] = salida["Km_Horometro_Actual"].apply(limpiar_numero)
    salida["Costo_CLP"] = salida["Costo_CLP"].apply(limpiar_numero)
    salida = aplicar_unidad_control_por_equipo(salida)
    salida = enriquecer_estado_proximas(salida)

    # Un solo análisis por equipo, siempre desde hoja EQUIPOS.
    salida["_prioridad"] = salida["Estado_Control"].apply(prioridad_estado_control)
    salida = salida.sort_values(["_prioridad", "Saldo_Restante", "Equipo"], ascending=[True, True, True])
    salida = salida.drop_duplicates(subset=["Equipo"], keep="first")
    salida = salida.drop(columns=["_prioridad"], errors="ignore")

    return salida

def ocultar_columnas_tecnicas(df):
    columnas_ocultar = [
        "ID_Equipo",
        "ID_Mantencion",
        "ID_Gasto",
        "ID_Registro",
        "Área",
        "Area",
        "Responsable",
        "Imagen",
        "Mes_Numero",
    ]
    return df.drop(columns=[c for c in columnas_ocultar if c in df.columns], errors="ignore")


def normalizar_tipo_mantencion(valor):
    """Normaliza mantenciones a solo dos familias operativas: Preventiva y Correctiva."""
    texto = str(valor).strip()

    if texto.lower() in ["", "nan", "none", "nat", "sin tipo", "0", "n/a", "na", "n.a", "no aplica"]:
        return "Sin tipo"

    texto_norm = normalizar_texto(texto)

    if "correct" in texto_norm:
        return "Correctiva"

    # Todo lo planificado, preventivo, predictivo o inspecciones se consolida como Preventiva.
    if (
        "prevent" in texto_norm
        or "predict" in texto_norm
        or "inspeccion" in texto_norm
        or "revision" in texto_norm
        or "mensual" in texto_norm
        or "250_horas" in texto_norm
        or "10_000" in texto_norm
    ):
        return "Preventiva"

    return texto.strip().capitalize()


def normalizar_tipo_gasto(valor):
    """Normaliza los tipos de gasto creados en Excel.
    Permite que Repuesto, Administrativo y Mantención Correctiva/Preventiva
    se usen correctamente en gráficos, filtros y consolidado de costos.
    """
    texto = str(valor).strip()

    if texto.lower() in ["", "nan", "none", "nat", "sin tipo", "0"]:
        return "Sin tipo"

    texto_norm = normalizar_texto(texto)

    if "combustible" in texto_norm or "diesel" in texto_norm or "petroleo" in texto_norm:
        return "Combustible"

    if "administr" in texto_norm or "permiso" in texto_norm or "circulacion" in texto_norm or "seguro" in texto_norm or "soap" in texto_norm or "revision_tecnica" in texto_norm or "rev_tecnica" in texto_norm:
        return "Administrativo"

    if "mantencion" in texto_norm or "mantenimiento" in texto_norm or "mant" in texto_norm:
        if "correct" in texto_norm:
            return "Mantención Correctiva"
        if "prevent" in texto_norm:
            return "Mantención Preventiva"
        if "predict" in texto_norm or "inspeccion" in texto_norm:
            return "Mantención Preventiva"
        return "Mantención"

    if "repuesto" in texto_norm or "filtro" in texto_norm or "manguera" in texto_norm or "neumatic" in texto_norm or "aceite" in texto_norm:
        return "Repuesto"

    return texto.strip().capitalize()


def es_combustible_tipo(tipo):
    return normalizar_tipo_gasto(tipo) == "Combustible"


def tipo_mantencion_desde_gasto(tipo_gasto, descripcion="", mantencion=""):
    """Devuelve Preventiva/Correctiva cuando un gasto adicional corresponde a mantención.
    Prioriza la columna Mantencion de la hoja Gastos/Repuestos. Así, un registro con
    Tipo_Gasto = Repuesto pero Mantencion = Correctiva se carga al consolidado Correctiva.
    """
    mant_directa = normalizar_tipo_mantencion(mantencion)
    if mant_directa in ["Preventiva", "Correctiva"]:
        return mant_directa

    texto = f"{tipo_gasto} {descripcion} {mantencion}"
    texto_norm = normalizar_texto(texto)

    if "combustible" in texto_norm or "diesel" in texto_norm or "petroleo" in texto_norm:
        return ""

    if "correct" in texto_norm:
        return "Correctiva"
    if "prevent" in texto_norm:
        return "Preventiva"
    if "predict" in texto_norm or "inspeccion" in texto_norm:
        return "Preventiva"

    return ""


def categoria_costo_gasto(tipo_gasto, descripcion="", mantencion=""):
    """Clasificación final para el consolidado de costos.
    - Si la hoja Gastos/Repuestos trae Mantencion = Preventiva/Correctiva,
      ese costo se suma a ese grupo, aunque Tipo_Gasto diga Repuesto.
    - Administrativo agrupa permisos de circulación, seguros, SOAP y revisión técnica.
    - Repuesto se mantiene separado solo si no está asociado a una mantención.
    """
    tipo_norm = normalizar_tipo_gasto(tipo_gasto)
    mant = tipo_mantencion_desde_gasto(tipo_norm, descripcion, mantencion)

    if mant:
        return mant

    if tipo_norm == "Administrativo":
        return "Administrativos"

    if tipo_norm == "Repuesto":
        return "Repuestos"

    if tipo_norm == "Combustible":
        return "Combustible"

    if tipo_norm in ["Sin tipo", ""]:
        return "Gastos adicionales"

    return tipo_norm


def gastos_no_combustible(gastos):
    if gastos is None or gastos.empty:
        return pd.DataFrame(columns=getattr(gastos, "columns", []))

    salida = gastos.copy()
    if "Tipo_Gasto" not in salida.columns:
        salida["Tipo_Gasto"] = "Sin tipo"

    salida["Tipo_Gasto"] = salida["Tipo_Gasto"].apply(normalizar_tipo_gasto)
    return salida[~salida["Tipo_Gasto"].apply(es_combustible_tipo)].copy()


def construir_consolidado_costos(mantenciones, gastos):
    """Construye el consolidado para gráficos de costos.
    Incluye mantenciones registradas en hoja MANTENCIONES y gastos adicionales
    clasificados desde Tipo_Gasto.
    """
    partes = []

    if mantenciones is not None and not mantenciones.empty and "Costo_CLP" in mantenciones.columns:
        mant = mantenciones.copy()
        if "Tipo_Mantencion" not in mant.columns:
            mant["Tipo_Mantencion"] = "Sin tipo"
        mant["Item"] = mant["Tipo_Mantencion"].apply(normalizar_tipo_mantencion)
        mant["Costo"] = mant["Costo_CLP"].apply(limpiar_numero)
        partes.append(mant[["Item", "Costo"]])

    if gastos is not None and not gastos.empty and "Costo_CLP" in gastos.columns:
        gas = gastos.copy()
        if "Tipo_Gasto" not in gas.columns:
            gas["Tipo_Gasto"] = "Sin tipo"
        if "Descripcion" not in gas.columns:
            gas["Descripcion"] = ""
        gas["Tipo_Gasto"] = gas["Tipo_Gasto"].apply(normalizar_tipo_gasto)
        gas["Item"] = gas.apply(lambda x: categoria_costo_gasto(x.get("Tipo_Gasto", ""), x.get("Descripcion", ""), x.get("Mantencion", "")), axis=1)
        gas["Costo"] = gas["Costo_CLP"].apply(limpiar_numero)
        gas = gas[gas["Item"] != "Combustible"].copy()
        partes.append(gas[["Item", "Costo"]])

    if not partes:
        return pd.DataFrame(columns=["Item", "Costo"])

    salida = pd.concat(partes, ignore_index=True)
    salida = salida[salida["Costo"] > 0].copy()

    if salida.empty:
        return pd.DataFrame(columns=["Item", "Costo"])

    orden = ["Preventiva", "Correctiva", "Mantención", "Repuestos", "Administrativos", "Gastos adicionales"]
    salida = salida.groupby("Item", as_index=False)["Costo"].sum()
    salida["_orden"] = salida["Item"].apply(lambda x: orden.index(x) if x in orden else len(orden))
    salida = salida.sort_values(["_orden", "Costo"], ascending=[True, False]).drop(columns=["_orden"])
    return salida

def preparar_tabla_mantenciones(mantenciones):
    mostrar = mantenciones.copy()

    if "Tipo_Mantencion" in mostrar.columns:
        mostrar["Mantencion"] = mostrar["Tipo_Mantencion"].apply(normalizar_tipo_mantencion)
    elif "Mantencion" in mostrar.columns:
        mostrar["Mantencion"] = mostrar["Mantencion"].apply(normalizar_tipo_mantencion)
    else:
        mostrar["Mantencion"] = "Sin tipo"

    if "Fecha" in mostrar.columns:
        mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)

    if "Costo_CLP" in mostrar.columns:
        mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)

    columnas_orden = [
        "Fecha",
        "Equipo",
        "Mantencion",
        "Categoria",
        "Proveedor",
        "Descripcion",
        "Costo_CLP",
        "Estado_Mantencion",
        "Documento_Respaldo",
        "Observacion",
        "Mes",
        "Año",
    ]

    columnas_orden = [c for c in columnas_orden if c in mostrar.columns]
    mostrar = mostrar[columnas_orden].copy()

    mostrar = mostrar.rename(
        columns={
            "Mantencion": "Mantención",
            "Categoria": "Categoría",
            "Descripcion": "Descripción",
            "Costo_CLP": "Costo",
            "Estado_Mantencion": "Estado",
            "Documento_Respaldo": "Documento respaldo",
            "Observacion": "Observación",
        }
    )

    return mostrar



def preparar_tabla_repuestos(gastos):
    mostrar = gastos.copy()

    # Elimina filas vacías que vienen desde el formato de Excel.
    if "Equipo" in mostrar.columns:
        equipo_txt = mostrar["Equipo"].fillna("").astype(str).str.strip().str.lower()
    else:
        equipo_txt = pd.Series([""] * len(mostrar), index=mostrar.index)

    if "Descripcion" in mostrar.columns:
        desc_txt = mostrar["Descripcion"].fillna("").astype(str).str.strip().str.lower()
    else:
        desc_txt = pd.Series([""] * len(mostrar), index=mostrar.index)

    costo_num = mostrar["Costo_CLP"].apply(limpiar_numero) if "Costo_CLP" in mostrar.columns else pd.Series([0] * len(mostrar), index=mostrar.index)
    mostrar = mostrar[(~equipo_txt.isin(["", "none", "nan"])) | (~desc_txt.isin(["", "none", "nan"])) | (costo_num > 0)].copy()

    if "Fecha" in mostrar.columns:
        mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)

    if "Costo_CLP" in mostrar.columns:
        mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)

    if "Clasificacion_Costo" not in mostrar.columns:
        mostrar["Clasificacion_Costo"] = mostrar.apply(
            lambda x: categoria_costo_gasto(x.get("Tipo_Gasto", ""), x.get("Descripcion", ""), x.get("Mantencion", "")),
            axis=1,
        )

    columnas_orden = [
        "Fecha",
        "Equipo",
        "Mantencion",
        "Tipo_Gasto",
        "Clasificacion_Costo",
        "Descripcion",
        "Proveedor",
        "Costo_CLP",
        "Documento_Respaldo",
        "Observacion",
        "Mes",
        "Año",
        "Periodo",
    ]

    columnas_orden = [c for c in columnas_orden if c in mostrar.columns]
    mostrar = mostrar[columnas_orden].copy()

    mostrar = mostrar.rename(
        columns={
            "Mantencion": "Mantención",
            "Tipo_Gasto": "Tipo gasto",
            "Clasificacion_Costo": "Consolidado",
            "Descripcion": "Descripción",
            "Costo_CLP": "Costo",
            "Documento_Respaldo": "Documento respaldo",
            "Observacion": "Observación",
        }
    )

    return mostrar


def preparar_tabla_proximas(proximas):
    mostrar = proximas.copy()
    mostrar = enriquecer_estado_proximas(mostrar)

    if "Km_Horometro_Actual" in mostrar.columns:
        mostrar["Km_Horometro_Actual"] = mostrar.apply(
            lambda x: formatear_valor_control(x.get("Km_Horometro_Actual", 0), x.get("Unidad_Control", "")),
            axis=1,
        )

    if "Saldo_Restante" in mostrar.columns:
        mostrar["Saldo_Restante"] = mostrar.apply(
            lambda x: formatear_saldo_control(x.get("Saldo_Restante", 0), x.get("Unidad_Control", "")),
            axis=1,
        )

    if "Costo_CLP" in mostrar.columns:
        mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)

    columnas_orden = [
        "Equipo",
        "Marca",
        "Modelo",
        "Patente_Codigo",
        "Km_Horometro_Actual",
        "Unidad_Control",
        "Frecuencia_Mantencion",
        "Categoria",
        "Tipo_Mantencion",
        "Descripcion",
        "Proxima_Mantencion",
        "Estado_Control",
        "Saldo_Restante",
        "Texto_Estado",
        "Costo_CLP",
        "Observacion",
    ]

    columnas_orden = [c for c in columnas_orden if c in mostrar.columns]
    mostrar = mostrar[columnas_orden].copy()

    mostrar = mostrar.rename(
        columns={
            "Patente_Codigo": "Patente / Código",
            "Km_Horometro_Actual": "Lectura actual",
            "Unidad_Control": "Unidad",
            "Frecuencia_Mantencion": "Frecuencia",
            "Categoria": "Categoría",
            "Tipo_Mantencion": "Mantención",
            "Descripcion": "Descripción",
            "Proxima_Mantencion": "Próxima mantención",
            "Estado_Control": "Estado",
            "Saldo_Restante": "Saldo restante",
            "Texto_Estado": "Análisis",
            "Costo_CLP": "Costo",
            "Observacion": "Observación",
        }
    )

    return mostrar

def estado_clase(estado):
    estado_norm = normalizar_texto(estado)

    if (
        "no_operativo" in estado_norm
        or "no_disponible" in estado_norm
        or "indisponible" in estado_norm
        or "inoperativo" in estado_norm
        or "fuera" in estado_norm
    ):
        return "estado-rojo"

    if "operativo" in estado_norm or "disponible" in estado_norm:
        return "estado-ok"

    if "mantencion" in estado_norm or "uso" in estado_norm:
        return "estado-alerta"

    return "estado-alerta"


# =========================================================
# ESTILO GENERAL
# =========================================================

def aplicar_estilo():
    st.markdown(
        """
<style>



/* =========================================================
   CORRECCIÓN 3.5: SIDEBAR FIJO, VISIBLE Y SIN DESORDEN
   ========================================================= */
:root {
    --menu-panel-width: 290px !important;
    --menu-inner-width: 260px !important;
}

section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    bottom: 0 !important;
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    height: 100vh !important;
    transform: translateX(0px) !important;
    background: #020617 !important;
    z-index: 9999 !important;
    border-right: 1px solid rgba(147, 197, 253, 0.34) !important;
    box-shadow: 10px 0 24px rgba(15, 23, 42, 0.32) !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    min-height: 100vh !important;
    background: #020617 !important;
    padding: 12px 14px 18px 14px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

[data-testid="stAppViewContainer"] > .main,
section.main,
main {
    margin-left: var(--menu-panel-width) !important;
    width: calc(100vw - var(--menu-panel-width)) !important;
    max-width: calc(100vw - var(--menu-panel-width)) !important;
}

.main .block-container,
.block-container {
    padding-top: 0rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    max-width: none !important;
    min-width: 1120px !important;
    overflow-x: visible !important;
}

[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[kind="header"],
header[data-testid="stHeader"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] .menu-brand {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    width: var(--menu-inner-width) !important;
    margin: 0 0 18px 0 !important;
}

section[data-testid="stSidebar"] .menu-icon {
    flex: 0 0 52px !important;
}

section[data-testid="stSidebar"] .menu-title,
section[data-testid="stSidebar"] .menu-title *,
section[data-testid="stSidebar"] .menu-subtitle,
section[data-testid="stSidebar"] .menu-subtitle * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: var(--menu-inner-width) !important;
    min-height: 48px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    border-radius: 13px !important;
    background: rgba(15, 23, 42, 0.72) !important;
    border: 1px solid rgba(147, 197, 253, 0.28) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 950 !important;
    margin-bottom: 7px !important;
    padding: 10px 12px !important;
    white-space: normal !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.85) !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background: rgba(37, 99, 235, 0.62) !important;
    border-color: rgba(191, 219, 254, 0.80) !important;
}

section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    box-sizing: border-box !important;
    padding: 12px 12px !important;
    border-radius: 13px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%) !important;
    border: 1px solid rgba(219, 234, 254, 0.95) !important;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.38) !important;
    font-size: 15.5px !important;
    font-weight: 950 !important;
    line-height: 1.25 !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.70) !important;
    margin-bottom: 7px !important;
    white-space: normal !important;
}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label,
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label * {
    color: #dbeafe !important;
    -webkit-text-fill-color: #dbeafe !important;
    opacity: 1 !important;
    font-weight: 950 !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #ffffff !important;
    border-radius: 12px !important;
    min-height: 44px !important;
    border: 1px solid rgba(255,255,255,0.45) !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    font-weight: 800 !important;
}

.title-main {
    white-space: nowrap !important;
    overflow: visible !important;
}

.kpi-card {
    min-width: 205px !important;
}

[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
}

[data-testid="stDataFrame"],
[data-testid="stPlotlyChart"] {
    max-width: 100% !important;
    overflow: hidden !important;
}

</style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<style>

header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stDeployButton"],
#MainMenu,
footer,
[data-testid="collapsedControl"],
button[kind="header"] {
    display: none !important;
    visibility: hidden !important;
    height: 0px !important;
    min-height: 0px !important;
    max-height: 0px !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

html,
body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
section.main,
main {
    background: #eef3f9 !important;
    color: #0f172a !important;
    padding-top: 0px !important;
    margin-top: 0px !important;
}

.main .block-container,
.block-container,
section.main > div {
    padding-top: 0rem !important;
    margin-top: 0rem !important;
    padding-bottom: 2rem !important;
    padding-left: 0rem !important;
    padding-right: 0.75rem !important;
    max-width: 100% !important;
}

div[data-testid="stVerticalBlock"] {
    gap: 0.45rem !important;
}

.stMarkdown h1 a,
.stMarkdown h2 a,
.stMarkdown h3 a {
    display: none !important;
    visibility: hidden !important;
}

/* =========================================================
   PANEL IZQUIERDO OSCURO COMPLETO
   ========================================================= */

.menu-marker {
    display: none;
}

/* Fondo fijo real del panel izquierdo completo */
.menu-bg {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 285px !important;
    height: 100vh !important;
    background: #020617 !important;
    z-index: 0 !important;
    border-right: 1px solid rgba(147, 197, 253, 0.28) !important;
    box-shadow: 10px 0 24px rgba(15, 23, 42, 0.35) !important;
}

/* Columna izquierda sobre el fondo oscuro */
div[data-testid="column"]:has(.menu-marker),
div[data-testid="column"]:has(.menu-brand),
div[data-testid="column"]:has(.menu-bg) {
    background: transparent !important;
    min-height: 100vh !important;
    height: 100vh !important;
    padding: 14px 12px 18px 12px !important;
    position: sticky !important;
    top: 0 !important;
    align-self: flex-start !important;
    z-index: 2 !important;
}

/* Todo el contenido interno del menú queda transparente */
div[data-testid="column"]:has(.menu-marker) > div,
div[data-testid="column"]:has(.menu-brand) > div,
div[data-testid="column"]:has(.menu-bg) > div,
div[data-testid="column"]:has(.menu-marker) div,
div[data-testid="column"]:has(.menu-brand) div,
div[data-testid="column"]:has(.menu-bg) div {
    background-color: transparent !important;
}

/* Contenido del menú encima del fondo */
.menu-panel-content,
.menu-brand,
.menu-line,
.menu-footer-box,
.menu-info {
    position: relative !important;
    z-index: 3 !important;
}

/* Encabezado del panel izquierdo */
.menu-brand {
    display: flex !important;
    align-items: center !important;
    gap: 11px !important;
    margin-top: 2px !important;
    margin-bottom: 18px !important;
    background: transparent !important;
}

.menu-icon {
    background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
    width: 52px !important;
    height: 52px !important;
    border-radius: 16px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 27px !important;
    box-shadow: 0 10px 24px rgba(37, 99, 235, 0.40) !important;
}

.menu-icon-img {
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    max-width: 44px !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    background: transparent !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: none !important;
    border: none !important;
}

.menu-icon-img img {
    width: 100% !important;
    height: 100% !important;
    object-fit: contain !important;
    display: block !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] .menu-icon-img {
    flex: 0 0 44px !important;
}

.menu-title {
    color: #ffffff !important;
    font-weight: 950 !important;
    font-size: 13.8px !important;
    line-height: 1.18 !important;
    letter-spacing: 0.45px !important;
    text-shadow: 0 2px 5px rgba(0,0,0,0.75) !important;
}

.menu-subtitle {
    color: #bfdbfe !important;
    font-size: 11.5px !important;
    margin-top: 5px !important;
    font-weight: 950 !important;
    letter-spacing: 0.30px !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.65) !important;
}

.menu-line {
    border: 0 !important;
    border-top: 1px solid rgba(191, 219, 254, 0.25) !important;
    margin: 14px 0 16px 0 !important;
}

/* Items del menú */
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"],
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] {
    gap: 0.32rem !important;
    background: transparent !important;
    position: relative !important;
    z-index: 3 !important;
}

div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label,
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label {
    background: transparent !important;
    border-radius: 12px !important;
    padding: 8px 10px !important;
    margin-bottom: 5px !important;
    min-height: 38px !important;
    border: 1px solid transparent !important;
}

div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label:hover,
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label:hover {
    background: rgba(37, 99, 235, 0.25) !important;
    border: 1px solid rgba(147, 197, 253, 0.40) !important;
}

div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label:has(input:checked),
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label:has(input:checked) {
    background: rgba(37, 99, 235, 0.35) !important;
    border: 1px solid rgba(147, 197, 253, 0.55) !important;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.28) !important;
}

div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label p,
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label p {
    color: #ffffff !important;
    font-size: 14px !important;
    line-height: 1.18 !important;
    font-weight: 850 !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.45) !important;
}



/* Refuerzo de legibilidad para textos del menú izquierdo */
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] *,
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] * {
    color: #ffffff !important;
    opacity: 1 !important;
    font-weight: 900 !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.75) !important;
}

div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label p,
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label span,
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label div,
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label p,
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label span,
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label div {
    color: #ffffff !important;
    opacity: 1 !important;
    font-size: 16px !important;
    font-weight: 900 !important;
    letter-spacing: 0.10px !important;
}

div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label:has(input:checked) p,
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label:has(input:checked) span,
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label:has(input:checked) div,
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label:has(input:checked) p,
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label:has(input:checked) span,
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label:has(input:checked) div {
    color: #ffffff !important;
    opacity: 1 !important;
    font-weight: 950 !important;
}

/* Texto Equipo, Año, Mes */
div[data-testid="column"]:has(.menu-marker) label,
div[data-testid="column"]:has(.menu-bg) label {
    color: #e0f2fe !important;
    font-weight: 900 !important;
    font-size: 13px !important;
}

/* Selectbox dentro del panel */
div[data-testid="column"]:has(.menu-marker) [data-baseweb="select"] > div,
div[data-testid="column"]:has(.menu-bg) [data-baseweb="select"] > div {
    background: #ffffff !important;
    border-radius: 12px !important;
    min-height: 42px !important;
    height: 42px !important;
    border: 1px solid rgba(255,255,255,0.45) !important;
}

div[data-testid="column"]:has(.menu-marker) [data-baseweb="select"] span,
div[data-testid="column"]:has(.menu-marker) [data-baseweb="select"] input,
div[data-testid="column"]:has(.menu-bg) [data-baseweb="select"] span,
div[data-testid="column"]:has(.menu-bg) [data-baseweb="select"] input {
    color: #0f172a !important;
    font-size: 13px !important;
}

/* Caja inferior */
.menu-footer-box {
    border: 1px solid rgba(147,197,253,0.35) !important;
    background: rgba(2, 6, 23, 0.96) !important;
    border-radius: 16px !important;
    padding: 13px !important;
    margin-top: 16px !important;
    box-shadow: 0 10px 20px rgba(0,0,0,0.40) !important;
    position: relative !important;
    z-index: 3 !important;
}

.menu-info {
    color: #ffffff !important;
    font-size: 12.5px !important;
    line-height: 1.68 !important;
    margin-top: 0px !important;
    font-weight: 850 !important;
}

.menu-info b {
    color: #93c5fd !important;
    font-weight: 950 !important;
}

/* =========================================================
   CONTENIDO PRINCIPAL
   ========================================================= */

.title-main {
    font-size: 42px;
    font-weight: 950;
    color: #0f172a;
    margin-top: 0px !important;
    margin-bottom: 0px !important;
    padding-top: 0px !important;
    padding-bottom: 0px !important;
    line-height: 1.05;
}

.header-logo-box {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
    text-align: right !important;
    margin-top: 0px !important;
}

.header-logo-box img {
    width: 170px !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

.header-separador {
    height: 20px;
}

.kpi-card {
    background: white;
    border: 1px solid #dbe3ef;
    border-radius: 20px;
    padding: 20px;
    min-height: 132px;
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.065);
}

.kpi-icon {
    width: 54px;
    height: 54px;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    margin-bottom: 12px;
}

.kpi-title {
    font-size: 13px;
    color: #475569;
    font-weight: 900;
}

.kpi-value {
    font-size: 26px;
    font-weight: 950;
    color: #0f172a;
    margin-top: 7px;
}

.kpi-sub {
    font-size: 12px;
    color: #64748b;
    margin-top: 7px;
}

.panel-title {
    color: #0f172a;
    font-weight: 950;
    font-size: 19px;
    margin-top: 20px;
    margin-bottom: 10px;
}

.next-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #e2e8f0;
    padding: 6px 0;
    min-height: 44px;
}

.next-title {
    font-weight: 950;
    color: #0f172a;
    font-size: 12px;
    line-height: 1.15;
}

.next-sub {
    color: #64748b;
    font-size: 10.5px;
    margin-top: 1px;
    line-height: 1.15;
}

.badge-days {
    background: #fff7ed;
    color: #f97316;
    border: 1px solid #fed7aa;
    padding: 4px 7px;
    border-radius: 999px;
    font-weight: 950;
    font-size: 10px;
    white-space: nowrap;
}

.equipo-card {
    background: #ffffff;
    border: 1px solid #dbe3ef;
    border-radius: 18px;
    padding: 13px;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
    min-height: 282px;
    box-sizing: border-box;
    overflow: hidden;
}

.equipo-img {
    width: 100%;
    height: 132px;
    object-fit: cover;
    border-radius: 14px;
    border: 1px solid #e2e8f0;
    margin-bottom: 10px;
    background: #f1f5f9;
    display: block;
}

.equipo-img-placeholder {
    width: 100%;
    height: 132px;
    border-radius: 14px;
    border: 1px dashed #cbd5e1;
    background: #f8fafc;
    color: #64748b;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 38px;
    margin-bottom: 10px;
    box-sizing: border-box;
}

.equipo-nombre {
    font-weight: 950;
    color: #0f172a;
    font-size: 16px;
    margin-bottom: 3px;
}

.equipo-sub {
    color: #64748b;
    font-size: 13px;
    margin-top: 4px;
    line-height: 1.25;
}

.estado-ok {
    color: #22c55e;
    font-size: 12px;
    font-weight: 950;
    margin-top: 8px;
}

.estado-alerta {
    color: #f59e0b;
    font-size: 12px;
    font-weight: 950;
    margin-top: 8px;
}

.estado-rojo {
    color: #ef4444;
    font-size: 12px;
    font-weight: 950;
    margin-top: 8px;
}

.progress-bg {
    width: 100%;
    height: 7px;
    background: #e2e8f0;
    border-radius: 999px;
    margin-top: 9px;
    overflow: hidden;
}

.progress-fill {
    height: 7px;
    border-radius: 999px;
    background-color: var(--barra-color, #94a3b8) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid #dbe3ef;
    border-radius: 13px;
    overflow: hidden;
}

/* Selectbox global */
div[data-baseweb="select"] > div {
    background: white !important;
    border: 1px solid #dbe3ef !important;
    border-radius: 12px !important;
    min-height: 44px !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] input {
    color: #0f172a !important;
}

label {
    color: #334155 !important;
    font-weight: 850 !important;
}

.stButton button {
    border-radius: 11px !important;
    font-weight: 850 !important;
    min-height: 44px !important;
}


/* =========================================================
   AJUSTE FINAL: MENÚ IZQUIERDO MÁS LEGIBLE
   ========================================================= */

/* Fuerza los textos del menú a blanco, aunque Streamlit aplique estilos internos */
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label,
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label *,
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label,
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label * {
    color: #ffffff !important;
    opacity: 1 !important;
    font-weight: 900 !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.75) !important;
}

/* Opción seleccionada con fondo azul para que destaque */
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] label:has(input:checked),
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] label:has(input:checked) {
    background: rgba(37, 99, 235, 0.45) !important;
    border: 1px solid rgba(147, 197, 253, 0.65) !important;
}

/* Radio button más visible */
div[data-testid="column"]:has(.menu-bg) div[role="radiogroup"] input,
div[data-testid="column"]:has(.menu-marker) div[role="radiogroup"] input {
    accent-color: #38bdf8 !important;
}

/* Títulos de filtros Equipo / Año / Mes */
div[data-testid="column"]:has(.menu-bg) label,
div[data-testid="column"]:has(.menu-bg) label *,
div[data-testid="column"]:has(.menu-marker) label,
div[data-testid="column"]:has(.menu-marker) label * {
    color: #e0f2fe !important;
    opacity: 1 !important;
    font-weight: 900 !important;
}


/* =========================================================
   CORRECCIÓN FINAL: TEXTO DEL MENÚ IZQUIERDO 100% LEGIBLE
   Streamlit a veces aplica opacidad/color interno a los radios.
   Este bloque fuerza blanco real en menú, filtros y estados.
   ========================================================= */

/* Radio menú: texto, emojis y contenedores internos */
div[data-testid="column"]:has(.menu-bg) div[data-testid="stRadio"],
div[data-testid="column"]:has(.menu-bg) div[data-testid="stRadio"] *,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stRadio"],
div[data-testid="column"]:has(.menu-marker) div[data-testid="stRadio"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
    filter: none !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.65) !important;
}

/* Cada opción del menú */
div[data-testid="column"]:has(.menu-bg) div[data-testid="stRadio"] label,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stRadio"] label {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
    font-weight: 950 !important;
    font-size: 15px !important;
    line-height: 1.25 !important;
}

/* Texto específico dentro de cada opción */
div[data-testid="column"]:has(.menu-bg) div[data-testid="stRadio"] label p,
div[data-testid="column"]:has(.menu-bg) div[data-testid="stRadio"] label span,
div[data-testid="column"]:has(.menu-bg) div[data-testid="stRadio"] label div,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stRadio"] label p,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stRadio"] label span,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stRadio"] label div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
    font-weight: 950 !important;
    font-size: 15px !important;
}

/* Opción seleccionada más marcada */
div[data-testid="column"]:has(.menu-bg) div[data-testid="stRadio"] label:has(input:checked),
div[data-testid="column"]:has(.menu-marker) div[data-testid="stRadio"] label:has(input:checked) {
    background: rgba(37, 99, 235, 0.42) !important;
    border: 1px solid rgba(147, 197, 253, 0.65) !important;
}

/* Etiquetas de filtros: Equipo, Año y Mes */
div[data-testid="column"]:has(.menu-bg) div[data-testid="stSelectbox"] label,
div[data-testid="column"]:has(.menu-bg) div[data-testid="stSelectbox"] label *,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stSelectbox"] label,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stSelectbox"] label * {
    color: #dbeafe !important;
    -webkit-text-fill-color: #dbeafe !important;
    opacity: 1 !important;
    font-weight: 950 !important;
    font-size: 13.5px !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.55) !important;
}

/* Texto dentro de los filtros desplegables */
div[data-testid="column"]:has(.menu-bg) [data-baseweb="select"] *,
div[data-testid="column"]:has(.menu-marker) [data-baseweb="select"] * {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    opacity: 1 !important;
    font-weight: 800 !important;
}



/* =========================================================
   MENÚ HTML PERSONALIZADO - LETRAS BLANCAS Y LEGIBLES
   ========================================================= */

.menu-nav {
    display: flex !important;
    flex-direction: column !important;
    gap: 7px !important;
    margin-top: 6px !important;
    margin-bottom: 12px !important;
    position: relative !important;
    z-index: 20 !important;
}

.menu-nav-item,
.menu-nav-item:link,
.menu-nav-item:visited {
    display: block !important;
    width: 100% !important;
    box-sizing: border-box !important;
    padding: 10px 12px !important;
    border-radius: 13px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
    font-size: 16px !important;
    font-weight: 950 !important;
    line-height: 1.25 !important;
    text-decoration: none !important;
    letter-spacing: 0.10px !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.85) !important;
    background: rgba(15, 23, 42, 0.30) !important;
    border: 1px solid rgba(147, 197, 253, 0.20) !important;
}

.menu-nav-item:hover {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: rgba(37, 99, 235, 0.40) !important;
    border: 1px solid rgba(147, 197, 253, 0.60) !important;
    text-decoration: none !important;
}

.menu-nav-item.active {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(14, 165, 233, 0.78)) !important;
    border: 1px solid rgba(191, 219, 254, 0.85) !important;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.35) !important;
}

/* Refuerzo para que Streamlit no pinte los links del menú en gris */
div[data-testid="column"] .menu-nav a,
div[data-testid="column"] .menu-nav a *,
.stApp .menu-nav a,
.stApp .menu-nav a * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
}


/* =========================================================
   MENÚ CON BOTONES STREAMLIT - NO ABRE PESTAÑAS NUEVAS
   ========================================================= */
.menu-botones-title {
    display: none !important;
}

div[data-testid="column"]:has(.menu-bg) div[data-testid="stButton"],
div[data-testid="column"]:has(.menu-marker) div[data-testid="stButton"] {
    width: 100% !important;
    margin: 0 0 7px 0 !important;
}

div[data-testid="column"]:has(.menu-bg) div[data-testid="stButton"] > button,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stButton"] > button {
    width: 100% !important;
    min-height: 46px !important;
    height: 46px !important;
    justify-content: flex-start !important;
    text-align: left !important;
    border-radius: 13px !important;
    padding: 10px 12px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: rgba(15, 23, 42, 0.30) !important;
    border: 1px solid rgba(147, 197, 253, 0.20) !important;
    font-size: 16px !important;
    font-weight: 950 !important;
    line-height: 1.25 !important;
    letter-spacing: 0.10px !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.85) !important;
    box-shadow: none !important;
}

div[data-testid="column"]:has(.menu-bg) div[data-testid="stButton"] > button:hover,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stButton"] > button:hover {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: rgba(37, 99, 235, 0.40) !important;
    border: 1px solid rgba(147, 197, 253, 0.60) !important;
}

/* Botón deshabilitado = página actual seleccionada */
div[data-testid="column"]:has(.menu-bg) div[data-testid="stButton"] > button:disabled,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stButton"] > button:disabled {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(14, 165, 233, 0.78)) !important;
    border: 1px solid rgba(191, 219, 254, 0.85) !important;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.35) !important;
}

div[data-testid="column"]:has(.menu-bg) div[data-testid="stButton"] > button:disabled *,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stButton"] > button:disabled * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
}



/* =========================================================
   AJUSTE FINAL: MENÚ SIN SOBRESALIR DEL PANEL IZQUIERDO
   ========================================================= */
:root {
    --menu-panel-width: 290px;
    --menu-inner-width: 260px;
}

.menu-bg {
    width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    overflow: hidden !important;
}

/* La columna izquierda queda limitada al ancho real del panel */
div[data-testid="column"]:has(.menu-bg),
div[data-testid="column"]:has(.menu-marker),
div[data-testid="column"]:has(.menu-brand) {
    width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    padding-left: 10px !important;
    padding-right: 10px !important;
}

.menu-panel-content,
.menu-nav,
.menu-line,
.menu-footer-box,
div[data-testid="column"]:has(.menu-bg) div[data-testid="stSelectbox"],
div[data-testid="column"]:has(.menu-marker) div[data-testid="stSelectbox"] {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}

.menu-nav {
    padding-right: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}

.menu-nav-item,
.menu-nav-item:link,
.menu-nav-item:visited,
.menu-nav-item:hover,
.menu-nav-item.active {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
    white-space: nowrap !important;
    text-overflow: ellipsis !important;
    padding-left: 12px !important;
    padding-right: 10px !important;
}

/* Selectores Equipo / Año / Mes dentro del ancho del panel */
div[data-testid="column"]:has(.menu-bg) [data-baseweb="select"],
div[data-testid="column"]:has(.menu-marker) [data-baseweb="select"],
div[data-testid="column"]:has(.menu-bg) [data-baseweb="select"] > div,
div[data-testid="column"]:has(.menu-marker) [data-baseweb="select"] > div {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
}

.menu-footer-box {
    margin-right: 0 !important;
}

/* Evita que cualquier bloque interno del menú se salga hacia la página principal */
div[data-testid="column"]:has(.menu-bg) *,
div[data-testid="column"]:has(.menu-marker) * {
    max-width: 100% !important;
}

/* En móviles mantiene el panel fijo sin invadir el contenido */
@media (max-width: 900px) {
    :root {
        --menu-panel-width: 290px;
        --menu-inner-width: 260px;
    }
}



/* =========================================================
   CORRECCIÓN 3.3: MENÚ VISIBLE Y ESTRUCTURA FIJA
   ========================================================= */
:root {
    --menu-panel-width: 290px !important;
    --menu-inner-width: 260px !important;
    --content-gap: 18px !important;
}

/* Ancho fijo del panel izquierdo completo */
.menu-bg {
    width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    z-index: 1 !important;
}

/* Columna izquierda fija: evita que el contenido se monte encima al hacer zoom */
div[data-testid="column"]:has(.menu-bg),
div[data-testid="column"]:has(.menu-marker),
div[data-testid="column"]:has(.menu-brand) {
    flex: 0 0 var(--menu-panel-width) !important;
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    padding-left: 12px !important;
    padding-right: 12px !important;
    overflow: hidden !important;
    z-index: 10 !important;
}

/* Columna derecha: queda separada del menú y no se mete debajo */
div[data-testid="column"]:has(.menu-bg) + div[data-testid="column"],
div[data-testid="column"]:has(.menu-marker) + div[data-testid="column"],
div[data-testid="column"]:has(.menu-brand) + div[data-testid="column"] {
    flex: 1 1 auto !important;
    min-width: 980px !important;
    padding-left: var(--content-gap) !important;
    box-sizing: border-box !important;
    position: relative !important;
    z-index: 2 !important;
}

/* Mantiene el tablero ordenado; si la ventana es muy angosta aparece scroll horizontal en vez de montar elementos */
.main .block-container,
.block-container {
    min-width: 1360px !important;
    overflow-x: auto !important;
}

/* Título más estable al cambiar zoom */
.title-main {
    font-size: clamp(30px, 2.25vw, 42px) !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

.header-logo-box img {
    width: 150px !important;
    max-width: 150px !important;
}

/* Botones del menú: siempre oscuros, nunca blancos */
div[data-testid="column"]:has(.menu-bg) div[data-testid="stButton"] button,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stButton"] button {
    width: 100% !important;
    min-height: 46px !important;
    height: auto !important;
    justify-content: flex-start !important;
    text-align: left !important;
    border-radius: 13px !important;
    padding: 10px 12px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: rgba(15, 23, 42, 0.52) !important;
    border: 1px solid rgba(147, 197, 253, 0.24) !important;
    font-size: 15px !important;
    font-weight: 950 !important;
    line-height: 1.25 !important;
    letter-spacing: 0.05px !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.85) !important;
    box-shadow: none !important;
    white-space: normal !important;
}

div[data-testid="column"]:has(.menu-bg) div[data-testid="stButton"] button:hover,
div[data-testid="column"]:has(.menu-marker) div[data-testid="stButton"] button:hover {
    background: rgba(37, 99, 235, 0.55) !important;
    border-color: rgba(191, 219, 254, 0.70) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* Item actualmente seleccionado: HTML propio, no botón deshabilitado */
.menu-active-item {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    box-sizing: border-box !important;
    padding: 12px 12px !important;
    border-radius: 13px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%) !important;
    border: 1px solid rgba(219, 234, 254, 0.95) !important;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.38) !important;
    font-size: 15.5px !important;
    font-weight: 950 !important;
    line-height: 1.25 !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.70) !important;
    margin-bottom: 7px !important;
    white-space: normal !important;
}

.menu-active-item * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* Anchos internos del menú */
.menu-panel-content,
.menu-nav,
.menu-line,
.menu-footer-box,
div[data-testid="column"]:has(.menu-bg) div[data-testid="stButton"],
div[data-testid="column"]:has(.menu-marker) div[data-testid="stButton"],
div[data-testid="column"]:has(.menu-bg) div[data-testid="stSelectbox"],
div[data-testid="column"]:has(.menu-marker) div[data-testid="stSelectbox"] {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
}

/* Ajuste especial para textos largos del menú */
.menu-brand {
    width: var(--menu-inner-width) !important;
}
.menu-title {
    font-size: 13px !important;
}
.menu-subtitle {
    font-size: 11px !important;
}

/* Selectores dentro del panel: no se salen */
div[data-testid="column"]:has(.menu-bg) [data-baseweb="select"],
div[data-testid="column"]:has(.menu-marker) [data-baseweb="select"],
div[data-testid="column"]:has(.menu-bg) [data-baseweb="select"] > div,
div[data-testid="column"]:has(.menu-marker) [data-baseweb="select"] > div {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
}

/* Tablas y gráficos contenidos dentro de su bloque */
[data-testid="stDataFrame"],
[data-testid="stPlotlyChart"] {
    max-width: 100% !important;
    overflow: hidden !important;
}



/* =========================================================
   CORRECCIÓN 3.4: MENÚ EN SIDEBAR FIJO Y RESPONSIVE
   ========================================================= */
:root {
    --menu-panel-width: 290px !important;
    --menu-inner-width: 260px !important;
}

/* Sidebar oficial de Streamlit: estable al agrandar/achicar o usar zoom */
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    background: #020617 !important;
    border-right: 1px solid rgba(147, 197, 253, 0.28) !important;
    box-shadow: 10px 0 24px rgba(15, 23, 42, 0.28) !important;
    overflow: hidden !important;
}

section[data-testid="stSidebar"] > div {
    background: #020617 !important;
    width: var(--menu-panel-width) !important;
    padding: 12px 14px 18px 14px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

section[data-testid="stSidebar"] .menu-bg {
    display: none !important;
}

section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] .menu-brand {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    margin: 0 0 18px 0 !important;
    width: var(--menu-inner-width) !important;
}

section[data-testid="stSidebar"] .menu-title {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 13px !important;
    font-weight: 950 !important;
    line-height: 1.15 !important;
    letter-spacing: 0.35px !important;
    text-shadow: 0 2px 5px rgba(0,0,0,0.75) !important;
}

section[data-testid="stSidebar"] .menu-subtitle {
    color: #bfdbfe !important;
    -webkit-text-fill-color: #bfdbfe !important;
    font-size: 11px !important;
    margin-top: 6px !important;
    font-weight: 950 !important;
}

section[data-testid="stSidebar"] .menu-line {
    border: 0 !important;
    border-top: 1px solid rgba(191, 219, 254, 0.25) !important;
    margin: 14px 0 16px 0 !important;
}

/* Botones del menú: visibles y dentro del panel */
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    min-height: 48px !important;
    height: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    border-radius: 13px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: rgba(15, 23, 42, 0.62) !important;
    border: 1px solid rgba(147, 197, 253, 0.26) !important;
    box-shadow: none !important;
    font-size: 15px !important;
    font-weight: 950 !important;
    line-height: 1.25 !important;
    letter-spacing: 0.05px !important;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.85) !important;
    margin-bottom: 7px !important;
    padding: 10px 12px !important;
    white-space: normal !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background: rgba(37, 99, 235, 0.55) !important;
    border-color: rgba(191, 219, 254, 0.70) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    box-sizing: border-box !important;
    padding: 12px 12px !important;
    border-radius: 13px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%) !important;
    border: 1px solid rgba(219, 234, 254, 0.95) !important;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.38) !important;
    font-size: 15.5px !important;
    font-weight: 950 !important;
    line-height: 1.25 !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.70) !important;
    margin-bottom: 7px !important;
    white-space: normal !important;
}

/* Filtros visibles dentro del panel izquierdo */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label,
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label * {
    color: #dbeafe !important;
    -webkit-text-fill-color: #dbeafe !important;
    opacity: 1 !important;
    font-weight: 950 !important;
    font-size: 13px !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.55) !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #ffffff !important;
    border-radius: 12px !important;
    min-height: 44px !important;
    border: 1px solid rgba(255,255,255,0.45) !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    font-weight: 800 !important;
}

section[data-testid="stSidebar"] .menu-footer-box {
    border: 1px solid rgba(147,197,253,0.35) !important;
    background: rgba(2, 6, 23, 0.96) !important;
    border-radius: 16px !important;
    padding: 13px !important;
    margin-top: 18px !important;
    box-shadow: 0 10px 20px rgba(0,0,0,0.40) !important;
}

section[data-testid="stSidebar"] .menu-info,
section[data-testid="stSidebar"] .menu-info * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 12.5px !important;
    line-height: 1.68 !important;
    font-weight: 850 !important;
}

section[data-testid="stSidebar"] .menu-info b {
    color: #93c5fd !important;
    -webkit-text-fill-color: #93c5fd !important;
    font-weight: 950 !important;
}

/* Contenido principal estable: no se monta sobre el menú */
.main .block-container,
.block-container {
    padding-top: 0rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: none !important;
    min-width: 1180px !important;
    overflow-x: auto !important;
}

/* Mantiene las tarjetas y gráficos en orden cuando se cambia zoom */
div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
}

.title-main {
    font-size: clamp(30px, 2.2vw, 42px) !important;
    white-space: nowrap !important;
    text-align: center !important;
}

.header-logo-box {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    text-align: right !important;
}

.header-logo-box img {
    width: 170px !important;
    max-width: 170px !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}



/* =========================================================
   AJUSTE 5.1: ENCABEZADO SUPERIOR FIJO Y PRÓXIMAS MANTENCIONES COMPACTO
   ========================================================= */
.main-fixed-header {
    position: sticky !important;
    top: 0 !important;
    z-index: 5000 !important;
    width: 100% !important;
    min-height: 64px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 18px !important;
    padding: 7px 14px 7px 0 !important;
    margin: 0 0 6px 0 !important;
    background: rgba(238, 243, 249, 0.96) !important;
    backdrop-filter: blur(7px) !important;
    border-bottom: 1px solid rgba(203, 213, 225, 0.70) !important;
    box-shadow: 0 7px 18px rgba(15, 23, 42, 0.055) !important;
    box-sizing: border-box !important;
}

.main-fixed-title {
    color: #0f172a !important;
    font-size: clamp(31px, 2.35vw, 43px) !important;
    font-weight: 950 !important;
    line-height: 1.03 !important;
    letter-spacing: -0.7px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

.main-fixed-logo {
    flex: 0 0 auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-end !important;
}

.main-fixed-logo img {
    width: 170px !important;
    max-width: 170px !important;
    height: auto !important;
    display: block !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}

.main-fixed-header-spacer {
    height: 10px !important;
}

.proximas-box {
    width: 100% !important;
    max-width: none !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
}

.proximas-box .panel-title {
    margin-top: 20px !important;
    margin-bottom: 8px !important;
    font-size: 18px !important;
    white-space: nowrap !important;
    text-align: center !important;
}

.proximas-box .next-item {
    width: 100% !important;
    max-width: none !important;
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) auto !important;
    column-gap: 8px !important;
    align-items: center !important;
    justify-content: start !important;
    padding: 5px 0 !important;
    min-height: 42px !important;
}

.proximas-box .next-title {
    font-size: 11.7px !important;
    line-height: 1.12 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

.proximas-box .next-sub {
    font-size: 10px !important;
    line-height: 1.10 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

.proximas-box .badge-days {
    justify-self: end !important;
    padding: 4px 6px !important;
    font-size: 9.6px !important;
    min-width: 46px !important;
    text-align: center !important;
}

.proximas-box .badge-days.badge-overdue {
    background: #fef2f2 !important;
    color: #dc2626 !important;
    border: 1px solid #fca5a5 !important;
    font-weight: 950 !important;
}

/* =========================================================
   AJUSTE 5.2: TÍTULO SUPERIOR SIN FRANJA DE FONDO
   - Se sube hacia la parte superior.
   - Se elimina caja, sombra, borde y blur detrás del título.
   ========================================================= */
.main .block-container,
.block-container,
section.main > div {
    padding-top: 0px !important;
    margin-top: 0px !important;
}

.main-fixed-header {
    position: sticky !important;
    top: 0px !important;
    z-index: 5000 !important;
    min-height: 54px !important;
    height: 54px !important;
    padding: 0px 14px 0px 0px !important;
    margin: -56px 0 4px 0 !important;
    background: transparent !important;
    background-color: transparent !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    border: 0 !important;
    border-bottom: 0 !important;
    box-shadow: none !important;
}

.main-fixed-title {
    background: transparent !important;
    background-color: transparent !important;
    color: #0f172a !important;
    font-size: clamp(32px, 2.35vw, 43px) !important;
    font-weight: 950 !important;
    line-height: 1 !important;
    text-shadow: none !important;
}

.main-fixed-logo {
    background: transparent !important;
    background-color: transparent !important;
}

.main-fixed-logo img {
    width: 170px !important;
    max-width: 170px !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}

.main-fixed-header-spacer {
    height: 0px !important;
}

</style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# CARGA DE DATOS
# =========================================================

def buscar_archivo_excel_equipos():
    """Busca la planilla de equipos dentro de la carpeta del proyecto.

    Prioriza el nombre exacto y, si no existe, acepta versiones como (5),
    _con_Planta u otras que comiencen con el mismo nombre base.
    """
    candidatos = []

    for carpeta in CARPETAS_EXCEL_EQUIPOS:
        if not os.path.isdir(carpeta):
            continue

        exacto = os.path.join(carpeta, f"{ARCHIVO_EQUIPOS_BASE}.xlsx")
        if os.path.isfile(exacto):
            return exacto

        patron = os.path.join(carpeta, f"{ARCHIVO_EQUIPOS_BASE}*.xlsx")
        candidatos.extend([ruta for ruta in glob.glob(patron) if os.path.isfile(ruta)])

    if not candidatos:
        return None

    # Se usa la versión más recientemente modificada cuando hay varias copias.
    candidatos = sorted(set(candidatos), key=lambda ruta: os.path.getmtime(ruta), reverse=True)
    return candidatos[0]


def leer_equipos_excel_local():
    """Lee exclusivamente la hoja EQUIPOS de la planilla local del proyecto."""
    ruta = buscar_archivo_excel_equipos()
    if not ruta:
        return pd.DataFrame(), None

    try:
        df = pd.read_excel(ruta, sheet_name="EQUIPOS")
    except Exception:
        return pd.DataFrame(), ruta

    # Conserva una columna sin encabezado cuando contiene datos (columna H de la planilla).
    # Se presenta como Detalle para no perder información como Brock SL-140.
    renombres = {}
    detalle_num = 1
    for columna in df.columns:
        nombre = str(columna).strip()
        if nombre.lower().startswith("unnamed"):
            serie = df[columna]
            tiene_datos = serie.notna() & (serie.astype(str).str.strip() != "")
            if tiene_datos.any():
                nuevo = "Detalle" if detalle_num == 1 else f"Detalle_{detalle_num}"
                renombres[columna] = nuevo
                detalle_num += 1

    if renombres:
        df = df.rename(columns=renombres)

    # Elimina únicamente columnas completamente vacías.
    df = df.dropna(axis=1, how="all")
    df = df.dropna(how="all")

    return normalizar_columnas_dataframe(df), ruta


@st.cache_data(ttl=CACHE_GOOGLE_SHEETS_SEGUNDOS, show_spinner="Actualizando datos...")
def cargar_datos():
    datos = {}

    for hoja in HOJAS_GOOGLE_SHEETS:
        datos[hoja] = leer_hoja_google_sheet(hoja)

    # La hoja EQUIPOS de Google Sheets se mantiene como respaldo y para no
    # alterar los demás módulos de la aplicación.
    if datos.get("EQUIPOS", pd.DataFrame()).empty:
        raise FileNotFoundError(
            "No se pudo leer la hoja EQUIPOS desde Google Sheets. "
            "Revisa que el archivo esté compartido como lector y que la pestaña se llame EQUIPOS."
        )

    # Para la página Equipos se prioriza la planilla que está en la carpeta.
    equipos_local, ruta_equipos = leer_equipos_excel_local()
    if equipos_local is not None and not equipos_local.empty:
        datos["EQUIPOS_PLANILLA"] = equipos_local
        fuente_equipos = ruta_equipos
    else:
        datos["EQUIPOS_PLANILLA"] = datos["EQUIPOS"].copy()
        fuente_equipos = GOOGLE_SHEET_URL

    datos["FUENTE_EQUIPOS"] = fuente_equipos
    return GOOGLE_SHEET_URL, datos


def preparar_equipos(df):
    equipos = normalizar_columnas_dataframe(df.copy())

    # Columnas propias de la planilla de equipos mostrada en Excel.
    for columna in [
        "Tipo_Equipo", "Marca", "Contrato", "Modelo", "Numero_Chasis",
        "Patente_Codigo", "Detalle", "Permiso", "Revision", "Acreditacion", "Planta"
    ]:
        equipos = asegurar_columna(equipos, columna, "")

    # Compatibilidad con versiones antiguas que todavía traen Patente.
    if "Patente" in equipos.columns:
        patente_codigo_vacia = (
            equipos["Patente_Codigo"].isna()
            | equipos["Patente_Codigo"].astype(str).str.strip().isin(["", "0", "0.0", "nan", "None"])
        )
        equipos.loc[patente_codigo_vacia, "Patente_Codigo"] = equipos.loc[patente_codigo_vacia, "Patente"]

    # Algunas versiones antiguas separaban los contratos con una fila que solo
    # contenía PLYWOOD 1, PLYWOOD 2, CONTRATO MULCHEN, CONSTRUCTORA, etc.
    # Aquí se transforma ese encabezado en la columna Contrato y se elimina la fila separadora.
    contrato_actual = ""
    filas_encabezado = []
    columnas_clave = ["Marca", "Modelo", "Numero_Chasis", "Patente_Codigo", "Año"]

    def valor_vacio(valor):
        if pd.isna(valor):
            return True
        return str(valor).strip().lower() in ["", "nan", "none", "nat", "0", "0.0"]

    for idx, fila in equipos.iterrows():
        tipo = str(fila.get("Tipo_Equipo", "")).strip()
        solo_encabezado = bool(tipo) and all(valor_vacio(fila.get(c, "")) for c in columnas_clave)

        if solo_encabezado:
            contrato_actual = tipo
            filas_encabezado.append(idx)
            continue

        contrato_fila = str(fila.get("Contrato", "")).strip()
        if valor_vacio(contrato_fila) and contrato_actual:
            equipos.at[idx, "Contrato"] = contrato_actual

    if filas_encabezado:
        equipos = equipos.drop(index=filas_encabezado).copy()

    # Si la versión anterior ya trae PLANTA, úsala también como respaldo de Contrato.
    if "Planta" in equipos.columns:
        contrato_vacio = equipos["Contrato"].apply(valor_vacio)
        equipos.loc[contrato_vacio, "Contrato"] = equipos.loc[contrato_vacio, "Planta"]

    # Fechas documentales de la planilla.
    for columna in ["Permiso", "Revision", "Acreditacion"]:
        equipos[columna] = equipos[columna].apply(convertir_fecha)

    # Columnas heredadas que utilizan Dashboard, Alertas y filtros generales.
    columnas_texto = [
        "ID_Equipo", "Equipo", "Patente_Codigo", "Tipo_Equipo", "Marca", "Modelo",
        "Estado", "Área", "Responsable", "Unidad_Control", "Frecuencia_Mantencion",
        "Observacion", "Imagen", "Contrato", "Numero_Chasis", "Detalle", "Planta"
    ]

    for columna in columnas_texto:
        equipos = asegurar_columna(equipos, columna, "")

    equipos = asegurar_columna(equipos, "Fecha_Ingreso", pd.NaT)
    equipos = asegurar_columna(equipos, "Proxima_Mantencion", 0)
    equipos = asegurar_columna(equipos, "Año", 0)
    equipos = asegurar_columna(equipos, "Km_Horometro_Actual", 0)

    equipos["Año"] = equipos["Año"].apply(limpiar_numero)
    equipos["Km_Horometro_Actual"] = equipos["Km_Horometro_Actual"].apply(limpiar_numero)
    equipos["Proxima_Mantencion"] = equipos["Proxima_Mantencion"].apply(limpiar_numero)
    equipos = preparar_fecha_columnas(equipos, ["Fecha_Ingreso"])

    # Construye un nombre de equipo cuando la nueva planilla no trae columna EQUIPO.
    def nombre_equipo(fila):
        existente = str(fila.get("Equipo", "")).strip()
        if existente.lower() not in ["", "nan", "none", "sin equipo"]:
            return existente

        tipo = str(fila.get("Tipo_Equipo", "")).strip()
        patente = str(fila.get("Patente_Codigo", "")).strip()
        modelo = str(fila.get("Modelo", "")).strip()
        chasis = str(fila.get("Numero_Chasis", "")).strip()

        if patente.lower() not in ["", "nan", "none"]:
            return f"{tipo} - {patente}".strip(" -")
        if modelo.lower() not in ["", "nan", "none"]:
            return f"{tipo} - {modelo}".strip(" -")
        if chasis.lower() not in ["", "nan", "none"]:
            return f"{tipo} - {chasis}".strip(" -")
        return tipo or "Sin equipo"

    equipos["Equipo"] = equipos.apply(nombre_equipo, axis=1)
    equipos["Estado"] = equipos["Estado"].fillna("Sin estado").astype(str).str.strip()
    equipos.loc[equipos["Estado"].isin(["", "nan", "None", "none"]), "Estado"] = "Sin estado"

    # Elimina filas sin información real de equipo.
    equipos = equipos[
        ~equipos["Tipo_Equipo"].fillna("").astype(str).str.strip().str.lower().isin(["", "nan", "none"])
    ].copy()

    equipos = aplicar_unidad_control_por_equipo(equipos)
    return equipos.reset_index(drop=True)


def preparar_mantenciones(df):
    mant = df.copy()

    columnas_texto = [
        "ID_Mantencion",
        "ID_Equipo",
        "Equipo",
        "Tipo_Mantencion",
        "Categoria",
        "Proveedor",
        "Responsable",
        "Descripcion",
        "Estado_Mantencion",
        "Documento_Respaldo",
        "Observacion",
    ]

    for columna in columnas_texto:
        mant = asegurar_columna(mant, columna, "")

    mant = asegurar_columna(mant, "Fecha", pd.NaT)
    mant = asegurar_columna(mant, "Costo_CLP", 0)
    mant["Costo_CLP"] = mant["Costo_CLP"].apply(limpiar_numero)

    mant = preparar_fecha_columnas(
        mant,
        [
            "Fecha",
        ],
    )

    # La hoja MANTENCIONES ya no utiliza la columna Proxima_Mantencion.
    # La próxima mantención oficial se calcula exclusivamente desde la hoja EQUIPOS.
    mant = mant.drop(columns=["Proxima_Mantencion"], errors="ignore")

    mant = preparar_periodo(mant)

    mant["Equipo"] = mant["Equipo"].fillna("").astype(str).str.strip()
    mant["Tipo_Mantencion"] = mant["Tipo_Mantencion"].fillna("Sin tipo").astype(str).str.strip().apply(normalizar_tipo_mantencion)
    mant["Mantencion"] = mant["Tipo_Mantencion"]
    mant["Estado_Mantencion"] = mant["Estado_Mantencion"].fillna("Sin estado").astype(str).str.strip()

    # Elimina filas vacías que vienen desde el formato de Excel y generaban registros $0 / Sin estado.
    mant = mant[
        (mant["Equipo"].str.lower().isin(["", "nan", "none"]) == False)
        | (mant["Fecha"].notna())
        | (mant["Costo_CLP"] > 0)
    ].copy()

    return mant


def preparar_gastos(df):
    gastos = df.copy()

    columnas_texto = [
        "ID_Gasto",
        "ID_Equipo",
        "Equipo",
        "Mantencion",
        "Tipo_Gasto",
        "Descripcion",
        "Proveedor",
        "Documento_Respaldo",
        "Observacion",
    ]

    for columna in columnas_texto:
        gastos = asegurar_columna(gastos, columna, "")

    # En algunas hojas el encabezado Mantencion se normaliza como Tipo_Mantencion.
    # Para gastos adicionales lo usamos como columna auxiliar de clasificación.
    if "Tipo_Mantencion" in gastos.columns:
        mant_aux = gastos["Tipo_Mantencion"].fillna("").astype(str).str.strip()
        gastos.loc[gastos["Mantencion"].fillna("").astype(str).str.strip().isin(["", "nan", "None", "none"]), "Mantencion"] = mant_aux

    gastos = asegurar_columna(gastos, "Costo_CLP", 0)
    gastos["Costo_CLP"] = gastos["Costo_CLP"].apply(limpiar_numero)

    gastos = preparar_fecha_columnas(gastos, ["Fecha"])
    gastos = preparar_periodo(gastos)

    gastos["Equipo"] = gastos["Equipo"].fillna("").astype(str).str.strip()
    gastos["Tipo_Gasto"] = gastos["Tipo_Gasto"].fillna("Sin tipo").astype(str).str.strip().apply(normalizar_tipo_gasto)
    gastos.loc[gastos["Tipo_Gasto"].str.lower().isin(["", "nan", "none", "nat", "0"]), "Tipo_Gasto"] = "Sin tipo"
    gastos["Mantencion"] = gastos["Mantencion"].fillna("Sin tipo").astype(str).str.strip().apply(normalizar_tipo_mantencion)

    if "Descripcion" not in gastos.columns:
        gastos["Descripcion"] = ""
    gastos["Clasificacion_Costo"] = gastos.apply(
        lambda x: categoria_costo_gasto(x.get("Tipo_Gasto", ""), x.get("Descripcion", ""), x.get("Mantencion", "")),
        axis=1,
    )

    # Elimina filas vacías que vienen desde el formato de Excel y generaban registros $0 / Sin mes.
    gastos = gastos[
        (gastos["Equipo"].str.lower().isin(["", "nan", "none"]) == False)
        | (gastos["Fecha"].notna())
        | (gastos["Costo_CLP"] > 0)
    ].copy()

    return gastos


def preparar_checklist(df):
    checklist = df.copy()

    columnas_texto = [
        "ID_Checklist",
        "ID_Equipo",
        "Equipo",
        "Operador",
        "Estado_Checklist",
        "Observacion",
        "Accion_Requerida",
        "Responsable",
        "Estado_Cierre",
    ]

    for columna in columnas_texto:
        checklist = asegurar_columna(checklist, columna, "")

    checklist = asegurar_columna(checklist, "Km_Horometro", 0)
    checklist["Km_Horometro"] = checklist["Km_Horometro"].apply(limpiar_numero)

    checklist = preparar_fecha_columnas(
        checklist,
        [
            "Fecha",
            "Fecha_Cierre",
        ],
    )

    checklist = preparar_periodo(checklist)
    checklist["Equipo"] = checklist["Equipo"].fillna("").astype(str).str.strip()

    return checklist


def preparar_combustible(df):
    combustible = df.copy()

    columnas_texto = [
        "ID_Registro",
        "ID_Equipo",
        "Equipo",
        "Tipo_Combustible",
        "Rendimiento",
        "Observacion",
    ]

    for columna in columnas_texto:
        combustible = asegurar_columna(combustible, columna, "")

    for columna in [
        "Litros",
        "Valor_Unitario",
        "Costo_Total",
        "Km_Horometro",
    ]:
        combustible = asegurar_columna(combustible, columna, 0)
        combustible[columna] = combustible[columna].apply(limpiar_numero)

    combustible = preparar_fecha_columnas(combustible, ["Fecha"])
    combustible = preparar_periodo(combustible)
    combustible["Equipo"] = combustible["Equipo"].fillna("").astype(str).str.strip()

    return combustible


def preparar_documentos(df):
    documentos = df.copy()

    columnas_texto = [
        "ID_Documento",
        "ID_Equipo",
        "Equipo",
        "Tipo_Documento",
        "Descripcion",
        "Estado",
        "Ruta_Link",
        "Observacion",
    ]

    for columna in columnas_texto:
        documentos = asegurar_columna(documentos, columna, "")

    documentos = preparar_fecha_columnas(
        documentos,
        [
            "Fecha",
            "Vencimiento",
        ],
    )

    documentos = preparar_periodo(documentos)
    documentos["Equipo"] = documentos["Equipo"].fillna("").astype(str).str.strip()

    return documentos


# =========================================================
# COMPONENTES VISUALES
# =========================================================

def aplicar_formato_grafico(figura, altura=360):
    figura.update_layout(
        height=altura,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(
            color=COLOR_TEXTO,
            size=12,
        ),
        title_font=dict(
            color=COLOR_TEXTO,
            size=16,
        ),
        legend=dict(
            font=dict(
                color=COLOR_TEXTO,
                size=12,
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(
            l=25,
            r=25,
            t=55,
            b=40,
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_color=COLOR_TEXTO,
        ),
    )

    figura.update_xaxes(
        title_text="",
        tickfont=dict(
            color=COLOR_GRIS,
            size=11,
        ),
        gridcolor="#eef2f7",
        zeroline=False,
    )

    figura.update_yaxes(
        title_text="",
        tickfont=dict(
            color=COLOR_GRIS,
            size=11,
        ),
        gridcolor="#eef2f7",
        zeroline=False,
    )

    return figura


def crear_donut_costos(costos_item):
    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=costos_item["Item"],
            values=costos_item["Costo"],
            hole=0.64,
            marker=dict(
                colors=[
                    "#2563eb",
                    "#ffb020",
                    "#55c595",
                ],
                line=dict(color="white", width=2),
            ),
            textinfo="percent",
            textposition="inside",
            insidetextorientation="auto",
            textfont=dict(
                color="white",
                size=14,
                family="Arial Black",
            ),
            hovertemplate="<b>%{label}</b><br>Monto: %{customdata}<br>Participación: %{percent}<extra></extra>",
            customdata=[pesos(v) for v in costos_item["Costo"]],
        )
    )

    total = costos_item["Costo"].sum()

    fig.update_layout(
        title="Distribución de Costos",
        height=350,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=COLOR_TEXTO),
        margin=dict(l=10, r=10, t=45, b=10),
        annotations=[
            dict(
                text=f"Total<br><b>$ {numero(total)}</b>",
                x=0.5,
                y=0.5,
                font_size=15,
                font_color="#0f172a",
                showarrow=False,
            )
        ],
        legend=dict(
            orientation="v",
            x=1.02,
            y=0.72,
            font=dict(size=12),
        ),
        uniformtext_minsize=11,
        uniformtext_mode="hide",
    )

    return fig



def calcular_barra_proxima_mantencion(km_actual, proxima_mantencion, unidad=""):
    return calcular_estado_proxima_mantencion(km_actual, proxima_mantencion, unidad)[:4]


def kpi_card(icono, titulo, valor, subtitulo, color_fondo):
    st.markdown(
        f"""
<div class="kpi-card">
    <div class="kpi-icon" style="background:{color_fondo};">{icono}</div>
    <div class="kpi-title">{titulo}</div>
    <div class="kpi-value">{valor}</div>
    <div class="kpi-sub">{subtitulo}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def tarjeta_equipo(fila):
    estado = str(fila.get("Estado", "Sin estado"))
    clase = estado_clase(estado)

    km_actual = limpiar_numero(fila.get("Km_Horometro_Actual", 0))
    unidad_raw = fila.get("Unidad_Control", "")
    unidad = escape_html(unidad_control_texto(unidad_raw))
    proxima = limpiar_numero(fila.get("Proxima_Mantencion", 0))
    avance, texto_barra, color_barra, proxima_txt = calcular_barra_proxima_mantencion(km_actual, proxima, unidad_raw)

    src = imagen_equipo_src(fila)

    if src:
        imagen_html = f'<img class="equipo-img" src="{src}" alt="Imagen equipo">'
    else:
        imagen_html = '<div class="equipo-img-placeholder">🚜</div>'

    equipo = escape_html(fila.get("Equipo", ""))
    modelo = escape_html(fila.get("Modelo", ""))
    patente = escape_html(fila.get("Patente_Codigo", ""))
    estado_txt = escape_html(estado)
    texto_barra = escape_html(texto_barra)
    proxima_txt = escape_html(proxima_txt)

    modelo_valido = modelo if modelo and modelo.lower() not in ["nan", "none", "s/c", "n/a"] else "Sin modelo"
    patente_valida = patente if patente and patente.lower() not in ["nan", "none", "s/c", "n/a"] else "Sin patente"
    detalle = f"Modelo: {modelo_valido} · Patente: {patente_valida}"

    valor_uso = formatear_valor_control(km_actual, unidad_raw)

    st.markdown(
        f"""
<div class="equipo-card">
    {imagen_html}
    <div class="equipo-nombre">{equipo}</div>
    <div class="equipo-sub">{detalle}</div>
    <div class="{clase}">{estado_txt}</div>
    <div class="equipo-sub">Lectura actual: {escape_html(valor_uso)}</div>
    <div class="equipo-sub">Próxima mantención: <b>{proxima_txt}</b></div>
    <div class="progress-bg">
        <div class="progress-fill" style="width:{avance:.0f}%; --barra-color:{color_barra}; background-color:{color_barra} !important;"></div>
    </div>
    <div class="equipo-sub"><b>Análisis próxima mantención:</b> {texto_barra}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# MENÚ PROPIO# =========================================================
# MENÚ PROPIO
# =========================================================

def construir_menu(equipos, mantenciones, gastos, combustible, checklist, documentos):
    # Ícono superior del menú.
    # Busca automáticamente una imagen llamada logoredondo / logo redondo en la carpeta del proyecto.
    ruta_logo_menu = (
        buscar_imagen_por_nombre("logoredondo")
        or buscar_imagen_por_nombre("logo redondo")
        or buscar_imagen_por_nombre("logo_redondo")
        or buscar_imagen_por_nombre("logo-redondo")
    )

    if ruta_logo_menu:
        logo_menu_b64 = archivo_a_base64(ruta_logo_menu)
        logo_menu_mime = extension_mime(ruta_logo_menu)
        icono_menu_html = (
            '<div class="menu-icon-img">'
            f'<img src="data:{logo_menu_mime};base64,{logo_menu_b64}" alt="Logo menú">'
            '</div>'
        )
    else:
        icono_menu_html = '<div class="menu-icon">🚜</div>'

    # Estado del menú usado por CSS.
    # Se define aquí para evitar alerta de Pylance cuando analiza esta función.
    colapsado = bool(st.session_state.get("menu_colapsado", False))
    estado_menu_css = "menu-state-collapsed" if colapsado else "menu-state-expanded"

    st.markdown(
        f"""
        <div class="menu-bg"></div>
        <div class="menu-marker {estado_menu_css}"></div>
        <div class="menu-panel-content">
            <div class="menu-brand">
                {icono_menu_html}
                <div>
                    <div class="menu-title">SEGUIMIENTO<br>EQUIPOS MÓVILES</div>
                    <div class="menu-subtitle">SAIVAM · MULCHÉN</div>
                </div>
            </div>
            <hr class="menu-line">
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Menú con botones nativos de Streamlit.
    # Esto evita que el navegador abra pestañas nuevas al cambiar de página.
    paginas_menu = {
        "panel": "📊 Dashboard Ejecutivo",
        "equipos": "🚚 Equipos",
        "mantenciones": "🛠️ Mantenciones",
        "repuestos": "🧾 Gastos Adicionales",
        "costos": "💰 Costos",
        "proximas": "📅 Próximas Mantenciones",
        "alertas": "🔔 Alertas",
        "documentos": "📁 Documentación Legal",
    }

    pagina_actual = st.query_params.get("pagina", "panel")

    if pagina_actual not in paginas_menu:
        pagina_actual = "panel"
        st.query_params["pagina"] = "panel"

    st.markdown('<div class="menu-botones-title"></div>', unsafe_allow_html=True)

    for clave, texto in paginas_menu.items():
        es_actual = clave == pagina_actual

        if es_actual:
            st.markdown(
                f'<div class="menu-active-item">{texto}</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.button(
                texto,
                key=f"menu_{clave}",
                use_container_width=True,
            ):
                st.query_params["pagina"] = clave
                st.session_state["_saivam_mobile_menu_open"] = False
                st.rerun()

    st.markdown('<hr class="menu-line">', unsafe_allow_html=True)

    if st.button("🔄 Actualizar", key="actualizar_base_datos", use_container_width=True):
        st.cache_data.clear()
        st.session_state["_saivam_mobile_menu_open"] = False
        st.rerun()

    st.markdown('<hr class="menu-line">', unsafe_allow_html=True)

    pagina = paginas_menu[pagina_actual]

    equipos_disponibles = (
        ["Todos los equipos"]
        + equipos["Equipo"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda x: x != ""]
        .drop_duplicates()
        .tolist()
    )

    anios_base = pd.concat(
        [
            mantenciones["Año"],
            gastos["Año"],
            combustible["Año"],
            checklist["Año"],
            documentos["Año"],
        ],
        ignore_index=True,
    )

    anios_disponibles = sorted(
        [
            int(x)
            for x in anios_base.dropna().unique().tolist()
            if str(x) != "nan"
        ]
    )

    filtro_equipo = st.selectbox(
        "Equipo",
        equipos_disponibles,
    )

    filtro_anio = st.selectbox(
        "Año",
        ["Todos"] + anios_disponibles,
    )

    filtro_mes = st.selectbox(
        "Mes",
        ["Todos"] + list(MESES.values()),
    )

    st.markdown(
        f"""
        <div class="menu-footer-box">
            <div class="menu-info">
                Versión {VERSION}<br>
                <b>Actualización:</b><br>
                {datetime.now().strftime("%d/%m/%Y %H:%M")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return pagina, filtro_equipo, filtro_anio, filtro_mes


# =========================================================
# ENCABEZADO
# =========================================================

def encabezado(titulo):
    logo_html = ""

    if os.path.exists(LOGO_SUPERIOR):
        logo_b64 = archivo_a_base64(LOGO_SUPERIOR)
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="SAIVAM">'

    st.markdown(
        f"""
        <div class="main-fixed-header">
            <div class="main-fixed-title">{escape_html(titulo)}</div>
            <div class="main-fixed-logo">{logo_html}</div>
        </div>
        <div class="main-fixed-header-spacer"></div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# PÁGINAS
# =========================================================

def pagina_dashboard(equipos_f, mant_f, gastos_f, combustible_f, proximas_originales, filtro_equipo):
    hoy = pd.Timestamp(datetime.now().date())

    gastos_sin_combustible = gastos_no_combustible(gastos_f)

    costo_mantenciones = float(mant_f["Costo_CLP"].sum())
    costo_gastos = float(gastos_sin_combustible["Costo_CLP"].sum())
    costo_combustible = float(combustible_f["Costo_Total"].sum()) if "Costo_Total" in combustible_f.columns else 0.0
    # En el tablero principal se excluye combustible del total solicitado para distribución.
    costo_total = costo_mantenciones + costo_gastos

    mant_realizadas = len(mant_f)
    repuestos_utilizados = len(gastos_sin_combustible)
    equipos_registrados = len(equipos_f)

    if "Proxima_Mantencion" not in proximas_originales.columns:
        proximas_originales = pd.DataFrame(columns=["Equipo", "Categoria", "Tipo_Mantencion", "Proxima_Mantencion", "Km_Horometro_Actual", "Unidad_Control", "Costo_CLP"])

    mant_proximas = proximas_originales.copy()
    if "Proxima_Mantencion" in mant_proximas.columns:
        mant_proximas["Proxima_Mantencion"] = mant_proximas["Proxima_Mantencion"].apply(limpiar_numero)
        mant_proximas = mant_proximas[mant_proximas["Proxima_Mantencion"] > 0].copy()

    if filtro_equipo != "Todos los equipos":
        mant_proximas = mant_proximas[mant_proximas["Equipo"] == filtro_equipo]

    mant_proximas = resumen_proximas_por_equipo(mant_proximas) if not mant_proximas.empty else mant_proximas
    if not mant_proximas.empty:
        proxima_fila = mant_proximas.iloc[0]
        equipo_proximo = str(proxima_fila.get("Equipo", "Sin equipo")).strip()
        proxima_valor = proxima_fila.get("Proxima_Texto", "Sin dato")
        proxima_estado = proxima_fila.get("Texto_Estado", "Sin análisis")

        # Dashboard Ejecutivo: en la tarjeta de Próxima Mantención se muestra primero
        # el equipo correspondiente y debajo el Km/Horómetro objetivo con su estado.
        # Ejemplo: Grúa horquilla / Próx.: 7.952 Horómetro | Vencida: excedida en 675 Horómetro
        proxima_texto = equipo_proximo if equipo_proximo else "Sin equipo"
        proxima_sub = f"Próx.: {proxima_valor} | {proxima_estado}"
    else:
        proxima_texto = "Sin registro"
        proxima_sub = "No programada"

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        kpi_card("🛠️", "Mantenciones", f"{mant_realizadas}", "Registros del período", "#dbeafe")

    with k2:
        kpi_card("💲", "Monto Total", pesos(costo_total), "Costos del período", "#dcfce7")

    with k3:
        kpi_card("🧰", "Gastos Adic.", f"{repuestos_utilizados}", "Repuestos, mantenciones y administrativos", "#f3e8ff")

    with k4:
        kpi_card("📅", "Próxima Mantención", proxima_texto, proxima_sub, "#ffedd5")

    with k5:
        kpi_card("🚚", "Equipos Registrados", f"{equipos_registrados}", "Total equipos", "#ccfbf1")

    c1, c2 = st.columns([1.55, 1])

    with c1:
        st.markdown('<div class="panel-title">Histórico de Intervenciones</div>', unsafe_allow_html=True)

        historico = mant_f.copy()
        if "Tipo_Mantencion" in historico.columns:
            historico["Mantencion"] = historico["Tipo_Mantencion"].apply(normalizar_tipo_mantencion)

        if not historico.empty:
            historico = historico.sort_values("Fecha", ascending=False).head(10)

            columnas_base = [
                "Fecha",
                "Equipo",
                "Mantencion",
                "Descripcion",
                "Costo_CLP",
                "Estado_Mantencion",
            ]

            columnas_base = [c for c in columnas_base if c in historico.columns]
            mostrar = historico[columnas_base].copy()

            if "Fecha" in mostrar.columns:
                mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)

            if "Costo_CLP" in mostrar.columns:
                mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)

            mostrar = mostrar.rename(
                columns={
                    "Mantencion": "Tipo",
                    "Descripcion": "Descripción",
                    "Costo_CLP": "Monto",
                    "Estado_Mantencion": "Estado",
                }
            )

            mostrar_tabla_clara(mostrar, height=310)

        else:
            st.info("No existen mantenciones registradas para el filtro aplicado.")

    with c2:
        st.markdown('<div class="panel-title">Distribución de Costos</div>', unsafe_allow_html=True)

        costos_item = construir_consolidado_costos(mant_f, gastos_f)

        fig_donut = crear_donut_costos(costos_item)
        st.plotly_chart(fig_donut, use_container_width=True)

    c3, c4, c5 = st.columns([1.08, 0.90, 1.12])

    with c3:
        st.markdown('<div class="panel-title">Gastos adicionales / Administrativos</div>', unsafe_allow_html=True)

        repuestos = gastos_sin_combustible.copy()

        if not repuestos.empty:
            repuestos = repuestos.sort_values("Fecha", ascending=False).head(6)

            columnas_repuestos = [
                "Fecha",
                "Equipo",
                "Tipo_Gasto",
                "Descripcion",
                "Costo_CLP",
            ]

            columnas_repuestos = [c for c in columnas_repuestos if c in repuestos.columns]
            mostrar = repuestos[columnas_repuestos].copy()

            if "Fecha" in mostrar.columns:
                mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)

            if "Costo_CLP" in mostrar.columns:
                mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)

            mostrar = mostrar.rename(
                columns={
                    "Tipo_Gasto": "Tipo",
                    "Descripcion": "Detalle",
                    "Costo_CLP": "Monto",
                }
            )

            mostrar_tabla_clara(mostrar, height=230)

        else:
            st.info("No existen gastos adicionales o administrativos registrados.")

    with c4:
        st.markdown('<div class="proximas-box">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Próximas Mantenciones</div>', unsafe_allow_html=True)

        proximas = mant_proximas.copy()

        if not proximas.empty:
            for _, fila in proximas.iterrows():
                proxima_txt = fila.get("Proxima_Texto", formatear_valor_control(fila.get("Proxima_Mantencion", 0), fila.get("Unidad_Control", "")))
                saldo_restante = limpiar_numero(fila.get("Saldo_Restante", 0))
                saldo_txt = formatear_saldo_control(saldo_restante, fila.get("Unidad_Control", ""))
                clase_badge = "badge-days badge-overdue" if saldo_restante < 0 else "badge-days"

                st.markdown(
                    f"""
<div class="next-item">
    <div>
        <div class="next-title">{escape_html(fila.get("Equipo", ""))}</div>
        <div class="next-sub">{escape_html(fila.get("Categoria", ""))}</div>
        <div class="next-sub">Próx.: {escape_html(proxima_txt)}</div>
    </div>
    <div class="{clase_badge}">{escape_html(saldo_txt)}</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

        else:
            st.info("No existen próximas mantenciones registradas.")

        st.markdown('</div>', unsafe_allow_html=True)

    with c5:
        st.markdown('<div class="panel-title">Evolución de Costos</div>', unsafe_allow_html=True)

        mant_mes = (
            mant_f
            .groupby(["Año", "Mes_Numero", "Periodo"], as_index=False)["Costo_CLP"]
            .sum()
            .rename(columns={"Costo_CLP": "Mantenciones"})
        )

        gasto_mes = (
            gastos_sin_combustible
            .groupby(["Año", "Mes_Numero", "Periodo"], as_index=False)["Costo_CLP"]
            .sum()
            .rename(columns={"Costo_CLP": "Gastos"})
        )

        comb_mes = (
            combustible_f
            .groupby(["Año", "Mes_Numero", "Periodo"], as_index=False)["Costo_Total"]
            .sum()
            .rename(columns={"Costo_Total": "Combustible"})
        )

        costos_mes = (
            mant_mes
            .merge(gasto_mes, on=["Año", "Mes_Numero", "Periodo"], how="outer")
            .merge(comb_mes, on=["Año", "Mes_Numero", "Periodo"], how="outer")
            .fillna(0)
        )

        if not costos_mes.empty:
            costos_mes = costos_mes.sort_values(["Año", "Mes_Numero"])

            costos_mes["Monto Acumulado"] = (
                costos_mes["Mantenciones"]
                + costos_mes["Gastos"]
                + costos_mes["Combustible"]
            ).cumsum()

            fig_linea = px.line(
                costos_mes,
                x="Periodo",
                y="Monto Acumulado",
                markers=True,
                template="plotly_white",
            )

            fig_linea.update_traces(
                line=dict(width=3, color="#2563eb"),
                marker=dict(size=7),
                name="",
                showlegend=False,
                customdata=costos_mes["Monto Acumulado"].apply(pesos),
                hovertemplate="<b>%{x}</b><br>Monto acumulado: %{customdata}<extra></extra>",
            )
            fig_linea.update_layout(title_text="", showlegend=False, legend_title_text="")

            st.plotly_chart(aplicar_formato_grafico(fig_linea, 210), use_container_width=True)

        else:
            st.info("Sin costos para graficar.")

    st.markdown('<div class="panel-title">Estado de los Equipos</div>', unsafe_allow_html=True)

    if equipos_f.empty:
        st.info("No existen equipos registrados.")

    else:
        cantidad_columnas = min(len(equipos_f), 7)

        if cantidad_columnas <= 0:
            cantidad_columnas = 1

        columnas = st.columns(cantidad_columnas)

        for columna, (_, fila) in zip(columnas, equipos_f.head(7).iterrows()):
            with columna:
                tarjeta_equipo(fila)


def pagina_equipos(equipos_f):
    if equipos_f is None or equipos_f.empty:
        st.info("No existen equipos registrados en la planilla.")
        return

    equipos_vista = equipos_f.copy()

    # Disponibilidad estandarizada a partir de la columna Estado de la planilla.
    # Así se aceptan tanto OPERATIVO / NO OPERATIVO como
    # DISPONIBLE / NO DISPONIBLE.
    if "Estado" not in equipos_vista.columns:
        equipos_vista["Estado"] = ""
    equipos_vista["Disponibilidad"] = equipos_vista["Estado"].apply(
        _estado_disponibilidad_equipo
    )

    # -----------------------------------------------------
    # Filtros propios de la hoja EQUIPOS: Equipo, Contrato, Modelo y Estado
    # -----------------------------------------------------
    def _opciones_texto_equipos(columna, dataframe=None):
        fuente = equipos_f if dataframe is None else dataframe
        if columna not in fuente.columns:
            return []
        return sorted(
            {
                str(v).strip()
                for v in fuente[columna].dropna().tolist()
                if str(v).strip().lower() not in ["", "nan", "none", "nat"]
            },
            key=lambda x: x.casefold(),
        )

    # El contrato controla las opciones disponibles del filtro Equipo.
    # Al cambiar de contrato, el selector de Equipo muestra únicamente
    # los tipos de equipos registrados dentro de ese contrato.
    opciones_contrato = ["Todos los contratos"] + _opciones_texto_equipos("Contrato")
    if st.session_state.get("filtro_contrato_pagina_equipos", "Todos los contratos") not in opciones_contrato:
        st.session_state["filtro_contrato_pagina_equipos"] = "Todos los contratos"

    contrato_actual = st.session_state.get(
        "filtro_contrato_pagina_equipos", "Todos los contratos"
    )

    equipos_para_selector = equipos_f.copy()
    if contrato_actual != "Todos los contratos" and "Contrato" in equipos_para_selector.columns:
        equipos_para_selector = equipos_para_selector[
            equipos_para_selector["Contrato"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
            == str(contrato_actual).strip().casefold()
        ].copy()

    opciones_equipo = ["Todos los equipos"] + _opciones_texto_equipos(
        "Tipo_Equipo", equipos_para_selector
    )
    opciones_modelo = ["Todos los modelos"] + _opciones_texto_equipos("Modelo")
    opciones_estado = [
        "Todos los estados",
        "Disponible",
        "No disponible",
        "Sin estado",
    ]

    # Si el usuario cambia de contrato y el equipo seleccionado ya no existe
    # en ese contrato, se vuelve automáticamente a "Todos los equipos".
    if st.session_state.get("filtro_equipo_pagina_equipos", "Todos los equipos") not in opciones_equipo:
        st.session_state["filtro_equipo_pagina_equipos"] = "Todos los equipos"

    if st.session_state.get("filtro_modelo_pagina_equipos", "Todos los modelos") not in opciones_modelo:
        st.session_state["filtro_modelo_pagina_equipos"] = "Todos los modelos"

    if st.session_state.get("filtro_estado_pagina_equipos", "Todos los estados") not in opciones_estado:
        st.session_state["filtro_estado_pagina_equipos"] = "Todos los estados"

    st.markdown(
        """
        <style>
        div[data-testid="stMain"] div[data-testid="stSelectbox"] label p {
            font-size: 13px !important;
            font-weight: 700 !important;
        }
        div[data-testid="stMain"] div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
            min-height: 38px !important;
            height: 38px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    c_eq, c_ct, c_mod, c_est, _ = st.columns([1.15, 1.15, 1.15, 1.15, 1.8])
    with c_eq:
        filtro_equipo = st.selectbox(
            "Equipo", opciones_equipo, key="filtro_equipo_pagina_equipos"
        )
    with c_ct:
        filtro_contrato = st.selectbox(
            "Contrato", opciones_contrato, key="filtro_contrato_pagina_equipos"
        )
    with c_mod:
        filtro_modelo = st.selectbox(
            "Modelo", opciones_modelo, key="filtro_modelo_pagina_equipos"
        )
    with c_est:
        filtro_estado = st.selectbox(
            "Estado", opciones_estado, key="filtro_estado_pagina_equipos"
        )

    if filtro_equipo != "Todos los equipos" and "Tipo_Equipo" in equipos_vista.columns:
        equipos_vista = equipos_vista[
            equipos_vista["Tipo_Equipo"].fillna("").astype(str).str.strip().str.casefold()
            == str(filtro_equipo).strip().casefold()
        ].copy()

    if filtro_contrato != "Todos los contratos" and "Contrato" in equipos_vista.columns:
        equipos_vista = equipos_vista[
            equipos_vista["Contrato"].fillna("").astype(str).str.strip().str.casefold()
            == str(filtro_contrato).strip().casefold()
        ].copy()

    if filtro_modelo != "Todos los modelos" and "Modelo" in equipos_vista.columns:
        equipos_vista = equipos_vista[
            equipos_vista["Modelo"].fillna("").astype(str).str.strip().str.casefold()
            == str(filtro_modelo).strip().casefold()
        ].copy()

    # Los KPI reflejan la flota resultante de Equipo/Contrato/Modelo.
    # El filtro Estado se usa para acotar el detalle de la tabla, evitando
    # que seleccionar "Disponible" fuerce artificialmente el KPI a 100%.
    resumen_disp = _resumen_disponibilidad_equipos(equipos_vista)
    disponibilidad_txt = (
        f"{resumen_disp['porcentaje']:.1f}".replace(".", ",") + "%"
    )

    if filtro_estado != "Todos los estados":
        equipos_vista = equipos_vista[
            equipos_vista["Disponibilidad"] == filtro_estado
        ].copy()

    k_total, k_disp, k_no_disp, k_pct = st.columns(4, gap="medium")
    with k_total:
        st.metric("Total equipos", resumen_disp["total"])
    with k_disp:
        st.metric("Disponibles", resumen_disp["disponibles"])
    with k_no_disp:
        st.metric("No disponibles", resumen_disp["no_disponibles"])
    with k_pct:
        st.metric("Disponibilidad", disponibilidad_txt)

    st.markdown(
        f'<div class="panel-title">Registro de Equipos <span style="font-size:0.84rem;font-weight:500;">({len(equipos_vista)} equipos)</span></div>',
        unsafe_allow_html=True,
    )

    # Mismo orden visual de la planilla Excel mostrada por el usuario.
    columnas_tabla_equipos = [
        "Tipo_Equipo",
        "Marca",
        "Contrato",
        "Disponibilidad",
        "Modelo",
        "Numero_Chasis",
        "Patente_Codigo",
        "Año",
        "Detalle",
        "Permiso",
        "Revision",
        "Acreditacion",
        "Planta",
    ]

    columnas_tabla_equipos = [c for c in columnas_tabla_equipos if c in equipos_vista.columns]
    equipos_mostrar = equipos_vista[columnas_tabla_equipos].copy()

    # Oculta columnas opcionales completamente vacías para que la tabla no quede con espacios inútiles.
    columnas_con_datos = []
    for col in equipos_mostrar.columns:
        serie = equipos_mostrar[col]
        tiene_datos = serie.notna() & (~serie.astype(str).str.strip().str.lower().isin(["", "nan", "none", "nat"]))
        if tiene_datos.any():
            columnas_con_datos.append(col)
    equipos_mostrar = equipos_mostrar[columnas_con_datos].copy()

    for col_fecha in ["Permiso", "Revision", "Acreditacion"]:
        if col_fecha in equipos_mostrar.columns:
            equipos_mostrar[col_fecha] = equipos_mostrar[col_fecha].apply(fecha_texto)

    if "Año" in equipos_mostrar.columns:
        equipos_mostrar["Año"] = equipos_mostrar["Año"].apply(
            lambda v: "" if limpiar_numero(v) <= 0 else str(int(limpiar_numero(v)))
        )

    equipos_mostrar = equipos_mostrar.rename(
        columns={
            "Tipo_Equipo": "Tipo de vehículo",
            "Marca": "Marca",
            "Contrato": "Contrato",
            "Disponibilidad": "Disponibilidad",
            "Modelo": "Modelo",
            "Numero_Chasis": "Número de chasis",
            "Patente_Codigo": "Patente",
            "Año": "Año",
            "Detalle": "Detalle",
            "Permiso": "Permiso",
            "Revision": "Revisión",
            "Acreditacion": "Acreditación",
            "Planta": "Planta",
        }
    )

    mostrar_tabla_clara(equipos_mostrar, height=620)


def pagina_mantenciones(mant_f):
    st.markdown('<div class="section-head"><div class="panel-title page-section-title">Historial de Mantenciones</div></div>', unsafe_allow_html=True)

    if mant_f.empty:
        st.info("No existen mantenciones para el filtro aplicado.")
        return

    mant_base = mant_f.copy()
    if "Tipo_Mantencion" not in mant_base.columns:
        mant_base["Tipo_Mantencion"] = mant_base.get("Mantencion", "Sin tipo")

    mant_base["Tipo_Mantencion"] = mant_base["Tipo_Mantencion"].apply(normalizar_tipo_mantencion)
    mant_base["Mantencion"] = mant_base["Tipo_Mantencion"]
    mant_base["Costo_CLP"] = mant_base["Costo_CLP"].apply(limpiar_numero)

    # En este panel se trabaja únicamente con Preventiva y Correctiva.
    mant_base = mant_base[mant_base["Tipo_Mantencion"].isin(["Preventiva", "Correctiva"])].copy()

    if mant_base.empty:
        st.info("No existen mantenciones preventivas o correctivas para el filtro aplicado.")
        return

    tipos_presentes = [t for t in ["Preventiva", "Correctiva"] if t in mant_base["Tipo_Mantencion"].unique()]
    filtro_tipo = st.selectbox(
        "Filtrar por tipo de mantención",
        ["Todos"] + tipos_presentes,
        index=0,
    )

    if filtro_tipo != "Todos":
        mant_vista = mant_base[mant_base["Tipo_Mantencion"] == filtro_tipo].copy()
    else:
        mant_vista = mant_base.copy()

    c1, c2 = st.columns(2)

    with c1:
        kpi_card(
            "🟢",
            "Preventivas",
            pesos(mant_base[mant_base["Tipo_Mantencion"] == "Preventiva"]["Costo_CLP"].sum()),
            "Costo acumulado",
            "#dcfce7",
        )

    with c2:
        kpi_card(
            "🔴",
            "Correctivas",
            pesos(mant_base[mant_base["Tipo_Mantencion"] == "Correctiva"]["Costo_CLP"].sum()),
            "Costo acumulado",
            "#fee2e2",
        )

    tipo = (
        mant_base
        .groupby("Tipo_Mantencion", as_index=False)["Costo_CLP"]
        .sum()
        .sort_values("Costo_CLP", ascending=False)
    )

    if not tipo.empty:
        total_costo = tipo["Costo_CLP"].sum()
        tipo["Monto"] = tipo["Costo_CLP"].apply(pesos)
        tipo["Porcentaje"] = tipo["Costo_CLP"].apply(
            lambda x: f"{(x / total_costo * 100):.1f}%" if total_costo > 0 else "0.0%"
        )
        tipo["Etiqueta"] = tipo.apply(
            lambda x: f"{x['Tipo_Mantencion']}<br>{x['Porcentaje']}<br>{x['Monto']}",
            axis=1,
        )

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=tipo["Tipo_Mantencion"],
                    values=tipo["Costo_CLP"],
                    hole=0.48,
                    text=tipo["Etiqueta"],
                    textinfo="text",
                    textposition="inside",
                    insidetextorientation="radial",
                    hovertemplate="%{label}<br>%{percent}<br>$ %{value:,.0f}<extra></extra>",
                )
            ]
        )

        fig.update_layout(
            title=dict(
                text="Distribución de costos por tipo de mantención",
                x=0.01,
                xanchor="left",
                y=0.98,
                yanchor="top",
                font=dict(size=16, color=COLOR_TEXTO),
            ),
            showlegend=True,
            legend_title_text="Tipo",
            margin=dict(l=18, r=18, t=42, b=18),
        )

        # Altura menor para que el gráfico de torta quepa completo en la pantalla.
        st.plotly_chart(aplicar_formato_grafico(fig, 340), use_container_width=True)

    if mant_vista.empty:
        st.info("No existen mantenciones para el tipo seleccionado.")
        return

    mostrar = preparar_tabla_mantenciones(mant_vista)
    mostrar_tabla_clara(mostrar, height=420)

def pagina_repuestos(gastos_f):
    st.markdown('<div class="panel-title">Repuestos y Gastos Adicionales</div>', unsafe_allow_html=True)

    gastos_sin_combustible = gastos_no_combustible(gastos_f)

    # Limpia filas vacías antes de graficar o mostrar tabla.
    gastos_sin_combustible = gastos_sin_combustible[
        (gastos_sin_combustible["Equipo"].astype(str).str.lower().str.strip().isin(["", "nan", "none"]) == False)
        | (gastos_sin_combustible["Costo_CLP"] > 0)
        | (gastos_sin_combustible["Fecha"].notna())
    ].copy()

    if gastos_sin_combustible.empty:
        st.info("No existen repuestos o gastos adicionales para el filtro aplicado.")
        return

    tipos = sorted([t for t in gastos_sin_combustible["Tipo_Gasto"].dropna().astype(str).unique() if t.strip() != ""])
    filtro_tipo_gasto = st.selectbox("Filtrar por tipo de gasto", ["Todos"] + tipos)

    gastos_vista = gastos_sin_combustible.copy()
    if filtro_tipo_gasto != "Todos":
        gastos_vista = gastos_vista[gastos_vista["Tipo_Gasto"] == filtro_tipo_gasto].copy()

    resumen = (
        gastos_vista
        .groupby("Clasificacion_Costo", as_index=False)["Costo_CLP"]
        .sum()
        .sort_values("Costo_CLP", ascending=False)
    )

    if not resumen.empty:
        resumen_grafico = resumen.copy()
        resumen_grafico["Costo_Millones"] = resumen_grafico["Costo_CLP"].apply(limpiar_numero) / 1_000_000
        fig = px.bar(
            resumen_grafico,
            x="Clasificacion_Costo",
            y="Costo_Millones",
            text=resumen_grafico["Costo_CLP"].apply(pesos),
            template="plotly_white",
            title="Costo consolidado por tipo de gasto",
            custom_data=["Costo_CLP"],
        )

        fig.update_traces(marker_color="#f59e0b", textposition="outside", hovertemplate="Consolidado: %{x}<br>Monto: $%{customdata[0]:,.0f}<br>Millones CLP: %{y:.2f} M<extra></extra>")
        fig.update_layout(xaxis_title="Consolidado", yaxis_title="Millones CLP")
        fig.update_yaxes(tickformat=",.1f", ticksuffix=" M", separatethousands=True)
        st.plotly_chart(aplicar_formato_grafico(fig, 390), use_container_width=True)

    if gastos_vista.empty:
        st.info("No existen registros para el tipo seleccionado.")
        return

    mostrar = preparar_tabla_repuestos(gastos_vista)
    mostrar_tabla_clara(mostrar, height=450)


def pagina_costos(mant_f, gastos_f, combustible_f):
    st.markdown('<div class="section-head"><div class="panel-title page-section-title">Análisis de Costos</div></div>', unsafe_allow_html=True)

    gastos_sin_combustible = gastos_no_combustible(gastos_f)

    costo_mantenciones = float(mant_f["Costo_CLP"].sum())
    costo_gastos = float(gastos_sin_combustible["Costo_CLP"].sum())
    costo_combustible = float(combustible_f["Costo_Total"].sum()) if "Costo_Total" in combustible_f.columns else 0.0
    # En el tablero principal se excluye combustible del total solicitado para distribución.
    costo_total = costo_mantenciones + costo_gastos

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card("💲", "Total", pesos(costo_total), "Costo acumulado", "#dcfce7")

    with c2:
        kpi_card("🛠️", "Mantenciones", pesos(costo_mantenciones), "Costo mantención", "#dbeafe")

    with c3:
        kpi_card("🧰", "Gastos Adic.", pesos(costo_gastos), "Repuestos, mantenciones y administrativos", "#ede9fe")

    costos_item = construir_consolidado_costos(mant_f, gastos_f)

    fig_donut = crear_donut_costos(costos_item)
    st.plotly_chart(fig_donut, use_container_width=True)


def pagina_proximas(proximas_base, filtro_equipo):
    st.markdown('<div class="section-head"><div class="panel-title page-section-title">Próximas Mantenciones por Km/Horómetro</div></div>', unsafe_allow_html=True)

    if "Proxima_Mantencion" not in proximas_base.columns:
        proximas_base = pd.DataFrame(columns=["Equipo", "Categoria", "Tipo_Mantencion", "Proxima_Mantencion", "Km_Horometro_Actual", "Unidad_Control", "Costo_CLP"])

    proximas = proximas_base.copy()
    proximas["Proxima_Mantencion"] = proximas["Proxima_Mantencion"].apply(limpiar_numero)
    proximas = proximas[proximas["Proxima_Mantencion"] > 0].copy()

    if filtro_equipo != "Todos los equipos":
        proximas = proximas[proximas["Equipo"] == filtro_equipo]

    if proximas.empty:
        st.info("No existen próximas mantenciones registradas por Km/Horómetro.")
        return

    proximas = aplicar_unidad_control_por_equipo(proximas)
    proximas = enriquecer_estado_proximas(proximas)
    proximas["_prioridad"] = proximas["Estado_Control"].apply(prioridad_estado_control)
    proximas = proximas.sort_values(["_prioridad", "Saldo_Restante", "Equipo"], ascending=[True, True, True]).drop(columns=["_prioridad"], errors="ignore")
    proximas = ocultar_columnas_tecnicas(proximas)
    mostrar = preparar_tabla_proximas(proximas)
    mostrar_tabla_clara(mostrar, height=520)


def pagina_alertas(proximas_mantenciones, checklist, documentos, filtro_equipo):
    st.markdown('<div class="section-head"><div class="panel-title page-section-title">Alertas Operacionales</div></div>', unsafe_allow_html=True)

    hoy = pd.Timestamp(datetime.now().date())

    # -----------------------------------------------------
    # Bases seguras: evita errores si una hoja o columna no existe.
    # -----------------------------------------------------
    # Base oficial para alertas de mantención: próximas mantenciones calculadas desde hoja EQUIPOS.
    # Esto permite detectar vencidas por Km/Horómetro aunque la hoja MANTENCIONES no tenga registros.
    mant_base = proximas_mantenciones.copy() if isinstance(proximas_mantenciones, pd.DataFrame) else pd.DataFrame()
    check_base = checklist.copy() if isinstance(checklist, pd.DataFrame) else pd.DataFrame()
    docs_base = documentos.copy() if isinstance(documentos, pd.DataFrame) else pd.DataFrame()

    for col in ["Equipo", "Tipo_Mantencion", "Categoria", "Proveedor", "Descripcion", "Estado_Mantencion", "Documento_Respaldo", "Observacion"]:
        mant_base = asegurar_columna(mant_base, col, "")
    mant_base = asegurar_columna(mant_base, "Fecha", pd.NaT)
    mant_base = asegurar_columna(mant_base, "Proxima_Mantencion", 0)
    mant_base = asegurar_columna(mant_base, "Km_Horometro_Actual", 0)
    mant_base = asegurar_columna(mant_base, "Unidad_Control", "")
    mant_base = asegurar_columna(mant_base, "Costo_CLP", 0)
    mant_base["Proxima_Mantencion"] = mant_base["Proxima_Mantencion"].apply(limpiar_numero)
    mant_base["Fecha"] = mant_base["Fecha"].apply(convertir_fecha)
    mant_base["Costo_CLP"] = mant_base["Costo_CLP"].apply(limpiar_numero)
    mant_base["Equipo"] = mant_base["Equipo"].fillna("").astype(str).str.strip()

    for col in ["Equipo", "Estado_Cierre", "Estado_Checklist", "Observacion", "Accion_Requerida", "Responsable"]:
        check_base = asegurar_columna(check_base, col, "")
    check_base = asegurar_columna(check_base, "Fecha", pd.NaT)
    check_base = asegurar_columna(check_base, "Fecha_Cierre", pd.NaT)
    check_base["Fecha"] = check_base["Fecha"].apply(convertir_fecha)
    check_base["Fecha_Cierre"] = check_base["Fecha_Cierre"].apply(convertir_fecha)
    check_base["Equipo"] = check_base["Equipo"].fillna("").astype(str).str.strip()

    for col in ["Equipo", "Tipo_Documento", "Descripcion", "Estado", "Ruta_Link", "Observacion"]:
        docs_base = asegurar_columna(docs_base, col, "")
    docs_base = asegurar_columna(docs_base, "Fecha", pd.NaT)
    docs_base = asegurar_columna(docs_base, "Vencimiento", pd.NaT)
    docs_base["Fecha"] = docs_base["Fecha"].apply(convertir_fecha)
    docs_base["Vencimiento"] = docs_base["Vencimiento"].apply(convertir_fecha)
    docs_base["Equipo"] = docs_base["Equipo"].fillna("").astype(str).str.strip()

    if filtro_equipo != "Todos los equipos":
        mant_base = mant_base[mant_base["Equipo"] == filtro_equipo].copy()
        check_base = check_base[check_base["Equipo"] == filtro_equipo].copy()
        docs_base = docs_base[docs_base["Equipo"] == filtro_equipo].copy()

    # -----------------------------------------------------
    # Mantenciones por Km/Horómetro: vencidas, próximas críticas y programadas.
    # -----------------------------------------------------
    mant_con_fecha = mant_base[
        (mant_base["Equipo"].str.lower().isin(["", "none", "nan", "sin equipo"]) == False)
        & (mant_base["Proxima_Mantencion"].apply(limpiar_numero) > 0)
    ].copy()
    mant_con_fecha = aplicar_unidad_control_por_equipo(mant_con_fecha)
    mant_con_fecha = enriquecer_estado_proximas(mant_con_fecha)

    mant_vencidas = mant_con_fecha[mant_con_fecha["Saldo_Restante"] <= 0].copy()
    mant_30 = mant_con_fecha[
        (mant_con_fecha["Saldo_Restante"] > 0)
        & (mant_con_fecha["Estado_Control"].isin(["Crítica", "Próxima"]))
    ].copy()

    docs_vencidos = docs_base[
        (docs_base["Equipo"].str.lower().isin(["", "none", "nan", "sin equipo"]) == False)
        & (docs_base["Vencimiento"].notna())
        & (docs_base["Vencimiento"] < hoy)
    ].copy()

    docs_30 = docs_base[
        (docs_base["Equipo"].str.lower().isin(["", "none", "nan", "sin equipo"]) == False)
        & (docs_base["Vencimiento"].notna())
        & (docs_base["Vencimiento"] >= hoy)
        & (docs_base["Vencimiento"] <= hoy + pd.Timedelta(days=30))
    ].copy()

    estado_cierre = check_base["Estado_Cierre"].fillna("").astype(str).str.lower().str.strip()
    check_equipo_valido = check_base["Equipo"].str.lower().isin(["", "none", "nan", "sin equipo"]) == False
    checklist_pendiente = check_base[
        check_equipo_valido
        & (~estado_cierre.isin(["cerrado", "cerrada", "ok", "finalizado", "finalizada", "sin observación", "sin observacion", "sin pendiente", ""] ))
    ].copy()

    # -----------------------------------------------------
    # KPIs principales.
    # -----------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card("🚨", "Mantenciones vencidas", f"{len(mant_vencidas)}", "Atención inmediata", "#fee2e2")

    with c2:
        kpi_card("🟠", "Mantenciones próximas", f"{len(mant_30)}", "Saldo bajo Km/Horómetro", "#ffedd5")

    with c3:
        kpi_card("📄", "Documentos críticos", f"{len(docs_vencidos) + len(docs_30)}", "Vencidos o por vencer", "#e0f2fe")

    with c4:
        kpi_card("✅", "Checklist pendientes", f"{len(checklist_pendiente)}", "Requieren cierre", "#ede9fe")

    # -----------------------------------------------------
    # Resumen ejecutivo de prioridad.
    # -----------------------------------------------------
    total_critico = len(mant_vencidas) + len(docs_vencidos) + len(checklist_pendiente)
    if total_critico == 0 and len(mant_30) == 0 and len(docs_30) == 0:
        st.success("Sin alertas críticas registradas para el filtro actual.")
    elif total_critico > 0:
        st.error(f"Hay {total_critico} alerta(s) crítica(s) que requieren revisión operacional.")
    else:
        st.warning("No hay vencimientos críticos, pero existen mantenciones próximas por saldo bajo de Km/Horómetro.")

    # -----------------------------------------------------
    # Mantenciones vencidas.
    # -----------------------------------------------------
    st.markdown('<div class="panel-title">Mantenciones vencidas</div>', unsafe_allow_html=True)

    if mant_vencidas.empty:
        st.info("No existen mantenciones vencidas para el filtro actual.")
    else:
        mant_vencidas = mant_vencidas.sort_values("Saldo_Restante", ascending=True)
        mostrar_mant = preparar_tabla_proximas(mant_vencidas)
        mostrar_tabla_clara(mostrar_mant, height=260)

    # -----------------------------------------------------
    # Mantenciones próximas por saldo bajo de Km/Horómetro.
    # -----------------------------------------------------
    st.markdown('<div class="panel-title">Mantenciones próximas por Km/Horómetro</div>', unsafe_allow_html=True)

    if mant_30.empty:
        st.info("No existen mantenciones próximas por saldo bajo de Km/Horómetro.")
    else:
        mant_30 = mant_30.sort_values("Saldo_Restante", ascending=True)
        mostrar_30 = preparar_tabla_proximas(mant_30)
        mostrar_tabla_clara(mostrar_30, height=260)

    # -----------------------------------------------------
    # Checklist pendientes.
    # -----------------------------------------------------
    st.markdown('<div class="panel-title">Checklist pendientes</div>', unsafe_allow_html=True)

    if checklist_pendiente.empty:
        st.info("No existen checklist pendientes para el filtro actual.")
    else:
        mostrar_check = checklist_pendiente.copy()
        for col in ["Fecha", "Fecha_Cierre"]:
            if col in mostrar_check.columns:
                mostrar_check[col] = mostrar_check[col].apply(fecha_texto)
        mostrar_check = ocultar_columnas_tecnicas(mostrar_check)
        columnas_check = [
            "Fecha",
            "Equipo",
            "Operador",
            "Estado_Checklist",
            "Observacion",
            "Accion_Requerida",
            "Estado_Cierre",
            "Fecha_Cierre",
        ]
        columnas_check = [c for c in columnas_check if c in mostrar_check.columns]
        mostrar_check = mostrar_check[columnas_check].rename(
            columns={
                "Estado_Checklist": "Estado checklist",
                "Observacion": "Observación",
                "Accion_Requerida": "Acción requerida",
                "Estado_Cierre": "Estado cierre",
                "Fecha_Cierre": "Fecha cierre",
            }
        )
        mostrar_tabla_clara(mostrar_check, height=260)

    # -----------------------------------------------------
    # Documentos vencidos o próximos.
    # -----------------------------------------------------
    st.markdown('<div class="panel-title">Documentos vencidos o próximos 30 días</div>', unsafe_allow_html=True)

    docs_alerta = pd.concat([docs_vencidos, docs_30], ignore_index=True, sort=False)
    if docs_alerta.empty:
        st.info("No existen documentos vencidos o próximos a vencer.")
    else:
        docs_alerta["Días"] = (docs_alerta["Vencimiento"] - hoy).dt.days
        docs_alerta["Estado alerta"] = docs_alerta["Días"].apply(lambda x: "Vencido" if x < 0 else "Por vencer")
        docs_alerta = docs_alerta.sort_values("Días", ascending=True)
        mostrar_docs = docs_alerta.copy()
        for col in ["Fecha", "Vencimiento"]:
            if col in mostrar_docs.columns:
                mostrar_docs[col] = mostrar_docs[col].apply(fecha_texto)
        mostrar_docs = ocultar_columnas_tecnicas(mostrar_docs)
        columnas_docs = [
            "Estado alerta",
            "Fecha",
            "Equipo",
            "Tipo_Documento",
            "Descripcion",
            "Estado",
            "Vencimiento",
            "Días",
            "Ruta_Link",
            "Observacion",
        ]
        columnas_docs = [c for c in columnas_docs if c in mostrar_docs.columns]
        mostrar_docs = mostrar_docs[columnas_docs].rename(
            columns={
                "Tipo_Documento": "Tipo documento",
                "Descripcion": "Descripción",
                "Ruta_Link": "Ruta / enlace",
                "Observacion": "Observación",
            }
        )
        mostrar_tabla_clara(mostrar_docs, height=260)

def pagina_documentos(documentos_f):
    st.markdown('<div class="section-head"><div class="panel-title page-section-title">Control Documental</div></div>', unsafe_allow_html=True)

    if documentos_f.empty:
        st.info("No existen documentos para el filtro aplicado.")
        return

    mostrar = documentos_f.copy()

    for col in ["Fecha", "Vencimiento"]:
        if col in mostrar.columns:
            mostrar[col] = mostrar[col].apply(fecha_texto)

    mostrar_tabla_clara(mostrar, height=520)


# =========================================================
# PANEL PRINCIPAL
# =========================================================

def mostrar_panel():
    fuente_datos, datos = cargar_datos()

    equipos = preparar_equipos(datos["EQUIPOS"])
    equipos_planilla = preparar_equipos(datos.get("EQUIPOS_PLANILLA", datos["EQUIPOS"]))
    mantenciones = preparar_mantenciones(datos["MANTENCIONES"])
    mantenciones_planilla = preparar_mantenciones_planilla(
        datos.get("MANTENCIONES_PLANILLA", pd.DataFrame())
    )
    gastos = preparar_gastos(datos["GASTOS_ADICIONALES"])
    checklist = preparar_checklist(datos["CHECKLIST"])
    combustible = preparar_combustible(datos["COMBUSTIBLE"])
    documentos = preparar_documentos(datos["DOCUMENTOS"])
    proximas_base = construir_proximas_mantenciones(equipos, mantenciones)

    with st.sidebar:
        pagina, filtro_equipo, filtro_contrato, filtro_anio, filtro_mes = construir_menu(
            equipos_planilla, mantenciones_planilla
        )

    # Filtros generales simplificados: solo Equipo y Contrato.
    # Año y Mes quedan siempre en "Todos" para no limitar los registros.
    equipos_planilla_f = filtrar_por_contrato(equipos_planilla, filtro_contrato)
    equipos_planilla_f = filtrar_por_equipo_catalogo(equipos_planilla_f, filtro_equipo, equipos_planilla)

    equipos_f = equipos_planilla_f.copy()

    mant_f = aplicar_filtro_periodo(mantenciones, "Todos los equipos", "Todos", "Todos")
    gastos_f = aplicar_filtro_periodo(gastos, "Todos los equipos", "Todos", "Todos")
    combustible_f = aplicar_filtro_periodo(combustible, "Todos los equipos", "Todos", "Todos")
    checklist_f = aplicar_filtro_periodo(checklist, "Todos los equipos", "Todos", "Todos")
    documentos_f = aplicar_filtro_periodo(documentos, "Todos los equipos", "Todos", "Todos")

    mant_f = filtrar_por_equipo_catalogo(filtrar_por_contrato(mant_f, filtro_contrato), filtro_equipo, equipos_planilla)
    gastos_f = filtrar_por_equipo_catalogo(filtrar_por_contrato(gastos_f, filtro_contrato), filtro_equipo, equipos_planilla)
    combustible_f = filtrar_por_equipo_catalogo(filtrar_por_contrato(combustible_f, filtro_contrato), filtro_equipo, equipos_planilla)
    checklist_f = filtrar_por_equipo_catalogo(filtrar_por_contrato(checklist_f, filtro_contrato), filtro_equipo, equipos_planilla)
    documentos_f = filtrar_por_equipo_catalogo(filtrar_por_contrato(documentos_f, filtro_contrato), filtro_equipo, equipos_planilla)

    if pagina == "📊 Dashboard Ejecutivo":
        titulo_pagina = "Seguimiento y Control de Equipos Móviles"
    else:
        titulo_pagina = (
            pagina.replace("🚚 ", "")
            .replace("🛠️ ", "")
            .replace("🧰 ", "").replace("🧾 ", "")
            .replace("💰 ", "")
            .replace("📅 ", "")
            .replace("🔔 ", "")
            .replace("📁 ", "")
        )

    encabezado(titulo_pagina)

    if pagina == "📊 Dashboard Ejecutivo":
        pagina_dashboard(equipos_f, mant_f, gastos_f, combustible_f, proximas_base, filtro_equipo)

    elif pagina == "🚚 Equipos":
        pagina_equipos(equipos_planilla_f)

    elif pagina == "🛠️ Intervenciones":
        pagina_mantenciones(mant_f)

    elif pagina == "📁 Documentacion":
        pagina_documentos(documentos_f)

    st.markdown(
        f"""
        <div style="text-align:center; color:#64748b; font-size:12px; padding:22px; line-height:1.55;">
            <div>Panel desarrollado por.</div>
            <div><b>Ricardo Grez – Contract Manager | SAIVAM</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# CORRECCIÓN FINAL V3.7
# - Sidebar fijo sin montarse sobre el contenido principal.
# - Menú y filtros visibles dentro del panel izquierdo.
# - Montos siempre con signo $ a la izquierda.
# =========================================================

_buscar_imagen_por_nombre_original = buscar_imagen_por_nombre

def buscar_imagen_por_nombre(nombre_base):
    """Busca imágenes evitando devolver carpetas."""
    if not nombre_base or str(nombre_base).strip().lower() in ["", "nan", "none"]:
        return None

    nombre_base = str(nombre_base).strip()

    # Casos directos con extensión o archivo sin extensión.
    if os.path.isfile(nombre_base):
        return nombre_base

    ruta = _buscar_imagen_por_nombre_original(nombre_base)

    if ruta and os.path.isfile(ruta):
        return ruta

    return None


def pesos(valor):
    """Formato CLP único para toda la aplicación: $ a la izquierda."""
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " $"
    except Exception:
        return "0 $"


def pesos_html(valor):
    """Formato CLP para HTML/Plotly: $ a la izquierda, sin barras ni dos puntos."""
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " $"
    except Exception:
        return "0 $"


def crear_donut_costos(costos_item):
    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=costos_item["Item"],
            values=costos_item["Costo"],
            hole=0.64,
            marker=dict(
                colors=["#2563eb", "#ffb020", "#55c595"],
                line=dict(color="white", width=2),
            ),
            textinfo="percent",
            textposition="inside",
            insidetextorientation="auto",
            textfont=dict(color="white", size=14, family="Arial Black"),
            hovertemplate="<b>%{label}</b><br>Monto: %{customdata}<br>Participación: %{percent}<extra></extra>",
            customdata=[pesos(v) for v in costos_item["Costo"]],
        )
    )

    total = float(costos_item["Costo"].sum())

    fig.update_layout(
        title="Distribución de Costos",
        height=350,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=COLOR_TEXTO),
        margin=dict(l=10, r=10, t=45, b=10),
        annotations=[
            dict(
                text="Total<br><b>" + pesos(total) + "</b>",
                x=0.5,
                y=0.5,
                font_size=15,
                font_color="#0f172a",
                showarrow=False,
            )
        ],
        legend=dict(orientation="v", x=1.02, y=0.72, font=dict(size=12)),
        uniformtext_minsize=11,
        uniformtext_mode="hide",
    )

    return fig


_aplicar_estilo_base = aplicar_estilo

def aplicar_estilo():
    """Aplica el estilo base y luego fuerza los ajustes finales de estructura."""
    _aplicar_estilo_base()

    css_final = """
<style>
:root {
    --menu-panel-width-final: 330px;
    --menu-inner-width-final: 286px;
}

/* Sidebar fijo y siempre visible */
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    left: 0 !important;
    top: 0 !important;
    bottom: 0 !important;
    width: var(--menu-panel-width-final) !important;
    min-width: var(--menu-panel-width-final) !important;
    max-width: var(--menu-panel-width-final) !important;
    height: 100vh !important;
    background: #020617 !important;
    border-right: 1px solid rgba(147, 197, 253, 0.34) !important;
    z-index: 1000 !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    transform: none !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: var(--menu-panel-width-final) !important;
    min-width: var(--menu-panel-width-final) !important;
    max-width: var(--menu-panel-width-final) !important;
    background: #020617 !important;
    padding: 18px 18px 24px 18px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

/* Oculta controles de colapso para que el menú no desaparezca */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[title="Collapse sidebar"],
button[title="Close sidebar"],
button[aria-label="Close sidebar"],
button[aria-label="Collapse sidebar"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

/* El contenido principal parte después del menú: evita que se monte encima */
div[data-testid="stMain"],
main,
section.main,
[data-testid="stAppViewContainer"] > .main {
    margin-left: var(--menu-panel-width-final) !important;
    width: calc(100vw - var(--menu-panel-width-final)) !important;
    max-width: calc(100vw - var(--menu-panel-width-final)) !important;
    min-width: 1320px !important;
    box-sizing: border-box !important;
    overflow-x: visible !important;
}

.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"] {
    max-width: none !important;
    min-width: 1320px !important;
    padding-left: 26px !important;
    padding-right: 26px !important;
    padding-top: 0px !important;
    box-sizing: border-box !important;
}

[data-testid="stAppViewContainer"],
.stApp {
    overflow-x: auto !important;
    background: #eef3f9 !important;
}

/* Mantiene las columnas en orden al agrandar/achicar o usar zoom */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: stretch !important;
}

.kpi-card {
    min-width: 215px !important;
}

.title-main {
    white-space: nowrap !important;
    overflow: visible !important;
    line-height: 1.05 !important;
}

/* Menú: botones completos dentro del panel */
section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-width-final) !important;
    max-width: var(--menu-inner-width-final) !important;
    min-width: var(--menu-inner-width-final) !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: var(--menu-inner-width-final) !important;
    max-width: var(--menu-inner-width-final) !important;
    min-height: 50px !important;
    padding: 10px 12px !important;
    border-radius: 13px !important;
    background: rgba(15, 23, 42, 0.72) !important;
    border: 1px solid rgba(147, 197, 253, 0.30) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 950 !important;
    text-align: left !important;
    white-space: normal !important;
    overflow: visible !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.85) !important;
}

section[data-testid="stSidebar"] .menu-active-item {
    min-height: 50px !important;
    padding: 12px 12px !important;
    display: flex !important;
    align-items: center !important;
    border-radius: 13px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%) !important;
    border: 1px solid rgba(219, 234, 254, 0.95) !important;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.38) !important;
    font-size: 15px !important;
    font-weight: 950 !important;
    line-height: 1.25 !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.70) !important;
    white-space: normal !important;
}

/* Selectores de filtros dentro del menú */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label,
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label * {
    color: #dbeafe !important;
    -webkit-text-fill-color: #dbeafe !important;
    opacity: 1 !important;
    font-weight: 950 !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #ffffff !important;
    border-radius: 12px !important;
    min-height: 44px !important;
    overflow: hidden !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #0f172a !important;
    -webkit-text-fill-color: #0f172a !important;
    font-weight: 800 !important;
}

/* Montos y textos fuertes */
.kpi-value,
[data-testid="stDataFrame"] {
    font-variant-numeric: tabular-nums !important;
}

</style>
"""
    st.markdown(css_final, unsafe_allow_html=True)


# =========================================================
# AJUSTE FINAL V3.8
# - Sidebar separado del contenido, sin superponerse.
# - Menú fijo/sticky y más arriba.
# - Montos CLP con $ a la izquierda.
# =========================================================



def pesos(valor):
    """Formato CLP definitivo: $ a la izquierda."""
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " $"
    except Exception:
        return "0 $"


def pesos_html(valor):
    """Formato CLP definitivo para HTML y Plotly."""
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " $"
    except Exception:
        return "0 $"


_aplicar_estilo_v37 = aplicar_estilo

def aplicar_estilo():
    _aplicar_estilo_v37()

    css_v38 = """
<style>
:root {
    --menu-width-v38: 318px;
    --menu-inner-v38: 278px;
    --content-min-v38: 1320px;
}

/* Página base con scroll horizontal solo si la ventana queda muy angosta */
html,
body,
.stApp,
[data-testid="stAppViewContainer"] {
    background: #eef3f9 !important;
    overflow-x: auto !important;
}

/* Sidebar separado del contenido principal: NO queda encima */
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: sticky !important;
    top: 0 !important;
    left: 0 !important;
    flex: 0 0 var(--menu-width-v38) !important;
    width: var(--menu-width-v38) !important;
    min-width: var(--menu-width-v38) !important;
    max-width: var(--menu-width-v38) !important;
    height: 100vh !important;
    min-height: 100vh !important;
    background: #020617 !important;
    border-right: 1px solid rgba(147, 197, 253, 0.34) !important;
    box-shadow: none !important;
    z-index: 20 !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    transform: none !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: var(--menu-width-v38) !important;
    min-width: var(--menu-width-v38) !important;
    max-width: var(--menu-width-v38) !important;
    background: #020617 !important;
    padding: 8px 14px 16px 14px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

/* Evita controles de colapso que achican el menú */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[title="Collapse sidebar"],
button[title="Close sidebar"],
button[aria-label="Close sidebar"],
button[aria-label="Collapse sidebar"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

/* Contenido principal: queda al lado del menú, nunca debajo */
[data-testid="stAppViewContainer"] {
    display: flex !important;
    align-items: stretch !important;
}

[data-testid="stAppViewContainer"] > .main,
div[data-testid="stMain"],
main,
section.main {
    position: relative !important;
    margin-left: 0 !important;
    flex: 1 0 auto !important;
    width: auto !important;
    min-width: var(--content-min-v38) !important;
    max-width: none !important;
    box-sizing: border-box !important;
    overflow: visible !important;
    background: #eef3f9 !important;
    z-index: 2 !important;
}

.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"] {
    max-width: none !important;
    min-width: var(--content-min-v38) !important;
    padding-top: 0px !important;
    padding-left: 28px !important;
    padding-right: 28px !important;
    padding-bottom: 26px !important;
    box-sizing: border-box !important;
}

/* Menú más arriba y con ancho completo dentro del panel */
section[data-testid="stSidebar"] .menu-brand {
    margin-top: 0px !important;
    margin-bottom: 12px !important;
}

section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-v38) !important;
    max-width: var(--menu-inner-v38) !important;
    min-width: var(--menu-inner-v38) !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-v38) !important;
    min-height: 46px !important;
    padding: 9px 12px !important;
    border-radius: 13px !important;
    font-size: 14.8px !important;
    font-weight: 950 !important;
    white-space: normal !important;
    overflow: visible !important;
    line-height: 1.20 !important;
    box-sizing: border-box !important;
}

/* Mantiene columnas y tarjetas sin romper orden visual */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: stretch !important;
}

.kpi-card {
    min-width: 215px !important;
}

.title-main {
    white-space: nowrap !important;
    overflow: visible !important;
}

</style>
"""
    st.markdown(css_v38, unsafe_allow_html=True)


# =========================================================
# AJUSTE FINAL V3.9
# - Menú izquierdo más ancho para que los ítems calcen completos.
# - Montos CLP con signo $ a la izquierda en tarjetas, tablas y gráficos.
# - Total del gráfico donut sin ':' ni barras.
# =========================================================

VERSION = "2.9"

def pesos(valor):
    """Formato CLP final: signo $ a la izquierda."""
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " $"
    except Exception:
        return "0 $"


def pesos_html(valor):
    """Formato CLP para HTML/Plotly sin activar MathJax."""
    try:
        return "<span>&#36;</span>&nbsp;" + f"{int(round(float(valor))):,}".replace(",", ".")
    except Exception:
        return "<span>&#36;</span>&nbsp;0"


def crear_donut_costos(costos_item):
    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=costos_item["Item"],
            values=costos_item["Costo"],
            hole=0.64,
            marker=dict(
                colors=["#2563eb", "#ffb020", "#55c595"],
                line=dict(color="white", width=2),
            ),
            textinfo="percent",
            textposition="inside",
            insidetextorientation="auto",
            textfont=dict(color="white", size=14, family="Arial Black"),
            hovertemplate="<b>%{label}</b><br>Monto: %{customdata}<br>Participación: %{percent}<extra></extra>",
            customdata=[pesos(v) for v in costos_item["Costo"]],
        )
    )

    total = float(costos_item["Costo"].sum())

    fig.update_layout(
        title="Distribución de Costos",
        height=350,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=COLOR_TEXTO),
        margin=dict(l=10, r=10, t=45, b=10),
        annotations=[
            dict(
                text="Total<br><b>" + pesos_html(total) + "</b>",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                font_size=15,
                font_color="#0f172a",
                showarrow=False,
                align="center",
            )
        ],
        legend=dict(orientation="v", x=1.02, y=0.72, font=dict(size=12)),
        uniformtext_minsize=11,
        uniformtext_mode="hide",
    )

    return fig


_aplicar_estilo_v38_final = aplicar_estilo

def aplicar_estilo():
    _aplicar_estilo_v38_final()

    st.markdown(
        """
<style>
:root {
    --menu-width-v39: 370px;
    --menu-inner-v39: 320px;
    --content-min-v39: 1320px;
}

/* Sidebar más ancho, fijo y separado del contenido */
section[data-testid="stSidebar"] {
    width: var(--menu-width-v39) !important;
    min-width: var(--menu-width-v39) !important;
    max-width: var(--menu-width-v39) !important;
    flex: 0 0 var(--menu-width-v39) !important;
    position: sticky !important;
    top: 0 !important;
    left: 0 !important;
    height: 100vh !important;
    min-height: 100vh !important;
    background: #020617 !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    z-index: 30 !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: var(--menu-width-v39) !important;
    min-width: var(--menu-width-v39) !important;
    max-width: var(--menu-width-v39) !important;
    padding: 8px 24px 18px 24px !important;
    background: #020617 !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

/* El contenido principal queda al lado del menú, no debajo */
[data-testid="stAppViewContainer"] {
    display: flex !important;
    align-items: stretch !important;
    overflow-x: auto !important;
}

[data-testid="stAppViewContainer"] > .main,
div[data-testid="stMain"],
main,
section.main {
    margin-left: 0 !important;
    flex: 1 0 auto !important;
    min-width: var(--content-min-v39) !important;
    width: auto !important;
    max-width: none !important;
    position: relative !important;
    z-index: 2 !important;
    background: #eef3f9 !important;
    box-sizing: border-box !important;
}

.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"] {
    max-width: none !important;
    min-width: var(--content-min-v39) !important;
    padding-top: 0px !important;
    padding-left: 30px !important;
    padding-right: 30px !important;
    box-sizing: border-box !important;
}

/* Menú más arriba y con ancho suficiente */
section[data-testid="stSidebar"] .menu-brand {
    margin-top: 0px !important;
    margin-bottom: 10px !important;
}

section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-v39) !important;
    min-width: var(--menu-inner-v39) !important;
    max-width: var(--menu-inner-v39) !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-v39) !important;
    min-width: var(--menu-inner-v39) !important;
    max-width: var(--menu-inner-v39) !important;
    min-height: 50px !important;
    padding: 10px 14px !important;
    border-radius: 13px !important;
    font-size: 15px !important;
    line-height: 1.18 !important;
    font-weight: 950 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    box-sizing: border-box !important;
}

/* Selectores de filtro completos */
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    min-height: 48px !important;
    height: 48px !important;
    border-radius: 12px !important;
}

/* Evita que la cabecera o tarjetas se monten al cambiar zoom */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: stretch !important;
}

.kpi-card {
    min-width: 215px !important;
}

.title-main {
    white-space: nowrap !important;
    text-align: center !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# AJUSTE FINAL V4.0
# - Menú izquierdo con enunciados alineados más a la izquierda.
# - Panel izquierdo más estable y separado del contenido principal.
# - Monto total del gráfico donut con signo $ a la izquierda.
# =========================================================

VERSION = "2.9"


def pesos(valor):
    """Formato CLP: signo $ siempre a la izquierda."""
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " $"
    except Exception:
        return "0 $"


def pesos_html(valor):
    """Formato CLP para textos HTML/Plotly, evitando que $ sea interpretado como fórmula."""
    try:
        return "&#36;&#8203; " + f"{int(round(float(valor))):,}".replace(",", ".")
    except Exception:
        return "&#36;&#8203; 0"


def kpi_card(icono, titulo, valor, subtitulo, color_fondo):
    """Tarjeta KPI con corrección de montos que pudieran venir con $ a la derecha."""
    valor_txt = str(valor).strip()

    if valor_txt.endswith("$"):
        valor_txt = "$ " + valor_txt.replace("$", "").strip()

    st.markdown(
        f"""
<div class="kpi-card">
    <div class="kpi-icon" style="background:{color_fondo};">{icono}</div>
    <div class="kpi-title">{titulo}</div>
    <div class="kpi-value">{valor_txt}</div>
    <div class="kpi-sub">{subtitulo}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def crear_donut_costos(costos_item):
    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=costos_item["Item"],
            values=costos_item["Costo"],
            hole=0.64,
            marker=dict(
                colors=["#2563eb", "#ffb020", "#55c595"],
                line=dict(color="white", width=2),
            ),
            textinfo="percent",
            textposition="inside",
            insidetextorientation="auto",
            textfont=dict(color="white", size=14, family="Arial Black"),
            hovertemplate="<b>%{label}</b><br>Monto: %{customdata}<br>Participación: %{percent}<extra></extra>",
            customdata=[pesos(v) for v in costos_item["Costo"]],
        )
    )

    total = float(costos_item["Costo"].sum())

    fig.update_layout(
        title="Distribución de Costos",
        height=350,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=COLOR_TEXTO),
        margin=dict(l=10, r=10, t=45, b=10),
        annotations=[
            dict(
                text="Total<br><b>" + pesos_html(total) + "</b>",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                font_size=15,
                font_color="#0f172a",
                showarrow=False,
                align="center",
            )
        ],
        legend=dict(orientation="v", x=1.02, y=0.72, font=dict(size=12)),
        uniformtext_minsize=11,
        uniformtext_mode="hide",
    )

    return fig


_aplicar_estilo_v39_final = aplicar_estilo


def aplicar_estilo():
    _aplicar_estilo_v39_final()

    st.markdown(
        """
<style>
:root {
    --menu-width-v40: 390px;
    --menu-inner-v40: 360px;
    --content-min-v40: 1320px;
}

/* Panel izquierdo fijo, más ancho y separado de la página principal */
section[data-testid="stSidebar"] {
    width: var(--menu-width-v40) !important;
    min-width: var(--menu-width-v40) !important;
    max-width: var(--menu-width-v40) !important;
    flex: 0 0 var(--menu-width-v40) !important;
    position: sticky !important;
    top: 0 !important;
    left: 0 !important;
    height: 100vh !important;
    min-height: 100vh !important;
    background: #020617 !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    z-index: 30 !important;
    box-sizing: border-box !important;
    border-right: 1px solid rgba(147, 197, 253, 0.35) !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: var(--menu-width-v40) !important;
    min-width: var(--menu-width-v40) !important;
    max-width: var(--menu-width-v40) !important;
    padding: 6px 12px 18px 12px !important;
    margin: 0 !important;
    background: #020617 !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

/* Quita márgenes internos de Streamlit que desplazaban los enunciados hacia el centro */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"],
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div,
section[data-testid="stSidebar"] div[data-testid="element-container"] {
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    width: var(--menu-inner-v40) !important;
    max-width: var(--menu-inner-v40) !important;
    box-sizing: border-box !important;
}

/* Contenido principal al lado del menú, no debajo */
[data-testid="stAppViewContainer"] {
    display: flex !important;
    align-items: stretch !important;
    overflow-x: auto !important;
}

[data-testid="stAppViewContainer"] > .main,
div[data-testid="stMain"],
main,
section.main {
    margin-left: 0 !important;
    flex: 1 0 auto !important;
    min-width: var(--content-min-v40) !important;
    width: auto !important;
    max-width: none !important;
    position: relative !important;
    z-index: 2 !important;
    background: #eef3f9 !important;
    box-sizing: border-box !important;
}

.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"] {
    max-width: none !important;
    min-width: var(--content-min-v40) !important;
    padding-top: 0 !important;
    padding-left: 24px !important;
    padding-right: 24px !important;
    box-sizing: border-box !important;
}

/* Encabezado del menú más arriba y alineado a la izquierda */
section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-brand,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-v40) !important;
    min-width: var(--menu-inner-v40) !important;
    max-width: var(--menu-inner-v40) !important;
    margin-left: 0 !important;
    margin-left: auto !important;
    margin-right: auto !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] .menu-brand {
    margin-top: 0 !important;
    margin-bottom: 10px !important;
    padding-left: 0 !important;
    justify-content: flex-start !important;
}

/* Ítems del menú: enunciados más a la izquierda */
section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-v40) !important;
    min-width: var(--menu-inner-v40) !important;
    max-width: var(--menu-inner-v40) !important;
    min-height: 50px !important;
    padding: 10px 16px !important;
    border-radius: 13px !important;
    font-size: 15px !important;
    line-height: 1.18 !important;
    font-weight: 950 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button *,
section[data-testid="stSidebar"] div[data-testid="stButton"] button p,
section[data-testid="stSidebar"] .menu-active-item,
section[data-testid="stSidebar"] .menu-active-item * {
    text-align: left !important;
    justify-content: flex-start !important;
    align-items: center !important;
    margin-left: 0 !important;
    margin-right: auto !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
}

/* Filtros completos y alineados */
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    min-height: 48px !important;
    height: 48px !important;
    border-radius: 12px !important;
}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label,
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label * {
    text-align: left !important;
    margin-left: 0 !important;
}

/* Reafirma que los montos de tarjetas no queden invertidos visualmente */
.kpi-value {
    direction: ltr !important;
    unicode-bidi: isolate !important;
    text-align: left !important;
}

/* Mantiene estructura al cambiar zoom */
div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: stretch !important;
}

.title-main {
    white-space: nowrap !important;
    text-align: center !important;
}

/* AJUSTE FINAL V4.1: menú compacto y sin barra vertical visible. */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    overflow-y: hidden !important;
    overflow-x: hidden !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
}

section[data-testid="stSidebar"]::-webkit-scrollbar,
section[data-testid="stSidebar"] *::-webkit-scrollbar {
    width: 0px !important;
    height: 0px !important;
    display: none !important;
    background: transparent !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 0px !important;
    padding-bottom: 10px !important;
}

section[data-testid="stSidebar"] .menu-brand {
    margin-top: 0px !important;
    margin-bottom: 8px !important;
}

section[data-testid="stSidebar"] .menu-line {
    margin-top: 8px !important;
    margin-bottom: 10px !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] .menu-active-item {
    min-height: 46px !important;
    height: 46px !important;
    margin-bottom: 5px !important;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    min-height: 44px !important;
    height: 44px !important;
}

section[data-testid="stSidebar"] .menu-footer-box {
    margin-top: 10px !important;
    padding: 12px !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# AJUSTE FINAL V4.2
# Refuerza que el menú izquierdo no muestre barra de desplazamiento.
# =========================================================

VERSION = "2.9"

_aplicar_estilo_v41_final = aplicar_estilo

def aplicar_estilo():
    _aplicar_estilo_v41_final()

    st.markdown(
        """
<style>
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    overflow-y: hidden !important;
    overflow-x: hidden !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
}

section[data-testid="stSidebar"]::-webkit-scrollbar,
section[data-testid="stSidebar"] *::-webkit-scrollbar {
    width: 0 !important;
    height: 0 !important;
    display: none !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# AJUSTE FINAL V4.7
# - Mantiene montos con signo $ a la izquierda.
# =========================================================

VERSION = "2.9"

_aplicar_estilo_v45_base = aplicar_estilo


def pesos(valor):
    """Formato CLP: signo $ siempre a la izquierda."""
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " $"
    except Exception:
        return "0 $"


def pesos_html(valor):
    """Formato CLP para HTML/Plotly."""
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " $"
    except Exception:
        return "0 $"


def kpi_card(icono, titulo, valor, subtitulo, color_fondo):
    """Tarjeta KPI con corrección para que $ quede a la izquierda."""
    valor_txt = str(valor).strip()

    if valor_txt.endswith("$"):
        valor_txt = "$ " + valor_txt.replace("$", "").strip()

    if valor_txt.startswith("＄"):
        valor_txt = "$ " + valor_txt.replace("＄", "").strip()

    st.markdown(
        f"""
<div class="kpi-card">
    <div class="kpi-icon" style="background:{color_fondo};">{icono}</div>
    <div class="kpi-title">{titulo}</div>
    <div class="kpi-value">{valor_txt}</div>
    <div class="kpi-sub">{subtitulo}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def crear_donut_costos(costos_item):
    fig = go.Figure()

    fig.add_trace(
        go.Pie(
            labels=costos_item["Item"],
            values=costos_item["Costo"],
            hole=0.64,
            marker=dict(
                colors=["#2563eb", "#ffb020", "#55c595"],
                line=dict(color="white", width=2),
            ),
            textinfo="percent",
            textposition="inside",
            insidetextorientation="auto",
            textfont=dict(color="white", size=14, family="Arial Black"),
            hovertemplate="<b>%{label}</b><br>Monto: %{customdata}<br>Participación: %{percent}<extra></extra>",
            customdata=[pesos(v) for v in costos_item["Costo"]],
        )
    )

    total = float(costos_item["Costo"].sum())

    fig.update_layout(
        title="Distribución de Costos",
        height=350,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color=COLOR_TEXTO),
        margin=dict(l=10, r=10, t=45, b=10),
        annotations=[
            dict(
                text="Total<br><b>" + pesos_html(total) + "</b>",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                font_size=15,
                font_color="#0f172a",
                showarrow=False,
                align="center",
            )
        ],
        legend=dict(orientation="v", x=1.02, y=0.72, font=dict(size=12)),
        uniformtext_minsize=11,
        uniformtext_mode="hide",
    )

    return fig


def aplicar_estilo():
    _aplicar_estilo_v45_base()

    st.markdown(
        """
<style>
/* =========================================================
   AJUSTE FINAL V5.0: MENÚ MÁS ANGOSTO Y MÁS ARRIBA
   ========================================================= */
:root {
    --menu-panel-width-final: 300px !important;
    --menu-inner-width-final: 262px !important;
    --menu-width-v38: 300px !important;
    --menu-inner-v38: 262px !important;
    --menu-panel-width: 300px !important;
    --menu-inner-width: 262px !important;
}

section[data-testid="stSidebar"] {
    width: 300px !important;
    min-width: 300px !important;
    max-width: 300px !important;
    padding-top: 0px !important;
    overflow-y: hidden !important;
    overflow-x: hidden !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: 300px !important;
    min-width: 300px !important;
    max-width: 300px !important;
    padding: 8px 12px 12px 12px !important;
    overflow-y: hidden !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
}

/* Sube cabecera y nombres del menú */
section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-brand {
    width: 262px !important;
    max-width: 262px !important;
    margin-top: 0px !important;
    margin-bottom: 8px !important;
    padding-top: 0px !important;
}

section[data-testid="stSidebar"] .menu-brand {
    transform: translateY(-6px) !important;
}

section[data-testid="stSidebar"] .menu-line {
    width: 262px !important;
    max-width: 262px !important;
    margin: 6px 0 8px 0 !important;
}

section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .menu-active-item {
    width: 262px !important;
    max-width: 262px !important;
    min-width: 262px !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] {
    margin-bottom: 2px !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] .menu-active-item {
    width: 262px !important;
    max-width: 262px !important;
    min-width: 262px !important;
    min-height: 43px !important;
    height: 43px !important;
    padding: 8px 12px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    font-size: 14px !important;
    line-height: 1.1 !important;
}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] {
    margin-top: 0px !important;
    margin-bottom: 4px !important;
}

section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    min-height: 40px !important;
    height: 40px !important;
}

section[data-testid="stSidebar"] .menu-footer-box {
    margin-top: 8px !important;
    padding: 10px 12px !important;
}

section[data-testid="stSidebar"] .menu-info {
    font-size: 11.4px !important;
    line-height: 1.45 !important;
}

/* Contenido principal separado según el nuevo ancho del menú */
[data-testid="stAppViewContainer"] > .main,
div[data-testid="stMain"],
section.main,
main {
    margin-left: 300px !important;
    width: calc(100vw - 300px) !important;
    max-width: calc(100vw - 300px) !important;
}

.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"] {
    padding-left: 24px !important;
    padding-right: 24px !important;
}


@media (max-width: 1100px) {
    section[data-testid="stSidebar"] {
        width: 300px !important;
        min-width: 300px !important;
        max-width: 300px !important;
    }

    [data-testid="stAppViewContainer"] > .main,
    div[data-testid="stMain"],
    section.main,
    main {
        margin-left: 300px !important;
        width: calc(100vw - 300px) !important;
        max-width: calc(100vw - 300px) !important;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# EJECUCIÓN FINAL V4.8
# Importante: se ejecuta al final para que el último aplicar_estilo()
# =========================================================

aplicar_estilo()

# =========================================================
# AJUSTE FINAL MENÚ IZQUIERDO - SIN CAMBIAR ANCHO
# Corrige espacio superior, título y separación entre items.
# =========================================================
st.markdown(
    """
<style>
/* Elimina el espacio superior del sidebar sin modificar su ancho */
section[data-testid="stSidebar"] {
    top: 0px !important;
    padding-top: 0px !important;
    margin-top: 0px !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 4px !important;
    margin-top: 0px !important;
}

/* Quita márgenes internos que Streamlit deja arriba */
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div,
section[data-testid="stSidebar"] div[data-testid="element-container"] {
    padding-top: 0px !important;
    margin-top: 0px !important;
}

/* Título del menú claro y sin corte */
section[data-testid="stSidebar"] .menu-panel-content {
    margin-top: 0px !important;
    padding-top: 0px !important;
    overflow: visible !important;
}

section[data-testid="stSidebar"] .menu-brand {
    transform: none !important;
    margin-top: 4px !important;
    margin-bottom: 10px !important;
    padding-top: 0px !important;
    min-height: 52px !important;
    overflow: visible !important;
    align-items: center !important;
}

section[data-testid="stSidebar"] .menu-icon {
    width: 48px !important;
    height: 48px !important;
    min-width: 48px !important;
    flex: 0 0 48px !important;
    font-size: 25px !important;
}

section[data-testid="stSidebar"] .menu-icon-img {
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    flex: 0 0 44px !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    border-radius: 16px !important;
    overflow: hidden !important;
}

section[data-testid="stSidebar"] .menu-icon-img img {
    width: 100% !important;
    height: 100% !important;
    object-fit: contain !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

section[data-testid="stSidebar"] .menu-title,
section[data-testid="stSidebar"] .menu-title * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 12.6px !important;
    line-height: 1.18 !important;
    font-weight: 950 !important;
    letter-spacing: 0.25px !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
}

section[data-testid="stSidebar"] .menu-subtitle,
section[data-testid="stSidebar"] .menu-subtitle * {
    color: #bfdbfe !important;
    -webkit-text-fill-color: #bfdbfe !important;
    font-size: 10.8px !important;
    line-height: 1.15 !important;
    font-weight: 950 !important;
    margin-top: 4px !important;
    white-space: normal !important;
    overflow: visible !important;
}

/* Línea bajo título más ordenada */
section[data-testid="stSidebar"] .menu-line {
    margin-top: 8px !important;
    margin-bottom: 12px !important;
}

/* Separación correcta entre Dashboard Ejecutivo y Equipos */
section[data-testid="stSidebar"] .menu-active-item {
    min-height: 43px !important;
    height: auto !important;
    display: flex !important;
    align-items: center !important;
    margin-top: 0px !important;
    margin-bottom: 10px !important;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
    line-height: 1.20 !important;
    overflow: hidden !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] {
    margin-top: 0px !important;
    margin-bottom: 8px !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    min-height: 43px !important;
    height: auto !important;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
    line-height: 1.20 !important;
    display: flex !important;
    align-items: center !important;
}

/* Mantiene todos los textos del menú legibles */
section[data-testid="stSidebar"] .menu-active-item,
section[data-testid="stSidebar"] .menu-active-item *,
section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] div[data-testid="stButton"] button * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
    font-weight: 950 !important;
}
</style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# CORRECCIÓN DEFINITIVA MENÚ IZQUIERDO - SIN ESPACIO SUPERIOR
# No modifica el ancho del menú. Solo sube el contenido interno.
# =========================================================
st.markdown(
    """
<style>
/* 1) Sidebar pegado arriba */
section[data-testid="stSidebar"] {
    top: 0px !important;
    margin-top: 0px !important;
    padding-top: 0px !important;
}

/* 2) El contenedor interno de Streamlit a veces deja un espacio invisible arriba.
      Este ajuste sube TODO el contenido del menú sin tocar el ancho. */
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 0px !important;
    margin-top: 0px !important;
    transform: none !important;
}

/* 3) Evita que el primer bloque agregue margen superior */
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > div:first-child,
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]:first-child,
section[data-testid="stSidebar"] div[data-testid="element-container"]:first-child {
    padding-top: 0px !important;
    margin-top: 0px !important;
}

/* 4) Cabecera clara, visible y sin corte */
section[data-testid="stSidebar"] .menu-panel-content {
    margin-top: 0px !important;
    padding-top: 0px !important;
    overflow: visible !important;
}

section[data-testid="stSidebar"] .menu-brand {
    margin-top: 0px !important;
    margin-bottom: 8px !important;
    padding-top: 0px !important;
    transform: none !important;
    min-height: 52px !important;
    align-items: center !important;
    overflow: visible !important;
}

section[data-testid="stSidebar"] .menu-title,
section[data-testid="stSidebar"] .menu-title * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
    font-size: 12.6px !important;
    line-height: 1.15 !important;
    font-weight: 950 !important;
    letter-spacing: 0.20px !important;
    white-space: normal !important;
    overflow: visible !important;
}

section[data-testid="stSidebar"] .menu-subtitle,
section[data-testid="stSidebar"] .menu-subtitle * {
    color: #bfdbfe !important;
    -webkit-text-fill-color: #bfdbfe !important;
    opacity: 1 !important;
    font-size: 10.8px !important;
    line-height: 1.15 !important;
    font-weight: 950 !important;
    margin-top: 4px !important;
    white-space: normal !important;
    overflow: visible !important;
}

/* 5) Línea y separación entre Dashboard Ejecutivo y Equipos */
section[data-testid="stSidebar"] .menu-line {
    margin-top: 8px !important;
    margin-bottom: 12px !important;
}

section[data-testid="stSidebar"] .menu-active-item {
    margin-top: 0px !important;
    margin-bottom: 10px !important;
    min-height: 43px !important;
    height: auto !important;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
    display: flex !important;
    align-items: center !important;
    line-height: 1.20 !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] {
    margin-top: 0px !important;
    margin-bottom: 8px !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    min-height: 43px !important;
    height: auto !important;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
    display: flex !important;
    align-items: center !important;
    line-height: 1.20 !important;
}

/* 6) En pantallas bajas, deja scroll vertical para que no se pierdan filtros inferiores */
section[data-testid="stSidebar"] {
    overflow-y: auto !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE V5.1 - COSTOS, DOCUMENTOS Y GASTOS COMPLEMENTARIOS
# =========================================================

VERSION = "2.9"


def pesos(valor):
    """Formato CLP único: signo $ siempre a la izquierda."""
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".") + " $"
    except Exception:
        return "0 $"


def pesos_html(valor):
    """Formato CLP para textos HTML/Plotly con $ a la izquierda."""
    return pesos(valor)


def kpi_card(icono, titulo, valor, subtitulo, color_fondo):
    """Tarjeta KPI: corrige cualquier monto que venga con $ al final."""
    valor_txt = str(valor).strip()
    if valor_txt.endswith("$"):
        valor_txt = "$ " + valor_txt.replace("$", "").strip()
    if valor_txt.startswith("＄"):
        valor_txt = "$ " + valor_txt.replace("＄", "").strip()
    st.markdown(
        f"""
<div class="kpi-card">
    <div class="kpi-icon" style="background:{color_fondo};">{icono}</div>
    <div class="kpi-title">{escape_html(titulo)}</div>
    <div class="kpi-value">{escape_html(valor_txt)}</div>
    <div class="kpi-sub">{escape_html(subtitulo)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def categoria_costo_gasto(tipo_gasto, descripcion="", mantencion=""):
    """Clasificación final para el consolidado.
    Si Mantención viene como Preventiva/Correctiva, manda el costo a ese grupo,
    aunque Tipo_Gasto diga Repuesto. Repuesto queda como Gastos Adicionales.
    """
    tipo_norm = normalizar_tipo_gasto(tipo_gasto)
    mant = tipo_mantencion_desde_gasto(tipo_norm, descripcion, mantencion)

    if mant in ["Preventiva", "Correctiva"]:
        return mant

    if tipo_norm == "Administrativo":
        return "Administrativos"

    if tipo_norm == "Repuesto":
        return "Gastos Adicionales"

    if tipo_norm == "Combustible":
        return "Combustible"

    if tipo_norm in ["Sin tipo", ""]:
        return "Gastos Adicionales"

    if tipo_norm in ["Mantención Preventiva", "Mantención Correctiva"]:
        return "Preventiva" if "Preventiva" in tipo_norm else "Correctiva"

    return tipo_norm


def construir_consolidado_costos(mantenciones, gastos):
    partes = []

    if isinstance(mantenciones, pd.DataFrame) and not mantenciones.empty and "Costo_CLP" in mantenciones.columns:
        mant = mantenciones.copy()
        if "Tipo_Mantencion" not in mant.columns:
            mant["Tipo_Mantencion"] = mant.get("Mantencion", "Sin tipo")
        mant["Item"] = mant["Tipo_Mantencion"].apply(normalizar_tipo_mantencion)
        mant["Item"] = mant["Item"].replace({"Predictiva": "Preventiva", "Mantención": "Preventiva"})
        mant["Costo"] = mant["Costo_CLP"].apply(limpiar_numero)
        partes.append(mant[["Item", "Costo"]])

    if isinstance(gastos, pd.DataFrame) and not gastos.empty and "Costo_CLP" in gastos.columns:
        gas = gastos.copy()
        for col, default in [("Tipo_Gasto", "Sin tipo"), ("Descripcion", ""), ("Mantencion", "")]:
            if col not in gas.columns:
                gas[col] = default
        gas["Tipo_Gasto"] = gas["Tipo_Gasto"].apply(normalizar_tipo_gasto)
        gas["Item"] = gas.apply(
            lambda x: categoria_costo_gasto(x.get("Tipo_Gasto", ""), x.get("Descripcion", ""), x.get("Mantencion", "")),
            axis=1,
        )
        gas["Costo"] = gas["Costo_CLP"].apply(limpiar_numero)
        gas = gas[gas["Item"] != "Combustible"].copy()
        partes.append(gas[["Item", "Costo"]])

    if not partes:
        return pd.DataFrame(columns=["Item", "Costo"])

    salida = pd.concat(partes, ignore_index=True)
    salida = salida[salida["Costo"] > 0].copy()
    if salida.empty:
        return pd.DataFrame(columns=["Item", "Costo"])

    salida = salida.groupby("Item", as_index=False)["Costo"].sum()
    orden = ["Correctiva", "Preventiva", "Administrativos", "Gastos Adicionales"]
    salida["_orden"] = salida["Item"].apply(lambda x: orden.index(x) if x in orden else len(orden))
    salida = salida.sort_values(["_orden", "Costo"], ascending=[True, False]).drop(columns=["_orden"])
    return salida


def crear_donut_costos(costos_item):
    """Gráfico de dona centrado, con leyenda legible y sin duplicar el título del panel."""
    fig = go.Figure()

    if costos_item is None or costos_item.empty:
        fig.update_layout(
            height=380,
            paper_bgcolor="rgba(255,255,255,0.90)",
            plot_bgcolor="rgba(255,255,255,0.90)",
            annotations=[
                dict(
                    text="Sin costos",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font_size=18,
                    font_color="#0f172a",
                )
            ],
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig

    total = float(costos_item["Costo"].sum())

    fig.add_trace(
        go.Pie(
            labels=costos_item["Item"],
            values=costos_item["Costo"],
            hole=0.62,
            sort=False,
            direction="clockwise",
            textinfo="percent",
            textposition="inside",
            insidetextorientation="radial",
            textfont=dict(color="white", size=16, family="Arial Black"),
            hovertemplate="<b>%{label}</b><br>Monto: %{customdata}<br>Participación: %{percent}<extra></extra>",
            customdata=[pesos(v) for v in costos_item["Costo"]],
            # Dona centrada y con espacio inferior para la leyenda.
            domain=dict(x=[0.08, 0.92], y=[0.20, 0.98]),
            showlegend=True,
        )
    )

    fig.update_layout(
        height=380,
        paper_bgcolor="rgba(255,255,255,0.90)",
        plot_bgcolor="rgba(255,255,255,0.90)",
        font=dict(color="#0f172a", size=13),
        margin=dict(l=8, r=8, t=8, b=60),
        annotations=[
            dict(
                text="Total<br><b>" + pesos(total) + "</b>",
                x=0.50,
                y=0.59,
                xref="paper",
                yref="paper",
                font_size=15,
                font_color="#0f172a",
                showarrow=False,
                align="center",
            )
        ],
        legend=dict(
            title=dict(text="Tipo de costo", font=dict(size=13, color="#0f172a")),
            orientation="h",
            x=0.50,
            y=-0.06,
            xanchor="center",
            yanchor="top",
            font=dict(size=13, color="#0f172a", family="Arial"),
            bgcolor="rgba(255,255,255,0.82)",
            bordercolor="rgba(15,23,42,0.16)",
            borderwidth=1,
            itemclick=False,
            itemdoubleclick=False,
        ),
        uniformtext_minsize=11,
        uniformtext_mode="hide",
    )
    return fig

def crear_barra_costos(costos_item):
    if costos_item is None or costos_item.empty:
        return aplicar_formato_grafico(go.Figure(), 360)

    datos = costos_item.copy()
    datos["Costo_Millones"] = datos["Costo"].apply(limpiar_numero) / 1_000_000

    fig = px.bar(
        datos,
        x="Item",
        y="Costo_Millones",
        text=[pesos(v) for v in datos["Costo"]],
        template="plotly_white",
        title="Costo por categoría",
        custom_data=["Costo"],
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="Categoría: %{x}<br>Monto: $%{customdata[0]:,.0f}<br>Millones CLP: %{y:.2f} M<extra></extra>",
    )
    fig.update_layout(
        xaxis_title="Categoría",
        yaxis_title="Millones CLP",
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        margin=dict(l=10, r=10, t=55, b=10),
    )
    fig.update_yaxes(tickformat=",.1f", ticksuffix=" M", separatethousands=True)
    return aplicar_formato_grafico(fig, 380)


def preparar_tabla_repuestos(gastos):
    mostrar = gastos.copy()

    if "Equipo" in mostrar.columns:
        equipo_txt = mostrar["Equipo"].fillna("").astype(str).str.strip().str.lower()
    else:
        equipo_txt = pd.Series([""] * len(mostrar), index=mostrar.index)

    if "Descripcion" in mostrar.columns:
        desc_txt = mostrar["Descripcion"].fillna("").astype(str).str.strip().str.lower()
    else:
        desc_txt = pd.Series([""] * len(mostrar), index=mostrar.index)

    costo_num = mostrar["Costo_CLP"].apply(limpiar_numero) if "Costo_CLP" in mostrar.columns else pd.Series([0] * len(mostrar), index=mostrar.index)
    mostrar = mostrar[(~equipo_txt.isin(["", "none", "nan"])) | (~desc_txt.isin(["", "none", "nan"])) | (costo_num > 0)].copy()

    if "Clasificacion_Costo" not in mostrar.columns:
        mostrar["Clasificacion_Costo"] = mostrar.apply(
            lambda x: categoria_costo_gasto(x.get("Tipo_Gasto", ""), x.get("Descripcion", ""), x.get("Mantencion", "")),
            axis=1,
        )
    else:
        mostrar["Clasificacion_Costo"] = mostrar.apply(
            lambda x: categoria_costo_gasto(x.get("Tipo_Gasto", ""), x.get("Descripcion", ""), x.get("Mantencion", "")),
            axis=1,
        )

    if "Fecha" in mostrar.columns:
        mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)
    if "Costo_CLP" in mostrar.columns:
        mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)

    columnas_orden = [
        "Fecha", "Equipo", "Mantencion", "Tipo_Gasto", "Clasificacion_Costo",
        "Descripcion", "Proveedor", "Costo_CLP", "Documento_Respaldo", "Observacion", "Mes", "Año"
    ]
    columnas_orden = [c for c in columnas_orden if c in mostrar.columns]
    mostrar = mostrar[columnas_orden].copy()
    mostrar = mostrar.rename(columns={
        "Mantencion": "Mantención",
        "Tipo_Gasto": "Tipo gasto",
        "Clasificacion_Costo": "Consolidado",
        "Descripcion": "Descripción",
        "Costo_CLP": "Costo",
        "Documento_Respaldo": "Documento respaldo",
        "Observacion": "Observación",
    })
    return mostrar


def pagina_repuestos(gastos_f):
    st.markdown('<div class="section-head"><div class="panel-title page-section-title">Gastos Adicionales</div><div class="panel-subtitle">Repuestos, administrativos y gastos asociados a mantenciones preventivas/correctivas.</div></div>', unsafe_allow_html=True)
    # st.caption("Repuestos, administrativos y gastos adicionales asociados a mantenciones preventivas/correctivas.")

    gastos_sin_combustible = gastos_no_combustible(gastos_f)
    if gastos_sin_combustible.empty:
        st.info("No existen gastos adicionales para el filtro aplicado.")
        return

    gastos_sin_combustible = gastos_sin_combustible.copy()
    if "Clasificacion_Costo" not in gastos_sin_combustible.columns:
        gastos_sin_combustible["Clasificacion_Costo"] = ""
    gastos_sin_combustible["Clasificacion_Costo"] = gastos_sin_combustible.apply(
        lambda x: categoria_costo_gasto(x.get("Tipo_Gasto", ""), x.get("Descripcion", ""), x.get("Mantencion", "")),
        axis=1,
    )

    tipos = sorted([t for t in gastos_sin_combustible["Clasificacion_Costo"].dropna().astype(str).unique() if t.strip() != ""])
    filtro_tipo_gasto = st.selectbox("Filtrar por consolidado", ["Todos"] + tipos)

    gastos_vista = gastos_sin_combustible.copy()
    if filtro_tipo_gasto != "Todos":
        gastos_vista = gastos_vista[gastos_vista["Clasificacion_Costo"] == filtro_tipo_gasto].copy()

    resumen = gastos_vista.groupby("Clasificacion_Costo", as_index=False)["Costo_CLP"].sum().sort_values("Costo_CLP", ascending=False)
    if not resumen.empty:
        resumen_grafico = resumen.copy()
        resumen_grafico["Costo_Millones"] = resumen_grafico["Costo_CLP"].apply(limpiar_numero) / 1_000_000
        fig = px.bar(
            resumen_grafico,
            x="Clasificacion_Costo",
            y="Costo_Millones",
            text=[pesos(v) for v in resumen_grafico["Costo_CLP"]],
            template="plotly_white",
            title="Costo por consolidado",
            custom_data=["Costo_CLP"],
        )
        fig.update_traces(
            textposition="outside",
            hovertemplate="Consolidado: %{x}<br>Monto: $%{customdata[0]:,.0f}<br>Millones CLP: %{y:.2f} M<extra></extra>",
        )
        fig.update_layout(xaxis_title="Consolidado", yaxis_title="Millones CLP")
        fig.update_yaxes(tickformat=",.1f", ticksuffix=" M", separatethousands=True)
        st.plotly_chart(aplicar_formato_grafico(fig, 390), use_container_width=True)

    if gastos_vista.empty:
        st.info("No existen registros para el filtro seleccionado.")
        return

    mostrar = preparar_tabla_repuestos(gastos_vista)
    mostrar_tabla_clara(mostrar, height=450)


def pagina_costos(mant_f, gastos_f, combustible_f):
    st.markdown('<div class="section-head"><div class="panel-title page-section-title">Análisis de Costos</div></div>', unsafe_allow_html=True)

    gastos_sin_combustible = gastos_no_combustible(gastos_f)
    costo_mantenciones = float(mant_f["Costo_CLP"].sum()) if "Costo_CLP" in mant_f.columns else 0.0
    costo_gastos = float(gastos_sin_combustible["Costo_CLP"].sum()) if "Costo_CLP" in gastos_sin_combustible.columns else 0.0
    costo_total = costo_mantenciones + costo_gastos

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("💲", "Total", pesos(costo_total), "Costo acumulado", "#dcfce7")
    with c2:
        kpi_card("🛠️", "Mantenciones", pesos(costo_mantenciones), "Preventivas y correctivas", "#dbeafe")
    with c3:
        kpi_card("🧾", "Gastos Adicionales", pesos(costo_gastos), "Administrativos y adicionales", "#ede9fe")

    costos_item = construir_consolidado_costos(mant_f, gastos_f)

    st.markdown('<div class="panel-title">Distribución de Costos</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.plotly_chart(crear_donut_costos(costos_item), use_container_width=True)
    with col2:
        st.plotly_chart(crear_barra_costos(costos_item), use_container_width=True)


def pagina_documentos(documentos_f):
    st.markdown('<div class="section-head"><div class="panel-title page-section-title">Control Documental</div></div>', unsafe_allow_html=True)

    if documentos_f.empty:
        st.info("No existen documentos para el filtro aplicado.")
        return

    mostrar = documentos_f.copy()
    columnas_eliminar = [
        "ID_Documento", "ID_Equipo", "Mes_Numero", "Periodo"
    ]
    mostrar = mostrar.drop(columns=[c for c in columnas_eliminar if c in mostrar.columns], errors="ignore")

    for col in ["Fecha", "Vencimiento"]:
        if col in mostrar.columns:
            mostrar[col] = mostrar[col].apply(fecha_texto)

    mostrar = mostrar.rename(columns={
        "Tipo_Documento": "Tipo documento",
        "Ruta_Link": "Ruta / enlace",
        "Observacion": "Observación",
    })
    mostrar_tabla_clara(mostrar, height=520)



# =========================================================
# AJUSTE V22 - LOGO MENÚ MÁS PEQUEÑO Y DOCUMENTACIÓN LEGAL
# =========================================================
st.markdown(
    """
<style>
.menu-icon-img,
section[data-testid="stSidebar"] .menu-icon-img {
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    max-width: 44px !important;
    flex: 0 0 44px !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
}

.menu-icon-img img,
section[data-testid="stSidebar"] .menu-icon-img img {
    width: 44px !important;
    height: 44px !important;
    object-fit: contain !important;
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
}
</style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# CORRECCIÓN STREAMLIT CLOUD V6.0
# - Busca imágenes relativas al archivo app.py y de forma recursiva.
# - Evita que Streamlit Cloud muestre tablas oscuras usando tablas HTML claras.
# =========================================================
try:
    BASE_DIR_APP = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR_APP = os.getcwd()


def _rutas_base_imagenes():
    """Devuelve carpetas candidatas en cwd y en la carpeta real del app.py."""
    bases = []
    for raiz in [os.getcwd(), BASE_DIR_APP]:
        for carpeta in CARPETAS_IMAGENES + [".", "fotos", "Fotos", "FOTOS", "assets", "imagenes", "images", "img", "equipos"]:
            ruta = os.path.abspath(os.path.join(raiz, carpeta))
            if ruta not in bases and os.path.isdir(ruta):
                bases.append(ruta)
    return bases


def listar_imagenes_disponibles():
    """Listado robusto para Streamlit Cloud.
    En la nube, el cwd puede no coincidir con la carpeta del script; por eso se busca
    desde BASE_DIR_APP, recursivamente y sin depender de mayúsculas/minúsculas.
    """
    imagenes = []
    extensiones_validas = {e.lower() for e in EXTENSIONES_IMAGEN}
    for carpeta in _rutas_base_imagenes():
        for raiz, _, archivos in os.walk(carpeta):
            for archivo in archivos:
                ext = os.path.splitext(archivo)[1].lower()
                if ext in extensiones_validas:
                    ruta = os.path.join(raiz, archivo)
                    if ruta not in imagenes:
                        imagenes.append(ruta)
    return imagenes


def _resolver_ruta_archivo(ruta):
    """Resuelve rutas absolutas o relativas al cwd y al archivo app.py."""
    if not ruta or str(ruta).strip().lower() in ["", "nan", "none"]:
        return None
    ruta = str(ruta).strip().strip('"').strip("'")
    candidatos = [ruta]
    if not os.path.isabs(ruta):
        candidatos.extend([
            os.path.join(os.getcwd(), ruta),
            os.path.join(BASE_DIR_APP, ruta),
        ])
    for candidato in candidatos:
        if os.path.isfile(candidato):
            return os.path.abspath(candidato)
    return None


def buscar_imagen_por_nombre(nombre_base):
    """Busca una imagen por ruta, nombre exacto o nombre normalizado.
    Corregido para Streamlit Cloud: considera carpeta del script, subcarpetas y
    diferencias de mayúsculas/minúsculas en GitHub/Linux.
    """
    if not nombre_base or str(nombre_base).strip().lower() in ["", "nan", "none"]:
        return None

    nombre_base = str(nombre_base).strip()
    ruta_directa = _resolver_ruta_archivo(nombre_base)
    if ruta_directa:
        return ruta_directa

    nombre_sin_ext = os.path.splitext(os.path.basename(nombre_base))[0]
    nombre_norm = normalizar_texto(nombre_sin_ext)

    equivalencias = {
        "camion_ford_cargo": ["camion_ford", "camion ford", "ford cargo", "camion", "camión"],
        "camion_ford": ["camion_ford", "camion ford", "ford cargo", "camion", "camión"],
        "ford_cargo": ["camion_ford", "camion ford", "ford cargo"],
        "carro_de_arrastre": ["carro_arrastre", "carro arrastre", "carro_de_arrastre"],
        "carro_arrastre": ["carro_arrastre", "carro arrastre", "carro_de_arrastre"],
        "minicargador": ["minicargador", "mini cargador", "mini_cargador"],
        "barredora_tennant_s30": ["barredora", "tennant", "tennant_s30", "barredora tennant"],
        "barredora": ["barredora", "tennant", "tennant_s30"],
        "camioneta_mitsubishi": ["camioneta", "mitsubishi", "l200"],
        "camioneta": ["camioneta", "mitsubishi", "l200"],
        "alza_hombre": ["alza_hombre", "alza hombre", "alzahombre", "alza"],
        "grua_horquilla": ["grua_horquilla", "grúa horquilla", "grua horquilla", "grua_orquilla", "orquilla", "horquilla"],
        "grua_orquilla": ["grua_horquilla", "grúa horquilla", "grua horquilla", "grua_orquilla", "orquilla", "horquilla"],
    }

    nombres_objetivo = [nombre_norm]
    for eq in equivalencias.get(nombre_norm, []):
        nombres_objetivo.append(normalizar_texto(eq))
    nombres_objetivo = list(dict.fromkeys(nombres_objetivo))

    imagenes = listar_imagenes_disponibles()

    # 1) Coincidencia exacta normalizada.
    for ruta in imagenes:
        base_norm = normalizar_texto(os.path.splitext(os.path.basename(ruta))[0])
        if base_norm in nombres_objetivo:
            return ruta

    # 2) Coincidencia parcial controlada.
    for ruta in imagenes:
        base_norm = normalizar_texto(os.path.splitext(os.path.basename(ruta))[0])
        for objetivo in nombres_objetivo:
            if objetivo and (objetivo in base_norm or base_norm in objetivo):
                return ruta

    return None


def buscar_imagen_equipo(fila):
    equipo = str(fila.get("Equipo", "")).strip()
    id_equipo = str(fila.get("ID_Equipo", "")).strip()
    tipo_equipo = str(fila.get("Tipo_Equipo", "")).strip()
    patente_codigo = str(fila.get("Patente_Codigo", "")).strip()
    marca = str(fila.get("Marca", "")).strip()
    modelo = str(fila.get("Modelo", "")).strip()
    imagen_excel = str(fila.get("Imagen", "")).strip()

    candidatos = []
    id_normal = normalizar_id_equipo(id_equipo)
    id_sin_guion = id_normal.replace("-", "")

    if id_normal in MAPEO_ID_EQUIPO_IMAGEN:
        candidatos.append(MAPEO_ID_EQUIPO_IMAGEN[id_normal])
    if id_sin_guion in MAPEO_ID_EQUIPO_IMAGEN:
        candidatos.append(MAPEO_ID_EQUIPO_IMAGEN[id_sin_guion])

    if imagen_excel and imagen_excel.lower() not in ["nan", "none", ""]:
        candidatos.append(imagen_excel)

    texto_equipo = " ".join([equipo, tipo_equipo, patente_codigo, marca, modelo])
    texto_norm = normalizar_texto(texto_equipo)

    if "grua" in texto_norm or "horquilla" in texto_norm or "orquilla" in texto_norm:
        candidatos.extend(["grua_horquilla", "grua_orquilla", "horquilla"])
    if "camioneta" in texto_norm or "mitsubishi" in texto_norm or "l200" in texto_norm:
        candidatos.extend(["camioneta_mitsubishi", "camioneta", "mitsubishi"])
    if "camion" in texto_norm and "ford" in texto_norm:
        candidatos.extend(["camion_ford_cargo", "camion_ford", "ford_cargo"])
    if "carro" in texto_norm and "arrastre" in texto_norm:
        candidatos.extend(["carro_de_arrastre", "carro_arrastre"])
    if "minicargador" in texto_norm or "mini_cargador" in texto_norm:
        candidatos.extend(["minicargador", "mini_cargador"])
    if "barredora" in texto_norm or "tennant" in texto_norm:
        candidatos.extend(["barredora_tennant_s30", "barredora", "tennant_s30"])
    if "alza" in texto_norm and "hombre" in texto_norm:
        candidatos.extend(["alza_hombre", "alzahombre"])

    candidatos.extend([id_equipo, equipo, tipo_equipo, patente_codigo, marca, modelo, texto_equipo])
    candidatos = list(dict.fromkeys([c for c in candidatos if str(c).strip()]))

    for candidato in candidatos:
        ruta = buscar_imagen_por_nombre(candidato)
        if ruta and os.path.isfile(ruta):
            return ruta
    return None


def es_url_valida(valor):
    texto = str(valor).strip()
    return texto.startswith("http://") or texto.startswith("https://")


def celda_html_con_enlace(columna, valor):
    """Permite abrir documentos desde columnas Ruta / enlace o Link.
    Si la celda trae una URL de Google Drive, Google Docs, SharePoint u otro sitio,
    se muestra como botón clickeable. Si no es URL, se muestra como texto normal.
    """
    valor_txt = "" if pd.isna(valor) else str(valor).strip()
    columna_norm = normalizar_texto(columna)

    es_columna_enlace = (
        "ruta" in columna_norm
        or "link" in columna_norm
        or "enlace" in columna_norm
        or "url" in columna_norm
    )

    if es_columna_enlace and es_url_valida(valor_txt):
        url = escape_html(valor_txt)
        return (
            f'<a class="link-documento" href="{url}" target="_blank" '
            f'rel="noopener noreferrer">Abrir documento</a>'
        )

    return escape_html(valor_txt)


def tabla_html_clara(df, height=280):
    """Genera tabla HTML clara, estable en Visual Studio Code y Streamlit Cloud."""
    if df is None or df.empty:
        return ""

    columnas = list(df.columns)
    thead = "".join(f"<th>{escape_html(col)}</th>" for col in columnas)
    filas = []
    for _, row in df.iterrows():
        celdas = []
        for col in columnas:
            valor = "" if pd.isna(row[col]) else str(row[col])
            clase = " monto" if col.lower() in ["monto", "costo", "valor", "total"] or "$" in valor else ""
            contenido = celda_html_con_enlace(col, row[col])
            celdas.append(f"<td class='{clase}'>{contenido}</td>")
        filas.append("<tr>" + "".join(celdas) + "</tr>")

    alto = int(height) if height else 280
    return f"""
<div class="tabla-clara-wrap" style="max-height:{alto}px;">
  <table class="tabla-clara">
    <thead><tr>{thead}</tr></thead>
    <tbody>{''.join(filas)}</tbody>
  </table>
</div>
"""


def mostrar_tabla_clara(df, height=280):
    if df is None or df.empty:
        st.info("No existen registros para el filtro aplicado.")
        return
    st.markdown(tabla_html_clara(df, height=height), unsafe_allow_html=True)


st.markdown(
    """
<style>
/* Tablas claras fijas para Streamlit Cloud: no dependen del tema oscuro del navegador/app. */
.tabla-clara-wrap {
    width: 100% !important;
    overflow: auto !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 13px !important;
    background: rgba(255, 255, 255, 0.66) !important;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05) !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
}
.tabla-clara {
    width: 100% !important;
    border-collapse: collapse !important;
    background: rgba(255, 255, 255, 0.60) !important;
    color: #0f172a !important;
    font-size: 13px !important;
    line-height: 1.35 !important;
}
.tabla-clara thead th {
    position: sticky !important;
    top: 0 !important;
    z-index: 2 !important;
    background: rgba(241, 245, 249, 0.92) !important;
    color: #475569 !important;
    font-weight: 850 !important;
    text-align: left !important;
    padding: 10px 12px !important;
    border-bottom: 1px solid #cbd5e1 !important;
    border-right: 1px solid #d7dee8 !important;
    white-space: nowrap !important;
    text-align: center !important;
}
.tabla-clara tbody td {
    background: rgba(255, 255, 255, 0.38) !important;
    color: #0f172a !important;
    padding: 10px 12px !important;
    border-bottom: 1px solid rgba(203, 213, 225, 0.72) !important;
    border-right: 1px solid rgba(203, 213, 225, 0.62) !important;
    vertical-align: top !important;
}
.tabla-clara tbody tr:hover td {
    background: rgba(239, 246, 255, 0.75) !important;
}
.tabla-clara a.link-documento {
    display: inline-block !important;
    padding: 5px 10px !important;
    border-radius: 999px !important;
    background: #2563eb !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 900 !important;
    text-decoration: none !important;
    white-space: nowrap !important;
    text-align: center !important;
}
.tabla-clara a.link-documento:hover {
    background: #1d4ed8 !important;
    text-decoration: none !important;
}
.tabla-clara td.monto,
.tabla-clara th:nth-last-child(2) {
    white-space: nowrap !important;
    font-variant-numeric: tabular-nums !important;
}
/* Refuerzo: si queda algún st.dataframe en otra página, se fuerza contenedor claro. */
[data-testid="stDataFrame"] {
    background: rgba(255, 255, 255, 0.72) !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 13px !important;
}
</style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# CORRECCIÓN FINAL: CAJA INFERIOR DEL MENÚ COMPLETA
# =========================================================
st.markdown(
    """
<style>
/* Evita que Streamlit Cloud corte la tarjeta inferior del menú. */
section[data-testid="stSidebar"] {
    overflow-y: auto !important;
    overflow-x: hidden !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    height: auto !important;
    min-height: 100vh !important;
    padding: 10px 12px 28px 12px !important;
    box-sizing: border-box !important;
    overflow-y: visible !important;
    overflow-x: hidden !important;
}

section[data-testid="stSidebar"] .menu-footer-box {
    width: 262px !important;
    min-width: 262px !important;
    max-width: 262px !important;
    height: auto !important;
    min-height: 118px !important;
    display: block !important;
    overflow: visible !important;
    box-sizing: border-box !important;
    padding: 12px 12px 14px 12px !important;
    margin-top: 10px !important;
    margin-bottom: 22px !important;
    border-radius: 15px !important;
    background: rgba(2, 6, 23, 0.98) !important;
    border: 1px solid rgba(147, 197, 253, 0.38) !important;
}

section[data-testid="stSidebar"] .menu-info,
section[data-testid="stSidebar"] .menu-info * {
    display: inline !important;
    height: auto !important;
    min-height: auto !important;
    overflow: visible !important;
    white-space: normal !important;
    word-break: normal !important;
    overflow-wrap: break-word !important;
    line-height: 1.55 !important;
    font-size: 12.2px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] .menu-info {
    display: block !important;
    width: 100% !important;
}

section[data-testid="stSidebar"] .menu-info b {
    color: #93c5fd !important;
    -webkit-text-fill-color: #93c5fd !important;
    font-weight: 950 !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL SOLICITADO
# 1) Menú principal: Dashboard Ejecutivo.
# 2) Documentación Legal sin columnas Año y Mes.
# 3) Montos CLP con signo $ siempre al inicio.
# =========================================================


def normalizar_monto_clp_texto(valor):
    """Devuelve montos en formato CLP con $ a la derecha.
    Corrige valores escritos como '180.000 $', '$1.850.000', '3430000', etc.
    """
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()
    if texto == "":
        return ""

    # Si no parece monto, no se interviene.
    tiene_signo = "$" in texto
    tiene_numero = bool(re.search(r"\d", texto))
    if not tiene_numero:
        return texto

    # Se aplica solo a columnas de monto/costo o a textos que ya tienen signo $.
    numero_limpio = limpiar_numero(texto)
    if tiene_signo or re.fullmatch(r"[0-9. ,\-]+", texto):
        return pesos(numero_limpio)

    return texto


def celda_html_con_enlace(columna, valor):
    """Renderiza celdas con soporte de link y formato CLP corregido."""
    valor_txt = "" if pd.isna(valor) else str(valor).strip()
    columna_norm = normalizar_texto(columna)

    es_columna_enlace = (
        "ruta" in columna_norm
        or "link" in columna_norm
        or "enlace" in columna_norm
        or "url" in columna_norm
    )

    if es_columna_enlace and es_url_valida(valor_txt):
        url = escape_html(valor_txt)
        return (
            f'<a class="link-documento" href="{url}" target="_blank" '
            f'rel="noopener noreferrer">Abrir documento</a>'
        )

    es_columna_monto = columna_norm in [
        "monto", "costo", "valor", "total", "costo_clp", "costo_total",
        "valor_unitario", "monto_total"
    ] or any(palabra in columna_norm for palabra in ["monto", "costo", "valor", "total"])

    if es_columna_monto or "$" in valor_txt:
        valor_txt = normalizar_monto_clp_texto(valor_txt)

    return escape_html(valor_txt)


def pagina_documentos(documentos_f):
    st.markdown('<div class="section-head"><div class="panel-title page-section-title">Control Documental</div></div>', unsafe_allow_html=True)

    if documentos_f.empty:
        st.info("No existen documentos para el filtro aplicado.")
        return

    mostrar = documentos_f.copy()

    # En Documentación Legal no se muestran las columnas Año y Mes.
    columnas_eliminar = [
        "ID_Documento",
        "ID_Equipo",
        "Año",
        "Ano",
        "Mes",
        "Mes_Numero",
        "Periodo",
    ]
    mostrar = mostrar.drop(columns=[c for c in columnas_eliminar if c in mostrar.columns], errors="ignore")

    for col in ["Fecha", "Vencimiento"]:
        if col in mostrar.columns:
            mostrar[col] = mostrar[col].apply(fecha_texto)

    mostrar = mostrar.rename(
        columns={
            "Tipo_Documento": "Tipo documento",
            "Ruta_Link": "Ruta / enlace",
            "Observacion": "Observación",
            "Descripcion": "Descripción",
        }
    )

    mostrar_tabla_clara(mostrar, height=520)



# =========================================================
# AJUSTE FINAL V5.2
# - Dashboard Ejecutivo aprovecha mejor el espacio vertical.
# - Histórico de Intervenciones queda más alto para evitar espacio vacío.
# - Distribución de Costos más compacta.
# - Todos los montos CLP se fuerzan con $ a la derecha, incluso si vienen desde Google Sheets como "65.000 $".
# =========================================================


def pesos(valor):
    """Formato CLP definitivo: $ siempre a la derecha del monto.
    Acepta números y textos como '65.000 $', '$65.000', '65000'.
    """
    try:
        if pd.isna(valor):
            return "0 $"
    except Exception:
        pass

    if isinstance(valor, str):
        numero_valor = limpiar_numero(valor)
    else:
        try:
            numero_valor = float(valor)
        except Exception:
            numero_valor = limpiar_numero(valor)

    try:
        return "$" + f"{int(round(float(numero_valor))):,}".replace(",", ".")
    except Exception:
        return "0 $"


def pesos_html(valor):
    return pesos(valor)


def normalizar_monto_clp_texto(valor):
    """Corrige cualquier monto para que quede como '10.000 $'."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()
    if texto == "":
        return ""

    tiene_numero = bool(re.search(r"\d", texto))
    if not tiene_numero:
        return texto

    # Se corrige cuando ya trae $, o cuando la columna lo tratará como monto.
    return pesos(texto)


def kpi_card(icono, titulo, valor, subtitulo, color_fondo):
    """Tarjeta KPI con corrección estricta de montos CLP."""
    valor_txt = "" if pd.isna(valor) else str(valor).strip()
    if "$" in valor_txt or "＄" in valor_txt:
        valor_txt = pesos(valor_txt.replace("＄", "$"))

    st.markdown(
        f"""
<div class="kpi-card">
    <div class="kpi-icon" style="background:{color_fondo};">{icono}</div>
    <div class="kpi-title">{escape_html(titulo)}</div>
    <div class="kpi-value">{escape_html(valor_txt)}</div>
    <div class="kpi-sub">{escape_html(subtitulo)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def celda_html_con_enlace(columna, valor):
    """Renderiza links y fuerza CLP con $ a la izquierda en columnas monetarias."""
    valor_txt = "" if pd.isna(valor) else str(valor).strip()
    columna_norm = normalizar_texto(columna)

    es_columna_enlace = (
        "ruta" in columna_norm
        or "link" in columna_norm
        or "enlace" in columna_norm
        or "url" in columna_norm
    )

    if es_columna_enlace and es_url_valida(valor_txt):
        url = escape_html(valor_txt)
        return (
            f'<a class="link-documento" href="{url}" target="_blank" '
            f'rel="noopener noreferrer">Abrir documento</a>'
        )

    es_columna_monto = any(
        palabra in columna_norm
        for palabra in ["monto", "costo", "valor", "total", "clp", "unitario"]
    )

    if es_columna_monto or "$" in valor_txt or "＄" in valor_txt:
        valor_txt = normalizar_monto_clp_texto(valor_txt.replace("＄", "$"))

    return escape_html(valor_txt)


def crear_donut_costos(costos_item):
    """Dona de costos compacta para aprovechar mejor el Dashboard Ejecutivo."""
    fig = go.Figure()

    if costos_item is None or costos_item.empty:
        fig.update_layout(
            height=310,
            paper_bgcolor="rgba(255,255,255,0.82)",
            plot_bgcolor="rgba(255,255,255,0.82)",
            annotations=[dict(text="Sin costos", x=0.5, y=0.5, showarrow=False, font_size=16, font_color="#0f172a")],
            margin=dict(l=6, r=6, t=4, b=6),
        )
        return fig

    total = float(costos_item["Costo"].sum())

    fig.add_trace(
        go.Pie(
            labels=costos_item["Item"],
            values=costos_item["Costo"],
            hole=0.62,
            sort=False,
            direction="clockwise",
            textinfo="percent",
            texttemplate="%{percent:.1%}",
            textposition="auto",
            insidetextorientation="auto",
            textfont=dict(color="white", size=14, family="Arial Black"),
            outsidetextfont=dict(color="#0f172a", size=13, family="Arial Black"),
            hovertemplate="<b>%{label}</b><br>Monto: %{customdata}<br>Participación: %{percent}<extra></extra>",
            customdata=[pesos(v) for v in costos_item["Costo"]],
            domain=dict(x=[0.07, 0.93], y=[0.22, 0.96]),
            showlegend=True,
        )
    )

    fig.update_layout(
        height=285,
        paper_bgcolor="rgba(255,255,255,0.82)",
        plot_bgcolor="rgba(255,255,255,0.82)",
        font=dict(color="#0f172a", size=12),
        margin=dict(l=6, r=6, t=0, b=44),
        annotations=[
            dict(
                text="Total<br><b>" + pesos(total) + "</b>",
                x=0.50,
                y=0.60,
                xref="paper",
                yref="paper",
                font_size=14,
                font_color="#0f172a",
                showarrow=False,
                align="center",
            )
        ],
        legend=dict(
            title=dict(text="Tipo de costo", font=dict(size=12, color="#0f172a")),
            orientation="h",
            x=0.50,
            y=-0.03,
            xanchor="center",
            yanchor="top",
            font=dict(size=12, color="#0f172a", family="Arial"),
            bgcolor="rgba(255,255,255,0.82)",
            bordercolor="rgba(15,23,42,0.16)",
            borderwidth=1,
            itemclick=False,
            itemdoubleclick=False,
        ),
        uniformtext_minsize=9,
        uniformtext_mode="show",
    )
    return fig


st.markdown(
    """
<style>
/* V5.2: mejor uso de espacios del Dashboard Ejecutivo */
.panel-title {
    margin-top: 8px !important;
    margin-bottom: 5px !important;
}
[data-testid="stPlotlyChart"] {
    margin-bottom: 0px !important;
}
.tabla-clara-wrap {
    margin-bottom: 4px !important;
}
.proximas-box {
    margin-top: 0px !important;
}
/* Montos: alineados a la derecha y sin separación visual extra */
.tabla-clara td.monto,
.tabla-clara th.monto {
    text-align: left !important;
    white-space: nowrap !important;
    text-align: center !important;
}
.kpi-value {
    white-space: nowrap !important;
    text-align: center !important;
}
</style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# OVERRIDE FINAL V5.3: FORMATO CLP DEFINITIVO
# =========================================================
def pesos(valor):
    """Formato CLP final: signo $ a la izquierda, sin espacio (ej.: $4.000)."""
    try:
        if pd.isna(valor):
            return "$0"
    except Exception:
        pass

    try:
        numero_valor = limpiar_numero(valor)
        return "$" + f"{int(round(float(numero_valor))):,}".replace(",", ".")
    except Exception:
        return "$0"


def pesos_html(valor):
    return pesos(valor)


def normalizar_monto_clp_texto(valor):
    """Normaliza cualquier monto a formato '$10.000'."""
    try:
        if pd.isna(valor):
            return ""
    except Exception:
        pass

    texto = str(valor).strip()
    if texto == "":
        return ""

    if not re.search(r"\d", texto):
        return texto

    return pesos(texto.replace("＄", "$"))


def kpi_card(icono, titulo, valor, subtitulo, color_fondo):
    """Tarjeta KPI con montos CLP siempre con $ a la izquierda."""
    valor_txt = "" if pd.isna(valor) else str(valor).strip()
    if "$" in valor_txt or "＄" in valor_txt:
        valor_txt = pesos(valor_txt.replace("＄", "$"))

    st.markdown(
        f"""
<div class="kpi-card">
    <div class="kpi-icon" style="background:{color_fondo};">{icono}</div>
    <div class="kpi-title">{escape_html(titulo)}</div>
    <div class="kpi-value">{escape_html(valor_txt)}</div>
    <div class="kpi-sub">{escape_html(subtitulo)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def celda_html_con_enlace(columna, valor):
    """Renderiza links y fuerza CLP con $ a la izquierda en columnas monetarias."""
    valor_txt = "" if pd.isna(valor) else str(valor).strip()
    columna_norm = normalizar_texto(columna)

    es_columna_enlace = (
        "ruta" in columna_norm
        or "link" in columna_norm
        or "enlace" in columna_norm
        or "url" in columna_norm
    )

    if es_columna_enlace and es_url_valida(valor_txt):
        url = escape_html(valor_txt)
        return (
            f'<a class="link-documento" href="{url}" target="_blank" '
            f'rel="noopener noreferrer">Abrir documento</a>'
        )

    es_columna_monto = any(
        palabra in columna_norm
        for palabra in ["monto", "costo", "valor", "total", "clp", "unitario"]
    )

    if es_columna_monto or "$" in valor_txt or "＄" in valor_txt:
        valor_txt = normalizar_monto_clp_texto(valor_txt.replace("＄", "$"))

    return escape_html(valor_txt)

# =========================================================
# AJUSTE FINAL V5.3
# - Montos CLP con signo $ a la derecha del monto.
# - Gráficos de costos con eje Y en millones CLP.
# - Mejor aprovechamiento de espacios verticales del dashboard.
# =========================================================
st.markdown(
    """
<style>
/* Compacta espacios entre tablas y bloques del dashboard */
.panel-title {
    margin-top: 6px !important;
    margin-bottom: 4px !important;
}
[data-testid="stVerticalBlock"] {
    gap: 0.26rem !important;
}
[data-testid="stHorizontalBlock"] {
    gap: 0.65rem !important;
}
.tabla-clara-wrap {
    margin-bottom: 2px !important;
}
[data-testid="stPlotlyChart"] {
    margin-top: 0px !important;
    margin-bottom: 0px !important;
}
.proximas-box, .proxima-row, .next-item {
    margin-top: 0px !important;
    margin-bottom: 1px !important;
}

/* Montos CLP: signo a la derecha y lectura uniforme */
.tabla-clara td.monto,
.tabla-clara th.monto {
    text-align: right !important;
    white-space: nowrap !important;
    text-align: center !important;
}
.kpi-value, .plotly .textpoint {
    white-space: nowrap !important;
    text-align: center !important;
}
</style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# OVERRIDE FINAL V5.4: TABLAS, GASTOS ADICIONALES Y GRÁFICOS
# =========================================================

def preparar_tabla_mantenciones(mantenciones):
    """Tabla de mantenciones sin columnas Mes/Año, compatible con Google Sheets sin esas columnas."""
    mostrar = mantenciones.copy() if isinstance(mantenciones, pd.DataFrame) else pd.DataFrame()

    if mostrar.empty:
        return mostrar

    if "Tipo_Mantencion" in mostrar.columns:
        mostrar["Mantencion"] = mostrar["Tipo_Mantencion"].apply(normalizar_tipo_mantencion)
    elif "Mantencion" in mostrar.columns:
        mostrar["Mantencion"] = mostrar["Mantencion"].apply(normalizar_tipo_mantencion)
    else:
        mostrar["Mantencion"] = "Sin tipo"

    if "Fecha" in mostrar.columns:
        mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)

    if "Costo_CLP" in mostrar.columns:
        mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)

    columnas_orden = [
        "Fecha",
        "Equipo",
        "Mantencion",
        "Categoria",
        "Proveedor",
        "Descripcion",
        "Costo_CLP",
        "Estado_Mantencion",
        "Documento_Respaldo",
        "Observacion",
    ]

    columnas_orden = [c for c in columnas_orden if c in mostrar.columns]
    mostrar = mostrar[columnas_orden].copy()

    mostrar = mostrar.rename(
        columns={
            "Mantencion": "Mantención",
            "Categoria": "Categoría",
            "Descripcion": "Descripción",
            "Costo_CLP": "Costo",
            "Estado_Mantencion": "Estado",
            "Documento_Respaldo": "Documento respaldo",
            "Observacion": "Observación",
        }
    )
    return mostrar


def preparar_tabla_repuestos(gastos):
    """Tabla de gastos adicionales sin columnas Mes/Año/Periodo."""
    mostrar = gastos.copy() if isinstance(gastos, pd.DataFrame) else pd.DataFrame()

    if mostrar.empty:
        return mostrar

    if "Equipo" in mostrar.columns:
        equipo_txt = mostrar["Equipo"].fillna("").astype(str).str.strip().str.lower()
    else:
        equipo_txt = pd.Series([""] * len(mostrar), index=mostrar.index)

    if "Descripcion" in mostrar.columns:
        desc_txt = mostrar["Descripcion"].fillna("").astype(str).str.strip().str.lower()
    else:
        desc_txt = pd.Series([""] * len(mostrar), index=mostrar.index)

    costo_num = mostrar["Costo_CLP"].apply(limpiar_numero) if "Costo_CLP" in mostrar.columns else pd.Series([0] * len(mostrar), index=mostrar.index)
    mostrar = mostrar[(~equipo_txt.isin(["", "none", "nan"])) | (~desc_txt.isin(["", "none", "nan"])) | (costo_num > 0)].copy()

    if mostrar.empty:
        return mostrar

    mostrar["Clasificacion_Costo"] = mostrar.apply(
        lambda x: categoria_costo_gasto(x.get("Tipo_Gasto", ""), x.get("Descripcion", ""), x.get("Mantencion", "")),
        axis=1,
    )

    if "Fecha" in mostrar.columns:
        mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)
    if "Costo_CLP" in mostrar.columns:
        mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)

    columnas_orden = [
        "Fecha",
        "Equipo",
        "Mantencion",
        "Tipo_Gasto",
        "Clasificacion_Costo",
        "Descripcion",
        "Proveedor",
        "Costo_CLP",
        "Documento_Respaldo",
        "Observacion",
    ]
    columnas_orden = [c for c in columnas_orden if c in mostrar.columns]
    mostrar = mostrar[columnas_orden].copy()
    mostrar = mostrar.rename(columns={
        "Mantencion": "Mantención",
        "Tipo_Gasto": "Tipo gasto",
        "Clasificacion_Costo": "Consolidado",
        "Descripcion": "Descripción",
        "Costo_CLP": "Costo",
        "Documento_Respaldo": "Documento respaldo",
        "Observacion": "Observación",
    })
    return mostrar


def preparar_tabla_proximas(proximas):
    """Tabla compacta de próximas mantenciones y alertas.
    Elimina Frecuencia, Categoría, Mantención y Costo.
    Formatea Próxima mantención sin decimales ni '.0'.
    """
    mostrar = proximas.copy() if isinstance(proximas, pd.DataFrame) else pd.DataFrame()

    if mostrar.empty:
        return mostrar

    mostrar = enriquecer_estado_proximas(mostrar)

    if "Proxima_Mantencion" in mostrar.columns:
        mostrar["Proxima_Mantencion"] = mostrar.apply(
            lambda x: formatear_valor_control(x.get("Proxima_Mantencion", 0), x.get("Unidad_Control", "")),
            axis=1,
        )

    if "Km_Horometro_Actual" in mostrar.columns:
        mostrar["Km_Horometro_Actual"] = mostrar.apply(
            lambda x: formatear_valor_control(x.get("Km_Horometro_Actual", 0), x.get("Unidad_Control", "")),
            axis=1,
        )

    if "Saldo_Restante" in mostrar.columns:
        mostrar["Saldo_Restante"] = mostrar.apply(
            lambda x: formatear_saldo_control(x.get("Saldo_Restante", 0), x.get("Unidad_Control", "")),
            axis=1,
        )

    columnas_orden = [
        "Equipo",
        "Marca",
        "Modelo",
        "Patente_Codigo",
        "Km_Horometro_Actual",
        "Unidad_Control",
        "Descripcion",
        "Proxima_Mantencion",
        "Estado_Control",
        "Saldo_Restante",
        "Texto_Estado",
        "Observacion",
    ]
    columnas_orden = [c for c in columnas_orden if c in mostrar.columns]
    mostrar = mostrar[columnas_orden].copy()

    mostrar = mostrar.rename(
        columns={
            "Patente_Codigo": "Patente / Código",
            "Km_Horometro_Actual": "Lectura actual",
            "Unidad_Control": "Unidad",
            "Descripcion": "Descripción",
            "Proxima_Mantencion": "Próxima mantención",
            "Estado_Control": "Estado",
            "Saldo_Restante": "Saldo restante",
            "Texto_Estado": "Análisis",
            "Observacion": "Observación",
        }
    )
    return mostrar


def crear_barra_costos(costos_item):
    """Barra de costos con colores distintos y eje Y en millones CLP."""
    if costos_item is None or costos_item.empty:
        return aplicar_formato_grafico(go.Figure(), 360)

    datos = costos_item.copy()
    datos["Costo_Millones"] = datos["Costo"].apply(limpiar_numero) / 1_000_000

    colores_costo = ["#2563eb", "#16a34a", "#f97316", "#dc2626", "#9333ea", "#0ea5e9"]

    fig = px.bar(
        datos,
        x="Item",
        y="Costo_Millones",
        color="Item",
        color_discrete_sequence=colores_costo,
        text=[pesos(v) for v in datos["Costo"]],
        template="plotly_white",
        title="Costo por categoría",
        custom_data=["Costo"],
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="Categoría: %{x}<br>Monto: $%{customdata[0]:,.0f}<br>Millones CLP: %{y:.2f} M<extra></extra>",
        marker_line_width=0,
    )
    fig.update_layout(
        xaxis_title="Categoría",
        yaxis_title="Millones CLP",
        showlegend=False,
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        margin=dict(l=10, r=10, t=55, b=10),
    )
    fig.update_yaxes(tickformat=".1f", ticksuffix=" M")
    return aplicar_formato_grafico(fig, 380)


def pagina_repuestos(gastos_f):
    st.markdown('<div class="section-head"><div class="panel-title page-section-title">Gastos Adicionales</div><div class="panel-subtitle">Repuestos, administrativos y gastos asociados a mantenciones preventivas/correctivas.</div></div>', unsafe_allow_html=True)
    # st.caption("Repuestos, administrativos y gastos adicionales asociados a mantenciones preventivas/correctivas.")

    gastos_sin_combustible = gastos_no_combustible(gastos_f)
    if gastos_sin_combustible.empty:
        st.info("No existen gastos adicionales para el filtro aplicado.")
        return

    gastos_sin_combustible = gastos_sin_combustible.copy()
    gastos_sin_combustible["Clasificacion_Costo"] = gastos_sin_combustible.apply(
        lambda x: categoria_costo_gasto(x.get("Tipo_Gasto", ""), x.get("Descripcion", ""), x.get("Mantencion", "")),
        axis=1,
    )

    tipos = sorted([t for t in gastos_sin_combustible["Clasificacion_Costo"].dropna().astype(str).unique() if t.strip() != ""])
    filtro_tipo_gasto = st.selectbox("Filtrar por consolidado", ["Todos"] + tipos)

    gastos_vista = gastos_sin_combustible.copy()
    if filtro_tipo_gasto != "Todos":
        gastos_vista = gastos_vista[gastos_vista["Clasificacion_Costo"] == filtro_tipo_gasto].copy()

    resumen = gastos_vista.groupby("Clasificacion_Costo", as_index=False)["Costo_CLP"].sum().sort_values("Costo_CLP", ascending=False)
    if not resumen.empty:
        resumen_grafico = resumen.copy()
        resumen_grafico["Costo_Millones"] = resumen_grafico["Costo_CLP"].apply(limpiar_numero) / 1_000_000
        colores_gastos = ["#2563eb", "#16a34a", "#f97316", "#dc2626", "#9333ea", "#0ea5e9"]
        fig = px.bar(
            resumen_grafico,
            x="Clasificacion_Costo",
            y="Costo_Millones",
            color="Clasificacion_Costo",
            color_discrete_sequence=colores_gastos,
            text=[pesos(v) for v in resumen_grafico["Costo_CLP"]],
            template="plotly_white",
            title="Costo por consolidado",
            custom_data=["Costo_CLP"],
        )
        fig.update_traces(
            textposition="outside",
            hovertemplate="Consolidado: %{x}<br>Monto: $%{customdata[0]:,.0f}<br>Millones CLP: %{y:.2f} M<extra></extra>",
            marker_line_width=0,
        )
        fig.update_layout(
            xaxis_title="Consolidado",
            yaxis_title="Millones CLP",
            showlegend=False,
        )
        fig.update_yaxes(tickformat=".1f", ticksuffix=" M")
        st.plotly_chart(aplicar_formato_grafico(fig, 390), use_container_width=True)

    if gastos_vista.empty:
        st.info("No existen registros para el filtro seleccionado.")
        return

    mostrar = preparar_tabla_repuestos(gastos_vista)
    mostrar_tabla_clara(mostrar, height=450)


# =========================================================
# AJUSTE FINAL V5.5
# - % visibles en gráfico de dona de costos.
# - Próximas Mantenciones más ancho en Dashboard Ejecutivo.
# - Se elimina la palabra "indefinido" del gráfico Evolución de Costos.
# =========================================================
st.markdown(
    """
<style>
.proximas-box {
    width: 100% !important;
    max-width: none !important;
}
.proximas-box .panel-title {
    font-size: 18px !important;
    margin-bottom: 8px !important;
}
.proximas-box .next-item {
    width: 100% !important;
    max-width: none !important;
    min-height: 39px !important;
    grid-template-columns: minmax(0, 1fr) auto !important;
    column-gap: 10px !important;
}
.proximas-box .next-title {
    font-size: 12px !important;
    line-height: 1.12 !important;
}
.proximas-box .next-sub {
    font-size: 10.3px !important;
    line-height: 1.10 !important;
}
.proximas-box .badge-days {
    min-width: 62px !important;
    font-size: 9.5px !important;
    padding: 5px 7px !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V5.6
# - Sube el título y logo de la página principal para aprovechar el espacio superior.
# - Compacta la tabla de Gastos Adicionales del Dashboard para evitar barra horizontal.
# - Botón del menú queda solo como "Actualizar".
# =========================================================


def pagina_dashboard(equipos_f, mant_f, gastos_f, combustible_f, proximas_originales, filtro_equipo):
    """Dashboard Ejecutivo optimizado para ver más contenido en 100% de zoom."""
    gastos_sin_combustible = gastos_no_combustible(gastos_f)

    costo_mantenciones = float(mant_f["Costo_CLP"].sum()) if "Costo_CLP" in mant_f.columns else 0.0
    costo_gastos = float(gastos_sin_combustible["Costo_CLP"].sum()) if "Costo_CLP" in gastos_sin_combustible.columns else 0.0
    costo_total = costo_mantenciones + costo_gastos

    mant_realizadas = len(mant_f)
    repuestos_utilizados = len(gastos_sin_combustible)
    equipos_registrados = len(equipos_f)

    if "Proxima_Mantencion" not in proximas_originales.columns:
        proximas_originales = pd.DataFrame(columns=[
            "Equipo", "Categoria", "Tipo_Mantencion", "Proxima_Mantencion",
            "Km_Horometro_Actual", "Unidad_Control", "Costo_CLP"
        ])

    mant_proximas = proximas_originales.copy()
    if "Proxima_Mantencion" in mant_proximas.columns:
        mant_proximas["Proxima_Mantencion"] = mant_proximas["Proxima_Mantencion"].apply(limpiar_numero)
        mant_proximas = mant_proximas[mant_proximas["Proxima_Mantencion"] > 0].copy()

    if filtro_equipo != "Todos los equipos" and "Equipo" in mant_proximas.columns:
        mant_proximas = mant_proximas[mant_proximas["Equipo"] == filtro_equipo]

    mant_proximas = resumen_proximas_por_equipo(mant_proximas) if not mant_proximas.empty else mant_proximas

    if not mant_proximas.empty:
        proxima_fila = mant_proximas.iloc[0]
        equipo_proximo = str(proxima_fila.get("Equipo", "Sin equipo")).strip()
        proxima_valor = proxima_fila.get("Proxima_Texto", "Sin dato")
        proxima_estado = proxima_fila.get("Texto_Estado", "Sin análisis")
        proxima_texto = equipo_proximo if equipo_proximo else "Sin equipo"
        proxima_sub = f"Próx.: {proxima_valor} | {proxima_estado}"
    else:
        proxima_texto = "Sin registro"
        proxima_sub = "No programada"

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card("🛠️", "Mantenciones", f"{mant_realizadas}", "Registros del período", "#dbeafe")
    with k2:
        kpi_card("💲", "Monto Total", pesos(costo_total), "Costos del período", "#dcfce7")
    with k3:
        kpi_card("🧰", "Gastos Adic.", f"{repuestos_utilizados}", "Repuestos, mantenciones y administrativos", "#f3e8ff")
    with k4:
        kpi_card("📅", "Próxima Mantención", proxima_texto, proxima_sub, "#ffedd5")
    with k5:
        kpi_card("🚚", "Equipos Registrados", f"{equipos_registrados}", "Total equipos", "#ccfbf1")

    c1, c2 = st.columns([1.55, 1])

    with c1:
        st.markdown('<div class="panel-title">Histórico de Intervenciones</div>', unsafe_allow_html=True)
        historico = mant_f.copy()
        if "Tipo_Mantencion" in historico.columns:
            historico["Mantencion"] = historico["Tipo_Mantencion"].apply(normalizar_tipo_mantencion)

        if not historico.empty:
            historico = historico.sort_values("Fecha", ascending=False).head(6)
            columnas_base = ["Fecha", "Equipo", "Mantencion", "Descripcion", "Costo_CLP", "Estado_Mantencion"]
            columnas_base = [c for c in columnas_base if c in historico.columns]
            mostrar = historico[columnas_base].copy()
            if "Fecha" in mostrar.columns:
                mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)
            if "Costo_CLP" in mostrar.columns:
                mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)
            mostrar = mostrar.rename(columns={
                "Mantencion": "Tipo",
                "Descripcion": "Descripción",
                "Costo_CLP": "Monto",
                "Estado_Mantencion": "Estado",
            })
            mostrar_tabla_clara(mostrar, height=218)
        else:
            st.info("No existen mantenciones registradas para el filtro aplicado.")

    with c2:
        st.markdown('<div class="panel-title">Distribución de Costos</div>', unsafe_allow_html=True)
        costos_item = construir_consolidado_costos(mant_f, gastos_f)
        st.plotly_chart(crear_donut_costos(costos_item), use_container_width=True)

    c3, c4, c5 = st.columns([1.22, 1.18, 1.18])

    with c3:
        st.markdown('<div class="panel-title">Gastos Adicionales</div>', unsafe_allow_html=True)
        repuestos = gastos_sin_combustible.copy()
        if not repuestos.empty:
            repuestos = repuestos.sort_values("Fecha", ascending=False).head(4)
            columnas_repuestos = ["Fecha", "Equipo", "Tipo_Gasto", "Descripcion", "Costo_CLP"]
            columnas_repuestos = [c for c in columnas_repuestos if c in repuestos.columns]
            mostrar = repuestos[columnas_repuestos].copy()
            if "Fecha" in mostrar.columns:
                mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)
            if "Costo_CLP" in mostrar.columns:
                mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)
            mostrar = mostrar.rename(columns={
                "Tipo_Gasto": "Tipo",
                "Descripcion": "Detalle",
                "Costo_CLP": "Monto",
            })
            mostrar_tabla_clara(mostrar, height=142)
        else:
            st.info("No existen gastos adicionales registrados.")

    with c4:
        st.markdown('<div class="proximas-box">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Próximas Mantenciones</div>', unsafe_allow_html=True)
        proximas = mant_proximas.copy()
        if not proximas.empty:
            for _, fila in proximas.head(6).iterrows():
                equipo = escape_html(fila.get("Equipo", "Sin equipo"))
                categoria = escape_html(fila.get("Categoria", fila.get("Tipo_Mantencion", "")))
                proxima_txt = escape_html(fila.get("Proxima_Texto", formatear_valor_control(fila.get("Proxima_Mantencion", 0), fila.get("Unidad_Control", ""))))
                saldo = formatear_saldo_control(fila.get("Saldo_Restante", 0), fila.get("Unidad_Control", ""))
                estado = str(fila.get("Estado_Control", ""))
                clase = "badge-danger" if estado in ["Vencida", "Crítica", "Vence ahora"] else "badge-warning"
                st.markdown(
                    f"""
                    <div class="next-item">
                        <div>
                            <div class="next-title">{equipo}</div>
                            <div class="next-sub">{categoria}</div>
                            <div class="next-sub">Próx.: {proxima_txt}</div>
                        </div>
                        <div class="badge-days {clase}">{escape_html(saldo)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No existen próximas mantenciones registradas.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c5:
        st.markdown('<div class="panel-title">Evolución de Costos</div>', unsafe_allow_html=True)
        if not mant_f.empty or not gastos_sin_combustible.empty:
            partes = []
            if not mant_f.empty and "Fecha" in mant_f.columns and "Costo_CLP" in mant_f.columns:
                a = mant_f[["Fecha", "Costo_CLP"]].copy()
                a["Costo"] = a["Costo_CLP"].apply(limpiar_numero)
                partes.append(a[["Fecha", "Costo"]])
            if not gastos_sin_combustible.empty and "Fecha" in gastos_sin_combustible.columns and "Costo_CLP" in gastos_sin_combustible.columns:
                b = gastos_sin_combustible[["Fecha", "Costo_CLP"]].copy()
                b["Costo"] = b["Costo_CLP"].apply(limpiar_numero)
                partes.append(b[["Fecha", "Costo"]])
            if partes:
                evolucion = pd.concat(partes, ignore_index=True)
                evolucion["Fecha"] = evolucion["Fecha"].apply(convertir_fecha)
                evolucion = evolucion.dropna(subset=["Fecha"])
                if not evolucion.empty:
                    evolucion["Año"] = evolucion["Fecha"].dt.year
                    evolucion["Mes_Numero"] = evolucion["Fecha"].dt.month
                    evolucion["Mes"] = evolucion["Mes_Numero"].map(MESES)
                    evolucion["Periodo"] = evolucion["Mes"].fillna("") + " " + evolucion["Año"].astype(str)
                    evolucion = evolucion.groupby(["Año", "Mes_Numero", "Periodo"], as_index=False)["Costo"].sum()
                    evolucion = evolucion.sort_values(["Año", "Mes_Numero"])
                    evolucion["Costo_Millones"] = evolucion["Costo"] / 1_000_000
                    fig = px.line(evolucion, x="Periodo", y="Costo_Millones", markers=True, template="plotly_white", custom_data=["Costo"])
                    fig.update_traces(line=dict(width=3), marker=dict(size=7), hovertemplate="Periodo: %{x}<br>Monto: $%{customdata[0]:,.0f}<br>Millones CLP: %{y:.2f} M<extra></extra>")
                    fig.update_layout(title_text="", xaxis_title="", yaxis_title="", showlegend=False, margin=dict(l=8, r=8, t=2, b=8))
                    fig.update_yaxes(tickformat=".2f", ticksuffix="M")
                    fig = aplicar_formato_grafico(fig, 220)
                    fig.update_layout(title_text="", margin=dict(l=16, r=12, t=2, b=28))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sin costos con fecha para graficar.")
            else:
                st.info("Sin información de costos para graficar.")
        else:
            st.info("Sin información de costos para graficar.")

    st.markdown('<div class="panel-title">Estado de los Equipos</div>', unsafe_allow_html=True)
    cols = st.columns(min(7, max(1, len(equipos_f)))) if not equipos_f.empty else []
    for idx, (_, fila) in enumerate(equipos_f.iterrows()):
        with cols[idx % len(cols)]:
            tarjeta_equipo(fila)


st.markdown(
    """
<style>
/* V5.6: sube el encabezado principal y aprovecha el espacio superior */
.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"] {
    padding-top: 0px !important;
}
.main-fixed-header {
    min-height: 42px !important;
    margin-top: -34px !important;
    margin-bottom: -4px !important;
    padding-top: 0px !important;
    align-items: flex-end !important;
}
.main-fixed-title,
.title-main {
    font-size: clamp(28px, 2.15vw, 37px) !important;
    line-height: 1.0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.main-fixed-logo,
.header-logo-box {
    margin-top: 0px !important;
    padding-top: 0px !important;
}
.main-fixed-logo img,
.header-logo-box img {
    width: 118px !important;
    max-width: 118px !important;
}
.main-fixed-header-spacer,
.header-separador {
    height: 2px !important;
    min-height: 2px !important;
}

/* V5.6: tabla de Gastos Adicionales más compacta y sin barra horizontal */
.tabla-clara-wrap {
    overflow-x: hidden !important;
    overflow-y: auto !important;
}
.tabla-clara {
    table-layout: fixed !important;
    width: 100% !important;
    min-width: 0 !important;
    font-size: 11.4px !important;
}
.tabla-clara thead th,
.tabla-clara tbody td {
    padding: 7px 8px !important;
    white-space: normal !important;
    word-break: normal !important;
    overflow-wrap: anywhere !important;
    line-height: 1.22 !important;
}
.tabla-clara td.monto,
.tabla-clara th.monto,
.tabla-clara td:last-child,
.tabla-clara th:last-child {
    white-space: nowrap !important;
    overflow-wrap: normal !important;
    text-align: right !important;
}

/* V5.6: botón de actualización más corto */
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    font-size: 13.6px !important;
}
</style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# AJUSTE FINAL V5.9
# - Habilita botón nativo para minimizar menú y agranda sidebar.
# - Deja un espacio controlado bajo el título principal.
# - Ajusta dona y evolución de costos dentro de sus marcos.
# - Mejora resumen de próximas mantenciones en Dashboard.
# =========================================================

def crear_donut_costos(costos_item):
    """Dona de costos ajustada para que porcentajes y leyenda queden dentro del marco."""
    fig = go.Figure()

    if costos_item is None or costos_item.empty:
        fig.update_layout(
            height=292,
            paper_bgcolor="rgba(255,255,255,0.82)",
            plot_bgcolor="rgba(255,255,255,0.82)",
            annotations=[dict(text="Sin costos", x=0.5, y=0.5, showarrow=False, font_size=16, font_color="#0f172a")],
            margin=dict(l=8, r=8, t=12, b=16),
        )
        return fig

    total = float(costos_item["Costo"].sum())

    fig.add_trace(
        go.Pie(
            labels=costos_item["Item"],
            values=costos_item["Costo"],
            hole=0.62,
            sort=False,
            direction="clockwise",
            textinfo="percent",
            texttemplate="%{percent:.1%}",
            textposition="auto",
            insidetextorientation="radial",
            textfont=dict(color="white", size=13, family="Arial Black"),
            outsidetextfont=dict(color="#0f172a", size=12, family="Arial Black"),
            hovertemplate="<b>%{label}</b><br>Monto: %{customdata}<br>Participación: %{percent}<extra></extra>",
            customdata=[pesos(v) for v in costos_item["Costo"]],
            domain=dict(x=[0.05, 0.95], y=[0.30, 0.90]),
            showlegend=True,
        )
    )

    fig.update_layout(
        height=292,
        paper_bgcolor="rgba(255,255,255,0.82)",
        plot_bgcolor="rgba(255,255,255,0.82)",
        font=dict(color="#0f172a", size=12),
        margin=dict(l=8, r=8, t=16, b=58),
        annotations=[
            dict(
                text="Total<br><b>" + pesos(total) + "</b>",
                x=0.50,
                y=0.60,
                xref="paper",
                yref="paper",
                font_size=14,
                font_color="#0f172a",
                showarrow=False,
                align="center",
            )
        ],
        legend=dict(
            title=dict(text="Tipo de costo", font=dict(size=11, color="#0f172a")),
            orientation="h",
            x=0.50,
            y=0.01,
            xanchor="center",
            yanchor="bottom",
            font=dict(size=11, color="#0f172a", family="Arial"),
            bgcolor="rgba(255,255,255,0.82)",
            bordercolor="rgba(15,23,42,0.16)",
            borderwidth=1,
            itemclick=False,
            itemdoubleclick=False,
        ),
        uniformtext_minsize=8,
        uniformtext_mode="show",
    )
    return fig


def pagina_dashboard(equipos_f, mant_f, gastos_f, combustible_f, proximas_originales, filtro_equipo):
    """Dashboard Ejecutivo V5.9: distribución, próximas y evolución mejor encuadradas."""
    gastos_sin_combustible = gastos_no_combustible(gastos_f)

    costo_mantenciones = float(mant_f["Costo_CLP"].sum()) if "Costo_CLP" in mant_f.columns else 0.0
    costo_gastos = float(gastos_sin_combustible["Costo_CLP"].sum()) if "Costo_CLP" in gastos_sin_combustible.columns else 0.0
    costo_total = costo_mantenciones + costo_gastos

    mant_realizadas = len(mant_f)
    repuestos_utilizados = len(gastos_sin_combustible)
    equipos_registrados = len(equipos_f)

    if "Proxima_Mantencion" not in proximas_originales.columns:
        proximas_originales = pd.DataFrame(columns=[
            "Equipo", "Categoria", "Tipo_Mantencion", "Proxima_Mantencion",
            "Km_Horometro_Actual", "Unidad_Control", "Costo_CLP"
        ])

    mant_proximas = proximas_originales.copy()
    if "Proxima_Mantencion" in mant_proximas.columns:
        mant_proximas["Proxima_Mantencion"] = mant_proximas["Proxima_Mantencion"].apply(limpiar_numero)
        mant_proximas = mant_proximas[mant_proximas["Proxima_Mantencion"] > 0].copy()

    if filtro_equipo != "Todos los equipos" and "Equipo" in mant_proximas.columns:
        mant_proximas = mant_proximas[mant_proximas["Equipo"] == filtro_equipo]

    mant_proximas = resumen_proximas_por_equipo(mant_proximas) if not mant_proximas.empty else mant_proximas

    if not mant_proximas.empty:
        proxima_fila = mant_proximas.iloc[0]
        equipo_proximo = str(proxima_fila.get("Equipo", "Sin equipo")).strip()
        proxima_valor = proxima_fila.get("Proxima_Texto", "Sin dato")
        proxima_estado = proxima_fila.get("Texto_Estado", "Sin análisis")
        proxima_texto = equipo_proximo if equipo_proximo else "Sin equipo"
        proxima_sub = f"Próx.: {proxima_valor} | {proxima_estado}"
    else:
        proxima_texto = "Sin registro"
        proxima_sub = "No programada"

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card("🛠️", "Mantenciones", f"{mant_realizadas}", "Registros del período", "#dbeafe")
    with k2:
        kpi_card("💲", "Monto Total", pesos(costo_total), "Costos del período", "#dcfce7")
    with k3:
        kpi_card("🧰", "Gastos Adic.", f"{repuestos_utilizados}", "Repuestos, mantenciones y administrativos", "#f3e8ff")
    with k4:
        kpi_card("📅", "Próxima Mantención", proxima_texto, proxima_sub, "#ffedd5")
    with k5:
        kpi_card("🚚", "Equipos Registrados", f"{equipos_registrados}", "Total equipos", "#ccfbf1")

    c1, c2 = st.columns([1.55, 1])

    with c1:
        st.markdown('<div class="panel-title">Histórico de Intervenciones</div>', unsafe_allow_html=True)
        historico = mant_f.copy()
        if "Tipo_Mantencion" in historico.columns:
            historico["Mantencion"] = historico["Tipo_Mantencion"].apply(normalizar_tipo_mantencion)

        if not historico.empty:
            historico = historico.sort_values("Fecha", ascending=False).head(6)
            columnas_base = ["Fecha", "Equipo", "Mantencion", "Descripcion", "Costo_CLP", "Estado_Mantencion"]
            columnas_base = [c for c in columnas_base if c in historico.columns]
            mostrar = historico[columnas_base].copy()
            if "Fecha" in mostrar.columns:
                mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)
            if "Costo_CLP" in mostrar.columns:
                mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)
            mostrar = mostrar.rename(columns={
                "Mantencion": "Tipo",
                "Descripcion": "Descripción",
                "Costo_CLP": "Monto",
                "Estado_Mantencion": "Estado",
            })
            mostrar_tabla_clara(mostrar, height=230)
        else:
            st.info("No existen mantenciones registradas para el filtro aplicado.")

    with c2:
        st.markdown('<div class="dashboard-costos-spacer"></div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title chart-title dashboard-costos-title">Distribución de Costos</div>', unsafe_allow_html=True)
        costos_item = construir_consolidado_costos(mant_f, gastos_f)
        st.plotly_chart(crear_donut_costos(costos_item), use_container_width=True)

    c3, c4, c5 = st.columns([1.10, 1.38, 1.36])

    with c3:
        st.markdown('<div class="panel-title">Gastos Adicionales</div>', unsafe_allow_html=True)
        repuestos = gastos_sin_combustible.copy()
        if not repuestos.empty:
            repuestos = repuestos.sort_values("Fecha", ascending=False).head(4)
            columnas_repuestos = ["Fecha", "Equipo", "Tipo_Gasto", "Descripcion", "Costo_CLP"]
            columnas_repuestos = [c for c in columnas_repuestos if c in repuestos.columns]
            mostrar = repuestos[columnas_repuestos].copy()
            if "Fecha" in mostrar.columns:
                mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)
            if "Costo_CLP" in mostrar.columns:
                mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)
            mostrar = mostrar.rename(columns={
                "Tipo_Gasto": "Tipo",
                "Descripcion": "Detalle",
                "Costo_CLP": "Monto",
            })
            mostrar_tabla_clara(mostrar, height=122)
        else:
            st.info("No existen gastos adicionales registrados.")

    with c4:
        st.markdown('<div class="proximas-box dashboard-proximas">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Próximas Mantenciones</div>', unsafe_allow_html=True)
        proximas = mant_proximas.copy()
        if not proximas.empty:
            for _, fila in proximas.head(6).iterrows():
                equipo = escape_html(fila.get("Equipo", "Sin equipo"))
                categoria = escape_html(fila.get("Categoria", fila.get("Tipo_Mantencion", "")))
                proxima_txt = escape_html(fila.get("Proxima_Texto", formatear_valor_control(fila.get("Proxima_Mantencion", 0), fila.get("Unidad_Control", ""))))
                saldo = formatear_saldo_control(fila.get("Saldo_Restante", 0), fila.get("Unidad_Control", ""))
                estado = str(fila.get("Estado_Control", ""))
                clase = "badge-danger" if estado in ["Vencida", "Crítica", "Vence ahora"] else "badge-warning"
                st.markdown(
                    f"""
                    <div class="next-item">
                        <div class="next-info">
                            <div class="next-title">{equipo}</div>
                            <div class="next-sub-line">{categoria} · Próx.: {proxima_txt}</div>
                        </div>
                        <div class="badge-days {clase}">{escape_html(saldo)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No existen próximas mantenciones registradas.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c5:
        st.markdown('<div class="panel-title chart-title">Evolución de Costos</div>', unsafe_allow_html=True)
        if not mant_f.empty or not gastos_sin_combustible.empty:
            partes = []
            if not mant_f.empty and "Fecha" in mant_f.columns and "Costo_CLP" in mant_f.columns:
                a = mant_f[["Fecha", "Costo_CLP"]].copy()
                a["Costo"] = a["Costo_CLP"].apply(limpiar_numero)
                partes.append(a[["Fecha", "Costo"]])
            if not gastos_sin_combustible.empty and "Fecha" in gastos_sin_combustible.columns and "Costo_CLP" in gastos_sin_combustible.columns:
                b = gastos_sin_combustible[["Fecha", "Costo_CLP"]].copy()
                b["Costo"] = b["Costo_CLP"].apply(limpiar_numero)
                partes.append(b[["Fecha", "Costo"]])
            if partes:
                evolucion = pd.concat(partes, ignore_index=True)
                evolucion["Fecha"] = evolucion["Fecha"].apply(convertir_fecha)
                evolucion = evolucion.dropna(subset=["Fecha"])
                if not evolucion.empty:
                    evolucion["Año"] = evolucion["Fecha"].dt.year
                    evolucion["Mes_Numero"] = evolucion["Fecha"].dt.month
                    evolucion["Mes"] = evolucion["Mes_Numero"].map(MESES)
                    evolucion["Periodo"] = evolucion["Mes"].fillna("") + " " + evolucion["Año"].astype(str)
                    evolucion = evolucion.groupby(["Año", "Mes_Numero", "Periodo"], as_index=False)["Costo"].sum()
                    evolucion = evolucion.sort_values(["Año", "Mes_Numero"])
                    evolucion["Costo_Millones"] = evolucion["Costo"] / 1_000_000
                    fig = px.line(evolucion, x="Periodo", y="Costo_Millones", markers=True, template="plotly_white", custom_data=["Costo"])
                    fig.update_traces(line=dict(width=3), marker=dict(size=7), hovertemplate="Periodo: %{x}<br>Monto: $%{customdata[0]:,.0f}<br>Millones CLP: %{y:.2f} M<extra></extra>")
                    fig.update_layout(title_text="", xaxis_title="", yaxis_title="", showlegend=False, margin=dict(l=48, r=18, t=18, b=42))
                    fig.update_yaxes(tickformat=".2f", ticksuffix="M", rangemode="tozero")
                    fig = aplicar_formato_grafico(fig, 250)
                    fig.update_layout(title_text="", margin=dict(l=50, r=18, t=18, b=42))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sin costos con fecha para graficar.")
            else:
                st.info("Sin información de costos para graficar.")
        else:
            st.info("Sin información de costos para graficar.")

    st.markdown('<div class="panel-title equipos-title-dashboard">Estado de los Equipos</div>', unsafe_allow_html=True)
    cols = st.columns(min(7, max(1, len(equipos_f)))) if not equipos_f.empty else []
    for idx, (_, fila) in enumerate(equipos_f.iterrows()):
        with cols[idx % len(cols)]:
            tarjeta_equipo(fila)


st.markdown(
    """
<style>
/* V5.9 aplicado antes de cargar la pantalla */
:root {
    --menu-panel-width: 345px !important;
    --menu-inner-width: 304px !important;
    --menu-panel-width-final: 345px !important;
    --menu-inner-width-final: 304px !important;
}

section[data-testid="stSidebar"] {
    width: 345px !important;
    min-width: 345px !important;
    max-width: 345px !important;
}
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: 345px !important;
    min-width: 345px !important;
    max-width: 345px !important;
}
[data-testid="stAppViewContainer"] > .main,
section.main,
main {
    margin-left: 345px !important;
    width: calc(100vw - 345px) !important;
    max-width: calc(100vw - 345px) !important;
}

/* Vuelve visible el botón nativo para minimizar/expandir el menú */
[data-testid="collapsedControl"],
button[title="Collapse sidebar"],
button[title="Close sidebar"],
button[aria-label="Collapse sidebar"],
button[aria-label="Close sidebar"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    height: 34px !important;
    min-height: 34px !important;
    width: 34px !important;
    min-width: 34px !important;
    z-index: 10050 !important;
}

.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"],
section.main > div {
    margin-top: -62px !important;
    padding-top: 0px !important;
}
.main-fixed-header {
    min-height: 58px !important;
    height: 58px !important;
    margin-top: 0px !important;
    margin-bottom: 12px !important;
    padding-top: 8px !important;
    align-items: flex-end !important;
}
.main-fixed-title,
.title-main {
    font-size: clamp(28px, 2.1vw, 37px) !important;
    line-height: 1.03 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.main-fixed-logo img,
.header-logo-box img {
    width: 116px !important;
    max-width: 116px !important;
}
.main-fixed-header-spacer,
.header-separador {
    height: 8px !important;
    min-height: 8px !important;
}

.panel-title {
    margin-top: 7px !important;
    margin-bottom: 5px !important;
}
.chart-title {
    margin-bottom: 2px !important;
}

/* Gráficos dentro del marco */
[data-testid="stPlotlyChart"] {
    overflow: hidden !important;
    border-radius: 12px !important;
    margin-bottom: 0px !important;
}
[data-testid="stPlotlyChart"] > div {
    max-height: 310px !important;
}

/* Próximas mantenciones del Dashboard: compacto, sin montarse */
.dashboard-proximas .next-item,
.proximas-box .next-item {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) auto !important;
    align-items: center !important;
    column-gap: 8px !important;
    min-height: 34px !important;
    padding: 2px 0 !important;
    border-bottom: 1px solid rgba(148, 163, 184, 0.22) !important;
}
.dashboard-proximas .next-info,
.proximas-box .next-info {
    min-width: 0 !important;
}
.dashboard-proximas .next-title,
.proximas-box .next-title {
    font-size: 11.8px !important;
    line-height: 1.02 !important;
    margin-bottom: 1px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.dashboard-proximas .next-sub-line,
.proximas-box .next-sub-line,
.dashboard-proximas .next-sub,
.proximas-box .next-sub {
    display: block !important;
    font-size: 9.2px !important;
    line-height: 1.05 !important;
    margin: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.dashboard-proximas .badge-days,
.proximas-box .badge-days {
    min-width: 76px !important;
    max-width: 86px !important;
    font-size: 8.7px !important;
    padding: 4px 6px !important;
    white-space: nowrap !important;
    text-align: center !important;
}
</style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# CORRECCIÓN FINAL URGENTE V6.1
# - Menú desplegable real: botón para minimizar / expandir.
# - Dashboard principal más compacto en Gastos / Próximas Mantenciones.
# - Próximas mantenciones con estructura clara por equipo.
# - Logo superior derecho SAIVAM más grande, manteniendo el fondo actual.
# =========================================================

def _menu_colapsado():
    """Menú fijo. Se elimina la opción de minimizar/expandir para evitar perder el menú."""
    st.session_state["menu_colapsado"] = False
    return False


def aplicar_ajustes_finales_ui():
    """CSS final dinámico. Se llama antes y después de construir la página para ganar prioridad."""
    colapsado = _menu_colapsado()
    menu_w = 86 if colapsado else 276
    inner_w = 58 if colapsado else 244
    logo_w = 168

    css_extra_colapsado = ""
    if colapsado:
        css_extra_colapsado = f"""
section[data-testid="stSidebar"] .menu-text,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] .menu-filter-area,
section[data-testid="stSidebar"] .menu-botones-title {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}

section[data-testid="stSidebar"] .menu-brand {{
    justify-content: center !important;
    width: {inner_w}px !important;
    max-width: {inner_w}px !important;
    margin: 2px auto 8px auto !important;
    gap: 0 !important;
}}

section[data-testid="stSidebar"] .menu-icon-img {{
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    max-width: 44px !important;
}}

section[data-testid="stSidebar"] .menu-line {{
    width: {inner_w}px !important;
    max-width: {inner_w}px !important;
    margin: 8px auto !important;
}}

section[data-testid="stSidebar"] .menu-active-item,
section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
    justify-content: center !important;
    text-align: center !important;
    padding: 0 !important;
    font-size: 20px !important;
}}

section[data-testid="stSidebar"] .menu-toggle-wrap,
section[data-testid="stSidebar"] .menu-toggle-wrap div[data-testid="stButton"],
section[data-testid="stSidebar"] .menu-toggle-wrap div[data-testid="stButton"] button {{
    width: 48px !important;
    min-width: 48px !important;
    max-width: 48px !important;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] .menu-active-item,
section[data-testid="stSidebar"] .menu-toggle-wrap {{
    margin-left: auto !important;
    margin-right: auto !important;
}}

section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] .menu-active-item {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}}

section[data-testid="stSidebar"] div[data-testid="stButton"] button *,
section[data-testid="stSidebar"] div[data-testid="stButton"] button p,
section[data-testid="stSidebar"] .menu-active-item * {{
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    margin-left: auto !important;
    margin-right: auto !important;
}}
"""

    st.markdown(
        f"""
<style>
:root {{
    --menu-panel-width: {menu_w}px !important;
    --menu-inner-width: {inner_w}px !important;
    --menu-panel-width-final: {menu_w}px !important;
    --menu-inner-width-final: {inner_w}px !important;
    --content-padding-x: 14px !important;
}}

section[data-testid="stSidebar"] {{
    width: {menu_w}px !important;
    min-width: {menu_w}px !important;
    max-width: {menu_w}px !important;
    top: 0 !important;
    left: 0 !important;
    background: #020617 !important;
    transition: width .20s ease, min-width .20s ease, max-width .20s ease !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;
    z-index: 99999 !important;
}}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
    width: {menu_w}px !important;
    min-width: {menu_w}px !important;
    max-width: {menu_w}px !important;
    padding: 9px 12px 13px 12px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}}

section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-brand,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .menu-active-item {{
    width: {inner_w}px !important;
    min-width: {inner_w}px !important;
    max-width: {inner_w}px !important;
    box-sizing: border-box !important;
}}

section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] .menu-active-item {{
    width: {inner_w}px !important;
    min-width: {inner_w}px !important;
    max-width: {inner_w}px !important;
    min-height: 46px !important;
    height: 46px !important;
    border-radius: 14px !important;
    margin-bottom: 7px !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}}

section[data-testid="stSidebar"] .menu-toggle-wrap,
section[data-testid="stSidebar"] .menu-toggle-wrap div[data-testid="stButton"],
section[data-testid="stSidebar"] .menu-toggle-wrap div[data-testid="stButton"] button {{
    width: 48px !important;
    min-width: 48px !important;
    max-width: 48px !important;
    box-sizing: border-box !important;
}}

section[data-testid="stSidebar"] .menu-toggle-wrap div[data-testid="stButton"] button {{
    height: 42px !important;
    min-height: 42px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
    border: 1px solid rgba(219,234,254,.95) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 20px !important;
    font-weight: 950 !important;
    box-shadow: 0 8px 20px rgba(37,99,235,.35) !important;
}}

section[data-testid="stSidebar"] .menu-toggle-wrap {{
    margin: 0 0 10px 0 !important;
}}

[data-testid="stAppViewContainer"] > .main,
div[data-testid="stMain"],
section.main,
main {{
    margin-left: {menu_w}px !important;
    width: calc(100vw - {menu_w}px) !important;
    max-width: calc(100vw - {menu_w}px) !important;
}}

.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"] {{
    padding-left: 14px !important;
    padding-right: 14px !important;
    max-width: 100% !important;
    min-width: 0 !important;
}}


.main-fixed-header {{
    min-height: 58px !important;
    height: 58px !important;
    margin-bottom: 8px !important;
    padding: 4px 12px 0 0 !important;
    display: flex !important;
    align-items: flex-end !important;
    justify-content: space-between !important;
}}

.main-fixed-logo img,
.header-logo-box img {{
    width: {logo_w}px !important;
    max-width: {logo_w}px !important;
    height: auto !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    object-fit: contain !important;
}}

.main-fixed-title,
.title-main {{
    font-size: clamp(30px, 2.15vw, 40px) !important;
    line-height: 1.03 !important;
    margin: 0 !important;
    padding: 0 !important;
}}

div[data-testid="stVerticalBlock"] {{
    gap: 0.22rem !important;
}}

div[data-testid="stHorizontalBlock"] {{
    gap: 0.78rem !important;
}}

.panel-title {{
    display: block !important;
    clear: both !important;
    position: relative !important;
    z-index: 5 !important;
    color: #0f172a !important;
    font-weight: 950 !important;
    font-size: clamp(18px, 1.15vw, 22px) !important;
    line-height: 1.22 !important;
    min-height: 28px !important;
    margin-top: 16px !important;
    margin-bottom: 12px !important;
    padding: 2px 0 6px 0 !important;
    overflow: visible !important;
}}

.section-head {{
    display: block !important;
    clear: both !important;
    position: relative !important;
    z-index: 6 !important;
    width: 100% !important;
    margin: 2px 0 14px 0 !important;
    padding: 0 0 2px 0 !important;
    overflow: visible !important;
}}

.section-head .panel-title,
.page-section-title {{
    margin-top: 0 !important;
    margin-bottom: 4px !important;
    padding: 0 !important;
    min-height: 26px !important;
}}

.panel-subtitle {{
    display: block !important;
    clear: both !important;
    color: #334155 !important;
    font-size: 15px !important;
    line-height: 1.25 !important;
    font-weight: 850 !important;
    margin: 0 0 8px 0 !important;
    padding: 0 !important;
    position: relative !important;
    z-index: 6 !important;
}}

[data-testid="stMarkdownContainer"]:has(.panel-title),
[data-testid="stMarkdownContainer"]:has(.section-head) {{
    overflow: visible !important;
}}

.tabla-clara-wrap {{
    margin-top: 8px !important;
}}

.dashboard-proximas .panel-title,
.proximas-box .panel-title,
.chart-title,
.panel-title.chart-title {{
    margin-top: 0 !important;
    margin-bottom: 8px !important;
    min-height: 24px !important;
    padding-bottom: 4px !important;
}}

.kpi-card {{
    min-height: 118px !important;
    padding: 15px 17px !important;
}}

.kpi-icon {{
    width: 44px !important;
    height: 44px !important;
    margin-bottom: 7px !important;
}}

.dashboard-proximas,
.proximas-box {{
    background: rgba(255,255,255,.72) !important;
    border: 1px solid rgba(203,213,225,.72) !important;
    border-radius: 16px !important;
    padding: 7px 10px !important;
    margin-top: 0 !important;
    box-shadow: 0 10px 24px rgba(15,23,42,.045) !important;
}}

.dashboard-proximas .next-item,
.proximas-box .next-item {{
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 96px !important;
    align-items: center !important;
    column-gap: 10px !important;
    min-height: 54px !important;
    padding: 7px 0 !important;
    border-bottom: 1px solid rgba(148,163,184,.28) !important;
}}

.dashboard-proximas .next-item:last-child,
.proximas-box .next-item:last-child {{
    border-bottom: 0 !important;
}}

.dashboard-proximas .next-title,
.proximas-box .next-title {{
    font-size: 13.2px !important;
    line-height: 1.14 !important;
    font-weight: 950 !important;
    color: #0f172a !important;
    margin-bottom: 3px !important;
    white-space: normal !important;
    overflow: visible !important;
}}

.dashboard-proximas .next-sub,
.dashboard-proximas .next-sub-line,
.proximas-box .next-sub,
.proximas-box .next-sub-line {{
    font-size: 11.3px !important;
    line-height: 1.18 !important;
    font-weight: 750 !important;
    color: #334155 !important;
    margin: 0 !important;
    white-space: normal !important;
    overflow: visible !important;
}}

.dashboard-proximas .next-meta,
.proximas-box .next-meta {{
    display: flex !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
    margin-top: 2px !important;
}}

.dashboard-proximas .badge-days,
.proximas-box .badge-days {{
    width: 96px !important;
    min-width: 96px !important;
    max-width: 96px !important;
    font-size: 10.2px !important;
    line-height: 1.1 !important;
    font-weight: 950 !important;
    padding: 7px 6px !important;
    white-space: normal !important;
    text-align: center !important;
    border-radius: 999px !important;
}}

.dashboard-compact-table [data-testid="stDataFrame"] {{
    margin-top: 0 !important;
}}

div[data-testid="stPlotlyChart"] {{
    margin-top: 0 !important;
}}

{css_extra_colapsado}

@media (max-width: 1400px) {{
    .main-fixed-logo img,
    .header-logo-box img {{
        width: 148px !important;
        max-width: 148px !important;
    }}

    .main-fixed-title,
    .title-main {{
        font-size: clamp(27px, 2vw, 36px) !important;
    }}
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def construir_menu(equipos, mantenciones, gastos, combustible, checklist, documentos):
    """Menú lateral con botón real de minimizar / expandir."""
    colapsado = _menu_colapsado()

    ruta_logo_menu = (
        buscar_imagen_por_nombre("logoredondo")
        or buscar_imagen_por_nombre("logo redondo")
        or buscar_imagen_por_nombre("logo_redondo")
        or buscar_imagen_por_nombre("logo-redondo")
    )

    if ruta_logo_menu:
        logo_menu_b64 = archivo_a_base64(ruta_logo_menu)
        logo_menu_mime = extension_mime(ruta_logo_menu)
        icono_menu_html = (
            '<div class="menu-icon-img">'
            f'<img src="data:{logo_menu_mime};base64,{logo_menu_b64}" alt="Logo menú">'
            '</div>'
        )
    else:
        icono_menu_html = '<div class="menu-icon">🚜</div>'

    estado_menu_css = "menu-state-collapsed" if colapsado else "menu-state-expanded"

    st.markdown(
        f"""
        <div class="menu-bg"></div>
        <div class="menu-marker {estado_menu_css}"></div>
        <div class="menu-panel-content">
            <div class="menu-brand">
                {icono_menu_html}
                <div class="menu-text">
                    <div class="menu-title">SEGUIMIENTO<br>EQUIPOS MÓVILES</div>
                    <div class="menu-subtitle">SAIVAM · MULCHÉN</div>
                </div>
            </div>
            <hr class="menu-line">
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Menú fijo: se elimina el botón de minimizar/expandir.
    st.markdown('<div class="menu-fixed-spacer"></div>', unsafe_allow_html=True)

    paginas_menu = {
        "panel": ("📊", "Dashboard Ejecutivo"),
        "equipos": ("🚚", "Equipos"),
        "mantenciones": ("🛠️", "Mantenciones"),
        "repuestos": ("🧾", "Gastos Adicionales"),
        "costos": ("💰", "Costos"),
        "proximas": ("📅", "Próximas Mantenciones"),
        "alertas": ("🔔", "Alertas"),
        "documentos": ("📁", "Documentación Legal"),
    }

    pagina_actual = st.query_params.get("pagina", "panel")
    if pagina_actual not in paginas_menu:
        pagina_actual = "panel"
        st.query_params["pagina"] = "panel"

    st.markdown('<div class="menu-botones-title"></div>', unsafe_allow_html=True)

    for clave, (icono, nombre) in paginas_menu.items():
        es_actual = clave == pagina_actual
        texto_completo = f"{icono} {nombre}"
        texto_visible = icono if colapsado else texto_completo

        if es_actual:
            st.markdown(
                f'<div class="menu-active-item" title="{escape_html(nombre)}">{escape_html(texto_visible)}</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.button(
                texto_visible,
                key=f"menu_{clave}",
                help=nombre,
                use_container_width=True,
            ):
                st.query_params["pagina"] = clave
                st.session_state["_saivam_mobile_menu_open"] = False
                st.rerun()

    st.markdown('<hr class="menu-line">', unsafe_allow_html=True)

    if st.button("🔄" if colapsado else "🔄 Actualizar", key="actualizar_base_datos", help="Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.session_state["_saivam_mobile_menu_open"] = False
        st.rerun()

    pagina = f"{paginas_menu[pagina_actual][0]} {paginas_menu[pagina_actual][1]}"

    equipos_disponibles = (
        ["Todos los equipos"]
        + equipos["Equipo"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda x: x != ""]
        .drop_duplicates()
        .tolist()
    )

    anios_base = pd.concat(
        [
            mantenciones["Año"],
            gastos["Año"],
            combustible["Año"],
            checklist["Año"],
            documentos["Año"],
        ],
        ignore_index=True,
    )

    anios_disponibles = sorted(
        [
            int(x)
            for x in anios_base.dropna().unique().tolist()
            if str(x) != "nan"
        ]
    )

    opciones_anio = ["Todos"] + anios_disponibles
    opciones_mes = ["Todos"] + list(MESES.values())

    if st.session_state.get("filtro_equipo_menu", "Todos los equipos") not in equipos_disponibles:
        st.session_state["filtro_equipo_menu"] = "Todos los equipos"
    if st.session_state.get("filtro_anio_menu", "Todos") not in opciones_anio:
        st.session_state["filtro_anio_menu"] = "Todos"
    if st.session_state.get("filtro_mes_menu", "Todos") not in opciones_mes:
        st.session_state["filtro_mes_menu"] = "Todos"

    if not colapsado:
        st.markdown('<hr class="menu-line"><div class="menu-filter-area">', unsafe_allow_html=True)
        filtro_equipo = st.selectbox("Equipo", equipos_disponibles, key="filtro_equipo_menu")
        filtro_anio = st.selectbox("Año", opciones_anio, key="filtro_anio_menu")
        filtro_mes = st.selectbox("Mes", opciones_mes, key="filtro_mes_menu")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="menu-footer-box">
                <div class="menu-info">
                    Versión {VERSION}<br>
                    <b>Actualización:</b><br>
                    {datetime.now().strftime("%d/%m/%Y %H:%M")}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        filtro_equipo = st.session_state.get("filtro_equipo_menu", "Todos los equipos")
        filtro_anio = st.session_state.get("filtro_anio_menu", "Todos")
        filtro_mes = st.session_state.get("filtro_mes_menu", "Todos")

        if filtro_equipo not in equipos_disponibles:
            filtro_equipo = "Todos los equipos"
        if filtro_anio not in opciones_anio:
            filtro_anio = "Todos"
        if filtro_mes not in opciones_mes:
            filtro_mes = "Todos"

    return pagina, filtro_equipo, filtro_anio, filtro_mes


def crear_donut_costos(costos_item):
    """Dona más baja para reducir espacio vertical del Dashboard."""
    fig = go.Figure()

    if costos_item is None or costos_item.empty:
        fig.update_layout(
            height=248,
            paper_bgcolor="rgba(255,255,255,0.82)",
            plot_bgcolor="rgba(255,255,255,0.82)",
            annotations=[dict(text="Sin costos", x=0.5, y=0.5, showarrow=False, font_size=15, font_color="#0f172a")],
            margin=dict(l=6, r=6, t=10, b=12),
        )
        return fig

    total = float(costos_item["Costo"].sum())

    fig.add_trace(
        go.Pie(
            labels=costos_item["Item"],
            values=costos_item["Costo"],
            hole=0.62,
            sort=False,
            direction="clockwise",
            textinfo="percent",
            texttemplate="%{percent:.1%}",
            textposition="auto",
            insidetextorientation="radial",
            textfont=dict(color="white", size=12, family="Arial Black"),
            outsidetextfont=dict(color="#0f172a", size=11, family="Arial Black"),
            hovertemplate="<b>%{label}</b><br>Monto: %{customdata}<br>Participación: %{percent}<extra></extra>",
            customdata=[pesos(v) for v in costos_item["Costo"]],
            domain=dict(x=[0.05, 0.95], y=[0.31, 0.91]),
            showlegend=True,
        )
    )

    fig.update_layout(
        height=248,
        paper_bgcolor="rgba(255,255,255,0.82)",
        plot_bgcolor="rgba(255,255,255,0.82)",
        font=dict(color="#0f172a", size=11),
        margin=dict(l=6, r=6, t=10, b=50),
        annotations=[
            dict(
                text="Total<br><b>" + pesos(total) + "</b>",
                x=0.50,
                y=0.61,
                xref="paper",
                yref="paper",
                font_size=13,
                font_color="#0f172a",
                showarrow=False,
                align="center",
            )
        ],
        legend=dict(
            title=dict(text="Tipo de costo", font=dict(size=10, color="#0f172a")),
            orientation="h",
            x=0.50,
            y=0.01,
            xanchor="center",
            yanchor="bottom",
            font=dict(size=10, color="#0f172a", family="Arial"),
            bgcolor="rgba(255,255,255,0.82)",
            bordercolor="rgba(15,23,42,0.16)",
            borderwidth=1,
            itemclick=False,
            itemdoubleclick=False,
        ),
        uniformtext_minsize=8,
        uniformtext_mode="show",
    )
    return fig


def _render_item_proxima_dashboard(fila):
    """Devuelve una fila HTML limpia para Próximas Mantenciones del Dashboard.

    Ajuste V6.8 solicitado:
    - No muestra columna ni texto "Próxima".
    - Debajo del nombre del equipo muestra la lectura actual de Km/Horómetro.
    - El badge naranjo/rojo queda dentro del mismo cuadro.
    """
    equipo = escape_html(fila.get("Equipo", "Sin equipo"))

    unidad = unidad_control_texto(fila.get("Unidad_Control", ""))
    actual_num = limpiar_numero(fila.get("Km_Horometro_Actual", 0))
    saldo_num = limpiar_numero(fila.get("Saldo_Restante", 0))

    actual_txt = f"{numero(actual_num)} {unidad}" if actual_num > 0 else "Sin dato"
    saldo_txt = formatear_saldo_control(saldo_num, unidad)

    if saldo_num < 0:
        clase_badge = "badge-days badge-overdue"
        badge_txt = f"Vencida {saldo_txt}"
    elif saldo_num == 0:
        clase_badge = "badge-days badge-danger"
        badge_txt = f"Faltan {saldo_txt}"
    else:
        clase_badge = "badge-days badge-warning"
        badge_txt = f"Faltan {saldo_txt}"

    return f"""
<div class="next-item next-row-v68">
    <div class="next-info-v68">
        <div class="next-equipo-v68">{equipo}</div>
        <div class="next-actual-v68"><span>Km/Horómetro actual:</span> {escape_html(actual_txt)}</div>
    </div>
    <div class="{clase_badge} next-badge-v68">{escape_html(badge_txt)}</div>
</div>
"""

def pagina_dashboard(equipos_f, mant_f, gastos_f, combustible_f, proximas_originales, filtro_equipo):
    """Dashboard Ejecutivo compacto y ordenado."""
    gastos_sin_combustible = gastos_no_combustible(gastos_f)

    costo_mantenciones = float(mant_f["Costo_CLP"].sum()) if "Costo_CLP" in mant_f.columns else 0.0
    costo_gastos = float(gastos_sin_combustible["Costo_CLP"].sum()) if "Costo_CLP" in gastos_sin_combustible.columns else 0.0
    costo_total = costo_mantenciones + costo_gastos

    mant_realizadas = len(mant_f)
    repuestos_utilizados = len(gastos_sin_combustible)
    equipos_registrados = len(equipos_f)

    if "Proxima_Mantencion" not in proximas_originales.columns:
        proximas_originales = pd.DataFrame(columns=[
            "Equipo", "Categoria", "Tipo_Mantencion", "Proxima_Mantencion",
            "Km_Horometro_Actual", "Unidad_Control", "Costo_CLP"
        ])

    mant_proximas = proximas_originales.copy()
    if "Proxima_Mantencion" in mant_proximas.columns:
        mant_proximas["Proxima_Mantencion"] = mant_proximas["Proxima_Mantencion"].apply(limpiar_numero)
        mant_proximas = mant_proximas[mant_proximas["Proxima_Mantencion"] > 0].copy()

    if filtro_equipo != "Todos los equipos" and "Equipo" in mant_proximas.columns:
        mant_proximas = mant_proximas[mant_proximas["Equipo"] == filtro_equipo]

    mant_proximas = resumen_proximas_por_equipo(mant_proximas) if not mant_proximas.empty else mant_proximas

    if not mant_proximas.empty:
        proxima_fila = mant_proximas.iloc[0]
        proxima_texto = str(proxima_fila.get("Equipo", "Sin equipo")).strip() or "Sin equipo"
        proxima_sub = f"Próx.: {proxima_fila.get('Proxima_Texto', 'Sin dato')} | {proxima_fila.get('Texto_Estado', 'Sin análisis')}"
    else:
        proxima_texto = "Sin registro"
        proxima_sub = "No programada"

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card("🛠️", "Mantenciones", f"{mant_realizadas}", "Registros del período", "#dbeafe")
    with k2:
        kpi_card("💲", "Monto Total", pesos(costo_total), "Costos del período", "#dcfce7")
    with k3:
        kpi_card("🧰", "Gastos Adic.", f"{repuestos_utilizados}", "Repuestos, mantenciones y administrativos", "#f3e8ff")
    with k4:
        kpi_card("📅", "Próxima Mantención", proxima_texto, proxima_sub, "#ffedd5")
    with k5:
        kpi_card("🚚", "Equipos Registrados", f"{equipos_registrados}", "Total equipos", "#ccfbf1")

    c1, c2 = st.columns([1.60, 1.0])

    with c1:
        st.markdown('<div class="panel-title">Histórico de Intervenciones</div>', unsafe_allow_html=True)
        historico = mant_f.copy()
        if "Tipo_Mantencion" in historico.columns:
            historico["Mantencion"] = historico["Tipo_Mantencion"].apply(normalizar_tipo_mantencion)

        if not historico.empty:
            historico = historico.sort_values("Fecha", ascending=False).head(6)
            columnas_base = ["Fecha", "Equipo", "Mantencion", "Descripcion", "Costo_CLP", "Estado_Mantencion"]
            columnas_base = [c for c in columnas_base if c in historico.columns]
            mostrar = historico[columnas_base].copy()
            if "Fecha" in mostrar.columns:
                mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)
            if "Costo_CLP" in mostrar.columns:
                mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)
            mostrar = mostrar.rename(columns={
                "Mantencion": "Tipo",
                "Descripcion": "Descripción",
                "Costo_CLP": "Monto",
                "Estado_Mantencion": "Estado",
            })
            st.markdown('<div class="dashboard-compact-table">', unsafe_allow_html=True)
            mostrar_tabla_clara(mostrar, height=210)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No existen mantenciones registradas para el filtro aplicado.")

    with c2:
        st.markdown('<div class="dashboard-costos-spacer"></div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title chart-title dashboard-costos-title">Distribución de Costos</div>', unsafe_allow_html=True)
        costos_item = construir_consolidado_costos(mant_f, gastos_f)
        st.plotly_chart(crear_donut_costos(costos_item), use_container_width=True)

    c3, c4, c5 = st.columns([1.05, 1.36, 1.25])

    with c3:
        st.markdown('<div class="panel-title">Gastos Adicionales</div>', unsafe_allow_html=True)
        repuestos = gastos_sin_combustible.copy()
        if not repuestos.empty:
            repuestos = repuestos.sort_values("Fecha", ascending=False).head(5)
            columnas_repuestos = ["Fecha", "Equipo", "Tipo_Gasto", "Descripcion", "Costo_CLP"]
            columnas_repuestos = [c for c in columnas_repuestos if c in repuestos.columns]
            mostrar = repuestos[columnas_repuestos].copy()
            if "Fecha" in mostrar.columns:
                mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)
            if "Costo_CLP" in mostrar.columns:
                mostrar["Costo_CLP"] = mostrar["Costo_CLP"].apply(pesos)
            mostrar = mostrar.rename(columns={
                "Tipo_Gasto": "Tipo",
                "Descripcion": "Detalle",
                "Costo_CLP": "Monto",
            })
            st.markdown('<div class="dashboard-compact-table">', unsafe_allow_html=True)
            mostrar_tabla_clara(mostrar, height=170)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No existen gastos adicionales o administrativos registrados.")

    with c4:
        if not mant_proximas.empty:
            filas_proximas_html = "".join(
                _render_item_proxima_dashboard(fila)
                for _, fila in mant_proximas.head(7).iterrows()
            )
        else:
            filas_proximas_html = '<div class="proximas-empty-v68">No existen próximas mantenciones registradas.</div>'

        html_proximas = (
            '<div class="dashboard-proximas dashboard-proximas-v68">'
            '<div class="panel-title proximas-title-v68">Próximas Mantenciones</div>'
            '<div class="next-list-v68">'
            + filas_proximas_html
            + '</div></div>'
        )
        st.markdown(html_proximas, unsafe_allow_html=True)

    with c5:
        st.markdown('<div class="panel-title">Evolución de Costos</div>', unsafe_allow_html=True)

        mant_mes = (
            mant_f.groupby(["Año", "Mes_Numero", "Periodo"], as_index=False)["Costo_CLP"].sum()
            .rename(columns={"Costo_CLP": "Mantenciones"})
        ) if not mant_f.empty and "Costo_CLP" in mant_f.columns else pd.DataFrame(columns=["Año", "Mes_Numero", "Periodo", "Mantenciones"])

        gasto_mes = (
            gastos_sin_combustible.groupby(["Año", "Mes_Numero", "Periodo"], as_index=False)["Costo_CLP"].sum()
            .rename(columns={"Costo_CLP": "Gastos"})
        ) if not gastos_sin_combustible.empty and "Costo_CLP" in gastos_sin_combustible.columns else pd.DataFrame(columns=["Año", "Mes_Numero", "Periodo", "Gastos"])

        comb_mes = (
            combustible_f.groupby(["Año", "Mes_Numero", "Periodo"], as_index=False)["Costo_Total"].sum()
            .rename(columns={"Costo_Total": "Combustible"})
        ) if not combustible_f.empty and "Costo_Total" in combustible_f.columns else pd.DataFrame(columns=["Año", "Mes_Numero", "Periodo", "Combustible"])

        costos_mes = (
            mant_mes
            .merge(gasto_mes, on=["Año", "Mes_Numero", "Periodo"], how="outer")
            .merge(comb_mes, on=["Año", "Mes_Numero", "Periodo"], how="outer")
            .fillna(0)
        )

        if not costos_mes.empty:
            costos_mes = costos_mes.sort_values(["Año", "Mes_Numero"])
            costos_mes["Monto Acumulado"] = (
                costos_mes["Mantenciones"] + costos_mes["Gastos"] + costos_mes["Combustible"]
            ).cumsum()

            fig_linea = px.line(
                costos_mes,
                x="Periodo",
                y="Monto Acumulado",
                markers=True,
                template="plotly_white",
            )
            fig_linea.update_traces(
                line=dict(width=3, color="#2563eb"),
                marker=dict(size=7),
                name="",
                showlegend=False,
                customdata=costos_mes["Monto Acumulado"].apply(pesos),
                hovertemplate="<b>%{x}</b><br>Monto acumulado: %{customdata}<extra></extra>",
            )
            fig_linea.update_layout(title_text="", showlegend=False, legend_title_text="")
            st.plotly_chart(aplicar_formato_grafico(fig_linea, 190), use_container_width=True)
        else:
            st.info("Sin costos para graficar.")

    st.markdown('<div class="panel-title">Estado de los Equipos</div>', unsafe_allow_html=True)

    if equipos_f.empty:
        st.info("No existen equipos registrados.")
    else:
        cantidad_columnas = min(len(equipos_f), 7)
        if cantidad_columnas <= 0:
            cantidad_columnas = 1
        columnas = st.columns(cantidad_columnas)
        for columna, (_, fila) in zip(columnas, equipos_f.head(7).iterrows()):
            with columna:
                tarjeta_equipo(fila)


# =========================================================
# AJUSTE FINAL SOLICITADO V8.0
# - Menú estable: todos los ítems usan el mismo componente y tamaño.
# - "Dashboard Ejecutivo" pasa a llamarse "Resumen Ejecutivo".
# - Se elimina el botón manual "Actualizar".
# - Documentación Legal incorpora KPI y control profesional de vencimientos.
# =========================================================


def _texto_normalizado_simple(valor):
    return normalizar_texto(str(valor or "")).replace("_", " ").strip()


CONTRATOS_EQUIVALENTES = {
    "PLYWOOD 1": ["PLYWOOD 1", "Plywood Aseo Maquinas", "Plywood aseo maquinas"],
    "PLYWOOD 2": ["PLYWOOD 2", "Plywood Aseo Pisos"],
    "CONTRATO MULCHEN": ["CONTRATO MULCHEN", "Mulchen Aseo Industrial"],
    "CONSTRUCTORA": ["CONSTRUCTORA", "Construccion"],
    "CONTRATO FOSAS": ["CONTRATO FOSAS", "Fosas"],
    "TRANSPORTES": ["TRANSPORTES", "Transporte"],
    "GERENCIA": ["GERENCIA", "Oficina Gerencia"],
    "RENTAL SPOT": ["RENTAL SPOT", "Otros Servicios (Spot)", "Otros Servicion (Spot)"],
    "RENTAL": ["RENTAL", "Rental zona Norte", "Rental Zona Norte"],
    "ECOMETALES": ["ECOMETALES", "EcoMetales", "Ecometales"],
    "ECOMETALES ZT": ["ECOMETALES ZT", "Ecometales ZT", "EcoMetales ZT"],
}


def _equivalencias_contrato_seleccionado(filtro_contrato):
    """Devuelve todas las variantes equivalentes al contrato seleccionado.

    Funciona tanto si el selector usa el nombre del catálogo de EQUIPOS
    (por ejemplo CONTRATO MULCHEN) como si usa el nombre registrado en
    MANTENCIONES (por ejemplo Mulchen Aseo Industrial).
    """
    objetivo = _texto_normalizado_simple(filtro_contrato)
    if not objetivo:
        return [filtro_contrato]

    for principal, alias in CONTRATOS_EQUIVALENTES.items():
        grupo = [principal] + list(alias)
        normalizados = {_texto_normalizado_simple(v) for v in grupo}
        if objetivo in normalizados:
            return list(dict.fromkeys(grupo))

    return [filtro_contrato]


def filtrar_por_contrato(df, filtro_contrato):
    """Aplica el filtro de contrato cuando el DataFrame trae Contrato o Planta."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
    if filtro_contrato in [None, "", "Todos los contratos", "Todos"]:
        return df.copy()

    columna = "Contrato" if "Contrato" in df.columns else ("Planta" if "Planta" in df.columns else None)
    if columna is None:
        return df.copy()

    equivalencias = _equivalencias_contrato_seleccionado(filtro_contrato)
    permitidos = {_texto_normalizado_simple(v) for v in equivalencias}
    serie = df[columna].fillna("").astype(str).map(_texto_normalizado_simple)
    mascara = serie.isin(permitidos)

    # Respaldo para nombres más largos o pequeñas variaciones de escritura.
    if not mascara.any():
        objetivo = _texto_normalizado_simple(filtro_contrato)
        if objetivo:
            mascara = serie.str.contains(objetivo, regex=False) | serie.apply(
                lambda x: bool(x) and x in objetivo
            )

    return df[mascara].copy()

def _fila_equipo_seleccionado(filtro_equipo, equipos_catalogo):
    if (
        filtro_equipo in [None, "", "Todos los equipos"]
        or equipos_catalogo is None
        or not isinstance(equipos_catalogo, pd.DataFrame)
        or equipos_catalogo.empty
        or "Equipo" not in equipos_catalogo.columns
    ):
        return None

    coincidencias = equipos_catalogo[
        equipos_catalogo["Equipo"].fillna("").astype(str).str.strip() == str(filtro_equipo).strip()
    ]
    if coincidencias.empty:
        return None
    return coincidencias.iloc[0]


def filtrar_por_equipo_catalogo(df, filtro_equipo, equipos_catalogo):
    """Filtra por el equipo seleccionado.

    El selector oficial usa los nombres de TIPO EQUIPO de la hoja
    MANTENCIONES. Por eso se intenta primero una coincidencia exacta
    contra Tipo_Equipo. Si una fuente antigua no trae esa columna,
    se mantiene el respaldo por Equipo/patente/chasis/modelo.
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
    if filtro_equipo in [None, "", "Todos los equipos"]:
        return df.copy()

    seleccionado = str(filtro_equipo).strip()

    if "Tipo_Equipo" in df.columns:
        tipo_txt = df["Tipo_Equipo"].fillna("").astype(str).str.strip()
        mascara_tipo = tipo_txt.str.casefold() == seleccionado.casefold()
        if mascara_tipo.any():
            return df[mascara_tipo].copy()

    fila = _fila_equipo_seleccionado(filtro_equipo, equipos_catalogo)
    if fila is None:
        if "Equipo" in df.columns:
            return df[
                df["Equipo"].fillna("").astype(str).str.strip().str.casefold()
                == seleccionado.casefold()
            ].copy()
        return df.iloc[0:0].copy() if "Tipo_Equipo" in df.columns else df.copy()

    mascaras = []

    if "Equipo" in df.columns:
        equipo_txt = df["Equipo"].fillna("").astype(str).str.strip()
        mascaras.append(equipo_txt.str.casefold() == seleccionado.casefold())

    candidatos = [
        ("Patente_Codigo", fila.get("Patente_Codigo", "")),
        ("Patente", fila.get("Patente_Codigo", "")),
        ("Numero_Chasis", fila.get("Numero_Chasis", "")),
        ("Modelo", fila.get("Modelo", "")),
    ]
    for columna, valor in candidatos:
        valor_txt = str(valor).strip()
        if columna in df.columns and valor_txt.lower() not in ["", "nan", "none", "nat"]:
            mascaras.append(
                df[columna].fillna("").astype(str).str.strip().str.casefold()
                == valor_txt.casefold()
            )

    if not mascaras and "Tipo_Equipo" in df.columns:
        tipo = str(fila.get("Tipo_Equipo", "")).strip()
        if tipo.lower() not in ["", "nan", "none"]:
            mascaras.append(
                df["Tipo_Equipo"].fillna("").astype(str).str.strip().str.casefold()
                == tipo.casefold()
            )

    if not mascaras:
        return df.copy()

    mascara_final = mascaras[0].copy()
    for mascara in mascaras[1:]:
        mascara_final = mascara_final | mascara

    return df[mascara_final].copy()

def construir_menu(equipos, mantenciones=None, gastos=None, combustible=None, checklist=None, documentos=None):
    """Menú lateral con filtros oficiales desde la hoja MANTENCIONES.

    Reglas solicitadas:
    - Equipo: nombres de Tipo_Equipo registrados en MANTENCIONES.
    - Contrato: contratos registrados en MANTENCIONES.
    - Año: año actual y los dos anteriores.
    - Mes: enero a diciembre.
    Los filtros Año/Mes se aplican al período de las intervenciones.
    """
    ruta_logo_menu = (
        buscar_imagen_por_nombre("logoredondo")
        or buscar_imagen_por_nombre("logo redondo")
        or buscar_imagen_por_nombre("logo_redondo")
        or buscar_imagen_por_nombre("logo-redondo")
    )

    if ruta_logo_menu:
        logo_menu_b64 = archivo_a_base64(ruta_logo_menu)
        logo_menu_mime = extension_mime(ruta_logo_menu)
        icono_menu_html = (
            '<div class="menu-icon-img">'
            f'<img src="data:{logo_menu_mime};base64,{logo_menu_b64}" alt="Logo menú">'
            '</div>'
        )
    else:
        icono_menu_html = '<div class="menu-icon">🚜</div>'

    st.markdown(
        f"""
        <div class="menu-bg"></div>
        <div class="menu-marker menu-state-expanded"></div>
        <div class="menu-panel-content">
            <div class="menu-brand">
                {icono_menu_html}
                <div class="menu-text">
                    <div class="menu-title">SEGUIMIENTO<br>EQUIPOS MÓVILES</div>
                    <div class="menu-subtitle">SAIVAM · MULCHÉN</div>
                </div>
            </div>
            <hr class="menu-line">
        </div>
        <div class="menu-top-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    paginas_menu = {
        "panel": ("📊", "Resumen Ejecutivo", "📊 Dashboard Ejecutivo"),
        "equipos": ("🚚", "Equipos", "🚚 Equipos"),
        "mantenciones": ("🛠️", "Intervenciones", "🛠️ Intervenciones"),
        "documentos": ("📁", "Documentacion (Pdt)", "📁 Documentacion"),
    }

    pagina_actual = st.query_params.get("pagina", "panel")
    if pagina_actual not in paginas_menu:
        pagina_actual = "panel"
        st.query_params["pagina"] = "panel"

    for clave, (icono, nombre_visible, _) in paginas_menu.items():
        es_actual = clave == pagina_actual
        presionado = st.button(
            f"{icono} {nombre_visible}",
            key=f"menu_estable_{clave}",
            help=nombre_visible,
            use_container_width=True,
            disabled=es_actual,
        )
        if presionado:
            st.query_params["pagina"] = clave
            st.session_state["_saivam_mobile_menu_open"] = False
            st.rerun()

    st.markdown('<hr class="menu-line">', unsafe_allow_html=True)
    st.markdown('<div class="menu-filter-gap"></div>', unsafe_allow_html=True)

    # Fuente oficial de los filtros: hoja MANTENCIONES local.
    mant_base = mantenciones.copy() if isinstance(mantenciones, pd.DataFrame) else pd.DataFrame()

    # Contratos: exactamente los que aparecen en la planilla de intervenciones.
    if not mant_base.empty and "Contrato" in mant_base.columns:
        contratos = sorted(
            {
                str(v).strip()
                for v in mant_base["Contrato"].dropna().tolist()
                if str(v).strip().lower() not in ["", "nan", "none", "nat"]
            },
            key=lambda x: x.casefold(),
        )
    else:
        contratos = []

    opciones_contrato = ["Todos los contratos"] + contratos
    if st.session_state.get("filtro_contrato_menu", "Todos los contratos") not in opciones_contrato:
        st.session_state["filtro_contrato_menu"] = "Todos los contratos"

    contrato_actual = st.session_state.get("filtro_contrato_menu", "Todos los contratos")
    mant_para_equipos = filtrar_por_contrato(mant_base, contrato_actual)

    # Equipos: se toman de TIPO EQUIPO de MANTENCIONES (Alto Vacío, Hidrolaser, etc.).
    if not mant_para_equipos.empty and "Tipo_Equipo" in mant_para_equipos.columns:
        nombres_equipo = sorted(
            {
                str(v).strip()
                for v in mant_para_equipos["Tipo_Equipo"].dropna().tolist()
                if str(v).strip().lower() not in ["", "nan", "none", "nat"]
            },
            key=lambda x: x.casefold(),
        )
    else:
        nombres_equipo = []

    equipos_disponibles = ["Todos los equipos"] + nombres_equipo
    if st.session_state.get("filtro_equipo_menu", "Todos los equipos") not in equipos_disponibles:
        st.session_state["filtro_equipo_menu"] = "Todos los equipos"

    # Año: actual + dos anteriores, independientemente de si algún mes no tiene registros.
    anio_sistema = datetime.now().year
    opciones_anio = ["Todos", anio_sistema, anio_sistema - 1, anio_sistema - 2]
    if st.session_state.get("filtro_anio_menu", "Todos") not in opciones_anio:
        st.session_state["filtro_anio_menu"] = "Todos"

    # Mes: siempre enero a diciembre.
    opciones_mes = ["Todos"] + [MESES[n] for n in range(1, 13)]
    if st.session_state.get("filtro_mes_menu", "Todos") not in opciones_mes:
        st.session_state["filtro_mes_menu"] = "Todos"

    filtro_equipo = st.selectbox("Equipo", equipos_disponibles, key="filtro_equipo_menu")
    filtro_contrato = st.selectbox("Contrato", opciones_contrato, key="filtro_contrato_menu")
    filtro_anio = st.selectbox("Año", opciones_anio, key="filtro_anio_menu")
    filtro_mes = st.selectbox("Mes", opciones_mes, key="filtro_mes_menu")

    st.markdown(
        f"""
        <div class="menu-footer-box">
            <div class="menu-info">
                Versión {VERSION}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pagina_interna = paginas_menu[pagina_actual][2]
    return pagina_interna, filtro_equipo, filtro_contrato, filtro_anio, filtro_mes

def _clasificar_vencimiento_documento(fecha_vencimiento, hoy):
    if pd.isna(fecha_vencimiento):
        return "Sin fecha", 3

    dias = int((fecha_vencimiento - hoy).days)
    if dias < 0:
        return "Vencido", 0
    if dias <= 30:
        return "Próximo a vencer", 1
    return "Vigente", 2


def _texto_dias_documento(fecha_vencimiento, hoy):
    if pd.isna(fecha_vencimiento):
        return "Sin fecha"

    dias = int((fecha_vencimiento - hoy).days)
    if dias < 0:
        return f"Vencido hace {abs(dias)} días"
    if dias == 0:
        return "Vence hoy"
    if dias == 1:
        return "Vence en 1 día"
    return f"Vence en {dias} días"


def pagina_documentos(documentos_f):
    """Control documental con KPI, alertas y priorización por vencimiento."""
    st.markdown(
        '<div class="section-head"><div class="panel-title page-section-title">Documentacion</div></div>',
        unsafe_allow_html=True,
    )

    if documentos_f.empty:
        st.info("No existen documentos para el filtro aplicado.")
        return

    hoy = pd.Timestamp.now().normalize()
    base = documentos_f.copy()

    if "Vencimiento" not in base.columns:
        base["Vencimiento"] = pd.NaT

    base["_Vencimiento_dt"] = base["Vencimiento"].apply(convertir_fecha)
    base["_Vencimiento_dt"] = pd.to_datetime(base["_Vencimiento_dt"], errors="coerce").dt.normalize()

    clasificacion = base["_Vencimiento_dt"].apply(
        lambda fecha: _clasificar_vencimiento_documento(fecha, hoy)
    )
    base["Estado"] = [item[0] for item in clasificacion]
    base["_Prioridad"] = [item[1] for item in clasificacion]
    base["Días restantes"] = base["_Vencimiento_dt"].apply(
        lambda fecha: _texto_dias_documento(fecha, hoy)
    )

    total = int(len(base))
    vencidos = int((base["Estado"] == "Vencido").sum())
    proximos_30 = int((base["Estado"] == "Próximo a vencer").sum())
    vigentes = int((base["Estado"] == "Vigente").sum())
    sin_fecha = int((base["Estado"] == "Sin fecha").sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("📄", "Documentos registrados", numero(total), f"{sin_fecha} sin fecha de vencimiento", "#dbeafe")
    with c2:
        kpi_card("⛔", "Documentos vencidos", numero(vencidos), "Requieren regularización", "#fee2e2")
    with c3:
        kpi_card("⏳", "Vencen en 30 días", numero(proximos_30), "Prioridad de seguimiento", "#ffedd5")
    with c4:
        kpi_card("✅", "Documentos vigentes", numero(vigentes), "Con más de 30 días", "#dcfce7")

    if vencidos > 0:
        st.error(f"Atención: existen {vencidos} documento(s) vencido(s).")
    elif proximos_30 > 0:
        st.warning(f"Seguimiento requerido: {proximos_30} documento(s) vence(n) dentro de los próximos 30 días.")
    else:
        st.success("La documentación con fecha de vencimiento se encuentra al día.")

    proximos = base[
        base["_Vencimiento_dt"].notna() & (base["_Vencimiento_dt"] >= hoy)
    ].sort_values(["_Vencimiento_dt", "Equipo"], ascending=[True, True]).head(6)

    st.markdown('<div class="panel-title">Próximos vencimientos</div>', unsafe_allow_html=True)
    if proximos.empty:
        st.info("No existen vencimientos futuros registrados para el filtro aplicado.")
    else:
        columnas_resumen = [
            c for c in ["Equipo", "Tipo_Documento", "Vencimiento", "Días restantes", "Estado"]
            if c in proximos.columns
        ]
        resumen = proximos[columnas_resumen].copy()
        if "Vencimiento" in resumen.columns:
            resumen["Vencimiento"] = resumen["Vencimiento"].apply(fecha_texto)
        resumen = resumen.rename(columns={"Tipo_Documento": "Tipo documento"})
        mostrar_tabla_clara(resumen, height=245)

    st.markdown('<div class="panel-title">Detalle de documentación</div>', unsafe_allow_html=True)

    mostrar = base.sort_values(
        ["_Prioridad", "_Vencimiento_dt", "Equipo"],
        ascending=[True, True, True],
        na_position="last",
    ).copy()

    columnas_eliminar = [
        "ID_Documento",
        "ID_Equipo",
        "Año",
        "Ano",
        "Mes",
        "Mes_Numero",
        "Periodo",
        "_Vencimiento_dt",
        "_Prioridad",
    ]
    mostrar = mostrar.drop(columns=[c for c in columnas_eliminar if c in mostrar.columns], errors="ignore")

    for col in ["Fecha", "Vencimiento"]:
        if col in mostrar.columns:
            mostrar[col] = mostrar[col].apply(fecha_texto)

    mostrar = mostrar.rename(
        columns={
            "Tipo_Documento": "Tipo documento",
            "Ruta_Link": "Ruta / enlace",
            "Observacion": "Observación",
            "Descripcion": "Descripción",
        }
    )
    mostrar_tabla_clara(mostrar, height=520)


def aplicar_correcciones_visuales_v80():
    st.markdown(
        """
<style>
/* Todos los elementos del menú conservan exactamente la misma caja. */
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    min-height: 46px !important;
    height: 46px !important;
    margin: 0 0 7px 0 !important;
    padding: 9px 12px !important;
    border-radius: 14px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    text-align: left !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

/* El botón activo sigue siendo un botón nativo; solo cambia su apariencia. */
section[data-testid="stSidebar"] div[data-testid="stButton"] button:disabled {
    opacity: 1 !important;
    cursor: default !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%) !important;
    border: 1px solid rgba(219, 234, 254, .95) !important;
    box-shadow: 0 8px 18px rgba(37, 99, 235, .34) !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button:disabled * {
    opacity: 1 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 950 !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


aplicar_ajustes_finales_ui()
aplicar_correcciones_visuales_v80()
# La marca antigua se desactiva para impedir el destello inicial.


# =========================================================
# CONTROL MÓVIL NATIVO V7.3
# Botón real de Streamlit: no utiliza etiquetas HTML interactivas.
# En computador se oculta mediante CSS; en teléfono abre/cierra el sidebar.
# =========================================================

if "_saivam_mobile_menu_open" not in st.session_state:
    st.session_state["_saivam_mobile_menu_open"] = False

def _alternar_menu_movil():
    st.session_state["_saivam_mobile_menu_open"] = not st.session_state["_saivam_mobile_menu_open"]

with st.container(key="saivam_mobile_menu_control"):
    st.button(
        "✕" if st.session_state["_saivam_mobile_menu_open"] else "☰",
        key="saivam_mobile_menu_button",
        on_click=_alternar_menu_movil,
        help="Cerrar menú" if st.session_state["_saivam_mobile_menu_open"] else "Abrir menú",
    )


# =========================================================
# AJUSTE FINAL V10.0 - MANTENCIONES DESDE PLANILLA LOCAL
# - La página Equipos continúa usando la hoja EQUIPOS del Excel local.
# - La página Mantenciones usa la segunda hoja MANTENCIONES del mismo Excel.
# - Tipos válidos: Reparacion, Mantencion, Logistica y Documentacion.
# - Se mantienen como únicos filtros globales del menú: Equipo y Contrato.
# =========================================================


def leer_mantenciones_excel_local():
    """Lee la hoja MANTENCIONES del mismo Excel local usado por Equipos."""
    ruta = buscar_archivo_excel_equipos()
    if not ruta:
        return pd.DataFrame(), None

    try:
        df = pd.read_excel(ruta, sheet_name="MANTENCIONES")
    except Exception:
        return pd.DataFrame(), ruta

    df = df.dropna(axis=1, how="all")
    df = df.dropna(how="all")
    return df, ruta


def _normalizar_tipo_intervencion(valor):
    texto = str(valor).strip()
    if texto.lower() in ["", "nan", "none", "nat", "0"]:
        return "Sin tipo"

    clave = normalizar_texto(texto)
    if "repar" in clave or "correct" in clave:
        return "Reparacion"
    if "mant" in clave or "prevent" in clave or "predict" in clave:
        return "Mantencion"
    if "logist" in clave:
        return "Logistica"
    if "document" in clave or "administr" in clave:
        return "Documentacion"
    return texto


def _limpiar_monto_planilla(valor):
    """Convierte montos como $1.591.794, $- o 1591794 a número."""
    if pd.isna(valor):
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip()
    if texto.lower() in ["", "-", "$-", "nan", "none", "nat"]:
        return 0.0

    texto = texto.replace("$", "").replace(" ", "")
    # La planilla usa punto como separador de miles y, eventualmente, coma decimal.
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(".", "")

    texto = re.sub(r"[^0-9.-]", "", texto)
    try:
        return float(texto)
    except Exception:
        return 0.0


def _total_servicio_oficial(valor):
    """Convierte correctamente montos provenientes de Google Sheets.

    Google Sheets puede entregar los valores monetarios como texto formateado
    (por ejemplo "$66.873" o "$1.894.235"). Para los KPI y gráficos estos
    valores deben convertirse a número en vez de descartarse como 0.
    """
    return _limpiar_monto_planilla(valor)


def preparar_mantenciones_planilla(df):
    """Adapta la hoja MANTENCIONES real a la estructura del panel."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(
            columns=[
                "Tipo_Equipo", "Patente_Codigo", "Modelo", "Tipo_Intervencion", "Fecha",
                "Servicios_Realizados", "Kilometraje", "UM", "Proveedor_Tipo",
                "Nombre_Proveedor", "Valor_Neto", "Valor_Total", "Total_Servicio",
                "Ceco", "Contrato"
            ]
        )

    mant = df.copy()

    renombres = {}
    mapa = {
        "tipo_equipo": "Tipo_Equipo",
        "tipoequipo": "Tipo_Equipo",
        "patente": "Patente_Codigo",
        "modelo": "Modelo",
        "tipo_de_intervencion": "Tipo_Intervencion",
        "tipodeintervencion": "Tipo_Intervencion",
        "tipo_intervencion": "Tipo_Intervencion",
        "fecha": "Fecha",
        "servicios_realizados": "Servicios_Realizados",
        "serviciosrealizados": "Servicios_Realizados",
        "kilometraje": "Kilometraje",
        "um": "UM",
        "proveedor": "Proveedor_Tipo",
        "nombre_proveedor": "Nombre_Proveedor",
        "nombreproveedor": "Nombre_Proveedor",
        "valor_neto": "Valor_Neto",
        "valorneto": "Valor_Neto",
        "valor_total": "Valor_Total",
        "valortotal": "Valor_Total",
        "total_servicio": "Total_Servicio",
        "totalservicio": "Total_Servicio",
        "ceco": "Ceco",
        "contrato": "Contrato",
    }

    for col in mant.columns:
        original = str(col).replace("\n", " ").replace("\r", " ").strip()
        clave_guion = normalizar_texto(original)
        clave = clave_guion.replace("_", "")
        renombres[col] = mapa.get(clave_guion, mapa.get(clave, original))

    mant = mant.rename(columns=renombres)

    columnas = [
        "Tipo_Equipo", "Patente_Codigo", "Modelo", "Tipo_Intervencion", "Fecha",
        "Servicios_Realizados", "Kilometraje", "UM", "Proveedor_Tipo",
        "Nombre_Proveedor", "Valor_Neto", "Valor_Total", "Total_Servicio",
        "Ceco", "Contrato"
    ]
    for col in columnas:
        if col not in mant.columns:
            mant[col] = ""

    mant["Tipo_Equipo"] = mant["Tipo_Equipo"].fillna("").astype(str).str.strip()
    mant["Patente_Codigo"] = mant["Patente_Codigo"].fillna("").astype(str).str.strip()
    mant["Modelo"] = mant["Modelo"].fillna("").astype(str).str.strip()
    mant["Tipo_Intervencion"] = mant["Tipo_Intervencion"].apply(_normalizar_tipo_intervencion)
    mant["Servicios_Realizados"] = mant["Servicios_Realizados"].fillna("").astype(str).str.strip()
    mant["UM"] = mant["UM"].fillna("").astype(str).str.strip()
    mant["Proveedor_Tipo"] = mant["Proveedor_Tipo"].fillna("").astype(str).str.strip()
    mant["Nombre_Proveedor"] = mant["Nombre_Proveedor"].fillna("").astype(str).str.strip()
    mant["Contrato"] = mant["Contrato"].fillna("").astype(str).str.strip()

    mant["Fecha"] = mant["Fecha"].apply(convertir_fecha)
    mant["Kilometraje"] = mant["Kilometraje"].apply(limpiar_numero)
    mant["Valor_Neto"] = mant["Valor_Neto"].apply(_limpiar_monto_planilla)
    mant["Valor_Total"] = mant["Valor_Total"].apply(_limpiar_monto_planilla)

    # Monto oficial del servicio: columna VALOR TOTAL (columna K) de Google Sheets.
    # No se mezcla con TOTAL SERVICIO para evitar dobles criterios o montos distintos.
    # Así todos los KPI, gráficos y tablas cuadran exactamente con la suma de VALOR TOTAL.
    mant["Total_Servicio"] = mant["Valor_Total"].astype(float)

    # Solo quedan registros reales y los cuatro tipos definidos para el control.
    mant = mant[
        (~mant["Tipo_Equipo"].str.lower().isin(["", "nan", "none"]))
        | (~mant["Patente_Codigo"].str.lower().isin(["", "nan", "none"]))
        | (mant["Servicios_Realizados"] != "")
    ].copy()

    tipos_validos = ["Reparacion", "Mantencion", "Logistica", "Documentacion"]
    mant = mant[mant["Tipo_Intervencion"].isin(tipos_validos)].copy()
    return mant[columnas].copy()


# Sobrescribe la carga anterior para incorporar la segunda hoja local sin afectar
# los demás módulos que todavía usan Google Sheets como respaldo.
@st.cache_data(ttl=CACHE_GOOGLE_SHEETS_SEGUNDOS, show_spinner="Actualizando datos...")
def cargar_datos():
    """Carga oficial 100% desde Google Sheets para despliegue en Streamlit Cloud.

    EQUIPOS y MANTENCIONES alimentan también las vistas PLANILLA, evitando que
    una copia Excel guardada en GitHub deje datos congelados.
    """
    datos = {}

    for hoja in HOJAS_GOOGLE_SHEETS:
        datos[hoja] = leer_hoja_google_sheet(hoja)

    if datos.get("EQUIPOS", pd.DataFrame()).empty:
        raise FileNotFoundError(
            "No se pudo leer la hoja EQUIPOS desde Google Sheets. "
            "Revisa que el archivo esté compartido como lector y que la pestaña se llame EQUIPOS."
        )

    # Fuente oficial del módulo Equipos: Google Sheets.
    datos["EQUIPOS_PLANILLA"] = datos["EQUIPOS"].copy()

    # Fuente oficial del módulo Intervenciones: pestaña MANTENCIONES de Google Sheets.
    # La función preparar_mantenciones_planilla() adapta esta hoja al formato del panel.
    datos["MANTENCIONES_PLANILLA"] = datos.get("MANTENCIONES", pd.DataFrame()).copy()

    datos["FUENTE_EQUIPOS"] = GOOGLE_SHEET_URL
    datos["FUENTE_MANTENCIONES"] = GOOGLE_SHEET_URL
    return GOOGLE_SHEET_URL, datos


def pagina_mantenciones(mant_f):
    # El encabezado general de la página ya muestra "Mantenciones".
    # Se elimina el segundo título y subtítulo para dejar una vista más limpia.
    if mant_f is None or mant_f.empty:
        st.info("No existen intervenciones para los filtros seleccionados.")
        return

    mant_base = mant_f.copy()
    tipos_orden = ["Reparacion", "Mantencion", "Logistica", "Documentacion"]

    # Cuatro categorías oficiales, sin agregar filtros adicionales al menú.
    columnas_kpi = st.columns(4)
    iconos = {
        "Reparacion": "🔧",
        "Mantencion": "🛠️",
        "Logistica": "🚚",
        "Documentacion": "📄",
    }
    fondos = {
        "Reparacion": "#fee2e2",
        "Mantencion": "#dbeafe",
        "Logistica": "#fef3c7",
        "Documentacion": "#ede9fe",
    }

    for col_ui, tipo in zip(columnas_kpi, tipos_orden):
        bloque = mant_base[mant_base["Tipo_Intervencion"] == tipo]
        cantidad = len(bloque)
        monto = float(bloque["Total_Servicio"].sum()) if "Total_Servicio" in bloque.columns else 0.0
        with col_ui:
            kpi_card(
                iconos[tipo],
                tipo,
                str(cantidad),
                f"Registros · {pesos(monto)}",
                fondos[tipo],
            )

    total_intervenciones = float(mant_base["Total_Servicio"].sum()) if "Total_Servicio" in mant_base.columns else 0.0
    st.markdown(
        f'<div style="text-align:right; font-size:16px; font-weight:800; margin:4px 2px 14px 0;">Total servicios: {pesos(total_intervenciones)}</div>',
        unsafe_allow_html=True,
    )

    resumen = (
        mant_base.groupby("Tipo_Intervencion", as_index=False)
        .agg(Registros=("Tipo_Intervencion", "size"), Total_Servicio=("Total_Servicio", "sum"))
    )
    resumen["_orden"] = resumen["Tipo_Intervencion"].apply(
        lambda x: tipos_orden.index(x) if x in tipos_orden else len(tipos_orden)
    )
    resumen = resumen.sort_values("_orden").drop(columns="_orden")

    if not resumen.empty:
        colores_intervencion = {
            "Reparacion": "#ef4444",
            "Mantencion": "#2563eb",
            "Logistica": "#f59e0b",
            "Documentacion": "#8b5cf6",
        }
        fig = px.bar(
            resumen,
            x="Tipo_Intervencion",
            y="Registros",
            text="Registros",
            color="Tipo_Intervencion",
            color_discrete_map=colores_intervencion,
            category_orders={"Tipo_Intervencion": tipos_orden},
            template="plotly_white",
            title="Distribución de intervenciones",
            custom_data=["Total_Servicio"],
        )
        fig.update_traces(
            textposition="outside",
            hovertemplate="Tipo: %{x}<br>Registros: %{y}<br>Total servicio: $%{customdata[0]:,.0f}<extra></extra>",
        )
        fig.update_layout(xaxis_title="Tipo de intervención", yaxis_title="Cantidad de registros")
        st.plotly_chart(aplicar_formato_grafico(fig, 300), use_container_width=True)

    mostrar = mant_base.copy()
    mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)
    mostrar["Kilometraje"] = mostrar["Kilometraje"].apply(
        lambda v: "" if limpiar_numero(v) <= 0 else numero(v)
    )

    for col_monto in ["Valor_Neto", "Valor_Total", "Total_Servicio"]:
        mostrar[col_monto] = mostrar[col_monto].apply(
            lambda v: "" if _limpiar_monto_planilla(v) <= 0 else pesos(_limpiar_monto_planilla(v))
        )

    columnas_tabla = [
        "Tipo_Equipo", "Patente_Codigo", "Tipo_Intervencion", "Fecha",
        "Servicios_Realizados", "Kilometraje", "UM", "Proveedor_Tipo",
        "Nombre_Proveedor", "Valor_Neto", "Valor_Total", "Total_Servicio",
        "Ceco", "Contrato"
    ]
    mostrar = mostrar[[c for c in columnas_tabla if c in mostrar.columns]].copy()
    mostrar = mostrar.rename(
        columns={
            "Tipo_Equipo": "Tipo equipo",
            "Patente_Codigo": "Patente",
            "Tipo_Intervencion": "Tipo de intervención",
            "Servicios_Realizados": "Servicios realizados",
            "Kilometraje": "Kilometraje",
            "UM": "UM",
            "Proveedor_Tipo": "Proveedor",
            "Nombre_Proveedor": "Nombre proveedor",
            "Valor_Neto": "Valor neto",
            "Valor_Total": "Valor total",
            "Total_Servicio": "Total servicio",
            "Ceco": "Ceco",
            "Contrato": "Contrato",
        }
    )

    st.markdown(
        f'<div class="panel-title">Registro de Intervenciones <span style="font-size:13px;font-weight:700;">({len(mostrar)} registros)</span></div>',
        unsafe_allow_html=True,
    )
    mostrar_tabla_clara(mostrar, height=560)


def mostrar_panel():
    fuente_datos, datos = cargar_datos()

    equipos = preparar_equipos(datos["EQUIPOS"])
    equipos_planilla = preparar_equipos(datos.get("EQUIPOS_PLANILLA", datos["EQUIPOS"]))
    mantenciones_google = preparar_mantenciones(datos["MANTENCIONES"])
    mantenciones_planilla = preparar_mantenciones_planilla(datos.get("MANTENCIONES_PLANILLA", pd.DataFrame()))
    gastos = preparar_gastos(datos["GASTOS_ADICIONALES"])
    checklist = preparar_checklist(datos["CHECKLIST"])
    combustible = preparar_combustible(datos["COMBUSTIBLE"])
    documentos = preparar_documentos(datos["DOCUMENTOS"])
    proximas_base = construir_proximas_mantenciones(equipos, mantenciones_google)

    with st.sidebar:
        pagina, filtro_equipo, filtro_contrato, filtro_anio, filtro_mes = construir_menu(
            equipos_planilla,
            mantenciones=mantenciones_planilla,
        )

    equipos_planilla_f = filtrar_por_contrato(equipos_planilla, filtro_contrato)
    equipos_planilla_f = filtrar_por_equipo_catalogo(
        equipos_planilla_f, filtro_equipo, equipos_planilla
    )
    equipos_f = equipos_planilla_f.copy()

    # Mantenciones del menú: fuente oficial = segunda hoja del Excel local.
    mant_planilla_f = filtrar_por_contrato(mantenciones_planilla, filtro_contrato)

    # El filtro Equipo representa Tipo_Equipo de la hoja MANTENCIONES.
    if filtro_equipo != "Todos los equipos" and "Tipo_Equipo" in mant_planilla_f.columns:
        mant_planilla_f = mant_planilla_f[
            mant_planilla_f["Tipo_Equipo"].fillna("").astype(str).str.strip().str.casefold()
            == str(filtro_equipo).strip().casefold()
        ].copy()

    # Año y Mes delimitan el período de los cuatro tipos de intervención
    # (Reparacion, Mantencion, Logistica y Documentacion).
    if "Fecha" in mant_planilla_f.columns:
        fechas_local = mant_planilla_f["Fecha"].apply(convertir_fecha)
        if filtro_anio != "Todos":
            mascara_anio = fechas_local.dt.year == int(filtro_anio)
            mant_planilla_f = mant_planilla_f[mascara_anio].copy()
            fechas_local = mant_planilla_f["Fecha"].apply(convertir_fecha)
        if filtro_mes != "Todos":
            mes_numero = next((n for n, nombre in MESES.items() if nombre == filtro_mes), None)
            if mes_numero is not None:
                mascara_mes = fechas_local.dt.month == mes_numero
                mant_planilla_f = mant_planilla_f[mascara_mes].copy()

    # Respaldo de los demás módulos existentes, respetando Año y Mes.
    mant_f = aplicar_filtro_periodo(mantenciones_google, "Todos los equipos", filtro_anio, filtro_mes)
    gastos_f = aplicar_filtro_periodo(gastos, "Todos los equipos", filtro_anio, filtro_mes)
    combustible_f = aplicar_filtro_periodo(combustible, "Todos los equipos", filtro_anio, filtro_mes)
    checklist_f = aplicar_filtro_periodo(checklist, "Todos los equipos", filtro_anio, filtro_mes)
    documentos_f = aplicar_filtro_periodo(documentos, "Todos los equipos", filtro_anio, filtro_mes)

    mant_f = filtrar_por_equipo_catalogo(
        filtrar_por_contrato(mant_f, filtro_contrato), filtro_equipo, equipos_planilla
    )
    gastos_f = filtrar_por_equipo_catalogo(
        filtrar_por_contrato(gastos_f, filtro_contrato), filtro_equipo, equipos_planilla
    )
    combustible_f = filtrar_por_equipo_catalogo(
        filtrar_por_contrato(combustible_f, filtro_contrato), filtro_equipo, equipos_planilla
    )
    checklist_f = filtrar_por_equipo_catalogo(
        filtrar_por_contrato(checklist_f, filtro_contrato), filtro_equipo, equipos_planilla
    )
    documentos_f = filtrar_por_equipo_catalogo(
        filtrar_por_contrato(documentos_f, filtro_contrato), filtro_equipo, equipos_planilla
    )

    if pagina == "📊 Dashboard Ejecutivo":
        titulo_pagina = "Seguimiento y Control de Equipos Móviles"
    else:
        titulo_pagina = (
            pagina.replace("🚚 ", "")
            .replace("🛠️ ", "")
            .replace("📁 ", "")
        )

    encabezado(titulo_pagina)

    if pagina == "📊 Dashboard Ejecutivo":
        pagina_dashboard(equipos_f, mant_f, gastos_f, combustible_f, proximas_base, filtro_equipo)
    elif pagina == "🚚 Equipos":
        pagina_equipos(equipos_planilla_f)
    elif pagina == "🛠️ Intervenciones":
        pagina_mantenciones(mant_planilla_f)
    elif pagina == "📁 Documentacion":
        pagina_documentos(documentos_f)

    st.markdown(
        f"""
        <div style="text-align:center; color:#64748b; font-size:12px; padding:22px; line-height:1.55;">
            <div>Panel desarrollado por.</div>
            <div><b>Ricardo Grez – Contract Manager | SAIVAM</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )



# =========================================================
# AJUSTE FINAL: FILTROS SOLO DENTRO DE MANTENCIONES
# - Menú lateral: sin filtros.
# - Mantenciones: Equipo, Contrato, Año y Mes debajo del título.
# =========================================================
def construir_menu(equipos=None, mantenciones=None, gastos=None, combustible=None, checklist=None, documentos=None):
    """Menú lateral fijo: solo navegación y datos del contrato, sin filtros."""
    ruta_logo_menu = (
        buscar_imagen_por_nombre("logoredondo")
        or buscar_imagen_por_nombre("logo redondo")
        or buscar_imagen_por_nombre("logo_redondo")
        or buscar_imagen_por_nombre("logo-redondo")
    )

    if ruta_logo_menu:
        logo_menu_b64 = archivo_a_base64(ruta_logo_menu)
        logo_menu_mime = extension_mime(ruta_logo_menu)
        icono_menu_html = (
            '<div class="menu-icon-img">'
            f'<img src="data:{logo_menu_mime};base64,{logo_menu_b64}" alt="Logo menú">'
            '</div>'
        )
    else:
        icono_menu_html = '<div class="menu-icon">🚜</div>'

    st.markdown(
        f"""
        <div class="menu-bg"></div>
        <div class="menu-marker menu-state-expanded"></div>
        <div class="menu-panel-content">
            <div class="menu-brand">
                {icono_menu_html}
                <div class="menu-text">
                    <div class="menu-title">SEGUIMIENTO<br>EQUIPOS MÓVILES</div>
                    <div class="menu-subtitle">SAIVAM · MULCHÉN</div>
                </div>
            </div>
            <hr class="menu-line">
        </div>
        <div class="menu-top-gap"></div>
        """,
        unsafe_allow_html=True,
    )

    paginas_menu = {
        "panel": ("📊", "Resumen Ejecutivo", "📊 Dashboard Ejecutivo"),
        "equipos": ("🚚", "Equipos", "🚚 Equipos"),
        "mantenciones": ("🛠️", "Intervenciones", "🛠️ Intervenciones"),
        "documentos": ("📁", "Documentacion (Pdt)", "📁 Documentacion"),
    }

    pagina_actual = st.query_params.get("pagina", "panel")
    if pagina_actual not in paginas_menu:
        pagina_actual = "panel"
        st.query_params["pagina"] = "panel"

    for clave, (icono, nombre_visible, _) in paginas_menu.items():
        es_actual = clave == pagina_actual
        presionado = st.button(
            f"{icono} {nombre_visible}",
            key=f"menu_estable_{clave}",
            help=nombre_visible,
            use_container_width=True,
            disabled=es_actual,
        )
        if presionado:
            st.query_params["pagina"] = clave
            st.session_state["_saivam_mobile_menu_open"] = False
            st.rerun()

    st.markdown('<hr class="menu-line">', unsafe_allow_html=True)

    # Se eliminan completamente los filtros del menú lateral.
    st.markdown(
        f"""
        <div class="menu-footer-box" style="margin-top:28px;">
            <div class="menu-info">
                Versión {VERSION}
            </div>
        </div>

        <div class="sidebar-credit-footer">
            <div class="sidebar-credit-management">
                <div>Gestión de Mantenimiento</div>
                <div>Rodrigo Parra - Jefe de Mantenimiento</div>
            </div>
            <div class="sidebar-credit-divider"></div>
            <div class="sidebar-credit-developed">
                <div>Panel desarrollado por.</div>
                <div>Ricardo Grez – Contract Manager | SAIVAM</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return paginas_menu[pagina_actual][2]


def pagina_mantenciones(mant_f, equipos_ref=None):
    """Intervenciones con Equipo, Contrato, Modelo, Año y Mes dentro de la página.

    Para este módulo se utilizan solo tres familias operativas:
    Reparación, Mantención y Logística. Los registros de Documentación
    se consolidan dentro de Logística para KPI, gráfico y tabla.
    """
    mant_origen = mant_f.copy() if isinstance(mant_f, pd.DataFrame) else pd.DataFrame()

    # En el menú Intervenciones, Documentación forma parte de Logística.
    # Se trabaja sobre una copia para no alterar la base utilizada por otros módulos.
    if not mant_origen.empty and "Tipo_Intervencion" in mant_origen.columns:
        mant_origen["Tipo_Intervencion"] = mant_origen["Tipo_Intervencion"].apply(
            _normalizar_tipo_intervencion
        )
        mant_origen.loc[
            mant_origen["Tipo_Intervencion"] == "Documentacion",
            "Tipo_Intervencion",
        ] = "Logistica"

    # -----------------------------------------------------
    # Modelo de cada mantención
    # -----------------------------------------------------
    # La hoja MANTENCIONES actual no siempre trae una columna MODELO.
    # Cuando falta, se obtiene desde la hoja EQUIPOS usando la patente como llave.
    if "Modelo" not in mant_origen.columns:
        mant_origen["Modelo"] = ""

    if isinstance(equipos_ref, pd.DataFrame) and not equipos_ref.empty:
        def _clave_patente_modelo(valor):
            return re.sub(r"[^A-Z0-9]", "", str(valor).upper())

        mapa_modelos = {}
        for _, fila_eq in equipos_ref.iterrows():
            patente_eq = _clave_patente_modelo(fila_eq.get("Patente_Codigo", ""))
            modelo_eq = str(fila_eq.get("Modelo", "")).strip()
            if patente_eq and modelo_eq.lower() not in ["", "nan", "none", "nat"]:
                mapa_modelos[patente_eq] = modelo_eq

        if "Patente_Codigo" in mant_origen.columns:
            for idx in mant_origen.index:
                modelo_actual = str(mant_origen.at[idx, "Modelo"]).strip()
                if modelo_actual.lower() in ["", "nan", "none", "nat"]:
                    clave_patente = _clave_patente_modelo(mant_origen.at[idx, "Patente_Codigo"])
                    if clave_patente in mapa_modelos:
                        mant_origen.at[idx, "Modelo"] = mapa_modelos[clave_patente]

    # -----------------------------------------------------
    # Filtros dependientes: cada selección limita las opciones
    # válidas de los otros filtros. Se conserva como prioridad
    # el último filtro modificado por el usuario.
    # -----------------------------------------------------
    mant_filtros = mant_origen.copy()

    if "Fecha" in mant_filtros.columns:
        fechas_filtro = mant_filtros["Fecha"].apply(convertir_fecha)
        mant_filtros["_Filtro_Ano"] = fechas_filtro.dt.year
        mant_filtros["_Filtro_Mes_Num"] = fechas_filtro.dt.month
        mant_filtros["_Filtro_Mes"] = mant_filtros["_Filtro_Mes_Num"].map(MESES)
    else:
        mant_filtros["_Filtro_Ano"] = pd.NA
        mant_filtros["_Filtro_Mes_Num"] = pd.NA
        mant_filtros["_Filtro_Mes"] = ""

    configuracion_filtros = {
        "equipo": {
            "key": "filtro_equipo_mantenciones",
            "columna": "Tipo_Equipo",
            "default": "Todos los equipos",
        },
        "contrato": {
            "key": "filtro_contrato_mantenciones",
            "columna": "Contrato",
            "default": "Todos los contratos",
        },
        "modelo": {
            "key": "filtro_modelo_mantenciones",
            "columna": "Modelo",
            "default": "Todos los modelos",
        },
        "anio": {
            "key": "filtro_anio_mantenciones",
            "columna": "_Filtro_Ano",
            "default": "Todos",
        },
        "mes": {
            "key": "filtro_mes_mantenciones",
            "columna": "_Filtro_Mes",
            "default": "Todos",
        },
    }

    orden_base_filtros = ["contrato", "equipo", "modelo", "anio", "mes"]

    def _marcar_ultimo_filtro_intervenciones(nombre_filtro):
        st.session_state["_ultimo_filtro_intervenciones"] = nombre_filtro

    def _opciones_disponibles_intervenciones(df_base, nombre_filtro):
        config = configuracion_filtros[nombre_filtro]
        columna = config["columna"]

        if df_base is None or df_base.empty or columna not in df_base.columns:
            return []

        if nombre_filtro == "anio":
            valores = pd.to_numeric(df_base[columna], errors="coerce").dropna()
            return sorted({int(v) for v in valores.tolist()}, reverse=True)

        if nombre_filtro == "mes":
            presentes = {
                str(v).strip()
                for v in df_base[columna].dropna().tolist()
                if str(v).strip().lower() not in ["", "nan", "none", "nat"]
            }
            return [MESES[n] for n in range(1, 13) if MESES[n] in presentes]

        return sorted(
            {
                str(v).strip()
                for v in df_base[columna].dropna().tolist()
                if str(v).strip().lower() not in ["", "nan", "none", "nat"]
            },
            key=lambda x: x.casefold(),
        )

    def _aplicar_un_filtro_intervenciones(df_base, nombre_filtro, valor):
        config = configuracion_filtros[nombre_filtro]
        columna = config["columna"]
        valor_default = config["default"]

        if valor in [None, "", valor_default] or columna not in df_base.columns:
            return df_base.copy()

        if nombre_filtro == "anio":
            serie = pd.to_numeric(df_base[columna], errors="coerce")
            return df_base[serie == int(valor)].copy()

        serie = df_base[columna].fillna("").astype(str).str.strip().str.casefold()
        return df_base[serie == str(valor).strip().casefold()].copy()

    # Inicializa los estados de los filtros.
    for nombre, config in configuracion_filtros.items():
        if config["key"] not in st.session_state:
            st.session_state[config["key"]] = config["default"]

    # El último filtro tocado se procesa primero. Así, por ejemplo, si el
    # usuario cambia Contrato, ese contrato se mantiene y Equipo/Modelo/Año/Mes
    # se limpian solamente cuando ya no corresponden a la selección realizada.
    ultimo_filtro = st.session_state.get("_ultimo_filtro_intervenciones", "contrato")
    if ultimo_filtro not in configuracion_filtros:
        ultimo_filtro = "contrato"

    orden_validacion = [ultimo_filtro] + [
        nombre for nombre in orden_base_filtros if nombre != ultimo_filtro
    ]

    base_validacion = mant_filtros.copy()
    for nombre_filtro in orden_validacion:
        config = configuracion_filtros[nombre_filtro]
        valor_actual = st.session_state.get(config["key"], config["default"])
        disponibles = _opciones_disponibles_intervenciones(
            base_validacion, nombre_filtro
        )

        if valor_actual != config["default"] and valor_actual not in disponibles:
            st.session_state[config["key"]] = config["default"]
            valor_actual = config["default"]

        if valor_actual != config["default"]:
            base_validacion = _aplicar_un_filtro_intervenciones(
                base_validacion, nombre_filtro, valor_actual
            )

    # Calcula las opciones finales de cada selector usando los demás filtros
    # activos. De esta forma todos los selectores se actualizan entre sí.
    opciones_finales = {}
    for nombre_filtro, config in configuracion_filtros.items():
        base_opciones = mant_filtros.copy()

        for otro_filtro, otra_config in configuracion_filtros.items():
            if otro_filtro == nombre_filtro:
                continue

            otro_valor = st.session_state.get(
                otra_config["key"], otra_config["default"]
            )
            if otro_valor != otra_config["default"]:
                base_opciones = _aplicar_un_filtro_intervenciones(
                    base_opciones, otro_filtro, otro_valor
                )

        disponibles = _opciones_disponibles_intervenciones(
            base_opciones, nombre_filtro
        )
        opciones_finales[nombre_filtro] = [config["default"]] + disponibles

    opciones_equipo = opciones_finales["equipo"]
    opciones_contrato = opciones_finales["contrato"]
    opciones_modelo = opciones_finales["modelo"]
    opciones_anio = opciones_finales["anio"]
    opciones_mes = opciones_finales["mes"]

    # -----------------------------------------------------
    # Presentación compacta de los filtros debajo del título
    # -----------------------------------------------------
    st.markdown(
        """
        <style>
        div[data-testid="stMain"] div[data-testid="stSelectbox"] label p {
            font-size: 13px !important;
            font-weight: 700 !important;
        }
        div[data-testid="stMain"] div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
            min-height: 38px !important;
            height: 38px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_equipo, col_contrato, col_modelo, col_anio, col_mes, _ = st.columns([1.45, 1.45, 1.45, 0.75, 0.9, 2.0])
    with col_equipo:
        filtro_equipo = st.selectbox(
            "Equipo",
            opciones_equipo,
            key="filtro_equipo_mantenciones",
            on_change=_marcar_ultimo_filtro_intervenciones,
            args=("equipo",),
        )
    with col_contrato:
        filtro_contrato = st.selectbox(
            "Contrato",
            opciones_contrato,
            key="filtro_contrato_mantenciones",
            on_change=_marcar_ultimo_filtro_intervenciones,
            args=("contrato",),
        )
    with col_modelo:
        filtro_modelo = st.selectbox(
            "Modelo",
            opciones_modelo,
            key="filtro_modelo_mantenciones",
            on_change=_marcar_ultimo_filtro_intervenciones,
            args=("modelo",),
        )
    with col_anio:
        filtro_anio = st.selectbox(
            "Año",
            opciones_anio,
            key="filtro_anio_mantenciones",
            on_change=_marcar_ultimo_filtro_intervenciones,
            args=("anio",),
        )
    with col_mes:
        filtro_mes = st.selectbox(
            "Mes",
            opciones_mes,
            key="filtro_mes_mantenciones",
            on_change=_marcar_ultimo_filtro_intervenciones,
            args=("mes",),
        )

    # -----------------------------------------------------
    # Aplicación simultánea de los cinco filtros
    # -----------------------------------------------------
    mant_base = mant_origen.copy()

    if filtro_equipo != "Todos los equipos" and "Tipo_Equipo" in mant_base.columns:
        mant_base = mant_base[
            mant_base["Tipo_Equipo"].fillna("").astype(str).str.strip().str.casefold()
            == str(filtro_equipo).strip().casefold()
        ].copy()

    if filtro_contrato != "Todos los contratos" and "Contrato" in mant_base.columns:
        mant_base = mant_base[
            mant_base["Contrato"].fillna("").astype(str).str.strip().str.casefold()
            == str(filtro_contrato).strip().casefold()
        ].copy()

    if filtro_modelo != "Todos los modelos" and "Modelo" in mant_base.columns:
        mant_base = mant_base[
            mant_base["Modelo"].fillna("").astype(str).str.strip().str.casefold()
            == str(filtro_modelo).strip().casefold()
        ].copy()

    if not mant_base.empty and "Fecha" in mant_base.columns:
        fechas = mant_base["Fecha"].apply(convertir_fecha)
        if filtro_anio != "Todos":
            mant_base = mant_base[fechas.dt.year == int(filtro_anio)].copy()
            fechas = mant_base["Fecha"].apply(convertir_fecha)
        if filtro_mes != "Todos":
            mes_numero = next((n for n, nombre in MESES.items() if nombre == filtro_mes), None)
            if mes_numero is not None:
                mant_base = mant_base[fechas.dt.month == mes_numero].copy()

    if mant_base.empty:
        st.info("No existen intervenciones para los filtros seleccionados.")
        return

    tipos_orden = ["Reparacion", "Mantencion", "Logistica"]
    total_intervenciones = (
        float(mant_base["Total_Servicio"].sum())
        if "Total_Servicio" in mant_base.columns
        else 0.0
    )

    # -----------------------------------------------------
    # KPI: 3 tipos de intervención + total de servicios
    # -----------------------------------------------------
    columnas_kpi = st.columns([1, 1, 1, 1.12])
    iconos = {
        "Reparacion": "🔧",
        "Mantencion": "🛠️",
        "Logistica": "🚚",
    }
    fondos = {
        "Reparacion": "#fee2e2",
        "Mantencion": "#dbeafe",
        "Logistica": "#fef3c7",
    }

    for col_ui, tipo in zip(columnas_kpi[:3], tipos_orden):
        bloque = mant_base[mant_base["Tipo_Intervencion"] == tipo]
        cantidad = len(bloque)
        monto = (
            float(bloque["Total_Servicio"].sum())
            if "Total_Servicio" in bloque.columns
            else 0.0
        )
        with col_ui:
            kpi_card(
                iconos[tipo],
                tipo,
                str(cantidad),
                f"Registros · {pesos(monto)}",
                fondos[tipo],
            )

    with columnas_kpi[3]:
        kpi_card(
            "💰",
            "Total servicios",
            pesos(total_intervenciones),
            "Monto del período filtrado",
            "#dcfce7",
        )

    # Separación visible entre las tarjetas KPI y el gráfico.
    st.markdown('<div style="height:34px"></div>', unsafe_allow_html=True)

    # -----------------------------------------------------
    # Gráfico de barras con valores visibles
    # -----------------------------------------------------
    resumen = (
        mant_base.groupby("Tipo_Intervencion", as_index=False)
        .agg(
            Registros=("Tipo_Intervencion", "size"),
            Total_Servicio=("Total_Servicio", "sum"),
        )
    )
    resumen["_orden"] = resumen["Tipo_Intervencion"].apply(
        lambda x: tipos_orden.index(x) if x in tipos_orden else len(tipos_orden)
    )
    resumen = resumen.sort_values("_orden").drop(columns="_orden")

    if not resumen.empty:
        colores_intervencion = {
            "Reparacion": "#ef4444",
            "Mantencion": "#2563eb",
            "Logistica": "#f59e0b",
        }
        fig = px.bar(
            resumen,
            x="Tipo_Intervencion",
            y="Registros",
            text="Registros",
            color="Tipo_Intervencion",
            color_discrete_map=colores_intervencion,
            category_orders={"Tipo_Intervencion": tipos_orden},
            template="plotly_white",
            title="Distribución de intervenciones",
            custom_data=["Total_Servicio"],
        )
        max_registros = max(float(resumen["Registros"].max()), 1.0)
        fig.update_traces(
            texttemplate="<b>%{y}</b>",
            textposition="outside",
            textfont=dict(size=18, color="#0f172a"),
            cliponaxis=False,
            hovertemplate=(
                "Tipo: %{x}<br>Registros: %{y}<br>"
                "Total servicio: $%{customdata[0]:,.0f}<extra></extra>"
            ),
        )
        fig.update_layout(
            xaxis_title="Tipo de intervención",
            yaxis_title="Cantidad de registros",
            yaxis=dict(range=[0, max_registros * 1.28]),
            margin=dict(l=28, r=24, t=78, b=44),
            uniformtext_minsize=14,
            uniformtext_mode="show",
        )
        st.plotly_chart(aplicar_formato_grafico(fig, 340), use_container_width=True)

    # -----------------------------------------------------
    # Tabla detallada
    # -----------------------------------------------------
    mostrar = mant_base.copy()
    if "Fecha" in mostrar.columns:
        mostrar["Fecha"] = mostrar["Fecha"].apply(fecha_texto)
    if "Kilometraje" in mostrar.columns:
        mostrar["Kilometraje"] = mostrar["Kilometraje"].apply(
            lambda v: "" if limpiar_numero(v) <= 0 else numero(v)
        )

    for col_monto in ["Valor_Neto", "Valor_Total", "Total_Servicio"]:
        if col_monto in mostrar.columns:
            mostrar[col_monto] = mostrar[col_monto].apply(
                lambda v: ""
                if _limpiar_monto_planilla(v) <= 0
                else pesos(_limpiar_monto_planilla(v))
            )

    columnas_tabla = [
        "Tipo_Equipo",
        "Patente_Codigo",
        "Tipo_Intervencion",
        "Fecha",
        "Servicios_Realizados",
        "Kilometraje",
        "UM",
        "Proveedor_Tipo",
        "Nombre_Proveedor",
        "Valor_Neto",
        "Valor_Total",
        "Total_Servicio",
        "Ceco",
        "Contrato",
    ]
    mostrar = mostrar[[c for c in columnas_tabla if c in mostrar.columns]].copy()
    mostrar = mostrar.rename(
        columns={
            "Tipo_Equipo": "Tipo equipo",
            "Patente_Codigo": "Patente",
            "Tipo_Intervencion": "Tipo de intervención",
            "Servicios_Realizados": "Servicios realizados",
            "Kilometraje": "Kilometraje",
            "UM": "UM",
            "Proveedor_Tipo": "Proveedor",
            "Nombre_Proveedor": "Nombre proveedor",
            "Valor_Neto": "Valor neto",
            "Valor_Total": "Valor total",
            "Total_Servicio": "Total servicio",
            "Ceco": "Ceco",
            "Contrato": "Contrato",
        }
    )

    st.markdown(
        f'<div class="panel-title">Registro de Intervenciones '
        f'<span style="font-size:13px;font-weight:700;">({len(mostrar)} registros)</span></div>',
        unsafe_allow_html=True,
    )
    mostrar_tabla_clara(mostrar, height=560)



# =========================================================
# RESUMEN EJECUTIVO PROFESIONAL V9.0
# - Usa exclusivamente la misma base del menú Intervenciones.
# - Documentación se consolida en Logística, igual que en Intervenciones.
# - KPIs, gráficos, tablas y filtros se calculan desde los datos reales.
# - No muestra indicadores (disponibilidad/confiabilidad) que la planilla no soporta.
# =========================================================

def _dashboard_base_intervenciones(mant_f):
    """Prepara la base del resumen con exactamente las mismas 3 familias de Intervenciones."""
    base = mant_f.copy() if isinstance(mant_f, pd.DataFrame) else pd.DataFrame()

    columnas = [
        "Tipo_Equipo", "Patente_Codigo", "Modelo", "Tipo_Intervencion", "Fecha",
        "Servicios_Realizados", "Kilometraje", "UM", "Proveedor_Tipo",
        "Nombre_Proveedor", "Valor_Neto", "Valor_Total", "Total_Servicio",
        "Ceco", "Contrato",
    ]

    if base.empty:
        return pd.DataFrame(columns=columnas)

    for col in columnas:
        if col not in base.columns:
            base[col] = 0.0 if col in ["Kilometraje", "Valor_Neto", "Valor_Total", "Total_Servicio"] else ""

    base["Tipo_Intervencion"] = base["Tipo_Intervencion"].apply(_normalizar_tipo_intervencion)
    base.loc[
        base["Tipo_Intervencion"] == "Documentacion",
        "Tipo_Intervencion",
    ] = "Logistica"

    base = base[base["Tipo_Intervencion"].isin(["Reparacion", "Mantencion", "Logistica"])].copy()
    base["Fecha"] = base["Fecha"].apply(convertir_fecha)
    base["Valor_Neto"] = base["Valor_Neto"].apply(_limpiar_monto_planilla)
    base["Valor_Total"] = base["Valor_Total"].apply(_limpiar_monto_planilla)
    # Una única fuente monetaria para todo el dashboard: VALOR TOTAL.
    base["Total_Servicio"] = base["Valor_Total"].astype(float)
    base["Kilometraje"] = base["Kilometraje"].apply(limpiar_numero)

    for col in ["Tipo_Equipo", "Patente_Codigo", "Modelo", "Contrato", "Ceco", "Proveedor_Tipo", "Nombre_Proveedor"]:
        base[col] = base[col].fillna("").astype(str).str.strip()

    return base[columnas].copy()


def _dashboard_nombre_tipo(tipo):
    return {
        "Reparacion": "Reparación",
        "Mantencion": "Mantención",
        "Logistica": "Logística",
    }.get(str(tipo), str(tipo))


def _dashboard_pesos_compacto(valor):
    valor = float(valor or 0)
    abs_valor = abs(valor)
    if abs_valor >= 1_000_000_000:
        return f"${valor / 1_000_000_000:.1f} mil MM".replace(".", ",")
    if abs_valor >= 1_000_000:
        return f"${valor / 1_000_000:.1f} MM".replace(".", ",")
    if abs_valor >= 1_000:
        return f"${valor / 1_000:.1f} mil".replace(".", ",")
    return "$" + f"{int(round(valor)):,}".replace(",", ".")


def _dashboard_cantidad_equipos(base):
    """Cuenta equipos intervenidos privilegiando patente/código y usando equipo-modelo como respaldo."""
    if base is None or base.empty:
        return 0

    claves = []
    for _, fila in base.iterrows():
        patente = str(fila.get("Patente_Codigo", "")).strip()
        tipo = str(fila.get("Tipo_Equipo", "")).strip()
        modelo = str(fila.get("Modelo", "")).strip()

        if patente.lower() not in ["", "nan", "none", "nat"]:
            claves.append("PAT-" + patente.casefold())
        elif tipo.lower() not in ["", "nan", "none", "nat"]:
            claves.append("EQ-" + (tipo + "|" + modelo).casefold())

    return len(set(claves))


def _dashboard_costos_por_intervencion(mant_f):
    """Costo real de Total Servicio por Reparación, Mantención y Logística."""
    base = _dashboard_base_intervenciones(mant_f)
    tipos = ["Reparacion", "Mantencion", "Logistica"]

    if base.empty:
        return pd.DataFrame({"Tipo_Intervencion": tipos, "Costo": [0.0, 0.0, 0.0], "Registros": [0, 0, 0]})

    resumen = (
        base.groupby("Tipo_Intervencion", as_index=False)
        .agg(Costo=("Total_Servicio", "sum"), Registros=("Tipo_Intervencion", "size"))
    )
    resumen = pd.DataFrame({"Tipo_Intervencion": tipos}).merge(
        resumen, on="Tipo_Intervencion", how="left"
    )
    resumen["Costo"] = resumen["Costo"].fillna(0.0)
    resumen["Registros"] = resumen["Registros"].fillna(0).astype(int)
    return resumen


def _dashboard_grafico_intervenciones(mant_f):
    """Barras ejecutivas: cantidad de intervenciones por tipo."""
    resumen = _dashboard_costos_por_intervencion(mant_f)
    resumen["Tipo"] = resumen["Tipo_Intervencion"].apply(_dashboard_nombre_tipo)

    colores = {
        "Reparacion": "#ef4444",
        "Mantencion": "#2563eb",
        "Logistica": "#f59e0b",
    }

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=resumen["Tipo"],
            y=resumen["Registros"],
            text=resumen["Registros"],
            textposition="outside",
            cliponaxis=False,
            marker=dict(
                color=[colores.get(v, "#94a3b8") for v in resumen["Tipo_Intervencion"]],
                line=dict(width=0),
            ),
            customdata=[[pesos(v)] for v in resumen["Costo"]],
            hovertemplate="%{x}<br>Intervenciones: %{y}<br>Costo: %{customdata[0]}<extra></extra>",
        )
    )

    ymax = max(float(resumen["Registros"].max()), 1.0)
    fig.update_layout(
        height=285,
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        margin=dict(l=34, r=18, t=24, b=34),
        showlegend=False,
        xaxis=dict(title=None, showgrid=False, tickfont=dict(size=11, color="#475569")),
        yaxis=dict(
            title=None,
            range=[0, ymax * 1.25],
            gridcolor="rgba(148,163,184,.18)",
            zeroline=False,
            tickfont=dict(size=10, color="#64748b"),
        ),
        font=dict(color="#0f172a"),
        hoverlabel=dict(bgcolor="#ffffff", font_color="#0f172a"),
    )
    fig.update_traces(textfont=dict(size=14, color="#0f172a"))
    return fig


def _dashboard_donut_intervenciones(mant_f):
    """Dona ejecutiva: participación del costo real por tipo de intervención."""
    resumen = _dashboard_costos_por_intervencion(mant_f)
    total = float(resumen["Costo"].sum()) if not resumen.empty else 0.0

    colores = {
        "Reparacion": "#ef4444",
        "Mantencion": "#2563eb",
        "Logistica": "#f59e0b",
    }

    fig = go.Figure()
    if total <= 0:
        fig.update_layout(
            height=285,
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            annotations=[dict(
                text="Sin costos registrados",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color="#64748b"),
            )],
        )
        return fig

    resumen = resumen[resumen["Costo"] > 0].copy()
    labels = resumen["Tipo_Intervencion"].apply(_dashboard_nombre_tipo).tolist()
    values = resumen["Costo"].astype(float).tolist()
    colors = [colores.get(v, "#94a3b8") for v in resumen["Tipo_Intervencion"]]

    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.67,
            sort=False,
            marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
            textinfo="percent",
            texttemplate="%{percent:.0%}",
            textfont=dict(size=12),
            customdata=[pesos(v) for v in values],
            hovertemplate="%{label}<br>Costo: %{customdata}<br>Participación: %{percent}<extra></extra>",
            showlegend=True,
        )
    )

    fig.update_layout(
        height=285,
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        margin=dict(l=4, r=4, t=8, b=44),
        annotations=[dict(
            text=f"Costo total<br><b>{_dashboard_pesos_compacto(total)}</b>",
            x=0.5, y=0.55,
            showarrow=False,
            align="center",
            font=dict(size=12, color="#0f172a"),
        )],
        legend=dict(
            orientation="h",
            x=0.5, y=-0.02,
            xanchor="center", yanchor="top",
            font=dict(size=10, color="#475569"),
            bgcolor="rgba(255,255,255,0)",
        ),
        font=dict(color="#0f172a"),
    )
    return fig


def _dashboard_evolucion_costos(mant_f):
    """Evolución mensual del Total Servicio de la misma base de Intervenciones."""
    base = _dashboard_base_intervenciones(mant_f)
    fig = go.Figure()

    if base.empty or base["Fecha"].notna().sum() == 0:
        fig.update_layout(
            height=230,
            paper_bgcolor="rgba(255,255,255,0)",
            plot_bgcolor="rgba(255,255,255,0)",
            annotations=[dict(text="Sin datos para evolución", x=0.5, y=0.5, showarrow=False)],
            margin=dict(l=18, r=18, t=20, b=20),
        )
        return fig

    base = base[base["Fecha"].notna()].copy()
    base["Periodo_Fecha"] = base["Fecha"].dt.to_period("M").dt.to_timestamp()
    mensual = (
        base.groupby("Periodo_Fecha", as_index=False)
        .agg(Total_Servicio=("Total_Servicio", "sum"), Intervenciones=("Tipo_Intervencion", "size"))
        .sort_values("Periodo_Fecha")
    )
    mensual["Periodo"] = mensual["Periodo_Fecha"].apply(
        lambda d: f"{MESES.get(d.month, d.month)} {d.year}"
    )

    fig.add_trace(
        go.Scatter(
            x=mensual["Periodo"],
            y=mensual["Total_Servicio"],
            mode="lines+markers",
            line=dict(width=3, color="#2563eb"),
            marker=dict(size=8, color="#2563eb", line=dict(width=2, color="#ffffff")),
            fill="tozeroy",
            fillcolor="rgba(37,99,235,.07)",
            customdata=list(zip([pesos(v) for v in mensual["Total_Servicio"]], mensual["Intervenciones"])),
            hovertemplate="%{x}<br>Costo: %{customdata[0]}<br>Intervenciones: %{customdata[1]}<extra></extra>",
            name="Costo mensual",
        )
    )

    fig.update_layout(
        height=230,
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        margin=dict(l=48, r=18, t=18, b=54),
        showlegend=False,
        xaxis=dict(title=None, tickangle=-20, showgrid=False, tickfont=dict(size=10, color="#64748b")),
        yaxis=dict(title="Costo CLP", gridcolor="rgba(148,163,184,.18)", zeroline=False, tickfont=dict(size=10, color="#64748b")),
        hoverlabel=dict(bgcolor="#ffffff", font_color="#0f172a"),
    )
    return fig


def _dashboard_historico_intervenciones(mant_f):
    """Últimas intervenciones con las mismas columnas del registro operacional."""
    mostrar = _dashboard_base_intervenciones(mant_f)
    if mostrar.empty:
        return mostrar

    if "Fecha" in mostrar.columns:
        mostrar = mostrar.sort_values("Fecha", ascending=False, na_position="last")

    columnas = [
        "Tipo_Equipo", "Patente_Codigo", "Tipo_Intervencion", "Fecha",
        "Servicios_Realizados", "Kilometraje", "UM", "Proveedor_Tipo",
        "Nombre_Proveedor", "Total_Servicio", "Ceco", "Contrato",
    ]
    mostrar = mostrar[[c for c in columnas if c in mostrar.columns]].copy()
    mostrar["Tipo_Intervencion"] = mostrar["Tipo_Intervencion"].apply(_dashboard_nombre_tipo)

    return mostrar.rename(
        columns={
            "Tipo_Equipo": "Tipo equipo",
            "Patente_Codigo": "Patente",
            "Tipo_Intervencion": "Tipo de intervención",
            "Servicios_Realizados": "Servicios realizados",
            "Proveedor_Tipo": "Proveedor",
            "Nombre_Proveedor": "Nombre proveedor",
            "Total_Servicio": "Total servicio",
            "Ceco": "Ceco",
            "Contrato": "Contrato",
        }
    )


def _dashboard_render_costo_por_tipo(mant_f):
    """Bloque visual inspirado en el resumen de referencia, usando participación real del costo."""
    resumen = _dashboard_costos_por_intervencion(mant_f)
    total = float(resumen["Costo"].sum()) if not resumen.empty else 0.0
    colores = {
        "Reparacion": "#ef4444",
        "Mantencion": "#2563eb",
        "Logistica": "#f59e0b",
    }

    bloques = []
    for _, fila in resumen.iterrows():
        tipo = fila["Tipo_Intervencion"]
        costo = float(fila["Costo"])
        pct = (costo / total * 100) if total > 0 else 0.0
        bloques.append(
            f"""
            <div class="exec9-cost-row">
                <div class="exec9-cost-head">
                    <span>{escape_html(_dashboard_nombre_tipo(tipo))}</span>
                    <span>{pesos(costo)} · {pct:.1f}%</span>
                </div>
                <div class="exec9-progress-track">
                    <div class="exec9-progress-fill" style="width:{max(0, min(100, pct)):.2f}%; background:{colores.get(tipo, '#94a3b8')};"></div>
                </div>
            </div>
            """
        )

    st.markdown("".join(bloques), unsafe_allow_html=True)


def _dashboard_render_disponibilidad_equipos(resumen_disp):
    """Línea horizontal ejecutiva con el porcentaje actual de disponibilidad de equipos."""
    resumen_disp = resumen_disp or {}
    total = int(resumen_disp.get("total", 0) or 0)
    disponibles = int(resumen_disp.get("disponibles", 0) or 0)
    no_disponibles = int(resumen_disp.get("no_disponibles", 0) or 0)
    sin_estado = int(resumen_disp.get("sin_estado", 0) or 0)
    porcentaje = float(resumen_disp.get("porcentaje", 0.0) or 0.0)
    porcentaje = max(0.0, min(100.0, porcentaje))

    porcentaje_txt = f"{porcentaje:.1f}".replace(".", ",") + "%"
    detalle = f"{disponibles} disponibles · {no_disponibles} no disponibles"
    if sin_estado > 0:
        detalle += f" · {sin_estado} sin estado"

    if total <= 0:
        st.markdown(
            """
            <div class="exec9-availability-empty">
                Sin equipos registrados para calcular disponibilidad.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="exec9-availability-wrap">
            <div class="exec9-availability-head">
                <span>Disponibilidad actual</span>
                <span class="exec9-availability-pct">{porcentaje_txt}</span>
            </div>
            <div class="exec9-availability-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{porcentaje:.1f}">
                <div class="exec9-availability-fill" style="width:{porcentaje:.2f}%;"></div>
            </div>
            <div class="exec9-availability-scale">
                <span>0%</span><span>50%</span><span>100%</span>
            </div>
            <div class="exec9-availability-note">{escape_html(detalle)} · Total {total} equipos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _dashboard_tabla_costos_contrato(mant_f, equipos_f=None):
    """Resumen ejecutivo de costos por contrato.

    Muestra todos los contratos registrados en la hoja EQUIPOS, aunque no tengan
    intervenciones en el período seleccionado. También conserva contratos que
    existan en el historial de intervenciones para no perder trazabilidad.
    """
    base = _dashboard_base_intervenciones(mant_f)

    # Catálogo maestro de contratos: hoja EQUIPOS + historial de intervenciones.
    # Se usa una llave normalizada solo para evitar duplicados por mayúsculas/minúsculas.
    contratos_catalogo = {}

    def registrar_contratos(serie):
        if serie is None:
            return
        for valor in serie:
            nombre = str(valor).strip()
            if nombre.lower() in ["", "nan", "none", "nat"]:
                continue
            clave = nombre.casefold()
            if clave not in contratos_catalogo:
                contratos_catalogo[clave] = nombre

    if isinstance(equipos_f, pd.DataFrame) and not equipos_f.empty and "Contrato" in equipos_f.columns:
        registrar_contratos(equipos_f["Contrato"])

    if not base.empty and "Contrato" in base.columns:
        registrar_contratos(base["Contrato"])

    if not contratos_catalogo:
        return pd.DataFrame(columns=["Contrato", "Intervenciones", "Monto", "% total"])

    # Resumen real del período/filtros activos.
    if base.empty:
        resumen_actividad = pd.DataFrame(columns=["_Contrato_Key", "Intervenciones", "Monto"])
        total = 0.0
    else:
        base = base.copy()
        base["Contrato"] = base["Contrato"].fillna("").astype(str).str.strip()
        base.loc[base["Contrato"].isin(["", "nan", "None", "NaT"]), "Contrato"] = "Sin contrato"
        base["_Contrato_Key"] = base["Contrato"].str.casefold()
        total = float(base["Total_Servicio"].sum())
        resumen_actividad = (
            base.groupby("_Contrato_Key", as_index=False)
            .agg(
                Intervenciones=("Tipo_Intervencion", "size"),
                Monto=("Total_Servicio", "sum"),
            )
        )

    catalogo = pd.DataFrame(
        [
            {"_Contrato_Key": clave, "Contrato": nombre}
            for clave, nombre in contratos_catalogo.items()
        ]
    )

    resumen = catalogo.merge(resumen_actividad, on="_Contrato_Key", how="left")
    resumen["Intervenciones"] = resumen["Intervenciones"].fillna(0).astype(int)
    resumen["Monto"] = resumen["Monto"].fillna(0.0).astype(float)
    resumen["% total"] = resumen["Monto"].apply(
        lambda v: (v / total * 100) if total > 0 else 0.0
    )

    # Primero contratos con movimiento; luego los contratos sin actividad, en orden alfabético.
    resumen["_Con_Actividad"] = (
        (resumen["Intervenciones"] > 0) | (resumen["Monto"] > 0)
    ).astype(int)
    resumen = resumen.sort_values(
        ["_Con_Actividad", "Monto", "Intervenciones", "Contrato"],
        ascending=[False, False, False, True],
        key=lambda s: s.str.casefold() if s.name == "Contrato" else s,
    )

    return resumen[["Contrato", "Intervenciones", "Monto", "% total"]].reset_index(drop=True)



def _estado_disponibilidad_equipo(valor):
    """Convierte el Estado de la hoja EQUIPOS a una disponibilidad ejecutiva estándar.

    Acepta, entre otros:
    - OPERATIVO / DISPONIBLE -> Disponible
    - NO OPERATIVO / NO DISPONIBLE / FUERA DE SERVICIO -> No disponible
    """
    texto = normalizar_texto(valor)

    if texto in ["", "nan", "none", "nat", "sin_estado"]:
        return "Sin estado"

    # Importante: evaluar primero los estados negativos para que
    # "NO OPERATIVO" no sea interpretado como "OPERATIVO".
    negativos = [
        "no_operativo",
        "no_disponible",
        "indisponible",
        "inoperativo",
        "fuera_de_servicio",
        "fuera_servicio",
        "fuera_de_operacion",
        "fuera_operacion",
    ]
    if any(patron in texto for patron in negativos):
        return "No disponible"

    positivos = [
        "operativo",
        "disponible",
        "en_servicio",
        "en_operacion",
        "activo",
    ]
    if any(patron in texto for patron in positivos):
        return "Disponible"

    return "Sin estado"


def _resumen_disponibilidad_equipos(equipos):
    """Calcula disponibilidad actual sobre el total de equipos del catálogo."""
    if equipos is None or not isinstance(equipos, pd.DataFrame) or equipos.empty:
        return {
            "total": 0,
            "disponibles": 0,
            "no_disponibles": 0,
            "sin_estado": 0,
            "porcentaje": 0.0,
        }

    base = equipos.copy()

    # Evita contar filas de formato o encabezados vacíos si llegaran a existir.
    if "Tipo_Equipo" in base.columns:
        tipo = base["Tipo_Equipo"].fillna("").astype(str).str.strip().str.lower()
        base = base[~tipo.isin(["", "nan", "none", "nat"])].copy()

    if base.empty:
        return {
            "total": 0,
            "disponibles": 0,
            "no_disponibles": 0,
            "sin_estado": 0,
            "porcentaje": 0.0,
        }

    if "Estado" not in base.columns:
        base["Estado"] = ""

    disponibilidad = base["Estado"].apply(_estado_disponibilidad_equipo)
    total = len(base)
    disponibles = int((disponibilidad == "Disponible").sum())
    no_disponibles = int((disponibilidad == "No disponible").sum())
    sin_estado = int((disponibilidad == "Sin estado").sum())
    porcentaje = (disponibles / total * 100.0) if total > 0 else 0.0

    return {
        "total": total,
        "disponibles": disponibles,
        "no_disponibles": no_disponibles,
        "sin_estado": sin_estado,
        "porcentaje": porcentaje,
    }


def _disponibilidad_por_contrato(equipos):
    """Resume la disponibilidad actual de equipos para cada contrato visible.

    Usa la misma regla de Estado del indicador general, de modo que el porcentaje
    por contrato siempre sea consistente con la disponibilidad total.
    """
    columnas = [
        "Contrato", "Total", "Disponibles",
        "No disponibles", "Sin estado", "Disponibilidad_%"
    ]

    if equipos is None or not isinstance(equipos, pd.DataFrame) or equipos.empty:
        return pd.DataFrame(columns=columnas)

    base = equipos.copy()
    if "Contrato" not in base.columns:
        base["Contrato"] = "Sin contrato"

    # Evita filas de formato o encabezados vacíos.
    if "Tipo_Equipo" in base.columns:
        tipo = base["Tipo_Equipo"].fillna("").astype(str).str.strip().str.lower()
        base = base[~tipo.isin(["", "nan", "none", "nat"])].copy()

    if base.empty:
        return pd.DataFrame(columns=columnas)

    base["Contrato"] = base["Contrato"].fillna("").astype(str).str.strip()
    base.loc[
        base["Contrato"].str.lower().isin(["", "nan", "none", "nat"]),
        "Contrato",
    ] = "Sin contrato"

    if "Estado" not in base.columns:
        base["Estado"] = ""

    base["_Disponibilidad"] = base["Estado"].apply(_estado_disponibilidad_equipo)
    filas = []
    for contrato, grupo in base.groupby("Contrato", dropna=False):
        total = int(len(grupo))
        disponibles = int((grupo["_Disponibilidad"] == "Disponible").sum())
        no_disponibles = int((grupo["_Disponibilidad"] == "No disponible").sum())
        sin_estado = int((grupo["_Disponibilidad"] == "Sin estado").sum())
        porcentaje = (disponibles / total * 100.0) if total > 0 else 0.0
        filas.append(
            {
                "Contrato": str(contrato),
                "Total": total,
                "Disponibles": disponibles,
                "No disponibles": no_disponibles,
                "Sin estado": sin_estado,
                "Disponibilidad_%": porcentaje,
            }
        )

    salida = pd.DataFrame(filas, columns=columnas)
    return salida.sort_values("Contrato", key=lambda s: s.astype(str).str.casefold()).reset_index(drop=True)


def _dashboard_render_disponibilidad_por_contrato(equipos):
    """Muestra una subdivisión compacta de disponibilidad por contrato."""
    resumen = _disponibilidad_por_contrato(equipos)
    if resumen.empty:
        return

    # El HTML se construye sin sangrías ni saltos que Markdown pueda interpretar
    # como bloque de código. Así Streamlit renderiza las barras y no muestra
    # las etiquetas <div> como texto en pantalla.
    bloques = []
    for _, fila in resumen.iterrows():
        contrato = str(fila.get("Contrato", "Sin contrato"))
        total = int(fila.get("Total", 0) or 0)
        disponibles = int(fila.get("Disponibles", 0) or 0)
        no_disponibles = int(fila.get("No disponibles", 0) or 0)
        sin_estado = int(fila.get("Sin estado", 0) or 0)
        pct = max(0.0, min(100.0, float(fila.get("Disponibilidad_%", 0.0) or 0.0)))
        pct_txt = f"{pct:.1f}".replace(".", ",") + "%"

        detalle = f"{disponibles}/{total} disponibles"
        if no_disponibles > 0:
            detalle += f" · {no_disponibles} no disponibles"
        if sin_estado > 0:
            detalle += f" · {sin_estado} sin estado"

        bloques.append(
            '<div class="exec9-contract-availability-row">'
            '<div class="exec9-contract-availability-head">'
            f'<div class="exec9-contract-availability-name">{escape_html(contrato)}</div>'
            f'<div class="exec9-contract-availability-pct">{pct_txt}</div>'
            '</div>'
            f'<div class="exec9-contract-availability-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{pct:.1f}">'
            f'<div class="exec9-contract-availability-fill" style="width:{pct:.2f}%;"></div>'
            '</div>'
            f'<div class="exec9-contract-availability-detail">{escape_html(detalle)}</div>'
            '</div>'
        )

    html = (
        '<div class="exec9-contract-availability-section">'
        '<div class="exec9-contract-availability-title">Disponibilidad por contrato</div>'
        + ''.join(bloques)
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def pagina_dashboard(equipos_f, mant_f, gastos_f=None, combustible_f=None, proximas_originales=None, filtro_equipo=None):
    """Resumen ejecutivo profesional basado únicamente en datos reales de Intervenciones."""
    mant_base = _dashboard_base_intervenciones(mant_f)

    st.markdown(
        """
<style>
/* =========================================================
   Resumen Ejecutivo V9.0
   ========================================================= */
.exec9-subtitle {
    margin: 0 0 14px 0 !important;
    color: #64748b !important;
    font-size: 12px !important;
    font-weight: 650 !important;
}
.exec9-filter-label {
    color: #475569 !important;
    font-size: 11px !important;
    font-weight: 800 !important;
    margin-bottom: 3px !important;
}
.exec9-kpi {
    min-height: 112px;
    background: rgba(255,255,255,.90);
    border: 1px solid rgba(148,163,184,.30);
    border-radius: 16px;
    padding: 15px 17px;
    box-shadow: 0 8px 24px rgba(15,23,42,.055);
    position: relative;
    overflow: hidden;
}
.exec9-kpi::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: var(--accent, #2563eb);
}
.exec9-kpi-title {
    font-size: 11px;
    color: #64748b;
    font-weight: 800;
    letter-spacing: .02em;
    margin-bottom: 7px;
}
.exec9-kpi-value {
    color: #0f172a;
    font-size: 24px;
    line-height: 1.08;
    font-weight: 900;
    margin-bottom: 7px;
}
.exec9-kpi-note {
    color: #64748b;
    font-size: 10.5px;
    font-weight: 650;
    line-height: 1.25;
}
.exec9-panel {
    background: rgba(255,255,255,.86);
    border: 1px solid rgba(148,163,184,.30);
    border-radius: 16px;
    padding: 15px 16px 10px 16px;
    box-shadow: 0 8px 24px rgba(15,23,42,.045);
    min-height: 100%;
}
.exec9-panel-title {
    color: #0f172a;
    font-size: 15px;
    font-weight: 900;
    margin: 0 0 2px 0;
}
.exec9-panel-title-spaced {
    margin: 8px 0 18px 0 !important;
}
.exec9-panel-title-contract {
    margin: 8px 0 26px 0 !important;
}
.exec9-panel-subtitle {
    color: #64748b;
    font-size: 10.5px;
    font-weight: 650;
    margin: 0 0 8px 0;
}
.exec9-section-gap {
    height: 18px;
}
.exec9-cost-row {
    margin: 14px 1px 16px 1px;
}
.exec9-cost-head {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    color: #334155;
    font-size: 11px;
    font-weight: 800;
    margin-bottom: 7px;
}
.exec9-progress-track {
    height: 7px;
    background: #e2e8f0;
    border-radius: 999px;
    overflow: hidden;
}
.exec9-progress-fill {
    height: 100%;
    border-radius: 999px;
}
.exec9-mini-insight {
    margin-top: 10px;
    padding: 9px 11px;
    border-radius: 11px;
    background: rgba(248,250,252,.92);
    border: 1px solid rgba(148,163,184,.22);
    color: #475569;
    font-size: 10.5px;
    font-weight: 650;
}
.exec9-availability-wrap {
    padding: 18px 2px 8px 2px;
}
.exec9-availability-head {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    color: #334155;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 11px;
}
.exec9-availability-pct {
    color: #0f172a;
    font-size: 24px;
    line-height: 1;
    font-weight: 900;
}
.exec9-availability-track {
    width: 100%;
    height: 10px;
    background: #e2e8f0;
    border-radius: 999px;
    overflow: hidden;
}
.exec9-availability-fill {
    height: 100%;
    border-radius: 999px;
    background: #16a34a;
}
.exec9-availability-scale {
    display: flex;
    justify-content: space-between;
    color: #94a3b8;
    font-size: 9.5px;
    font-weight: 700;
    margin-top: 5px;
}
.exec9-availability-note {
    margin-top: 17px;
    padding: 9px 11px;
    border-radius: 10px;
    background: rgba(248,250,252,.88);
    border: 1px solid rgba(148,163,184,.22);
    color: #475569;
    font-size: 10.5px;
    font-weight: 700;
    line-height: 1.35;
}
.exec9-availability-empty {
    margin-top: 18px;
    padding: 14px;
    border-radius: 10px;
    background: rgba(248,250,252,.88);
    border: 1px solid rgba(148,163,184,.22);
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
}

.exec9-contract-availability-section {
    margin-top: 16px;
    padding-top: 14px;
    border-top: 1px solid rgba(148,163,184,.28);
}
.exec9-contract-availability-title {
    color: #334155;
    font-size: 11.5px;
    font-weight: 900;
    margin: 0 0 11px 0;
}
.exec9-contract-availability-row {
    margin: 0 0 11px 0;
}
.exec9-contract-availability-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 5px;
}
.exec9-contract-availability-name {
    min-width: 0;
    color: #334155;
    font-size: 10.5px;
    font-weight: 800;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.exec9-contract-availability-pct {
    flex: 0 0 auto;
    color: #0f172a;
    font-size: 11px;
    font-weight: 900;
}
.exec9-contract-availability-track {
    width: 100%;
    height: 6px;
    background: #e2e8f0;
    border-radius: 999px;
    overflow: hidden;
}
.exec9-contract-availability-fill {
    height: 100%;
    border-radius: 999px;
    background: #16a34a;
}
.exec9-contract-availability-detail {
    margin-top: 4px;
    color: #64748b;
    font-size: 9px;
    font-weight: 650;
    line-height: 1.25;
}
/* Selectores del dashboard */
div[data-testid="stMain"] div[data-testid="stSelectbox"] {
    margin-bottom: 0 !important;
}
div[data-testid="stMain"] div[data-testid="stSelectbox"] label {
    margin-bottom: 1px !important;
}
div[data-testid="stMain"] div[data-testid="stSelectbox"] label p {
    font-size: 10.5px !important;
    line-height: 1.05 !important;
    font-weight: 800 !important;
    color: #475569 !important;
}
div[data-testid="stMain"] div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    min-height: 32px !important;
    height: 32px !important;
    border-radius: 9px !important;
    font-size: 13px !important;
}
div[data-testid="stMain"] div[data-testid="stSelectbox"] [data-baseweb="select"] input {
    min-height: 30px !important;
    height: 30px !important;
}
/* Dataframes del resumen */
div[data-testid="stDataFrame"] {
    border: 1px solid rgba(148,163,184,.30) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )

    if mant_base.empty:
        st.info("No existen intervenciones registradas para construir el resumen ejecutivo.")
        return

    # -----------------------------------------------------
    # Filtros ejecutivos: período y contrato
    # El selector ofrece solamente enero-septiembre de 2026.
    # IMPORTANTE: "Todos los períodos" usa la base completa de Intervenciones
    # para que los KPI y costos coincidan exactamente con ese módulo.
    # -----------------------------------------------------
    mant_base["_Periodo_Fecha"] = mant_base["Fecha"].dt.to_period("M").dt.to_timestamp()
    mant_base["_Periodo_Clave"] = mant_base["_Periodo_Fecha"].dt.strftime("%Y-%m")

    # Lista fija visible: solo enero a septiembre de 2026.
    # Se presenta desde el mes más reciente al más antiguo.
    meses_resumen_2026 = list(range(9, 0, -1))
    opciones_periodo = ["Todos"] + [f"2026-{mes:02d}" for mes in meses_resumen_2026]
    periodo_etiquetas = {
        f"2026-{mes:02d}": f"{MESES[mes]} 2026"
        for mes in meses_resumen_2026
    }

    contratos = sorted(
        {
            str(v).strip()
            for v in mant_base["Contrato"].tolist()
            if str(v).strip().lower() not in ["", "nan", "none", "nat"]
        },
        key=lambda x: x.casefold(),
    )
    opciones_contrato = ["Todos los contratos"] + contratos

    # Filtros compactos y alineados lado a lado para reducir el espacio superior.
    f_periodo, f_contrato, _ = st.columns([0.72, 0.92, 4.36], gap="small")
    with f_periodo:
        periodo_sel = st.selectbox(
            "Período",
            opciones_periodo,
            key="dashboard_periodo_v9",
            format_func=lambda x: "Todos los períodos" if x == "Todos" else periodo_etiquetas.get(x, x),
        )
    with f_contrato:
        contrato_sel = st.selectbox(
            "Contrato",
            opciones_contrato,
            key="dashboard_contrato_v9",
        )

    dashboard = mant_base.copy()
    if periodo_sel != "Todos":
        dashboard = dashboard[dashboard["_Periodo_Clave"] == periodo_sel].copy()
    if contrato_sel != "Todos los contratos":
        dashboard = dashboard[
            dashboard["Contrato"].fillna("").astype(str).str.strip().str.casefold()
            == str(contrato_sel).strip().casefold()
        ].copy()

    dashboard = dashboard.drop(columns=["_Periodo_Fecha", "_Periodo_Clave"], errors="ignore")

    if dashboard.empty:
        st.info("No existen intervenciones para los filtros seleccionados.")
        return

    total_intervenciones = len(dashboard)
    total_servicios = float(dashboard["Total_Servicio"].sum())
    costo_promedio = total_servicios / total_intervenciones if total_intervenciones > 0 else 0.0

    # Disponibilidad actual desde la columna Estado de la hoja EQUIPOS.
    # El filtro de contrato sí se aplica; el filtro de período no, porque
    # la disponibilidad representa el estado actual de la flota.
    equipos_disponibilidad = (
        equipos_f.copy()
        if isinstance(equipos_f, pd.DataFrame)
        else pd.DataFrame()
    )
    if contrato_sel != "Todos los contratos":
        equipos_disponibilidad = filtrar_por_contrato(
            equipos_disponibilidad, contrato_sel
        )

    disponibilidad = _resumen_disponibilidad_equipos(equipos_disponibilidad)
    # El total de equipos debe salir de la hoja maestra EQUIPOS, no del historial
    # de intervenciones. Así se evita contar referencias históricas o duplicadas.
    equipos_registrados = int(disponibilidad.get("total", 0))
    disponibilidad_pct_txt = (
        f"{disponibilidad['porcentaje']:.1f}".replace(".", ",") + "%"
    )
    nota_disponibilidad = (
        f"{disponibilidad['disponibles']} disponibles · "
        f"{disponibilidad['no_disponibles']} no disponibles"
    )
    if disponibilidad["sin_estado"] > 0:
        nota_disponibilidad += f" · {disponibilidad['sin_estado']} sin estado"

    resumen_tipo = _dashboard_costos_por_intervencion(dashboard)
    tipo_mas_frecuente = resumen_tipo.sort_values("Registros", ascending=False).iloc[0]
    tipo_mayor_costo = resumen_tipo.sort_values("Costo", ascending=False).iloc[0]

    # -----------------------------------------------------
    # KPIs superiores
    # -----------------------------------------------------
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        st.markdown(
            f"""
            <div class="exec9-kpi" style="--accent:#2563eb;">
                <div class="exec9-kpi-title">INTERVENCIONES</div>
                <div class="exec9-kpi-value">{numero(total_intervenciones)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="exec9-kpi" style="--accent:#16a34a;">
                <div class="exec9-kpi-title">COSTO TOTAL DE SERVICIOS</div>
                <div class="exec9-kpi-value">{pesos(total_servicios)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="exec9-kpi" style="--accent:#f59e0b;">
                <div class="exec9-kpi-title">EQUIPOS REGISTRADOS</div>
                <div class="exec9-kpi-value">{numero(equipos_registrados)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
            <div class="exec9-kpi" style="--accent:#0ea5e9;">
                <div class="exec9-kpi-title">DISPONIBILIDAD DE EQUIPOS</div>
                <div class="exec9-kpi-value">{disponibilidad_pct_txt}</div>
                <div class="exec9-kpi-note">{escape_html(nota_disponibilidad)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="exec9-section-gap"></div>', unsafe_allow_html=True)

    # -----------------------------------------------------
    # Intervenciones por tipo + distribución del costo
    # -----------------------------------------------------
    col_barras, col_donut = st.columns([1.55, 1.0], gap="medium")

    with col_barras:
        st.markdown('<div class="exec9-panel-title exec9-panel-title-spaced">Intervenciones por tipo</div>', unsafe_allow_html=True)
        st.plotly_chart(
            _dashboard_grafico_intervenciones(dashboard),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with col_donut:
        st.markdown('<div class="exec9-panel-title exec9-panel-title-spaced">Distribución del costo</div>', unsafe_allow_html=True)
        st.plotly_chart(
            _dashboard_donut_intervenciones(dashboard),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.markdown('<div class="exec9-section-gap"></div>', unsafe_allow_html=True)

    # -----------------------------------------------------
    # Disponibilidad de equipos + costo por contrato
    # -----------------------------------------------------
    col_tipo, col_contrato = st.columns([1.0, 1.45], gap="medium")

    with col_tipo:
        st.markdown('<div class="exec9-panel-title exec9-panel-title-spaced">Disponibilidad de equipos</div>', unsafe_allow_html=True)
        _dashboard_render_disponibilidad_equipos(disponibilidad)
        _dashboard_render_disponibilidad_por_contrato(equipos_disponibilidad)

    with col_contrato:
        st.markdown('<div class="exec9-panel-title exec9-panel-title-contract">Costo de servicios por contrato</div>', unsafe_allow_html=True)
        tabla_contrato = _dashboard_tabla_costos_contrato(
            dashboard,
            equipos_disponibilidad,
        ).copy()

        # Vista ejecutiva: monto con separador de miles y participación visual.
        tabla_contrato_vista = tabla_contrato.copy()
        tabla_contrato_vista["Monto"] = tabla_contrato_vista["Monto"].apply(
            lambda v: f"${int(round(float(v))):,}".replace(",", ".")
        )

        # Altura dinámica para mostrar todos los contratos sin dejar espacio vacío innecesario.
        alto_tabla_contrato = min(460, max(205, 38 + (len(tabla_contrato_vista) * 36)))

        st.dataframe(
            tabla_contrato_vista,
            use_container_width=True,
            hide_index=True,
            height=alto_tabla_contrato,
            column_config={
                "Contrato": st.column_config.TextColumn(
                    "Contrato",
                    help="Contratos registrados en EQUIPOS y contratos con historial de intervenciones.",
                    width="medium",
                ),
                "Intervenciones": st.column_config.NumberColumn(
                    "Intervenciones",
                    format="%d",
                    help="Cantidad de intervenciones para los filtros seleccionados.",
                    width="small",
                ),
                "Monto": st.column_config.TextColumn(
                    "Monto",
                    help="Costo total de servicios del contrato.",
                    width="medium",
                ),
                "% total": st.column_config.ProgressColumn(
                    "Participación",
                    min_value=0.0,
                    max_value=100.0,
                    format="%.1f %%",
                    help="Participación del contrato sobre el costo total filtrado.",
                    width="small",
                ),
            },
        )

        # Evolución mensual compacta, ubicada inmediatamente debajo de la tabla de costos por contrato.
        st.markdown('<div class="exec9-evolution-under-table-gap"></div>', unsafe_allow_html=True)
        st.markdown('<div class="exec9-panel-title exec9-panel-title-contract">Evolución mensual de costos</div>', unsafe_allow_html=True)
        st.plotly_chart(
            _dashboard_evolucion_costos(dashboard),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    st.markdown('<div class="exec9-section-gap"></div>', unsafe_allow_html=True)

    # -----------------------------------------------------
    # Detalle disponible sin recargar visualmente el resumen
    # -----------------------------------------------------
    with st.expander("Ver últimas intervenciones"):
        historico = _dashboard_historico_intervenciones(dashboard)
        if historico.empty:
            st.info("No existen intervenciones registradas.")
        else:
            st.dataframe(
                historico.head(20),
                use_container_width=True,
                hide_index=True,
                height=370,
                column_config={
                    "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                    "Kilometraje": st.column_config.NumberColumn("Kilometraje", format="%.0f"),
                    "Total servicio": st.column_config.NumberColumn("Total servicio", format="$%.0f"),
                },
            )

@st.cache_data(ttl=CACHE_GOOGLE_SHEETS_SEGUNDOS, show_spinner=False)
def leer_hoja_google_sheet_cache(nombre_hoja):
    """Cache independiente por pestaña para evitar recargar todo el archivo en cada página."""
    return leer_hoja_google_sheet(nombre_hoja)


def cargar_datos_pagina(pagina):
    """Carga solo las pestañas necesarias para la vista actual.

    Esto reduce de 6 lecturas de Google Sheets a 1 o 2 en la carga inicial,
    manteniendo la actualización automática y el caché por pestaña.
    """
    mapa_hojas = {
        "📊 Dashboard Ejecutivo": ["EQUIPOS", "MANTENCIONES"],
        "🚚 Equipos": ["EQUIPOS"],
        "🛠️ Intervenciones": ["EQUIPOS", "MANTENCIONES"],
        "📁 Documentacion": ["DOCUMENTOS"],
    }
    hojas = mapa_hojas.get(pagina, ["EQUIPOS", "MANTENCIONES"])
    datos = {hoja: leer_hoja_google_sheet_cache(hoja) for hoja in hojas}

    if "EQUIPOS" in hojas and datos.get("EQUIPOS", pd.DataFrame()).empty:
        raise FileNotFoundError(
            "No se pudo leer la hoja EQUIPOS desde Google Sheets. "
            "Revisa que el archivo esté compartido como lector y que la pestaña se llame EQUIPOS."
        )

    return datos


def mostrar_panel():
    # Primero se construye la navegación. No requiere descargar datos.
    with st.sidebar:
        pagina = construir_menu()

    # Después se consulta únicamente la(s) pestaña(s) necesaria(s) para esa página.
    datos = cargar_datos_pagina(pagina)

    if pagina == "📊 Dashboard Ejecutivo":
        equipos = preparar_equipos(datos.get("EQUIPOS", pd.DataFrame()))
        mantenciones_planilla = preparar_mantenciones_planilla(
            datos.get("MANTENCIONES", pd.DataFrame())
        )

        encabezado("Seguimiento y Control de Equipos Móviles")
        pagina_dashboard(
            equipos,
            mantenciones_planilla,
            None,
            None,
            None,
            "Todos los equipos",
        )
        return

    if pagina == "🚚 Equipos":
        equipos = preparar_equipos(datos.get("EQUIPOS", pd.DataFrame()))
        encabezado("Equipos")
        pagina_equipos(equipos)
        return

    if pagina == "🛠️ Intervenciones":
        equipos = preparar_equipos(datos.get("EQUIPOS", pd.DataFrame()))
        mantenciones_planilla = preparar_mantenciones_planilla(
            datos.get("MANTENCIONES", pd.DataFrame())
        )
        encabezado("Intervenciones")
        pagina_mantenciones(mantenciones_planilla, equipos)
        return

    if pagina == "📁 Documentacion":
        documentos = preparar_documentos(datos.get("DOCUMENTOS", pd.DataFrame()))
        encabezado("Documentacion")
        pagina_documentos(documentos)
        return


# =========================================================
# AJUSTE FINAL V5.1: VISTA COMPLETA AL 100% DEL NAVEGADOR
# - Menú más angosto.
# - Contenido principal sin ancho mínimo forzado.
# - Evita que el título, KPIs, tablas y gráficos queden cortados.
# =========================================================
st.markdown(
    """
<style>
:root {
    --menu-panel-width: 280px !important;
    --menu-inner-width: 248px !important;
    --menu-panel-width-final: 280px !important;
    --menu-inner-width-final: 248px !important;
    --content-padding-x: 18px !important;
}

/* Menú izquierdo más compacto */
section[data-testid="stSidebar"] {
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    overflow-x: hidden !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    padding: 8px 10px 12px 10px !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-brand,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-width) !important;
    min-width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    box-sizing: border-box !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] .menu-active-item {
    width: var(--menu-inner-width) !important;
    min-width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    min-height: 42px !important;
    height: 42px !important;
    padding: 8px 10px !important;
    font-size: 13.2px !important;
    line-height: 1.05 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

section[data-testid="stSidebar"] .menu-title {
    font-size: 12.2px !important;
    line-height: 1.1 !important;
}

section[data-testid="stSidebar"] .menu-subtitle {
    font-size: 10.4px !important;
    line-height: 1.1 !important;
}

section[data-testid="stSidebar"] .menu-icon-img {
    width: 42px !important;
    height: 42px !important;
    min-width: 42px !important;
    max-width: 42px !important;
}

/* Contenido principal: parte justo después del menú y usa todo el ancho disponible */
[data-testid="stAppViewContainer"] > .main,
div[data-testid="stMain"],
section.main,
main {
    margin-left: var(--menu-panel-width) !important;
    width: calc(100vw - var(--menu-panel-width)) !important;
    max-width: calc(100vw - var(--menu-panel-width)) !important;
    min-width: 0 !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
}

.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"] {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    padding-left: var(--content-padding-x) !important;
    padding-right: var(--content-padding-x) !important;
    padding-top: 0px !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
}

/* Elimina anchos mínimos antiguos que provocaban corte horizontal */
[data-testid="stHorizontalBlock"],
[data-testid="stVerticalBlock"],
[data-testid="stElementContainer"],
[data-testid="column"] {
    min-width: 0 !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

[data-testid="stHorizontalBlock"] {
    gap: 0.75rem !important;
}

/* Título y logo ajustados para no salirse al 100% */
.title-main {
    font-size: clamp(28px, 2.15vw, 38px) !important;
    line-height: 1.05 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    max-width: 100% !important;
    margin-left: 0 !important;
}

.header-logo-box img {
    width: 132px !important;
    max-width: 132px !important;
}

/* Tarjetas KPI más compactas */
.kpi-card {
    min-width: 0 !important;
    width: 100% !important;
    padding: 16px !important;
    min-height: 118px !important;
}

.kpi-icon {
    width: 46px !important;
    height: 46px !important;
    border-radius: 15px !important;
    font-size: 22px !important;
    margin-bottom: 9px !important;
}

.kpi-title {
    font-size: 12px !important;
}

.kpi-value {
    font-size: clamp(20px, 1.55vw, 25px) !important;
    line-height: 1.05 !important;
}

.kpi-sub {
    font-size: 11px !important;
    line-height: 1.25 !important;
}

/* Tablas y gráficos contenidos dentro de la pantalla */
[data-testid="stDataFrame"],
[data-testid="stTable"],
[data-testid="stPlotlyChart"],
.js-plotly-plot,
.plot-container,
.svg-container {
    width: 100% !important;
    max-width: 100% !important;
    min-width: 0 !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
}

</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL DASHBOARD EJECUTIVO 100%
# =========================================================
st.markdown(
    """
<style>
/* Mantiene visible el Dashboard Ejecutivo a zoom 100% */
:root {
    --menu-panel-width: 250px !important;
    --menu-inner-width: 218px !important;
    --content-padding-x: 14px !important;
}
section[data-testid="stSidebar"] {
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
}
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    padding: 10px 10px 14px 10px !important;
}
section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-brand,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .menu-active-item,
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: var(--menu-inner-width) !important;
    min-width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
}
[data-testid="stAppViewContainer"] > .main,
section.main,
main {
    margin-left: var(--menu-panel-width) !important;
    width: calc(100vw - var(--menu-panel-width)) !important;
    max-width: calc(100vw - var(--menu-panel-width)) !important;
}
.main .block-container,
.block-container {
    padding-top: 0.15rem !important;
    padding-left: var(--content-padding-x) !important;
    padding-right: var(--content-padding-x) !important;
    padding-bottom: 1rem !important;
    max-width: none !important;
    min-width: 0 !important;
}
.main-fixed-header {
    min-height: 58px !important;
    margin-bottom: 8px !important;
}
.main-fixed-title,
.title-main {
    font-size: clamp(28px, 2.2vw, 38px) !important;
    line-height: 1.05 !important;
    white-space: normal !important;
}
.main-fixed-logo img,
.header-logo-box img {
    width: 125px !important;
    max-width: 125px !important;
}
.main-fixed-header-spacer,
.header-separador {
    height: 6px !important;
    min-height: 6px !important;
}
.kpi-card {
    min-height: 104px !important;
    padding: 12px 14px !important;
    border-radius: 16px !important;
}
.kpi-icon {
    width: 40px !important;
    height: 40px !important;
    font-size: 20px !important;
    margin-bottom: 7px !important;
}
.kpi-title { font-size: 11.2px !important; }
.kpi-value { font-size: clamp(19px, 1.35vw, 24px) !important; }
.kpi-sub { font-size: 10.5px !important; line-height: 1.2 !important; }
.panel-title {
    font-size: 17px !important;
    margin-top: 12px !important;
    margin-bottom: 7px !important;
}
[data-testid="stHorizontalBlock"] {
    gap: 0.65rem !important;
    align-items: stretch !important;
}
.next-item {
    min-height: 34px !important;
    padding: 4px 0 !important;
}
.next-title { font-size: 11px !important; }
.next-sub { font-size: 9.6px !important; }
.badge-days { font-size: 9px !important; padding: 4px 6px !important; }
.equipo-card {
    padding: 10px !important;
    border-radius: 16px !important;
}
.equipo-img {
    height: 88px !important;
    min-height: 88px !important;
}
.equipo-nombre { font-size: 15px !important; }
.equipo-sub { font-size: 11px !important; }
/* Refuerzo de montos con $ a la derecha en tablas HTML */
td, th { white-space: normal !important; }
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V5.7: SUBIR TODAS LAS PÁGINAS PRINCIPALES
# - Elimina espacio superior vacío en Dashboard, Mantenciones, Costos, Alertas, etc.
# - Mantiene título y logo más arriba para aprovechar pantalla al 100%.
# =========================================================
st.markdown(
    """
<style>
/* Quita márgenes/paddings superiores acumulados de Streamlit */
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
div[data-testid="stMain"],
section.main,
main {
    padding-top: 0px !important;
    margin-top: 0px !important;
}

.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"],
section.main > div {
    padding-top: 0px !important;
    margin-top: -92px !important;
    padding-bottom: 0.8rem !important;
}

/* Encabezado común de todas las páginas */
.main-fixed-header {
    position: relative !important;
    top: auto !important;
    min-height: 42px !important;
    height: 42px !important;
    padding: 0px 10px 0px 0px !important;
    margin-top: 0px !important;
    margin-bottom: 2px !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    display: flex !important;
    align-items: flex-end !important;
    justify-content: space-between !important;
}

.main-fixed-title,
.title-main {
    font-size: clamp(27px, 2.05vw, 36px) !important;
    line-height: 0.98 !important;
    margin: 0px !important;
    padding: 0px !important;
    white-space: normal !important;
}

.main-fixed-logo,
.header-logo-box {
    margin: 0px !important;
    padding: 0px !important;
    align-self: flex-end !important;
}

.main-fixed-logo img,
.header-logo-box img {
    width: 112px !important;
    max-width: 112px !important;
    height: auto !important;
    margin: 0px !important;
    padding: 0px !important;
}

.main-fixed-header-spacer,
.header-separador {
    height: 0px !important;
    min-height: 0px !important;
    max-height: 0px !important;
    margin: 0px !important;
    padding: 0px !important;
}

/* Reduce espacios verticales generales entre bloques */
div[data-testid="stVerticalBlock"] {
    gap: 0.32rem !important;
}

.panel-title {
    margin-top: 8px !important;
    margin-bottom: 5px !important;
}

/* Dashboard: acerca KPI al título */
.kpi-card {
    margin-top: 0px !important;
}

/* En pantallas más bajas, sube un poco más */
@media (max-height: 850px) {
    .main .block-container,
    .block-container,
    div[data-testid="stMainBlockContainer"],
    section.main > div {
        margin-top: -112px !important;
    }

    .main-fixed-header {
        min-height: 38px !important;
        height: 38px !important;
    }

    .main-fixed-title,
    .title-main {
        font-size: clamp(25px, 1.95vw, 34px) !important;
    }

    .main-fixed-logo img,
    .header-logo-box img {
        width: 104px !important;
        max-width: 104px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V5.8: ESPACIO SUPERIOR Y DASHBOARD MÁS EQUILIBRADO
# - Baja levemente los títulos para que no queden pegados al borde superior.
# - Deja un pequeño espacio entre título/logo y contenido.
# - Compacta la zona Gastos Adicionales / Próximas Mantenciones.
# =========================================================
st.markdown(
    """
<style>
/* Baja levemente todas las páginas, sin volver a dejar el espacio superior excesivo */
.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"],
section.main > div {
    margin-top: -72px !important;
    padding-top: 0px !important;
    padding-bottom: 0.65rem !important;
}

.main-fixed-header {
    min-height: 50px !important;
    height: 50px !important;
    margin-top: 0px !important;
    margin-bottom: 9px !important;
    padding-top: 4px !important;
    padding-right: 10px !important;
    align-items: flex-end !important;
}

.main-fixed-title,
.title-main {
    line-height: 1.03 !important;
    margin: 0px !important;
    padding: 0px !important;
}

.main-fixed-logo,
.header-logo-box {
    align-self: flex-end !important;
    margin-bottom: 2px !important;
}

.main-fixed-logo img,
.header-logo-box img {
    width: 116px !important;
    max-width: 116px !important;
}

.main-fixed-header-spacer,
.header-separador {
    height: 4px !important;
    min-height: 4px !important;
    max-height: 4px !important;
}

/* Menos aire entre secciones del Dashboard */
div[data-testid="stVerticalBlock"] {
    gap: 0.24rem !important;
}

.panel-title {
    margin-top: 5px !important;
    margin-bottom: 4px !important;
}

/* Tablas más compactas para que Gastos Adicionales se vea completo */
.tabla-clara-wrap {
    overflow-x: hidden !important;
    overflow-y: auto !important;
}

.tabla-clara {
    font-size: 10.8px !important;
    table-layout: fixed !important;
    width: 100% !important;
}

.tabla-clara thead th,
.tabla-clara tbody td {
    padding: 5px 7px !important;
    line-height: 1.16 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}

/* Montos siempre en una línea */
.tabla-clara td.monto,
.tabla-clara th.monto,
.tabla-clara td:last-child,
.tabla-clara th:last-child {
    white-space: nowrap !important;
    overflow-wrap: normal !important;
    word-break: normal !important;
    text-align: right !important;
}

/* Próximas Mantenciones más compactas verticalmente, pero legibles */
.proximas-box .panel-title {
    margin-top: 0px !important;
}

.next-item {
    min-height: 28px !important;
    padding: 2px 0 !important;
}

.next-title {
    font-size: 10.8px !important;
    line-height: 1.05 !important;
}

.next-sub {
    font-size: 9px !important;
    line-height: 1.05 !important;
    margin-top: 0px !important;
}

.badge-days {
    font-size: 8.7px !important;
    padding: 3px 6px !important;
    min-width: 72px !important;
    text-align: center !important;
}

/* En pantallas bajas se conserva el aprovechamiento, pero sin cortar el título */
@media (max-height: 850px) {
    .main .block-container,
    .block-container,
    div[data-testid="stMainBlockContainer"],
    section.main > div {
        margin-top: -82px !important;
    }

    .main-fixed-header {
        min-height: 46px !important;
        height: 46px !important;
        margin-bottom: 7px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# OVERRIDE VISUAL FINAL V5.9
# =========================================================
st.markdown(
    """
<style>
:root {
    --menu-panel-width: 345px !important;
    --menu-inner-width: 304px !important;
    --menu-panel-width-final: 345px !important;
    --menu-inner-width-final: 304px !important;
}
section[data-testid="stSidebar"] {
    width: 345px !important;
    min-width: 345px !important;
    max-width: 345px !important;
}
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: 345px !important;
    min-width: 345px !important;
    max-width: 345px !important;
}
section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .menu-brand,
section[data-testid="stSidebar"] .menu-active-item {
    width: 304px !important;
    max-width: 304px !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: 304px !important;
    min-height: 52px !important;
    font-size: 15px !important;
}
[data-testid="stAppViewContainer"] > .main,
section.main,
main {
    margin-left: 345px !important;
    width: calc(100vw - 345px) !important;
    max-width: calc(100vw - 345px) !important;
}
[data-testid="collapsedControl"],
button[title="Collapse sidebar"],
button[title="Close sidebar"],
button[aria-label="Collapse sidebar"],
button[aria-label="Close sidebar"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    height: 34px !important;
    min-height: 34px !important;
    width: 34px !important;
    min-width: 34px !important;
    z-index: 10050 !important;
}
.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"],
section.main > div {
    margin-top: -62px !important;
    padding-top: 0px !important;
}
.main-fixed-header {
    min-height: 58px !important;
    height: 58px !important;
    margin-top: 0px !important;
    margin-bottom: 12px !important;
    padding-top: 8px !important;
    align-items: flex-end !important;
}
.main-fixed-title,
.title-main {
    font-size: clamp(28px, 2.1vw, 37px) !important;
    line-height: 1.03 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.main-fixed-logo img,
.header-logo-box img {
    width: 116px !important;
    max-width: 116px !important;
}
.main-fixed-header-spacer,
.header-separador {
    height: 8px !important;
    min-height: 8px !important;
}
.panel-title {
    margin-top: 7px !important;
    margin-bottom: 5px !important;
}
[data-testid="stPlotlyChart"] {
    overflow: hidden !important;
    border-radius: 12px !important;
}
.dashboard-proximas .next-item,
.proximas-box .next-item {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) auto !important;
    align-items: center !important;
    column-gap: 8px !important;
    min-height: 34px !important;
    padding: 2px 0 !important;
}
.dashboard-proximas .next-title,
.proximas-box .next-title {
    font-size: 11.8px !important;
    line-height: 1.02 !important;
    margin-bottom: 1px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.dashboard-proximas .next-sub-line,
.proximas-box .next-sub-line,
.dashboard-proximas .next-sub,
.proximas-box .next-sub {
    display: block !important;
    font-size: 9.2px !important;
    line-height: 1.05 !important;
    margin: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.dashboard-proximas .badge-days,
.proximas-box .badge-days {
    min-width: 76px !important;
    max-width: 86px !important;
    font-size: 8.7px !important;
    padding: 4px 6px !important;
    white-space: nowrap !important;
    text-align: center !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# AJUSTE FINAL SOLICITADO V6.0
# 1) Menú izquierdo 20% más angosto y botón nativo claro para ocultar/mostrar.
# 2) Títulos de distribución dentro de fondo blanco del gráfico.
# 3) Próximas mantenciones ordenadas, con tipografía uniforme y mejor espaciado.
# 4) Gráfico de torta de Historial de Mantenciones encuadrado completo.
# =========================================================
st.markdown(
    """
<style>
:root {
    --menu-panel-width: 276px !important;
    --menu-inner-width: 244px !important;
    --menu-panel-width-final: 276px !important;
    --menu-inner-width-final: 244px !important;
    --content-padding-x: 16px !important;
}

/* 1. Menú izquierdo 20% más angosto */
section[data-testid="stSidebar"] {
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    transition: width .22s ease, min-width .22s ease, max-width .22s ease !important;
}
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
    padding: 10px 12px 14px 12px !important;
    box-sizing: border-box !important;
}
section[data-testid="stSidebar"] .menu-panel-content,
section[data-testid="stSidebar"] .menu-brand,
section[data-testid="stSidebar"] .menu-line,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] div[data-testid="stButton"],
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-baseweb="select"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] .menu-active-item,
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    width: var(--menu-inner-width) !important;
    min-width: var(--menu-inner-width) !important;
    max-width: var(--menu-inner-width) !important;
    box-sizing: border-box !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] .menu-active-item {
    min-height: 48px !important;
    height: 48px !important;
    font-size: 14px !important;
    padding: 9px 11px !important;
    border-radius: 14px !important;
}
[data-testid="stAppViewContainer"] > .main,
div[data-testid="stMain"],
section.main,
main {
    margin-left: var(--menu-panel-width) !important;
    width: calc(100vw - var(--menu-panel-width)) !important;
    max-width: calc(100vw - var(--menu-panel-width)) !important;
}
.main .block-container,
.block-container,
div[data-testid="stMainBlockContainer"] {
    padding-left: var(--content-padding-x) !important;
    padding-right: var(--content-padding-x) !important;
    max-width: 100% !important;
    min-width: 0 !important;
}

/* Botón claro para minimizar/agrandar menú */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[title="Collapse sidebar"],
button[title="Close sidebar"],
button[title="Open sidebar"],
button[aria-label="Collapse sidebar"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    position: fixed !important;
    top: 14px !important;
    left: calc(var(--menu-panel-width) - 17px) !important;
    width: 38px !important;
    height: 38px !important;
    min-width: 38px !important;
    min-height: 38px !important;
    border-radius: 999px !important;
    background: #2563eb !important;
    border: 2px solid #ffffff !important;
    color: #ffffff !important;
    box-shadow: 0 8px 20px rgba(15,23,42,.35) !important;
    z-index: 100000 !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg,
button[title="Collapse sidebar"] svg,
button[title="Close sidebar"] svg,
button[title="Open sidebar"] svg,
button[aria-label="Collapse sidebar"] svg,
button[aria-label="Close sidebar"] svg,
button[aria-label="Open sidebar"] svg {
    color: #ffffff !important;
    fill: #ffffff !important;
    stroke: #ffffff !important;
}

/* 2. Títulos de distribución dentro de tarjeta blanca */
.chart-title,
.panel-title.chart-title {
    display: block !important;
    width: 100% !important;
    background: rgba(255,255,255,.82) !important;
    border: 1px solid rgba(203,213,225,.75) !important;
    border-bottom: 0 !important;
    border-radius: 18px 18px 0 0 !important;
    padding: 10px 14px 7px 14px !important;
    margin: 8px 0 -1px 0 !important;
    box-sizing: border-box !important;
}
.chart-title + div[data-testid="stPlotlyChart"],
.panel-title.chart-title + div[data-testid="stPlotlyChart"] {
    background: rgba(255,255,255,.82) !important;
    border: 1px solid rgba(203,213,225,.75) !important;
    border-top: 0 !important;
    border-radius: 0 0 18px 18px !important;
    padding: 4px 8px 8px 8px !important;
    box-sizing: border-box !important;
}

/* 3. Próximas Mantenciones más ordenadas */
.dashboard-proximas,
.proximas-box {
    padding: 8px 10px !important;
    border-radius: 16px !important;
}
.dashboard-proximas .next-item,
.proximas-box .next-item {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 92px !important;
    align-items: center !important;
    column-gap: 10px !important;
    min-height: 44px !important;
    padding: 6px 0 !important;
    border-bottom: 1px solid rgba(148,163,184,.28) !important;
}
.dashboard-proximas .next-item:last-child,
.proximas-box .next-item:last-child {
    border-bottom: 0 !important;
}
.dashboard-proximas .next-title,
.proximas-box .next-title {
    font-size: 12.8px !important;
    line-height: 1.15 !important;
    font-weight: 950 !important;
    margin: 0 0 2px 0 !important;
    color: #0f172a !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
}
.dashboard-proximas .next-sub-line,
.proximas-box .next-sub-line,
.dashboard-proximas .next-sub,
.proximas-box .next-sub {
    font-size: 12.3px !important;
    line-height: 1.18 !important;
    font-weight: 700 !important;
    margin: 0 !important;
    color: #0f172a !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
}
.dashboard-proximas .badge-days,
.proximas-box .badge-days {
    width: 92px !important;
    min-width: 92px !important;
    max-width: 92px !important;
    font-size: 10.2px !important;
    line-height: 1.1 !important;
    font-weight: 950 !important;
    padding: 7px 6px !important;
    white-space: normal !important;
    text-align: center !important;
    border-radius: 999px !important;
}

/* 4. Historial de Mantenciones: torta completa dentro de pantalla */
div[data-testid="stPlotlyChart"] {
    max-width: 100% !important;
    overflow: hidden !important;
}
.js-plotly-plot,
.plot-container,
.svg-container {
    max-width: 100% !important;
    overflow: visible !important;
}

/* Ajuste responsivo */
@media (max-width: 1400px) {
    :root {
        --menu-panel-width: 260px !important;
        --menu-inner-width: 228px !important;
        --content-padding-x: 12px !important;
    }
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    button[title="Collapse sidebar"],
    button[title="Close sidebar"],
    button[title="Open sidebar"],
    button[aria-label="Collapse sidebar"],
    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"] {
        left: calc(var(--menu-panel-width) - 17px) !important;
    }
    .dashboard-proximas .next-item,
    .proximas-box .next-item {
        grid-template-columns: minmax(0, 1fr) 82px !important;
    }
    .dashboard-proximas .badge-days,
    .proximas-box .badge-days {
        width: 82px !important;
        min-width: 82px !important;
        max-width: 82px !important;
        font-size: 9.5px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)



# Refuerzo final posterior a los estilos acumulados.
aplicar_ajustes_finales_ui()

# =========================================================
# AJUSTE FINAL V6.2
# - Botón menú solo con ícono.
# - Separación segura de títulos/subtítulos para que no queden debajo de tablas, KPIs o tarjetas.
# =========================================================
st.markdown(
    """
<style>
section[data-testid="stSidebar"] .menu-toggle-wrap,
section[data-testid="stSidebar"] .menu-toggle-wrap div[data-testid="stButton"],
section[data-testid="stSidebar"] .menu-toggle-wrap div[data-testid="stButton"] button {
    width: 48px !important;
    min-width: 48px !important;
    max-width: 48px !important;
}
section[data-testid="stSidebar"] .menu-toggle-wrap div[data-testid="stButton"] button {
    height: 42px !important;
    min-height: 42px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    font-size: 21px !important;
    line-height: 1 !important;
}
.panel-title {
    display: block !important;
    clear: both !important;
    position: relative !important;
    z-index: 20 !important;
    color: #0f172a !important;
    font-weight: 950 !important;
    font-size: clamp(18px, 1.15vw, 22px) !important;
    line-height: 1.22 !important;
    min-height: 30px !important;
    margin-top: 16px !important;
    margin-bottom: 12px !important;
    padding: 2px 0 7px 0 !important;
    overflow: visible !important;
}
.section-head {
    display: block !important;
    clear: both !important;
    position: relative !important;
    z-index: 21 !important;
    width: 100% !important;
    margin: 2px 0 16px 0 !important;
    padding: 0 0 2px 0 !important;
    overflow: visible !important;
}
.section-head .panel-title,
.page-section-title {
    margin-top: 0 !important;
    margin-bottom: 5px !important;
    padding: 0 !important;
    min-height: 28px !important;
}
.panel-subtitle {
    display: block !important;
    clear: both !important;
    color: #334155 !important;
    font-size: 15px !important;
    line-height: 1.25 !important;
    font-weight: 850 !important;
    margin: 0 0 10px 0 !important;
    padding: 0 !important;
    position: relative !important;
    z-index: 21 !important;
}
.tabla-clara-wrap {
    margin-top: 10px !important;
}
.equipo-card,
.kpi-card,
.tabla-clara-wrap,
[data-testid="stPlotlyChart"] {
    position: relative !important;
    z-index: 2 !important;
}
.dashboard-proximas .panel-title,
.proximas-box .panel-title,
.chart-title,
.panel-title.chart-title {
    margin-top: 0 !important;
    margin-bottom: 8px !important;
    min-height: 24px !important;
    padding-bottom: 4px !important;
}
[data-testid="stElementContainer"]:has(.section-head),
[data-testid="stElementContainer"]:has(.panel-title) {
    overflow: visible !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# AJUSTE FINAL V6.3
# - Próximas Mantenciones dashboard con formato uniforme por equipo.
# - Íconos centrados cuando el menú está minimizado.
# =========================================================
st.markdown(
    """
<style>
/* ===== Próximas Mantenciones: formato uniforme y con separación real ===== */
.dashboard-proximas,
.proximas-box {
    padding: 12px 14px !important;
    border-radius: 17px !important;
    background: rgba(255,255,255,.74) !important;
}

.dashboard-proximas .panel-title,
.proximas-box .panel-title {
    margin: 0 0 9px 0 !important;
    padding: 0 0 6px 0 !important;
    min-height: 26px !important;
    line-height: 1.18 !important;
}

.dashboard-proximas .next-item,
.proximas-box .next-item,
.dashboard-proximas .next-row-pro,
.proximas-box .next-row-pro {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 102px !important;
    align-items: center !important;
    column-gap: 12px !important;
    min-height: 62px !important;
    padding: 8px 0 !important;
    margin: 0 !important;
    border-bottom: 1px solid rgba(100,116,139,.24) !important;
    box-sizing: border-box !important;
}

.dashboard-proximas .next-item:last-child,
.proximas-box .next-item:last-child {
    border-bottom: 0 !important;
}

.dashboard-proximas .next-info,
.proximas-box .next-info {
    min-width: 0 !important;
    width: 100% !important;
}

.dashboard-proximas .next-header-row,
.proximas-box .next-header-row {
    display: grid !important;
    grid-template-columns: minmax(120px, 0.95fr) minmax(120px, 1.05fr) !important;
    gap: 8px !important;
    align-items: end !important;
    margin-bottom: 5px !important;
}

.dashboard-proximas .next-title,
.proximas-box .next-title {
    font-size: 13.4px !important;
    line-height: 1.12 !important;
    font-weight: 950 !important;
    color: #0f172a !important;
    margin: 0 !important;
    padding: 0 !important;
    white-space: normal !important;
}

.dashboard-proximas .next-frequency,
.proximas-box .next-frequency {
    font-size: 10.7px !important;
    line-height: 1.1 !important;
    font-weight: 850 !important;
    color: #475569 !important;
    margin: 0 !important;
    padding: 0 !important;
    text-align: left !important;
}

.dashboard-proximas .next-values-grid,
.proximas-box .next-values-grid {
    display: grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 6px !important;
}

.dashboard-proximas .next-value-box,
.proximas-box .next-value-box {
    display: grid !important;
    grid-template-columns: 48px minmax(0, 1fr) !important;
    align-items: center !important;
    gap: 4px !important;
    background: rgba(248,250,252,.62) !important;
    border: 1px solid rgba(148,163,184,.26) !important;
    border-radius: 9px !important;
    padding: 3px 6px !important;
    min-height: 25px !important;
    box-sizing: border-box !important;
}

.dashboard-proximas .next-label,
.proximas-box .next-label {
    color: #475569 !important;
    font-size: 10.1px !important;
    line-height: 1 !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: .15px !important;
}

.dashboard-proximas .next-value,
.proximas-box .next-value {
    color: #0f172a !important;
    font-size: 11.5px !important;
    line-height: 1.08 !important;
    font-weight: 850 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}

.dashboard-proximas .badge-days,
.proximas-box .badge-days {
    width: 102px !important;
    min-width: 102px !important;
    max-width: 102px !important;
    min-height: 28px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    font-size: 10.2px !important;
    line-height: 1.12 !important;
    font-weight: 950 !important;
    padding: 6px 7px !important;
    border-radius: 999px !important;
    white-space: normal !important;
    box-sizing: border-box !important;
}

/* ===== Menú minimizado: botones e íconos centrados ===== */
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] {
    text-align: center !important;
}

body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-panel-content,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-brand,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-line,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] div[data-testid="stButton"],
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-active-item,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-toggle-wrap {
    margin-left: auto !important;
    margin-right: auto !important;
}

body:has(.menu-state-collapsed) section[data-testid="stSidebar"] div[data-testid="stButton"],
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-active-item {
    width: 58px !important;
    min-width: 58px !important;
    max-width: 58px !important;
}

body:has(.menu-state-collapsed) section[data-testid="stSidebar"] div[data-testid="stButton"] button,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-active-item {
    width: 58px !important;
    min-width: 58px !important;
    max-width: 58px !important;
    height: 58px !important;
    min-height: 58px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    font-size: 21px !important;
    line-height: 1 !important;
}

body:has(.menu-state-collapsed) section[data-testid="stSidebar"] div[data-testid="stButton"] button > div,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] div[data-testid="stButton"] button p,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] div[data-testid="stButton"] button span,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-active-item > div,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-active-item p,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-active-item span {
    width: 100% !important;
    margin: 0 auto !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}

body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-toggle-wrap,
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-toggle-wrap div[data-testid="stButton"],
body:has(.menu-state-collapsed) section[data-testid="stSidebar"] .menu-toggle-wrap div[data-testid="stButton"] button {
    width: 58px !important;
    min-width: 58px !important;
    max-width: 58px !important;
    height: 48px !important;
    min-height: 48px !important;
}

@media (max-width: 1500px) {
    .dashboard-proximas .next-item,
    .proximas-box .next-item,
    .dashboard-proximas .next-row-pro,
    .proximas-box .next-row-pro {
        grid-template-columns: minmax(0, 1fr) 94px !important;
        column-gap: 9px !important;
        min-height: 60px !important;
    }
    .dashboard-proximas .next-header-row,
    .proximas-box .next-header-row {
        grid-template-columns: 1fr !important;
        gap: 2px !important;
        margin-bottom: 4px !important;
    }
    .dashboard-proximas .next-values-grid,
    .proximas-box .next-values-grid {
        grid-template-columns: 1fr !important;
        gap: 4px !important;
    }
    .dashboard-proximas .badge-days,
    .proximas-box .badge-days {
        width: 94px !important;
        min-width: 94px !important;
        max-width: 94px !important;
        font-size: 9.7px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V6.5
# - Baja el cuadro Distribución de Costos en Dashboard Ejecutivo.
# - Próximas Mantenciones en una fila uniforme por equipo.
# =========================================================
st.markdown(
    """
<style>
/* Baja el bloque Distribución de Costos para que no se monte sobre los KPI */
.dashboard-costos-spacer {
    height: 18px !important;
    display: block !important;
}
.dashboard-costos-title,
.panel-title.chart-title.dashboard-costos-title {
    margin-top: 4px !important;
    margin-bottom: 12px !important;
    line-height: 1.18 !important;
    position: relative !important;
    z-index: 30 !important;
}

/* Contenedor de Próximas Mantenciones del Dashboard */
.dashboard-proximas,
.proximas-box {
    padding: 14px 16px !important;
    border-radius: 18px !important;
    background: rgba(255,255,255,.70) !important;
    overflow: visible !important;
}
.dashboard-proximas .panel-title,
.proximas-box .panel-title {
    margin: 0 0 10px 0 !important;
    padding: 0 0 6px 0 !important;
    min-height: 28px !important;
    line-height: 1.18 !important;
    clear: both !important;
}

/* Fila por equipo: equipo | actual | próxima | saldo */
.dashboard-proximas .next-row-v65,
.proximas-box .next-row-v65,
.dashboard-proximas .next-item.next-row-v65,
.proximas-box .next-item.next-row-v65 {
    display: grid !important;
    grid-template-columns: minmax(118px, .95fr) minmax(120px, 1fr) minmax(128px, 1fr) 104px !important;
    align-items: center !important;
    column-gap: 8px !important;
    min-height: 48px !important;
    padding: 7px 0 !important;
    margin: 0 !important;
    border-bottom: 1px solid rgba(100,116,139,.22) !important;
    box-sizing: border-box !important;
}
.dashboard-proximas .next-row-v65:last-child,
.proximas-box .next-row-v65:last-child {
    border-bottom: 0 !important;
}
.dashboard-proximas .next-equipo-block,
.proximas-box .next-equipo-block {
    min-width: 0 !important;
    overflow: hidden !important;
}
.dashboard-proximas .next-row-v65 .next-title,
.proximas-box .next-row-v65 .next-title {
    font-size: 12.9px !important;
    line-height: 1.08 !important;
    font-weight: 950 !important;
    color: #0f172a !important;
    margin: 0 0 3px 0 !important;
    padding: 0 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
.dashboard-proximas .next-row-v65 .next-frequency,
.proximas-box .next-row-v65 .next-frequency {
    font-size: 10.2px !important;
    line-height: 1.05 !important;
    font-weight: 800 !important;
    color: #475569 !important;
    margin: 0 !important;
    padding: 0 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
.dashboard-proximas .next-metric-box,
.proximas-box .next-metric-box {
    display: grid !important;
    grid-template-columns: 42px minmax(0, 1fr) !important;
    align-items: center !important;
    gap: 4px !important;
    background: rgba(248,250,252,.72) !important;
    border: 1px solid rgba(148,163,184,.24) !important;
    border-radius: 9px !important;
    padding: 4px 6px !important;
    min-height: 30px !important;
    box-sizing: border-box !important;
}
.dashboard-proximas .next-row-v65 .next-label,
.proximas-box .next-row-v65 .next-label {
    color: #475569 !important;
    font-size: 9.7px !important;
    line-height: 1 !important;
    font-weight: 950 !important;
    text-transform: uppercase !important;
    letter-spacing: .10px !important;
}
.dashboard-proximas .next-row-v65 .next-value,
.proximas-box .next-row-v65 .next-value {
    color: #0f172a !important;
    font-size: 11.2px !important;
    line-height: 1.05 !important;
    font-weight: 900 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
.dashboard-proximas .next-row-v65 .badge-days,
.proximas-box .next-row-v65 .badge-days {
    width: 104px !important;
    min-width: 104px !important;
    max-width: 104px !important;
    min-height: 30px !important;
    padding: 5px 7px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    font-size: 10.2px !important;
    line-height: 1.08 !important;
    font-weight: 950 !important;
    border-radius: 999px !important;
    white-space: normal !important;
    box-sizing: border-box !important;
}

@media (max-width: 1500px) {
    .dashboard-proximas .next-row-v65,
    .proximas-box .next-row-v65,
    .dashboard-proximas .next-item.next-row-v65,
    .proximas-box .next-item.next-row-v65 {
        grid-template-columns: minmax(105px, .9fr) minmax(96px, 1fr) minmax(102px, 1fr) 92px !important;
        column-gap: 6px !important;
        min-height: 48px !important;
        padding: 7px 0 !important;
    }
    .dashboard-proximas .next-metric-box,
    .proximas-box .next-metric-box {
        grid-template-columns: 36px minmax(0, 1fr) !important;
        padding: 4px 5px !important;
    }
    .dashboard-proximas .next-row-v65 .next-value,
    .proximas-box .next-row-v65 .next-value {
        font-size: 10.4px !important;
    }
    .dashboard-proximas .next-row-v65 .badge-days,
    .proximas-box .next-row-v65 .badge-days {
        width: 92px !important;
        min-width: 92px !important;
        max-width: 92px !important;
        font-size: 9.3px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V6.6
# - Distribución de Costos más abajo respecto a los KPI.
# - Próximas Mantenciones: una fila limpia por equipo con Actual, Próxima y Faltan.
# =========================================================
st.markdown(
    """
<style>
/* Más separación entre KPI superiores y Distribución de Costos */
.dashboard-costos-spacer {
    height: 42px !important;
    min-height: 42px !important;
    display: block !important;
}
.dashboard-costos-title,
.panel-title.chart-title.dashboard-costos-title {
    margin-top: 12px !important;
    margin-bottom: 12px !important;
    padding-top: 0 !important;
    line-height: 1.20 !important;
}

/* Próximas Mantenciones Dashboard: fila final ordenada */
.dashboard-proximas,
.proximas-box {
    padding: 12px 14px !important;
    overflow: visible !important;
}
.dashboard-proximas .panel-title,
.proximas-box .panel-title {
    margin: 0 0 12px 0 !important;
    padding: 0 0 6px 0 !important;
    min-height: 28px !important;
}
.dashboard-proximas .next-row-v66,
.proximas-box .next-row-v66,
.dashboard-proximas .next-item.next-row-v66,
.proximas-box .next-item.next-row-v66 {
    display: grid !important;
    grid-template-columns: minmax(110px, 0.72fr) minmax(145px, 1fr) 108px !important;
    align-items: center !important;
    column-gap: 10px !important;
    min-height: 54px !important;
    padding: 8px 0 !important;
    margin: 0 !important;
    border-bottom: 1px solid rgba(100,116,139,.24) !important;
    box-sizing: border-box !important;
}
.dashboard-proximas .next-row-v66:last-child,
.proximas-box .next-row-v66:last-child {
    border-bottom: 0 !important;
}
.dashboard-proximas .next-equipo-v66,
.proximas-box .next-equipo-v66,
.dashboard-proximas .next-data-v66,
.proximas-box .next-data-v66 {
    min-width: 0 !important;
    overflow: hidden !important;
}
.dashboard-proximas .next-row-v66 .next-title,
.proximas-box .next-row-v66 .next-title {
    font-size: 12.8px !important;
    line-height: 1.08 !important;
    font-weight: 950 !important;
    color: #0f172a !important;
    margin: 0 0 3px 0 !important;
    padding: 0 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
.dashboard-proximas .next-row-v66 .next-frequency,
.proximas-box .next-row-v66 .next-frequency {
    font-size: 10.3px !important;
    line-height: 1.08 !important;
    font-weight: 800 !important;
    color: #475569 !important;
    margin: 0 !important;
    padding: 0 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
.dashboard-proximas .next-data-v66,
.proximas-box .next-data-v66 {
    display: grid !important;
    grid-template-columns: 1fr !important;
    row-gap: 4px !important;
    background: rgba(248,250,252,.62) !important;
    border: 1px solid rgba(148,163,184,.22) !important;
    border-radius: 10px !important;
    padding: 6px 8px !important;
    box-sizing: border-box !important;
}
.dashboard-proximas .next-kv-v66,
.proximas-box .next-kv-v66 {
    color: #0f172a !important;
    font-size: 11.4px !important;
    line-height: 1.08 !important;
    font-weight: 850 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.dashboard-proximas .next-kv-v66 span,
.proximas-box .next-kv-v66 span {
    color: #334155 !important;
    font-weight: 950 !important;
}
.dashboard-proximas .next-badge-v66,
.proximas-box .next-badge-v66,
.dashboard-proximas .next-row-v66 .badge-days,
.proximas-box .next-row-v66 .badge-days {
    width: 108px !important;
    min-width: 108px !important;
    max-width: 108px !important;
    min-height: 32px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    font-size: 9.6px !important;
    line-height: 1.10 !important;
    font-weight: 950 !important;
    padding: 5px 7px !important;
    border-radius: 999px !important;
    white-space: normal !important;
    box-sizing: border-box !important;
}

@media (max-width: 1500px) {
    .dashboard-costos-spacer {
        height: 48px !important;
        min-height: 48px !important;
    }
    .dashboard-proximas .next-row-v66,
    .proximas-box .next-row-v66,
    .dashboard-proximas .next-item.next-row-v66,
    .proximas-box .next-item.next-row-v66 {
        grid-template-columns: minmax(92px, 0.68fr) minmax(130px, 1fr) 92px !important;
        column-gap: 7px !important;
        min-height: 56px !important;
        padding: 8px 0 !important;
    }
    .dashboard-proximas .next-row-v66 .next-title,
    .proximas-box .next-row-v66 .next-title {
        font-size: 11.8px !important;
    }
    .dashboard-proximas .next-row-v66 .next-frequency,
    .proximas-box .next-row-v66 .next-frequency {
        font-size: 9.6px !important;
    }
    .dashboard-proximas .next-data-v66,
    .proximas-box .next-data-v66 {
        padding: 5px 6px !important;
        row-gap: 3px !important;
    }
    .dashboard-proximas .next-kv-v66,
    .proximas-box .next-kv-v66 {
        font-size: 10.5px !important;
    }
    .dashboard-proximas .next-badge-v66,
    .proximas-box .next-badge-v66,
    .dashboard-proximas .next-row-v66 .badge-days,
    .proximas-box .next-row-v66 .badge-days {
        width: 92px !important;
        min-width: 92px !important;
        max-width: 92px !important;
        font-size: 8.8px !important;
        padding: 5px 5px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V6.7
# - Menú fijo: sin botón minimizar/expandir y sin controles nativos.
# - Elimina barra blanca superior en Próximas Mantenciones.
# - Próximas Mantenciones: una fila limpia por equipo, solo Actual/Próxima/Faltan.
# =========================================================
st.markdown(
    """
<style>
:root {
    --menu-panel-width: 280px !important;
    --menu-inner-width: 248px !important;
    --menu-panel-width-final: 280px !important;
    --menu-inner-width-final: 248px !important;
}
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    transform: translateX(0px) !important;
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
}
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    width: var(--menu-panel-width) !important;
    min-width: var(--menu-panel-width) !important;
    max-width: var(--menu-panel-width) !important;
}
[data-testid="stAppViewContainer"] > .main,
section.main,
main {
    margin-left: var(--menu-panel-width) !important;
    width: calc(100vw - var(--menu-panel-width)) !important;
    max-width: calc(100vw - var(--menu-panel-width)) !important;
}
section[data-testid="stSidebar"] .menu-toggle-wrap,
section[data-testid="stSidebar"] .menu-fixed-spacer,
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
button[title="Collapse sidebar"],
button[title="Close sidebar"],
button[title="Open sidebar"],
button[aria-label="Collapse sidebar"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
    min-width: 0 !important;
    min-height: 0 !important;
    pointer-events: none !important;
}
section[data-testid="stSidebar"] .menu-text,
section[data-testid="stSidebar"] .menu-footer-box,
section[data-testid="stSidebar"] .menu-filter-area,
section[data-testid="stSidebar"] .menu-botones-title {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] .menu-active-item {
    justify-content: flex-start !important;
    text-align: left !important;
}
.dashboard-proximas:not(.dashboard-proximas-v67):empty,
.proximas-box:empty {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: 0 !important;
    box-shadow: none !important;
    background: transparent !important;
}
.dashboard-proximas-v67 {
    background: rgba(255,255,255,.72) !important;
    border: 1px solid rgba(203,213,225,.72) !important;
    border-radius: 16px !important;
    padding: 10px 12px !important;
    margin-top: 0 !important;
    box-shadow: 0 10px 24px rgba(15,23,42,.045) !important;
    overflow: visible !important;
}
.dashboard-proximas-v67 .proximas-title-v67 {
    display: block !important;
    margin: 0 0 8px 0 !important;
    padding: 0 0 5px 0 !important;
    min-height: 24px !important;
    line-height: 1.15 !important;
    font-size: clamp(18px, 1.05vw, 21px) !important;
    font-weight: 950 !important;
    color: #0f172a !important;
}
.next-list-v67 {
    display: flex !important;
    flex-direction: column !important;
    gap: 0 !important;
}
.dashboard-proximas-v67 .next-row-v67 {
    display: grid !important;
    grid-template-columns: minmax(112px, .95fr) minmax(120px, 1fr) minmax(120px, 1fr) 116px !important;
    align-items: center !important;
    column-gap: 10px !important;
    min-height: 42px !important;
    padding: 7px 0 !important;
    margin: 0 !important;
    border-bottom: 1px solid rgba(100,116,139,.22) !important;
    box-sizing: border-box !important;
}
.dashboard-proximas-v67 .next-row-v67:last-child {
    border-bottom: 0 !important;
}
.dashboard-proximas-v67 .next-equipo-v67 {
    color: #0f172a !important;
    font-size: 12.5px !important;
    line-height: 1.10 !important;
    font-weight: 950 !important;
    min-width: 0 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
.dashboard-proximas-v67 .next-actual-v67,
.dashboard-proximas-v67 .next-proxima-v67 {
    color: #0f172a !important;
    font-size: 12.1px !important;
    line-height: 1.10 !important;
    font-weight: 850 !important;
    min-width: 0 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.dashboard-proximas-v67 .next-actual-v67 span,
.dashboard-proximas-v67 .next-proxima-v67 span {
    color: #334155 !important;
    font-weight: 950 !important;
}
.dashboard-proximas-v67 .next-badge-v67,
.dashboard-proximas-v67 .badge-days.next-badge-v67 {
    width: 116px !important;
    min-width: 116px !important;
    max-width: 116px !important;
    min-height: 30px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    font-size: 9.4px !important;
    line-height: 1.08 !important;
    font-weight: 950 !important;
    padding: 5px 7px !important;
    border-radius: 999px !important;
    white-space: normal !important;
    box-sizing: border-box !important;
}
.proximas-empty-v68 {
    color: #334155 !important;
    font-size: 13px !important;
    font-weight: 800 !important;
    padding: 8px 0 !important;
}
@media (max-width: 1500px) {
    .dashboard-proximas-v67 .next-row-v67 {
        grid-template-columns: minmax(92px, .9fr) minmax(98px, 1fr) minmax(98px, 1fr) 100px !important;
        column-gap: 7px !important;
        min-height: 40px !important;
        padding: 6px 0 !important;
    }
    .dashboard-proximas-v67 .next-equipo-v67 {
        font-size: 11.3px !important;
    }
    .dashboard-proximas-v67 .next-actual-v67,
    .dashboard-proximas-v67 .next-proxima-v67 {
        font-size: 10.8px !important;
    }
    .dashboard-proximas-v67 .next-badge-v67,
    .dashboard-proximas-v67 .badge-days.next-badge-v67 {
        width: 100px !important;
        min-width: 100px !important;
        max-width: 100px !important;
        font-size: 8.7px !important;
        padding: 5px 5px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V6.8
# - Próximas Mantenciones dashboard: sin texto Próxima, lectura actual bajo equipo.
# - Badge naranjo/rojo siempre dentro del cuadro.
# =========================================================
st.markdown(
    """
<style>
.dashboard-proximas-v68 {
    background: rgba(255,255,255,.72) !important;
    border: 1px solid rgba(203,213,225,.72) !important;
    border-radius: 18px !important;
    padding: 14px 16px 16px 16px !important;
    margin-top: 0 !important;
    box-shadow: 0 10px 24px rgba(15,23,42,.045) !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    max-width: 100% !important;
}
.dashboard-proximas-v68 .proximas-title-v68 {
    display: block !important;
    margin: 0 0 12px 0 !important;
    padding: 0 !important;
    min-height: 26px !important;
    line-height: 1.15 !important;
    font-size: clamp(19px, 1.08vw, 22px) !important;
    font-weight: 950 !important;
    color: #0f172a !important;
}
.next-list-v68 {
    display: flex !important;
    flex-direction: column !important;
    gap: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    overflow: hidden !important;
}
.dashboard-proximas-v68 .next-row-v68,
.dashboard-proximas-v68 .next-item.next-row-v68 {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 128px !important;
    align-items: center !important;
    column-gap: 12px !important;
    min-height: 52px !important;
    padding: 8px 0 !important;
    margin: 0 !important;
    border-bottom: 1px solid rgba(100,116,139,.20) !important;
    box-sizing: border-box !important;
    width: 100% !important;
    max-width: 100% !important;
    overflow: hidden !important;
}
.dashboard-proximas-v68 .next-row-v68:last-child {
    border-bottom: 0 !important;
}
.dashboard-proximas-v68 .next-info-v68 {
    min-width: 0 !important;
    max-width: 100% !important;
    overflow: hidden !important;
}
.dashboard-proximas-v68 .next-equipo-v68 {
    color: #0f172a !important;
    font-size: 13px !important;
    line-height: 1.10 !important;
    font-weight: 950 !important;
    margin: 0 0 5px 0 !important;
    padding: 0 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
.dashboard-proximas-v68 .next-actual-v68 {
    color: #0f172a !important;
    font-size: 12.2px !important;
    line-height: 1.16 !important;
    font-weight: 850 !important;
    margin: 0 !important;
    padding: 0 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
.dashboard-proximas-v68 .next-actual-v68 span {
    color: #334155 !important;
    font-weight: 950 !important;
}
.dashboard-proximas-v68 .next-badge-v68,
.dashboard-proximas-v68 .badge-days.next-badge-v68 {
    justify-self: end !important;
    width: 128px !important;
    min-width: 128px !important;
    max-width: 128px !important;
    min-height: 32px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    font-size: 9.3px !important;
    line-height: 1.08 !important;
    font-weight: 950 !important;
    padding: 5px 8px !important;
    border-radius: 999px !important;
    white-space: normal !important;
    box-sizing: border-box !important;
    overflow-wrap: anywhere !important;
}
.proximas-empty-v68 {
    color: #334155 !important;
    font-size: 13px !important;
    font-weight: 800 !important;
    padding: 8px 0 !important;
}
@media (max-width: 1500px) {
    .dashboard-proximas-v68 {
        padding: 12px 12px 14px 12px !important;
    }
    .dashboard-proximas-v68 .next-row-v68,
    .dashboard-proximas-v68 .next-item.next-row-v68 {
        grid-template-columns: minmax(0, 1fr) 108px !important;
        column-gap: 8px !important;
        min-height: 50px !important;
        padding: 7px 0 !important;
    }
    .dashboard-proximas-v68 .next-equipo-v68 {
        font-size: 12px !important;
    }
    .dashboard-proximas-v68 .next-actual-v68 {
        font-size: 11px !important;
    }
    .dashboard-proximas-v68 .next-badge-v68,
    .dashboard-proximas-v68 .badge-days.next-badge-v68 {
        width: 108px !important;
        min-width: 108px !important;
        max-width: 108px !important;
        font-size: 8.4px !important;
        padding: 5px 5px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# RESPONSIVE FINAL V7.3
# - Escritorio: no cambia la distribución existente.
# - Teléfono vertical/horizontal: menú cerrado por defecto y botón Streamlit real.
# =========================================================

_menu_movil_abierto = bool(st.session_state.get("_saivam_mobile_menu_open", False))
_menu_transform = "translate3d(0,0,0)" if _menu_movil_abierto else "translate3d(-110%,0,0)"
_menu_visibility = "visible" if _menu_movil_abierto else "hidden"
_menu_pointer = "auto" if _menu_movil_abierto else "none"
_boton_left = "calc(var(--mobile-menu-width) - 54px)" if _menu_movil_abierto else "max(10px, env(safe-area-inset-left))"
_boton_bg = "#ef4444" if _menu_movil_abierto else "linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%)"

st.markdown(
    f"""
<style>
/* En escritorio el nuevo control no existe visualmente. */
.st-key-saivam_mobile_menu_control,
div[class*="st-key-saivam_mobile_menu_control"] {{
    display: none !important;
}}

/* Safari/iPhone horizontal puede informar un ancho mayor; se complementa con pointer coarse. */
@media (max-width: 768px),
       (max-width: 1100px) and (max-height: 700px),
       (hover: none) and (pointer: coarse) and (max-width: 1100px) {{

    :root {{
        --mobile-menu-width: min(86vw, 300px) !important;
        --mobile-page-padding: 10px !important;
    }}

    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"] {{
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }}

    /* Control nativo real de Streamlit. */
    .st-key-saivam_mobile_menu_control,
    div[class*="st-key-saivam_mobile_menu_control"] {{
        display: block !important;
        position: fixed !important;
        top: max(10px, env(safe-area-inset-top)) !important;
        left: {_boton_left} !important;
        width: 44px !important;
        height: 44px !important;
        margin: 0 !important;
        padding: 0 !important;
        z-index: 2147483647 !important;
    }}

    .st-key-saivam_mobile_menu_control [data-testid="stButton"],
    div[class*="st-key-saivam_mobile_menu_control"] [data-testid="stButton"] {{
        width: 44px !important;
        height: 44px !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    .st-key-saivam_mobile_menu_control button,
    div[class*="st-key-saivam_mobile_menu_control"] button {{
        width: 44px !important;
        min-width: 44px !important;
        max-width: 44px !important;
        height: 44px !important;
        min-height: 44px !important;
        max-height: 44px !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 13px !important;
        border: 2px solid #ffffff !important;
        background: {_boton_bg} !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 24px !important;
        line-height: 1 !important;
        font-weight: 950 !important;
        box-shadow: 0 8px 24px rgba(15,23,42,.42) !important;
    }}

    /* Oculta controles laterales nativos que estaban en conflicto. */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    button[title="Open sidebar"],
    button[title="Close sidebar"],
    button[aria-label="Open sidebar"],
    button[aria-label="Close sidebar"] {{
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }}

    header[data-testid="stHeader"] {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
    }}

    /* Sidebar móvil: no reserva ancho cuando está cerrado. */
    html body section[data-testid="stSidebar"] {{
        display: block !important;
        position: fixed !important;
        inset: 0 auto 0 0 !important;
        width: var(--mobile-menu-width) !important;
        min-width: var(--mobile-menu-width) !important;
        max-width: var(--mobile-menu-width) !important;
        height: 100vh !important;
        height: 100dvh !important;
        margin: 0 !important;
        transform: {_menu_transform} !important;
        visibility: {_menu_visibility} !important;
        opacity: 1 !important;
        pointer-events: {_menu_pointer} !important;
        overflow-x: hidden !important;
        overflow-y: auto !important;
        overscroll-behavior: contain !important;
        transition: transform .22s ease, visibility .22s ease !important;
        z-index: 2147483645 !important;
        background: #020617 !important;
        box-shadow: 14px 0 34px rgba(2,6,23,.48) !important;
    }}

    html body section[data-testid="stSidebar"] > div,
    html body section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
        width: var(--mobile-menu-width) !important;
        min-width: var(--mobile-menu-width) !important;
        max-width: var(--mobile-menu-width) !important;
        min-height: 100vh !important;
        min-height: 100dvh !important;
        padding: 10px 12px calc(28px + env(safe-area-inset-bottom)) 12px !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }}

    html body section[data-testid="stSidebar"] .menu-panel-content,
    html body section[data-testid="stSidebar"] .menu-brand,
    html body section[data-testid="stSidebar"] .menu-line,
    html body section[data-testid="stSidebar"] .menu-footer-box,
    html body section[data-testid="stSidebar"] .menu-filter-area,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"],
    html body section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
    html body section[data-testid="stSidebar"] [data-baseweb="select"],
    html body section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    html body section[data-testid="stSidebar"] .menu-active-item,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
        width: calc(var(--mobile-menu-width) - 24px) !important;
        min-width: 0 !important;
        max-width: calc(var(--mobile-menu-width) - 24px) !important;
        box-sizing: border-box !important;
    }}

    html body section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    html body section[data-testid="stSidebar"] .menu-active-item {{
        min-height: 43px !important;
        height: auto !important;
        padding: 9px 10px !important;
        font-size: 13px !important;
        line-height: 1.16 !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }}

    /* Contenido principal: ancho completo, sin el margen de 280/300 px de PC. */
    html body [data-testid="stAppViewContainer"] > .main,
    html body div[data-testid="stMain"],
    html body section.main,
    html body main {{
        margin-left: 0 !important;
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
        box-sizing: border-box !important;
    }}

    html body .main .block-container,
    html body .block-container,
    html body div[data-testid="stMainBlockContainer"],
    html body section.main > div {{
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: calc(62px + env(safe-area-inset-top)) var(--mobile-page-padding)
                 calc(74px + env(safe-area-inset-bottom)) var(--mobile-page-padding) !important;
        overflow-x: hidden !important;
        box-sizing: border-box !important;
    }}

    html body .main *,
    html body main * {{
        min-width: 0;
        box-sizing: border-box;
    }}


    .main-fixed-header,
    .header-principal {{
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        height: auto !important;
        min-height: 52px !important;
        padding: 7px 8px !important;
        margin: 0 0 8px 0 !important;
        gap: 8px !important;
        overflow: hidden !important;
    }}

    .main-fixed-title,
    .title-main {{
        min-width: 0 !important;
        max-width: 100% !important;
        font-size: clamp(20px, 6vw, 29px) !important;
        line-height: 1.08 !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
    }}

    .main-fixed-logo,
    .header-logo-box {{
        flex: 0 0 auto !important;
        max-width: 28% !important;
    }}

    .main-fixed-logo img,
    .header-logo-box img {{
        width: min(112px, 27vw) !important;
        max-width: 100% !important;
        height: auto !important;
    }}

    /* En vertical: todos los bloques quedan en una sola columna legible. */
    html body [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: column !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
        gap: .55rem !important;
    }}

    html body [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
        flex: 1 1 100% !important;
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
    }}

    .kpi-card,
    .panel-box,
    .chart-card,
    .equipo-card,
    .dashboard-proximas,
    .dashboard-proximas-v68,
    .proximas-box {{
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        overflow: hidden !important;
    }}

    .panel-title,
    .page-section-title,
    .chart-title {{
        font-size: clamp(17px, 5vw, 22px) !important;
        line-height: 1.15 !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
    }}

    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"],
    [data-testid="stTable"] {{
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
    }}

    [data-testid="stDataFrame"] {{
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }}

    [data-testid="stPlotlyChart"] {{
        min-height: 260px !important;
        overflow: hidden !important;
    }}

    [data-testid="stPlotlyChart"] > div,
    [data-testid="stPlotlyChart"] iframe {{
        width: 100% !important;
        max-width: 100% !important;
    }}

    .equipo-img,
    .equipo-img-placeholder {{
        width: 100% !important;
        height: 170px !important;
        min-height: 170px !important;
        object-fit: cover !important;
    }}

    .dashboard-proximas-v68 .next-row-v68,
    .dashboard-proximas-v68 .next-item.next-row-v68 {{
        grid-template-columns: minmax(0, 1fr) !important;
        row-gap: 7px !important;
    }}

    .dashboard-proximas-v68 .next-badge-v68,
    .dashboard-proximas-v68 .badge-days.next-badge-v68 {{
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
    }}
}}

/* Teléfono horizontal: dos columnas generales y tres KPI por fila. */
@media (min-width: 601px) and (max-width: 1100px)
       and (orientation: landscape) and (max-height: 700px),
       (hover: none) and (pointer: coarse)
       and (min-width: 601px) and (max-width: 1100px) {{

    :root {{
        --mobile-menu-width: min(42vw, 320px) !important;
    }}

    html body [data-testid="stHorizontalBlock"] {{
        flex-direction: row !important;
        flex-wrap: wrap !important;
    }}

    html body [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
        flex: 1 1 calc(50% - .35rem) !important;
        width: calc(50% - .35rem) !important;
        max-width: calc(50% - .35rem) !important;
    }}

    html body [data-testid="stHorizontalBlock"]:has(.kpi-card)
    > [data-testid="column"] {{
        flex: 1 1 calc(33.333% - .4rem) !important;
        width: calc(33.333% - .4rem) !important;
        max-width: calc(33.333% - .4rem) !important;
    }}

    .kpi-card {{
        min-height: 100px !important;
        padding: 9px 10px !important;
    }}

    .equipo-img,
    .equipo-img-placeholder {{
        height: 145px !important;
        min-height: 145px !important;
    }}
}}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# AJUSTE FINAL V8.1 - MENÚ Y FILTROS MÁS COMPACTOS
# Reduce moderadamente la separación vertical sin cambiar
# el ancho, alto ni posición de los elementos seleccionados.
# =========================================================
st.markdown(
    """
<style>
/* Reduce el espacio automático entre bloques internos del sidebar */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
    gap: 0.22rem !important;
}

/* Menor separación entre cada opción del menú */
section[data-testid="stSidebar"] div[data-testid="stButton"] {
    margin-top: 0px !important;
    margin-bottom: 4px !important;
}

/* Mantiene todos los botones con el mismo tamaño */
section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
section[data-testid="stSidebar"] div[data-testid="stButton"] button {
    margin-top: 0px !important;
    margin-bottom: 0px !important;
}

/* Acerca el último menú a los filtros Equipo y Contrato */
section[data-testid="stSidebar"] .menu-line {
    margin-top: 6px !important;
    margin-bottom: 6px !important;
}

/* Compacta ligeramente los filtros sin reducir su legibilidad */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] {
    margin-top: 0px !important;
    margin-bottom: 2px !important;
}

section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label {
    margin-bottom: 2px !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# - Usa exclusivamente la imagen cuyo nombre base es "saivam".
# - La muestra completa, centrada y sin recortes.
# =========================================================


# =========================================================
# REFUERZO FINAL V9.1 - MARCA OFICIAL SIEMPRE VISIBLE
# =========================================================
st.markdown(
    """
<style>



/* =========================================================
   ESCRITORIO: SIDEBAR FIJO Y CONTENIDO TOTALMENTE SEPARADO
   ========================================================= */
@media screen and (min-width: 1101px) {

    html body section[data-testid="stSidebar"] {
        position: fixed !important;
        inset: 0 auto 0 0 !important;
        width: var(--menu-panel-width) !important;
        min-width: var(--menu-panel-width) !important;
        max-width: var(--menu-panel-width) !important;
        height: 100vh !important;
        margin: 0 !important;
        transform: none !important;
        z-index: 10000 !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
        overflow-y: auto !important;
    }

    /*
    Selector correcto para las versiones actuales de Streamlit:
    stMain es un elemento SECTION, no un DIV.
    */
    html body section[data-testid="stMain"],
    html body [data-testid="stAppViewContainer"] > section[data-testid="stMain"],
    html body section.stMain {
        position: relative !important;
        left: 0 !important;
        transform: none !important;
        margin-left: var(--menu-panel-width) !important;
        margin-right: 0 !important;
        width: calc(100vw - var(--menu-panel-width)) !important;
        min-width: 0 !important;
        max-width: calc(100vw - var(--menu-panel-width)) !important;
        flex: 0 0 calc(100vw - var(--menu-panel-width)) !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
        z-index: 1 !important;
    }

    html body section[data-testid="stMain"] > div,
    html body div[data-testid="stMainBlockContainer"],
    html body .stMainBlockContainer,
    html body .block-container {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        padding-left: 14px !important;
        padding-right: 14px !important;
        box-sizing: border-box !important;
    }

    /*
    Evita que cualquier regla antigua vuelva a desplazar el contenido
    debajo del menú.
    */
    html body [data-testid="stAppViewContainer"] {
        width: 100vw !important;
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }
}

/* =========================================================
   MÓVIL: NO SE APLICA EL DESPLAZAMIENTO DE ESCRITORIO
   ========================================================= */
@media screen and (max-width: 1100px) {
    html body section[data-testid="stMain"],
    html body [data-testid="stAppViewContainer"] > section[data-testid="stMain"],
    html body section.stMain {
        margin-left: 0 !important;
        width: 100vw !important;
        max-width: 100vw !important;
        flex-basis: 100vw !important;
    }


}
</style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# AJUSTE FINAL V10.0 - MENÚ FIJO Y DISTRIBUCIÓN VERTICAL
# - Sidebar inmóvil en escritorio.
# - Mayor separación entre marca superior y Resumen Ejecutivo.
# - Filtros Equipo/Contrato y caja informativa desplazados hacia abajo.
# =========================================================
st.markdown(
    """
<style>
@media screen and (min-width: 1101px) {
    html body section[data-testid="stSidebar"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        bottom: 0 !important;
        height: 100vh !important;
        max-height: 100vh !important;
        overflow-x: hidden !important;
        overflow-y: hidden !important;
        overscroll-behavior: none !important;
        z-index: 10000 !important;
    }

    html body section[data-testid="stSidebar"] > div,
    html body section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        height: 100vh !important;
        max-height: 100vh !important;
        overflow: hidden !important;
        box-sizing: border-box !important;
    }
}

/* Espacio visual entre SEGUIMIENTO EQUIPOS MÓVILES y el primer botón. */
section[data-testid="stSidebar"] .menu-top-gap {
    display: block !important;
    height: 22px !important;
    min-height: 22px !important;
    width: 100% !important;
}

/* Separa el bloque de navegación de los filtros. */
section[data-testid="stSidebar"] .menu-filter-gap {
    display: block !important;
    height: 26px !important;
    min-height: 26px !important;
    width: 100% !important;
}

/* La caja Contrato/Cliente/Versión queda más abajo respecto de los filtros. */
section[data-testid="stSidebar"] .menu-footer-box {
    margin-top: 28px !important;
}

/* Mantiene una separación limpia bajo la marca superior. */
section[data-testid="stSidebar"] .menu-brand {
    margin-bottom: 10px !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CORRECCIÓN FINAL V10.1 - SIDEBAR FIJO SIN CORTE SUPERIOR
# Neutraliza desplazamientos antiguos que ocultaban la cabecera y filtros.
# =========================================================
st.markdown(
    """
<style>
/* Sidebar siempre visible y pegado al borde superior. */
html body section[data-testid="stSidebar"] {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    bottom: 0 !important;
    height: 100vh !important;
    max-height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow-x: hidden !important;
    overflow-y: hidden !important;
    z-index: 10000 !important;
}

/* Corrección principal: nunca desplazar el contenido interno hacia arriba. */
html body section[data-testid="stSidebar"] > div,
html body section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    top: 0 !important;
    margin-top: 0 !important;
    padding-top: 14px !important;
    transform: none !important;
    translate: none !important;
    height: 100vh !important;
    max-height: 100vh !important;
    overflow-x: hidden !important;
    overflow-y: hidden !important;
    box-sizing: border-box !important;
}

/* La marca superior queda completamente visible. */
html body section[data-testid="stSidebar"] .menu-panel-content {
    margin-top: 0 !important;
    padding-top: 0 !important;
    transform: none !important;
    overflow: visible !important;
}

html body section[data-testid="stSidebar"] .menu-brand {
    margin-top: 0 !important;
    margin-bottom: 12px !important;
    transform: none !important;
    min-height: 58px !important;
}

/* Espacio solicitado antes de Resumen Ejecutivo. */
html body section[data-testid="stSidebar"] .menu-top-gap {
    display: block !important;
    height: 46px !important;
    min-height: 46px !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Separación entre navegación y filtros. */
html body section[data-testid="stSidebar"] .menu-filter-gap {
    display: block !important;
    height: 24px !important;
    min-height: 24px !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Filtros y caja informativa más abajo, pero sin salir de pantalla. */
html body section[data-testid="stSidebar"] div[data-testid="stSelectbox"] {
    margin-bottom: 8px !important;
}

html body section[data-testid="stSidebar"] .menu-footer-box {
    margin-top: 22px !important;
    margin-bottom: 0 !important;
}

/* Evita que Streamlit conserve un scroll interno del sidebar. */
html body section[data-testid="stSidebar"]::-webkit-scrollbar,
html body section[data-testid="stSidebar"] *::-webkit-scrollbar {
    width: 0 !important;
    height: 0 !important;
    display: none !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# AJUSTE FINAL V10.2 - MARCA ARRIBA + ESPACIO ANTES DEL MENÚ
# La marca queda anclada a la parte superior del sidebar y el espacio
# se reserva debajo de ella, antes de "Resumen Ejecutivo".
# =========================================================
st.markdown(
    """
<style>
@media screen and (min-width: 1101px) {
    /* El contenedor lateral sirve de referencia para la marca superior. */
    html body section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        position: relative !important;
        padding-top: 12px !important;
        margin-top: 0 !important;
    }

    /* Logo + título siempre pegados a la parte superior. */
    html body section[data-testid="stSidebar"] .menu-panel-content {
        position: absolute !important;
        top: 18px !important;
        left: 14px !important;
        right: 14px !important;
        width: auto !important;
        max-width: none !important;
        margin: 0 !important;
        padding: 0 !important;
        transform: none !important;
        z-index: 5 !important;
    }

    html body section[data-testid="stSidebar"] .menu-brand {
        margin: 0 0 8px 0 !important;
        padding: 0 !important;
        transform: none !important;
        min-height: 58px !important;
    }

    /* Reserva el espacio bajo la cabecera y deja el aire solicitado
       antes de que comience Resumen Ejecutivo. */
    html body section[data-testid="stSidebar"] .menu-top-gap {
        display: block !important;
        height: 148px !important;
        min-height: 148px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
}

/* En pantallas angostas conserva el comportamiento móvil sin desplazar la cabecera. */
@media screen and (max-width: 1100px) {
    html body section[data-testid="stSidebar"] .menu-panel-content {
        margin-top: 0 !important;
        transform: none !important;
    }

    html body section[data-testid="stSidebar"] .menu-top-gap {
        height: 34px !important;
        min-height: 34px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# AJUSTE FINAL V10.3 - LOGO/CABECERA PEGADOS AL BORDE SUPERIOR
# Fuerza la marca del menú a la parte superior real del viewport.
# El espacio se conserva debajo de la cabecera, antes de los botones.
# =========================================================
st.markdown(
    """
<style>
@media screen and (min-width: 1101px) {
    /* La cabecera ya no depende de la posición del bloque Markdown. */
    html body section[data-testid="stSidebar"] .menu-panel-content {
        position: fixed !important;
        top: 12px !important;
        left: 17px !important;
        right: auto !important;
        width: var(--menu-inner-width) !important;
        max-width: var(--menu-inner-width) !important;
        margin: 0 !important;
        padding: 0 !important;
        transform: none !important;
        z-index: 10020 !important;
    }

    html body section[data-testid="stSidebar"] .menu-brand {
        margin: 0 0 10px 0 !important;
        padding: 0 !important;
        min-height: 58px !important;
        align-items: center !important;
    }

    /* La línea queda inmediatamente bajo el logo/título. */
    html body section[data-testid="stSidebar"] .menu-panel-content .menu-line {
        margin-top: 8px !important;
        margin-bottom: 0 !important;
    }

    /* Reserva espacio únicamente debajo de la cabecera fija. */
    html body section[data-testid="stSidebar"] .menu-top-gap {
        display: block !important;
        height: 118px !important;
        min-height: 118px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
}

@media screen and (max-width: 1100px) {
    html body section[data-testid="stSidebar"] .menu-panel-content {
        position: relative !important;
        top: auto !important;
        left: auto !important;
        right: auto !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V10.5 - CUATRO FILTROS COMPACTOS
# Equipo + Contrato + Año + Mes con menor altura y separación.
# =========================================================
st.markdown(
    """
<style>
/* Reduce la altura total de los cuatro filtros del menú lateral. */
html body section[data-testid="stSidebar"] div[data-testid="stSelectbox"] {
    margin-top: 0 !important;
    margin-bottom: 3px !important;
    padding: 0 !important;
}

html body section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label,
html body section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label * {
    font-size: 12px !important;
    line-height: 1.05 !important;
    margin-bottom: 2px !important;
    min-height: 0 !important;
}

html body section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    min-height: 36px !important;
    height: 36px !important;
    border-radius: 11px !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

html body section[data-testid="stSidebar"] [data-baseweb="select"] span,
html body section[data-testid="stSidebar"] [data-baseweb="select"] input {
    font-size: 14px !important;
    line-height: 36px !important;
}

/* Con cuatro filtros, acerca la caja informativa para mantener todo visible. */
html body section[data-testid="stSidebar"] .menu-footer-box {
    margin-top: 12px !important;
    min-height: 96px !important;
    padding: 13px 14px !important;
}

html body section[data-testid="stSidebar"] .menu-filter-gap {
    height: 12px !important;
    min-height: 12px !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL - CRÉDITOS FIJOS AL PIE DEL MENÚ IZQUIERDO
# =========================================================
st.markdown(
    """
<style>
@media screen and (min-width: 1101px) {
    html body section[data-testid="stSidebar"] .sidebar-credit-footer {
        position: fixed !important;
        left: 18px !important;
        bottom: 14px !important;
        width: calc(var(--menu-inner-width) - 2px) !important;
        box-sizing: border-box !important;
        z-index: 10030 !important;
        color: #cbd5e1 !important;
        text-align: center !important;
        font-size: 10.5px !important;
        line-height: 1.35 !important;
        padding: 8px 6px 2px 6px !important;
        background: #020817 !important;
    }

    html body section[data-testid="stSidebar"] .sidebar-credit-management {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }

    html body section[data-testid="stSidebar"] .sidebar-credit-management div:first-child {
        font-size: 11px !important;
        margin-bottom: 2px !important;
    }

    html body section[data-testid="stSidebar"] .sidebar-credit-divider {
        height: 1px !important;
        background: rgba(148, 163, 184, 0.28) !important;
        margin: 7px 14px 6px 14px !important;
    }

    html body section[data-testid="stSidebar"] .sidebar-credit-developed {
        color: #94a3b8 !important;
    }

    html body section[data-testid="stSidebar"] .menu-footer-box {
        margin-bottom: 94px !important;
    }
}

@media screen and (max-width: 1100px) {
    html body section[data-testid="stSidebar"] .sidebar-credit-footer {
        position: relative !important;
        left: auto !important;
        bottom: auto !important;
        width: 100% !important;
        margin-top: 18px !important;
        padding: 10px 4px !important;
        color: #cbd5e1 !important;
        text-align: center !important;
        font-size: 10.5px !important;
        line-height: 1.35 !important;
    }

    html body section[data-testid="stSidebar"] .sidebar-credit-divider {
        height: 1px !important;
        background: rgba(148, 163, 184, 0.28) !important;
        margin: 7px 14px 6px 14px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# AJUSTE FINAL - RECUADRO DE VERSION COMPACTO
# =========================================================
st.markdown(
    """
<style>
/* El recuadro de versión se ajusta exactamente al contenido. */
html body section[data-testid="stSidebar"] .menu-footer-box {
    display: block !important;
    width: fit-content !important;
    min-width: 0 !important;
    max-width: calc(100% - 8px) !important;
    height: auto !important;
    min-height: 0 !important;
    padding: 8px 12px !important;
    margin-top: 12px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    box-sizing: border-box !important;
    border-radius: 12px !important;
}

html body section[data-testid="stSidebar"] .menu-footer-box .menu-info,
html body section[data-testid="stSidebar"] .menu-footer-box .menu-info * {
    display: inline !important;
    width: auto !important;
    height: auto !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
    text-align: center !important;
}

@media screen and (min-width: 1101px) {
    html body section[data-testid="stSidebar"] .menu-footer-box {
        margin-bottom: 94px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL - SELLO DE AGUA SAIVAM EN TODO EL CONTENIDO
# - Busca automáticamente una imagen llamada "saivam" en las carpetas de imágenes.
# - Se aplica en todas las páginas del contenido principal.
# - El menú lateral queda completamente excluido del sello de agua.
# =========================================================
def aplicar_sello_agua_saivam():
    ruta_sello = buscar_imagen_por_nombre("saivam")

    if not ruta_sello:
        return

    sello_b64 = archivo_a_base64(ruta_sello)
    if not sello_b64:
        return

    mime_sello = extension_mime(ruta_sello)

    st.markdown(
        f"""
<style>
/*
   Capa fija de sello de agua sobre toda el área principal.
   El borde izquierdo comienza exactamente después del menú.
*/
[data-testid="stAppViewContainer"]::after {{
    content: "" !important;
    position: fixed !important;
    top: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    left: var(--menu-panel-width, 250px) !important;
    width: auto !important;
    height: 100vh !important;
    background-image: url("data:{mime_sello};base64,{sello_b64}") !important;
    background-repeat: no-repeat !important;
    background-position: center center !important;
    background-size: cover !important;
    opacity: 0.12 !important;
    pointer-events: none !important;
    user-select: none !important;
    z-index: 9000 !important;
}}

/* El menú siempre queda sobre la capa y nunca recibe el sello. */
section[data-testid="stSidebar"] {{
    z-index: 10000 !important;
}}

/* En pantallas pequeñas se mantiene respetado el ancho real del menú. */
@media screen and (max-width: 1100px) {{
    [data-testid="stAppViewContainer"]::after {{
        left: var(--menu-panel-width, 250px) !important;
    }}
}}
</style>
        """,
        unsafe_allow_html=True,
    )


aplicar_sello_agua_saivam()


# =========================================================
# AJUSTE FINAL V2.6 - POSICIÓN DEL MENÚ + GRÁFICO COMPACTO
# - Los ítems de navegación quedan más hacia la izquierda.
# - Solo el recuadro de Versión permanece centrado.
# - Evolución mensual queda compacta debajo de Costos por contrato.
# =========================================================
st.markdown(
    """
<style>
/* Menú de navegación: anclado hacia el borde izquierdo del sidebar. */
@media screen and (min-width: 1101px) {
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] {
        margin-left: 0 !important;
        margin-right: auto !important;
        transform: translateX(-4px) !important;
    }

    html body section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] button {
        margin-left: 0 !important;
        margin-right: 0 !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }

    /* La versión es el único bloque del menú que se mantiene centrado. */
    html body section[data-testid="stSidebar"] .menu-footer-box {
        margin-left: auto !important;
        margin-right: auto !important;
        transform: none !important;
        text-align: center !important;
    }
}

/* Separación breve entre la tabla y el gráfico compacto. */
.exec9-evolution-under-table-gap {
    height: 18px !important;
    min-height: 18px !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# AJUSTE FINAL V2.6 - CENTRADO EXACTO DEL RECUADRO DE VERSIÓN
# =========================================================
st.markdown(
    """
<style>
@media screen and (min-width: 1101px) {
    html body section[data-testid="stSidebar"] .menu-footer-box {
        position: relative !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        text-align: center !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V2.6 - SIDEBAR MÁS ANGOSTO + VERSIÓN AL PIE
# - Reduce levemente el ancho del menú lateral.
# - Mantiene los ítems alineados a la izquierda.
# - Créditos al pie y Versión 2.6 centrada debajo de Ricardo Grez.
# =========================================================
st.markdown(
    """
<style>
:root {
    --menu-panel-width: 260px !important;
    --menu-inner-width: 230px !important;
    --menu-panel-width-final: 260px !important;
    --menu-inner-width-final: 230px !important;
}

@media screen and (min-width: 1101px) {
    /* Panel lateral un poco más angosto. */
    html body section[data-testid="stSidebar"] {
        width: var(--menu-panel-width) !important;
        min-width: var(--menu-panel-width) !important;
        max-width: var(--menu-panel-width) !important;
    }

    html body section[data-testid="stSidebar"] > div,
    html body section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        width: var(--menu-panel-width) !important;
        min-width: var(--menu-panel-width) !important;
        max-width: var(--menu-panel-width) !important;
        padding-left: 14px !important;
        padding-right: 14px !important;
    }

    /* Ajusta el contenido principal al nuevo ancho del sidebar. */
    html body section[data-testid="stMain"],
    html body [data-testid="stAppViewContainer"] > section[data-testid="stMain"],
    html body section.stMain,
    html body [data-testid="stAppViewContainer"] > .main,
    html body section.main,
    html body main {
        margin-left: var(--menu-panel-width) !important;
        width: calc(100vw - var(--menu-panel-width)) !important;
        max-width: calc(100vw - var(--menu-panel-width)) !important;
        flex-basis: calc(100vw - var(--menu-panel-width)) !important;
    }

    /* Todos los elementos de navegación respetan el ancho compacto. */
    html body section[data-testid="stSidebar"] .menu-panel-content,
    html body section[data-testid="stSidebar"] .menu-line,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"],
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    html body section[data-testid="stSidebar"] .menu-active-item {
        width: var(--menu-inner-width) !important;
        min-width: var(--menu-inner-width) !important;
        max-width: var(--menu-inner-width) !important;
    }

    /* Créditos: suben ligeramente para dejar la versión debajo de Ricardo. */
    html body section[data-testid="stSidebar"] .sidebar-credit-footer {
        position: fixed !important;
        left: 15px !important;
        bottom: 67px !important;
        width: var(--menu-inner-width) !important;
        max-width: var(--menu-inner-width) !important;
        margin: 0 !important;
        padding: 7px 4px 2px 4px !important;
        text-align: center !important;
        box-sizing: border-box !important;
    }

    /* Versión: último elemento, centrado debajo de Ricardo Grez. */
    html body section[data-testid="stSidebar"] .menu-footer-box {
        position: fixed !important;
        left: calc(var(--menu-panel-width) / 2) !important;
        right: auto !important;
        bottom: 12px !important;
        top: auto !important;
        transform: translateX(-50%) !important;
        display: block !important;
        width: fit-content !important;
        min-width: 0 !important;
        max-width: calc(var(--menu-inner-width) - 20px) !important;
        height: auto !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 8px 12px !important;
        text-align: center !important;
        box-sizing: border-box !important;
        z-index: 10040 !important;
    }

    html body section[data-testid="stSidebar"] .menu-footer-box .menu-info,
    html body section[data-testid="stSidebar"] .menu-footer-box .menu-info * {
        text-align: center !important;
        white-space: nowrap !important;
    }
}

/* El sello de agua comienza después del nuevo ancho del menú. */
[data-testid="stAppViewContainer"]::after {
    left: var(--menu-panel-width) !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V2.6 - SIDEBAR COMPACTO REAL
# - Corrige el ancho flex heredado de ajustes anteriores.
# - Reduce efectivamente la barra oscura izquierda.
# =========================================================
st.markdown(
    """
<style>
:root {
    --sidebar-compact-width: 260px !important;
    --sidebar-compact-inner: 230px !important;
}

@media screen and (min-width: 1101px) {
    /* El sidebar participa del layout con el mismo ancho visual. */
    html body section[data-testid="stSidebar"] {
        width: var(--sidebar-compact-width) !important;
        min-width: var(--sidebar-compact-width) !important;
        max-width: var(--sidebar-compact-width) !important;
        flex: 0 0 var(--sidebar-compact-width) !important;
        flex-basis: var(--sidebar-compact-width) !important;
        box-sizing: border-box !important;
    }

    html body section[data-testid="stSidebar"] > div,
    html body section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        width: var(--sidebar-compact-width) !important;
        min-width: var(--sidebar-compact-width) !important;
        max-width: var(--sidebar-compact-width) !important;
        padding-left: 15px !important;
        padding-right: 15px !important;
        box-sizing: border-box !important;
    }

    /* Elimina anchos heredados de 360 px dentro del menú. */
    html body section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"],
    html body section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div,
    html body section[data-testid="stSidebar"] div[data-testid="element-container"],
    html body section[data-testid="stSidebar"] .menu-panel-content,
    html body section[data-testid="stSidebar"] .menu-brand,
    html body section[data-testid="stSidebar"] .menu-line,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"],
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    html body section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
    html body section[data-testid="stSidebar"] [data-baseweb="select"],
    html body section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    html body section[data-testid="stSidebar"] .menu-active-item {
        width: var(--sidebar-compact-inner) !important;
        min-width: var(--sidebar-compact-inner) !important;
        max-width: var(--sidebar-compact-inner) !important;
        box-sizing: border-box !important;
    }

    /* Contenido principal directamente al costado, sin doble margen. */
    html body [data-testid="stAppViewContainer"] {
        display: flex !important;
        align-items: stretch !important;
    }

    html body [data-testid="stAppViewContainer"] > .main,
    html body div[data-testid="stMain"],
    html body section[data-testid="stMain"],
    html body section.stMain,
    html body section.main,
    html body main {
        margin-left: 0 !important;
        flex: 1 0 auto !important;
        width: auto !important;
        max-width: none !important;
    }

    /* Créditos y versión alineados al nuevo ancho. */
    html body section[data-testid="stSidebar"] .sidebar-credit-footer {
        left: 15px !important;
        width: var(--sidebar-compact-inner) !important;
        max-width: var(--sidebar-compact-inner) !important;
    }

    html body section[data-testid="stSidebar"] .menu-footer-box {
        left: calc(var(--sidebar-compact-width) / 2) !important;
        max-width: calc(var(--sidebar-compact-inner) - 12px) !important;
    }
}

[data-testid="stAppViewContainer"]::after {
    left: var(--sidebar-compact-width) !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# AJUSTE FINAL V2.6 - SIDEBAR MÁS ANGOSTO + CONTENIDO AL COSTADO
# - Reduce el ancho real del panel lateral.
# - Reduce el tamaño de texto de los 4 ítems de navegación.
# - Evita que la página principal quede debajo del menú fijo.
# - Hace que el contenido use solamente el ancho disponible a la derecha.
# =========================================================
st.markdown(
    """
<style>
:root {
    --sidebar-final-width: 230px !important;
    --sidebar-final-inner: 204px !important;
}

@media screen and (min-width: 1101px) {
    /* 1) Barra lateral realmente más angosta. */
    html body section[data-testid="stSidebar"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        bottom: 0 !important;
        width: var(--sidebar-final-width) !important;
        min-width: var(--sidebar-final-width) !important;
        max-width: var(--sidebar-final-width) !important;
        flex: 0 0 var(--sidebar-final-width) !important;
        flex-basis: var(--sidebar-final-width) !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    html body section[data-testid="stSidebar"] > div,
    html body section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        width: var(--sidebar-final-width) !important;
        min-width: var(--sidebar-final-width) !important;
        max-width: var(--sidebar-final-width) !important;
        padding-left: 13px !important;
        padding-right: 13px !important;
        box-sizing: border-box !important;
    }

    /* Elementos internos del menú dentro del nuevo ancho. */
    html body section[data-testid="stSidebar"] .menu-panel-content,
    html body section[data-testid="stSidebar"] .menu-brand,
    html body section[data-testid="stSidebar"] .menu-line,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"],
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    html body section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
    html body section[data-testid="stSidebar"] [data-baseweb="select"],
    html body section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    html body section[data-testid="stSidebar"] .menu-active-item {
        width: var(--sidebar-final-inner) !important;
        min-width: var(--sidebar-final-inner) !important;
        max-width: var(--sidebar-final-inner) !important;
        box-sizing: border-box !important;
    }

    /* Ítems Resumen Ejecutivo / Equipos / Intervenciones / Documentación. */
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] > button,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] button,
    html body section[data-testid="stSidebar"] .menu-active-item {
        min-height: 43px !important;
        padding: 8px 9px !important;
        font-size: 13.2px !important;
        line-height: 1.18 !important;
        border-radius: 12px !important;
        white-space: nowrap !important;
    }

    html body section[data-testid="stSidebar"] div[data-testid="stButton"] button p,
    html body section[data-testid="stSidebar"] div[data-testid="stButton"] button span,
    html body section[data-testid="stSidebar"] .menu-active-item,
    html body section[data-testid="stSidebar"] .menu-active-item * {
        font-size: 13.2px !important;
        line-height: 1.18 !important;
    }

    /* Marca superior proporcionada al sidebar compacto. */
    html body section[data-testid="stSidebar"] .menu-brand {
        gap: 8px !important;
    }

    html body section[data-testid="stSidebar"] .menu-icon,
    html body section[data-testid="stSidebar"] .menu-icon-img {
        flex-basis: 43px !important;
        width: 43px !important;
        max-width: 43px !important;
    }

    /* 2) La página principal comienza exactamente al lado del menú fijo. */
    html body [data-testid="stAppViewContainer"] {
        display: block !important;
        width: 100vw !important;
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }

    html body [data-testid="stAppViewContainer"] > section[data-testid="stMain"],
    html body [data-testid="stAppViewContainer"] > .main {
        margin-left: var(--sidebar-final-width) !important;
        width: calc(100vw - var(--sidebar-final-width)) !important;
        max-width: calc(100vw - var(--sidebar-final-width)) !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
        position: relative !important;
    }

    /* Evita doble desplazamiento en elementos main internos. */
    html body [data-testid="stAppViewContainer"] > section[data-testid="stMain"] main,
    html body [data-testid="stAppViewContainer"] > section[data-testid="stMain"] section.main,
    html body [data-testid="stAppViewContainer"] > .main main {
        margin-left: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
    }

    /* El dashboard se adapta al ancho útil en vez de conservar mínimos antiguos. */
    html body [data-testid="stAppViewContainer"] > section[data-testid="stMain"] .block-container,
    html body [data-testid="stAppViewContainer"] > .main .block-container {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        padding-left: 16px !important;
        padding-right: 16px !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    /* Footer y versión alineados con el nuevo ancho. */
    html body section[data-testid="stSidebar"] .sidebar-credit-footer {
        left: 13px !important;
        width: var(--sidebar-final-inner) !important;
        max-width: var(--sidebar-final-inner) !important;
        font-size: 9.6px !important;
    }

    html body section[data-testid="stSidebar"] .menu-footer-box {
        left: calc(var(--sidebar-final-width) / 2) !important;
        max-width: calc(var(--sidebar-final-inner) - 12px) !important;
    }
}

/* El sello de agua también respeta el ancho definitivo del menú. */
[data-testid="stAppViewContainer"]::after {
    left: var(--sidebar-final-width) !important;
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE DEFINITIVO V2.6 - CONTENIDO PRINCIPAL FUERA DEL SIDEBAR
# - No depende de que stMain sea hijo directo de stAppViewContainer.
# - Reserva físicamente el ancho del menú dentro del área principal.
# - Evita que títulos, filtros, KPI, gráficos y tablas queden ocultos
#   detrás del sidebar fijo al cambiar resolución o zoom del navegador.
# =========================================================
st.markdown(
    """
<style>
:root {
    --sidebar-final-width: 230px !important;
    --sidebar-final-inner: 204px !important;
    --main-edge-gap: 16px !important;
}

@media screen and (min-width: 1101px) {
    /* Sidebar fijo y con un único ancho de referencia. */
    html body section[data-testid="stSidebar"] {
        position: fixed !important;
        inset: 0 auto 0 0 !important;
        width: var(--sidebar-final-width) !important;
        min-width: var(--sidebar-final-width) !important;
        max-width: var(--sidebar-final-width) !important;
        box-sizing: border-box !important;
        z-index: 10000 !important;
    }

    /*
       Corrección clave:
       stMain conserva el ancho total del viewport, pero reserva a la izquierda
       exactamente el espacio ocupado por el menú. Así ningún elemento del
       dashboard puede comenzar debajo del sidebar, incluso si cambia el DOM
       interno de Streamlit.
    */
    html body section[data-testid="stMain"],
    html body div[data-testid="stMain"] {
        margin-left: 0 !important;
        margin-right: 0 !important;
        padding-left: var(--sidebar-final-width) !important;
        width: 100vw !important;
        min-width: 0 !important;
        max-width: 100vw !important;
        box-sizing: border-box !important;
        position: relative !important;
        left: 0 !important;
        right: auto !important;
        transform: none !important;
        overflow-x: hidden !important;
    }

    /* La zona útil del dashboard ocupa solo el espacio a la derecha. */
    html body div[data-testid="stMainBlockContainer"],
    html body section[data-testid="stMain"] div[data-testid="stMainBlockContainer"],
    html body section[data-testid="stMain"] .stMainBlockContainer,
    html body section[data-testid="stMain"] .block-container,
    html body div[data-testid="stMain"] .block-container {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        padding-left: var(--main-edge-gap) !important;
        padding-right: var(--main-edge-gap) !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    /* Anula desplazamientos antiguos que podían volver a meter el contenido debajo. */
    html body section[data-testid="stMain"] main,
    html body section[data-testid="stMain"] section.main,
    html body section[data-testid="stMain"] .main,
    html body div[data-testid="stMain"] main,
    html body div[data-testid="stMain"] section.main,
    html body div[data-testid="stMain"] .main {
        margin-left: 0 !important;
        padding-left: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    /* Los bloques horizontales pueden reducirse sin forzar solapamiento. */
    html body section[data-testid="stMain"] [data-testid="stHorizontalBlock"],
    html body div[data-testid="stMain"] [data-testid="stHorizontalBlock"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    /* Gráficos/tablas siempre dentro del ancho útil. */
    html body section[data-testid="stMain"] [data-testid="stPlotlyChart"],
    html body section[data-testid="stMain"] [data-testid="stDataFrame"],
    html body div[data-testid="stMain"] [data-testid="stPlotlyChart"],
    html body div[data-testid="stMain"] [data-testid="stDataFrame"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }
}

/* El sello de agua parte después del menú, igual que el contenido. */
[data-testid="stAppViewContainer"]::after {
    left: var(--sidebar-final-width) !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# AJUSTE FINAL V2.8 - CONTENIDO MÁS ARRIBA EN TODAS LAS PÁGINAS
# - Reduce el espacio vacío sobre el encabezado principal.
# - Aplica por igual a Resumen Ejecutivo, Equipos, Intervenciones y Documentación.
# - Se declara al final para prevalecer sobre ajustes visuales anteriores.
# =========================================================
st.markdown(
    """
<style>
@media screen and (min-width: 1101px) {
    html body div[data-testid="stMainBlockContainer"],
    html body section[data-testid="stMain"] div[data-testid="stMainBlockContainer"],
    html body section[data-testid="stMain"] .stMainBlockContainer,
    html body section[data-testid="stMain"] .block-container,
    html body div[data-testid="stMain"] .block-container {
        margin-top: -185px !important;
        padding-top: 0 !important;
    }

    html body .main-fixed-header {
        min-height: 38px !important;
        height: 38px !important;
        margin-top: 0 !important;
        margin-bottom: 4px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        align-items: flex-end !important;
    }

    html body .main-fixed-header-spacer,
    html body .header-separador {
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# AJUSTE FINAL V3.0 - POSICIÓN SUPERIOR AJUSTADA EN TODAS LAS PÁGINAS
# - Baja levemente el bloque principal respecto del ajuste anterior, manteniéndolo compacto.
# - Aplica a Resumen Ejecutivo, Equipos, Intervenciones y Documentación.
# - Se declara al final para anular márgenes/paddings heredados de Streamlit.
# =========================================================
st.markdown(
    """
<style>
@media screen and (min-width: 1101px) {
    html body div[data-testid="stMainBlockContainer"],
    html body section[data-testid="stMain"] div[data-testid="stMainBlockContainer"],
    html body [data-testid="stAppViewContainer"] div[data-testid="stMainBlockContainer"] {
        position: relative !important;
        top: -110px !important;
        transform: none !important;
        margin-top: 0 !important;
        margin-bottom: -110px !important;
        padding-top: 0 !important;
        padding-bottom: 0.25rem !important;
    }

    html body .main-fixed-header {
        margin-top: 0 !important;
        margin-bottom: 3px !important;
        min-height: 40px !important;
        height: 40px !important;
        padding: 0 10px 0 0 !important;
        align-items: flex-end !important;
    }

    html body .main-fixed-header-spacer,
    html body .header-separador {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# AJUSTE FINAL V3.1 - AIRE ENTRE TÍTULO Y FILTROS
# - Agrega una separación visual mínima entre el encabezado de cada página
#   y la primera fila de filtros/contenido.
# - Aplica a Resumen Ejecutivo, Equipos, Intervenciones y Documentación.
# =========================================================
st.markdown(
    """
<style>
@media screen and (min-width: 1101px) {
    html body .main-fixed-header {
        margin-bottom: 12px !important;
    }

    /* Pequeño aire adicional antes de las etiquetas de los filtros. */
    html body div[data-testid="stMain"] div[data-testid="stSelectbox"] > label,
    html body section[data-testid="stMain"] div[data-testid="stSelectbox"] > label {
        margin-top: 1px !important;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# AJUSTE FINAL V3.2 - VERSIÓN COMPACTA SIN RECUADRO
# - Actualiza la versión visible a 2.9.
# - Elimina borde, fondo y sombra del indicador de versión.
# - Reduce tipografía y espaciado para dejarlo discreto.
# =========================================================
st.markdown(
    """
<style>
html body section[data-testid="stSidebar"] .menu-footer-box {
    background: transparent !important;
    background-color: transparent !important;
    border: 0 !important;
    outline: 0 !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    min-height: 0 !important;
    height: auto !important;
}

html body section[data-testid="stSidebar"] .menu-footer-box .menu-info,
html body section[data-testid="stSidebar"] .menu-footer-box .menu-info * {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
    font-size: 10px !important;
    line-height: 1.1 !important;
    font-weight: 650 !important;
    color: #93c5fd !important;
    -webkit-text-fill-color: #93c5fd !important;
    padding: 0 !important;
    margin: 0 !important;
}
</style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# EJECUCIÓN FINAL
# Se deja deliberadamente al final del archivo para que todo el CSS esté
# cargado antes de dibujar el dashboard. Evita el efecto de "acomodarse"
# o cambiar de ancho después del primer render.
# =========================================================
try:
    mostrar_panel()
except FileNotFoundError:
    st.error("No se pudo cargar la información desde Google Sheets.")
    st.info(
        "Revisa que el Google Sheets esté compartido como 'Cualquier persona con el enlace - Lector' "
        "y que las pestañas requeridas mantengan sus nombres originales."
    )
    st.code(GOOGLE_SHEET_URL)
except Exception as error:
    st.error("Ocurrió un error al cargar o procesar la información.")
    st.exception(error)


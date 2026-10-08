# app.py
# Dashboard ejecutivo · Óptica COALIVI
# Elaborado por MDF Consulting para la Dirección Ejecutiva de COALIVI (2026)
#
# Para correrlo en el computador:  streamlit run app.py

import base64
import glob
import io
import os
import zipfile

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

import procesamiento as pr


# =============================================================================
# 1. Configuración general y colores COALIVI
# =============================================================================
CARPETA_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_LOGO = os.path.join(CARPETA_APP, 'logo.png')

st.set_page_config(page_title='Dashboard Ejecutivo · Óptica COALIVI',
                   page_icon=RUTA_LOGO if os.path.exists(RUTA_LOGO) else '👓',
                   layout='wide', initial_sidebar_state='expanded')

AZUL = '#1A4474'        # azul institucional COALIVI
NARANJO = '#FA9219'     # naranjo institucional COALIVI
AZUL_SUAVE = '#A9B8CE'  # para el "año anterior" en las comparaciones
TINTA = '#1F2A44'
GRIS = '#6B7385'
GRILLA = '#E6E9EF'

# Paleta para categorías (validada para daltonismo, en este orden)
SERIES = ['#2F6DB5', '#F08C1A', '#1BAF7A', '#7B6FD6', '#E87BA4', '#EDA100']

# Colores fijos por entidad: cada línea / segmento / proveedor tiene siempre el mismo color
COLOR_LINEA = dict(zip(pr.LINEAS, SERIES))
COLOR_PROVEEDOR = {'TEKNOL': SERIES[0], 'MERCAVISION': SERIES[1], 'MEGALUX': SERIES[2],
                   'ITALOPTIC': SERIES[3], 'RODENSTOCK': SERIES[4], 'PEDIDO URGENTE': SERIES[5]}
COLOR_FAMILIA = {'Cristal': SERIES[0], 'Armazón': SERIES[1], 'Gafas': SERIES[2], 'Accesorio': SERIES[3]}

# Semáforo: solo para metas, siempre con texto (nunca solo color)
SEMAFORO = {'Cumple': ('#0CA30C', 'white'), 'En riesgo': ('#FAB219', TINTA),
            'No cumple': ('#D03B3B', 'white'), 'Sin dato': ('#C3C8D4', TINTA)}
ROJO = '#D03B3B'

MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

# Plantilla de Plotly con la identidad de COALIVI
pio.templates['coalivi'] = go.layout.Template(layout=dict(
    font=dict(family='Inter, Segoe UI, system-ui, sans-serif', size=13, color=TINTA),
    paper_bgcolor='white', plot_bgcolor='white',
    colorway=SERIES,
    separators=',.',                       # 1.234.567,8 (formato chileno)
    margin=dict(l=10, r=10, t=40, b=10),
    title=dict(font=dict(size=15, color=AZUL), x=0, xanchor='left'),
    xaxis=dict(showgrid=False, linecolor='#C3C8D4', ticks='', title=dict(font=dict(color=GRIS))),
    yaxis=dict(gridcolor=GRILLA, zeroline=False, linecolor='#C3C8D4', title=dict(font=dict(color=GRIS))),
    legend=dict(orientation='h', yanchor='bottom', y=1.0, xanchor='right', x=1, title=dict(text='')),
    hoverlabel=dict(bgcolor='white', bordercolor=AZUL, font=dict(color=TINTA)),
    bargap=0.25,
))
pio.templates.default = 'coalivi'


# =============================================================================
# 2. Estilo visual (CSS)
# =============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', 'Segoe UI', sans-serif; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }}

/* Encabezado */
.encabezado {{ background: linear-gradient(90deg, {AZUL} 0%, #24578F 100%);
  border-bottom: 5px solid {NARANJO}; border-radius: 14px; padding: 18px 26px; margin-bottom: 16px;
  display: flex; align-items: center; gap: 22px; }}
.encabezado img {{ height: 84px; width: 84px; }}
.encabezado h1 {{ color: white; font-size: 1.75rem; font-weight: 700; margin: 0; padding: 0; }}
.encabezado p {{ color: #D9E2EF; margin: 4px 0 0 0; font-size: 0.92rem; }}
.encabezado .marca {{ color: {NARANJO}; font-weight: 700; letter-spacing: 1px; font-size: 0.78rem; }}

/* Tarjetas KPI */
.kpi {{ background: white; border-radius: 12px; padding: 14px 16px 12px 16px;
  border-left: 5px solid {NARANJO}; box-shadow: 0 1px 3px rgba(26,68,116,0.12); min-height: 128px; }}
.kpi-t {{ color: {GRIS}; font-size: 0.76rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; }}
.kpi-v {{ color: {AZUL}; font-size: 1.6rem; font-weight: 700; line-height: 1.25; margin-top: 2px; }}
.kpi-d {{ font-size: 0.8rem; font-weight: 600; margin-top: 2px; }}
.kpi-d span {{ color: {GRIS}; font-weight: 400; }}
.kpi-m {{ font-size: 0.75rem; color: {GRIS}; margin-top: 6px; }}
.sube {{ color: #0A7A0A; }}  .baja {{ color: {ROJO}; }}  .neutro {{ color: {GRIS}; }}
.chip {{ display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;
  margin-right: 6px; white-space: nowrap; }}

/* Títulos de sección */
.seccion {{ color: {AZUL}; font-size: 1.1rem; font-weight: 700; border-left: 4px solid {NARANJO};
  padding-left: 10px; margin: 22px 0 6px 0; }}
.subtitulo {{ color: {GRIS}; font-size: 0.85rem; margin: -2px 0 8px 14px; }}

/* Caja de hallazgos y nota de método */
.hallazgos {{ background: #FFF6EA; border: 1px solid #F8D3A0; border-radius: 12px; padding: 14px 20px; }}
.hallazgos h4 {{ color: {AZUL}; margin: 0 0 6px 0; font-size: 1rem; }}
.hallazgos li {{ margin-bottom: 4px; color: {TINTA}; font-size: 0.92rem; }}
.nota {{ background: #EEF3FA; border-left: 4px solid {AZUL}; border-radius: 8px; padding: 10px 14px;
  font-size: 0.85rem; color: {TINTA}; margin: 6px 0 12px 0; }}

/* Tablas ejecutivas */
.tabla {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; background: white; }}
.tabla th {{ background: {AZUL}; color: white; text-align: right; padding: 8px 10px; font-weight: 600; }}
.tabla th:first-child, .tabla td:first-child {{ text-align: left; }}
.tabla td {{ border-bottom: 1px solid {GRILLA}; padding: 7px 10px; color: {TINTA}; text-align: right; }}
.tabla tr.total td {{ font-weight: 700; border-top: 2px solid {AZUL}; background: #F4F6FA; }}
.tabla td.neg {{ color: {ROJO}; }}

/* Pestañas */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 2px solid {GRILLA}; }}
.stTabs [data-baseweb="tab"] {{ padding: 8px 16px; font-weight: 600; color: {AZUL}; }}

/* Barra lateral */
[data-testid="stSidebar"] .logo {{ text-align: center; margin-bottom: 6px; }}
[data-testid="stSidebar"] .logo img {{ width: 110px; }}
[data-testid="stSidebar"] .logo-texto {{ background: {AZUL}; color: white; border-radius: 10px; padding: 14px;
  text-align: center; border-bottom: 4px solid {NARANJO}; font-weight: 700; letter-spacing: 2px; }}
.pie {{ color: {GRIS}; font-size: 0.8rem; text-align: center; margin-top: 30px; }}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 3. Funciones de formato y de dibujo
# =============================================================================
def miles(x, dec=0):
    # 1234567.8 -> '1.234.568' (separador de miles chileno)
    if x is None or pd.isna(x):
        return '–'
    texto = f'{x:,.{dec}f}'
    return texto.replace(',', 'X').replace('.', ',').replace('X', '.')


def etiqueta_mes(fechas):
    # 2025-03-01 -> 'Mar 25' (meses en español para los ejes)
    return fechas.dt.month.map(lambda m: MESES[int(m) - 1]) + ' ' + fechas.dt.strftime('%y')


def clp(x):
    return '–' if x is None or pd.isna(x) else ('-$' if x < 0 else '$') + miles(abs(x))


def mm(x):
    # Montos grandes en millones: $245,3 MM
    if x is None or pd.isna(x):
        return '–'
    signo = '-' if x < 0 else ''
    return signo + '$' + miles(abs(x) / 1e6, 1) + ' MM' if abs(x) >= 1e6 else clp(x)


def pct(x, dec=1):
    return '–' if x is None or pd.isna(x) else miles(x, dec) + '%'


def variacion(actual, anterior):
    # Variación porcentual; None si no hay base de comparación
    if anterior is None or pd.isna(anterior) or anterior == 0 or actual is None or pd.isna(actual):
        return None
    return 100 * (actual - anterior) / abs(anterior)   # abs: sirve también si el año anterior fue negativo


def estado_meta(valor, meta, mayor_es_mejor=True):
    # Semáforo: Cumple / En riesgo (a menos de 10% de la meta) / No cumple
    if meta is None or valor is None or pd.isna(valor):
        return 'Sin dato'
    holgura = max(abs(meta) * 0.10, 1)
    brecha = (valor - meta) if mayor_es_mejor else (meta - valor)
    if brecha >= 0:
        return 'Cumple'
    return 'En riesgo' if brecha >= -holgura else 'No cumple'


def chip(estado, texto=None):
    fondo, letra = SEMAFORO[estado]
    return f'<span class="chip" style="background:{fondo};color:{letra}">● {texto or estado}</span>'


def tarjeta(titulo, valor, delta=None, comparado='', invertir=False, puntos=False, meta=None):
    # Tarjeta KPI en HTML.
    # invertir = True cuando subir es malo (ej. % de errores); puntos = delta en puntos porcentuales
    # meta = (estado, texto) para mostrar el semáforo
    if delta is None:
        linea = f'<div class="kpi-d neutro">{comparado}</div>' if comparado else '<div class="kpi-d">&nbsp;</div>'
    else:
        bueno = (delta >= 0) != invertir
        clase = 'neutro' if abs(delta) < 0.05 else ('sube' if bueno else 'baja')
        flecha = '▲' if delta > 0 else ('▼' if delta < 0 else '●')
        unidad = ' pp' if puntos else '%'
        linea = (f'<div class="kpi-d {clase}">{flecha} {miles(abs(delta), 1)}{unidad} '
                 f'<span>{comparado}</span></div>')
    pie = f'<div class="kpi-m">{chip(meta[0])}{meta[1]}</div>' if meta else ''
    return (f'<div class="kpi"><div class="kpi-t">{titulo}</div><div class="kpi-v">{valor}</div>'
            f'{linea}{pie}</div>')


def fila_kpi(tarjetas):
    columnas = st.columns(len(tarjetas), gap='small')
    for col, html in zip(columnas, tarjetas):
        col.markdown(html, unsafe_allow_html=True)


def seccion(texto, sub=''):
    st.markdown(f'<div class="seccion">{texto}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="subtitulo">{sub}</div>', unsafe_allow_html=True)


def nota(texto):
    st.markdown(f'<div class="nota">{texto}</div>', unsafe_allow_html=True)


def mostrar(fig, alto=360):
    fig.update_layout(height=alto)
    st.plotly_chart(fig, config={'displaylogo': False})


def sin_datos(texto='No hay datos para el período seleccionado.'):
    st.info(texto)


def barras_h(df, x, y, titulo, color=AZUL, formato='$', alto=360, etiqueta=None):
    # Barras horizontales de una sola serie (un solo color), ordenadas de mayor a menor
    df = df.sort_values(x)
    fig = px.bar(df, x=x, y=y, orientation='h', title=titulo)
    fig.update_traces(marker_color=color, marker_line_width=0)
    if etiqueta is not None:
        fig.update_traces(text=df[etiqueta], textposition='outside', cliponaxis=False)
    plantilla = '%{y}<br>' + ('$%{x:,.0f}' if formato == '$' else '%{x:,.1f}' + formato) + '<extra></extra>'
    fig.update_traces(hovertemplate=plantilla)
    fig.update_layout(xaxis_title=None, yaxis_title=None,
                      xaxis=dict(showticklabels=etiqueta is None, gridcolor=GRILLA, showgrid=True))
    mostrar(fig, alto)


def actual_vs_anterior(df, x, y, nombre_act, nombre_ant, titulo, formato='$', alto=360):
    # Barras agrupadas: período actual (azul COALIVI) vs mismo período del año anterior
    fig = px.bar(df, x=x, y=y, color='Período', barmode='group', title=titulo,
                 color_discrete_map={nombre_act: AZUL, nombre_ant: AZUL_SUAVE},
                 category_orders={'Período': [nombre_ant, nombre_act]})
    valor = '$%{y:,.0f}' if formato == '$' else '%{y:,.0f}' + formato
    fig.update_traces(hovertemplate='%{x}<br>' + valor + '<extra>%{fullData.name}</extra>',
                      marker_line_width=0)
    fig.update_layout(xaxis_title=None, yaxis_title=None)
    mostrar(fig, alto)


def tabla_html(df, con_total=False, negativas=()):
    # Tabla ejecutiva en HTML. Si con_total=True, la última fila se destaca como total
    cab = ''.join(f'<th>{c}</th>' for c in df.columns)
    filas = ''
    for i, (_, fila) in enumerate(df.iterrows()):
        clase = ' class="total"' if con_total and i == len(df) - 1 else ''
        celdas = ''
        for c in df.columns:
            valor = fila[c]
            neg = ' class="neg"' if c in negativas and str(valor).startswith('-') else ''
            celdas += f'<td{neg}>{valor}</td>'
        filas += f'<tr{clase}>{celdas}</tr>'
    st.markdown(f'<table class="tabla"><tr>{cab}</tr>{filas}</table>', unsafe_allow_html=True)


def logo_base64():
    if os.path.exists(RUTA_LOGO):
        with open(RUTA_LOGO, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None


# =============================================================================
# 4. Carga de datos
# =============================================================================
@st.cache_data(show_spinner='Cargando datos de COALIVI...')
def cargar_repositorio():
    # Lee las tablas limpias (.csv.gz) que vienen en el repositorio.
    # Las busca en data/, en la carpeta principal o en cualquier subcarpeta,
    # por si al subir a GitHub la carpeta data/ quedó con otro nombre o se aplanó.
    tablas = {}
    for clave in pr.FECHAS:
        encontrados = sorted(glob.glob(os.path.join(CARPETA_APP, '**', f'{clave}.csv.gz'), recursive=True))
        if encontrados:
            tablas[clave] = pr.leer_tabla(encontrados[0], clave)

    # Si se subió el .zip tal cual a GitHub, se leen las tablas desde adentro del zip
    for ruta_zip in glob.glob(os.path.join(CARPETA_APP, '**', '*.zip'), recursive=True):
        with zipfile.ZipFile(ruta_zip) as z:
            for nombre in z.namelist():
                clave = os.path.basename(nombre).replace('.csv.gz', '')
                if nombre.endswith('.csv.gz') and clave in pr.FECHAS and clave not in tablas:
                    tablas[clave] = pr.leer_tabla(io.BytesIO(z.read(nombre)), clave)
    return tablas


@st.cache_data(show_spinner='Procesando planilla subida...')
def procesar_subida(nombre, contenido):
    # Limpia una planilla original subida desde la barra lateral
    return pr.procesar_archivo(contenido, nombre)


datos = cargar_repositorio()
origen_datos = {clave: 'Repositorio' for clave in datos}
LOGO = logo_base64()

# ---- Barra lateral: logo y carga de archivos
with st.sidebar:
    if LOGO:
        st.markdown(f'<div class="logo"><img src="data:image/png;base64,{LOGO}"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="logo-texto">COALIVI</div>', unsafe_allow_html=True)

    with st.expander('Cargar / actualizar bases de datos', expanded=not datos):
        st.caption('Sube las planillas originales (.xlsx) tal como las entrega TI. '
                   'Se reconocen por sus columnas (aunque el archivo tenga otro nombre) y '
                   'reemplazan a las del repositorio mientras la página esté abierta.')
        subidos = st.file_uploader('Planillas Excel', type=['xlsx'],
                                   accept_multiple_files=True, label_visibility='collapsed')
        for archivo in subidos or []:
            try:
                clave, tabla = procesar_subida(archivo.name, archivo.getvalue())
                datos[clave] = tabla
                origen_datos[clave] = f'Subido: {archivo.name}'
                st.success(f'{pr.BASES[clave]["nombre"]}: {miles(len(tabla))} filas')
            except Exception as error:
                st.warning(f'{archivo.name}: {error}')

if 'ventas' not in datos:
    st.markdown('<div class="encabezado"><div><span class="marca">ÓPTICA COALIVI · MDF CONSULTING</span>'
                '<h1>Dashboard Ejecutivo</h1><p>Sube las planillas en la barra lateral para comenzar.</p>'
                '</div></div>', unsafe_allow_html=True)
    st.warning('No se encontraron los datos en el repositorio. Revisa en GitHub que exista la '
               'carpeta **data/** con los archivos .csv.gz (ventas.csv.gz, ot_sala.csv.gz, ...). '
               'Mientras tanto, puedes subir las planillas originales en la barra lateral.')
    st.stop()

# Tablas vacías para las bases que no estén cargadas (así la app no se cae)
for clave in pr.FECHAS:
    if clave not in datos:
        datos[clave] = pd.DataFrame()
        origen_datos[clave] = 'No cargada'

ventas = datos['ventas'].copy()
ventas['linea'] = ventas['tipo'].apply(pr.linea_producto)
ot_sala = datos['ot_sala']
ot_conv = datos['ot_convenio']
pedidos = datos['pedidos']
costos = datos['costos']
inventario = datos['inventario']
convenios = datos['convenios']

# ---- Filtros de período, supuestos financieros y metas
fecha_max = ventas['fecha'].max()
anios = sorted(ventas['anio'].dropna().unique().tolist(), reverse=True)

with st.sidebar:
    st.markdown('**Período de análisis**')
    anio = st.selectbox('Año', anios, index=0)
    mes_ini, mes_fin = st.select_slider('Meses', options=MESES, value=(MESES[0], MESES[-1]))
    st.caption('Todo se compara con el **mismo tramo del año anterior**.')

    with st.expander('Supuestos financieros'):
        st.caption('Gastos operacionales **mensuales** de la óptica. Son supuestos de MDF Consulting: '
                   'reemplazarlos por las cifras reales de COALIVI.')
        gasto_rem = st.number_input('Remuneraciones equipo óptica', min_value=0, value=4_500_000, step=100_000)
        gasto_arr = st.number_input('Arriendo y gastos comunes', min_value=0, value=1_200_000, step=100_000)
        gasto_ser = st.number_input('Servicios, sistemas y comunicaciones', min_value=0, value=600_000, step=50_000)
        gasto_mkt = st.number_input('Marketing y difusión', min_value=0, value=300_000, step=50_000)
        gasto_otr = st.number_input('Otros gastos de administración', min_value=0, value=500_000, step=50_000)
        con_iva = st.checkbox('Los precios de venta incluyen IVA (19%)', value=True)

    with st.expander('Metas'):
        meta_crec = st.number_input('Crecimiento de ingresos vs año anterior (%)', value=5.0, step=1.0)
        meta_md = st.number_input('Margen directo mínimo (%)', value=65.0, step=1.0)
        meta_mo = st.number_input('Margen operacional mínimo (%)', value=20.0, step=1.0)
        meta_lt = st.number_input('Plazo de entrega máximo (días, mediana)', value=10.0, step=1.0)
        meta_atr = st.number_input('Entregas fuera de plazo máximo (%)', value=10.0, step=1.0)
        meta_err = st.number_input('Venta con OT mal registrada máximo (%)', value=2.0, step=0.5)
        meta_urg = st.number_input('Pedidos de cristal urgentes máximo (%)', value=5.0, step=0.5)

GASTO_MENSUAL = gasto_rem + gasto_arr + gasto_ser + gasto_mkt + gasto_otr
FACTOR_IVA = 1.19 if con_iva else 1.0

i1, i2 = MESES.index(mes_ini) + 1, MESES.index(mes_fin) + 1
ini = pd.Timestamp(int(anio), i1, 1)
fin = pd.Timestamp(int(anio), i2, 1) + pd.offsets.MonthEnd(0)
if ini <= fecha_max < fin:
    fin = fecha_max                        # el año en curso se corta en el último dato
ini_ant = ini - pd.DateOffset(years=1)
fin_ant = fin - pd.DateOffset(years=1)
MESES_PERIODO = ((fin - ini).days + 1) / 30.44   # meses del período (para los gastos)
MESES_RANGO = range(i1, fin.month + 1)            # meses con datos (para los gráficos mensuales)

ACT, ANT = str(int(anio)), str(int(anio) - 1)
COMPARADO = f'vs mismo tramo {ANT}'


def periodo(df, anterior=False, col='fecha'):
    # Filtra una tabla al período elegido (o al mismo tramo del año anterior)
    if df.empty or col not in df.columns:
        return df
    a, b = (ini_ant, fin_ant) if anterior else (ini, fin)
    return df[(df[col] >= a) & (df[col] <= b)]


with st.sidebar:
    st.caption(f'Período: {ini:%d-%m-%Y} al {fin:%d-%m-%Y}')
    st.markdown('<div class="pie">Elaborado por <b>MDF Consulting</b><br>'
                'Ingeniería Civil Industrial · UDD · 2026</div>', unsafe_allow_html=True)

# Tablas del período actual y del anterior
v_act, v_ant = periodo(ventas), periodo(ventas, True)
if v_act.empty:
    st.warning(f'No hay ventas registradas entre {ini:%d-%m-%Y} y {fin:%d-%m-%Y}. '
               'Cambia el año o los meses en la barra lateral.')
    st.stop()
s_act, s_ant = periodo(ot_sala), periodo(ot_sala, True)
c_act, c_ant = periodo(ot_conv), periodo(ot_conv, True)
p_act, p_ant = periodo(pedidos), periodo(pedidos, True)

# Si no hay ventas el año anterior (ej. 2024 es el primer año), no se compara nada
if v_ant.empty:
    s_ant, c_ant, p_ant = s_ant.iloc[0:0], c_ant.iloc[0:0], p_ant.iloc[0:0]
    COMPARADO = f'sin datos de {ANT} para comparar'


# =============================================================================
# 5. Estado de resultados por línea de producto
# =============================================================================
def porcentaje_costo():
    # % de costo directo sobre el precio de venta, por línea, según el informe de costos.
    # Las líneas sin datos propios usan el promedio general.
    if not costos.empty:
        ok = costos[costos['costeable']].copy()
        ok['linea'] = ok['familia'].apply(
            lambda f: pr.FAMILIA_A_LINEA.get(pr.sin_tildes(f), 'Reparaciones y otros'))
        general = ok['costo'].sum() / ok['venta'].sum() if ok['venta'].sum() else 0.30
        por_linea = ok.groupby('linea').agg(venta=('venta', 'sum'), costo=('costo', 'sum'), n=('venta', 'size'))
    else:
        general, por_linea = 0.30, pd.DataFrame(columns=['venta', 'costo', 'n'])
    filas = []
    for linea in pr.LINEAS:
        if linea in por_linea.index and por_linea.loc[linea, 'venta'] > 0:
            r = por_linea.loc[linea]
            filas.append({'linea': linea, 'pct_costo': r['costo'] / r['venta'],
                          'fuente': f'Informe de costos ({miles(r["n"])} líneas)'})
        else:
            filas.append({'linea': linea, 'pct_costo': general, 'fuente': 'Promedio general (sin datos propios)'})
    return pd.DataFrame(filas).set_index('linea')


PCT_COSTO = porcentaje_costo()


def estado_resultados(v, meses):
    # Ingresos netos, costo directo, margen directo, gastos operacionales y margen operacional por línea
    bruto = v.groupby('linea')['total'].sum().reindex(pr.LINEAS, fill_value=0)
    er = pd.DataFrame(index=pr.LINEAS)
    er['ingresos'] = bruto / FACTOR_IVA
    er['costo'] = bruto * PCT_COSTO['pct_costo']          # el % de costo es sobre el precio de venta
    er['margen_directo'] = er['ingresos'] - er['costo']
    total_ing = er['ingresos'].sum()
    participacion = er['ingresos'] / total_ing if total_ing else 0
    er['gastos'] = GASTO_MENSUAL * meses * participacion   # gastos repartidos según los ingresos
    er['margen_operacional'] = er['margen_directo'] - er['gastos']
    er.loc['Total'] = er.sum()
    er['pct_ingresos'] = 100 * er['ingresos'] / total_ing if total_ing else np.nan
    er['pct_md'] = 100 * er['margen_directo'] / er['ingresos'].replace(0, np.nan)
    er['pct_mo'] = 100 * er['margen_operacional'] / er['ingresos'].replace(0, np.nan)
    return er


ER_ACT = estado_resultados(v_act, MESES_PERIODO)
ER_ANT = estado_resultados(v_ant, MESES_PERIODO)
TOT, TOT_ANT = ER_ACT.loc['Total'], ER_ANT.loc['Total']


# =============================================================================
# 6. Indicadores comunes y metas
# =============================================================================
def resumen_ventas(v):
    venta = v['total'].sum()
    boletas = v['folio'].nunique()
    return venta, boletas, (venta / boletas if boletas else np.nan)


def unidades(v):
    # Una venta a crédito se boletea en dos líneas (abono + saldo) con la misma cantidad,
    # así que las unidades se cuentan sin las líneas de saldo
    return v.loc[v['clase_linea'] != 'Saldo', 'cantidad'].sum()


def pct_error(v):
    # % del monto facturado cuya OT está mal o no registrada
    total = v['total'].sum() if not v.empty else 0
    return 100 * v.loc[v['estado_ot'] != 'Registrada', 'total'].sum() / total if total else np.nan


def ticket_ot(s):
    con_valor = s[s['total'] > 0]['total'] if not s.empty else pd.Series(dtype=float)
    return con_valor.mean() if len(con_valor) else np.nan


def pct_atraso(s):
    n = s['atraso'].notna().sum() if not s.empty else 0
    return 100 * (s['atraso'] > 0).sum() / n if n else np.nan


venta_act, boletas_act, ticket_act = resumen_ventas(v_act)
venta_ant, boletas_ant, ticket_ant = resumen_ventas(v_ant)
lt_act = s_act['lead_time'].median() if not s_act.empty else np.nan
lt_ant = s_ant['lead_time'].median() if not s_ant.empty else np.nan
err_act, err_ant = pct_error(v_act), pct_error(v_ant)
atr_act, atr_ant = pct_atraso(s_act), pct_atraso(s_ant)
urg_act = 100 * p_act['urgente'].mean() if not p_act.empty else np.nan
urg_ant = 100 * p_ant['urgente'].mean() if not p_ant.empty else np.nan
crec_ing = variacion(TOT['ingresos'], TOT_ANT['ingresos'])

# Cuadro de metas: (indicador, valor actual, valor anterior, unidad, meta, mayor_es_mejor)
METAS = [
    ('Crecimiento de ingresos', crec_ing, None, '%', meta_crec, True),
    ('Margen directo', TOT['pct_md'], TOT_ANT['pct_md'], '%', meta_md, True),
    ('Margen operacional', TOT['pct_mo'], TOT_ANT['pct_mo'], '%', meta_mo, True),
    ('Plazo de entrega (mediana)', lt_act, lt_ant, 'días', meta_lt, False),
    ('Entregas fuera de plazo', atr_act, atr_ant, '%', meta_atr, False),
    ('Venta con OT mal registrada', err_act, err_ant, '%', meta_err, False),
    ('Pedidos de cristal urgentes', urg_act, urg_ant, '%', meta_urg, False),
]


def texto_meta(meta, unidad, mayor_es_mejor):
    signo = '≥' if mayor_es_mejor else '≤'
    return f'meta {signo} ' + (pct(meta) if unidad == '%' else f'{miles(meta)} días')


def semaforo(nombre):
    # Devuelve (estado, texto de la meta) para mostrar en la tarjeta
    for n, valor, _, unidad, meta, mayor in METAS:
        if n == nombre:
            return estado_meta(valor, meta, mayor), texto_meta(meta, unidad, mayor)
    return None


def valor_meta(valor, unidad):
    return pct(valor) if unidad == '%' else ('–' if valor is None or pd.isna(valor) else f'{miles(valor)} días')


# =============================================================================
# 7. Reporte ejecutivo descargable (Excel)
# =============================================================================
def reporte_excel():
    from openpyxl.styles import Alignment, Font, PatternFill

    salida = io.BytesIO()
    with pd.ExcelWriter(salida, engine='openpyxl') as w:
        # Hoja 1: indicadores principales y cuadro de metas
        principales = pd.DataFrame([
            ['Ingresos netos ($)', TOT['ingresos'], TOT_ANT['ingresos'], '', ''],
            ['Margen directo ($)', TOT['margen_directo'], TOT_ANT['margen_directo'], '', ''],
            ['Margen operacional ($)', TOT['margen_operacional'], TOT_ANT['margen_operacional'], '', ''],
            ['OT sala de venta', len(s_act), len(s_ant), '', ''],
            ['Ticket promedio por OT ($)', ticket_ot(s_act), ticket_ot(s_ant), '', ''],
            ['OT convenio institucional', len(c_act), len(c_ant), '', ''],
        ] + [[f'{n} ({u})', valor, ant, meta, estado_meta(valor, meta, mayor)]
             for n, valor, ant, u, meta, mayor in METAS],
            columns=['Indicador', f'Actual ({ACT})', f'Mismo tramo {ANT}', 'Meta', 'Estado'])
        principales = principales.round(1)
        principales.to_excel(w, sheet_name='Resumen', startrow=4, index=False)

        # Hoja 2: estado de resultados por línea
        er = ER_ACT[['ingresos', 'pct_ingresos', 'costo', 'margen_directo', 'pct_md', 'gastos',
                     'margen_operacional', 'pct_mo']].reset_index()
        er.columns = ['Línea', 'Ingresos netos', '% de ingresos', 'Costo directo', 'Margen directo',
                      '% margen directo', 'Gastos operacionales', 'Margen operacional', '% margen operacional']
        er.round(1).to_excel(w, sheet_name='Resultados por línea', startrow=4, index=False)

        # Hoja 3: venta mensual
        vm = pd.DataFrame({'Mes': [MESES[m - 1] for m in MESES_RANGO],
                           f'Venta {ACT}': [v_act.loc[v_act['fecha'].dt.month == m, 'total'].sum() for m in MESES_RANGO],
                           f'Venta {ANT}': [v_ant.loc[v_ant['fecha'].dt.month == m, 'total'].sum() for m in MESES_RANGO]})
        vm.to_excel(w, sheet_name='Venta mensual', startrow=4, index=False)

        # Hoja 4: supuestos
        sup = pd.DataFrame({'Línea': PCT_COSTO.index, '% costo sobre precio': 100 * PCT_COSTO['pct_costo'].values,
                            'Fuente': PCT_COSTO['fuente'].values})
        sup.round(1).to_excel(w, sheet_name='Supuestos', startrow=4, index=False)
        gastos = pd.DataFrame({'Gasto operacional mensual': ['Remuneraciones', 'Arriendo y gastos comunes',
                                                             'Servicios y sistemas', 'Marketing', 'Otros', 'TOTAL'],
                               'Monto ($)': [gasto_rem, gasto_arr, gasto_ser, gasto_mkt, gasto_otr, GASTO_MENSUAL]})
        gastos.to_excel(w, sheet_name='Supuestos', startrow=len(sup) + 7, index=False)

        # Formato: título, encabezados azules, números y anchos de columna
        titulos = {'Resumen': 'Reporte ejecutivo · Óptica COALIVI',
                   'Resultados por línea': 'Estado de resultados por línea de producto (montos netos de IVA)',
                   'Venta mensual': 'Venta facturada mensual (con IVA)',
                   'Supuestos': 'Supuestos del cálculo de márgenes'}
        for hoja, titulo in titulos.items():
            ws = w.book[hoja]
            ws['A1'] = titulo
            ws['A1'].font = Font(bold=True, size=14, color='1A4474')
            ws['A2'] = f'Período {ini:%d-%m-%Y} al {fin:%d-%m-%Y} · comparado con el mismo tramo de {ANT}'
            ws['A3'] = f'Generado el {pd.Timestamp.today():%d-%m-%Y} · MDF Consulting'
            ws['A3'].font = Font(italic=True, color='6B7385')
            for fila in ws.iter_rows(min_row=6):
                for celda in fila:
                    if isinstance(celda.value, (int, float)):
                        celda.number_format = '#,##0' if abs(celda.value) >= 1000 else '#,##0.0'
            for fila_cab in (5, len(sup) + 8) if hoja == 'Supuestos' else (5,):
                for celda in ws[fila_cab]:
                    if celda.value is not None:
                        celda.fill = PatternFill('solid', fgColor='1A4474')
                        celda.font = Font(bold=True, color='FFFFFF')
                        celda.alignment = Alignment(horizontal='center', wrap_text=True)
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 20
            ws.column_dimensions['A'].width = 40
    return salida.getvalue()


# =============================================================================
# 8. Encabezado y pestañas
# =============================================================================
img_logo = f'<img src="data:image/png;base64,{LOGO}">' if LOGO else ''
st.markdown(f"""
<div class="encabezado">
  {img_logo}
  <div>
    <span class="marca">ÓPTICA COALIVI · CUADRO DE MANDO DE LA DIRECCIÓN EJECUTIVA</span>
    <h1>Dashboard Ejecutivo</h1>
    <p>Período {ini:%d-%m-%Y} al {fin:%d-%m-%Y} · comparado con el mismo tramo de {ANT} ·
       datos de ventas hasta el {fecha_max:%d-%m-%Y}</p>
  </div>
</div>""", unsafe_allow_html=True)

tabs = st.tabs(['Resumen ejecutivo', 'Resultados por línea', 'Comercial', 'Operaciones', 'Calidad de datos'])


# =============================================================================
# 9. Pestaña: Resumen ejecutivo
# =============================================================================
with tabs[0]:
    col_a, col_b = st.columns([4, 1])
    col_a.caption('Ingresos netos de IVA. Costo directo estimado con el informe de costos y gastos '
                  'operacionales según los supuestos de la barra lateral.')
    col_b.download_button('Descargar reporte (Excel)', reporte_excel(),
                          file_name=f'Reporte_COALIVI_{ini:%Y%m%d}_{fin:%Y%m%d}.xlsx',
                          mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                          key='reporte_resumen')

    fila_kpi([
        tarjeta('Ingresos netos', mm(TOT['ingresos']), crec_ing, COMPARADO,
                meta=semaforo('Crecimiento de ingresos')),
        tarjeta('Margen directo', pct(TOT['pct_md']), None, f'{mm(TOT["margen_directo"])} · estimado',
                meta=semaforo('Margen directo')),
        tarjeta('Margen operacional', pct(TOT['pct_mo']), None, f'{mm(TOT["margen_operacional"])} · estimado',
                meta=semaforo('Margen operacional')),
        tarjeta('Ticket promedio por OT', clp(ticket_ot(s_act)),
                variacion(ticket_ot(s_act), ticket_ot(s_ant)), COMPARADO),
    ])
    st.write('')
    fila_kpi([
        tarjeta('OT sala de venta', miles(len(s_act)), variacion(len(s_act), len(s_ant)), COMPARADO),
        tarjeta('OT convenio institucional', miles(len(c_act)), variacion(len(c_act), len(c_ant)), COMPARADO),
        tarjeta('Plazo de entrega (mediana)', f'{miles(lt_act)} días', variacion(lt_act, lt_ant), COMPARADO,
                invertir=True, meta=semaforo('Plazo de entrega (mediana)')),
        tarjeta('Venta con OT mal registrada', pct(err_act),
                None if pd.isna(err_ant) or pd.isna(err_act) else err_act - err_ant, COMPARADO,
                invertir=True, puntos=True, meta=semaforo('Venta con OT mal registrada')),
    ])

    col1, col2 = st.columns([3, 2], gap='medium')
    with col1:
        seccion('Del ingreso al margen operacional', f'período {ACT} · montos netos de IVA')
        pasos = ['Ingresos netos', 'Costo directo', 'Margen directo', 'Gastos operacionales', 'Margen operacional']
        valores = [TOT['ingresos'], -TOT['costo'], TOT['margen_directo'], -TOT['gastos'], TOT['margen_operacional']]
        fig = go.Figure(go.Waterfall(
            x=pasos, y=[valores[0], valores[1], 0, valores[3], 0],
            measure=['absolute', 'relative', 'total', 'relative', 'total'],
            text=[mm(x) for x in valores], textposition='outside',
            increasing=dict(marker=dict(color=AZUL)), decreasing=dict(marker=dict(color=NARANJO)),
            totals=dict(marker=dict(color=AZUL)), connector=dict(line=dict(color='#C3C8D4', width=1)),
            hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>'))
        tope = max(TOT['ingresos'], 1) * 1.15
        fig.update_layout(yaxis_title=None, showlegend=False,
                          yaxis_range=[min(0, TOT['margen_operacional'] * 1.3), tope])
        mostrar(fig, 360)
    with col2:
        seccion('Cuadro de metas', 'las metas se editan en la barra lateral')
        tabla_html(pd.DataFrame([{
            'Indicador': n,
            'Actual': valor_meta(valor, unidad),
            'Meta': texto_meta(meta, unidad, mayor).replace('meta ', ''),
            'Estado': chip(estado_meta(valor, meta, mayor)),
        } for n, valor, _, unidad, meta, mayor in METAS]))

    col1, col2 = st.columns([3, 2], gap='medium')
    with col1:
        seccion('Venta mensual', f'{ACT} contra el mismo mes de {ANT} (con IVA)')
        filas = []
        for m in MESES_RANGO:
            filas.append({'Mes': MESES[m - 1], 'Período': ACT,
                          'Venta': v_act.loc[v_act['fecha'].dt.month == m, 'total'].sum()})
            filas.append({'Mes': MESES[m - 1], 'Período': ANT,
                          'Venta': v_ant.loc[v_ant['fecha'].dt.month == m, 'total'].sum()})
        actual_vs_anterior(pd.DataFrame(filas), 'Mes', 'Venta', ACT, ANT, None, alto=340)

    with col2:
        # Hallazgos que se escriben solos según los datos del período
        puntos = []
        if crec_ing is not None:
            puntos.append(f'Los ingresos netos {"crecieron" if crec_ing >= 0 else "cayeron"} '
                          f'<b>{pct(abs(crec_ing))}</b> frente al mismo tramo de {ANT} '
                          f'({mm(TOT["ingresos"])} vs {mm(TOT_ANT["ingresos"])}).')
        er_l = ER_ACT.drop('Total')
        if er_l['ingresos'].sum() > 0:
            top = er_l['margen_directo'].idxmax()
            puntos.append(f'<b>{top}</b> genera el {pct(100 * er_l.loc[top, "margen_directo"] / TOT["margen_directo"])} '
                          f'del margen directo, con un margen de {pct(er_l.loc[top, "pct_md"])}.')
            negativas = er_l[(er_l['margen_operacional'] < 0) & (er_l['ingresos'] > 0)].index.tolist()
            if negativas:
                puntos.append(f'Con los supuestos de gastos, <b>{", ".join(negativas)}</b> no alcanza a cubrir '
                              f'sus gastos operacionales.')
        if not s_act.empty and not s_ant.empty:
            seg_a, seg_b = s_act['segmento'].value_counts(), s_ant['segmento'].value_counts()
            crec = ((seg_a - seg_b) / seg_b * 100).dropna()
            if not crec.empty:
                puntos.append(f'El segmento <b>{crec.idxmax()}</b> es el que más crece en OT ({pct(crec.max())}).')
        if not pd.isna(lt_act):
            puntos.append(f'Una OT demora <b>{miles(lt_act)} días</b> (mediana) en entregarse y el '
                          f'<b>{pct(atr_act)}</b> se entrega después de la fecha prometida.')
        if not pd.isna(err_act):
            puntos.append(f'El <b>{pct(err_act)}</b> del monto facturado tiene la OT mal o no registrada.')
        lista = ''.join(f'<li>{p}</li>' for p in puntos)
        st.markdown(f'<div class="hallazgos" style="margin-top:22px"><h4>Hallazgos clave del período</h4>'
                    f'<ul>{lista}</ul></div>', unsafe_allow_html=True)


# =============================================================================
# 10. Pestaña: Resultados por línea
# =============================================================================
with tabs[1]:
    nota('<b>Cómo se calcula.</b> Ingresos = venta de boletas sin IVA. Costo directo = % de costo de cada '
         'línea según el informe de costos (nov-2025 a jun-2026), aplicado a todo el período: es un '
         '<b>estimado</b>. Gastos operacionales = supuestos mensuales de la barra lateral, repartidos según '
         'la participación de cada línea en los ingresos.')

    fila_kpi([
        tarjeta('Ingresos netos', mm(TOT['ingresos']), crec_ing, COMPARADO,
                meta=semaforo('Crecimiento de ingresos')),
        tarjeta('Margen directo', mm(TOT['margen_directo']),
                variacion(TOT['margen_directo'], TOT_ANT['margen_directo']), COMPARADO,
                meta=semaforo('Margen directo')),
        tarjeta('Gastos operacionales', mm(TOT['gastos']), None,
                f'{clp(GASTO_MENSUAL)} al mes · supuesto'),
        tarjeta('Margen operacional', mm(TOT['margen_operacional']),
                variacion(TOT['margen_operacional'], TOT_ANT['margen_operacional']), COMPARADO,
                meta=semaforo('Margen operacional')),
    ])

    seccion('Estado de resultados por línea de producto', f'período {ACT} · montos netos de IVA')
    tabla_html(pd.DataFrame({
        'Línea': ER_ACT.index,
        'Ingresos netos': ER_ACT['ingresos'].apply(clp),
        '% del total': ER_ACT['pct_ingresos'].apply(pct),
        'Costo directo': ER_ACT['costo'].apply(clp),
        'Margen directo': ER_ACT['margen_directo'].apply(clp),
        '% MD': ER_ACT['pct_md'].apply(pct),
        'Gastos operacionales': ER_ACT['gastos'].apply(clp),
        'Margen operacional': ER_ACT['margen_operacional'].apply(clp),
        '% MO': ER_ACT['pct_mo'].apply(pct),
    }), con_total=True, negativas=('Margen operacional', '% MO'))

    col1, col2 = st.columns(2, gap='medium')
    with col1:
        seccion('Margen directo y operacional por línea', '% sobre los ingresos netos')
        mg = ER_ACT.drop('Total')
        mg = mg[mg['ingresos'] > 0].rename_axis('linea').reset_index()
        mg = mg.melt(id_vars='linea', value_vars=['pct_md', 'pct_mo'], var_name='Margen', value_name='pct')
        mg['Margen'] = mg['Margen'].map({'pct_md': 'Margen directo', 'pct_mo': 'Margen operacional'})
        fig = px.bar(mg, x='linea', y='pct', color='Margen', barmode='group',
                     color_discrete_map={'Margen directo': AZUL, 'Margen operacional': NARANJO},
                     category_orders={'linea': pr.LINEAS})
        fig.update_traces(marker_line_width=0, hovertemplate='%{x}<br>%{y:.1f}%<extra>%{fullData.name}</extra>')
        fig.add_hline(y=0, line_color='#C3C8D4', line_width=1)
        fig.update_layout(xaxis_title=None, yaxis_title='%')
        mostrar(fig, 360)
    with col2:
        seccion('Ingresos netos por línea', f'{ACT} vs {ANT}')
        il = pd.concat([ER_ACT.drop('Total')[['ingresos']].assign(Período=ACT),
                        ER_ANT.drop('Total')[['ingresos']].assign(Período=ANT)]).rename_axis('Línea').reset_index()
        actual_vs_anterior(il, 'Línea', 'ingresos', ACT, ANT, None, alto=360)

    seccion('Ingresos netos mensuales por línea', f'período {ACT}')
    im = v_act.groupby(['mes', 'linea'], as_index=False)['total'].sum()
    im['ingresos'] = im['total'] / FACTOR_IVA
    im['Mes'] = im['mes'].dt.month.apply(lambda m: MESES[m - 1])
    fig = px.bar(im, x='Mes', y='ingresos', color='linea', color_discrete_map=COLOR_LINEA,
                 category_orders={'linea': pr.LINEAS, 'Mes': MESES})
    fig.update_traces(marker_line_color='white', marker_line_width=1.5,
                      hovertemplate='%{x}<br>$%{y:,.0f}<extra>%{fullData.name}</extra>')
    fig.update_layout(barmode='stack', xaxis_title=None, yaxis_title=None)
    mostrar(fig, 340)

    with st.expander('Supuestos del cálculo'):
        tabla_html(pd.DataFrame({
            'Línea': PCT_COSTO.index,
            '% costo sobre precio de venta': (100 * PCT_COSTO['pct_costo']).apply(pct),
            'Fuente': PCT_COSTO['fuente'],
        }))
        st.caption(f'Gastos operacionales: {clp(GASTO_MENSUAL)} al mes × {miles(MESES_PERIODO, 1)} meses del '
                   f'período = {clp(GASTO_MENSUAL * MESES_PERIODO)}. Precios con IVA: {"sí" if con_iva else "no"}.')

    with st.expander('Rentabilidad por producto (informe de costos)'):
        if costos.empty:
            sin_datos('El informe de costos no está cargado.')
        else:
            st.caption(f'Cubre del {costos["fecha"].min():%d-%m-%Y} al {costos["fecha"].max():%d-%m-%Y} '
                       f'({miles(costos["ot"].nunique())} OT). Parte de los costos de cristales son un '
                       f'supuesto (40% del precio) y no un costo real.')
            ok = costos[costos['costeable']]
            prod = ok.groupby('producto').agg(lineas=('venta', 'size'), venta=('venta', 'sum'),
                                              costo=('costo', 'sum'), familia=('familia', 'first')).reset_index()
            prod = prod[prod['lineas'] >= 5]
            prod['margen'] = 100 * (prod['venta'] - prod['costo']) / prod['venta']
            fig = px.scatter(prod, x='venta', y='margen', size='lineas', color='familia', hover_name='producto',
                             color_discrete_map=COLOR_FAMILIA, size_max=28,
                             title='Productos: venta vs margen (5 o más líneas)')
            fig.update_traces(marker=dict(line=dict(color='white', width=1.5), opacity=0.85),
                              hovertemplate='<b>%{hovertext}</b><br>Venta $%{x:,.0f}<br>Margen %{y:.1f}%<extra></extra>')
            fig.update_layout(xaxis_title='venta ($)', yaxis_title='margen directo (%)', xaxis_showgrid=True,
                              xaxis_gridcolor=GRILLA)
            mostrar(fig, 380)

            def tabla_productos(df):
                return pd.DataFrame({'Producto': df['producto'], 'Líneas': df['lineas'],
                                     'Venta': df['venta'].apply(clp), 'Margen': df['margen'].apply(pct)})
            col1, col2 = st.columns(2, gap='medium')
            col1.markdown('**Top 10 por venta**')
            col1.dataframe(tabla_productos(prod.sort_values('venta', ascending=False).head(10)), hide_index=True)
            col2.markdown('**Top 10 de menor margen**')
            col2.dataframe(tabla_productos(prod.sort_values('margen').head(10)), hide_index=True)

    with st.expander('Inventario de armazones: margen de lista y descuento'):
        if inventario.empty:
            sin_datos('El inventario no está cargado.')
        else:
            inv_ok = inventario.dropna(subset=['margen_pct'])
            lista_med = inv_ok['p_venta'].median()
            arm = v_act[v_act['tipo'] == 'Armazón']
            cobrado = arm['total'].sum() / unidades(arm) if unidades(arm) else np.nan
            desc = 100 * (1 - cobrado / lista_med) if lista_med and not pd.isna(cobrado) else np.nan
            fila_kpi([
                tarjeta('Ítems en inventario', miles(len(inventario)), None, f'{miles(len(inv_ok))} con precios válidos'),
                tarjeta('Margen de lista (mediana)', pct(inv_ok['margen_pct'].median()), None, 'antes de descuentos'),
                tarjeta('Precio de lista mediano', clp(lista_med), None, 'armazón en inventario'),
                tarjeta('Descuento implícito', pct(desc), None, f'precio cobrado {ACT} vs lista'),
            ])
            pv = inv_ok.groupby('proveedor').agg(items=('margen_pct', 'size'), margen=('margen_pct', 'mean')).reset_index()
            pv = pv.sort_values('items', ascending=False).head(10)
            pv['texto'] = pv['margen'].apply(pct)
            barras_h(pv, 'margen', 'proveedor', 'Margen de lista promedio por proveedor (10 con más ítems)',
                     formato='%', etiqueta='texto', alto=340)


# =============================================================================
# 11. Pestaña: Comercial (ventas, clientes, canales y convenios)
# =============================================================================
with tabs[2]:
    part = 100 * (s_act['segmento'] == 'Particular').mean() if not s_act.empty else np.nan
    fila_kpi([
        tarjeta('Boletas emitidas', miles(boletas_act), variacion(boletas_act, boletas_ant), COMPARADO),
        tarjeta('Ticket promedio por boleta', clp(ticket_act), variacion(ticket_act, ticket_ant), COMPARADO),
        tarjeta('Unidades vendidas', miles(unidades(v_act)), variacion(unidades(v_act), unidades(v_ant)), COMPARADO),
        tarjeta('Clientes particulares', pct(part), None, 'de las OT de sala de venta'),
    ])

    seccion('Tendencia histórica de la venta mensual', 'con IVA · la zona sombreada es el período seleccionado')
    hist = ventas.groupby('mes', as_index=False)['total'].sum()
    hist = hist[hist['mes'] <= fecha_max].reset_index(drop=True)
    hist['Mes'] = etiqueta_mes(hist['mes'])
    fig = px.line(hist, x='Mes', y='total', markers=True)
    fig.update_traces(line=dict(color=AZUL, width=2), marker=dict(size=7, color=AZUL),
                      hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>')
    dentro = hist.index[(hist['mes'] >= ini.replace(day=1)) & (hist['mes'] <= fin)]
    if len(dentro):
        fig.add_vrect(x0=dentro.min() - 0.5, x1=dentro.max() + 0.5, fillcolor=NARANJO, opacity=0.12, line_width=0)
    fig.update_layout(xaxis_title=None, yaxis_title=None, xaxis_type='category')
    mostrar(fig, 300)

    col1, col2 = st.columns(2, gap='medium')
    with col1:
        seccion('OT por segmento comercial', f'sala de venta · {ACT} vs {ANT}')
        if s_act.empty:
            sin_datos()
        else:
            seg = pd.concat([s_act.assign(Período=ACT), s_ant.assign(Período=ANT)])
            seg = seg.groupby(['segmento', 'Período'], as_index=False).size().rename(columns={'size': 'OT'})
            actual_vs_anterior(seg, 'segmento', 'OT', ACT, ANT, None, formato=' OT', alto=320)
    with col2:
        seccion('Ticket promedio por segmento', f'{ACT} vs {ANT}')
        if s_act.empty:
            sin_datos()
        else:
            tk = pd.concat([s_act.assign(Período=ACT), s_ant.assign(Período=ANT)])
            tk = tk[tk['total'] > 0].groupby(['segmento', 'Período'], as_index=False)['total'].mean()
            actual_vs_anterior(tk, 'segmento', 'total', ACT, ANT, None, alto=320)

    with st.expander('Ventas: forma de pago, vendedoras, días y precios'):
        col1, col2 = st.columns(2, gap='medium')
        with col1:
            fp = v_act.groupby('forma_pago', as_index=False)['total'].sum()
            fp['texto'] = (100 * fp['total'] / fp['total'].sum()).apply(pct)
            barras_h(fp, 'total', 'forma_pago', 'Venta por forma de pago', etiqueta='texto', alto=320)
        with col2:
            vd = v_act.groupby('vendedora').agg(venta=('total', 'sum'), boletas=('folio', 'nunique')).reset_index()
            vd['ticket'] = vd['venta'] / vd['boletas']
            vd = vd.sort_values('venta')
            fig = px.bar(vd, x='venta', y='vendedora', orientation='h', custom_data=['boletas', 'ticket'],
                         title='Venta y ticket por vendedora')
            fig.update_traces(marker_color=AZUL, hovertemplate='<b>%{y}</b><br>Venta $%{x:,.0f}<br>'
                              'Boletas %{customdata[0]:,.0f}<br>Ticket $%{customdata[1]:,.0f}<extra></extra>')
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            mostrar(fig, 320)
        col1, col2 = st.columns(2, gap='medium')
        with col1:
            ds = v_act.groupby(v_act['fecha'].dt.dayofweek)['total'].sum().reindex(range(7), fill_value=0)
            ds = pd.DataFrame({'día': DIAS, 'venta': ds.values})
            fig = px.bar(ds, x='día', y='venta', title='Venta por día de la semana')
            fig.update_traces(marker_color=AZUL, hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>')
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            mostrar(fig, 320)
        with col2:
            def precio_medio(v, tipo):
                x = v[v['tipo'] == tipo]
                u = unidades(x)
                return x['total'].sum() / u if u else np.nan
            productos = [('Armazón', 'Armazón'), ('Cristal (unidad)', 'Cristales'), ('Lentes de sol', 'Gafa')]
            st.markdown('**Precio medio por unidad (con IVA)**')
            st.dataframe(pd.DataFrame({
                'Producto': [p for p, _ in productos],
                ACT: [clp(precio_medio(v_act, t)) for _, t in productos],
                ANT: [clp(precio_medio(v_ant, t)) for _, t in productos],
                'Variación': [pct(variacion(precio_medio(v_act, t), precio_medio(v_ant, t))) for _, t in productos],
            }), hide_index=True)
            nc = 100 * v_act.loc[v_act['es_nc'], 'total'].sum() / venta_act if venta_act else np.nan
            st.caption(f'Notas de crédito: {pct(nc, 2)} de la venta del período.')

    with st.expander('Clientes: convenios, profesionales que derivan y edad'):
        if s_act.empty:
            sin_datos('No hay OT de sala de venta para el período (o la base no está cargada).')
        else:
            def por_conv(s):
                return s.groupby('convenio').agg(ot=('ot', 'size'), venta=('total', 'sum'))
            cv = por_conv(s_act).join(por_conv(s_ant), rsuffix='_ant', how='left').fillna(0)
            cv = cv.sort_values('ot', ascending=False).reset_index()
            st.markdown('**Detalle por convenio** (OT de sala de venta)')
            st.dataframe(pd.DataFrame({
                'Convenio': cv['convenio'].str.title(),
                'Segmento': cv['convenio'].apply(pr.segmento),
                f'OT {ACT}': cv['ot'].astype(int),
                f'OT {ANT}': cv['ot_ant'].astype(int),
                'Variación OT': [pct(variacion(a, b)) for a, b in zip(cv['ot'], cv['ot_ant'])],
                f'Venta {ACT}': cv['venta'].apply(clp),
                'Ticket promedio': (cv['venta'] / cv['ot']).apply(clp),
            }), hide_index=True, height=280)
            col1, col2 = st.columns(2, gap='medium')
            with col1:
                sin_origen = 100 * (s_act['origen'] == 'Sin registro').mean()
                og = s_act[s_act['origen'] != 'Sin registro']['origen'].value_counts().head(10).reset_index()
                og.columns = ['origen', 'ot']
                og['origen'] = og['origen'].str.title()
                barras_h(og, 'ot', 'origen', f'Profesionales que más derivan ({pct(sin_origen)} sin registro)',
                         formato=' OT', alto=340)
            with col2:
                tramos = pd.cut(s_act['edad'], [0, 12, 18, 30, 45, 60, 75, 110],
                                labels=['0-12', '13-18', '19-30', '31-45', '46-60', '61-75', '76+'])
                ed = tramos.value_counts().sort_index().reset_index()
                ed.columns = ['tramo', 'ot']
                fig = px.bar(ed, x='tramo', y='ot', title='Edad de los clientes')
                fig.update_traces(marker_color=AZUL, hovertemplate='%{x} años<br>%{y} OT<extra></extra>')
                fig.update_layout(xaxis_title='años', yaxis_title=None)
                mostrar(fig, 340)

    with st.expander('Canal convenio institucional (SSCC / COSADES)'):
        if c_act.empty:
            sin_datos('No hay OT de convenio institucional para el período (o la base no está cargada).')
        else:
            st.caption('Volumen de OT derivadas desde la red pública. Este canal no registra precios.')
            col1, col2 = st.columns(2, gap='medium')
            with col1:
                filas = []
                for m in MESES_RANGO:
                    filas.append({'Mes': MESES[m - 1], 'Período': ACT, 'OT': (c_act['fecha'].dt.month == m).sum()})
                    filas.append({'Mes': MESES[m - 1], 'Período': ANT, 'OT': (c_ant['fecha'].dt.month == m).sum()})
                actual_vs_anterior(pd.DataFrame(filas), 'Mes', 'OT', ACT, ANT, 'OT por mes', formato=' OT', alto=320)
            with col2:
                ct = c_act['centro_origen'].value_counts().head(10).reset_index()
                ct.columns = ['centro', 'ot']
                ct['centro'] = ct['centro'].str.replace('Centro de Salud Familiar', 'CESFAM', regex=False)
                barras_h(ct, 'ot', 'centro', 'Centros que más derivan (top 10)', formato=' OT', alto=320)

    with st.expander('Cartera de convenios'):
        if convenios.empty:
            sin_datos('La planilla de convenios no está cargada.')
        else:
            con_estado = 100 * (convenios['estado'] != 'Sin estado').mean()
            st.caption(f'{miles(len(convenios))} convenios registrados · {pct(con_estado)} con estado declarado.')
            col1, col2 = st.columns(2, gap='medium')
            with col1:
                cat = convenios['categoria'].value_counts().reset_index()
                cat.columns = ['categoria', 'n']
                barras_h(cat, 'n', 'categoria', 'Convenios por categoría', formato=' convenios', etiqueta='n', alto=280)
            with col2:
                af = (convenios.dropna(subset=['anio_firma'])['anio_firma'].astype(int)
                      .value_counts().sort_index().reset_index())
                af.columns = ['año', 'n']
                af['año'] = af['año'].astype(str)
                fig = px.bar(af, x='año', y='n', title='Año de firma')
                fig.update_traces(marker_color=AZUL, hovertemplate='%{x}<br>%{y} convenios<extra></extra>')
                fig.update_layout(xaxis_title=None, yaxis_title=None)
                mostrar(fig, 280)
            buscar = st.text_input('Buscar organización', '')
            tabla = convenios
            if buscar:
                tabla = tabla[tabla['organizacion'].str.contains(buscar, case=False, na=False)]
            st.dataframe(pd.DataFrame({
                'Organización': tabla['organizacion'], 'Categoría': tabla['categoria'],
                'Año firma': tabla['anio_firma'].apply(lambda x: '' if pd.isna(x) else str(int(x))),
                'Estado': tabla['estado'],
            }), hide_index=True, height=300)


# =============================================================================
# 12. Pestaña: Operaciones
# =============================================================================
with tabs[3]:
    fila_kpi([
        tarjeta('Plazo de entrega (mediana)', f'{miles(lt_act)} días', variacion(lt_act, lt_ant), COMPARADO,
                invertir=True, meta=semaforo('Plazo de entrega (mediana)')),
        tarjeta('Entregas fuera de plazo', pct(atr_act),
                None if pd.isna(atr_ant) or pd.isna(atr_act) else atr_act - atr_ant,
                COMPARADO, invertir=True, puntos=True, meta=semaforo('Entregas fuera de plazo')),
        tarjeta('Cristales pedidos a laboratorio', miles(len(p_act)), variacion(len(p_act), len(p_ant)), COMPARADO),
        tarjeta('Pedidos urgentes', pct(urg_act),
                None if pd.isna(urg_ant) or pd.isna(urg_act) else urg_act - urg_ant,
                COMPARADO, invertir=True, puntos=True, meta=semaforo('Pedidos de cristal urgentes')),
    ])

    col1, col2 = st.columns(2, gap='medium')
    with col1:
        seccion('Días entre la OT y la entrega', f'OT de sala de venta · período {ACT}')
        lt = s_act['lead_time'].dropna() if not s_act.empty else pd.Series(dtype=float)
        if lt.empty:
            sin_datos()
        else:
            fig = px.histogram(lt.to_frame('días'), x='días', nbins=30)
            fig.update_traces(marker_color=AZUL, marker_line_color='white', marker_line_width=1.5,
                              hovertemplate='%{x} días<br>%{y} OT<extra></extra>')
            fig.add_vline(x=lt.median(), line_color=NARANJO, line_width=2,
                          annotation_text=f'Mediana {miles(lt.median())} días', annotation_position='top right')
            fig.add_vline(x=meta_lt, line_color=GRIS, line_width=1,
                          annotation_text=f'Meta {miles(meta_lt)}', annotation_position='bottom right')
            fig.update_layout(xaxis_title='días', yaxis_title='OT', bargap=0.05)
            mostrar(fig, 340)
    with col2:
        seccion('Plazo de entrega mes a mes', 'mediana de días (últimos 24 meses)')
        if ot_sala.empty:
            sin_datos()
        else:
            lm = ot_sala[ot_sala['fecha'] > fecha_max - pd.DateOffset(months=24)]
            lm = lm.groupby('mes', as_index=False)['lead_time'].median().sort_values('mes')
            lm['Mes'] = etiqueta_mes(lm['mes'])
            fig = px.line(lm, x='Mes', y='lead_time', markers=True)
            fig.update_traces(line=dict(color=AZUL, width=2), marker=dict(size=7, color=AZUL),
                              hovertemplate='%{x}<br>%{y:.0f} días<extra></extra>')
            fig.add_hline(y=meta_lt, line_color=GRIS, line_width=1, annotation_text='meta',
                          annotation_position='top left')
            fig.update_layout(xaxis_title=None, yaxis_title='días', xaxis_type='category')
            mostrar(fig, 340)

    col1, col2 = st.columns(2, gap='medium')
    with col1:
        seccion('Mix de proveedores de cristales por año', '% de cristales pedidos a cada laboratorio')
        if pedidos.empty:
            sin_datos('La base de pedidos de cristales no está cargada.')
        else:
            mx = pedidos.groupby(['anio', 'proveedor'], as_index=False).size()
            mx['pct'] = 100 * mx['size'] / mx.groupby('anio')['size'].transform('sum')
            mx['Año'] = mx['anio'].astype(str)
            orden = [p for p in COLOR_PROVEEDOR if p in mx['proveedor'].unique()]
            orden += [p for p in mx['proveedor'].unique() if p not in orden]
            fig = px.bar(mx, x='Año', y='pct', color='proveedor', color_discrete_map=COLOR_PROVEEDOR,
                         category_orders={'proveedor': orden}, custom_data=['size'])
            fig.update_traces(marker_line_color='white', marker_line_width=1.5,
                              hovertemplate='%{x}<br>%{y:.1f}% · %{customdata[0]:,.0f} cristales'
                                            '<extra>%{fullData.name}</extra>')
            fig.update_layout(barmode='stack', xaxis_title=None, yaxis_title='%', yaxis_range=[0, 100])
            mostrar(fig, 360)
    with col2:
        seccion('Cristales pedidos por mes', f'{ACT} vs {ANT}')
        filas = []
        for m in MESES_RANGO:
            filas.append({'Mes': MESES[m - 1], 'Período': ACT,
                          'Cristales': (p_act['fecha'].dt.month == m).sum() if not p_act.empty else 0})
            filas.append({'Mes': MESES[m - 1], 'Período': ANT,
                          'Cristales': (p_ant['fecha'].dt.month == m).sum() if not p_ant.empty else 0})
        actual_vs_anterior(pd.DataFrame(filas), 'Mes', 'Cristales', ACT, ANT, None, formato=' cristales', alto=360)

    with st.expander('Cristales más pedidos'):
        if p_act.empty:
            sin_datos()
        else:
            tc = p_act['cristal'].value_counts().head(10).reset_index()
            tc.columns = ['cristal', 'pedidos']
            barras_h(tc, 'pedidos', 'cristal', None, formato=' cristales', alto=340)


# =============================================================================
# 13. Pestaña: Calidad de datos
# =============================================================================
with tabs[4]:
    neg = (inventario['saldo_sala'] < 0).sum() if not inventario.empty else 0
    sin_est = (convenios['estado'] == 'Sin estado').sum() if not convenios.empty else 0
    sin_or = 100 * (s_act['origen'] == 'Sin registro').mean() if not s_act.empty else np.nan
    fila_kpi([
        tarjeta('Venta con OT mal registrada', pct(err_act), None, f'período {ACT}',
                meta=semaforo('Venta con OT mal registrada')),
        tarjeta('OT sin profesional de origen', pct(sin_or), None, f'período {ACT}'),
        tarjeta('Ítems con saldo negativo', miles(neg), None,
                f'de {miles(len(inventario))} en inventario' if not inventario.empty else ''),
        tarjeta('Convenios sin estado', miles(sin_est), None,
                f'de {miles(len(convenios))} registrados' if not convenios.empty else ''),
    ])

    col1, col2 = st.columns(2, gap='medium')
    with col1:
        seccion('% del monto con OT mal o no registrada', 'mes a mes, toda la historia')
        em = ventas.assign(monto_error=np.where(ventas['estado_ot'] != 'Registrada', ventas['total'], 0))
        em = em.groupby('mes', as_index=False)[['monto_error', 'total']].sum()
        em['pct'] = 100 * em['monto_error'] / em['total']
        em['Mes'] = etiqueta_mes(em['mes'])
        fig = px.line(em, x='Mes', y='pct', markers=True)
        fig.update_traces(line=dict(color=AZUL, width=2), marker=dict(size=7, color=AZUL),
                          hovertemplate='%{x}<br>%{y:.1f}%<extra></extra>')
        fig.add_hline(y=meta_err, line_color=GRIS, line_width=1, annotation_text='meta',
                      annotation_position='top left')
        fig.update_layout(xaxis_title=None, yaxis_title='%', xaxis_type='category')
        mostrar(fig, 320)
    with col2:
        seccion('Registro de OT por vendedora', f'% de líneas con OT mal o no registrada · {ACT}')
        ev = v_act.assign(error=v_act['estado_ot'] != 'Registrada').groupby('vendedora').agg(
            lineas=('error', 'size'), errores=('error', 'sum')).reset_index()
        ev = ev[ev['lineas'] >= 20]
        ev['pct'] = 100 * ev['errores'] / ev['lineas']
        ev['texto'] = ev['pct'].apply(pct)
        barras_h(ev, 'pct', 'vendedora', None, formato='%', etiqueta='texto', alto=320)

    seccion('Auditoría de calidad', 'hallazgos para pedir correcciones a TI')
    hallazgos = [
        ('Crítica', 'OT convenio', 'El canal convenio no registra ningún precio', f'{miles(len(ot_conv))} OT sin valorizar'),
        ('Crítica', 'Inventario', 'Ítems con saldo negativo en sala', f'{miles(neg)} ítems'),
        ('Crítica', 'Convenios', 'Convenios sin estado (vigente / vencido)', f'{miles(sin_est)} de {miles(len(convenios))}'),
        ('Alta', 'Ventas', 'Monto con OT mal o no registrada (toda la historia)', pct(pct_error(ventas))),
        ('Alta', 'OT sala', 'OT sin profesional de origen registrado',
         pct(100 * (ot_sala['origen'] == 'Sin registro').mean()) if not ot_sala.empty else '–'),
        ('Alta', 'Costos', 'Líneas del informe de costos sin costo o sin precio',
         pct(100 * (~costos['costeable']).mean()) if not costos.empty else '–'),
        ('Alta', 'OT sala', 'OT sin fecha de entrega real',
         pct(100 * ot_sala['fecha_entrega'].isna().mean()) if not ot_sala.empty else '–'),
    ]
    color_criticidad = {'Crítica': 'No cumple', 'Alta': 'En riesgo'}
    tabla_html(pd.DataFrame([{'Criticidad': chip(color_criticidad[c], c), 'Fuente': f, 'Hallazgo': h,
                              'Magnitud': f'<b>{v}</b>'} for c, f, h, v in hallazgos]))

    with st.expander('Trazabilidad de la OT entre sistemas'):
        ot_ped = set(pedidos.loc[pedidos['anio'] >= 2024, 'ot'].dropna()) if not pedidos.empty else set()
        ot_sal = set(ot_sala['ot'].dropna()) if not ot_sala.empty else set()
        ot_con = set(ot_conv['ot'].dropna()) if not ot_conv.empty else set()
        ot_bol = set(ventas['ot'].dropna())
        ot_cos = set(costos['ot'].dropna()) if not costos.empty else set()
        cruces = [
            ['Pedidos de cristal (2024+) sin OT en ningún sistema de venta', len(ot_ped - ot_sal - ot_con), len(ot_ped)],
            ['OT de sala sin pedido de cristal asociado', len(ot_sal - ot_ped), len(ot_sal)],
            ['OT de sala sin boleta asociada', len(ot_sal - ot_bol), len(ot_sal)],
            ['OT de sala sin costeo en el informe de costos', len(ot_sal - ot_cos), len(ot_sal)],
        ]
        tabla_html(pd.DataFrame([{'Cruce': c, 'Sin match': miles(a), 'Universo': miles(b),
                                  '%': pct(100 * a / b if b else np.nan)} for c, a, b in cruces]))

    with st.expander('Bases cargadas, actualización y descarga de tablas'):
        resumen = []
        for clave, info in pr.BASES.items():
            df = datos[clave]
            tiene_fecha = 'fecha' in df.columns and not df.empty
            resumen.append({
                'Base': info['nombre'], 'Origen': origen_datos[clave], 'Filas': miles(len(df)),
                'Desde': f'{df["fecha"].min():%d-%m-%Y}' if tiene_fecha else '',
                'Hasta': f'{df["fecha"].max():%d-%m-%Y}' if tiene_fecha else '',
            })
        tabla_html(pd.DataFrame(resumen))
        st.markdown("""
**Actualizar solo para esta sesión:** barra lateral → *Cargar / actualizar bases de datos* → subir las
planillas originales (`CONSOLIDADO VENTAS ... NUBOX`, `OT APPS FINAL - ÓPTICA SALA DE VENTA`,
`OT APPS CONVENIO FINAL`, `Centralización Cristales`, `informe_costos_analitico`,
`OT APPS FINAL - INVENTARIO ARMAZONES`, `Convenios COALIVI`).

**Actualizar para todos:** volver a correr el notebook de Colab y subir a GitHub la carpeta `data` nueva.
""")
        columnas = st.columns(4)
        for n_, (clave, info) in enumerate(pr.BASES.items()):
            df = datos[clave]
            if not df.empty:
                columnas[n_ % 4].download_button(info['nombre'], df.to_csv(index=False).encode('utf-8-sig'),
                                                 file_name=f'coalivi_{clave}.csv', mime='text/csv',
                                                 key=f'descarga_{clave}')

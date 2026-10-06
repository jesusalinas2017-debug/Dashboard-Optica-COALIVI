# app.py
# Dashboard ejecutivo · Óptica COALIVI
# Elaborado por MDF Consulting para la Dirección Ejecutiva de COALIVI (2026)
#
# Para correrlo en el computador:  streamlit run app.py

import os

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
st.set_page_config(page_title='Dashboard Ejecutivo · Óptica COALIVI',
                   page_icon='👓', layout='wide', initial_sidebar_state='expanded')

AZUL = '#1A4474'        # azul institucional COALIVI
NARANJO = '#FA9219'     # naranjo institucional COALIVI
AZUL_SUAVE = '#A9B8CE'  # para el "año anterior" en las comparaciones
TINTA = '#1F2A44'
GRIS = '#6B7385'
GRILLA = '#E6E9EF'

# Paleta para categorías (validada para daltonismo, en este orden)
SERIES = ['#2F6DB5', '#F08C1A', '#1BAF7A', '#7B6FD6', '#E87BA4', '#EDA100']

# Colores fijos por entidad: cada segmento / proveedor / tipo tiene siempre el mismo color
COLOR_SEGMENTO = {'Particular': SERIES[0], 'Empresas y convenios': SERIES[1],
                  'Público / social': SERIES[2]}
COLOR_PROVEEDOR = {'TEKNOL': SERIES[0], 'MERCAVISION': SERIES[1], 'MEGALUX': SERIES[2],
                   'ITALOPTIC': SERIES[3], 'RODENSTOCK': SERIES[4], 'PEDIDO URGENTE': SERIES[5]}
COLOR_TIPO = {'Cristales': SERIES[0], 'Armazón': SERIES[1], 'Gafa': SERIES[2], 'Otros': SERIES[3]}
COLOR_FAMILIA = {'Cristal': SERIES[0], 'Armazón': SERIES[1], 'Gafas': SERIES[2], 'Accesorio': SERIES[3]}

# Colores de estado (semáforo): solo para alertas, nunca para series
VERDE, AMARILLO, ROJO = '#0CA30C', '#FAB219', '#D03B3B'

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
  border-bottom: 5px solid {NARANJO}; border-radius: 14px; padding: 22px 28px; margin-bottom: 18px; }}
.encabezado h1 {{ color: white; font-size: 1.75rem; font-weight: 700; margin: 0; padding: 0; }}
.encabezado p {{ color: #D9E2EF; margin: 4px 0 0 0; font-size: 0.95rem; }}
.encabezado .marca {{ color: {NARANJO}; font-weight: 700; letter-spacing: 1px; font-size: 0.8rem; }}

/* Tarjetas KPI */
.kpi {{ background: white; border-radius: 12px; padding: 14px 16px 12px 16px;
  border-left: 5px solid {NARANJO}; box-shadow: 0 1px 3px rgba(26,68,116,0.12); min-height: 112px; }}
.kpi-t {{ color: {GRIS}; font-size: 0.78rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.4px; }}
.kpi-v {{ color: {AZUL}; font-size: 1.65rem; font-weight: 700; line-height: 1.25; margin-top: 2px; }}
.kpi-d {{ font-size: 0.82rem; font-weight: 600; margin-top: 2px; }}
.kpi-d span {{ color: {GRIS}; font-weight: 400; }}
.sube {{ color: #0A7A0A; }}  .baja {{ color: {ROJO}; }}  .neutro {{ color: {GRIS}; }}

/* Títulos de sección */
.seccion {{ color: {AZUL}; font-size: 1.1rem; font-weight: 700; border-left: 4px solid {NARANJO};
  padding-left: 10px; margin: 22px 0 6px 0; }}
.subtitulo {{ color: {GRIS}; font-size: 0.85rem; margin: -2px 0 8px 14px; }}

/* Caja de hallazgos */
.hallazgos {{ background: #FFF6EA; border: 1px solid #F8D3A0; border-radius: 12px; padding: 14px 20px; }}
.hallazgos h4 {{ color: {AZUL}; margin: 0 0 6px 0; font-size: 1rem; }}
.hallazgos li {{ margin-bottom: 4px; color: {TINTA}; font-size: 0.92rem; }}

/* Tabla de auditoría */
.tabla {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; background: white; }}
.tabla th {{ background: {AZUL}; color: white; text-align: left; padding: 8px 10px; }}
.tabla td {{ border-bottom: 1px solid {GRILLA}; padding: 7px 10px; color: {TINTA}; }}
.chip {{ display: inline-block; padding: 2px 9px; border-radius: 10px; font-size: 0.75rem;
  font-weight: 700; color: white; }}

/* Pestañas */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 2px solid {GRILLA}; }}
.stTabs [data-baseweb="tab"] {{ padding: 8px 14px; font-weight: 600; color: {AZUL}; }}

/* Barra lateral */
[data-testid="stSidebar"] .logo {{ background: {AZUL}; color: white; border-radius: 10px;
  padding: 14px; text-align: center; margin-bottom: 10px; border-bottom: 4px solid {NARANJO}; }}
[data-testid="stSidebar"] .logo b {{ font-size: 1.35rem; letter-spacing: 2px; }}
[data-testid="stSidebar"] .logo small {{ color: #D9E2EF; }}
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
    return '–' if x is None or pd.isna(x) else '$' + miles(x)


def mm(x):
    # Montos grandes en millones: $245,3 MM
    if x is None or pd.isna(x):
        return '–'
    return '$' + miles(x / 1e6, 1) + ' MM' if abs(x) >= 1e6 else clp(x)


def pct(x, dec=1):
    return '–' if x is None or pd.isna(x) else miles(x, dec) + '%'


def variacion(actual, anterior):
    # Variación porcentual; None si no hay base de comparación
    if anterior is None or pd.isna(anterior) or anterior == 0 or pd.isna(actual):
        return None
    return 100 * (actual / anterior - 1)


def tarjeta(titulo, valor, delta=None, comparado='', invertir=False, puntos=False):
    # Tarjeta KPI en HTML. 'invertir' = True cuando subir es malo (ej. % de errores)
    # 'puntos' = True cuando el delta se expresa en puntos porcentuales
    if delta is None:
        linea = f'<div class="kpi-d neutro">{comparado}</div>' if comparado else '<div class="kpi-d">&nbsp;</div>'
    else:
        bueno = (delta >= 0) != invertir
        clase = 'neutro' if abs(delta) < 0.05 else ('sube' if bueno else 'baja')
        flecha = '▲' if delta > 0 else ('▼' if delta < 0 else '●')
        unidad = ' pp' if puntos else '%'
        linea = (f'<div class="kpi-d {clase}">{flecha} {miles(abs(delta), 1)}{unidad} '
                 f'<span>{comparado}</span></div>')
    return f'<div class="kpi"><div class="kpi-t">{titulo}</div><div class="kpi-v">{valor}</div>{linea}</div>'


def fila_kpi(tarjetas):
    columnas = st.columns(len(tarjetas), gap='small')
    for col, html in zip(columnas, tarjetas):
        col.markdown(html, unsafe_allow_html=True)


def seccion(texto, sub=''):
    st.markdown(f'<div class="seccion">{texto}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="subtitulo">{sub}</div>', unsafe_allow_html=True)


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
    fig.update_layout(xaxis_title=None, yaxis_title=None, xaxis=dict(showticklabels=etiqueta is None,
                                                                     gridcolor=GRILLA, showgrid=True))
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


# =============================================================================
# 4. Carga de datos
# =============================================================================
CARPETA_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


@st.cache_data(show_spinner='Cargando datos de COALIVI...')
def cargar_repositorio():
    # Lee las tablas limpias que vienen en la carpeta data/ del repositorio
    tablas = {}
    for clave in pr.FECHAS:
        ruta = os.path.join(CARPETA_DATOS, f'{clave}.csv.gz')
        if os.path.exists(ruta):
            tablas[clave] = pr.leer_tabla(ruta, clave)
    return tablas


@st.cache_data(show_spinner='Procesando planilla subida...')
def procesar_subida(nombre, contenido):
    # Limpia una planilla original subida desde la barra lateral
    return pr.procesar_archivo(contenido, nombre)


datos = cargar_repositorio()
origen_datos = {clave: 'Repositorio' for clave in datos}

# ---- Barra lateral: logo, carga de archivos y filtros
with st.sidebar:
    st.markdown('<div class="logo"><b>COALIVI</b><br><small>Óptica · Dirección Ejecutiva</small></div>',
                unsafe_allow_html=True)

    with st.expander('Cargar / actualizar bases de datos', expanded=not datos):
        st.caption('Sube las planillas originales (.xlsx) tal como las entrega TI. '
                   'Se reconocen por su nombre y reemplazan a las del repositorio mientras '
                   'la página esté abierta.')
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
    st.markdown('<div class="encabezado"><span class="marca">ÓPTICA COALIVI · MDF CONSULTING</span>'
                '<h1>Dashboard Ejecutivo</h1><p>Sube las planillas en la barra lateral para comenzar.</p></div>',
                unsafe_allow_html=True)
    st.warning('No se encontró la base de ventas. Súbela desde la barra lateral '
               '("CONSOLIDADO VENTAS ÓPTICA ... NUBOX.xlsx").')
    st.stop()

# Tablas vacías para las bases que no estén cargadas (así la app no se cae)
for clave in pr.FECHAS:
    if clave not in datos:
        datos[clave] = pd.DataFrame()
        origen_datos[clave] = 'No cargada'

ventas = datos['ventas']
ot_sala = datos['ot_sala']
ot_conv = datos['ot_convenio']
pedidos = datos['pedidos']
costos = datos['costos']
inventario = datos['inventario']
convenios = datos['convenios']

# ---- Filtros de período
fecha_max = ventas['fecha'].max()
anios = sorted(ventas['anio'].dropna().unique().tolist(), reverse=True)

with st.sidebar:
    st.markdown('**Período de análisis**')
    anio = st.selectbox('Año', anios, index=0)
    mes_ini, mes_fin = st.select_slider('Meses', options=MESES, value=(MESES[0], MESES[-1]))
    st.caption('Todos los indicadores se comparan con el **mismo tramo del año anterior**.')

i1, i2 = MESES.index(mes_ini) + 1, MESES.index(mes_fin) + 1
ini = pd.Timestamp(int(anio), i1, 1)
fin = pd.Timestamp(int(anio), i2, 1) + pd.offsets.MonthEnd(0)
if ini <= fecha_max < fin:
    fin = fecha_max                        # el año en curso se corta en el último dato
ini_ant = ini - pd.DateOffset(years=1)
fin_ant = fin - pd.DateOffset(years=1)

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

if fin < ini:
    st.warning('No hay datos para el período elegido. Cambia el año o los meses en la barra lateral.')
    st.stop()

# Tablas del período actual y del anterior
v_act, v_ant = periodo(ventas), periodo(ventas, True)
if v_act.empty:
    st.warning(f'No hay ventas registradas entre {ini:%d-%m-%Y} y {fin:%d-%m-%Y}. '
               'Cambia el año o los meses en la barra lateral.')
    st.stop()
s_act, s_ant = periodo(ot_sala), periodo(ot_sala, True)
c_act, c_ant = periodo(ot_conv), periodo(ot_conv, True)
p_act, p_ant = periodo(pedidos), periodo(pedidos, True)

# =============================================================================
# 5. Encabezado
# =============================================================================
st.markdown(f"""
<div class="encabezado">
  <span class="marca">ÓPTICA COALIVI · CUADRO DE MANDO</span>
  <h1>Dashboard Ejecutivo</h1>
  <p>Período {ini:%d-%m-%Y} al {fin:%d-%m-%Y} · comparado con el mismo tramo de {ANT} ·
     datos de ventas hasta el {fecha_max:%d-%m-%Y}</p>
</div>""", unsafe_allow_html=True)

tabs = st.tabs(['Resumen ejecutivo', 'Ventas', 'Clientes y canales', 'Operaciones',
                'Rentabilidad', 'Convenios', 'Calidad de datos', 'Datos'])


# =============================================================================
# 6. Indicadores comunes
# =============================================================================
def unidades(v):
    # Una venta a crédito se boletea en dos líneas (abono + saldo) con la misma cantidad,
    # así que las unidades se cuentan sin las líneas de saldo
    return v.loc[v['clase_linea'] != 'Saldo', 'cantidad'].sum()


def resumen_ventas(v):
    venta = v['total'].sum()
    boletas = v['folio'].nunique()
    return venta, boletas, (venta / boletas if boletas else np.nan)


venta_act, boletas_act, ticket_act = resumen_ventas(v_act)
venta_ant, boletas_ant, ticket_ant = resumen_ventas(v_ant)

# Días entre la OT y la entrega (mediana)
lt_act = s_act['lead_time'].median() if not s_act.empty else np.nan
lt_ant = s_ant['lead_time'].median() if not s_ant.empty else np.nan


def pct_error(v):
    # % del monto facturado cuya OT está mal o no registrada
    total = v['total'].sum()
    return 100 * v.loc[v['estado_ot'] != 'Registrada', 'total'].sum() / total if total else np.nan


def ticket_ot(s):
    con_valor = s[s['total'] > 0]['total'] if not s.empty else pd.Series(dtype=float)
    return con_valor.mean() if len(con_valor) else np.nan


# =============================================================================
# 7. Pestaña: Resumen ejecutivo
# =============================================================================
with tabs[0]:
    err_act, err_ant = pct_error(v_act), pct_error(v_ant)

    fila_kpi([
        tarjeta('Venta facturada', mm(venta_act), variacion(venta_act, venta_ant), COMPARADO),
        tarjeta('Boletas emitidas', miles(boletas_act), variacion(boletas_act, boletas_ant), COMPARADO),
        tarjeta('Ticket promedio por boleta', clp(ticket_act), variacion(ticket_act, ticket_ant), COMPARADO),
        tarjeta('OT sala de venta', miles(len(s_act)), variacion(len(s_act), len(s_ant)), COMPARADO),
    ])
    st.write('')

    # Margen bruto del informe de costos (solo cubre algunos meses)
    k_ok = costos[costos['costeable']] if not costos.empty else costos
    margen = 100 * k_ok['utilidad'].sum() / k_ok['venta'].sum() if not k_ok.empty and k_ok['venta'].sum() else np.nan

    fila_kpi([
        tarjeta('Ticket promedio por OT', clp(ticket_ot(s_act)),
                variacion(ticket_ot(s_act), ticket_ot(s_ant)), COMPARADO),
        tarjeta('OT convenio institucional', miles(len(c_act)), variacion(len(c_act), len(c_ant)), COMPARADO),
        tarjeta('Margen bruto estimado', pct(margen), None,
                'según informe de costos' if not k_ok.empty else 'sin informe de costos'),
        tarjeta('Venta con OT mal o no registrada', pct(err_act),
                None if pd.isna(err_ant) or pd.isna(err_act) else err_act - err_ant, COMPARADO,
                invertir=True, puntos=True),
    ])

    col1, col2 = st.columns([3, 2], gap='medium')
    with col1:
        seccion('Venta mensual', f'{ACT} contra el mismo mes de {ANT}')
        meses_rango = list(range(i1, i2 + 1))
        filas = []
        for m in meses_rango:
            filas.append({'Mes': MESES[m - 1], 'Período': ACT,
                          'Venta': v_act.loc[v_act['fecha'].dt.month == m, 'total'].sum()})
            filas.append({'Mes': MESES[m - 1], 'Período': ANT,
                          'Venta': v_ant.loc[v_ant['fecha'].dt.month == m, 'total'].sum()})
        actual_vs_anterior(pd.DataFrame(filas), 'Mes', 'Venta', ACT, ANT, None, alto=340)

    with col2:
        seccion('Mix de venta por tipo de producto', 'participación en el período')
        if v_act.empty:
            sin_datos()
        else:
            mix = v_act.groupby('tipo', as_index=False)['total'].sum()
            mix['part'] = 100 * mix['total'] / mix['total'].sum()
            mix['texto'] = mix['part'].apply(lambda x: pct(x))
            barras_h(mix, 'total', 'tipo', None, etiqueta='texto', alto=340)

    col1, col2 = st.columns([2, 3], gap='medium')
    with col1:
        seccion('OT por segmento comercial', f'sala de venta · {ACT} vs {ANT}')
        if s_act.empty:
            sin_datos()
        else:
            seg = pd.concat([s_act.assign(Período=ACT), s_ant.assign(Período=ANT)])
            seg = seg.groupby(['segmento', 'Período'], as_index=False).size().rename(columns={'size': 'OT'})
            actual_vs_anterior(seg, 'segmento', 'OT', ACT, ANT, None, formato=' OT', alto=330)

    with col2:
        # Hallazgos que se escriben solos según los datos del período
        puntos = []
        dv = variacion(venta_act, venta_ant)
        if dv is not None:
            puntos.append(f'La venta facturada {"creció" if dv >= 0 else "cayó"} <b>{pct(abs(dv))}</b> '
                          f'frente al mismo tramo de {ANT} ({mm(venta_act)} vs {mm(venta_ant)}).')
        dt = variacion(ticket_act, ticket_ant)
        db = variacion(boletas_act, boletas_ant)
        if dt is not None and db is not None:
            puntos.append(f'Se emitieron <b>{pct(abs(db))} {"más" if db >= 0 else "menos"}</b> boletas, '
                          f'con un ticket promedio <b>{pct(abs(dt))} {"mayor" if dt >= 0 else "menor"}</b> '
                          f'({clp(ticket_act)} vs {clp(ticket_ant)}).')
        if not s_act.empty and not s_ant.empty:
            seg_a = s_act['segmento'].value_counts()
            seg_b = s_ant['segmento'].value_counts()
            crec = ((seg_a - seg_b) / seg_b * 100).dropna()
            if not crec.empty:
                top = crec.idxmax()
                puntos.append(f'El segmento <b>{top}</b> es el que más crece en OT ({pct(crec.max())}); '
                              f'los particulares son el {pct(100 * seg_a.get("Particular", 0) / seg_a.sum())} de las OT.')
        if not pd.isna(err_act):
            puntos.append(f'El <b>{pct(err_act)}</b> del monto facturado tiene la OT mal o no registrada: '
                          f'impide medir rentabilidad por venta.')
        if not pd.isna(lt_act):
            atraso = 100 * (s_act['atraso'] > 0).sum() / max(s_act['atraso'].notna().sum(), 1)
            puntos.append(f'Una OT demora <b>{miles(lt_act)} días</b> (mediana) en entregarse y el '
                          f'<b>{pct(atraso)}</b> se entrega después de la fecha prometida.')
        if not p_act.empty:
            puntos.append(f'El <b>{pct(100 * p_act["urgente"].mean())}</b> de los cristales pedidos al '
                          f'laboratorio fueron pedidos urgentes.')
        lista = ''.join(f'<li>{p}</li>' for p in puntos)
        st.markdown(f'<div class="hallazgos" style="margin-top:22px"><h4>Hallazgos clave del período</h4>'
                    f'<ul>{lista}</ul></div>', unsafe_allow_html=True)


# =============================================================================
# 8. Pestaña: Ventas
# =============================================================================
with tabs[1]:
    unid_act, unid_ant = unidades(v_act), unidades(v_ant)

    def precio_medio(v, tipo):
        # Precio efectivo por unidad = monto cobrado / unidades vendidas
        x = v[v['tipo'] == tipo]
        u = unidades(x)
        return x['total'].sum() / u if u else np.nan

    nc_act = 100 * v_act.loc[v_act['es_nc'], 'total'].sum() / venta_act if venta_act else np.nan
    fila_kpi([
        tarjeta('Unidades vendidas', miles(unid_act), variacion(unid_act, unid_ant), COMPARADO),
        tarjeta('Precio medio armazón', clp(precio_medio(v_act, 'Armazón')),
                variacion(precio_medio(v_act, 'Armazón'), precio_medio(v_ant, 'Armazón')), COMPARADO),
        tarjeta('Precio medio cristal (unidad)', clp(precio_medio(v_act, 'Cristales')),
                variacion(precio_medio(v_act, 'Cristales'), precio_medio(v_ant, 'Cristales')), COMPARADO),
        tarjeta('Notas de crédito', pct(nc_act, 2), None, 'sobre la venta del período'),
    ])

    seccion('Tendencia histórica de la venta mensual', 'la zona sombreada es el período seleccionado')
    hist = ventas.groupby('mes', as_index=False)['total'].sum()
    hist = hist[hist['mes'] <= fecha_max].reset_index(drop=True)
    hist['Mes'] = etiqueta_mes(hist['mes'])
    fig = px.line(hist, x='Mes', y='total', markers=True)
    fig.update_traces(line=dict(color=AZUL, width=2), marker=dict(size=7, color=AZUL),
                      hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>')
    # Sombreado del período elegido (el eje es por categorías: 0, 1, 2, ...)
    dentro = hist.index[(hist['mes'] >= ini.replace(day=1)) & (hist['mes'] <= fin)]
    if len(dentro):
        fig.add_vrect(x0=dentro.min() - 0.5, x1=dentro.max() + 0.5, fillcolor=NARANJO,
                      opacity=0.12, line_width=0)
    fig.update_layout(xaxis_title=None, yaxis_title=None, xaxis_type='category')
    mostrar(fig, 320)

    col1, col2 = st.columns(2, gap='medium')
    with col1:
        seccion('Venta mensual por tipo de producto', f'período {ACT}')
        if v_act.empty:
            sin_datos()
        else:
            x = v_act.copy()
            x['grupo'] = np.where(x['tipo'].isin(['Cristales', 'Armazón', 'Gafa']), x['tipo'], 'Otros')
            x = x.groupby(['mes', 'grupo'], as_index=False)['total'].sum()
            x['Mes'] = x['mes'].dt.month.apply(lambda m: MESES[m - 1])
            fig = px.bar(x, x='Mes', y='total', color='grupo', color_discrete_map=COLOR_TIPO,
                         category_orders={'grupo': list(COLOR_TIPO), 'Mes': MESES})
            fig.update_traces(marker_line_color='white', marker_line_width=1.5,
                              hovertemplate='%{x}<br>$%{y:,.0f}<extra>%{fullData.name}</extra>')
            fig.update_layout(xaxis_title=None, yaxis_title=None, barmode='stack')
            mostrar(fig, 340)

    with col2:
        seccion('Venta por forma de pago', 'participación en el período')
        if v_act.empty:
            sin_datos()
        else:
            fp = v_act.groupby('forma_pago', as_index=False)['total'].sum()
            fp['texto'] = (100 * fp['total'] / fp['total'].sum()).apply(pct)
            barras_h(fp, 'total', 'forma_pago', None, etiqueta='texto', alto=340)

    col1, col2 = st.columns(2, gap='medium')
    with col1:
        seccion('Venta y ticket por vendedora', 'pasa el mouse para ver el ticket promedio')
        if v_act.empty:
            sin_datos()
        else:
            vd = v_act.groupby('vendedora').agg(venta=('total', 'sum'), boletas=('folio', 'nunique')).reset_index()
            vd['ticket'] = vd['venta'] / vd['boletas']
            vd = vd.sort_values('venta')
            fig = px.bar(vd, x='venta', y='vendedora', orientation='h', custom_data=['boletas', 'ticket'])
            fig.update_traces(marker_color=AZUL, hovertemplate='<b>%{y}</b><br>Venta $%{x:,.0f}<br>'
                              'Boletas %{customdata[0]:,.0f}<br>Ticket $%{customdata[1]:,.0f}<extra></extra>')
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            mostrar(fig, 340)

    with col2:
        seccion('Venta por día de la semana', 'útil para planificar turnos de la sala')
        if v_act.empty:
            sin_datos()
        else:
            ds = v_act.groupby(v_act['fecha'].dt.dayofweek)['total'].sum().reindex(range(7), fill_value=0)
            ds = pd.DataFrame({'día': DIAS, 'venta': ds.values})
            fig = px.bar(ds, x='día', y='venta')
            fig.update_traces(marker_color=AZUL, hovertemplate='%{x}<br>$%{y:,.0f}<extra></extra>')
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            mostrar(fig, 340)

    seccion('Detalle por tipo de producto', f'{ACT} vs {ANT} (mismo tramo)')
    if not v_act.empty:
        def por_tipo(v):
            u = v.assign(u=np.where(v['clase_linea'] != 'Saldo', v['cantidad'], 0))
            return u.groupby('tipo').agg(venta=('total', 'sum'), unidades=('u', 'sum'))
        t = por_tipo(v_act).join(por_tipo(v_ant), rsuffix='_ant', how='outer').fillna(0)
        t['precio'] = t['venta'] / t['unidades'].replace(0, np.nan)
        t = t.sort_values('venta', ascending=False).reset_index()
        tabla = pd.DataFrame({
            'Tipo': t['tipo'],
            f'Venta {ACT}': t['venta'].apply(clp),
            f'Venta {ANT}': t['venta_ant'].apply(clp),
            'Variación': [pct(variacion(a, b)) for a, b in zip(t['venta'], t['venta_ant'])],
            f'Unidades {ACT}': t['unidades'].apply(miles),
            'Precio medio': t['precio'].apply(clp),
            'Participación': (100 * t['venta'] / t['venta'].sum()).apply(pct),
        })
        st.dataframe(tabla, hide_index=True)


# =============================================================================
# 9. Pestaña: Clientes y canales
# =============================================================================
with tabs[2]:
    if s_act.empty:
        sin_datos('No hay OT de sala de venta para el período (o la base no está cargada).')
    else:
        part = 100 * (s_act['segmento'] == 'Particular').mean()
        part_ant = 100 * (s_ant['segmento'] == 'Particular').mean() if not s_ant.empty else np.nan
        tk_part = ticket_ot(s_act[s_act['segmento'] == 'Particular'])
        tk_part_ant = ticket_ot(s_ant[s_ant['segmento'] == 'Particular']) if not s_ant.empty else np.nan
        sin_origen = 100 * (s_act['origen'] == 'Sin registro').mean()
        fila_kpi([
            tarjeta('Clientes particulares', pct(part),
                    None if pd.isna(part_ant) else part - part_ant, COMPARADO, puntos=True),
            tarjeta('Ticket OT particular', clp(tk_part), variacion(tk_part, tk_part_ant), COMPARADO),
            tarjeta('Edad mediana del cliente', f'{miles(s_act["edad"].median())} años', None, 'OT sala de venta'),
            tarjeta('OT sin profesional de origen', pct(sin_origen), None, 'no se sabe quién derivó'),
        ])

        col1, col2 = st.columns(2, gap='medium')
        with col1:
            seccion('Ticket promedio por segmento', f'{ACT} vs {ANT}')
            tk = pd.concat([s_act.assign(Período=ACT), s_ant.assign(Período=ANT)])
            tk = tk[tk['total'] > 0].groupby(['segmento', 'Período'], as_index=False)['total'].mean()
            actual_vs_anterior(tk, 'segmento', 'total', ACT, ANT, None, alto=330)
        with col2:
            seccion('Evolución mensual de OT por segmento', f'período {ACT}')
            ev = s_act.groupby(['mes', 'segmento'], as_index=False).size().sort_values('mes')
            ev['Mes'] = etiqueta_mes(ev['mes'])
            fig = px.line(ev, x='Mes', y='size', color='segmento', markers=True,
                          color_discrete_map=COLOR_SEGMENTO,
                          category_orders={'segmento': list(COLOR_SEGMENTO), 'Mes': ev['Mes'].unique().tolist()})
            fig.update_traces(line_width=2, marker_size=8,
                              hovertemplate='%{x}<br>%{y} OT<extra>%{fullData.name}</extra>')
            fig.update_layout(xaxis_title=None, yaxis_title=None, xaxis_type='category')
            mostrar(fig, 330)

        seccion('Detalle por convenio', 'OT de sala de venta según el convenio con que se atendió el cliente')
        def por_conv(s):
            return s.groupby('convenio').agg(ot=('ot', 'size'), venta=('total', 'sum'))
        cv = por_conv(s_act).join(por_conv(s_ant), rsuffix='_ant', how='left').fillna(0)
        cv = cv.sort_values('ot', ascending=False).reset_index()
        st.dataframe(pd.DataFrame({
            'Convenio': cv['convenio'].str.title(),
            'Segmento': cv['convenio'].apply(pr.segmento),
            f'OT {ACT}': cv['ot'].astype(int),
            f'OT {ANT}': cv['ot_ant'].astype(int),
            'Variación OT': [pct(variacion(a, b)) for a, b in zip(cv['ot'], cv['ot_ant'])],
            f'Venta {ACT}': cv['venta'].apply(clp),
            'Ticket promedio': (cv['venta'] / cv['ot']).apply(clp),
        }), hide_index=True, height=300)

        col1, col2 = st.columns(2, gap='medium')
        with col1:
            seccion('Profesionales que más derivan', f'top 10 · {pct(sin_origen)} de las OT no registra origen')
            og = s_act[s_act['origen'] != 'Sin registro']['origen'].value_counts().head(10).reset_index()
            og.columns = ['origen', 'ot']
            og['origen'] = og['origen'].str.title()
            barras_h(og, 'ot', 'origen', None, formato=' OT', alto=360)
        with col2:
            seccion('Distribución de edad de los clientes', 'OT de sala de venta del período')
            tramos = pd.cut(s_act['edad'], [0, 12, 18, 30, 45, 60, 75, 110],
                            labels=['0-12', '13-18', '19-30', '31-45', '46-60', '61-75', '76+'])
            ed = tramos.value_counts().sort_index().reset_index()
            ed.columns = ['tramo', 'ot']
            fig = px.bar(ed, x='tramo', y='ot')
            fig.update_traces(marker_color=AZUL, hovertemplate='%{x} años<br>%{y} OT<extra></extra>')
            fig.update_layout(xaxis_title='años', yaxis_title=None)
            mostrar(fig, 360)

    seccion('Canal convenio institucional (SSCC / COSADES)',
            'volumen de OT derivadas desde la red pública · este canal no registra precios')
    if c_act.empty:
        sin_datos('No hay OT de convenio institucional para el período (o la base no está cargada).')
    else:
        fila_kpi([
            tarjeta('OT convenio institucional', miles(len(c_act)), variacion(len(c_act), len(c_ant)), COMPARADO),
            tarjeta('Centros de salud que derivan', miles(c_act['centro_origen'].nunique()), None, 'en el período'),
            tarjeta('OT por mes (promedio)', miles(c_act.groupby('mes').size().mean()), None, 'en el período'),
            tarjeta('Participación SSCC', pct(100 * (c_act['contraparte'] == 'SSCC').mean()), None, 'del canal'),
        ])
        col1, col2 = st.columns(2, gap='medium')
        with col1:
            filas = []
            for m in range(i1, i2 + 1):
                filas.append({'Mes': MESES[m - 1], 'Período': ACT, 'OT': (c_act['fecha'].dt.month == m).sum()})
                filas.append({'Mes': MESES[m - 1], 'Período': ANT, 'OT': (c_ant['fecha'].dt.month == m).sum()})
            actual_vs_anterior(pd.DataFrame(filas), 'Mes', 'OT', ACT, ANT, 'OT por mes', formato=' OT', alto=340)
        with col2:
            ct = c_act['centro_origen'].value_counts().head(10).reset_index()
            ct.columns = ['centro', 'ot']
            ct['centro'] = ct['centro'].str.replace('Centro de Salud Familiar', 'CESFAM', regex=False)
            barras_h(ct, 'ot', 'centro', 'Centros que más derivan (top 10)', formato=' OT', alto=340)


# =============================================================================
# 10. Pestaña: Operaciones
# =============================================================================
with tabs[3]:
    con_atraso = s_act['atraso'].notna().sum() if not s_act.empty else 0
    atraso_act = 100 * (s_act['atraso'] > 0).sum() / con_atraso if con_atraso else np.nan
    con_atraso_ant = s_ant['atraso'].notna().sum() if not s_ant.empty else 0
    atraso_ant = 100 * (s_ant['atraso'] > 0).sum() / con_atraso_ant if con_atraso_ant else np.nan
    urg_act = 100 * p_act['urgente'].mean() if not p_act.empty else np.nan
    urg_ant = 100 * p_ant['urgente'].mean() if not p_ant.empty else np.nan

    fila_kpi([
        tarjeta('Días OT → entrega (mediana)', f'{miles(lt_act)} días',
                variacion(lt_act, lt_ant), COMPARADO, invertir=True),
        tarjeta('Entregas fuera de plazo', pct(atraso_act),
                None if pd.isna(atraso_ant) or pd.isna(atraso_act) else atraso_act - atraso_ant,
                COMPARADO, invertir=True, puntos=True),
        tarjeta('Cristales pedidos a laboratorio', miles(len(p_act)), variacion(len(p_act), len(p_ant)), COMPARADO),
        tarjeta('Pedidos urgentes', pct(urg_act),
                None if pd.isna(urg_ant) or pd.isna(urg_act) else urg_act - urg_ant,
                COMPARADO, invertir=True, puntos=True),
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
        for m in range(i1, i2 + 1):
            filas.append({'Mes': MESES[m - 1], 'Período': ACT,
                          'Cristales': (p_act['fecha'].dt.month == m).sum() if not p_act.empty else 0})
            filas.append({'Mes': MESES[m - 1], 'Período': ANT,
                          'Cristales': (p_ant['fecha'].dt.month == m).sum() if not p_ant.empty else 0})
        actual_vs_anterior(pd.DataFrame(filas), 'Mes', 'Cristales', ACT, ANT, None, formato=' cristales', alto=360)

    seccion('Cristales más pedidos', f'top 10 del período {ACT}')
    if not p_act.empty:
        tc = p_act['cristal'].value_counts().head(10).reset_index()
        tc.columns = ['cristal', 'pedidos']
        barras_h(tc, 'pedidos', 'cristal', None, formato=' cristales', alto=340)


# =============================================================================
# 11. Pestaña: Rentabilidad
# =============================================================================
with tabs[4]:
    if costos.empty:
        sin_datos('El informe de costos no está cargado.')
    else:
        st.info(f'El informe de costos cubre solo del {costos["fecha"].min():%d-%m-%Y} al '
                f'{costos["fecha"].max():%d-%m-%Y} ({miles(costos["ot"].nunique())} OT), por eso esta '
                f'pestaña no usa el filtro de período. Parte de los costos de cristales son un supuesto '
                f'(40% del precio de venta) y no un costo real.')
        ok = costos[costos['costeable']]
        sin_costo = 100 * (~costos['costeable']).mean()
        supuesto = 100 * ok['costo_supuesto'].mean() if len(ok) else np.nan
        fila_kpi([
            tarjeta('Venta costeada', mm(ok['venta'].sum()), None, f'{miles(len(ok))} líneas con costo'),
            tarjeta('Costo directo', mm(ok['costo'].sum()), None, 'armazones, cristales y otros'),
            tarjeta('Margen bruto estimado', pct(100 * ok['utilidad'].sum() / ok['venta'].sum()), None,
                    'sobre la venta costeada'),
            tarjeta('Líneas sin costo', pct(sin_costo), None, f'{pct(supuesto)} con costo supuesto'),
        ])

        col1, col2 = st.columns(2, gap='medium')
        with col1:
            seccion('Margen bruto por familia', 'venta − costo directo, sobre la venta')
            fam = ok.groupby('familia').agg(venta=('venta', 'sum'), costo=('costo', 'sum')).reset_index()
            fam['margen'] = 100 * (fam['venta'] - fam['costo']) / fam['venta']
            fam['texto'] = fam['margen'].apply(pct)
            barras_h(fam, 'margen', 'familia', None, formato='%', etiqueta='texto', alto=320)
        with col2:
            seccion('Venta y costo por familia', 'montos del informe de costos')
            vc = fam.melt(id_vars='familia', value_vars=['venta', 'costo'], var_name='Monto', value_name='valor')
            vc['Monto'] = vc['Monto'].map({'venta': 'Venta', 'costo': 'Costo'})
            fig = px.bar(vc, x='familia', y='valor', color='Monto', barmode='group',
                         color_discrete_map={'Venta': AZUL, 'Costo': NARANJO})
            fig.update_traces(marker_line_width=0, hovertemplate='%{x}<br>$%{y:,.0f}<extra>%{fullData.name}</extra>')
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            mostrar(fig, 320)

        seccion('Productos: venta vs margen', 'productos con 5 o más líneas · tamaño = cantidad de líneas')
        prod = ok.groupby('producto').agg(lineas=('venta', 'size'), venta=('venta', 'sum'),
                                         costo=('costo', 'sum'), familia=('familia', 'first')).reset_index()
        prod = prod[prod['lineas'] >= 5]
        prod['margen'] = 100 * (prod['venta'] - prod['costo']) / prod['venta']
        fig = px.scatter(prod, x='venta', y='margen', size='lineas', color='familia', hover_name='producto',
                         color_discrete_map=COLOR_FAMILIA, size_max=28)
        fig.update_traces(marker=dict(line=dict(color='white', width=1.5), opacity=0.85),
                          hovertemplate='<b>%{hovertext}</b><br>Venta $%{x:,.0f}<br>Margen %{y:.1f}%<extra></extra>')
        fig.update_layout(xaxis_title='venta ($)', yaxis_title='margen (%)', xaxis_showgrid=True,
                          xaxis_gridcolor=GRILLA)
        mostrar(fig, 400)

        col1, col2 = st.columns(2, gap='medium')
        def tabla_productos(df):
            return pd.DataFrame({'Producto': df['producto'], 'Líneas': df['lineas'],
                                 'Venta': df['venta'].apply(clp), 'Margen': df['margen'].apply(pct)})
        with col1:
            seccion('Top 10 por venta')
            st.dataframe(tabla_productos(prod.sort_values('venta', ascending=False).head(10)), hide_index=True)
        with col2:
            seccion('Top 10 de menor margen')
            st.dataframe(tabla_productos(prod.sort_values('margen').head(10)), hide_index=True)

    seccion('Inventario de armazones', 'margen de lista: precio de venta vs precio de compra cargado')
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
        pv = inv_ok.groupby('proveedor').agg(items=('margen_pct', 'size'), margen=('margen_pct', 'mean'),
                                             precio=('p_venta', 'median')).reset_index()
        pv = pv.sort_values('items', ascending=False).head(10)
        pv['texto'] = pv['margen'].apply(pct)
        barras_h(pv, 'margen', 'proveedor', 'Margen de lista promedio por proveedor (10 con más ítems)',
                 formato='%', etiqueta='texto', alto=360)


# =============================================================================
# 12. Pestaña: Convenios
# =============================================================================
with tabs[5]:
    if convenios.empty:
        sin_datos('La planilla de convenios no está cargada.')
    else:
        n = len(convenios)
        con_estado = 100 * (convenios['estado'] != 'Sin estado').mean()
        fechas_act = convenios['ultima_actualizacion'].fillna('').astype(str).str.strip()
        con_act = 100 * (~fechas_act.isin(['', 'nan', 'NaT', 'None'])).mean()
        recientes = (convenios['anio_firma'] >= int(anio) - 2).sum()
        fila_kpi([
            tarjeta('Convenios registrados', miles(n), None, 'empresas, municipios e instituciones'),
            tarjeta('Con estado declarado', pct(con_estado), None, 'vigente / vencido / por actualizar'),
            tarjeta('Con fecha de actualización', pct(con_act), None, 'seguimiento de la cartera'),
            tarjeta(f'Firmados desde {int(anio) - 2}', miles(recientes), None, 'convenios recientes'),
        ])
        col1, col2 = st.columns(2, gap='medium')
        with col1:
            seccion('Convenios por categoría')
            cat = convenios['categoria'].value_counts().reset_index()
            cat.columns = ['categoria', 'n']
            barras_h(cat, 'n', 'categoria', None, formato=' convenios', etiqueta='n', alto=300)
        with col2:
            seccion('Año de firma de los convenios', 'antigüedad de la cartera')
            af = convenios.dropna(subset=['anio_firma'])['anio_firma'].astype(int).value_counts().sort_index().reset_index()
            af.columns = ['año', 'n']
            af['año'] = af['año'].astype(str)
            fig = px.bar(af, x='año', y='n')
            fig.update_traces(marker_color=AZUL, hovertemplate='%{x}<br>%{y} convenios<extra></extra>')
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            mostrar(fig, 300)

        seccion('Cartera de convenios', 'filtra por categoría o busca por nombre')
        col1, col2 = st.columns([1, 2])
        cats = col1.multiselect('Categoría', sorted(convenios['categoria'].unique()))
        buscar = col2.text_input('Buscar organización', '')
        tabla = convenios.copy()
        if cats:
            tabla = tabla[tabla['categoria'].isin(cats)]
        if buscar:
            tabla = tabla[tabla['organizacion'].str.contains(buscar, case=False, na=False)]
        st.dataframe(pd.DataFrame({
            'Organización': tabla['organizacion'], 'Categoría': tabla['categoria'],
            'Año firma': tabla['anio_firma'].apply(lambda x: '' if pd.isna(x) else str(int(x))),
            'Estado': tabla['estado'], 'Tipo de gestión': tabla['tipo_gestion'],
        }), hide_index=True, height=360)


# =============================================================================
# 13. Pestaña: Calidad de datos
# =============================================================================
with tabs[6]:
    neg = (inventario['saldo_sala'] < 0).sum() if not inventario.empty else 0
    sin_est = (convenios['estado'] == 'Sin estado').sum() if not convenios.empty else 0
    sin_or = 100 * (s_act['origen'] == 'Sin registro').mean() if not s_act.empty else np.nan
    fila_kpi([
        tarjeta('Venta con OT mal o no registrada', pct(pct_error(v_act)), None, f'período {ACT}'),
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
        fig.update_traces(line=dict(color=ROJO, width=2), marker=dict(size=7, color=ROJO),
                          hovertemplate='%{x}<br>%{y:.1f}%<extra></extra>')
        fig.update_layout(xaxis_title=None, yaxis_title='%', xaxis_type='category')
        mostrar(fig, 320)
    with col2:
        seccion('Registro de OT por vendedora', f'% de líneas con OT mal o no registrada · {ACT}')
        if v_act.empty:
            sin_datos()
        else:
            ev = v_act.assign(error=v_act['estado_ot'] != 'Registrada').groupby('vendedora').agg(
                lineas=('error', 'size'), errores=('error', 'sum')).reset_index()
            ev = ev[ev['lineas'] >= 20]
            ev['pct'] = 100 * ev['errores'] / ev['lineas']
            ev['texto'] = ev['pct'].apply(pct)
            barras_h(ev, 'pct', 'vendedora', None, color=ROJO, formato='%', etiqueta='texto', alto=320)

    seccion('Trazabilidad de la OT entre sistemas', 'la OT es la llave que une venta, pedido, entrega y costo')
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
    st.dataframe(pd.DataFrame([{'Cruce': c, 'Sin match': miles(a), 'Universo': miles(b),
                                '%': pct(100 * a / b if b else np.nan)} for c, a, b in cruces]),
                 hide_index=True)

    seccion('Auditoría de calidad', 'hallazgos para pedir correcciones a TI')
    con_c = (ot_conv.shape[0])
    hallazgos = [
        ('CRÍTICA', 'OT convenio', 'El canal convenio no registra ningún precio', f'{miles(con_c)} OT sin valorizar'),
        ('CRÍTICA', 'Inventario', 'Ítems con saldo negativo en sala', f'{miles(neg)} ítems'),
        ('CRÍTICA', 'Convenios', 'Convenios sin estado (vigente / vencido)', f'{miles(sin_est)} de {miles(len(convenios))}'),
        ('ALTA', 'Ventas', 'Monto con OT mal o no registrada (toda la historia)', pct(pct_error(ventas))),
        ('ALTA', 'OT sala', 'OT sin profesional de origen registrado',
         pct(100 * (ot_sala['origen'] == 'Sin registro').mean()) if not ot_sala.empty else '–'),
        ('ALTA', 'Costos', 'Líneas del informe de costos sin costo o sin precio',
         pct(100 * (~costos['costeable']).mean()) if not costos.empty else '–'),
        ('MEDIA', 'OT sala', 'OT sin fecha de entrega real',
         pct(100 * ot_sala['fecha_entrega'].isna().mean()) if not ot_sala.empty else '–'),
        ('MEDIA', 'Pedidos', 'Nombre de proveedor escrito de varias formas', 'normalizado en este dashboard'),
    ]
    color_crit = {'CRÍTICA': ROJO, 'ALTA': '#E07B00', 'MEDIA': '#B58900'}
    filas = ''.join(f'<tr><td><span class="chip" style="background:{color_crit[c]}">{c}</span></td>'
                    f'<td>{f}</td><td>{h}</td><td><b>{v}</b></td></tr>' for c, f, h, v in hallazgos)
    st.markdown(f'<table class="tabla"><tr><th>Criticidad</th><th>Fuente</th><th>Hallazgo</th>'
                f'<th>Magnitud</th></tr>{filas}</table>', unsafe_allow_html=True)


# =============================================================================
# 14. Pestaña: Datos
# =============================================================================
with tabs[7]:
    seccion('Bases cargadas', 'de dónde viene cada tabla y qué período cubre')
    resumen = []
    for clave, info in pr.BASES.items():
        df = datos[clave]
        tiene_fecha = 'fecha' in df.columns and not df.empty
        resumen.append({
            'Base': info['nombre'],
            'Origen': origen_datos[clave],
            'Filas': miles(len(df)),
            'Desde': f'{df["fecha"].min():%d-%m-%Y}' if tiene_fecha else '',
            'Hasta': f'{df["fecha"].max():%d-%m-%Y}' if tiene_fecha else '',
        })
    st.dataframe(pd.DataFrame(resumen), hide_index=True)

    seccion('¿Cómo actualizar los datos?')
    st.markdown("""
1. **Rápido (solo para esta sesión):** abre *Cargar / actualizar bases de datos* en la barra lateral
   y sube las planillas originales. Se reconocen por el nombre del archivo:
   `CONSOLIDADO VENTAS ... NUBOX`, `OT APPS FINAL - ÓPTICA SALA DE VENTA`, `OT APPS CONVENIO FINAL`,
   `Centralización Cristales - SOLICITUD_CRISTALES`, `informe_costos_analitico`,
   `OT APPS FINAL - INVENTARIO ARMAZONES` y `Convenios COALIVI`.
2. **Permanente (para todos los que abren el link):** vuelve a correr el notebook de Colab con las
   planillas nuevas en Drive. Regenera la carpeta `data/` y la sube a GitHub; Streamlit se actualiza solo.
""")

    seccion('Descargar tablas limpias', 'en CSV, para usarlas en Excel o Power BI')
    columnas = st.columns(4)
    for n_, (clave, info) in enumerate(pr.BASES.items()):
        df = datos[clave]
        if not df.empty:
            columnas[n_ % 4].download_button(info['nombre'], df.to_csv(index=False).encode('utf-8-sig'),
                                             file_name=f'coalivi_{clave}.csv', mime='text/csv',
                                             key=f'descarga_{clave}')

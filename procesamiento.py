# procesamiento.py
# Limpieza de las planillas de la sala de ventas de la Óptica COALIVI (foco: venta particular).
# Lo usan:
#   - generar_datos.py  -> para crear la carpeta data/ desde las planillas originales
#   - app.py            -> cuando alguien sube planillas nuevas desde la barra lateral
# MDF Consulting · 2026

import io
import re
import unicodedata

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Catálogo de bases
# ---------------------------------------------------------------------------
# Para cada base: palabras que pueden aparecer en el nombre del archivo, hoja y fila del encabezado
BASES = {
    'ventas':  {'claves': ['CONSOLIDADO VENTAS'], 'hoja': 0, 'header': 0,
                'nombre': 'Boletas de la sala (Nubox)'},
    'ot_sala': {'claves': ['SALA DE VENTAS PARTICULAR', 'OPTICA SALA DE VENTA'], 'hoja': 0, 'header': 0,
                'nombre': 'OT de la sala de ventas'},
    'costos':  {'claves': ['INFORME_COSTOS_SALA', 'INFORME COSTOS SALA', 'INFORME_COSTOS_ANALITICO'], 'hoja': 0, 'header': 0,
                'nombre': 'Informe de costos de la sala'},
}

# Planillas que se reconocen pero quedan fuera: licitaciones y convenio institucional (fuera del foco particular)
EXCLUIDAS = ['APPS CONVENIO', 'COSTOS_CONVENIO', 'COSTOS CONVENIO']

# Columnas de fecha de cada tabla limpia (para leer los .csv.gz con el tipo correcto)
FECHAS = {
    'ventas': ['fecha'],
    'ot_sala': ['fecha', 'fecha_prometida', 'fecha_entrega'],
    'costos': ['fecha'],
}

# Líneas de producto para el estado de resultados
LINEAS = ['Cristales', 'Armazones', 'Lentes de sol', 'Accesorios y líquidos', 'Reparaciones y otros']
TIPO_A_LINEA = {'CRISTALES': 'Cristales', 'ARMAZON': 'Armazones', 'GAFA': 'Lentes de sol',
                'ACCESORIO': 'Accesorios y líquidos', 'LIQUIDO': 'Accesorios y líquidos'}
# Familias del informe de costos -> líneas
FAMILIA_A_LINEA = {'CRISTAL': 'Cristales', 'ARMAZON': 'Armazones', 'GAFAS': 'Lentes de sol',
                   'ACCESORIO': 'Accesorios y líquidos'}


# ---------------------------------------------------------------------------
# 2. Funciones de apoyo
# ---------------------------------------------------------------------------
def sin_tildes(texto):
    # Quita tildes, pasa a mayúscula y saca espacios dobles
    if pd.isna(texto):
        return np.nan
    limpio = unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', limpio).upper().strip()


def a_numero(serie):
    # Convierte a número lo que viene como texto ('30.000', ' 30000 ', '#N/A')
    if pd.api.types.is_numeric_dtype(serie):
        return serie.astype(float)
    texto = serie.astype(str).str.replace(r'[^0-9,.\-]', '', regex=True)
    texto = texto.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    return pd.to_numeric(texto, errors='coerce')


def a_fecha(serie):
    # Los datos parten en 2024: fechas anteriores o imposibles (año 202, futuras) quedan vacías
    # Se deja solo el día (sin hora) para que todas las fechas se guarden con el mismo formato
    fecha = pd.to_datetime(serie, errors='coerce').dt.normalize()
    hoy = pd.Timestamp.today().normalize()
    return fecha.where(fecha.between('2024-01-01', hoy))


def extraer_ot(serie):
    # La OT viene mezclada con texto ('121053 EFECT MARITZ') o como 122732.0: rescatamos el número
    return serie.astype(str).str.extract(r'(\d{5,7})')[0]


def agregar_periodo(df, col='fecha'):
    # Columnas de año y mes (primer día del mes) para agrupar
    df['anio'] = df[col].dt.year.astype('Int64')
    df['mes'] = df[col].dt.to_period('M').dt.to_timestamp()
    return df


def nombre_vendedora(serie):
    # Unifica nombres de vendedoras ('JUANPABLO' y 'JUAN PABLO' son la misma)
    s = serie.apply(sin_tildes).replace({'JUANPABLO': 'JUAN PABLO', 'SIN VENDEDORA': np.nan})
    return s.str.title().fillna('Sin registro')


def forma_de_pago(serie):
    # La forma de pago viene escrita de muchas formas
    p = serie.apply(sin_tildes)
    return np.select(
        [p.str.contains('DEBITO', na=False), p.str.contains('EFECTIVO', na=False),
         p.str.contains('TRANSFER', na=False), p.str.contains('CREDITO', na=False)],
        ['Crédito / Débito', 'Efectivo', 'Transferencia', 'Crédito directo'],
        default='Otro / sin dato')


def linea_producto(tipo):
    # Todo lo que no calza con las 4 primeras líneas va a 'Reparaciones y otros'
    return TIPO_A_LINEA.get(sin_tildes(tipo), 'Reparaciones y otros')


def segmento(convenio):
    # Agrupa los "convenios" de la OT de sala en 3 segmentos (el dashboard muestra solo Particular)
    c = str(convenio)
    if c in ('PARTICULAR', 'NAN', ''):
        return 'Particular'
    if c.startswith(('DAS', 'SSC', 'COSADES')):
        return 'Licitación (DAS/SSC/COSADES)'
    return 'Convenios y operativos'


def limpiar_origen(serie):
    # ORIGEN = profesional que derivó al paciente. Devuelve (nombre, tipo de profesional)
    o = serie.apply(sin_tildes).replace({'NO REGISTRA': np.nan, 'NAN': np.nan, 'OTROS': np.nan})
    prefijo = pd.Series(np.select([o.str.match(r'^DRA?\.', na=False), o.str.match(r'^TEC\.', na=False)],
                                  ['Oftalmólogo/a', 'Tecnólogo/a médico'], default='Otro'), index=o.index)
    nombre = o.str.replace(r'^(DRA?\.|TEC\.|PROF\.)\s*', '', regex=True).str.strip()
    # Un mismo profesional aparece a veces con 'TEC.' y otras sin título: le asignamos el tipo conocido
    con_titulo = prefijo != 'Otro'
    tipo_conocido = dict(zip(nombre[con_titulo], prefijo[con_titulo]))
    tipo = nombre.map(tipo_conocido).fillna('Otro')
    tipo[nombre.isna()] = 'Sin registro'
    return nombre.str.title().fillna('Sin registro'), tipo


def columna(df, nombre):
    # Devuelve la columna si existe; si no, una columna vacía (para columnas opcionales)
    return df[nombre] if nombre in df.columns else pd.Series(np.nan, index=df.index)


# ---------------------------------------------------------------------------
# 3. Limpieza de cada base
# ---------------------------------------------------------------------------
def limpiar_ventas(df):
    v = pd.DataFrame()
    v['fecha'] = a_fecha(df['Fecha Emision'])
    v['folio'] = df['Folio']
    v['producto'] = df['Producto'].fillna('').astype(str)
    v['tipo'] = df['Tipo'].fillna('OTRO').astype(str).str.strip()
    v['linea'] = v['tipo'].apply(linea_producto)
    v['cantidad'] = a_numero(df['Cantidad'])
    v['precio'] = a_numero(df['Precio'])
    v['total'] = a_numero(df['Total'])                     # con IVA
    v['vendedora'] = nombre_vendedora(df['Codigo Vendedor'])
    v['forma_pago'] = forma_de_pago(df['Forma de pago'])

    # Estado de registro de la OT en el sistema (9 formas de escribir 3 estados)
    estado = df['ESTADO OT SISTEMA'].apply(sin_tildes)
    v['estado_ot'] = np.select(
        [estado.str.contains('MAL', na=False), estado.str.contains('NO REG', na=False)],
        ['Mal registrada', 'No registrada'], default='Registrada')

    # Una venta se parte en abono + saldo, por eso se marca el tipo de línea
    prod = v['producto'].str.upper()
    v['clase_linea'] = np.where(prod.str.contains('ABONO', na=False), 'Abono',
                                np.where(prod.str.contains('SALDO', na=False), 'Saldo', 'Venta directa'))
    v['es_nc'] = df['nota de credito'].apply(sin_tildes).eq('NC')
    v['ot'] = extraer_ot(df['ot no registradas'])

    v = v.dropna(subset=['fecha', 'total'])
    return agregar_periodo(v)


def limpiar_ot_sala(df):
    df = df.drop_duplicates(subset=['OT', 'FECHA OT', 'total', 'VENDEDORA', 'CONVENIO'])
    s = pd.DataFrame()
    s['ot'] = extraer_ot(df['OT'])
    s['fecha'] = a_fecha(df['FECHA OT'])
    s['vendedora'] = nombre_vendedora(df['VENDEDORA'])
    s['convenio'] = df['CONVENIO'].apply(sin_tildes).fillna('PARTICULAR')
    s['segmento'] = s['convenio'].apply(segmento)
    s['origen'], s['origen_tipo'] = limpiar_origen(df['ORIGEN'])
    s['total'] = a_numero(df['total']).fillna(0)           # con IVA

    # Descuento: casi siempre es un %, a veces texto ('discapacidad', 'socios', 'desct10')
    s['con_descuento'] = df['descT'].notna()
    d = df['descT'].astype(str).str.extract(r'(\d+)')[0].astype(float)
    s['descuento_pct'] = d.where(d.between(1, 50))
    s['forma_pago'] = forma_de_pago(columna(df, 'efectivo total'))
    s['estado'] = df['estado de ot'].apply(sin_tildes).fillna('SIN ESTADO')

    # Plazos: fecha prometida al cliente vs fecha real de entrega
    s['fecha_prometida'] = a_fecha(df['Fecha de entrega'])
    s['fecha_entrega'] = a_fecha(df['FECHA ENTREGA'])
    dias = (s['fecha_entrega'] - s['fecha']).dt.days
    s['lead_time'] = dias.where(dias.between(0, 120))
    s['atraso'] = (s['fecha_entrega'] - s['fecha_prometida']).dt.days

    s = s.dropna(subset=['fecha'])
    return agregar_periodo(s)


def limpiar_costos(df):
    # Una fila = un producto de una OT (armazón, cada cristal, gafa, accesorio)
    df = df.drop_duplicates()
    k = pd.DataFrame()
    k['fecha'] = a_fecha(df['Fecha'])
    k['ot'] = extraer_ot(df['OT'])
    k['vendedora'] = nombre_vendedora(df['Vendedora'])
    k['familia'] = df['Familia'].fillna('Sin familia')
    k['linea'] = k['familia'].apply(lambda f: FAMILIA_A_LINEA.get(sin_tildes(f), 'Reparaciones y otros'))
    k['tipo'] = df['Tipo']
    k['uso'] = columna(df, 'Uso').fillna('Sin dato')
    k['tipo_lente'] = columna(df, 'V5_TIPO_LENTE_MATCH').fillna('Sin dato')
    k['producto'] = columna(df, 'Producto Analítico').fillna(df['Producto']).astype(str)
    k['producto'] = k['producto'].where(~k['producto'].str.fullmatch(r'\s*\d*\s*'), 'Sin nombre comercial')
    prov = df['PROVEEDOR'].apply(sin_tildes)
    k['proveedor'] = prov.str.replace(r'MERCAVIS.*', 'MERCAVISION', regex=True).fillna('Sin dato')

    cant = a_numero(df['Cantidad'])
    precio = a_numero(df['Pventa Unitario'])
    costo_unit = a_numero(df['Pcosto Unitario'])

    # Arreglo 1: cantidad y precio invertidos (gafas con cantidad = 119.900 y precio = 1)
    invertido = (cant > 1000) & (precio <= 1)
    precio = precio.where(~invertido, cant)
    cant = cant.where(~invertido, 1)

    # Arreglo 2: separador de miles mal leído (14.99 -> 14.990)
    mal_miles = (precio > 0) & (precio < 200)
    precio = precio.where(~mal_miles, precio * 1000)

    k['cantidad'] = cant
    k['venta'] = precio * cant                             # con IVA
    k['arreglo'] = np.select([invertido, mal_miles], ['Cantidad y precio invertidos', 'Separador de miles'], default='')

    # Arreglo 3: costo (neto). Cristales: costo nuevo con listas de proveedores (V5, preliminar) si existe
    costo_informe = (costo_unit * cant).fillna(0)
    costo_v5 = a_numero(columna(df, 'V5_COSTO_TOTAL_NUEVO'))
    usa_v5 = k['familia'].eq('Cristal') & costo_v5.notna()
    k['costo'] = np.where(usa_v5, costo_v5, costo_informe)
    k['fuente_costo'] = np.select([usa_v5, costo_informe > 0],
                                  ['Lista proveedores V5 (preliminar)', 'Informe de costos'], default='Sin costo')
    k['costeable'] = (k['venta'] > 0) & (k['costo'] > 0)
    k = k.dropna(subset=['fecha'])
    return agregar_periodo(k)


LIMPIEZA = {'ventas': limpiar_ventas, 'ot_sala': limpiar_ot_sala, 'costos': limpiar_costos}


# ---------------------------------------------------------------------------
# 4. Identificar, leer y procesar un archivo original
# ---------------------------------------------------------------------------
# Columnas que necesita cada base: sirven para reconocer la planilla por su contenido
# y para avisar con claridad si le falta alguna columna
COLUMNAS = {
    'ventas': ['Fecha Emision', 'Folio', 'Producto', 'Tipo', 'Cantidad', 'Precio', 'Total',
               'Codigo Vendedor', 'Forma de pago', 'ESTADO OT SISTEMA', 'nota de credito', 'ot no registradas'],
    'ot_sala': ['OT', 'FECHA OT', 'VENDEDORA', 'CONVENIO', 'ORIGEN', 'total', 'descT',
                'estado de ot', 'Fecha de entrega', 'FECHA ENTREGA'],
    'costos': ['Fecha', 'OT', 'Vendedora', 'Familia', 'Tipo', 'Producto', 'Cantidad',
               'Pventa Unitario', 'Pcosto Unitario', 'PROVEEDOR'],
}


def _abrir(archivo):
    # Deja el archivo listo para leerlo varias veces (ruta o bytes de un archivo subido)
    if isinstance(archivo, (bytes, bytearray)):
        return io.BytesIO(archivo)
    if hasattr(archivo, 'seek'):
        archivo.seek(0)
    return archivo


def leer_excel(archivo, **kwargs):
    # calamine es mucho más rápido; si no está instalado se usa openpyxl
    try:
        return pd.read_excel(_abrir(archivo), engine='calamine', **kwargs)
    except Exception:
        return pd.read_excel(_abrir(archivo), **kwargs)


def _faltantes(columnas, clave):
    presentes = {sin_tildes(c) for c in columnas}
    return [c for c in COLUMNAS[clave] if sin_tildes(c) not in presentes]


def identificar_por_nombre(nombre_archivo):
    n = sin_tildes(nombre_archivo)
    for clave, info in BASES.items():
        if any(palabra in n for palabra in info['claves']):
            return clave
    return None


def identificar_por_columnas(archivo):
    # Ve con qué base calzan los encabezados de la primera hoja (al menos el 80% de las columnas)
    try:
        columnas = leer_excel(archivo, sheet_name=0, nrows=0).columns
    except Exception:
        return None
    mejor, mejor_pct = None, 0
    for clave in COLUMNAS:
        p = 1 - len(_faltantes(columnas, clave)) / len(COLUMNAS[clave])
        if p > mejor_pct:
            mejor, mejor_pct = clave, p
    return mejor if mejor_pct >= 0.8 else None


def normalizar_columnas(df, clave):
    # Si TI cambia mayúsculas o tildes de una columna, se deja con el nombre que espera el código
    canonico = {sin_tildes(c): c for c in COLUMNAS[clave]}
    df = df.copy()
    df.columns = [canonico.get(sin_tildes(c), c) for c in df.columns]
    return df


def procesar_archivo(archivo, nombre_archivo):
    # Reconoce, lee, revisa y limpia un archivo original. Devuelve (clave, tabla_limpia)
    n = sin_tildes(nombre_archivo)
    if any(x in n for x in EXCLUIDAS):
        raise ValueError('es una planilla de convenio / licitación: queda fuera del foco de venta particular.')
    clave = identificar_por_nombre(nombre_archivo) or identificar_por_columnas(archivo)
    if clave is None:
        raise ValueError('no corresponde a ninguna base del dashboard (ni por su nombre ni por sus columnas).')
    bruto = normalizar_columnas(leer_excel(archivo, sheet_name=BASES[clave]['hoja'],
                                           header=BASES[clave]['header']), clave)
    faltan = _faltantes(bruto.columns, clave)
    if faltan:
        raise ValueError(f'parece ser la planilla de "{BASES[clave]["nombre"]}", pero le faltan las '
                         f'columnas: {", ".join(faltan)}. Revisar con TI si cambiaron de nombre.')
    return clave, LIMPIEZA[clave](bruto)


# ---------------------------------------------------------------------------
# 5. Guardar y leer las tablas limpias (carpeta data/)
# ---------------------------------------------------------------------------
def guardar_tablas(tablas, carpeta='data'):
    import os
    os.makedirs(carpeta, exist_ok=True)
    for clave, df in tablas.items():
        df.to_csv(os.path.join(carpeta, f'{clave}.csv.gz'), index=False, compression='gzip')


def leer_tabla(ruta, clave):
    # 'ruta' puede ser la ruta del .csv.gz o el archivo ya abierto (por ejemplo, desde un zip)
    df = pd.read_csv(ruta, low_memory=False, compression='gzip',
                     dtype={'ot': 'object', 'folio': 'object', 'arreglo': 'object'})
    for col in FECHAS.get(clave, []):
        df[col] = pd.to_datetime(df[col], errors='coerce', format='mixed')
    for col in ('es_nc', 'costeable', 'con_descuento'):
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().eq('true')
    if 'arreglo' in df.columns:
        df['arreglo'] = df['arreglo'].fillna('')
    if 'fecha' in df.columns:
        df = agregar_periodo(df)
    return df


# ---------------------------------------------------------------------------
# 6. Filtro a venta particular (lo usa la app)
# ---------------------------------------------------------------------------
def solo_particular(ventas, ot_sala, costos):
    # La OT define qué es particular. Las boletas y los costos se filtran por el número de OT.
    s = ot_sala[ot_sala['convenio'] == 'PARTICULAR'].copy() if not ot_sala.empty else ot_sala
    ots = set(s['ot'].dropna()) if not s.empty else set()
    v = ventas.copy()
    v['es_particular'] = v['ot'].isin(ots)
    k = costos[costos['ot'].isin(ots)].copy() if not costos.empty else costos
    if not k.empty and not s.empty:
        info = s.sort_values('fecha').drop_duplicates('ot', keep='last').set_index('ot')
        k['origen_tipo'] = k['ot'].map(info['origen_tipo'])
        k['con_descuento'] = k['ot'].map(info['con_descuento'])
    return v, s, k

# procesamiento.py
# Limpieza de las planillas de la Óptica COALIVI.
# Lo usan el notebook de Colab (para generar la carpeta data/) y la app de Streamlit
# (cuando alguien sube planillas nuevas desde la barra lateral).
# MDF Consulting · 2026

import io
import re
import unicodedata

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Catálogo de bases
# ---------------------------------------------------------------------------
# Para cada base: palabras que aparecen en el nombre del archivo original,
# hoja que se lee y fila del encabezado (header de pandas).
BASES = {
    'ventas':      {'claves': ['CONSOLIDADO VENTAS', 'NUBOX'],
                    'hoja': 0, 'header': 0,
                    'nombre': 'Ventas facturadas (Nubox)'},
    'ot_sala':     {'claves': ['SALA DE VENTA'],
                    'hoja': 0, 'header': 0,
                    'nombre': 'OT sala de venta'},
    'ot_convenio': {'claves': ['APPS CONVENIO', 'OPTICA CONVENIO'],
                    'hoja': 0, 'header': 0,
                    'nombre': 'OT convenio institucional'},
    'pedidos':     {'claves': ['SOLICITUD_CRISTALES', 'CENTRALIZACION CRISTALES'],
                    'hoja': 0, 'header': 0,
                    'nombre': 'Pedidos de cristales a proveedor'},
    'costos':      {'claves': ['INFORME_COSTOS'],
                    'hoja': 'informe_costos_analitico_v3_con', 'header': 0,
                    'nombre': 'Informe de costos'},
    'inventario':  {'claves': ['INVENTARIO'],
                    'hoja': 0, 'header': 0,
                    'nombre': 'Inventario de armazones'},
    'convenios':   {'claves': ['CONVENIOS COALIVI'],
                    'hoja': None, 'header': 2,      # None = todas las hojas
                    'nombre': 'Cartera de convenios'},
}

# Columnas de fecha de cada tabla limpia (para leer los .csv.gz con el tipo correcto)
FECHAS = {
    'ventas': ['fecha'],
    'ot_sala': ['fecha', 'fecha_prometida', 'fecha_entrega'],
    'ot_convenio': ['fecha'],
    'pedidos': ['fecha'],
    'costos': ['fecha'],
    'inventario': [],
    'convenios': [],
}

MESES_ES = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
            'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10,
            'noviembre': 11, 'diciembre': 12}


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
    # Fechas como texto o datetime; las imposibles quedan vacías
    fecha = pd.to_datetime(serie, errors='coerce')
    hoy = pd.Timestamp.today().normalize()
    return fecha.where(fecha.between('2015-01-01', hoy))


def extraer_ot(serie):
    # La OT viene mezclada con texto ('121053 EFECT MARITZ'): rescatamos el número
    return serie.astype(str).str.extract(r'(\d{5,7})')[0]


def agregar_periodo(df, col='fecha'):
    # Columnas de año y mes (primer día del mes) para agrupar
    df['anio'] = df[col].dt.year.astype('Int64')
    df['mes'] = df[col].dt.to_period('M').dt.to_timestamp()
    return df


def nombre_vendedora(serie):
    # Unifica nombres de vendedoras ('JUANPABLO' y 'JUAN PABLO' son la misma)
    s = serie.apply(sin_tildes).replace({'JUANPABLO': 'JUAN PABLO', 'SIN VENDEDORA': np.nan})
    return s.fillna('Sin registro').str.title()


# Líneas de producto para el estado de resultados (según el 'Tipo' de la boleta)
LINEAS = ['Cristales', 'Armazones', 'Lentes de sol', 'Accesorios y líquidos', 'Reparaciones y otros']
TIPO_A_LINEA = {'CRISTALES': 'Cristales', 'ARMAZON': 'Armazones', 'GAFA': 'Lentes de sol',
                'ACCESORIO': 'Accesorios y líquidos', 'LIQUIDO': 'Accesorios y líquidos'}
# Familias del informe de costos -> líneas
FAMILIA_A_LINEA = {'CRISTAL': 'Cristales', 'ARMAZON': 'Armazones', 'GAFAS': 'Lentes de sol',
                   'ACCESORIO': 'Accesorios y líquidos'}


def linea_producto(tipo):
    # Todo lo que no calza con las 4 primeras líneas va a 'Reparaciones y otros'
    return TIPO_A_LINEA.get(sin_tildes(tipo), 'Reparaciones y otros')


def segmento(convenio):
    # Agrupa los convenios de la OT de sala en 3 segmentos comerciales
    c = str(convenio)
    if c in ('PARTICULAR', 'NAN', ''):
        return 'Particular'
    if re.search(r'OPERATIVO EMPRESA|CONVENIO |MUTUAL|GENDARM|IST|FUNCIONARIO|SERMECAP', c):
        return 'Empresas y convenios'
    return 'Público / social'


# ---------------------------------------------------------------------------
# 3. Limpieza de cada base
# ---------------------------------------------------------------------------
def limpiar_ventas(df):
    v = pd.DataFrame()
    v['fecha'] = a_fecha(df['Fecha Emision'])
    v['folio'] = df['Folio']
    v['producto'] = df['Producto'].fillna('').astype(str)
    v['tipo'] = df['Tipo'].fillna('OTRO').astype(str).str.strip()
    v['cantidad'] = a_numero(df['Cantidad'])
    v['precio'] = a_numero(df['Precio'])
    v['total'] = a_numero(df['Total'])
    v['vendedora'] = nombre_vendedora(df['Codigo Vendedor'])

    # Forma de pago: viene escrita de varias formas
    pago = df['Forma de pago'].apply(sin_tildes)
    v['forma_pago'] = np.select(
        [pago.str.contains('DEBITO', na=False), pago.str.contains('EFECTIVO', na=False),
         pago.str.contains('TRANSFER', na=False), pago.str.contains('CREDITO', na=False)],
        ['Crédito / Débito', 'Efectivo', 'Transferencia', 'Crédito directo'],
        default='Otro / sin dato')

    # Estado de registro de la OT en el sistema
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
    s = pd.DataFrame()
    s['ot'] = extraer_ot(df['OT'])
    s['fecha'] = a_fecha(df['FECHA OT'])
    s['vendedora'] = nombre_vendedora(df['VENDEDORA'])
    s['convenio'] = df['CONVENIO'].apply(sin_tildes).fillna('PARTICULAR')
    s['segmento'] = s['convenio'].apply(segmento)

    # Origen = profesional que deriva al paciente
    origen = df['ORIGEN'].apply(sin_tildes)
    origen = origen.str.replace(r'^TEC\.?\s*', '', regex=True)
    origen = origen.str.replace(r'^(DRA?)\.\s*', r'\1. ', regex=True)
    s['origen'] = origen.replace({'NO REGISTRA': np.nan, 'NAN': np.nan}).fillna('Sin registro')

    edad = a_numero(df['EDAD'])
    s['edad'] = edad.where(edad.between(1, 110))
    s['total'] = a_numero(df['total']).fillna(0)
    s['estado'] = df['estado de ot'].apply(sin_tildes).fillna('SIN ESTADO')

    # Plazos: fecha prometida al cliente vs fecha real de entrega
    s['fecha_prometida'] = a_fecha(df['Fecha de entrega'])
    s['fecha_entrega'] = a_fecha(df['FECHA ENTREGA'])
    dias = (s['fecha_entrega'] - s['fecha']).dt.days
    s['lead_time'] = dias.where(dias.between(0, 120))
    s['atraso'] = (s['fecha_entrega'] - s['fecha_prometida']).dt.days

    s = s.dropna(subset=['fecha'])
    return agregar_periodo(s)


def limpiar_ot_convenio(df):
    c = pd.DataFrame()
    c['ot'] = extraer_ot(df['OT'])
    c['fecha'] = a_fecha(df['FECHA OT'])
    c['vendedora'] = nombre_vendedora(df['VENDEDORA'])
    c['contraparte'] = df['CONVENIO'].apply(sin_tildes).fillna('SIN DATO')
    c['centro_origen'] = df['CENTRO DE ORIGEN'].astype('object').fillna('Sin registro').astype(str).str.strip()
    edad = a_numero(df['EDAD'])
    c['edad'] = edad.where(edad.between(1, 110))
    c = c.dropna(subset=['fecha'])
    return agregar_periodo(c)


def limpiar_pedidos(df):
    p = pd.DataFrame()

    # La fecha viene como texto: '11 de junio de 2026'
    partes = df['FECHA_PEDIDO'].astype(str).str.lower().str.extract(
        r'(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})')
    texto = partes[2] + '-' + partes[1].map(MESES_ES).astype('Int64').astype(str) + '-' + partes[0]
    p['fecha'] = a_fecha(pd.to_datetime(texto, format='%Y-%m-%d', errors='coerce'))

    prov = df['PROVEEDOR'].apply(sin_tildes).fillna('SIN DATO')
    prov = prov.str.replace(r'MERCAVIS.*', 'MERCAVISION', regex=True)
    prov = prov.str.replace(r'PEDIDOS? URGENTES?', 'PEDIDO URGENTE', regex=True)
    p['proveedor'] = prov
    p['urgente'] = prov.eq('PEDIDO URGENTE')

    cristal = df['CRISTAL'].apply(sin_tildes)
    p['cristal'] = cristal.str.replace(r'[^A-Z0-9 .+/]', '', regex=True).str.strip()
    p['ot'] = extraer_ot(df['OT'])

    p = p.dropna(subset=['fecha'])
    return agregar_periodo(p)


def limpiar_costos(df):
    k = pd.DataFrame()
    k['fecha'] = a_fecha(df['Fecha'])
    k['ot'] = extraer_ot(df['OT'])
    k['vendedora'] = nombre_vendedora(df['Vendedora'])
    k['familia'] = df['Familia'].fillna('Sin familia')
    k['tipo'] = df['Tipo']
    k['producto'] = df['Producto Analítico'].fillna(df['Producto']).astype(str)
    k['venta'] = a_numero(df['Pventa Total']).fillna(0)
    k['costo'] = a_numero(df['Pcosto Total']).fillna(0)
    k['utilidad'] = k['venta'] - k['costo']
    k['costeable'] = (k['venta'] > 0) & (k['costo'] > 0)
    # Costo "supuesto": cuando el costo es exactamente el 40% del precio
    k['costo_supuesto'] = k['costeable'] & ((k['costo'] / k['venta'].where(k['venta'] > 0)).round(3) == 0.4)
    k['costo_match'] = df['Costo Match'].fillna('Sin dato')
    k['proveedor'] = df['PROVEEDOR'].apply(sin_tildes).fillna('SIN DATO')
    k = k.dropna(subset=['fecha'])
    return agregar_periodo(k)


def limpiar_inventario(df):
    i = pd.DataFrame()
    i['codigo'] = df['CODIGO'].apply(lambda x: '' if pd.isna(x) else str(int(x)) if isinstance(x, float) else str(x))
    i['nombre'] = df['NOMBRE ITEM']
    i['tipo_item'] = df['TIPO ITEM'].apply(sin_tildes)
    i['marca'] = df['MARCA'].apply(sin_tildes)
    i['material'] = df['MATERIAL'].apply(sin_tildes)
    i['proveedor'] = df['PROVEEDOR'].apply(sin_tildes).fillna('SIN DATO')
    i['linea'] = df['ADICIONAL'].apply(sin_tildes).fillna('SIN DATO')
    i['saldo_sala'] = a_numero(df['S.VENTAS'])
    i['p_compra'] = a_numero(df['P.COMPRA'])
    # Hay dos columnas P.VENTA: pandas deja la primera como 'P.VENTA'
    i['p_venta'] = a_numero(df['P.VENTA'])
    valido = (i['p_compra'] > 0) & (i['p_venta'] > 0)
    i['margen_pct'] = np.where(valido, 100 * (i['p_venta'] - i['p_compra']) / i['p_venta'], np.nan)
    return i


def limpiar_convenios(hojas):
    # 'hojas' es un diccionario {nombre_hoja: DataFrame} con las 4 categorías
    categorias = {'EMPRESA': 'Empresa', 'MUNICIPAL': 'Municipalidad',
                  'INSTITUCION': 'Institución', 'CORPORACION': 'Corporación'}
    tablas = []
    for hoja, d in hojas.items():
        d = d.dropna(how='all').copy()
        d.columns = [str(x).strip() for x in d.columns]
        hoja_n = sin_tildes(hoja)
        categoria = next((v for k, v in categorias.items() if k in hoja_n), hoja.strip().title())

        # La columna con el nombre de la organización cambia de nombre en cada hoja
        col_nombre = [x for x in d.columns
                      if sin_tildes(x).startswith(('EMPRESA', 'MUNICIPALIDAD', 'INSTITUCION',
                                                   'COORPORACION', 'CORPORACION'))]
        if not col_nombre:
            continue
        t = pd.DataFrame()
        t['organizacion'] = d[col_nombre[0]].astype('object')
        t['categoria'] = categoria
        t['anio_firma'] = a_numero(d.get('Fecha convenio', pd.Series(index=d.index, dtype=float)))
        t['ultima_actualizacion'] = d.get('Ultima actualización', pd.Series(index=d.index, dtype=object)).astype('object')
        t['estado'] = d.get('Estado', pd.Series(index=d.index, dtype=object)).astype('object').fillna('Sin estado')
        t['tipo_gestion'] = d.get('Tipo de Gestión', pd.Series(index=d.index, dtype=object)).astype('object').fillna('Sin dato')
        tablas.append(t)

    conv = pd.concat(tablas, ignore_index=True)
    conv = conv.dropna(subset=['organizacion'])
    conv['organizacion'] = conv['organizacion'].astype(str).str.strip()
    conv['ultima_actualizacion'] = conv['ultima_actualizacion'].fillna('').astype(str).replace({'nan': ''})
    return conv


LIMPIEZA = {
    'ventas': limpiar_ventas,
    'ot_sala': limpiar_ot_sala,
    'ot_convenio': limpiar_ot_convenio,
    'pedidos': limpiar_pedidos,
    'costos': limpiar_costos,
    'inventario': limpiar_inventario,
    'convenios': limpiar_convenios,
}


# ---------------------------------------------------------------------------
# 4. Identificar, leer y procesar un archivo original
# ---------------------------------------------------------------------------
def identificar(nombre_archivo):
    # Devuelve la clave de la base según el nombre del archivo (o None)
    n = sin_tildes(nombre_archivo)
    for clave, info in BASES.items():
        if any(palabra in n for palabra in info['claves']):
            return clave
    return None


def leer_original(archivo, clave):
    # 'archivo' puede ser una ruta o los bytes de un archivo subido
    if isinstance(archivo, (bytes, bytearray)):
        archivo = io.BytesIO(archivo)
    info = BASES[clave]
    hoja = info['hoja']
    if isinstance(hoja, str):
        # Si la hoja con ese nombre no existe, se usa la primera
        hojas = pd.ExcelFile(archivo).sheet_names
        hoja = hoja if hoja in hojas else 0
        if hasattr(archivo, 'seek'):
            archivo.seek(0)
    return pd.read_excel(archivo, sheet_name=hoja, header=info['header'])


def procesar_archivo(archivo, nombre_archivo):
    # Lee y limpia un archivo original. Devuelve (clave, tabla_limpia)
    clave = identificar(nombre_archivo)
    if clave is None:
        raise ValueError('no corresponde a ninguna base del dashboard, se ignoró.')
    bruto = leer_original(archivo, clave)
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
                     dtype={'ot': 'object', 'codigo': 'object', 'folio': 'object'})
    # Fechas y verdadero/falso vuelven como texto desde el CSV: se convierten
    for col in FECHAS.get(clave, []):
        df[col] = pd.to_datetime(df[col], errors='coerce')
    for col in ('es_nc', 'costeable', 'costo_supuesto', 'urgente'):
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().eq('true')
    if 'fecha' in df.columns:
        df = agregar_periodo(df)
    return df

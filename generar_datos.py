# generar_datos.py
# Crea la carpeta data/ (tablas limpias .csv.gz) a partir de las planillas originales de COALIVI.
#
# Uso (en el computador o en Colab):
#   python generar_datos.py "carpeta/con/las/planillas"
#
# Reconoce sola estas planillas (aunque cambien un poco de nombre):
#   - CONSOLIDADO VENTAS ÓPTICA Y OT + BOLETAS_.xlsx
#   - OT APPS FINAL - Sala de ventas particular.xlsx
#   - informe_costos_Sala_ventas__particulaes_16-10-2026.xlsx
# Las planillas de convenio / licitaciones se saltan (fuera del foco particular).

import os
import sys

import procesamiento as pr

carpeta = sys.argv[1] if len(sys.argv) > 1 else '.'
salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

tablas = {}
for nombre in sorted(os.listdir(carpeta)):
    if not nombre.lower().endswith('.xlsx') or nombre.startswith('~$'):
        continue
    try:
        clave, tabla = pr.procesar_archivo(os.path.join(carpeta, nombre), nombre)
    except ValueError as aviso:
        print(f'(se salta) {nombre}: {aviso}')
        continue
    tablas[clave] = tabla
    print(f'OK  {pr.BASES[clave]["nombre"]:32s} {len(tabla):>8,} filas  <- {nombre}')

faltan = [c for c in pr.BASES if c not in tablas]
if faltan:
    print('OJO, faltan planillas:', ', '.join(pr.BASES[c]['nombre'] for c in faltan))

pr.guardar_tablas(tablas, salida)
print('Tablas guardadas en', salida)

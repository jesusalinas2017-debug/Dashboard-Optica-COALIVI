# Dashboard Ejecutivo · Venta particular · Óptica COALIVI

Cuadro de mando de la venta particular de la Óptica COALIVI (Concepción).
Elaborado por **MDF Consulting** · Ingeniería Civil Industrial UDD · 2026.

**Foco:** solo OT con convenio PARTICULAR. Las licitaciones (SSCC, COSADES, DAS) y los convenios y operativos
con empresas quedan fuera. Las boletas y los costos se filtran según el número de OT.

## Pestañas

| Pestaña | Qué muestra |
|---|---|
| Resumen ejecutivo | KPIs con semáforo de metas, cascada del ingreso al margen, cuadro de metas, venta mensual y hallazgos clave. Botón de reporte en Excel |
| Resultados por línea | Estado de resultados por línea de producto y rentabilidad real del informe de costos (familia, tipo de lente, derivador, descuento, proveedor, productos) |
| Comercial | Boletas, ticket, tendencia, OT y ticket por mes, **derivación desde el Centro Médico**, forma de pago, vendedoras y descuentos |
| Operaciones | Plazos de entrega, entregas fuera de plazo, OT por día de la semana y desempeño por vendedora |
| Calidad de datos | OT mal registradas, auditoría para TI, trazabilidad de la OT y descarga de tablas |

La barra lateral tiene el período, las **metas** (editables) y los **gastos operacionales**, que están en 0 hasta
que COALIVI entregue las cifras. Mientras estén en 0, el dashboard llega hasta el margen directo.

## Archivos

| Archivo | Para qué |
|---|---|
| `app.py` | La aplicación de Streamlit |
| `procesamiento.py` | Limpieza de las planillas originales |
| `generar_datos.py` | Crea la carpeta `data/` desde las planillas originales |
| `data/` | Tablas limpias (`ventas`, `ot_sala`, `costos` en .csv.gz) |
| `logo.png`, `.streamlit/config.toml` | Logo y colores de COALIVI |

## Publicar (GitHub + Streamlit Community Cloud)

1. En GitHub, subir **todo el contenido** de esta carpeta al repositorio (incluidas las carpetas `data` y `.streamlit`).
   Si ya existe el repositorio del dashboard anterior, basta con reemplazar los archivos: la app se actualiza sola
   con el mismo link. Borrar del repositorio los `.csv.gz` antiguos que ya no se usan
   (`convenios`, `inventario`, `ot_convenio`, `pedidos`).
2. En [share.streamlit.io](https://share.streamlit.io): **Create app** → repositorio → rama `main` → archivo `app.py`.

## Dar acceso a Leonardo (u otra persona)

Si el repositorio es privado, la app también lo es. En la app: **Share** (arriba a la derecha) → escribir el correo →
**Invite**. Le llega un correo con el link y entra con su cuenta de Google o con un link de acceso por correo; no
necesita cuenta de GitHub. Streamlit Community Cloud permite una sola app privada por cuenta.

## Actualizar los datos

- **Para todos:** dejar las 3 planillas nuevas en una carpeta y correr
  `python generar_datos.py "ruta/a/la/carpeta"`. Después subir a GitHub la carpeta `data` nueva.
- **Solo para una sesión:** barra lateral → *Cargar / actualizar bases de datos* → subir las planillas.

Planillas que reconoce: `CONSOLIDADO VENTAS ÓPTICA Y OT + BOLETAS`, `OT APPS FINAL - Sala de ventas particular`
e `informe_costos_Sala_ventas`. Las planillas de convenio se saltan.

## Correr en el computador

```
pip install -r requirements.txt
streamlit run app.py
```

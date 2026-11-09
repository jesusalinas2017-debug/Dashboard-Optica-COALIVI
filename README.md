# Dashboard Ejecutivo · Venta particular · Óptica COALIVI

Cuadro de mando de la venta particular de la Óptica COALIVI (Concepción).
Elaborado por **MDF Consulting** · Ingeniería Civil Industrial UDD · 2026.

**Foco:** solo OT con convenio PARTICULAR. Las licitaciones (SSCC, COSADES, DAS) y los convenios y operativos
con empresas quedan fuera. Las boletas y los costos se filtran según el número de OT.

## Pestañas

| Pestaña | Qué muestra |
|---|---|
| Resumen ejecutivo | KPIs con semáforo de metas, cascada del ingreso al margen, cuadro de metas, venta mensual y hallazgos clave. Botón de reporte en Excel |
| Resultados por línea | Estado de resultados por línea de producto (con gastos operacionales reales) y rentabilidad real del informe de costos (familia, tipo de lente, derivador, descuento, proveedor, productos) |
| EERR contable | Estado de resultados contable de **toda la óptica** (incluye licitaciones): comparativo por año y mismo tramo, ingresos por tipo de venta, gastos por categoría, hallazgos y cuadratura con las boletas |
| Comercial | Boletas, ticket, tendencia, OT y ticket por mes, **derivación desde el Centro Médico**, forma de pago y vendedoras |
| Descuentos | Descuento real por código, monto descontado, margen a precio de lista vs cobrado y **simulador** del descuento máximo por línea |
| Operaciones | Plazos de entrega, entregas fuera de plazo, OT por día de la semana y desempeño por vendedora |
| Calidad de datos | OT mal registradas, auditoría para TI, trazabilidad de la OT y descarga de tablas |

La barra lateral tiene el período, las **metas** (editables) y los **gastos operacionales**.

### Cómo se calculan los gastos operacionales

- Vienen de los **estados de resultados contables de la óptica** (`Estado_de_Resultados_Comparativo_..._OPTICA.xlsx`,
  uno por año). Se suman **todas** las subcuentas (la planilla de 2026 omite finiquitos y encomiendas en su total).
- Se excluyen los **insumos** (ya están en el costo directo de cada línea) y, por defecto, los **finiquitos**
  (no recurrentes; se pueden incluir en la barra lateral).
- Los gastos son de toda la óptica, así que se **asignan a la venta particular** según su peso en los ingresos:
  venta particular del dashboard (boletas sin IVA) ÷ ingresos contables de la óptica, en los mismos meses.
- Los meses posteriores al último estado de resultados se **estiman** con el promedio de los últimos 12 meses.
- **Arriendo = $0** (el inmueble es propio). **Luz, agua y gas** no aparecen en el estado de resultados: se pagan en
  conjunto para todo el inmueble (un solo medidor). Si se acuerda un monto para la óptica, se ingresa en la barra lateral.
- Ojo: la cuenta contable 5301-01 "Ventas lentes ópticos (particulares)" cuadra con **todas** las boletas de la sala,
  no solo con las OT particulares. En el dashboard se llama "Venta sala (cta. particulares)".

Si no hay estados de resultados cargados, la barra lateral vuelve a pedir los gastos a mano.

## Archivos

| Archivo | Para qué |
|---|---|
| `app.py` | La aplicación de Streamlit |
| `procesamiento.py` | Limpieza de las planillas originales |
| `generar_datos.py` | Crea la carpeta `data/` desde las planillas originales |
| `data/` | Tablas limpias (`ventas`, `ot_sala`, `costos`, `eerr` en .csv.gz) |
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

Planillas que reconoce: `CONSOLIDADO VENTAS ÓPTICA Y OT + BOLETAS`, `OT APPS FINAL - Sala de ventas particular`,
`informe_costos_Sala_ventas` y `Estado_de_Resultados_Comparativo_..._OPTICA` (se pueden subir varios años juntos;
si un mes viene en dos archivos, queda el último). Las planillas de convenio se saltan.

## Correr en el computador

```
pip install -r requirements.txt
streamlit run app.py
```

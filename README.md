# Dashboard Ejecutivo · Óptica COALIVI

Cuadro de mando para la Dirección Ejecutiva de la Óptica COALIVI (Concepción).
Elaborado por **MDF Consulting** · Ingeniería Civil Industrial UDD · 2026.

## Pestañas

| Pestaña | Qué muestra |
|---|---|
| Resumen ejecutivo | KPIs con semáforo de metas, cascada del ingreso al margen operacional, cuadro de metas, venta mensual y hallazgos clave. Botón de reporte en Excel |
| Resultados por línea | Estado de resultados por línea de producto: ingresos netos, costo directo, margen directo, gastos operacionales y margen operacional |
| Comercial | Tendencia de venta, segmentos, ticket, formas de pago, vendedoras, convenios, derivación y canal institucional |
| Operaciones | Plazos de entrega, atrasos, pedidos de cristales y mix de proveedores |
| Calidad de datos | Registro de OT, auditoría para TI, trazabilidad entre sistemas y descarga de tablas |

Los gastos operacionales y las metas se editan en la barra lateral. Los gastos que vienen por defecto
son **supuestos** de MDF Consulting y deben reemplazarse por las cifras reales de COALIVI.

## Estructura

```
app.py               # la aplicación Streamlit
logo.png             # logo de Óptica COALIVI
procesamiento.py     # limpieza de las planillas originales
data/*.csv.gz        # tablas limpias que lee el dashboard
.streamlit/config.toml
requirements.txt
```

## Actualizar los datos

- **Solo para una sesión:** barra lateral → *Cargar / actualizar bases de datos* → subir las planillas `.xlsx` originales.
- **Para todos:** volver a correr el notebook `Dashboard_COALIVI_Colab_GitHub_Streamlit.ipynb` en Colab; regenera `data/` y la sube a este repositorio. Streamlit se actualiza solo.

## Correr en local

```
pip install -r requirements.txt
streamlit run app.py
```

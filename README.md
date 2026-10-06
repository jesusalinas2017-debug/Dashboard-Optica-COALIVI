# Dashboard Ejecutivo · Óptica COALIVI

Cuadro de mando para la Dirección Ejecutiva de la Óptica COALIVI (Concepción).
Elaborado por **MDF Consulting** · Ingeniería Civil Industrial UDD · 2026.

## Pestañas

| Pestaña | Qué muestra |
|---|---|
| Resumen ejecutivo | KPIs principales, venta mensual vs año anterior, mix de producto, segmentos y hallazgos clave |
| Ventas | Tendencia histórica, venta por tipo, forma de pago, vendedora y día de la semana |
| Clientes y canales | Segmentos, convenios, profesionales que derivan, edad y canal convenio institucional |
| Operaciones | Plazos de entrega, atrasos, pedidos de cristales y mix de proveedores |
| Rentabilidad | Margen por familia y producto (informe de costos) y margen de lista del inventario |
| Convenios | Cartera de convenios por categoría, antigüedad y estado |
| Calidad de datos | Registro de OT, trazabilidad entre sistemas y auditoría para TI |
| Datos | Bases cargadas, cómo actualizarlas y descarga de tablas limpias |

## Estructura

```
app.py               # la aplicación Streamlit
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

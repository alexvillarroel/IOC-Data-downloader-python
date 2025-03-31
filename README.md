# IOC-Data-Downloader-Python

Este script permite descargar y procesar datos del nivel del mar desde la web del IOC, con opciones para eliminar la señal de marea y extraer datos asociados a eventos sísmicos.  

# 🇪🇸 

## Requerimientos / Request

Para ejecutar este script, asegúrate de tener instaladas las siguientes bibliotecas de Python:

### Lista de dependencias

| Biblioteca       | Descripción |
|-----------------|------------|
| `requests`      | Para realizar solicitudes HTTP y descargar datos. |
| `pandas`        | Para manipulación y análisis de datos. |
| `numpy`         | Para cálculos numéricos y manejo de datos. |
| `matplotlib`    | Para la visualización de datos. |
| `scipy`         | Para el procesamiento de señales. |
| `beautifulsoup4` | Para el análisis de HTML y scraping. |




Este script permite descargar datos del monitoreo del nivel del mar desde la página web del IOC.

## Descripción

El script `ioc_getdata.py` realiza lo siguiente:

1. **Solicitud de datos**  
   - Se conecta a la web del IOC y extrae los datos solicitados.

2. **Parámetros de entrada**  
   - Código(s) de las estaciones de las cuales se desea extraer datos.  
   - Fecha de inicio de los datos (en UTC).  
   - Número de días de datos a extraer.  

3. **Extracción de datos para eventos sísmicos** *(opcional)*  
   - Permite ingresar la fecha y hora UTC del evento.  
   - Se pueden definir los minutos posteriores al evento para extraer datos específicos del tsunami.  

4. **Eliminación de la señal de marea** *(opcional)*  
   - Se ofrece la opción de remover la señal de marea.  
   - Esto permite obtener únicamente la señal del tsunami.  
   - La eliminación se realiza restando la señal de marea de la señal original.
5. **Visualización de la señal**
   - Visualización de la señal procesada mediante matplotlib.
# 🇺🇸

# IOC-Data-Downloader-Python

This script allows downloading sea level monitoring data from the IOC website.

## Description

The `get_data.py` script performs the following tasks:

1. **Data Request**  
   - Connects to the IOC website and retrieves the requested data.

2. **Input Parameters**  
   - Code(s) of the stations from which data is to be extracted.  
   - Start date of the data (in UTC).  
   - Number of days of data to extract.  

3. **Earthquake Event Data Extraction** *(optional)*  
   - Allows entering the event's UTC date and time.  
   - Users can define the minutes after the event to extract specific tsunami data.  

4. **Tide Signal Removal** *(optional)*  
   - Offers the option to remove the tidal signal.  
   - This allows obtaining only the tsunami signal.  
   - The removal is performed by subtracting the tidal signal from the original data.  

5. **Signal Visualization**  
   - Displays the processed signal using Matplotlib.  

## Run

Just in the same folder, run `python ioc_getdata.py` , the data will be saved in the same directory

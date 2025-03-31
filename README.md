# IOC-Data-Downloader-Python

Este script permite descargar datos del monitoreo del nivel del mar desde la página web del IOC.

## Descripción

El script `get_data.py` realiza lo siguiente:

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

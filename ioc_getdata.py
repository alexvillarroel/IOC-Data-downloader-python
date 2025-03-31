import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def remove_tide(time, data, order=3):
    time_seconds = (time - time.iloc[0]).dt.total_seconds()

    def butter_lowpass(cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return b, a

    def lowpass_filter(data, cutoff, fs, order=5):
        b, a = butter_lowpass(cutoff, fs, order=order)
        y = filtfilt(b, a, data)
        return y

    cutoff = 1 / (3600*6)  # 6 hours
    fs = 1 / (time_seconds[1] - time_seconds[0])
    order = 5

    tide_data = lowpass_filter(data, cutoff, fs, order)
    tsunami_data = data - tide_data
    return tsunami_data, tide_data

def obtener_datos(station_code, start_date, period_days):
    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = start_datetime + timedelta(days=period_days)
    end_date = end_datetime.strftime("%Y-%m-%d")

    url = f"https://ioc-sealevelmonitoring.org/bgraph.php?code={station_code}&output=tab&period={period_days}&endtime={end_date}"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        table_rows = soup.find_all("tr")

        data = []
        for row in table_rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2:  # Asegurarse de que haya al menos dos columnas
                time = cols[0].text.strip()
                value = float(cols[1].text.strip()) if cols[1].text.strip() else np.nan  # Manejar valores vacíos
                # Si deseas agregar la columna rad(m), puedes hacerlo de esta forma
                rad_value = float(cols[2].text.strip()) if len(cols) > 2 and cols[2].text.strip() else np.nan
                if value !=np.nan:
                    data.append([time, value, rad_value])  # Agregar rad(m) a los datos

        if data:
            data = [row for row in data if not np.isnan(row[1])]
            df = pd.DataFrame(data, columns=["Time (UTC)", "prs(m)", "rad(m)"])
            df["Time (UTC)"] = pd.to_datetime(df["Time (UTC)"], format="%Y-%m-%d %H:%M:%S")
            return df
        else:
            print(f"No se encontraron datos para la estación {station_code}.")
            return None
    else:
        print(f"Error al descargar los datos para la estación {station_code}: {response.status_code}")
        return None

def procesar_datos(df, filtrar, cortar, sismo_datetime=None, tiempo_guardar=None):
    if filtrar == "s":
        df["prs(m)"] = df["prs(m)"] - df["prs(m)"].mean()  # Centrar la señal
        df["prs_original"] = df["prs(m)"]  # Guardar copia antes de modificar
        df["prs(m)"], tide_data = remove_tide(df["Time (UTC)"], df["prs(m)"])

    if cortar == "s" and sismo_datetime is not None and tiempo_guardar is not None:
        df["Diff"] = abs(df["Time (UTC)"] - sismo_datetime)
        closest_time = df.loc[df["Diff"].idxmin(), "Time (UTC)"]
        end_sismo_time = closest_time + timedelta(minutes=tiempo_guardar)
        df = df[(df["Time (UTC)"] >= closest_time) & (df["Time (UTC)"] <= end_sismo_time)].copy()
        df.drop(columns=["Diff"], inplace=True)

    return df

def guardar_datos(df, station_code, sismo_datetime):
    minutos = (df["Time (UTC)"] - df["Time (UTC)"].iloc[0]).dt.total_seconds() / 60
    filename_txt = f"{station_code}_{sismo_datetime.strftime('%Y-%m-%d')}.txt"
    np.savetxt(filename_txt, np.column_stack((minutos, df["prs(m)"])), fmt="%.6f", header="Minutos\tNivel del Mar (m)")
    print(f"Datos guardados en '{filename_txt}'")

def visualizar_datos(df, filtrar):
    minutos = (df["Time (UTC)"] - df["Time (UTC)"].iloc[0]).dt.total_seconds() / 60
    plt.figure(figsize=(10, 5))
    plt.plot(minutos, df["prs_original"], label="Nivel del mar (original)", color="b", alpha=0.7)
    if filtrar == "s":
        plt.plot(minutos, df["prs(m)"], label="Nivel del mar (filtrado)", color="r", linestyle="--")
    plt.xlabel("Tiempo (minutos)")
    plt.ylabel("Altura (m)")
    plt.title("Variación del Nivel del Mar")
    plt.legend()
    plt.grid()
    plt.show()

# Ingresar múltiples códigos de estación
ioc_info = pd.read_csv("ioc_stations.txt", sep="\s+", engine="python", header=0)
ioc_info.columns = ["Code", "Country", "Location"]

# Mostrar los códigos de las estaciones disponibles
show_stations = input("¿Desea ver los códigos de las estaciones disponibles? (s/n): ").strip().lower()
if show_stations == "s":
    country = input("Ingrese el país (en inglés, ex. USA): ").strip()
    filtered_data = ioc_info[ioc_info["Country"].str.contains(country, case=False, na=False)]
    print(filtered_data[["Code", "Location"]].to_string(index=False))

station_codes = input("Ingrese los códigos de las estaciones separados por coma (ej: ancu,quintero): ").split(",")
start_date = input("Ingrese la fecha de inicio (YYYY-MM-DD): ").strip()
period_days = int(input("Ingrese el período en días: ").strip())

# Preguntar si desea filtrar y cortar los datos para todas las estaciones
filtrar = input("¿Desea filtrar la marea y la tendencia para todas las estaciones? (s/n): ").strip().lower()
cortar = input("¿Desea cortar los datos a partir de un terremoto para todas las estaciones? (s/n): ").strip().lower()

sismo_datetime = None
if cortar == "s":
    sismo_date = input("Ingrese la fecha del terremoto (YYYY-MM-DD): ").strip()
    sismo_time = input("Ingrese la hora del terremoto en UTC (HH:MM:SS): ").strip()
    sismo_datetime = datetime.strptime(f"{sismo_date} {sismo_time}", "%Y-%m-%d %H:%M:%S")
    tiempo_guardar = int(input("Ingrese el tiempo en minutos a guardar después del evento: "))

# Procesar cada estación
for station_code in station_codes:
    station_code = station_code.strip()
    df = obtener_datos(station_code, start_date, period_days)
    if df is not None:
        df = procesar_datos(df, filtrar, cortar, sismo_datetime, tiempo_guardar)

        # Visualizar los datos
        visualizar = input(f"¿Desea visualizar los datos de la estación {station_code}? (s/n): ").strip().lower()
        if visualizar == "s":
            visualizar_datos(df, filtrar)

        # Guardar los datos en archivo .txt
        guardar_datos(df, station_code, sismo_datetime)

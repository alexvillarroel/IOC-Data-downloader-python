import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def remove_tide(time, data, order=3):
    """
    Elimina la señal de marea utilizando un filtro pasa-bajos.
    Removes the tidal signal using a low-pass filter.
    """
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

    cutoff = 1 / (3600*6)  # 6 horas / 6 hours
    fs = 1 / (time_seconds[1] - time_seconds[0])
    
    tide_data = lowpass_filter(data, cutoff, fs, order)
    tsunami_data = data - tide_data
    return tsunami_data, tide_data

def obtener_datos(station_code, start_date, period_days):
    """
    Descarga datos de nivel del mar desde la web del IOC.
    Downloads sea level data from the IOC website.
    """
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
            if len(cols) >= 2:
                time = cols[0].text.strip()
                value = float(cols[1].text.strip()) if cols[1].text.strip() else np.nan
                rad_value = float(cols[2].text.strip()) if len(cols) > 2 and cols[2].text.strip() else np.nan
                if value != np.nan:
                    data.append([time, value, rad_value])

        if data:
            data = [row for row in data if not np.isnan(row[1])]
            df = pd.DataFrame(data, columns=["Time (UTC)", "prs(m)", "rad(m)"])
            df["Time (UTC)"] = pd.to_datetime(df["Time (UTC)"], format="%Y-%m-%d %H:%M:%S")
            return df
        else:
            print(f"No se encontraron datos para la estación {station_code}. / No data found for station {station_code}.")
            return None
    else:
        print(f"Error al descargar los datos para la estación {station_code}: {response.status_code} / Error downloading data for station {station_code}: {response.status_code}")
        return None

def procesar_datos(df, filtrar, cortar, sismo_datetime=None, tiempo_guardar=None):
    """
    Procesa los datos eliminando la marea y cortando los datos alrededor de un sismo.
    Processes the data by removing the tide and trimming the data around an earthquake event.
    """
    if filtrar == "s":
        df["prs(m)"] = df["prs(m)"] - df["prs(m)"].mean()
        df["prs_original"] = df["prs(m)"]
        df["prs(m)"], tide_data = remove_tide(df["Time (UTC)"], df["prs(m)"])

    if cortar == "s" and sismo_datetime is not None and tiempo_guardar is not None:
        df["Diff"] = abs(df["Time (UTC)"] - sismo_datetime)
        closest_time = df.loc[df["Diff"].idxmin(), "Time (UTC)"]
        end_sismo_time = closest_time + timedelta(minutes=tiempo_guardar)
        df = df[(df["Time (UTC)"] >= closest_time) & (df["Time (UTC)"] <= end_sismo_time)].copy()
        df.drop(columns=["Diff"], inplace=True)

    return df

def guardar_datos(df, station_code, sismo_datetime):
    """
    Guarda los datos en un archivo de texto.
    Saves the data to a text file.
    """
    minutos = (df["Time (UTC)"] - df["Time (UTC)"].iloc[0]).dt.total_seconds() / 60
    filename_txt = f"{station_code}_{sismo_datetime.strftime('%Y-%m-%d')}.txt"
    np.savetxt(filename_txt, np.column_stack((minutos, df["prs(m)"])), fmt="%.6f", header="Minutes\tSea Level (m)")
    print(f"Datos guardados en '{filename_txt}' / Data saved in '{filename_txt}'")

def visualizar_datos(df, filtrar):
    """
    Visualiza los datos de nivel del mar.
    Plots the sea level data.
    """
    minutos = (df["Time (UTC)"] - df["Time (UTC)"].iloc[0]).dt.total_seconds() / 60
    plt.figure(figsize=(10, 5))
    plt.plot(minutos, df["prs_original"], label="Nivel del mar (original) / Sea Level (original)", color="b", alpha=0.7)
    if filtrar == "s":
        plt.plot(minutos, df["prs(m)"], label="Nivel del mar (filtrado) / Sea Level (filtered)", color="r", linestyle="--")
    plt.xlabel("Tiempo (minutos) / Time (minutes)")
    plt.ylabel("Altura (m) / Height (m)")
    plt.title("Variación del Nivel del Mar / Sea Level Variation")
    plt.legend()
    plt.grid()
    plt.show()

# Leer estaciones desde archivo / Read stations from file
ioc_info = pd.read_csv("ioc_stations.txt", sep="\s+", engine="python", header=0)
ioc_info.columns = ["Code", "Country", "Location"]

# Mostrar estaciones disponibles / Show available stations
show_stations = input("¿Desea ver los códigos de las estaciones disponibles? (s/n) / Do you want to see available station codes? (y/n): ").strip().lower()
if show_stations == "s":
    country = input("Ingrese el país (en inglés, ex. USA) / Enter the country (in English, e.g., USA): ").strip()
    filtered_data = ioc_info[ioc_info["Country"].str.contains(country, case=False, na=False)]
    print(filtered_data[["Code", "Location"]].to_string(index=False))

# Solicitar parámetros de entrada / Request input parameters
station_codes = input("Ingrese los códigos de las estaciones separados por coma (ej: ancu,quintero) / Enter station codes separated by commas (e.g., ancu,quintero): ").split(",")
start_date = input("Ingrese la fecha de inicio (YYYY-MM-DD) / Enter start date (YYYY-MM-DD): ").strip()
period_days = int(input("Ingrese el período en días / Enter the period in days: ").strip())

# Preguntar opciones de filtrado y corte / Ask about filtering and trimming options
filtrar = input("¿Desea filtrar la marea y la tendencia? (s/n) / Do you want to filter the tide and trend? (y/n): ").strip().lower()
cortar = input("¿Desea cortar los datos por un terremoto? (s/n) / Do you want to trim the data based on an earthquake? (y/n): ").strip().lower()

sismo_datetime = None
if cortar == "s":
    sismo_date = input("Ingrese la fecha del terremoto (YYYY-MM-DD) / Enter earthquake date (YYYY-MM-DD): ").strip()
    sismo_time = input("Ingrese la hora del terremoto en UTC (HH:MM:SS) / Enter earthquake time in UTC (HH:MM:SS): ").strip()
    sismo_datetime = datetime.strptime(f"{sismo_date} {sismo_time}", "%Y-%m-%d %H:%M:%S")
    tiempo_guardar = int(input("Ingrese el tiempo en minutos a guardar / Enter time in minutes to save: "))

for station_code in station_codes:
    station_code = station_code.strip()
    df = obtener_datos(station_code, start_date, period_days)
    if df is not None:
        df = procesar_datos(df, filtrar, cortar, sismo_datetime, tiempo_guardar)
        visualizar_datos(df, filtrar)
        guardar_datos(df, station_code, sismo_datetime)

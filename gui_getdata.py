import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QDateEdit, QSpinBox, 
    QCheckBox, QLineEdit, QPushButton, QVBoxLayout, QWidget, QTextEdit, QFileDialog
)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ioc_getdata import obtener_datos, procesar_datos

class SeaLevelApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IOC Data Downloader")
        self.setGeometry(100, 100, 500, 600)

        # Layout principal
        layout = QVBoxLayout()
        # Selección de estación (Múltiples estaciones)
        self.label_station = QLabel("Ingresa los códigos de las estaciones (separados por coma):")
        layout.addWidget(self.label_station)
        self.input_station = QLineEdit()
        layout.addWidget(self.input_station)

        # Botón para ver estaciones disponibles
        self.btn_ver_estaciones = QPushButton("Ver estaciones por país")
        self.btn_ver_estaciones.clicked.connect(self.ver_estaciones_por_pais)
        layout.addWidget(self.btn_ver_estaciones)

        # Selección de fecha
        self.label_date = QLabel("Fecha de inicio:")
        layout.addWidget(self.label_date)
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        layout.addWidget(self.date_picker)

        # Selección de días
        self.label_days = QLabel("Período en días:")
        layout.addWidget(self.label_days)
        self.spin_days = QSpinBox()
        self.spin_days.setRange(1, 365)
        layout.addWidget(self.spin_days)

        # Opción de filtrar marea
        self.check_filter = QCheckBox("Filtrar marea")
        layout.addWidget(self.check_filter)

        # Opción de evento sísmico
        self.check_sismo = QCheckBox("¿Agregar evento sísmico?")
        self.check_sismo.toggled.connect(self.toggle_sismo_fields)
        layout.addWidget(self.check_sismo)

        # Campos de entrada de fecha y hora del terremoto (ocultos inicialmente)
        self.label_sismo_date = QLabel("Fecha del terremoto (YYYY-MM-DD):")
        self.label_sismo_date.setVisible(False)
        layout.addWidget(self.label_sismo_date)
        self.input_sismo_date = QLineEdit()
        self.input_sismo_date.setVisible(False)
        layout.addWidget(self.input_sismo_date)

        self.label_sismo_time = QLabel("Hora del terremoto (HH:MM:SS):")
        self.label_sismo_time.setVisible(False)
        layout.addWidget(self.label_sismo_time)
        self.input_sismo_time = QLineEdit()
        self.input_sismo_time.setVisible(False)
        layout.addWidget(self.input_sismo_time)

        self.label_sismo_minutes = QLabel("Minutos a registrar después del sismo:")
        self.label_sismo_minutes.setVisible(False)
        layout.addWidget(self.label_sismo_minutes)
        self.input_sismo_minutes = QSpinBox()
        self.input_sismo_minutes.setRange(1, 1440)  # 1 día en minutos
        self.input_sismo_minutes.setVisible(False)
        layout.addWidget(self.input_sismo_minutes)

        # Botón para visualizar los datos
        self.btn_visualizar = QPushButton("Visualizar Datos")
        self.btn_visualizar.clicked.connect(self.visualizar_datos)
        layout.addWidget(self.btn_visualizar)

        # Botón para guardar los datos
        self.btn_guardar = QPushButton("Guardar Datos")
        self.btn_guardar.clicked.connect(self.guardar_datos)
        layout.addWidget(self.btn_guardar)

        # Widget central
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def toggle_sismo_fields(self):
        """Habilita o deshabilita los campos de fecha, hora y minutos de sismo."""
        enabled = self.check_sismo.isChecked()
        self.label_sismo_date.setVisible(enabled)
        self.input_sismo_date.setVisible(enabled)
        self.label_sismo_time.setVisible(enabled)
        self.input_sismo_time.setVisible(enabled)
        self.label_sismo_minutes.setVisible(enabled)
        self.input_sismo_minutes.setVisible(enabled)

    def ver_estaciones_por_pais(self):
        """Muestra una ventana emergente con estaciones ordenadas por país y alfabéticamente."""
        try:
            ioc_info = pd.read_csv(r"ioc_stations.txt", sep=r"\s+", engine="python", header=0)
            ioc_info.columns = ["Code", "Country", "Location"]
            ioc_info = ioc_info.sort_values(["Country", "Code"])

            estaciones_texto = ""
            for country, group in ioc_info.groupby("Country"):
                estaciones_texto += f"{country}:\n"
                estaciones_texto += ", ".join(group["Code"].tolist()) + "\n\n"

            self.estaciones_window = QWidget()
            self.estaciones_window.setWindowTitle("Estaciones por país")
            self.estaciones_window.setGeometry(150, 150, 400, 400)

            layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setPlainText(estaciones_texto)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)

            self.estaciones_window.setLayout(layout)
            self.estaciones_window.show()
        except Exception as e:
            print(f"Error cargando estaciones: {e}")

    def visualizar_datos(self):
        station_codes = self.input_station.text().strip().split(",")
        station_codes = [code.strip() for code in station_codes if code.strip()]
        start_date = self.date_picker.date().toString("yyyy-MM-dd")
        period_days = self.spin_days.value()
        filtrar = "s" if self.check_filter.isChecked() else "n"

        cortar = "s" if self.check_sismo.isChecked() else "n"
        sismo_datetime = None
        tiempo_guardar = None
        if cortar == "s":
            try:
                sismo_datetime = datetime.strptime(
                    f"{self.input_sismo_date.text()} {self.input_sismo_time.text()}", "%Y-%m-%d %H:%M:%S"
                )
                tiempo_guardar = self.input_sismo_minutes.value()
            except ValueError:
                print("Error: La fecha y hora del sismo deben ser correctas.")
                return

        dfs = []
        for station_code in station_codes:
            df = obtener_datos(station_code, start_date, period_days)
            if df is not None and not df.empty:
                df = procesar_datos(df, filtrar, cortar, sismo_datetime, tiempo_guardar)
                dfs.append((station_code, df))

        if not dfs:
            print("No hay datos para graficar.")
            return

        fig, axes = plt.subplots(len(dfs), 1, sharex=True)
        if len(dfs) == 1:
            axes = [axes]

        for ax, (station_code, df) in zip(axes, dfs):
            minutos = (df["Time (UTC)"] - df["Time (UTC)"].iloc[0]).dt.total_seconds() / 60
            ax.plot(minutos, df["prs_original"], label="Nivel del mar (original)", color="b", alpha=0.7)
            if filtrar == "s":
                ax.plot(minutos, df["prs(m)"], label="Nivel del mar (filtrado)", color="r", linestyle="--")
            ax.set_ylabel("Altura (m)")
            ax.set_title(f"Estación: {station_code}")
            ax.legend()
            ax.grid()

        axes[-1].set_xlabel("Tiempo (minutos)")
        plt.tight_layout()
        plt.show()
    def guardar_datos(self):
        """Guarda los datos en un directorio seleccionado por el usuario."""
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para guardar")
        if not folder:
            print("No se seleccionó una carpeta.")
            return

        station_codes = self.input_station.text().strip().split(",")
        station_codes = [code.strip() for code in station_codes if code.strip()]
        start_date = self.date_picker.date().toString("yyyy-MM-dd")
        period_days = self.spin_days.value()
        filtrar = "s" if self.check_filter.isChecked() else "n"

        # Verificar si se quiere recortar por evento sísmico
        cortar = "s" if self.check_sismo.isChecked() else "n"
        sismo_datetime = None
        tiempo_guardar = None
        if cortar == "s":
            try:
                sismo_datetime = datetime.strptime(
                    f"{self.input_sismo_date.text()} {self.input_sismo_time.text()}", "%Y-%m-%d %H:%M:%S"
                )
                tiempo_guardar = self.input_sismo_minutes.value()
            except ValueError:
                print("Error: La fecha y hora del sismo deben ser correctas.")
                return

        for station_code in station_codes:
            df = obtener_datos(station_code, start_date, period_days)
            if df is not None and not df.empty:
                df = procesar_datos(df, filtrar, cortar, sismo_datetime, tiempo_guardar)
                minutos = (df["Time (UTC)"] - df["Time (UTC)"].iloc[0]).dt.total_seconds() / 60

                # Definir el nombre del archivo
                if cortar == "s":
                    filename = os.path.join(folder, f"{station_code}_{sismo_datetime.strftime('%Y-%m-%d_%H-%M-%S')}.txt")
                else:
                    filename = os.path.join(folder, f"{station_code}_{start_date}.txt")

                np.savetxt(filename, np.column_stack((minutos, df["prs(m)"])), fmt="%.6f", header="Minutos\tNivel del Mar (m)")
                print(f"Datos guardados en {filename}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeaLevelApp()
    window.show()
    sys.exit(app.exec())

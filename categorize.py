import pandas as pd
import os
import re
from datetime import datetime
from pathlib import Path

def read_file(filepath, startrow = 1200, rowcount = 1500):
    '''
    :param filepath:
    Pfad zur Datei die eingelesen wird
    :param startrow:
    Erste Reihe der CSV die betrachtet wird
    :param rowcount:
    Anzahl der Reihen die ab startrow betrachtet wird.
    --> startrow + rowcount = letzte reihe die betrachtet wird
    :return:
    Gibt ein DataFrame mit 2 Spalten zurück:
    part: Bezeichnung des Teils
    kN: Maximaler Wert für kN im betrachteten Bereich
    '''
    # Einlesen der Datei. Die ersten "startrow" Zeilen werden übersprungen,
    # danach rowcount Zeilen eingelesen.
    df = pd.read_csv(
        filepath, delimiter = ";", skiprows = startrow, nrows = rowcount,
        engine = "python", names = ["Time", "X1", "kN", "X2"]
    )
    # Teilebezeichnung wird im Pfad gesucht
    df["part"] = re.search(r"EBE\d{6}", filepath).group()
    df.dropna(inplace=True)
    df["kN"] = df["kN"].str.replace(",", ".")
    df = df.astype({"kN" : "float"})
    # Zeile mit größtem kN-Wert wird gefunden
    max = df.loc[[df["kN"].idxmax()]][["part", "kN"]]
    # Teil wird kategorisiert
    max = categorizeKN(max)
    return max

def categorizeKN(df):
    '''
    :param df:
    DataFrame das Teilebezeichnung und einen Wert für kN enthält.
    :return:
    Fügt Spalte category hinzu, die dem Teil eine Kategorie je nach Größe
    des kN-Wertes zuweist.
    '''
    kn = float(df["kN"])
    if kn > 0.45:
        df["category"] = 3
    elif kn > 0.3:
        df["category"] = 2
    elif kn > 0.1:
        df["category"] = 1
    else:
        df["category"] = 0
    return(df)

def get_directory():
    '''
    :return:
    User Input für den Pfad für die Eingabedateien un den Pfad für die Ausgabe
    wird abgefragt. Falls kein Input getätigt wird, wird für die Eingabe-
    dateien im Pfad des Codes nach dem Ordner data, und für die Ausgabedatei
    nach dem Ordner output gesucht.
    '''
    input_dir = input("Pfad zum Orner der CSV-Dateien:\n")
    if "\\" in input_dir:
        input_dir += "\\"
    if "/" in input_dir:
        input_dir += "/"
    if input_dir == "":
        input_dir = "data/"
    output_dir = input("Pfad zum Ausgabeordner:\n")
    if "\\" in output_dir:
        output_dir += "\\"
    if "/" in output_dir:
        output_dir += "/"
    if output_dir == "":
        output_dir = "output/"
    return input_dir, output_dir

# Pfade für Ein- und Ausgabe werden abgefragt.
directory_in_str, directory_out_str = (get_directory())
directory = os.fsencode(Path(directory_in_str))

files = []

# Liste mit dem Pfad jeder Datei wird erstellt.
for file in os.listdir(directory):
     filename = os.fsdecode(file)
     files.append(filename)

data = pd.DataFrame()
i = 1

# Für jede Datei im Eingabepfad wird die Funktion read_file durchgeführt.
for filename in files:
    print(str(i) + " / " + str(len(files)) + " files done")
    i += 1
    try:
        if data.empty:
            data = read_file(str(directory_in_str + filename))
        else:
            data = data.append(read_file(str(directory_in_str + filename)))
    except:
        pass

# Ausgabedatei wird erstellt.
data.reset_index(drop = True).to_excel(
    Path(directory_out_str + str(datetime.now().strftime("%y%m%d_%H%M")) +
         "_categorized_parts" + ".xlsx"), index = False
)

print("\nFertig")


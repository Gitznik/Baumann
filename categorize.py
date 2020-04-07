import pandas as pd
import os
import re
from datetime import datetime
from pathlib import Path
import configparser


def read_file(filepath, config, startrow=1200, rowcount=1500):
    '''
    :param filepath:
    Pfad zur Datei die eingelesen wird
    :param config:
    Eingelesene Konfigurationsdatei
    :param startrow:
    Reihe in der CSV ab der ausgewertet wird
    :param rowcount:
    Anzahl der Reihen die ab startrow betrachtet werden
    --> startrow + rowcount = letzte Reihe die betrachtet wird
    :return:
    Gibt ein DataFrame mit 3 Spalten zurück:
    part: Bezeichnung des Teils
    kN: Maximaler Wert für kN im betrachteten Bereich
    category: Zugewiesene Kategorie aus der config.ini
    '''
    # Einlesen der Datei. Die ersten "startrow" Zeilen werden übersprungen,
    # danach rowcount Zeilen eingelesen.
    df = pd.read_csv(
        filepath, delimiter=";", skiprows=startrow, nrows=rowcount,
        engine="python", names=["Time", "X1", "kN", "X2"]
    )
    # Teilebezeichnung wird im Pfad gesucht
    df["part"] = re.search(r"EBE\d{6}", str(filepath)).group()
    df.dropna(inplace=True)
    df["kN"] = df["kN"].str.replace(",", ".")
    df = df.astype({"kN": "float"})
    # Zeile mit größtem kN-Wert wird gefunden
    max = df.loc[[df["kN"].idxmax()]][["part", "kN"]]
    # Teil wird kategorisiert
    max = categorizeKN(max, config)
    return max


def read_config():
    '''
    :return:
    Ließt die config.ini file ein und gibt sie zurück.
    '''
    config = configparser.ConfigParser()
    config.read("config.ini")
    print("\nKonfigurationsdatei geladen.\n")
    return config


def categorizeKN(df, config):
    '''
    :param df:
    DataFrame das Teilebezeichnung und einen Wert für kN enthält.
    Der kN-Wert wird in der Funktion read_file gefunden und ist der maximale
    kN-Wert der entsprechenden Datei.
    :param config:
    Eingelesene Konfigurationsdatei
    :return:
    Fügt Spalte category hinzu, die dem Teil eine Kategorie je nach Größe
    des kN-Wertes zuweist.
    '''
    kn = float(df["kN"])
    # Geht die verschiedenen Kategorien durch und weißt die richtige zu.
    df["category"] = "Keine Kategorie aus config.ini zutreffend!"
    for key in config["CATEGORIES"]:
        limits = config["CATEGORIES"][key].split("-")
        if (kn > float(limits[0])) & (kn < float(limits[1])):
            df["category"] = key
            break
        else:
            continue
    return (df)


def get_directory(config):
    '''
    :param config:
    Eingelesene Konfigurationsdatei
    :return:
    Korrekt formatierter Pfad zu den Eingabedateien und der Ausgabedatei.
    '''
    # Ordner zu den Eingabedateien
    input_dir = config["PATHS"]["Input"]
    if ("\\" in input_dir) & (input_dir[-1] != "\\"):
        input_dir += "\\"
    if ("/" in input_dir) & (input_dir[-1] != "/"):
        input_dir += "/"
    else:
        input_dir += "/"
    # Ordner zu den Ausgabedateien
    output_dir = config["PATHS"]["Output"]
    if ("\\" in output_dir) & (output_dir[-1] != "\\"):
        output_dir += "\\"
    if ("/" in output_dir) & (output_dir[-1] != "/"):
        output_dir += "/"
    else:
        output_dir += "/"

    print("Input-directory: " + str(input_dir))
    print("Output-directory: " + str(output_dir) + "\n")
    return input_dir, output_dir


def check_directory(directory_in_path, directory_out_path):
    '''
    :param directory_in_path:
    Path-Variable zum Ordner mit den Eingabedateien.
    :param directory_out_path:
    Path-Variable zum Ordner mit den Ausgabedateien.
    :return:
    Falls kein Fehler gefunden wird, wird die Funktion beendet.
    '''
    # Prüfung des Ordners mit den Eingabedateien. Erzeugt Fehlermeldung wenn
    # er nicht existiert.
    if directory_in_path.exists() == False:
        raise OSError("In der config.ini definierter Pfad zu den Eingabedateien"
                      "existiert nicht!")

    # Prüfung des Ordners mit den Ausgabedateien. Fragt an ob er erzeugt werden
    # soll, wenn er nicht existiert. Ansonsten wird das Skript abgebrochen.
    if directory_out_path.exists() == False:
        create_path = input("In der config.ini definierter Ausgabeordner "
                            "existiert nicht. Soll er erstellt werden? (J/N)\n")

        while create_path.upper() not in ["J", "N"]:
            create_path = input(
                "Eingabe war nicht J oder N. Bitte erneut eingeben.\n"
            )

        if create_path.upper() == "J":
            directory_out_path.mkdir(parents=True)
            print("Angegebener Ausgabeordner wurde erstellt.\n")
        else:
            exit("Ordner wurde nicht erstellt und Skript abgebrochen. Bitte den "
                 "Pfad zum Ausgabeordner in config.ini anpassen.")
    pass


# Konfigurationsdatei wird geladen
config = read_config()

# Pfade für Ein- und Ausgabe werden aus der Konfigurationsdatei ausgelesen.
directory_in_str, directory_out_str = (get_directory(config))
directory_in_path = Path(directory_in_str)
directory_out_path = Path(directory_out_str)

# Prüfung der ausgelesenen Pfade
check_directory(directory_in_path, directory_out_path)

directory = os.fsencode(directory_in_path)

files = []

# Liste mit dem Pfad jeder Datei wird erstellt.
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    files.append(filename)

data = pd.DataFrame()
i = 0

# Für jede Datei im Eingabepfad wird die Funktion read_file durchgeführt.
errors = []
for filename in files:
    i += 1
    try:
        if data.empty:
            data = read_file(Path(directory_in_str + filename), config)
            print(str(i) + " / " + str(len(files)) + " files done")
        else:
            data = data.append(read_file(Path(
                directory_in_str + filename), config))
            print(str(i) + " / " + str(len(files)) + " files done")
    except:
        print("File " + str(filename) + " konnte nicht eingelesen werden.")
        errors.append(str(filename))
        pass

# Dateien die nicht ausgelesen werden konnten werden zurückgegeben.
if len(errors) != 0:
    print("\nFolgende Dateien konnten nicht eingelesen werden:")
    [print(error) for error in errors]

# Ausgabedatei wird erstellt.
data.reset_index(drop=True).to_excel(
    Path(directory_out_str + str(datetime.now().strftime("%y%m%d_%H%M")) +
         "_categorized_parts" + ".xlsx"), index=False
)

print("\nKategorisierung abgeschlossen.")

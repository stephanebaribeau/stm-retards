import logging
import sqlite3
import zipfile
from pathlib import Path
import pandas as pd
import requests

URL_GTFS = "https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip"
DOSSIER_DATA = Path("data")
CHEMIN_ZIP = DOSSIER_DATA / "gtfs_stm.zip"
CHEMIN_BD = DOSSIER_DATA / "gtfs.db"
PETITES_TABLES = ["routes", "trips", "stops", "calendar", "calendar_dates"]
COLONNES_STOP_TIMES = ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"]

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        )
log = logging.getLogger("charger_gtfs")


def telecharger(url: str, destination: Path) -> None:
    log.info("Telechargement de %s", url)
    with requests.get(url, stream=True, timeout=60) as reponse:
        reponse.raise_for_status()
        with open(destination, "wb") as fichier:
            for bloc in reponse.iter_content(chunk_size=1024 * 1024):
                fichier.write(bloc)
    log.info("Telecharge: %.1f Mo", destination.stat().st_size / 1e6)


def en_secondes(heures: pd.Series) -> pd.Series:
    """ Convertit '25:10:30' en secondes depuis le début de la journée de service."""
    morceaux = heures.str.split(":",  expand=True).apply(pd.to_numeric)
    return (morceaux[0] * 3600 + morceaux[1] * 60 + morceaux[2]).astype("Int64")
     

def lire_csv(archive: zipfile.ZipFile, nom: str, **options) -> pd.DataFrame:
    with archive.open(nom) as fichier:
        return pd.read_csv(fichier, dtype=str, **options)


def charger_tables(connexion: sqlite3.Connection, archive: zipfile.ZipFile) -> None:
    fichiers_presents = archive.namelist()

    for table in PETITES_TABLES:
        nom_fichier = f"{table}.txt"
        if nom_fichier not in fichiers_presents:
            log.warning("%s absent de l'archive, ignoré", nom_fichier)
            continue
        df = lire_csv(archive, nom_fichier)
        df.to_sql(table, connexion, if_exists="replace", index=False)
        log.info("%-15s %10d lignes", table, len(df))

    log.info("Lecture de stop_times.txt (ca peut prendre une minute)...")
    stop_times = lire_csv(archive, "stop_times.txt", usecols=COLONNES_STOP_TIMES)
    stop_times["stop_sequence"] = stop_times["stop_sequence"].astype(int)
    stop_times["arrival_sec"] = en_secondes(stop_times["arrival_time"])
    stop_times.to_sql("stop_times", connexion, if_exists="replace", index=False, chunksize=100_000)
    log.info("%-15s %10d lignes", "stop_times", len(stop_times))


def creer_index(connexion: sqlite3.Connection) -> None:
    log.info("Création des index")
    connexion.execute("CREATE INDEX IF NOT EXISTS idx_stop_times ON stop_times (trip_id, stop_sequence)")
    connexion.execute("CREATE INDEX IF NOT EXISTS idx_trips on trips (trip_id)")
    connexion.execute("CREATE INDEX IF NOT EXISTS idx_stops on stops (stop_id)")
    connexion.commit()

def main() -> None:
    DOSSIER_DATA.mkdir(exist_ok=True)
    telecharger(URL_GTFS, CHEMIN_ZIP)

    connexion = sqlite3.connect(CHEMIN_BD)
    try:
        with zipfile.ZipFile(CHEMIN_ZIP) as archive:
            charger_tables(connexion, archive)
        creer_index(connexion)
    finally:
        connexion.close()

    log.info("Terminé : %s", CHEMIN_BD)


if __name__ == "__main__":
    main()


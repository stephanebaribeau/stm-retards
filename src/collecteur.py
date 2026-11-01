import logging
import os
import sqlite3
import time
from pathlib import Path
import requests
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2
from explorer_flux import URL_POSITION, lire_flux

INTERVALLE_SECONDES = 30
CHEMIN_BD = Path("data/positions.db")

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        )
log = logging.getLogger("collecteur")

StatutArret = gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus
StatutOccupation = gtfs_realtime_pb2.VehiclePosition.OccupancyStatus

def creer_bd(chemin: Path) -> sqlite3.Connection:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    connexion = sqlite3.connect(chemin)
    connexion.execute("""
                      CREATE TABLE IF NOT EXISTS positions (
                          vehicle_id    TEXT    NOT NULL,
                          timestamp     INTEGER NOT NULL,
                          trip_id       TEXT,
                          start_date    TEXT,
                          route_id      TEXT,
                          direction_id  INTEGER,
                          latitude      REAL,
                          longitude     REAL,
                          bearing       REAL,
                          speed         REAL,
                          stop_sequence INTEGER,
                          stop_id       TEXT,
                          current_status TEXT,
                          occupancy     TEXT,
                          PRIMARY KEY (vehicle_id, timestamp)
                        )
                      """)
    return connexion

def extraire_lignes(flux: gtfs_realtime_pb2.FeedMessage) -> list[tuple]:
    lignes = []
    for entite in flux.entity:
        if not entite.HasField("vehicle"):
            continue

        v = entite.vehicle
        lignes.append((
            v.vehicle.id,
            v.timestamp,
            v.trip.trip_id,
            v.trip.start_date,
            v.trip.route_id,
            v.trip.direction_id,
            v.position.latitude,
            v.position.longitude,
            v.position.bearing,
            v.position.speed,
            v.current_stop_sequence,
            v.stop_id,
            StatutArret.Name(v.current_status),
            StatutOccupation.Name(v.occupancy_status),
            ))

    return lignes

def enregistrer(connexion: sqlite3.Connection, lignes: list[tuple]) -> int:
    avant = connexion.total_changes
    connexion.executemany(
            "INSERT OR IGNORE INTO positions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            lignes,
        )
    connexion.commit()
    return connexion.total_changes - avant

def main() -> None:
    load_dotenv()
    cle_api = os.getenv("STM_API_KEY")
    if not cle_api:
        raise SystemExit("STM_API_KEY manquante dans le fichier .env")

    connexion = creer_bd(CHEMIN_BD)
    log.info("Collecte démarrée, enregistrement dans %s", CHEMIN_BD)

    try:
        while True:
            try:
                flux = lire_flux(URL_POSITION, cle_api)
                lignes = extraire_lignes(flux)
                nouvelles =  enregistrer(connexion, lignes)
                log.info("%d véhicules reçus, %d nouvelles_positions", len(lignes), nouvelles)
            except requests.RequestException as erreur:
                log.warning("Erreur résesau : %s", erreur)

            time.sleep(INTERVALLE_SECONDES)
    except KeyboardInterrupt:
        log.info("Arrêt demandé, fermeture de la base de donées")
    finally:
        connexion.close()


if __name__ == "__main__":
    main()


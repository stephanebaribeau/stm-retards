import os
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2

URL_POSITION = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions"

def lire_flux(url: str, cle_api: str) -> gtfs_realtime_pb2.FeedMessage:
    """ Appel l'API et décode la réponse Protocol Buffers."""
    reponse = requests.get(url, headers={"apiKey": cle_api}, timeout=30)
    reponse.raise_for_status()

    flux = gtfs_realtime_pb2.FeedMessage()
    flux.ParseFromString(reponse.content)
    return flux

def afficher_resume(flux: gtfs_realtime_pb2.FeedMessage, nb_exemples: int = 5) -> None:
    horodatage = datetime.fromtimestamp(flux.header.timestamp, tz=timezone.utc)
    print(f"Flux généré à: {horodatage.isoformat()}")
    print(f"Nombre d'entitée : {len(flux.entity)}\n")

    for entite in flux.entity[:nb_exemples]:
        if not entite.HasField("vehicle"):
            continue

        v = entite.vehicle
        print(f"Véhicule      : {v.vehicle.id}")
        print(f"  Ligne       : {v.trip.route_id}")
        print(f"  Trajet      : {v.trip.trip_id}")
        print(f"  Position    : {v.position.latitude:.5f}, {v.position.longitude:.5f}")
        print(f"  horodatage  : {datetime.fromtimestamp(v.timestamp, tz=timezone.utc)}")
        print()

    print("=== Exemple brut ===")
    print(flux.entity[0])


def main() -> None:
    load_dotenv()
    cle_api = os.getenv("STM_API_KEY")
    if not cle_api:
        raise SystemExit("STM_API_KEY manquante dans le fichier .env")

    flux = lire_flux(URL_POSITION, cle_api)
    afficher_resume(flux)


if __name__ == "__main__":
    main()


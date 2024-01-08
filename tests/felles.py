# Lager relevante filbaner
import os
from pathlib import Path

import pandas as pd

from fram import FRAM

FILNAVN_FASIT = Path(__file__).parent / "fasiter.csv"
testinputfiler = Path(__file__).parent / 'input'
analysemappe = Path(str(Path(__file__).parent.parent / "fram" / "eksempler" / "eksempel_analyser"))
inputmappe = Path(str(analysemappe / "Inputfiler"))
ramappe = Path(str(analysemappe / "RA"))
outputmappe = Path(str(analysemappe / "Outputfiler"))
# Henter inn riktige strekninger som skal kjøre


strekningsliste = [i[:-5] for i in os.listdir(inputmappe) if i.endswith("xlsx") if not "fram 3_5" in i]

# Henter tiltakspakker for hver relevante strekning
strekning_pakke = []
for strekning in strekningsliste:
    tiltakspakker = list(map(lambda i: i[7:-5], os.listdir(outputmappe / strekning)))
    for pakke in tiltakspakker:
        if not pakke:
            continue
        strekning_pakke.append((strekning, int(pakke)))

skal_ha_delvis_fram = {
    "Strekning 3": [5, 9, 1],
    "Strekning 9": [11, 12, 21, 22, 31, 32, 33, 34],
    "Strekning 12.1": [29, 1, 14],
    "Strekning 10" : [90,80,40,51],
    "Strekning 8" : [1,4,9],
    "Strekning 12.2" : [14],
    "Strekning 15" : [1],
}

skal_ha_aisyrisk = {
    "Strekning 14": [11]
}

def fasiter():
    return (
        pd.
        read_csv(FILNAVN_FASIT)
        .loc[lambda df: df.Virkninger != "0"]
    )

def beregn_lonnsomhet(strekning, pakke):
    delvis = pakke in skal_ha_delvis_fram.get(strekning, [])
    aisyrisk = pakke in skal_ha_aisyrisk.get(strekning, [])
    s = FRAM(
        str(inputmappe / str(strekning + ".xlsx")),
        tiltakspakke=pakke,
        les_RA_paa_nytt=False,
        ra_dir=ramappe,
        delvis_fram=delvis,
        aisyrisk_input=aisyrisk,
    )
    s.run(skriv_output=False)
    return s.kontantstrommer().reset_index().drop('Aktør', axis=1).set_index(['Virkninger'])["Nåverdi levetid"]


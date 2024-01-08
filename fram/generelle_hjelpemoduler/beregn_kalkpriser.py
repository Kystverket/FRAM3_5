from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd

from fram.generelle_hjelpemoduler.konstanter import FRAM_DIRECTORY
from fram.virkninger.drivstoff.hjelpemoduler_virkningsgrad import virkningsgrad
from fram.virkninger.tid.verdsetting import _tidskalk_vektet



def beregn(tilaar: int):
    """
    Denne funksjonen leser inn informasjon fra filen "nasjonale_mmsi_vekter" i Forutsetninger_FRAM. Dette er
    et xlsx-ark med beriket skipsinformasjon og mmsi-vekter per mmsi. Basert på denne arkfanen
    lages det nasjonale kalkulasjonspriser for  for tidsavhengige
    (kroner per time) og distanseavhengige kostnader (kroner per time) for et gitt år. Disse lagres på gitmappe,
    og kan brukes videre i de samfunnsøkonomiske beregningene. OBS! Denne overskriver
    gjeldende kalkulasjonspriser for samme år. mmsi-vektene har angitt følgende kolonner:
        mmsi
        vekt - antall mmsi-punkter innenfor et avgrenset geografisk område
        Skipstype - Kystverkets skipstyper
        Lengdegruppe - Kystverkets lengdegrupper
        speed - service-hastighet
         engine_kw_total - motorstørrelse
        dwt - dødvektstonn
        grosstonnage - bruttotonnasje
        skipslengde - lengde i meter
        gasskap - gasskapasitet
        year_built - år bygget

    Args
    - tilaar: kroneåret du vil ha priser oppgitt i

    Returns
    xlsx-bok med nasjonale kalkulasjonspriser for drivstoff og  tidsavhengige kostnader
    fordelt etter skipstype og lengdegruppe. Disse legger seg på følgende plassering:
    fram/kalkpriser/tid_drivstoff.
    """

    filbane = FRAM_DIRECTORY / "kalkpriser" / "tid_drivstoff" / f"nasjonale_tidskostnader_{str(tilaar)}.xlsx"

    # TIDSKOSTNADER
    writer = pd.ExcelWriter(filbane, engine="xlsxwriter",)
    print("Beregner tidskostnader med _tidskalk_vektet")

    nasjonale_vekter = FRAM_DIRECTORY / "Forutsetninger_FRAM.xlsx"

    tidskostnader_nasjonale = _tidskalk_vektet(nasjonale_vekter, tilaar, "nasjonale_mmsi_vekter")

    tidskostnader_nasjonale.to_excel(writer, sheet_name="Tidskostnader")

    writer.close()

    # DRIVSTOFFKOSTNADER
    print("Leser inn nasjonale vekter til distanseavhengige kostnader")
    skipsinfo = pd.read_excel(nasjonale_vekter, sheet_name="nasjonale_mmsi_vekter")
    for col in ["engine_kw_total", "year_built", "speed"]:
        skipsinfo[col] = skipsinfo[col].replace(-1, None)

    #  Lager en dict for å drivstoffspesifikke "stubnames"
    # SFOC() og get_SFOC() er byttet ut med virkningsgrad() og get_virkningsgrad()
    miks = dict(
        zip(
            ["MGO og HFO", "LNG", "Karbonøytrale drivstoff", "Elektrisitet"],
            ["MGO", "LNG", "NOY", "EL"],
        )
    )

    for drivstofftype in miks.keys():
        skipsinfo[f"Virkningsgrad_{miks[drivstofftype]}"] = virkningsgrad(
            skipsinfo, drivstofftype
        )  # PF - endret til type
        skipsinfo[f"Virkningsgrad_{miks[drivstofftype]}"] = skipsinfo[
            f"Virkningsgrad_{miks[drivstofftype]}"
        ].replace(0.0, np.nan)

    skipsinfo = (
        skipsinfo.dropna(
            subset=["Virkningsgrad_MGO"]
        )  # PF fjerner manglende verdier der det ikke er noen skip nasjonalt
        .groupby(["Skipstype", "Lengdegruppe"])
        .apply(
            lambda x: pd.Series(
                {
                    "Virkningsgrad_MGO": vektet_gjennomsnitt_dropna(
                        x.Virkningsgrad_MGO, vekter=x.vekt
                    ),
                    "Virkningsgrad_LNG": vektet_gjennomsnitt_dropna(
                        x.Virkningsgrad_LNG, vekter=x.vekt
                    ),
                    "Virkningsgrad_NOY": vektet_gjennomsnitt_dropna(
                        x.Virkningsgrad_NOY, vekter=x.vekt
                    ),
                    "Virkningsgrad_EL": vektet_gjennomsnitt_dropna(x.Virkningsgrad_EL, vekter=x.vekt),
                    "engine_kw_total": vektet_gjennomsnitt_dropna(x.engine_kw_total, vekter=x.vekt),
                    "speed": vektet_gjennomsnitt_dropna(x.speed, vekter=x.vekt),
                }
            )
        )
        .rename(columns={"speed": "service_speed"})
    )

    skipsinfo = skipsinfo[
        [
            "engine_kw_total",
            "service_speed",
            "Virkningsgrad_MGO",
            "Virkningsgrad_LNG",
            "Virkningsgrad_NOY",
            "Virkningsgrad_EL",
        ]
    ].reset_index()

    skipsinfo.to_excel(
        FRAM_DIRECTORY
        / "kalkpriser"
        / "tid_drivstoff"
        / "nasjonale_drivstoffvekter.xlsx", index=False
    )

def vektet_gjennomsnitt_dropna(serie, vekter):
    """ Dropper na i serie før den regner ut vektet gjsn med vekter som vekter 
    """
    not_na_idx = serie.notnull()
    return np.average(serie[not_na_idx], weights=vekter[not_na_idx])

if __name__ == "__main__":
    beregn(
        tilaar=2021
    )
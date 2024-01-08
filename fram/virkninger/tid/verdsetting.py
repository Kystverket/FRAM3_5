"""
Funksjoner for å hente frem og beregne kalkpriser. Både en hovedfunksjon for å hente frem ferdigberegnede kalkpriser,
i tillegg til flere hjelpefunksjoner.

:py:func:`~fram.virkninger.tid.verdsetting.get_kalkpris_tid` benyttes for å hente ut ferdigberegnede kalkpriser på strekningsnivå.

Hjelpefunksjonene henger sammen på følgende måte:

- :py:func:`~fram.virkninger.tid.verdsetting._kalkulasjonspris_tid_strekning` benyttes som toppnivå i `beregn`-scriptet. Denne tar en liste med mmsi og metadata
  og sammenstiller fornuftig gjennomsnittsinformasjon etter å ha filtrert ut outliers.
- :py:func:`~fram.virkninger.tid.verdsetting._kalkp_tid` kalles av funksjonen over. Den kaller på underliggende nivå og får ferdigberegnede kalkpriser i et gitt
  utgangsaar. Deretter realprisjusterer den og gjør klar en kalkpris i riktig kroneår
- :py:func:`~fram.virkninger.tid.verdsetting._tidskost_kalk` anvender konkrete funksjoner (estimert av Propel AS) på skipsmetadata for å regne ut kalkpriser på
  mmsi-nivå.

"""
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler import kalkpriser
from fram.generelle_hjelpemoduler.hjelpefunksjoner import get_lengdegruppe
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.tid.schemas import KalkprisTidSchema


@verbose_schema_error
@pa.check_types(lazy=True)
def get_kalkpris_tid(
    filbane_tidskost: Path,
    til_kroneaar: int,
    beregningsaar: List[int],
    opprinnelig_kroneaar: int,
) -> DataFrame[KalkprisTidSchema]:
    tid = pd.read_excel(filbane_tidskost, sheet_name="Tidskostnader")
    tid["Skipstype"] = tid["Skipstype"].fillna(method="ffill")

    if "21-28" in tid.Lengdegruppe.unique():
        raise KeyError(
            "Kalkprisene inneholder de gamle lengdegruppene. Dette er feil! \n, Kjør Kalkpriser.beregn(strekning,filbane_til_vekter)"
        )

    tid[opprinnelig_kroneaar] = tid["kalkp_tid"]
    forste_aar = min(til_kroneaar, opprinnelig_kroneaar, min(beregningsaar))
    siste_aar = max(til_kroneaar, opprinnelig_kroneaar, max(beregningsaar))

    for year in range(forste_aar + 1, siste_aar + 1):
        tid[year] = tid[year - 1] * (1 + kalkpriser.get_vekstfaktor(year))
    return tid[["Skipstype", "Lengdegruppe"] + beregningsaar]


def _tidskalk_per_skip(df, tilaar, utgangsaar=2021):
    """
    En hjelpemetode som beregner tidsavhengige kostnader for skip i en bestemt
    df. Henter inn definerte kalkulasjonspriser for bestemte skipstyper som avhenger
    av skipenes egenskaper. Deretter både kroneprisjusteres og realprisjusteres disse.

    Args:
        df: DatFrame som må ha kolonnene 'Skipstype', 'dwt', 'grosstonnage', 'gasskap' og 'skipslengde'
        utgangsaar: Året i int som du vil ha prisjustert fra. Defalut er 2021
        tilaar: Året i int som du vil ha prisjustert til. Default er None og da hentes predefinerte kroneår fra `Forutsetninger_FRAM.xlsx` tilgjengelig fra fram\

    Returns:
        En dataframe (df) med tidsavhengige kalkulasjonspris (krone per time) som er både krone- og realprisjustert.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("df må være en pandas DataFrame")
    if not isinstance(utgangsaar, int):
        raise ValueError("utgangsaar må være et integer")
    if not utgangsaar <= tilaar:
        raise ValueError("utangsaar må være mindre eller lik tilaar")
    for col in ["Skipstype", "dwt", "grosstonnage", "gasskap", "skipslengde"]:
        if col not in list(df):
            raise KeyError(f"df må ha en kolonne {col}")

            
    prisfaktor = kalkpriser.prisjustering(1, utgangsaar, tilaar)
    realfaktor = kalkpriser.realprisjustering_kalk(
        belop=1, utgangsaar=utgangsaar, tilaar=tilaar
    )
    priser_ujustert = df.apply(
        lambda x: tidskalk_funksjoner(
            Skipstype=x["Skipstype"],
            dwt=x["dwt"],
            grosstonnage=x["grosstonnage"],
            gasskap=x["gasskap"],
            skipslengde=x["skipslengde"],
        ),
        axis=1,
    )
    priser_justert = priser_ujustert * prisfaktor * realfaktor
    return priser_justert


def tidskalk_funksjoner(
    Skipstype, dwt=None, grosstonnage=None, gasskap=None, skipslengde=None
):
    """
    Hjelpemetode som lager funksjoner for beregning av tidsavhengige kostnader på mmsi-nivå.
    Funksjonene er hentet fra Kystverket, og spesifisert i `Forutsetninger_FRAM.xlsx` tilgjengelig fra fram.

    Det finnes i utgangspunktet ikke kalkulasjonspriser for fiskefartøy over 100 meter, men for skip større enn 100 meter 
    benyttes prisen for de mellom 28 til 100 justert for lengde.

    Disse prisene benyttes til å lage kalkulasjonspriser for bruk i FRAM. For å spare tid så ferdigberegnes kalkulasjonspriser i FRAM. 
    Dersom prisene under oppdateres må nye ferdigberegnede priser estimeres. Disse kan beregnes ved å benyttes følgende funksjon:
    `from fram.generelle_hjelpemoduler.kalkpriser import beregn`.

    Args:
        Skipstype: Skipstype i henhold til Kystverkets skipstyper.
        dwt: Skipets dødsvektstonn.
        grosstonnage: Skipets bruttotonnasje.
        gasskap: Skipets gasskapasitet.
        skipslengde: Skipets lengde målt i meter.

    Returns:
        En float med tidsavhengig kalkulasjonspris (kroner per time) for et gitt skip og skipstype. Kroneverdi er 2021.

    """
    # hack for å unngå at manglende verdier leses som np.nan
    if type(Skipstype) != str:
        Skipstype = "Mangler"

    if Skipstype == "Oljetankskip":
        if dwt > 0:
            return 0.011 * dwt + 4269
        else:
            return np.nan

    elif Skipstype == "Kjemikalie-/Produktskip":
        if dwt > 0:
            return 0.0823 * dwt + 2161.3
        return np.nan

    elif Skipstype == "Gasstankskip":
        if gasskap > 0:
            return 0.1001 * gasskap + 3969.4
        else:
            return np.nan

    elif Skipstype == "Bulkskip":
        if dwt > 0:
            return 0.0427 * dwt + 1049.9   
        else:
            return np.nan

    elif Skipstype == "Stykkgods-/Roro-skip":
        if dwt > 0:
            return 0.186 * dwt + 74.535     
        return np.nan

    elif Skipstype == "Containerskip":
        if dwt > 0:
            return 0.0681 * dwt + 2235.7
        else:
            return np.nan

    elif Skipstype == "Passasjerbåt":
        if grosstonnage > 0:
            return 1.0237 * grosstonnage + 2660.1
        else:
            return np.nan

    elif Skipstype == "Passasjerskip/Roro":
        if grosstonnage > 0:
            return 1.0237 * grosstonnage + 2660.1
        else:
            return np.nan

    elif Skipstype == "Cruiseskip":
        if grosstonnage > 0:
            return 1.0237 * grosstonnage + 2660.1
        else:
            return np.nan

    elif Skipstype == "Offshore supplyskip":
        if grosstonnage > 0:
            return (dwt / 4000) * 3994
        else:
            return np.nan

    elif Skipstype == "Andre offshorefartøy":
        if grosstonnage > 0:
            return (dwt / 4000) * 3994
        else:
            return np.nan

    elif Skipstype == "Brønnbåt":
        if grosstonnage > 0:
            return 2.076 * grosstonnage + 414.01
        return np.nan

    elif Skipstype == "Slepefartøy":
        if grosstonnage > 0:
            return (dwt / 4000) * 17752
        else:
            return np.nan

    elif Skipstype == "Andre servicefartøy":
        if grosstonnage > 0:
            return 2.076 * grosstonnage + 414.01
        else:
            return np.nan

     # Tester nye kalkpriser
    elif Skipstype == "Fiskefartøy":
        if skipslengde <= 0:
            return np.nan
        elif skipslengde <= 13:
            return 496
        elif 13 < skipslengde <= 28:
            return 92 * skipslengde - 731
        elif skipslengde > 28:
            return 152 * skipslengde - 2487
        else:
            return np.nan

    elif Skipstype == "Annet":
        return np.nan
    else:
        return np.nan


def _tidskalk_vektet(filbane_mmsi_vekter, tilaar, sheet):
    """
    Hjelpefunksjon som legger til kalkulasjonspris for tidsbruk for skip, og kollapser per skipstype
    og lengdegruppe innenfor en strekning.

    Args:
        filbane_mmsi_vekter: Peker til en fil der du har mmsi, vekt, og de relevante metadatakolonnene for de skipene du vil bruke som utgangspunkt for å beregne kalkulasjonsprisene dine.
        tilaar: kroneprisåret du vil ha oppgitt prisene i
        sheet: arknavn i excelbok med mmsi-vekter

    Returns:
        Dataframe med tidsavhengig kalkulasjonspriser (kroner per time) per Skipstype og Lengdegruppe vektet etter mmsi.
        
    """
    if isinstance(filbane_mmsi_vekter, str):
        filbane_mmsi_vekter = Path(filbane_mmsi_vekter)
    if not filbane_mmsi_vekter.is_file():
        raise FileNotFoundError(
            f"Finner ikke filen med mmsi_vekter på {filbane_mmsi_vekter}"
        )
    mmsi_observasjoner = pd.read_excel(filbane_mmsi_vekter, sheet_name=sheet).assign(
        Lengdegruppe=lambda df: df.skipslengde.map(get_lengdegruppe)
    )
    if "gasskap" not in mmsi_observasjoner:
        mmsi_observasjoner["gasskap"] = np.nan
    mmsi_observasjoner["kalkp_tid"] = _tidskalk_per_skip(mmsi_observasjoner, tilaar)

    # fjerner de observasjonene som ser rare ut.
    # dette gjelder der vi mangler info til å beregne kalkpriser
    mmsi_observasjoner = mmsi_observasjoner.dropna(subset=["kalkp_tid"])
    # dette gjelder der kalkprisene blir null eller negative
    mmsi_observasjoner = mmsi_observasjoner.loc[mmsi_observasjoner.kalkp_tid > 0]
    # dette gjelder der vi ikke har data og disse er satt til -1
    mmsi_observasjoner = mmsi_observasjoner.loc[
        (mmsi_observasjoner.dwt != -1) | (mmsi_observasjoner.grosstonnage != -1)
    ]
    output = (
        mmsi_observasjoner.loc[mmsi_observasjoner.kalkp_tid.notnull()]
        .groupby(["Skipstype", "Lengdegruppe"])
        .apply(
            lambda x: pd.Series(
                {
                    "kalkp_tid": np.average(x.kalkp_tid, weights=x.vekt),
                    "grosstonnage": np.average(x.grosstonnage, weights=x.vekt),
                    "dwt": np.average(x.dwt, weights=x.vekt),
                    "gasskap": np.average(x.gasskap, weights=x.vekt),
                    "gjsn_lengde": np.average(x.skipslengde, weights=x.vekt),
                    "antall_observasjoner": np.sum(x.vekt),
                }
            )
        )
    )
    return output

import datetime
from typing import Optional

import numpy as np
import pandas as pd

from fram.generelle_hjelpemoduler.hjelpefunksjoner import forut, get_forut_verdi

KRONEAAR = int(get_forut_verdi("Kroneår"))
REALPRISVEKST = get_forut_verdi("Realprisvekst")
PERSONSKADER = forut("kalkpriser_helse", 2)


def get_vekstfaktor(
    aar: int, kroneaar: int = KRONEAAR, realprisvekst: int = REALPRISVEKST,
):
    """Hjelpemetode for å regne ut vekstfaktoren som behøves for å realprisjustere til et gitt fremtidsår"""
    if aar <= kroneaar:
        return 0
    elif aar <= 2060:
        return realprisvekst
    elif aar > 2060:
        return max(realprisvekst * (1 - (aar - 2060) / (2100 - 2060)), 0)


def realprisjustering_kalk(
    belop: float, utgangsaar: int, tilaar: int = KRONEAAR,
):
    """
    Realprisjusterer 'belop' fra 'utgangsaar' til 'tilaar'

    Args:

    - belop: Beløpet du vil realprisjustere
    - utgangsaar: Året du realprisjusterer fra
    - tilaar: Året du realprisjusterer til.  Default er None og da henter
      den informasjon fra forutsetninger_FRAM.xlsx som ligger på utiltites/kost_nytte

    Returns:
    En float med realprisjustert belop.
    """

    REALPRIS = dict(
        zip(forut("BNP per innbygger")["aar"], forut("BNP per innbygger")["realpris"])
    )

    if not isinstance(utgangsaar, int):
        raise ValueError("utgangsaar må være int")
    if utgangsaar > tilaar:
        raise ValueError(
            f"utgangsaar ({utgangsaar}) må være mindre eller lik tilaar ({tilaar})."
        )
    faktor = 1
    for aar in range(tilaar - 1, utgangsaar - 1, -1):
        justering = REALPRIS[aar]
        faktor = faktor * justering
    return faktor * belop


def prisjustering(belop: float, utgangsaar: int, tilaar: Optional[int] = None):
    """
    Prisjusterer 'belop' fra 'utgangsaar' til 'tilaar'

    Args:

    - belop: Beløp i kroner du vil ha prisjustert
    - utgangsaar: Året i int som du vil ha prisjustert fra
    - tilaar: Året i int som du vil ha prisjustert til. Default er None og da henter
      den informasjon fra forutsetninger_SOA.xlsx som ligger på utiltites/kost_nytte

    Returns
    En float med prisjustert belop
    """

    if tilaar is None:
        tilaar = KRONEAAR
    if not isinstance(utgangsaar, int):
        raise ValueError("utgangsaar må være et integer")
    if not utgangsaar <= tilaar:
        raise ValueError("utangsaar må være mindre eller lik tilaar")
    sluttdeflator = get_forut_verdi(f"Deflator{str(tilaar)[-2:]}")
    deflator = get_forut_verdi(f"Deflator{str(utgangsaar)[-2:]}")
    return belop / (deflator / sluttdeflator)


def diskontering(
    sammenstillingsaar: Optional[int] = datetime.datetime.today().year,
    fra_aar: Optional[int] = datetime.datetime.today().year,
    til_aar: Optional[int] = datetime.datetime.today().year + 75,
):
    """
    Lager en diskonteringsfaktor for hvert år i fra_aar til og med til_aar.
    Bruker forutsetninger basert på Finansdepartementets rundskriv r109-14.

    Args:
        - sammenstillingsaar: Første rente i rentetrappa. Default er i år
        - fra_aar - hvilket år man vil starte fra. Default er i år
        - til_aar - hvilket år man vil slutte i. Default er i år + 75 år

    Returns:
        Dataframe med diskonteringsfaktorer og rente fra (fra_aar) og til (til_aar)
    for et gitt sammenstillingsaar.
    """
    beregningsaar = np.arange(min(fra_aar, sammenstillingsaar), til_aar + 1)
    forste_aar_rente_3_prosent = get_forut_verdi("Diskår 2")
    forste_aar_rente_2_prosent = get_forut_verdi("Diskår 3")
    rente = np.where(
        beregningsaar < forste_aar_rente_3_prosent,
        0.04,
        np.where(beregningsaar < forste_aar_rente_2_prosent, 0.03, 0.02),
    )
    rente = (
        pd.Series(index=beregningsaar, data=rente)
        .rename("rente")
        .to_frame()
        .assign(diskonteringsfaktor=lambda x: (x.rente + 1).cumprod(axis=0))
        .assign(
            diskonteringsfaktor=lambda x: 1
            / (x.diskonteringsfaktor / x.diskonteringsfaktor[sammenstillingsaar])
        )
        .loc[lambda x: x.index >= fra_aar]
    )

    return rente

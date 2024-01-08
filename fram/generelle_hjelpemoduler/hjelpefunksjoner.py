import functools
from typing import Union, Any, List

import numpy as np
import pandas as pd

from openpyxl import workbook, worksheet
from openpyxl.utils.dataframe import dataframe_to_rows
from pandas import DataFrame

from fram.generelle_hjelpemoduler.konstanter import (
    VERDSATT_COLS,
    ALLE,
    MISSING_LENGDE,
    FRAM_DIRECTORY,
    VERDSATT_COLS_STRING_VALUES,
    VERDSATT_COLS_INT_VALUES,
    ALLE_INT,
    SKATTEFINANSIERINGSKOSTNAD,
)


def interpoler_linear_vekstfaktor(
    grunnaar: int, verdi_grunnaar: np.array, sluttaar: int, verdi_sluttaar: np.array
):
    """Hjelpemetode for å interpolere verdier lineært mellom grunnår og sluttår

    Benytter numpy for (svært) mye raskere interpolering

    Args:
        grunnaar: Året du har første observasjoner for
        verdi_grunnaar: Verdiene i grunnåret
        sluttaar: Siste året du har observasjoner for
        verdi_sluttaar: Verdiene i sluttåret

    Returns:
        DataFrame: med samme antall rader som lengden på verdi_grunnaar og verdi_sluttaar,
        der hver kolonne utgjør et år i perioden [grunnaar, sluttaar]
    """
    aar = np.arange(grunnaar, sluttaar + 1)
    tidsspenn = sluttaar - grunnaar
    verdi_grunnaar = verdi_grunnaar.reshape((verdi_grunnaar.shape[0], 1))
    verdi_sluttaar = verdi_sluttaar.reshape((verdi_sluttaar.shape[0], 1))
    verdier = (
        verdi_grunnaar * (sluttaar - aar) + verdi_sluttaar * (aar - grunnaar)
    ) / tidsspenn

    return pd.DataFrame(columns=aar, data=verdier)


def interpoler_produkt_vekstfaktor(
    grunnaar: int, verdi_grunnaar, sluttaar: int, verdi_sluttaar
):
    """Hjelpemetode for å interpolere verdier eksponensielt (konstant årlig vekstfaktor) mellom grunnår og sluttår

    Benytter numpy for (svært) mye raskere interpolering

    Args:
        grunnaar: Året du har første observasjoner for
        verdi_grunnaar (array): Verdiene i grunnåret
        sluttaar: Siste året du har observasjoner for
        verdi_sluttaar (array): Verdiene i sluttåret

    Returns:
        DataFrame: med samme antall rader som lengden på verdi_grunnaar og verdi_sluttaar,
        der hver kolonne utgjør et år i perioden [grunnaar, sluttaar]
    """
    aar = (np.arange(grunnaar, sluttaar + 1) - grunnaar)[np.newaxis, :]
    tidsspenn = sluttaar - grunnaar
    aarlig_vekst = (verdi_sluttaar / verdi_grunnaar) ** (1 / tidsspenn)
    vekstfaktorer = np.power(aarlig_vekst[:, np.newaxis], aar)
    verdier = np.multiply(verdi_grunnaar[:, np.newaxis], vekstfaktorer)

    return pd.DataFrame(columns=list(range(grunnaar, sluttaar + 1)), data=verdier)


def lag_kontantstrom(
    tidsserie: DataFrame,
    navn: str,
    diskonteringsfaktorer: DataFrame,
    levetid: List[int],
    analyseperiode: List[int],
):
    """Hjelpemetode for å lage og diskontere kontantstrøm

    Args:
        tidsserie: Må være en dataframe med aar som indeks og verdiene som
            celler. Må ha en kolonne som heter `navn`
        navn: Kolonnen det skal lages tidsserie av. Må være i `tidsserie`
        diskonteringsfaktorer: Diskonteringsfaktorer og rente fra (fra_aar) og til (til_aar)
        levetid: Liste med årene i hele tilakets levetid
        analyseperiode: Liste med årene i analyseperioden

    """
    if not isinstance(tidsserie, pd.DataFrame):
        raise ValueError("tidsserie må være en DataFrame")
    if navn not in list(tidsserie):
        raise KeyError(f"{navn} er ikke en kolonne i 'tidsserie'")

    # Pandas reagerer hvis man ikke har verdier i tidsserien for alle år i levetid. Fyller derfor ut med nullere
    tidsserie = tidsserie.copy().reindex(levetid).fillna(0)

    kontantstr_levetid = pd.Series(
        data=(
            diskonteringsfaktorer["diskonteringsfaktor"][levetid]
            * tidsserie[navn][levetid]
        ).sum(),
        index=["Nåverdi levetid"],
    ).append(tidsserie[navn])

    kontantstr = pd.Series(
        data=(
            diskonteringsfaktorer["diskonteringsfaktor"][analyseperiode]
            * tidsserie[navn][analyseperiode]
        ).sum(),
        index=["Nåverdi analyseperiode"],
    ).append(kontantstr_levetid)

    return kontantstr


def fyll_indeks(df, **kwargs):
    """
    Fyller inn manglende outputindekskolonner i investeringskostnaddataframen.
    """
    df = df.reset_index()
    if "index" in df.columns:
        df = df.drop("index", axis=1)
    for navn, arg in kwargs.items():
        if arg in df.index.names:
            pass
        elif arg in df.columns:
            df = df.rename(columns={arg: navn})
        elif arg is not None:
            df[navn] = arg
        else:
            df[navn] = ALLE

    for col in VERDSATT_COLS_STRING_VALUES:
        if col not in df.columns:
            df[col] = ALLE
    for col in VERDSATT_COLS_INT_VALUES:
        if col not in df.columns:
            df[col] = ALLE_INT

    if SKATTEFINANSIERINGSKOSTNAD not in df.columns:
        df[SKATTEFINANSIERINGSKOSTNAD] = 0.0

    return df.set_index(VERDSATT_COLS)


def _legg_til_kolonne(
    df: pd.DataFrame, kolonnenavn: Union[str, int], kolonneverdier: Any
):
    """ Hjelpemetode for å kunne assigne variable kolonnenavn i en metodekjede """
    if callable(kolonneverdier):
        df[kolonnenavn] = kolonneverdier(df)
    else:
        df[kolonnenavn] = kolonneverdier
    return df


def get_lengdegruppe(lengde):
    """Mapper en lengde (float eller int) til en av de spesifiserte lengdegruppene fra Kystverket.

    Args:
        lengde (float): Lengde i float

    Returns:
        str: Navnet på lengdegruppen, slik angitt av Kystverket og brukt i SØA
    """
    try:
        lengde = float(lengde)
    except ValueError:
        return MISSING_LENGDE
    lengdegrupper = [
        (0, MISSING_LENGDE),
        (30, "0-30"),
        (70, "30-70"),
        (100, "70-100"),
        (150, "100-150"),
        (200, "150-200"),
        (250, "200-250"),
        (300, "250-300"),
        (1000, "300-"),
    ]
    for terskel, kategori in lengdegrupper:
        if lengde <= terskel:
            return kategori
    return MISSING_LENGDE


@functools.lru_cache(maxsize=3)
def forutsetninger_soa():
    """Hjelpemetode for å cache en Excel-fil vi leser mange ganger"""
    return pd.ExcelFile(FRAM_DIRECTORY / "Forutsetninger_FRAM.xlsx")


def forut(sheet: str, antall_kolonner: int = 5):
    """
    Hjelpemetode for å hente inn informasjon fra forutsetningsbok. Denne forutsetnings-
    boken er en xlsx-bok med predefinerte forusetninger i Kystverkets analyser. Filen
    ligger på fram/kost_nytte/Forutsetninger_FRAM.xlsx.

    Args:
        sheet: spesifisering av hvilken arkfane du vil lese inn fra forutsetningsboken.
        antall_kolonner: speisifisering av hvor mange kolonner du vil ha med fra
        kolonne A.

    Returns:
        DataFrame: Returnerer en dataframe med informasjon fra forutsetningsboken.
    """
    inputdata = pd.read_excel(
        forutsetninger_soa(),
        sheet_name=sheet,
        usecols=list(range(antall_kolonner + 1)),
    )
    return inputdata


def get_forut_verdi(variabel: str) -> float:
    """
    Hjelpemetode for å raskt hente fra forutsetningsarket. Variabel må være en streng.

    Args:

    variabel: spesifisering av variabel du ønsker å hente ut. Kan velge mellom
      følgende variabler: "Ferdigstillelsesår", "Sammenstillingsår", "Analyseperiode",
      "Levetid", "Skattefinansieringskostnad", "Selskapsskattesats", "Skjermingsfradrag skatt",
      "Marinalskattesats", "Diskår 1", "Diskår 2", "Diskår 3", "Kalkrente 1", "Kalkrente 2",
      "Kalkrente 3", "Realprisvekst", "Deflator09", "Deflator10", "Deflator11", "Deflator12",
      "Deflator13", "Deflator14", "Deflator15", "Deflator16", "Deflator17", "Deflator18",
      "Deflator19", "Deflator20", "Kroneår", "KPI-vekst forventet"

    Returns:
        Verdi for spesifisert variabel.
    """

    FORUTSETNINGER = dict(
        zip(forut("Forutsetninger")["Variabel"], forut("Forutsetninger")["Verdi"])
    )

    if variabel not in FORUTSETNINGER.keys():
        raise KeyError(f"Finner ikke {variabel} under forutsetninger")
    return FORUTSETNINGER[variabel]


def _multiply_df_with_col(df, column):
    """ Hjelpefunksjon for å gange en dataframe med en av sine egne kolonner """
    return df.multiply(df[column], axis=0)


def _divide_df_with_col(df, column):
    """ Hjelpefunksjon for å dele en dataframe på en av sine egne kolonner """
    return df.divide(df[column], axis=0)


def legg_til_kolonne_hvis_mangler(df: pd.DataFrame, kolonnenavn: Union[list, int, str], fyllverdi):
    """
    Hjelpefunksjon for å legge til manglende kolonner i en dataframe
    Args:
        df: Dataframen det gjelder
        kolonnenavn: Navnene som skal sjekkes om mangler. Liste eller enkeltkolonner
        fyllverdi: verdien det skal fylles med. Må være én unik verdi

    Returns:
        Dataframe med tillagte kolonner
    """
    out = df.copy()
    if not isinstance(kolonnenavn, list):
        kolonnenavn = list(kolonnenavn)
    for col in kolonnenavn:
        if col not in out.columns:
            out[col] = fyllverdi
    return out
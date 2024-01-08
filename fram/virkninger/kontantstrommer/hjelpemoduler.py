import pandas as pd
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.kalkpriser import prisjustering
from fram.virkninger.kontantstrommer.schemas import KontanstromSchema


def prisjuster_kontantstrom(kontantstrom: DataFrame[KontanstromSchema], kroneaar: int) -> DataFrame[KontanstromSchema]:
    """
    Prisjusterer kontantstrømmene fra året angitt i "Kroneverdi"-kolonnen til kroneaar
    Args:
        kontantstrom: Dataframe med kontantstrøm
        kroneaar: kroneåret du vil justere til.

    Returns:
        DataFrame: Kontantstrømmene prisjustert til kroneaar

    """
    kontantstrom = kontantstrom.copy()
    if "Kroneverdi" in list(kontantstrom):
        for idx, row in kontantstrom.iterrows():
            for aar in [
                col
                for col in kontantstrom.columns
                if isinstance(col, int) or col.isdigit()
            ]:
                kontantstrom.loc[idx, aar] = prisjustering(
                    belop=kontantstrom.loc[idx, aar],
                    utgangsaar=int(row.Kroneverdi),
                    tilaar=kroneaar,
                )

    return kontantstrom


def legg_til_skattefinansieringskostnad_hvis_mangler(df):
    """
    Legger til manglende kolonne Skattefinansieringskostnad hvis den ikke finnes. Settes til 0 skattekost"

    Args:
        df (DataFrame): Dataframen skattefinansiering skal legges til

    Returns:
        DataFrame: df med skattefinansieringskolonne
    """
    df = df.copy()
    if "Andel skattefinansieringskostnad" not in df.columns:
        df["Andel skattefinansieringskostnad"] = 0

    return df

def legg_til_aktør_hvis_mangler(df):
    """
    Legger til manglende kolonne aktør hvis den ikke finnes. Settes til 'Ikke kategorisert'"

    Args:
        df (DataFrame): Dataframen aktør skal legges til

    Returns:
        DataFrame: df med aktørkolonne
    """
    df = df.copy()
    if "Aktør" not in df.columns:
        df["Aktør"] = "Ikke kategorisert"

    return df

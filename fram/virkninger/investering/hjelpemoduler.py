import pandas as pd
from pandera.typing import DataFrame
from typing import Callable, List

from fram.generelle_hjelpemoduler.hjelpefunksjoner import _legg_til_kolonne
from fram.virkninger.investering.schemas import InvesteringskostnadSchema
from fram.generelle_hjelpemoduler.kalkpriser import prisjustering
from fram.generelle_hjelpemoduler.konstanter import FOLSOMHET_KOLONNE, KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG
from datetime import datetime

def sikre_bakoverkompatibilitet_investtype(
    investeringskostnader: DataFrame[InvesteringskostnadSchema],
    logger: Callable = print,
) -> DataFrame[InvesteringskostnadSchema]:
    """
    Funksjon for å sikre at input som ikke er fordelt over 'Utdyping', 'Navigasjonsinnretninger' og 'Annet' blir det.

    Args:
        investeringskostnader: Investeringskostnader fra input
        logger: callable som log-meldinger skal skrives til

    Returns:
        DataFrame: Investeringskostnader-df med investeringer fordelt utover "Utdyping", "Navigasjonsinnretninger" og "Annet".

    """
    if (
        investeringskostnader is None
        or "Investeringstype" in investeringskostnader.columns
    ):
        return investeringskostnader
    logger(
        "Advarsel: Ettersom investeringstype ikke er angitt, spres investeringskostnadene likt utover 'Utdyping', 'Navigasjonsinnretninger' og 'Annet'"
                )
    return (
        pd.concat([investeringskostnader] * 3)
        .assign(
            kr=lambda df: df["Forventningsverdi (kroner)"] / 3,
            Investeringstype=sorted(["Utdyping", "Navigasjonsinnretninger", "Annet"]
            * len(investeringskostnader)),
        )
        .pipe(
            _legg_til_kolonne,
            KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG,
            lambda df: df[KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG] / 3
        )
        .drop("Forventningsverdi (kroner)", axis=1)
        .rename(columns={"kr": "Forventningsverdi (kroner)"})
    )


def prisjuster_investeringskostnader(
    investeringskostnader: DataFrame[InvesteringskostnadSchema], kroneaar: int
) -> DataFrame[InvesteringskostnadSchema]:
    """
    Prisjusterer investeringskostnadene fra året angitt i "Kroneverdi"-kolonnen

    Args:
        investeringskostnader: Investeringskostnader fra inputfila
        kroneaar: året prisene skal justeres til

    Returns:
        Prisjusterte investeringskostnader
    """
    for col in ["P50 (kroner)", "Forventningsverdi (kroner)"]:
        investeringskostnader[col] = investeringskostnader.apply(
            lambda row: prisjustering(row[col], int(row["Kroneverdi"]), kroneaar),
            axis=1,
        )

    return investeringskostnader


def fyll_beregningsaar(df, beregningsaar: List[int]):
    """
    Fyller inn manglende beregningsår i en dataframe med data for noen år.

    Args:
        df (DataFrame): DataFramen som skal fylles
        beregningsaar: Årskolonner som skal kreves i DataFramen

    Returns:
        DataFrame: df med alle årskolonner
    """
    df = df.set_index(
        ["Tiltaksomraade", "Tiltakspakke", "Investeringstype", FOLSOMHET_KOLONNE]
    )
    fyll_df = pd.DataFrame(index=df.index, columns=beregningsaar).fillna(0)

    return fyll_df.add(df, fill_value=0).reset_index()


def spre_kostnader(totalt: float, forste: int, siste: int, analysestart: int):
    """
    Hjelpemetode for å spre kostnadene utover anleggsårene. Denne vil feile om analysestart er senere enn første år med kostnader

    Args:
        totalt: Totale kostnader i hele perioden
        forste: Første år med investeringskostnader
        siste: Siste år med investeringskostnader
        analysestart: Året du starter analysen fra. 

    Returns:
        Series: Pandas serie med kostnadene uniformt fordelt over årene mellom forste og siste

    """
    if forste < analysestart:
        raise ValueError(f"Du har investeringskostnader som kommer før analysestart og disse kommer ikke med i beregningen. Flytt ferdigstillelsesår eller anleggsperiode")
    else:
        aarlig = totalt / (siste + 1 - forste)
        return pd.Series({year: aarlig for year in range(forste, siste + 1)})


def spre_investeringskostnader(investeringskostnader: DataFrame[InvesteringskostnadSchema], 
kolonne: str = "Forventningsverdi (kroner)", ferdigstillelsesaar: int = 2026, analysestart: int = datetime.now().year):
    """
    Sprer investeringskostnader over beregningsårene for den angitte kolonnen.
    Args:
        investeringskostnader: DataFrame med investeringskostnader
        kolonne: Kolonnen som skal spres.
        ferdigstillelsesaar: Første året med nyttevirkning
        analysestart: Året analysen starter

    Returns:
        DataFrame: Investeringskostnadene spredt over årskolonner
    """

    return (
        investeringskostnader[
            ["Tiltaksomraade", "Tiltakspakke", "Analysenavn", "Investeringstype"]
        ]
        .reset_index(drop=True)
        .join(
            pd.DataFrame(
                [
                    spre_kostnader(
                        investeringskostnader.iloc[i][kolonne],
                        ferdigstillelsesaar -investeringskostnader.iloc[i]["Anleggsperiode"],
                        ferdigstillelsesaar - 1,
                        analysestart,
                    )
                    for i in range(len(investeringskostnader))
                ]
            )
        )

    )


def legg_til_utslipp_hvis_mangler(df):
    """
    Legger til manglende kolonne CO2-utslipp hvis den ikke finnes. Settes til 0"

    Args:
        df (DataFrame): Dataframen utslippet skal legges til

    Returns:
        DataFrame: df med kolonne CO2-utslipp
    """
    df = df.copy()
    if KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG not in df.columns:
        df[KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG] = 0

    return df
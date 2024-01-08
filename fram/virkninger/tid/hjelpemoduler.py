from typing import List

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.schemas import TidsbrukPerPassSchema
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error


@verbose_schema_error
@pa.check_types(lazy=True)
def fremskriv_konstant_tidsbruk_per_passering(
    tidsbruk: pd.Series, fremskrivingskolonner: List
) -> DataFrame[TidsbrukPerPassSchema]:
    """
    Fremskriver innholdet i serien `tidsbruk` over alle kolonnene i `fremskrivingskolonner`

    Args:
        tidsbruk:  En pd.Series med verdier som skal framskrives
        fremskrivingskolonner: Kolonnene du vil ha skrevet verdien til

    Returns:
        pd.DataFrame
    """
    tidsbruk = tidsbruk.to_frame("Input")
    for col in fremskrivingskolonner:
        tidsbruk[col] = tidsbruk["Input"].astype(float)
    return tidsbruk


def multipliser_venstre_hoyre(venstre, hoyre, koblekolonner, multipliseringskolonner):

    koblet = venstre.merge(hoyre, how="left", on=koblekolonner, indicator=True)

    for col in multipliseringskolonner:
        koblet[col] = koblet[str(col) + "_x"].multiply(koblet[str(col) + "_y"])

    return koblet


def sjekk_alle_koblet(
    df: pd.DataFrame,
    feilmelding: str,
    lete_kolonner: List,
    unntak: str,
    unntak_verdi: str,
):
    """
    Hjelpefunksjon for å sjekke at kolonnenavn _merge er both for alle rader unntatt de der alle lete_kolonner
    er lik null.
    Args:
        df: dataframe man sjekke hvis ingen feil returneres den uendret
        feilmelding: feilen man vil gi beskjed om i en valueerror
        lete_kolonner: kolonnene man vil sjekke om man har match på.
        unntak: kolonner man ønsker redusere
        unntak_verdi: kolonneverdi i kolonne unntak man ønsker å redusere med

    Returns:
        df

    """

    df_med_feil = (
        df.copy()
        .loc[lambda df: df._merge != "both"]
        .loc[lambda df: df[lete_kolonner].apply(lambda row: all(row != 0), axis=1)]
        .reset_index()
        .loc[lambda df: df[unntak] != unntak_verdi]
    )

    if len(df_med_feil) == 0:
        return df

    else:
        raise ValueError(feilmelding + "\n" + df_med_feil.to_string())

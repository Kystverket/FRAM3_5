from typing import List, Callable, Tuple

import pandas as pd
from pandera.typing import DataFrame

from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.risiko.hjelpemoduler.generelle import hent_ut_konsekvensinput, lag_konsekvensmatrise
from fram.virkninger.risiko.schemas import KonsekvensmatriseSchema


@verbose_schema_error
def les_inn_konsekvensmatriser(beregningsaar: List[int],
                               excel_inputfil: pd.ExcelFile,
                               tiltakspakke: int,
                               logger: Callable = print) -> Tuple[
    DataFrame[KonsekvensmatriseSchema],
    DataFrame[KonsekvensmatriseSchema],
]:
    """ Leser inn konvekvensmatriser basert på inputboken for strekningen som analyseres

    Trenger en liste med beregningsår, en inputbok en tiltakspakke og et sted å logge. Sjekker om arkfanene
    "Konsekvensinput referansebanen" og "Konsekvensinput TP {tiltakspakke}" eksisterer. Hvis ja, forsøker den å lese
    inn disse. Hvis nei, benytter den like standardmatriser fra Excel-boken med felles forutsetninger

    Args:
        beregningsaar: Liste med heltall beregningsår
        excel_inputfil: En åpnet pandas ExcelFile for strekningen som analyseres
        tiltakspakke: Heltall som angir tiltakspakken som analyseres
        logger: En funksjon der vi kan logge, defaulter til print

    Returns:
        konsekvensmatrise_ref: Gyldig konsekvensmatrise som kan benyttes i virkningen Risiko
        konsekvensmatrise_tiltak: Gyldig konsekvensmatrise som kan benyttes i virkningen Risiko

    """
    standard_konsekvensinput = hent_ut_konsekvensinput()
    standard_konsekvensmatrise = lag_konsekvensmatrise(standard_konsekvensinput, beregningsaar)
    if "Konsekvensinput referansebanen" not in excel_inputfil.sheet_names:
        logger(
            "Finner ikke at det er angitt spesifikk konksenvensmatriseinput for referansebanen. Benytter standard konsekvensmatrise")
        konsekvensmatrise_ref = standard_konsekvensmatrise
    else:
        logger("Leser inn input til konsekvensmatrise i referansebanen fra brukerangitt inputfil")
        konsekvensinput_ref = pd.read_excel(excel_inputfil, sheet_name="Konsekvensinput referansebanen")
        konsekvensmatrise_ref = lag_konsekvensmatrise(konsekvensinput_ref, beregningsaar)

    if f"Konsekvensinput TP {tiltakspakke}" not in excel_inputfil.sheet_names:
        logger(
            f"Finner ikke at det er angitt spesifikk konksenvensmatriseinput for tiltakspakken (sjekket 'Konsekvensinput TP {tiltakspakke}'). Benytter standard konsekvensmatrise")
        konsekvensmatrise_tiltak = standard_konsekvensmatrise
    else:
        logger(f"Leser inn input til konsekvensmatrise i tiltaksbanen fra brukerangitt inputfil")
        konsekvensinput_tiltak = pd.read_excel(excel_inputfil, sheet_name=f"Konsekvensinput TP {tiltakspakke}")

        konsekvensmatrise_tiltak = lag_konsekvensmatrise(konsekvensinput_tiltak, beregningsaar)

    return konsekvensmatrise_ref, konsekvensmatrise_tiltak

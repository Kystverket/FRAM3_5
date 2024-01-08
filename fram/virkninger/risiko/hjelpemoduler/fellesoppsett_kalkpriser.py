from pathlib import Path
from typing import Union, List

from pandas import ExcelFile
import pandas as pd
from pandera.typing import DataFrame
import pandera as pa

from fram.generelle_hjelpemoduler.excel import vask_kolonnenavn_for_exceltull
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.risiko.hjelpemoduler.generelle import ARKNAVN_KONSEKVENSER_UTSLIPP
from fram.virkninger.risiko.hjelpemoduler.verdsetting import get_kalkpris_oljeutslipp, \
    get_kalkpris_opprenskingskostnader
from fram.virkninger.risiko.schemas import KalkprisOljeutslippSchema, KalkprisOljeopprenskingSchema
from fram.virkninger.ventetid.hjelpemoduler import set_columns


def hent_om_angitt_spesifikke_utslippskonsekvensark(inputfil: Union[Path, str, ExcelFile], tiltakspakke: int) -> dict:
    input_df = pd.read_excel(inputfil, sheet_name=f"Tiltakspakke {tiltakspakke}", skiprows=1, index_col=None)

    if len(input_df.axes[1])<45:
        return {}
    else:
        input_df = (input_df.iloc[:,[43,44,45]]
        .dropna(how="all")
        .pipe(vask_kolonnenavn_for_exceltull)
        .set_index("Analyseomraade")
        .pipe(set_columns, ["ref", "tiltak"])
        .dropna(how="all")
        .to_dict(orient="index")
        )
        return input_df


@verbose_schema_error
@pa.check_types(lazy=True)
def les_inn_kalkpriser_utslipp(kroneaar: int,
                               beregningsaar: List[int],
                               excel_inputfil: Union[Path, str],
                               tiltakspakke: int,
                               analyseomraader: List[str],
                               logger: callable = print) -> (
    DataFrame[KalkprisOljeutslippSchema],
    DataFrame[KalkprisOljeutslippSchema],
    DataFrame[KalkprisOljeopprenskingSchema],
    DataFrame[KalkprisOljeopprenskingSchema],
):
    """
    En funksjon ment å benyttes direkte i FRAM for å lese inn konsekvensmatriser for utslipp fra angitt Excel-input.

    Tar en filbane, en tiltakspakke, en liste med analyseområder, et kroneår og en liste med beregningsår som input.
    Den leser så først inn fra arket 'Tiltakspakke x' hvilke brukerangitte utslippskonsekvenser som er, deretter setter
    den sammen kalkpriser for utslipp og opprensking i referanse- og tiltaksbanen, hvor den hhv benytter brukerangitte
    og standard konsekvensmatriser, avhengig av hva den finner.

    Parameters:
        kroneaar: Kroneåret analysen skal gjøres i. Kalkpriser oppdateres til dette året
        beregningsaar: Liste over de årene du vil ha beregnet kalkpriser for
        excel_inputfil: Filbane til input-filen den skal lete i
        tiltakspakke: Nummeret på tiltakspakken. Brukes for å finne rett inputark
        analyseomraader: Liste over analyseområder det skal lages kalkpriser for. Uten denne, kan den ikke fylle ut alle
        logger: Dersom du vil lede loggingen til noe annet enn print. Må være callable med tekst som input
    """
    an_omr_til_ark = hent_om_angitt_spesifikke_utslippskonsekvensark(inputfil=excel_inputfil, tiltakspakke=tiltakspakke)
    kalkpriser_utslipp_ref = []
    kalkpriser_utslipp_tiltak = []
    kalkpriser_opprensking_ref = []
    kalkpriser_opprensking_tiltak = []

    felles_kalkpris_utslipp = get_kalkpris_oljeutslipp(
        konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP,
        kroneaar=kroneaar,
        beregningsaar=beregningsaar
    )

    felles_kalkpris_opprensking = get_kalkpris_opprenskingskostnader(
        kroneaar=kroneaar, beregningsaar=beregningsaar,
        konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP
    )

    for omraade in analyseomraader:
        spesifikke_ark = an_omr_til_ark.get(omraade, {})
        # Deretter tiltaksbanen
        if not spesifikke_ark or (spesifikke_ark.get("ref") is None): #Ikke angitt i input, vi bruker standard
            logger(f"Finner ikke angitte konsekvensark for utslipp i referansebanen for tiltaksomraade {omraade}. Benytter standard i FRAM")
            kalkpriser_utslipp_ref.append(felles_kalkpris_utslipp.assign(Analyseomraade=omraade))
            kalkpriser_opprensking_ref.append(felles_kalkpris_opprensking.assign(Analyseomraade=omraade))
        else:
            logger(f"Benytter brukerangitte utslippskonsekvenser for tiltaksomraade {omraade} i referansebanen, fra arket {spesifikke_ark['ref']}")
            # logger(spesifikke_ark["ref"])
            bok_ark = excel_inputfil+":::"+spesifikke_ark["ref"]
            try:
                kalkpris_utslipp_ref = get_kalkpris_oljeutslipp(
                konsekvenser_utslipp_sheet_name=bok_ark,
                kroneaar=kroneaar,
                beregningsaar=beregningsaar
            )
            except ValueError as e:
                logger(f"Kalkpris utslipp: Fikk likevel ikke til den brukerangitte utslippskonsekvensen {e}")
                kalkpris_utslipp_ref = felles_kalkpris_utslipp
            try:
                kalkpris_opprensking_ref = get_kalkpris_opprenskingskostnader(
                kroneaar=kroneaar, beregningsaar=beregningsaar,
                konsekvenser_utslipp_sheet_name=bok_ark,
            )
            except ValueError as e:
                logger(f"Kalkpris opprensking: Fikk likevel ikke til den brukerangitte utslippskonsekvensen {e}")
                kalkpris_opprensking_ref = felles_kalkpris_opprensking
            kalkpriser_utslipp_ref.append(kalkpris_utslipp_ref.assign(Analyseomraade=omraade))
            kalkpriser_opprensking_ref.append(kalkpris_opprensking_ref.assign(Analyseomraade=omraade))

        if not spesifikke_ark or (spesifikke_ark.get("tiltak") is None): #Ikke angitt i input, vi bruker standard
            logger(f"Finner ikke angitte konsekvensark for utslipp i tiltaksbanen for tiltaksomraade {omraade}. Benytter standard i FRAM")
            kalkpriser_utslipp_tiltak.append(felles_kalkpris_utslipp.assign(Analyseomraade=omraade))
            kalkpriser_opprensking_tiltak.append(felles_kalkpris_opprensking.assign(Analyseomraade=omraade))
        else:
            logger(
                f"Benytter brukerangitte utslippskonsekvenser for tiltaksomraade {omraade} i tiltaksbanen, fra arket {spesifikke_ark['ref']}")
            bok_ark = excel_inputfil+":::"+spesifikke_ark["tiltak"]
            try:
                kalkpris_utslipp_tiltak = get_kalkpris_oljeutslipp(
                konsekvenser_utslipp_sheet_name=bok_ark,
                kroneaar=kroneaar,
                beregningsaar=beregningsaar
            )
            except ValueError as e:
                logger(f"Fikk likevel ikke til den brukerangitte utslippskonsekvensen: {e}")
                kalkpris_utslipp_tiltak = felles_kalkpris_utslipp
            try:
                kalkpris_opprensking_tiltak = get_kalkpris_opprenskingskostnader(
                kroneaar=kroneaar, beregningsaar=beregningsaar,
                konsekvenser_utslipp_sheet_name=bok_ark
            )
            except ValueError as e:
                logger(f"Fikk likevel ikke til den brukerangitte utslippskonsekvensen: {e}")
                kalkpris_opprensking_tiltak = felles_kalkpris_opprensking
            kalkpriser_utslipp_tiltak.append(kalkpris_utslipp_tiltak.assign(Analyseomraade=omraade))
            kalkpriser_opprensking_tiltak.append(kalkpris_opprensking_tiltak.assign(Analyseomraade=omraade))


    return (
        pd.concat(kalkpriser_utslipp_ref),
        pd.concat(kalkpriser_utslipp_tiltak),
        pd.concat(kalkpriser_opprensking_ref),
        pd.concat(kalkpriser_opprensking_tiltak)
    )
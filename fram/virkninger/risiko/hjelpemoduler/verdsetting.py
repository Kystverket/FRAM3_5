"""Her ligger verdsettingsfaktorer osvg"""
from pathlib import Path
from typing import List

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

import fram.generelle_hjelpemoduler.hjelpefunksjoner
from fram.generelle_hjelpemoduler import kalkpriser
from fram.generelle_hjelpemoduler.hjelpefunksjoner import interpoler_linear_vekstfaktor
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.risiko.hjelpemoduler import (
    oljeutslipp,
    opprensking,
)
from fram.virkninger.risiko.hjelpemoduler.generelle import ARKNAVN_KONSEKVENSER_UTSLIPP
from fram.virkninger.risiko.hjelpemoduler.utslipp_felles import hent_sannsynligheter
from fram.virkninger.risiko.schemas import (
    KalkprisHelseSchema,
    KalkprisOljeutslippSchema,
    KalkprisMaterielleSchema,
    KalkprisOljeopprenskingSchema,
)
from fram.virkninger.tid.schemas import KalkprisTidSchema

PERSONSKADER = fram.generelle_hjelpemoduler.hjelpefunksjoner.forut(
    "kalkpriser_helse", 2
)
MAPPE_FERDIGBEREGNET_OLJEUTSLIPP = (
    Path(__file__).parent.parent.parent.parent / "kalkpriser" / "oljeutslipp"
)


@verbose_schema_error
@pa.check_types(lazy=True)
def get_kalkpris_helse(kroneaar: int, siste_aar: int) -> DataFrame[KalkprisHelseSchema]:
    """
    Hovedfunksjon for å hente kalkulasjonspriser på helse

    Sørger for at alle verdier er kronejustert til `kroneaar`. Gir en dataframe med indeks "Konsekvens",
    som tar verdiene "Dodsfall" og "Personskade", samt kolonner i hvert år fra og med kroneaar til (men ikke med)
    siste_aar
    Args:
        kroneaar: Året du vil ha verdiene kronejustert til
        siste_aar: Siste året det beregnes kalkulasjonspriser for

    Returns:
        DataFrame med verdsettingsfaktorer for dødsfall og personskader
    """
    # Slår opp og finner gyldige verdier i kroneåret
    personulykker = pd.DataFrame(
        {
            kroneaar: {
                "Dodsfall": _verdi_per_skade_mennesker("Dødsfall", kroneaar),
                "Personskade": _verdi_per_skade_mennesker("Personskade", kroneaar),
            }
        }
    )
    # Prisjusterer og fyller ut alle år fra og med kroneaar til siste_aar
    for year in range(kroneaar + 1, siste_aar):
        personulykker[year] = personulykker[year - 1] * (
            1 + kalkpriser.get_vekstfaktor(year)
        )
    personulykker.index = personulykker.index.rename("Konsekvens")
    return personulykker


def _verdi_per_skade_mennesker(omfang: str, tilaar: int):
    """
    Gjør oppslag i excel på verden av ulike typer personskader og realprisjusterer til tilaar

    Args:
    - omfang: Tar følgende input: Dødsfall eller Personskade
    - tilaar: Året i int som du vil ha prisjustert til.

    Returns:
        Float med prisjustert verdi (kr per personskade) for personskade og dødsfall.

    """
    if tilaar!=2024:
        raise ValueError("VSL er bare definert i 2024-kroner etter sommeren 2023.")
    if omfang not in ["Dødsfall", "Personskade"]:
        raise ValueError("omfang må være en av to kategorier: Dødsfall, Personskade")
    if omfang == "Dødsfall":
        personskade = PERSONSKADER.loc[
            PERSONSKADER["Variabel"] == omfang, "Input"
        ].values[0]
        kroneaar = int(
            PERSONSKADER.loc[PERSONSKADER["Variabel"] == omfang, "Kroneverdi"].values[0]
        )
        prisfaktor = kalkpriser.prisjustering(1, kroneaar, tilaar)
        realfaktor = kalkpriser.realprisjustering_kalk(1, kroneaar, tilaar)
        omfang_justert = personskade * prisfaktor * realfaktor
    else:
        personskade = PERSONSKADER.loc[
            PERSONSKADER["Variabel"] == "Gjennomsnitt rapportert personskade", "Input",
        ].values[0]
        kroneaar = int(
            PERSONSKADER.loc[
                PERSONSKADER["Variabel"] == "Gjennomsnitt rapportert personskade",
                "Kroneverdi",
            ].values[0]
        )
        prisfaktor = kalkpriser.prisjustering(1, kroneaar, tilaar)
        realfaktor = kalkpriser.realprisjustering_kalk(1, kroneaar, tilaar)
        omfang_justert = personskade * prisfaktor * realfaktor

    return omfang_justert


@verbose_schema_error
@pa.check_types(lazy=True)
def get_kalkpris_materielle_skader(
    kroneaar: int,
    beregningsaar: List[int],
    tidskostnader: DataFrame[KalkprisTidSchema],
) -> DataFrame[KalkprisMaterielleSchema]:
    """
    Leser inn fra Excel og beregner reparasjonskostnader og kostnader ved tid ute av drift. Disse
    oppstår som følge av grunnstøting, kontaktskade og kollisjoner
    (struck og striking - de er like).

    Args:
        kroneaar: Hvilket kroneår virkningen skal prissettes i
        beregningsaar: For hvilke år du ønsker å få beregnet verdsettingsfaktorer
        tidskostnader: En dataframe med gyldige verdsettingskostnader for tid

    Returns:
    En dataframe (df) per skipstype, lengdegruppe og hendelsestype med kalkulasjonspriser for
    reparasjonskostnader og tid ute av drift over tid. Tid ute av drift realprisjusteres. Alt
    er oppgitt i kroner per hendelse.
    """
    tidskostnader = tidskostnader.set_index(["Skipstype", "Lengdegruppe"])
    sheet_names = {
        "Striking": "kalkpris_materiell_koll",
        "Struck": "kalkpris_materiell_koll",
        "Grunnstøting": "kalkpris_materiell_grunn",
        "Kontaktskade": "kalkpris_materiell_kontakt",
    }
    output = []
    for navn, sheet_name in sheet_names.items():
        kollpriser = (
            fram.generelle_hjelpemoduler.hjelpefunksjoner.forut(sheet_name, 6)
            .iloc[:160, :]
            .assign(
                Reparasjonskostnader=lambda x: kalkpriser.prisjustering(
                    belop=x.Reparasjonskostnader,
                    utgangsaar=int(x["Kroneverdi repkostnader"].values[0]),
                    tilaar=kroneaar,
                )
            )
            .drop("Kroneverdi repkostnader", axis=1)
            .set_index(["Skipstype", "Lengdegruppe"])[
                ["Reparasjonskostnader", "tid_u_drift"]
            ]
        )
        for analyse in tidskostnader.Analysenavn.unique():
            for year in beregningsaar:
                kollpriser[f"tid_u_drift_{year}"] = (
                    kollpriser["tid_u_drift"] * tidskostnader.query(f"Analysenavn=='{analyse}'")[year]
                ).fillna(0)

            output.append(
                kollpriser.drop("tid_u_drift", axis=1)
                .assign(Hendelsestype=navn)
                .reset_index()
                .set_index(["Skipstype", "Lengdegruppe", "Hendelsestype"])
                .assign(Analysenavn=analyse)
            )
    return pd.concat(output, axis=0, sort=False)


@verbose_schema_error
@pa.check_types(lazy=True)
def get_kalkpris_oljeutslipp(
    konsekvenser_utslipp_sheet_name: str, kroneaar: int, beregningsaar: List[int],
) -> DataFrame[KalkprisOljeutslippSchema]:
    """
    Lager en tabell med kalkulasjonspriser for oljeutlipp (kroner per hendelse)
    fordelt på Hendelsestype, Skipstype, lengdegruppe, Drivstofftype, Saarbarhet og
    fylke. Hensyntar endringer i drivstoff, og typer drivstoff
    som forventes fremover i tid. Kalkulasjonsprisene varierer over tid både som følge av endring i drivstoff-
    sammensetning og fordi kalkulasjonsprisene realprisjusteres over tid.

    Args:
        kroneaar: Året du vil ha kroneverdiene i
        beregningsaar: Liste over år du vil ha beregnet kalkpriser for

    Returns:
    Dataframe med kalkulasjonspriser som varierer over tid og som avhenger av hendelsestype, skipstype,
    lengdegruppe, drivstofftype, sårbarhet i området og fylke.
    """
    sammensatt = oljeutslipp._hent_kalkpriser(kroneaar=kroneaar, konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name).merge(
        hent_sannsynligheter(konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name),
        left_index=True,
        right_index=True,
        how="left",
    )
    sammensatt["vektet_pris_2018"] = (
        sammensatt["Kalkpris"] * sammensatt["Sannsynlighet2018"]
    )
    sammensatt["vektet_pris_2050"] = (
        sammensatt["Kalkpris"] * sammensatt["Sannsynlighet2050"]
    )
    sammensatt = (
        sammensatt.groupby(
            by=[
                "Hendelsestype",
                "Skipstype",
                "Lengdegruppe",
                "Drivstofftype",
                "Saarbarhet",
                "Fylke",
                "Lasttype",
            ]
        )[["vektet_pris_2018", "vektet_pris_2050"]]
        .sum()
        .reset_index()
    )

    # Setter prisen for hendelsestypen Striking til null fordi denne ikke skal verdsettes i følge DNV GL
    sammensatt.loc[sammensatt.Hendelsestype == "Striking", "vektet_pris_2018"] = 0
    sammensatt.loc[sammensatt.Hendelsestype == "Striking", "vektet_pris_2050"] = 0

    sammensatt = pd.merge(
        sammensatt.drop(["vektet_pris_2018", "vektet_pris_2050"], axis=1),
        interpoler_linear_vekstfaktor(
            2018,
            sammensatt["vektet_pris_2018"].values,
            2050,
            sammensatt["vektet_pris_2050"].values,
        ),
        left_index=True,
        right_index=True,
    )
    siste_aar = max(beregningsaar[-1], 2060) + 1
    for year in range(2051, siste_aar):
        sammensatt[year] = sammensatt[2050]

    vekstfaktorer = pd.Series(
        {year: 1 + kalkpriser.get_vekstfaktor(year) for year in range(2018, siste_aar)}
    ).cumprod()

    for col in range(2018, siste_aar):
        sammensatt[col] = sammensatt[col] * vekstfaktorer[col]

    sammensatt = sammensatt[
        ["Hendelsestype", "Skipstype", "Lengdegruppe", "Saarbarhet", "Fylke",]
        + beregningsaar
    ]
    return sammensatt


@verbose_schema_error
@pa.check_types(lazy=True)
def get_kalkpris_opprenskingskostnader(
    kroneaar: int, beregningsaar: List[int], konsekvenser_utslipp_sheet_name: str
) -> DataFrame[KalkprisOljeopprenskingSchema]:
    """
    Verdsetter opprenskingskostnader (kroner per hendelse) som følge av oljeutslipp.
    Kalkulasjonsprisen avhenger av hvor mange tonn olje som slippes ut ved en hendelse. Bruker derfor informasjon
    om forventet utslippsmengde ved en hendelse, og beregner opprenskingskostnaden.

    Args:
        kroneaar: Året du vil ha kroneverdiene regnet om til
        beregningsaar: De årene du vil ha kalkpriser for

    Returns:
        Dataframe med opprenskingskostnader per hendelse fordelt på skipstype, lengdegruppe og hendelsestype.
    """

    forventet_opprensingskostnad_bunkers = opprensking.bunkers_utslipp_opp(
        kroneaar=kroneaar, konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name
    )
    forventet_opprensingskostnad_last = opprensking.last_utslipp_opp(kroneaar=kroneaar, konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name)
    forventet_opprensingskostnad = forventet_opprensingskostnad_bunkers.merge(
        forventet_opprensingskostnad_last, how="left", left_index=True, right_index=True
    )
    forventet_opprensingskostnad["vektet_pris_2018"] = forventet_opprensingskostnad[
        "vektet_pris_2018"
    ].fillna(0)
    forventet_opprensingskostnad["vektet_pris_2050"] = forventet_opprensingskostnad[
        "vektet_pris_2050"
    ].fillna(0)
    forventet_opprensingskostnad["vektet_pris_2018"] = (
        forventet_opprensingskostnad["vektet_pris_2018"]
        + forventet_opprensingskostnad["kalkpris_bunker_2018"]
    )
    forventet_opprensingskostnad["vektet_pris_2050"] = (
        forventet_opprensingskostnad["vektet_pris_2050"]
        + forventet_opprensingskostnad["kalkpris_bunker_2050"]
    )
    forventet_opprensingskostnad = forventet_opprensingskostnad.drop(
        [
            "kalkpris_bunker_2018",
            "kalkpris_bunker_2050",
            "Utslippsmengde_bunkers_2018",
            "kalkpris_bunker_2050",
        ],
        axis=1,
    ).reset_index()

    # Setter prisen for hendelsestypen Striking til null fordi denne ikke skal verdsettes i følge DNV GL
    forventet_opprensingskostnad.loc[
        forventet_opprensingskostnad.Hendelsestype == "Striking", "vektet_pris_2018"
    ] = 0
    forventet_opprensingskostnad.loc[
        forventet_opprensingskostnad.Hendelsestype == "Striking", "vektet_pris_2050"
    ] = 0

    forventet_opprensingskostnad = pd.merge(
        forventet_opprensingskostnad.drop(
            ["vektet_pris_2018", "vektet_pris_2050"], axis=1
        ),
        interpoler_linear_vekstfaktor(
            2018,
            forventet_opprensingskostnad["vektet_pris_2018"].values,
            2050,
            forventet_opprensingskostnad["vektet_pris_2050"].values,
        ),
        left_index=True,
        right_index=True,
    )
    siste_aar = max(beregningsaar[-1], 2060) + 1
    for year in range(2051, siste_aar):
        forventet_opprensingskostnad[year] = forventet_opprensingskostnad[2050]

    return forventet_opprensingskostnad

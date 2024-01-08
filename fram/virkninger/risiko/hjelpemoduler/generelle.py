"""
Se tekst i .ventetidssituasjon.py
"""
from collections import OrderedDict
from pathlib import Path
from typing import List, Optional, Tuple, Any, Union

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame
from xlrd import XLRDError

from fram.generelle_hjelpemoduler.excel import angi_kolonnenavn, vask_kolonnenavn_for_exceltull
from fram.generelle_hjelpemoduler.hjelpefunksjoner import (
    _legg_til_kolonne,
    forutsetninger_soa,
)
from fram.generelle_hjelpemoduler.hjelpefunksjoner import interpoler_linear_vekstfaktor
from fram.generelle_hjelpemoduler.konstanter import (
    VIRKNINGSNAVN,
    VERDSATT_COLS,
    SKATTEFINANSIERINGSKOSTNAD,
    KOLONNENAVN_VOLUMVIRKNING,
    KOLONNENAVN_VOLUM_MAALEENHET,
    FOLSOMHET_COLS,
    FOLSOMHET_KOLONNE,
)
from fram.generelle_hjelpemoduler.schemas import VerdsattSchema
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.risiko.schemas import (
    HendelseSchema,
    KonsekvensSchema,
    SarbarhetSchema,
    KalkprisMaterielleSchema,
    KonsekvensmatriseSchema,
    KalkprisHelseSchema,
    KalkprisOljeutslippSchema,
    KalkprisOljeopprenskingSchema, KonsekvensinputSchema,
)

VIRKNINGSNAVN_REP = "Ulykker - endring i reparasjonskostnader"
VIRKNINGSNAVN_TUD = "Ulykker - endring i tid ute av drift"
VIRKNINGSNAVN_HELSE_DOD = "Ulykker - endring i dødsfall"
VIRKNINGSNAVN_HELSE_SKADE = "Ulykker - endring i personskader"
AGG_COLS_KONSEKVENS = FOLSOMHET_COLS + [
    "Risikoanalyse",
    "Hendelsestype",
    KOLONNENAVN_VOLUMVIRKNING,
    KOLONNENAVN_VOLUM_MAALEENHET,
]
SKIP_LENGDE_HENDELSE_AAR = ["Skipstype", "Lengdegruppe", "Hendelsestype", "Aar"]
SKIP_LENGDE_HENDELSE = ["Skipstype", "Lengdegruppe", "Hendelsestype"]
SKIP_LENGDE_KONSEKVENS_HENDELSE = ["Skipstype", "Lengdegruppe", "Konsekvens", "Hendelsestype"]

ARKNAVN_KONSEKVENSER_UTSLIPP = "forutsetninger:::konsekvenser_utslipp"


@verbose_schema_error
@pa.check_types(lazy=True)
def hent_ut_konsekvensinput(excel_filbane: Optional[Union[Path, str]] = None) -> DataFrame[KonsekvensinputSchema]:
    """
    Leser inn sannsynlighet for skade og dødsfall og betinget antall skadde og døde per hendelse fra fellesboken "Forutsetninger_FRAM.xlsx"

    Dersom argumentet `excel_filbane` angis, lagres filen dit for lettere gjenbruk i egne analyser.

    Returns:
        pandas DataFrame med forventningsverdier per skipstype, lengdegruppe, hendelsestype, der hver kolonne er år
    """
    grunnaar = 2018
    sheet_names = {
        "Dodsfall": "konsekvenser_død",
        "Personskade": "konsekvenser_personska",
    }
    rad_offset = {
        "Grunnstøting": 82,
        "Kontaktskade": 105,
        "Striking": 59,
        "Struck": 59,
    }
    antall_rader_innlesing = 16
    kolonner_innlesing = 'M:U'

    dfs = []
    sannsynligheter = []
    for konsekvensnavn in ["Dodsfall", "Personskade"]:
        sheet_name = sheet_names[konsekvensnavn]

        sannsynligheter.append(
            pd.read_excel(forutsetninger_soa(),
                          sheet_name=sheet_name,
                          usecols="A:F",
                          skiprows=5,
                          nrows=3)
                .iloc[:, [0, 4]]
                .pipe(angi_kolonnenavn, ["Hendelsestype", f"Sannsynlighet {konsekvensnavn}"])
                .assign(Hendelsestype=lambda df: df.Hendelsestype.map(
                {"Kollisjoner": "Struck", "Grunnstøtinger": "Grunnstøting", "Kontaktskader": "Kontaktskade"}))
                .set_index("Hendelsestype")
        )

        for navn, skiprows in rad_offset.items():
            ant_konsekvenser = (
                pd.read_excel(
                    forutsetninger_soa(),
                    sheet_name=sheet_name,
                    usecols=kolonner_innlesing,
                    skiprows=skiprows,
                    nrows=antall_rader_innlesing
                )
                    .pipe(vask_kolonnenavn_for_exceltull)
                    .assign(
                    Hendelsestype=navn,
                    Konsekvensnavn=konsekvensnavn,
                    Aar=grunnaar)
                    .rename(columns={"Skipstype Kystverket": "Skipstype"})
            )
            dfs.append(ant_konsekvenser)
    sannsynligheter = pd.concat(sannsynligheter, axis=1)
    df = (
        pd.melt(
            pd.concat(dfs),
            id_vars=["Skipstype", "Hendelsestype", "Aar", "Konsekvensnavn"],
            var_name="Lengdegruppe",
            value_name="Konsekvens",
        )
            .pipe(_sett_til_null_hvis_striking)
            .set_index(["Skipstype", "Lengdegruppe", "Hendelsestype", "Aar", "Konsekvensnavn"])
            .unstack()
            .pipe(_dropp_overste_kolonnenavnnivaa)
            .reset_index()
            .rename(
            columns={"Dodsfall": "Antall dodsfall hvis dodsfall", "Personskade": "Antall personskade hvis personskade"})
            .merge(right=sannsynligheter, left_on="Hendelsestype", right_index=True, how='left')
            .fillna({"Sannsynlighet Dodsfall": 0, "Sannsynlighet Personskade": 0})
            .sort_values(by=["Skipstype", "Lengdegruppe", "Hendelsestype", "Aar"])
    )
    if excel_filbane:
        print(f"Lagrer innlest konsekvensinput til {excel_filbane}.")
        df.to_excel(excel_filbane, index=False)
    return df

def interpoler_og_fremskriv_konsekvenser(konsekvensinput: DataFrame, beregningsaar: List[int]):
    """
    - Hvis bare ett år i grunnlaget, returneres konstant verdi for alle beregningsaar
    - Ellers er regelen lineær interpolering mellom de angitte årene, og konstant fremskriving frem til første angitte år og etter siste angitte år

    """
    beregningsaar = sorted(beregningsaar)
    aar_i_input = sorted(list(konsekvensinput.Aar.unique()))
    AGGKOLONNER = [col for col in FOLSOMHET_COLS if col in konsekvensinput.columns]
    if len(aar_i_input) == 1:
        # Bare ett år, vi repeterer bare input for alle år
        output = pd.concat([konsekvensinput.copy().assign(Aar=aar) for aar in beregningsaar])
        assert len(output) == len(beregningsaar) * len(
            konsekvensinput.loc[lambda df: df.Aar == list(df.Aar.unique())[0]])
        _idx = list(set(AGGKOLONNER + SKIP_LENGDE_HENDELSE_AAR))
        output = (pd.melt(
            output,
            id_vars= _idx,
            value_vars=["Dodsfall", "Personskade"],
            var_name="Konsekvens",
            value_name="antall"
        )
                  .set_index(SKIP_LENGDE_KONSEKVENS_HENDELSE + ["Aar"])
                  .unstack()
                  .pipe(_dropp_overste_kolonnenavnnivaa)
                  )
    else:
        # Roter data slik at vi enkelt kan gjenbruke samme kodesnutten som sist
        stacket = konsekvensinput.set_index(list(OrderedDict.fromkeys(AGGKOLONNER + SKIP_LENGDE_HENDELSE_AAR)))
        sluttindekser = list(OrderedDict.fromkeys((AGGKOLONNER + SKIP_LENGDE_HENDELSE)))
        results = {"Dodsfall": [], "Personskade": []}
        for konsekvensnavn in results.keys():
            utg_punkt = stacket[konsekvensnavn].unstack(-1)
            for aar_par in zip(aar_i_input[:-1], aar_i_input[1:]):
                interpolert = (interpoler_linear_vekstfaktor(
                    grunnaar=aar_par[0],
                    verdi_grunnaar=utg_punkt[aar_par[0]].values,
                    sluttaar=aar_par[1],
                    verdi_sluttaar=utg_punkt[aar_par[1]].values
                )
                               .set_index(utg_punkt.index)
                               .reset_index()
                               .set_index(sluttindekser)
                               )
                results[konsekvensnavn].append(interpolert)
            if beregningsaar[-1] > aar_i_input[-1]:  # Skal beregne etter siste år med angitte konsekvenser
                etter_siste_konsekvensaar = utg_punkt[aar_i_input[-1]].copy().to_frame()
                for year in range(aar_i_input[-1]+1, beregningsaar[-1] + 1):
                    results[konsekvensnavn].append(
                        etter_siste_konsekvensaar
                            .rename(columns={aar_i_input[-1]: year})
                            .reset_index()
                            .set_index(sluttindekser)
                    )
            if beregningsaar[0] < aar_i_input[0]:  # Skal beregne før første år med angitte konsekvenser
                foer_foerste_konsekvensaar = utg_punkt[aar_i_input[0]].copy().to_frame()
                for year in range(beregningsaar[0], aar_i_input[0]):
                    results[konsekvensnavn].append(
                        foer_foerste_konsekvensaar
                            .rename(columns={aar_i_input[0]: year})
                            .reset_index()
                            .set_index(sluttindekser)
                    )

        for key, value in results.items():
            results[key] = pd.concat(value, axis=1).sort_index(axis=1).assign(Konsekvens=key)
        output = pd.concat(results.values(), axis=0).reset_index().set_index(list(OrderedDict.fromkeys(AGGKOLONNER + SKIP_LENGDE_KONSEKVENS_HENDELSE)))
    return output


@pa.check_types
def lag_konsekvensmatrise(konsekvensinput: DataFrame[KonsekvensinputSchema], beregningsaar: List[int]) -> DataFrame[
    KonsekvensmatriseSchema]:
    """ Omsetter en gyldig konsekvensinput og en liste med beregningsår i en gyldig konsekvensmatrise for alle år

    Konsekvensmatrisen må ha input Skipstype, Lengdegruppe, Hendelsestype, Aar, Antall dodsfall hvis dodsfall,
    Antall personskade hvis personskade, Sannsynlighet Dodsfall og Sannsynlighet Personskade. I tillegg kan den ha flere
    kolonner som identifiserer rute, analyseomraade, tiltakspakke etc. Nivåer som ikke er angitt her, vil få samme verdi
    anvendt på alle. Man kan for eksempel legge til Analyseomraade og angi to ulike, da vil alle ruter i hvert
    analyseområde behandles likt.


    Regelen for oversetting er som følger
    - Hvis bare ett år i grunnlaget, returneres konstant verdi for alle beregningsaar
    - Ellers er regelen lineær interpolering mellom de angitte årene, og konstant fremskriving frem til første angitte år og etter siste angitte år

    """
    return (
        konsekvensinput.copy()
            .assign(Dodsfall=lambda df: df["Sannsynlighet Dodsfall"] * df["Antall dodsfall hvis dodsfall"],
                    Personskade=lambda df: df["Sannsynlighet Personskade"] * df["Antall personskade hvis personskade"],
                    )
        [list(set([col for col in FOLSOMHET_COLS + SKIP_LENGDE_HENDELSE_AAR if col in konsekvensinput.columns] + ["Dodsfall", "Personskade"]))]
            .pipe(interpoler_og_fremskriv_konsekvenser, beregningsaar=beregningsaar)
    )



@verbose_schema_error
@pa.check_types(lazy=True)
def les_inn_konsekvensmatrise(
    navn: str, beregningsaar: List[int]
) -> DataFrame[KonsekvensmatriseSchema]:
    """
    Leser inn forventet antall døde eller skadde per hendelse fra fellesboken "Forutsetninger_FRAM.xlsx"

    Args:
        navn: Streng, "Dodsfall" eller "Personskade"
        beregningsaar: Liste med år det skal returneres konsekvenser for

    Returns:
        pandas DataFrame med forventningsverdier per skipstype, lengdegruppe, hendelsestype, der hver kolonne er år
    """
    godkjente_navn = ["Dodsfall", "Personskade"]
    if navn not in godkjente_navn:
        raise KeyError(
            f"'les_inn_konsekvensmatrise' fikk et ukjent konsekvensnavn {navn}. Må være blant {godkjente_navn}"
        )

    sheet_name = {
        "Dodsfall": "konsekvenser_død",
        "Personskade": "konsekvenser_personska",
    }[navn]
    konsekvenser = {
        "Grunnstøting": [82, 147],
        "Kontaktskade": [105, 170],
        "Striking": [59, 126],
        "Struck": [59, 126],
    }

    dfs = []
    for navn in konsekvenser.keys():
        for offset in konsekvenser[navn]:
            df = _les_konsekvensmatrise(offset, sheet_name=sheet_name).assign(
                Hendelsestype=navn
            )
            dfs.append(df)
    df = (
        pd.melt(
            pd.concat(dfs).rename(columns={"Skipstype Kystverket": "Skipstype"}),
            id_vars=["Skipstype", "Hendelsestype", "Aar"],
            var_name="Lengdegruppe",
            value_name="Konsekvens",
        )
        .pipe(_sett_til_null_hvis_striking)
        .set_index(["Skipstype", "Lengdegruppe", "Hendelsestype", "Aar"])
        .unstack()
        .pipe(_dropp_overste_kolonnenavnnivaa)
    )
    grunnaar_konsekvens, fremtidsaar_konsekvens = tuple(df.columns.to_list())
    interpolert = interpoler_linear_vekstfaktor(
        grunnaar=grunnaar_konsekvens,
        verdi_grunnaar=df[grunnaar_konsekvens].values,
        sluttaar=fremtidsaar_konsekvens,
        verdi_sluttaar=df[fremtidsaar_konsekvens].values,
    ).set_index(df.index)
    if beregningsaar[-1] > fremtidsaar_konsekvens:
        for year in range(2050, beregningsaar[-1] + 1):
            interpolert[year] = interpolert[2050]

    if beregningsaar[0] < grunnaar_konsekvens:
        raise KeyError(
            f"Første år med konsekvensmatrise er {grunnaar_konsekvens}. Du har bedt om å få beregnet konsekvenser for årene {beregningsaar}"
        )
    return interpolert[beregningsaar]


@verbose_schema_error
@pa.check_types(lazy=True)
def _forventet_ant_konsekvenser(
    hendelser: DataFrame[HendelseSchema], konsekvensmatrise: DataFrame[KonsekvensmatriseSchema], beregningsaar: List[int]
) -> DataFrame[KonsekvensSchema]:
    """Multipliserer ut hendelser med innlest konsekvensmatrise for å komme frem til samlede årlige konsekvenser

    Args:
        hendelser: Gyldig definert dataframe med hendelser, slik som `self.hendelser_ref`
        beregningsaar: Liste over de årene du vil ha beregnet virkningen for
        konsekvensmatrise: Gyldig definert konsekvensmatrise, med forventet antall skadde og døde per hendelse
    """
    merge_cols = [col for col in FOLSOMHET_COLS if col in konsekvensmatrise.index.names] + ["Hendelsestype"]
    konsekvenser = hendelser.reset_index().merge(
        right=konsekvensmatrise.rename(columns=lambda x: f"h_{x}").reset_index(),
        on=merge_cols,
        how='inner'
    )
    for year in beregningsaar:
        konsekvenser[year] = konsekvenser[year] * konsekvenser[f"h_{year}"]
    konsekvenser = (
        konsekvenser
        .rename(columns={"Konsekvens": KOLONNENAVN_VOLUMVIRKNING})
        .pipe(_legg_til_kolonne, KOLONNENAVN_VOLUM_MAALEENHET, "Antall")
        .groupby(AGG_COLS_KONSEKVENS)[beregningsaar]
        .sum()
    )
    return konsekvenser


@verbose_schema_error
@pa.check_types(lazy=True)
def verdsett_materielle_skader(
    hendelser_ref: DataFrame[HendelseSchema],
    kroner_hendelser: DataFrame[KalkprisMaterielleSchema],
    beregningsaar: List[int],
    hendelser_tiltak: Optional[DataFrame[HendelseSchema]] = None,
):
    """
    Verdsetter materielle skader i referanse, tiltak og netto, basert på angitte hendelser og kalkulasjonspriser

    Funksjonen kobler først sammen hendelser og kalkpriser for tid
    ute av drift på riktig skipstype, lengdegruppe og hendelsestype, og deretter ganges
    dette sammen. Det samme gjelder reparasjonskostnader. Tilslutt settes både
    tid ute av drift og reparasjonskostnader sammen i samme dataframe.

    Args:
      - hendelser_ref: Dataframe med antall hendelser i referansebanen. Må følge schema for hendelsesmatrise.
      - hendelser_tiltak: Dataframe med antall hendelser i referansebanen. Må følge schema for hendelsesmatrise.
      - kroner_hendelser: Dataframe med verdsettingsfaktorer for tid ute av drift
        realprisjustert over tid og reparasjonskostnader fordelt etter skipstype, lengdegruppe og hendelsestype.
      - beregningsaar (list): Liste med de år det skal beregnes virkninger for.
    Returns:
        kroner_materielle_ref, kroner_materielle_tiltak, kroner_materielle_diff. Tre DataFrames
        med verdsatte konsekvenser for materielle skader fordelt etter tid ute av drift og
        reparasjonskostnader over tid for hhv referanse, tiltak og netto
    """

    def multipliser_hendelser_kroner(hendelser, kroner_hendelser, beregningsaar):
        """Hjelpefunksjon for å sikre lik multiplikasjon i ref og tiltak"""
        KOLONNER_MERGE = [
            "Skipstype",
            "Lengdegruppe",
            "Hendelsestype",
            FOLSOMHET_KOLONNE,
        ]

        hendelser = hendelser.rename(columns=lambda x: f"h_{x}").reset_index()
        kroner_hendelser = kroner_hendelser.reset_index()
        koblet = hendelser.merge(
            right=kroner_hendelser,
            on=KOLONNER_MERGE,
        )

        tid_u_drift = koblet.copy()
        for year in beregningsaar:
            tid_u_drift[year] = (
                tid_u_drift[f"tid_u_drift_{year}"] * tid_u_drift[f"h_{year}"]
            )
        tid_u_drift = (
            tid_u_drift.groupby(FOLSOMHET_COLS, as_index=False)[beregningsaar].sum()
        ).pipe(_legg_til_kolonne, VIRKNINGSNAVN, VIRKNINGSNAVN_TUD)

        reparasjon = koblet.copy()
        for year in beregningsaar:
            reparasjon[year] = (
                reparasjon["Reparasjonskostnader"] * reparasjon[f"h_{year}"]
            )
        reparasjon = (
            reparasjon.groupby(FOLSOMHET_COLS, as_index=False)[beregningsaar].sum()
        ).pipe(_legg_til_kolonne, VIRKNINGSNAVN, VIRKNINGSNAVN_REP)

        materielle_kostnader = (
            pd.concat([tid_u_drift, reparasjon])
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0)
            .set_index(VERDSATT_COLS)
        )
        return materielle_kostnader

    # Disse skrives disaggregert
    kroner_materielle_ref = multipliser_hendelser_kroner(
        hendelser_ref, kroner_hendelser, beregningsaar
    )
    if hendelser_tiltak is None:
        kroner_materielle_tiltak = None
        kroner_materielle_diff = None
    else:
        kroner_materielle_tiltak = multipliser_hendelser_kroner(
            hendelser_tiltak, kroner_hendelser, beregningsaar
        )

        reduksjon_hendelser = (
            hendelser_ref.subtract(hendelser_tiltak, fill_value=0)
        ).fillna(0)

        # Differansen aggregeres til konsekvensene 'Tid ute av drift' og 'Reparasjonskostnader'
        kroner_materielle_diff = multipliser_hendelser_kroner(
            reduksjon_hendelser, kroner_hendelser, beregningsaar
        )

    return kroner_materielle_ref, kroner_materielle_tiltak, kroner_materielle_diff


@verbose_schema_error
@pa.check_types(lazy=True)
def verdsett_helse(
    konsekvenser_ref: DataFrame[KonsekvensSchema],
    verdsettingsfaktorer: DataFrame[KalkprisHelseSchema],
    beregningsaar: List[int],
    konsekvenser_tiltak: Optional[DataFrame[KonsekvensSchema]] = None,
) -> Tuple[DataFrame[VerdsattSchema], Optional[DataFrame[VerdsattSchema]]]:
    """
    Verdsetter reduksjonen i personskader, altså produktet av reduksjonen i skader og verdsettingen av hver skade

    Args:
        konsekvenser_ref: Gyldig konsekvens-dataframe med forventede konsekvenser hvert år
        verdsettingsfaktorer: Gyldige verdsettingsfaktorer for helse
        beregningsaar: Liste over de år du vil ha beregnet virkningen for
        konsekvenser_tiltak: Gyldig konsekvens-dataframe med forventede konsekvenser hvert år

    Returns:
        DataFrame: Tuple med brutto kostnader som følge av personskader i hhv ref og tiltak. Gyldige verdsatt-dataframes
    """
    verdsettingsfaktorer = verdsettingsfaktorer.rename(columns=lambda x: f"p_{x}")

    def kroner_risiko(konsekvenser, verdsettingsfaktorer):
        """
        Hjelpefunksjon for å multiplisere sammen konsekvenser og verdsettingsfaktorer
        """
        kroner_konsekvens = (
            konsekvenser.rename(columns=lambda x: f"k_{x}")
            .reset_index()
            .merge(
                right=verdsettingsfaktorer.reset_index(),
                left_on=KOLONNENAVN_VOLUMVIRKNING,
                right_on="Konsekvens",
            )
        )
        # Summerer hvert år og collapser per konsekvens (dødsfall, personskade)
        for year in beregningsaar:
            kroner_konsekvens[year] = (
                kroner_konsekvens[f"k_{year}"] * kroner_konsekvens[f"p_{year}"]
            )
        virkningsnavn = (
            kroner_konsekvens["Konsekvens"]
            .map(
                {
                    "Dodsfall": VIRKNINGSNAVN_HELSE_DOD,
                    "Personskade": VIRKNINGSNAVN_HELSE_SKADE,
                }
            )
            .values
        )
        kroner_konsekvens = (
            kroner_konsekvens.pipe(_legg_til_kolonne, VIRKNINGSNAVN, virkningsnavn)
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0)
            .groupby(VERDSATT_COLS)[beregningsaar]
            .sum()
        )

        return kroner_konsekvens

    kroner_helse_ref = kroner_risiko(konsekvenser_ref, verdsettingsfaktorer)
    if konsekvenser_tiltak is None:
        kroner_helse_tiltak = None
    else:
        kroner_helse_tiltak = kroner_risiko(konsekvenser_tiltak, verdsettingsfaktorer)

    return kroner_helse_ref, kroner_helse_tiltak


@verbose_schema_error
@pa.check_types(lazy=True)
def verdsett_oljeutslipp(
    hendelser_ref: DataFrame[HendelseSchema],
    kalkulasjonspriser_ref: DataFrame[KalkprisOljeutslippSchema],
    sarbarhet: DataFrame[SarbarhetSchema],
    beregningsaar: List[int],
    hendelser_tiltak: Optional[DataFrame[HendelseSchema]] = None,
    kalkulasjonspriser_tiltak: Optional[DataFrame[KalkprisOljeutslippSchema]] = None,
) -> Tuple[DataFrame[VerdsattSchema], Optional[DataFrame[VerdsattSchema]], Any]:
    """
    Verdsetter oljeutslipp basert på angitt antall hendelser i ref (og evt tiltak), angitte kalkulasjonspriser og
    angitt såbarhet for de berørte områdene

    Kalkprisen varierer over tid som følge av fremskrivningene av sannsynlighet for utslipp og utslippsmengde og
    realprisjustering. Kobler sammen utslippskostnader per hendelse med reduksjon i antall hendelser, og multipliserer.

    Args:
        - hendelser_ref: Gyldig hendelsesdataframe over levetiden beregningsårene fordelt på Skipstype, lengdegruppe,
          hendelsestype og risikoanalyse. Påkrevd
        - kalkulasjonspriser: Gydlig dataframe med kalkulasjonspriser for utslipp, kroner
          per hendelser over tid fordelt etter skipstype, lengdegruppe og hendelsestype. Påkrevd.
        - sarbarhet: Gydlig sårbarhetsdataframe som inneholder informasjon om sårbarhetsnivå og fylke per analyseområde,
          tiltakspakke, tiltaksområde, strekning. Påkrevd.
        - beregningsaar: Liste over de år du vil ha beregnet virkningen for.
        - hendelser_tiltak: Gyldig hendelsesdataframe over levetiden beregningsårene fordelt på Skipstype, lengdegruppe,
          hendelsestype og risikoanalyse. Valgfri, men påkrevd hvis du vil ha beregnet netto verdi

    Returns:
        dataframe med verdsatte hendelsesreduksjoner for oljeutslippsskostnader over tid.
    """

    def multipliser_hendelser_kroner(hendelser, kroner_utslipp):
        # Forhåndslagrer koblekolonnene mellom hendelser og kroner_utslipp
        koblekolonner = [
                    "Saarbarhet",
                    "Fylke",
                    "Skipstype",
                    "Lengdegruppe",
                    "Hendelsestype",
                ]
        # Dersom det er angitt 'Analyseomraade' i kroner_utslipp, som betyr at det er analyseomraade-spesifikke
        # konsekvensmatriser for utslipp, kobler vi også på denne
        if "Analyseomraade" in kroner_utslipp.columns:
            koblekolonner += ["Analyseomraade"]
        hendelser = hendelser.reset_index().merge(sarbarhet, how="left")

        relevante_verdsettingsfaktorer = hendelser.rename(
            columns={"Sarbarhet": "Saarbarhet"}
        ).merge(
            kroner_utslipp[koblekolonner + beregningsaar],
            how="left",
            on=koblekolonner,
        )

        utvalgte_verdsettingsfaktorer = relevante_verdsettingsfaktorer[
            koblekolonner
            + [str(aar) + "_y" for aar in beregningsaar]
        ]

        for aar in beregningsaar:
            relevante_verdsettingsfaktorer[aar] = (
                relevante_verdsettingsfaktorer[str(aar) + "_x"]
                * relevante_verdsettingsfaktorer[str(aar) + "_y"]
            )

        relevante_verdsettingsfaktorer = (
            relevante_verdsettingsfaktorer.pipe(
                _legg_til_kolonne,
                VIRKNINGSNAVN,
                "Ulykker - endring i forventet velferdstap ved oljeutslipp",
            )
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0)
            .groupby(VERDSATT_COLS)[beregningsaar]
            .sum()
        )
        return relevante_verdsettingsfaktorer, utvalgte_verdsettingsfaktorer

    # Disse er disaggregert
    (
        kroner_oljeutslipp_ref,
        utvalgte_verdsettingsfaktorer,
    ) = multipliser_hendelser_kroner(hendelser_ref, kalkulasjonspriser_ref)
    if hendelser_tiltak is None:
        kroner_oljeutslipp_tiltak = None
    else:
        (
            kroner_oljeutslipp_tiltak,
            _,
        ) = multipliser_hendelser_kroner(hendelser_tiltak, kalkulasjonspriser_tiltak)

    return (
        kroner_oljeutslipp_ref,
        kroner_oljeutslipp_tiltak,
        utvalgte_verdsettingsfaktorer,
    )


@verbose_schema_error
@pa.check_types(lazy=True)
def verdsett_opprenskingskostnader(
    hendelser_ref: DataFrame[HendelseSchema],
    kalkulasjonspriser_ref: DataFrame[KalkprisOljeopprenskingSchema],
    beregningsaar: List[int],
    hendelser_tiltak: Optional[DataFrame[HendelseSchema]] = None,
    kalkulasjonspriser_tiltak: Optional[DataFrame[KalkprisOljeopprenskingSchema]] = None,
) -> Tuple[DataFrame[VerdsattSchema], Optional[DataFrame[VerdsattSchema]], Any]:
    """
    Verdsetter opprenskingskostnader etter oljeutslipp basert på angitt antall hendelser i ref (og evt tiltak) og
    angitte kalkulasjonspriser

    Kalkprisen varierer over tid som følge av fremskrivningene av sannsynlighet for utslipp og utslippsmengder.
    Kobler sammen opprenskingskostnader per hendelse med reduksjon i antall hendelser, og multipliserer.

    Args:
        - hendelser_ref: Gyldig hendelsesdataframe over levetiden beregningsårene fordelt på Skipstype, lengdegruppe,
          hendelsestype og risikoanalyse. Påkrevd
        - kalkulasjonspriser: Gydlig dataframe med kalkulasjonspriser for opprensking, kroner
          per hendelser over tid fordelt etter skipstype, lengdegruppe og hendelsestype. Påkrevd.
        - beregningsaar: Liste over de år du vil ha beregnet virkningen for.
        - hendelser_tiltak: Gyldig hendelsesdataframe over levetiden beregningsårene fordelt på Skipstype, lengdegruppe,
          hendelsestype og risikoanalyse. Valgfri, men påkrevd hvis du vil ha beregnet netto verdi

    Returns:
        dataframe med verdsatte hendelsesreduksjoner for oljeopprenskingskostnader over tid.
    """

    def multipliser_hendelser_kroner(hendelser, kalkulasjonspriser):
        """Hjelpefunksjon for å sikre at vi multipliserer likt i ref og tiltak"""
        koblekolonner = ["Skipstype", "Lengdegruppe", "Hendelsestype"]
        # Dersom det er angitt 'Analyseomraade' i kalkulasjonspriser, som betyr at det er analyseomraade-spesifikke
        # konsekvensmatriser for utslipp, kobler vi også på denne
        if "Analyseomraade" in kalkulasjonspriser.columns:
            koblekolonner += ["Analyseomraade"]

        hendelser = hendelser.reset_index()

        kroner_utslipp = kalkulasjonspriser.set_index(
            koblekolonner
        )[beregningsaar].reset_index()
        kostnader = hendelser.merge(
            kroner_utslipp,
            how="left",
            on=koblekolonner,
        )

        utvalgt_verdsett_opprensking = (
            kostnader[
                koblekolonner
                + [str(aar) + "_y" for aar in beregningsaar]
            ]
            .groupby(koblekolonner)
            .mean()
        )

        for aar in beregningsaar:
            kostnader[aar] = kostnader[str(aar) + "_x"] * kostnader[str(aar) + "_y"]

        kostnader = (
            kostnader.pipe(
                _legg_til_kolonne,
                VIRKNINGSNAVN,
                "Ulykker - endring i forventet opprenskingskostnad ved oljeutslipp",
            )
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0)
            .groupby(VERDSATT_COLS)[beregningsaar]
            .sum()
        )
        return kostnader, utvalgt_verdsett_opprensking

    kroner_opprensking_ref, utvalgt_verdsett_opprensking = multipliser_hendelser_kroner(
        hendelser_ref, kalkulasjonspriser_ref
    )
    if hendelser_tiltak is None:
        kroner_opprensking_tiltak = None
    else:
        (
            kroner_opprensking_tiltak,
            utvalgt_verdsett_opprensking,
        ) = multipliser_hendelser_kroner(hendelser_tiltak, kalkulasjonspriser_tiltak)

    return (
        kroner_opprensking_ref,
        kroner_opprensking_tiltak,
        utvalgt_verdsett_opprensking,
    )


def _les_konsekvensmatrise(skiprows: int, sheet_name: str) -> pd.DataFrame:
    """Leser inn konsekvensmatrisen"""
    df = pd.read_excel(
        forutsetninger_soa(),
        sheet_name=sheet_name,
        usecols=list(range(10)),
        skiprows=skiprows,
        nrows=16,
    )
    return df


def _sett_til_null_hvis_striking(df: pd.DataFrame) -> pd.DataFrame:
    """Setter konsekvensen til null hvis hendelsestypen er 'Striking' """
    df.loc[df.Hendelsestype == "Striking", "Konsekvens"] = 0
    return df


def _dropp_overste_kolonnenavnnivaa(df: pd.DataFrame) -> pd.DataFrame:
    """Dropper det øverste kolonnenivået i en dataframe

    Args:
        df: En dataframe med hierarkiske kolonner du vil droppe det øverste kolonnenivået fra
    """
    df.columns = df.columns.droplevel()
    return df


def _erstatt_lengdegrupper(df: pd.DataFrame) -> pd.DataFrame:
    """Hjelpefunksjon som sjekker om IWRAP-inputen inkluderer lengdegruppene 300-350 og 350-,
    og erstatter dem med 300- hvis nødvendig
    """
    if "300-350" in df.columns:
        df["300-"] = df["300-350"] + df["350-"]

    return df


@verbose_schema_error
@pa.check_types(lazy=True)
def _beregn_helsekonsekvenser(
    hendelser_ref: DataFrame[HendelseSchema],
    konsekvensmatrise_ref: DataFrame[KonsekvensmatriseSchema],
    beregningsaar: List[int],
    hendelser_tiltak: Optional[DataFrame[HendelseSchema]] = None,
    konsekvensmatrise_tiltak: Optional[DataFrame[KonsekvensmatriseSchema]] = None,
) -> Tuple[
    DataFrame[KonsekvensSchema],
    DataFrame[KonsekvensSchema],
    DataFrame[KonsekvensSchema],
]:
    """
    Basert på konsekvensmatrisen, regner den ut totalt antall skadde og døde per rute per år

    Args:
        hendelser_ref: Hendelser i referansebanen på samme format som self.hendelser_ref
        hendelser_tiltak: Hendelser i referansebanen på samme format som self.hendelser_tiltak
        beregningsaar: En liste over de årene du vil beregne virknignen over

    Returns:
        Returnerer tre dataframes med beregnede helsekonsekvenser i hhv ref, tiltak og netto
    """
    konsekvenser_ref = _forventet_ant_konsekvenser(hendelser=hendelser_ref, konsekvensmatrise=konsekvensmatrise_ref, beregningsaar=beregningsaar)
    if hendelser_tiltak is None:
        konsekvenser_tiltak = None
        konsekvensendring = None
    else:
        # HendelseSchema.validate(hendelser_tiltak)
        konsekvenser_tiltak = _forventet_ant_konsekvenser(hendelser=hendelser_tiltak, konsekvensmatrise=konsekvensmatrise_tiltak, beregningsaar=beregningsaar)

        konsekvensendring = (
            konsekvenser_tiltak.subtract(konsekvenser_ref, fill_value=0)
        ).fillna(0)

    return konsekvenser_ref, konsekvenser_tiltak, konsekvensendring


def les_inn_hvilke_ra_som_brukes_fra_fram_input(
    filbane: Union[Path, pd.ExcelFile], tiltakspakke: int, arknavn: str = "Risikoanalyser referansebanen"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    try:
        ra_ref = (
            pd.read_excel(filbane, sheet_name=arknavn)
            .set_index(
                [
                    "Strekning",
                    "Tiltaksomraade",
                    "Tiltakspakke",
                    "Analyseomraade",
                    "Rute",
                ]
            )
            .stack()
            .reset_index()
            .rename(columns={0: "Risikoanalyse", "level_5": "aar"})
            .assign(
                ra_aar=lambda df: df.aar.str.split(expand=True)
                .iloc[:, -1]
                .astype(int)
            )
            .drop("aar", axis=1)
        )
        ra_ref = ra_ref.loc[ra_ref.Tiltakspakke == tiltakspakke].copy()

        # Leser inn tiltaks-RAene og fyller manglende informasjon om trafikkgrunnlaget med 'referanse'
        ra_t = (
            pd.read_excel(
                filbane,
                sheet_name=f"Tiltakspakke {tiltakspakke}",
                skiprows=1,
                usecols=[21, 22, 23],
                names=["Risiko ref", "Risiko tiltak", "RA_trafikkgrunnlag"],
            )
            .dropna(subset=["Risiko ref", "Risiko tiltak"])
            .assign(
                RA_trafikkgrunnlag=lambda df: df.RA_trafikkgrunnlag.fillna(
                    "Referanse"
                ).str.lower()
            )
        )

        ra_endring = dict(zip(ra_t["Risiko ref"], ra_t["Risiko tiltak"]))
        ra_tiltak = (
            ra_ref.copy()
            .assign(Risikoanalyse=lambda x: x.Risikoanalyse.map(ra_endring))
            .merge(
                right=ra_t[["Risiko tiltak", "RA_trafikkgrunnlag"]],
                left_on="Risikoanalyse",
                right_on="Risiko tiltak",
                how="left",
            )
            .drop("Risiko tiltak", axis=1)
            .assign(
                RA_trafikkgrunnlag=lambda df: df.RA_trafikkgrunnlag.fillna(
                    "Referanse"
                )
                .str.lower()
                .str.strip()
            )
        )
    except (
        IndexError,
        XLRDError,
    ) as err:  # Fanger feilmeldingen. Disse viser at RA ikke finnes i Excel-arket. Det er ok, men vi returnerer None
        if err.args[0] in [
            "single positional indexer is out-of-bounds",
            f"No sheet named <'{arknavn}'>",
        ]:
            ra_ref = None
            ra_tiltak = None
        else:
            raise err
    return ra_ref, ra_tiltak

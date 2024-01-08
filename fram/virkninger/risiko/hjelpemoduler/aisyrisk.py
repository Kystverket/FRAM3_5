import numpy as np
import pandas as pd
from pandera.typing import DataFrame
from typing import Callable, List

from fram.generelle_hjelpemoduler.hjelpefunksjoner import (
    forut, _multiply_df_with_col, _divide_df_with_col, _legg_til_kolonne,
)
from fram.generelle_hjelpemoduler.konstanter import FOLSOMHET_COLS, FOLSOMHET_KOLONNE
from fram.generelle_hjelpemoduler.schemas import TrafikkGrunnlagSchema
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.risiko.schemas import AISyRISKKonvertertSchema

STRIKING_COLUMNS = ['Freq_coll_head', 'Freq_coll_over',
                    'Freq_coll_cross']  # Deles på to senere, siden kan strike eller bli struck
STRUCK_COLUMNS = STRIKING_COLUMNS
GRUNNSTØTING_COLUMNS = ['Freq_pg_criticalturn', 'Freq_pg_closetoshore', 'Freq_dg']
KOLONNEOVERSETTERE = {
    "Ship_type_ID": "risk_norwegian_main_vessel_category_id",
    "Ship_types": "risk_norwegian_main_vessel_category_name",
    "Ship_size_ID": "gt_gruppe_id"
}
SKIPSTYPE_OVERSETTER = (
    forut("aisyrisk_skipstypekonvertering")
    .loc[lambda df: df.Vekt.notna()]
    .reset_index(drop=True)
)
SKIPSLENGDE_OVERSETTER = (
    forut("aisyrisk_lengdekonvertering", 4)
    .loc[lambda df: df.Vekt.notna()]
    .reset_index(drop=True)
)

def konverter_aisyrisk_lengdegrupper(aisy_ra, kast_ut_andre_skipstyper=True, kast_ut_mangler_lengde=True, returner_alle_kolonner=False) -> DataFrame[AISyRISKKonvertertSchema]:
    """
    Leser inn aisyrisk-output, og kobler så denne med skipstypekonverterer, og konverterer deretter vekt-og lengdegrupper.
    Returnerer aisyrisk-RAen på et format med Kystverket skipstyper og lengdegrupper

    Summerer deretter striking, struck, kontaktskade og grunnstøting basert på kolonnene angitt.

    Args:
        aisy_ra: Risikoanalyse slik den foreligger fra AISyRISK i csv-format
        kast_ut_andre_skipstyper: Hvorvidt skipstypen 'Annet' skal kastes ut. Default True
        kast_ut_mangler_lengde: Hvorvidt lengdegruppen 'Mangler' skal kastes ut. Default True
        returner_alle_kolonner: Hvorvidt alle kolonner i AISyRISK-kjøringen skal returneres, eller kun de som FRAM bruker videre. Default False, altså returneres kun de FRAM behøver

    Returns:

    """
    mergecol_skipstype = "Ship_type_ID" if "Ship_type_ID" in aisy_ra.columns else "Ship_types"
    if "Ship_sizes" in aisy_ra.columns:
        aisy_ra = aisy_ra.assign(Ship_size_ID = lambda df: df.Ship_sizes.str.split(".", expand=True)[0].astype(int))
    aisy_ra_grouped = (
        aisy_ra
        .astype({"Sailed_time_hours": float})
        .groupby([mergecol_skipstype, 'Ship_size_ID', "Analyseomraade"]).sum().reset_index()  # Grupperer over alle typer drivstoff. Dette er OK siden absolutte risikotall
        .assign(striking = lambda df: df[STRIKING_COLUMNS].sum(axis=1) / 2,  # Deles på to siden man kan både strike og bli struck
                struck = lambda df: df[STRUCK_COLUMNS].sum(axis=1) / 2,  # Deles på to siden man kan både strike og bli struck
                kontaktskade = 0,
                grunnstøting = lambda df: df[GRUNNSTØTING_COLUMNS].sum(axis=1)
                )

    )


    aisy_ra_grouped_merged = (
        aisy_ra_grouped
            .merge(
                SKIPSTYPE_OVERSETTER[[KOLONNEOVERSETTERE[mergecol_skipstype], 'Skipstype', 'Vekt']],
                left_on=mergecol_skipstype,
                right_on=KOLONNEOVERSETTERE[mergecol_skipstype],
                how="inner"
        )
        .drop([KOLONNEOVERSETTERE[mergecol_skipstype], mergecol_skipstype], axis=1)
        .fillna({"Vekt": 1})
        .set_index(['Skipstype', "Ship_size_ID", "Analyseomraade"])
        .pipe(_multiply_df_with_col, "Vekt")
        .reset_index()
        .drop(["Vekt"], axis=1)
        .merge(
            SKIPSLENGDE_OVERSETTER[[KOLONNEOVERSETTERE["Ship_size_ID"], 'Lengdegruppe', 'Vekt']],
            left_on="Ship_size_ID",
            right_on=KOLONNEOVERSETTERE["Ship_size_ID"],
            how="inner"
        )
        .drop(KOLONNEOVERSETTERE["Ship_size_ID"], axis=1)
        .fillna({"Vekt": 1})
        .set_index(["Skipstype", "Lengdegruppe", "Analyseomraade"])
        .pipe(_multiply_df_with_col, "Vekt")
        .drop(["Vekt"], axis=1)
        .reset_index()
        .groupby(["Skipstype", "Lengdegruppe", "Analyseomraade"], as_index=False).sum()
    )
    if not returner_alle_kolonner:
        aisy_ra_grouped_merged = aisy_ra_grouped_merged[["Skipstype", "Lengdegruppe", "Analyseomraade", "striking", "struck", "kontaktskade", "grunnstøting"]]
        AISyRISKKonvertertSchema.validate(aisy_ra_grouped_merged)

    if kast_ut_andre_skipstyper:
        aisy_ra_grouped_merged = aisy_ra_grouped_merged.query("Skipstype != 'Annet'")
    if kast_ut_mangler_lengde:
        aisy_ra_grouped_merged = aisy_ra_grouped_merged.query("Lengdegruppe != 'Mangler lengde'")

    return aisy_ra_grouped_merged


@verbose_schema_error
def fordel_og_fremskriv_ra(aisy_ra_konvertert: DataFrame[AISyRISKKonvertertSchema],
                           trafikk: DataFrame[TrafikkGrunnlagSchema],
                           risikoanalyseaar: int,
                           beregningsaar: List[int],
                           spre_hendelser_fra_skip_uten_trafikk: bool = True,
                           strekning: str = "strekning test",
                           tiltaksomraade: str = "test",
                           tiltakspakke: int = 1,
                           analyseomraade: str = "1_1",
                           rute: str = 'A',
                           risikoanalysenavn: str = "Midlertidig placeholder",
                           risiko_logger: Callable = print,
                           tiltak_eller_ref=''
                           ):
    """
    Tar input en aiysrisk konvertert til Kystverkets skips- og lengdegrupper.
    Reshaper denne til long-format, og fremskriver deretter risikoen for hver type lineært med trafikkveksten for hver skips/lengdegruppe innad i dette analyseomraadet.

    Fordi det kun foreligger én kjøring av AISyRISK, har vi ikke data til å finne parametre for andre funksjonsformer enn en lineær sammenheng mellom trafikk og hendelser.
    Fremskrivingen av hendelsene foregår derfor lineært med trafikken.

    Ved default kjøring vil funksjonen spre alle hendelser utover skipene med trafikk. De hendelsene der det ikke er skipstyper og lengdegrupper med trafikk, vil spres
    utover øvrige skipstyper og lengdegrupper proporsjonalt med deres trafikk. Dette styres av flagget `spre_hendelser_fra_skip_uten_trafikk`.

    Args:
        aisy_ra_konvertert: AISyRISk-hendelser ferdig konvertert til IWRAP-typer og -lengder. Lages av :py:.*?:`~`konverter_aisyrisk_lengdegrupper`
        trafikk: Trafikkgrunnlag som følger fastsatt schema
        risikoanalyseaar: Året RA-en er kjørt for (for å koble mot trafikk)
        beregningsaar: Liste med år det skal beregnes virkninger for
        spre_hendelser_fra_skip_uten_trafikk: En bool som angir om hendelsene for skip uten trafikk skal spres proporsjonalt med trafikken på øvrige skip
        strekning:
        tiltaksomraade:
        tiltakspakke:
        analyseomraade:
        rute:
        risikoanalysenavn: Brukes for å identifisere kjøringen i videre analyser
        risiko_logger: Callable hvor informasjon fra virkninger logges til
        tiltak_eller_ref: Streng som angir om det er tiltak eller referansebane. Brukes til mer informativ logging

    Returns:

    """
    analyseomraade = str(analyseomraade)
    relevant_ra = (
        aisy_ra_konvertert
        .reset_index()
        .astype({"Analyseomraade": str})
        .loc[lambda df: df.Analyseomraade == analyseomraade]
        .melt(
            id_vars=["Skipstype", "Lengdegruppe", "Analyseomraade"],
            value_vars=["striking", "struck", "kontaktskade", "grunnstøting"],
            var_name="Hendelsestype",
            value_name=risikoanalyseaar,
        )
        .assign(Hendelsestype = lambda df: df.Hendelsestype.str.title())

    )
    beregningsaar_pluss_ra_aar = beregningsaar if risikoanalyseaar in beregningsaar else beregningsaar + [risikoanalyseaar]
    endringsfaktorer = (
        trafikk
        .groupby(["Skipstype", "Lengdegruppe", "Analyseomraade", FOLSOMHET_KOLONNE])[beregningsaar_pluss_ra_aar].sum()
        .pipe(_divide_df_with_col, risikoanalyseaar)
        .reset_index()
        .astype({"Analyseomraade": str})
        .loc[lambda df: df.Analyseomraade == analyseomraade]
    )

    koblet = (
        relevant_ra # Må gjenta ra én gang for hver analyse for å sikre at det ikke blir kluss med antall rader i koblingen når noen har hendelser uten trafikk
        .pipe(
            _stable_folsomhetsanalyse,
            folsomheter=sorted(endringsfaktorer.Analysenavn.unique()),
            folsomhetsnavn=FOLSOMHET_KOLONNE
        )
        .merge(
            right=endringsfaktorer.drop(risikoanalyseaar, axis=1),
            on=["Skipstype", "Lengdegruppe", "Analyseomraade", FOLSOMHET_KOLONNE],
            how="outer",
            indicator=True
        )
    )
    _sjekk = koblet.groupby(["Hendelsestype", FOLSOMHET_KOLONNE])[risikoanalyseaar].sum().unstack()
    for column in _sjekk:
        pd.testing.assert_series_equal(_sjekk[column], relevant_ra.groupby("Hendelsestype")[risikoanalyseaar].sum(), check_names=False)



    trafikk_uten_hendelser = koblet.loc[lambda df: df._merge == "right_only"][
        ["Skipstype", "Lengdegruppe", "Analyseomraade", "Hendelsestype", "Analysenavn", risikoanalyseaar]]
    trafikk_og_hendelser = koblet.loc[lambda df: df._merge == "both"].copy()[
        ["Skipstype", "Lengdegruppe", "Analyseomraade", "Hendelsestype", "Analysenavn", risikoanalyseaar]]
    hendelser_uten_trafikk = koblet.loc[lambda df: df._merge == "left_only"][
        ["Skipstype", "Lengdegruppe", "Analyseomraade", "Hendelsestype", "Analysenavn", risikoanalyseaar]]

    antall_hendelser_uten_trafikk = hendelser_uten_trafikk.groupby("Hendelsestype")[risikoanalyseaar].sum()

    if len(trafikk_uten_hendelser) > 0:
        melding = "Har trafikk uten tilhørende hendelser."
        if tiltak_eller_ref:
            melding += f" Gjelder {tiltak_eller_ref}."
        melding += f" Analyseområde {analyseomraade}. \n"
        melding += f"{trafikk_uten_hendelser[['Skipstype', 'Lengdegruppe']].drop_duplicates()}"
        risiko_logger(melding)

    if len(hendelser_uten_trafikk) > 0:
        melding = "Har hendelser uten trafikk."
        if spre_hendelser_fra_skip_uten_trafikk:
            melding += " Disse blir spredt på de andre skipene proporsjonalt med deres trafikk."
        if tiltak_eller_ref:
            melding += f" Gjelder {tiltak_eller_ref}."
        melding += f" Analyseområde {analyseomraade}. \n"
        melding += f"{hendelser_uten_trafikk[['Skipstype', 'Lengdegruppe']].drop_duplicates()}"
        risiko_logger(melding)

    # Kristoffer: Enighet med Kystverket 19. oktober om at hendelser uten trafikk skal samles opp, og spres på øvrige skip
    # proporsjonalt med deres trafikk
    if len(hendelser_uten_trafikk) > 0 and spre_hendelser_fra_skip_uten_trafikk:
        vekter_for_spredning = (
            trafikk.reset_index()
            .loc[lambda df: df.Analyseomraade == analyseomraade]
            .groupby(["Skipstype", "Lengdegruppe", "Analysenavn"])
            [risikoanalyseaar]
            .sum()
            .reindex(
                trafikk_og_hendelser[["Skipstype", "Lengdegruppe", "Analysenavn"]].drop_duplicates()
            )
        )
        vekter_for_spredning = (vekter_for_spredning / vekter_for_spredning.sum(axis=0))
        assert np.allclose(vekter_for_spredning.sum(axis=0),
                           1), f"Noe er galt i prosessen med å komme frem til vekter for å stpre trafikken. De summerer ikke til 1"

        spredt = pd.concat([
            (
                vekter_for_spredning
                .multiply(antall_hendelser_uten_trafikk[hendelse])
                .to_frame()
                .assign(Hendelsestype=hendelse)
            )
            for hendelse in antall_hendelser_uten_trafikk.index.values
        ], axis=0).reset_index().set_index(["Skipstype", "Lengdegruppe", "Hendelsestype", "Analysenavn"])

        try:
            pd.testing.assert_series_equal(spredt.groupby("Hendelsestype")[risikoanalyseaar].sum(),
                                           antall_hendelser_uten_trafikk)
        except AssertionError:
            raise AssertionError(
                f"Noe har gått galt i spredningen av hendelser uten trafikk på øvrige skip. Du må debugge i funksjonen fordel_og_fremskriv_ra")

        tillagt_spredte_hendelser = (
            trafikk_og_hendelser.rename(columns={risikoanalyseaar: "left"})
            .merge(right=spredt.reset_index().rename(columns={risikoanalyseaar: "right"}),
                   on=["Skipstype", "Lengdegruppe", "Hendelsestype", FOLSOMHET_KOLONNE],
                   how="inner"
                   )
            .pipe(
                _legg_til_kolonne,
                risikoanalyseaar,
                lambda df: df["left"] + df["right"])
            [["Skipstype", "Lengdegruppe", "Hendelsestype", FOLSOMHET_KOLONNE, risikoanalyseaar]]
        )

        pd.testing.assert_series_equal(tillagt_spredte_hendelser.groupby("Hendelsestype")[risikoanalyseaar].sum(),
                                       koblet.groupby("Hendelsestype")[risikoanalyseaar].sum())

        hendelser = (
            tillagt_spredte_hendelser
            .merge(
                right=endringsfaktorer.drop(risikoanalyseaar, axis=1),
                on=["Skipstype", "Lengdegruppe", "Analysenavn"],
                how="left",
                indicator=True
            )
        )

        assert (hendelser._merge == "both").all()

    else: # Det foreligger trafikk for alle hendelser
        hendelser = koblet.loc[lambda df: df._merge == "both"]

    fremskrivingsaar = [aar for aar in beregningsaar if aar != risikoanalyseaar]
    for aar in fremskrivingsaar:
        hendelser[aar] = hendelser[aar] * hendelser[risikoanalyseaar]

    return (
        hendelser
        .drop("_merge", axis=1)
        .assign(
            Strekning=strekning,
            Tiltaksomraade=tiltaksomraade,
            Tiltakspakke=tiltakspakke,
            Rute=rute,
            Risikoanalyse=risikoanalysenavn
        )
        .set_index(FOLSOMHET_COLS + ["Risikoanalyse", "Hendelsestype"])
    )


def _stable_folsomhetsanalyse(df: DataFrame, folsomheter: List, folsomhetsnavn: str):
    """
    Hjelpefunksjon for å sørge for at RA har én rad for hver følsomhetsanalyse.

    Ellers blir det kluss i koblingen mellom ra og trafikk når noen hendelser mangler trafikk.

    Args:
        df: dataframen med risikoanalysene
        folsomheter: de enkelte verdiene som skal fylles inn i følsomhetskolonnen. Antall her bestemmer hvor mange df gjentas
        folsomhetsnavn: navnet på følsomhetskolonnen

    Returns:

    """
    return pd.concat([df.copy().pipe(_legg_til_kolonne, folsomhetsnavn, folsomhet) for folsomhet in folsomheter], axis=0)

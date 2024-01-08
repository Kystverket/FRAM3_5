import numpy as np
import pandas as pd
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.hjelpefunksjoner import forut, _legg_til_kolonne
from fram.generelle_hjelpemoduler.kalkpriser import (
    prisjustering,
    realprisjustering_kalk,
    get_vekstfaktor,
)
from fram.generelle_hjelpemoduler.konstanter import FOLSOMHET_COLS, VIRKNINGSNAVN_UTSLIPP_ANLEGG
from fram.generelle_hjelpemoduler.schemas import FolsomColsSchema, AggColsSchema, UtslippAnleggsfasenSchema
from fram.generelle_hjelpemoduler.konstanter import FOLSOMHET_COLS, FOLSOM_KARBON_HOY, FOLSOM_KARBON_LAV
from fram.generelle_hjelpemoduler.schemas import FolsomColsSchema, AggColsSchema
from fram.virkninger.drivstoff.hjelpemodul_drivstofforbruk import (
    utslipp_til_luft_per_time,
)
from fram.virkninger.utslipp_til_luft.schemas import (
    HastighetsSchema,
    KalkprisSchema,
)

utslippstype_til_virknignsnavn = {
    "CO2": "Endring i globale utslipp til luft",
    "CO2-høy": "Endring i globale utslipp til luft",
    "CO2-lav": "Endring i globale utslipp til luft",
    "PM10": "Endring i lokale utslipp til luft",
    "NOX": "Endring i lokale utslipp til luft",
}

utslippstype_til_maaleenhet = {"CO2": "Kg CO2-e", "PM10": "Kg", "NOX": "Kg"}


def get_kalkpris_utslipp_til_luft(
    beregningsaar: list, kroneaar: int,
):
    """
    Hovedfunksjon for å hente kalkulasjonspriser for utslipp til luft.Kalkulasjonspriser for utslipp til luft,
    kroner per kg, for CO2, PM10 og NOX.

    Denne funksjonen sørger for at alle verdier er kronejustert til "kroneaar" og enkelte av verdiene er realprisjustert.
    Gir en dataframe med index "utslipp" om tar verdiene "PM10", "NOX" og "CO2". Kolonner er alle år i analyseperioden
    fra og med ferdigstillelsesår i tråd med "beregningsaar".

    FOR PM10 og NOX er det kun kalkulasjonspriser for "spredt" bebyggelse som benyttes videre i
    beregningene. For CO2 er det "Alle" områder ettersom det kun finnes en kalkulasjonspris for denne utslippstypen.

    Kun PM10 og NOX realprisjusteres. Det kommer av at det allerede ligger en prisvekst i CO2-prisen.
    Dersom kalkulasjonsprisene er oppgitt i kroneår annet enn kroneåret som kalkulasjonsprisene skal oppgis i, så
    realprisjusteres kalkulasjonsprisen til dette året. Etter kroneprisåret justeres også verdiene med forventet
    realprisvekst i gjeldende perspektivmelding.

    Args:
        beregningsaar: liste med beregningsaar fra og med ferdigstillelsesår
        kroneaar: Året du vil ha verdiene kronejustert til

    Returns:
        Dataframe med verdsettingsfaktorer for utslipp til luft.

    """
    # TODO: Oppdatere dette året til 2022?
    antall_kolonner = beregningsaar[-1] - 2015 + 3

    priser = (
        forut("kalkpris_utslipp_luft", antall_kolonner=antall_kolonner)
        .iloc[:8, :]
        .loc[lambda df: df["Område"].isin(["Alle", "Spredt"])]
        .drop(["Område"], axis=1)
        .set_index("Utslipp")
    )

    fra_kroneaar = priser["Kroneverdi"].astype(int).to_dict()
    til_aar = kroneaar

    priser.drop(["Kroneverdi"], axis=1, inplace=True)
    for utslippstype in priser.index:
        korreksjonsfaktor = prisjustering(1, utgangsaar=fra_kroneaar[utslippstype], tilaar=til_aar) if til_aar >= fra_kroneaar[utslippstype] else 1
        priser.loc[utslippstype] *= korreksjonsfaktor

    priser = priser.T

    vekstfaktorer = pd.Series(
        {year: 1 + get_vekstfaktor(year) for year in range(2016, 2200)}
    ).cumprod()

    for col in ["PM10", "NOX"]:
        priser[col] = realprisjustering_kalk(
            priser[col].values, utgangsaar=fra_kroneaar[utslippstype], tilaar=til_aar
        )
        priser[col] *= vekstfaktorer

    priser = priser.T[beregningsaar]
    return priser


def beregn_kg(
    hastighet_per_passering: DataFrame[HastighetsSchema],
    total_tidsbruk: DataFrame[AggColsSchema],
    beregningsaar: list,
):
    """
    Hovedfunksjon for å beregne utslipp til luft målt i kilogram basert på hastighet og tidsbruk. Gir en dataframe med
    totale utslipp fordelt på utslippstype (CO2, NOX, PM10) per skipstype og lengdegruppe på rutenivå over
    analyseperioden fra ferdigstillelsesår (beregningsaar).

    Funksjonen henter ut utslippsfaktorer (utslipp per time) basert på drivstofforbruket som avhenger av hastighet.
    Deretter ganges disse utslippsfaktorene sammen med total tidsbruk per skipstype og lengdegruppe på en spesifikk rute.

    Args:
        hastighet_per_passering: hastighet per skipstype, lengdegruppe per rute. Streng formatering
        total_tidsbruk: total tidsbruk per skipstype, lengdegruppe per rute. Streng formatering
        beregningsaar: liste med år over analyseperioden fra og med ferdigstillesesår.

    Returns:
        DataFrame med totale utslipp til luft per skipstype, lengdegruppe og utslippstype på rutenivå.
    """

    kg_per_time = (
        utslipp_til_luft_per_time(hastighet_per_passering.reset_index(), beregningsaar)
        .rename(columns=lambda x: f"kg_{x}")
        .reset_index()
    )

    timer = total_tidsbruk.rename(columns=lambda x: f"timer_{x}").reset_index()

    kg = timer.merge(right=kg_per_time, on=["Skipstype", "Lengdegruppe", "Rute"], how="left")
    for year in beregningsaar:
        kg[year] = kg[f"kg_{year}"] * kg[f"timer_{year}"]

    kg = kg.set_index(FOLSOMHET_COLS + ["Type"])[beregningsaar].reset_index()

    return kg


def verdsett_utslipp_til_luft(
    total_tidsbruk_ref: DataFrame[FolsomColsSchema],
    total_tidsbruk_tiltak: DataFrame[FolsomColsSchema],
    hastighet_per_passering_ref: DataFrame[HastighetsSchema],
    hastighet_per_passering_tiltak: DataFrame[HastighetsSchema],
    trafikkaar: list,
    alle_aar: list,
    kroneaar: int,
    kalkpris_utslipp_til_luft: DataFrame[KalkprisSchema] = None,
    utslipp_anleggsfasen: DataFrame[UtslippAnleggsfasenSchema] = None
):
    """
    Hovedfunksjon for å beregne verdsatt virkning for utslipp til luft basert på hastighet, tidsbruk og kalkulasjonspriser.
    Oppgitt i kroneverdier tilsvarende "kroneaar". Gir to dataframes med verdsatte virkninger per utslippstype per år i
    analyseperioden fra og med ferdigstillelsesåret.

    Dersom det gis med en DataFrame "kalkpris_utslipp_luft" benyttes denne i beregningen. Denne dataframen må ha
    utslippsfaktorer målt i kr per kilogram utslipp fordelt på utslippstyper. Og må ha riktig kroneår.
    Alternativt benyttes beregningsmetode fra FRAM-modellen. I dette tilfellet brukes kroneaar.

    Args:
        total_tidsbruk_ref: total tidsbruk per skipstype, lengdegruppe per rute i referansebanen. Streng formatering
        total_tidsbruk_tiltak: total tidsbruk per skipstype, lengdegruppe per rute i tiltaksbanen. Streng formatering
        hastighet_per_passering_ref: hastighet per skipstype, lengdegruppe per rute i referansebanen. Streng formatering
        hastighet_per_passering_tiltak: hastighet per skipstype, lengdegruppe per rute i tiltaksbanen. Streng formatering
        trafikkaar: liste med år over analyseperioden fra og med åpningsåret.
        alle_aar: liste med år over analyseperioden fra og med første investeringsår.
        kroneaar: Året du vil ha verdiene kronejustert til
        kalkpris_utslipp_til_luft: df med kr per kg utslipp - Kun relevant om man ønsker å bruke kalkpriser utenfor FRAM-modellen.
        utslipp_anleggsfasen: Valgfritt. Kan legge ved utslipp i anleggsfasen for å få fanget dem også

    Returns:
        DataFrame med totale verdsatte utslipp til luft per utslippstype.
    """
    if total_tidsbruk_ref is not None:
        kg_ref = (
            beregn_kg(hastighet_per_passering_ref, total_tidsbruk_ref, trafikkaar)
            .pipe(
                _legg_til_manglende_kolonner,
                kolonner=alle_aar,
                fyllverdi=0.0
            )
            .fillna(0)
            .groupby(FOLSOMHET_COLS + ["Type"])[alle_aar]
            .sum()
            .reset_index()
            .rename(columns={"Type": "Utslipp"})
            .pipe( # Logikk for å koble følsomhetsanalysene mot riktig prisbane fra arket
                replace_column_value_condition,
                column_replace="Utslipp",
                new_value="CO2-høy",
                condition=lambda df: (df.Analysenavn == FOLSOM_KARBON_HOY) & (df.Utslipp == "CO2")
            )
            .pipe( # Logikk for å koble følsomhetsanalysene mot riktig prisbane fra arket
                replace_column_value_condition,
                column_replace="Utslipp",
                new_value="CO2-lav",
                condition=lambda df: (df.Analysenavn == FOLSOM_KARBON_LAV) & (df.Utslipp == "CO2")
            )
        )
    else:
        kg_ref = None

    if total_tidsbruk_ref is None:
        _kg_tiltak = utslipp_anleggsfasen
    else:
        _kg_tiltak =  pd.concat([
            beregn_kg(hastighet_per_passering_tiltak, total_tidsbruk_tiltak, trafikkaar),
            utslipp_anleggsfasen
            ],
            axis=0,
            ignore_index=True
        )

    kg_tiltak = (
       _kg_tiltak
        .pipe(
            _legg_til_manglende_kolonner,
            kolonner=alle_aar,
            fyllverdi=0.0
        )
        .fillna(0)
        .groupby(FOLSOMHET_COLS + ["Type"])[alle_aar]
        .sum()
        .reset_index()
        .rename(columns={"Type": "Utslipp"})
        .pipe( # Logikk for å koble følsomhetsanalysene mot riktig prisbane fra arket
            replace_column_value_condition,
            column_replace="Utslipp",
            new_value="CO2-høy",
            condition=lambda df: (df.Analysenavn == FOLSOM_KARBON_HOY) & (df.Utslipp == "CO2")
        )
        .pipe( # Logikk for å koble følsomhetsanalysene mot riktig prisbane fra arket
            replace_column_value_condition,
            column_replace="Utslipp",
            new_value="CO2-lav",
            condition=lambda df: (df.Analysenavn == FOLSOM_KARBON_LAV) & (df.Utslipp == "CO2")
        )
    )

    if kalkpris_utslipp_til_luft is None:
        utslippspriser = get_kalkpris_utslipp_til_luft(alle_aar, kroneaar)
    else:
        utslippspriser = kalkpris_utslipp_til_luft

    if kg_ref is not None:
        kr_ref = (
            multipliser_venstre_hoyre(kg_ref, utslippspriser, "Utslipp", alle_aar)
            .set_index(FOLSOMHET_COLS + ["Utslipp"])[alle_aar]
            .reset_index()
            .rename(columns={"Utslipp": "Undervirkning"})
            .assign(
                Virkningsnavn=lambda df: df.Undervirkning.map(
                    utslippstype_til_virknignsnavn
                )
            )
            .assign(Undervirkning=lambda df: np.where(df.Skipstype == "Anleggsfasen", "CO2 utslipp anleggsfasen",
                                                      df.Undervirkning))
            .assign(Virkningsnavn=lambda df: np.where(df.Skipstype == "Anleggsfasen", "CO2 utslipp anleggsfasen",
                                                      df.Virkningsnavn))
            .assign(Skipstype=lambda df: df.Skipstype.replace("Anleggsfasen", "Alle"))
            .assign(Lengdegruppe=lambda df: df.Lengdegruppe.replace("Anleggsfasen", "Alle"))
        )
        kg_ref = kg_ref.pipe(_bytt_skipstype_lengde_fra_anlegg)
    else:
        kr_ref = None


    kr_tiltak = (
        multipliser_venstre_hoyre(kg_tiltak, utslippspriser, "Utslipp", alle_aar)
        .set_index(FOLSOMHET_COLS + ["Utslipp"])[alle_aar]
        .reset_index()
        .rename(columns={"Utslipp": "Undervirkning"})
        .assign(
            Virkningsnavn=lambda df: df.Undervirkning.map(
                utslippstype_til_virknignsnavn
            )
        )
        .assign(Undervirkning=lambda df: np.where(df.Skipstype == "Anleggsfasen", VIRKNINGSNAVN_UTSLIPP_ANLEGG, df.Undervirkning))
        .assign(Virkningsnavn=lambda df: np.where(df.Skipstype == "Anleggsfasen", VIRKNINGSNAVN_UTSLIPP_ANLEGG, df.Virkningsnavn))
        .assign(Skipstype=lambda df: df.Skipstype.replace("Anleggsfasen", "Alle"))
        .assign(Lengdegruppe=lambda df: df.Lengdegruppe.replace("Anleggsfasen", "Alle"))
    )

    return kr_ref,\
           kr_tiltak,\
           kg_ref, \
           kg_tiltak.pipe(_bytt_skipstype_lengde_fra_anlegg)


def multipliser_venstre_hoyre(venstre, hoyre, koblekolonner, multipliseringskolonner):

    koblet = venstre.merge(hoyre, how="left", on=koblekolonner)

    for col in multipliseringskolonner:
        koblet[col] = koblet[str(col) + "_x"].multiply(koblet[str(col) + "_y"])

    return koblet


def replace_column_value_condition(df, column_replace, new_value, condition):
    _df = df.copy()
    mask = condition(_df)
    _df.loc[mask, column_replace] = new_value
    return _df
def _bytt_skipstype_lengde_fra_anlegg(df):
    return (
        df
        .assign(Skipstype= lambda df: df.Skipstype.replace("Anleggsfasen", "Alle"))
        .assign(Lengdegruppe=lambda df: df.Lengdegruppe.replace("Anleggsfasen", "Alle"))
    )

def _legg_til_manglende_kolonner(df, kolonner, fyllverdi):
    _df = df.copy()
    for col in kolonner:
        if col not in _df:
            _df[col] = fyllverdi
    return _df
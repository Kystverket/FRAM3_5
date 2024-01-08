import itertools
import random

import pandas as pd
import pytest

from fram.generelle_hjelpemoduler.konstanter import (
    TRAFIKK_COLS,
    SKIPSTYPER,
    LENGDEGRUPPER_UTEN_MANGLER,
    FOLSOMHET_COLS,
    FOLSOMHET_KOLONNE,
)
from fram.generelle_hjelpemoduler.schemas import TrafikkGrunnlagSchema
from fram.virkninger.tid.virkning import Tidsbruk

NUM_ROWS = 10
YEARS = [2026, 2027]


@pytest.fixture()
def df_kalkpris():
    alle_mulige = list(itertools.product(SKIPSTYPER, LENGDEGRUPPER_UTEN_MANGLER))
    utvalgte = random.sample(alle_mulige, NUM_ROWS)

    skipstyper, lengdegrupper = zip(*utvalgte)
    data = {"Skipstype": skipstyper, "Lengdegruppe": lengdegrupper}
    for year in YEARS:
        data[year] = 1.0
    return pd.DataFrame.from_dict(data).assign(Analysenavn="Test")


@pytest.fixture()
def df_tidsbruk_passeringer(df_kalkpris):
    dummy_df = df_kalkpris.copy().drop(FOLSOMHET_KOLONNE, axis=1)
    dummy_df["Strekning"] = "a"
    dummy_df["Tiltaksomraade"] = -999
    dummy_df["Tiltakspakke"] = 1
    dummy_df["Analyseomraade"] = "a"
    dummy_df["Rute"] = "a"

    dummy_df = dummy_df.set_index(TRAFIKK_COLS)
    return dummy_df


@pytest.fixture()
def df_trafikkgrunnlag_duplikater(df_tidsbruk_passeringer):
    df = (
        df_tidsbruk_passeringer.copy()
        .reset_index()
        .assign(Skipstype="Cruiseskip", Lengdegruppe="100-150")
        .assign(Analysenavn="Test")
        .set_index(FOLSOMHET_COLS)
    )
    return df


@pytest.fixture()
def velfungerende_virkning(df_kalkpris):
    tidsbruk = Tidsbruk(beregningsaar=YEARS, kalkulasjonspriser=df_kalkpris)
    return tidsbruk


def test_virkning_korrekt_input(velfungerende_virkning, df_tidsbruk_passeringer):

    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=df_tidsbruk_passeringer,
        tidsbruk_per_passering_tiltak=df_tidsbruk_passeringer,
        trafikk_ref=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
        trafikk_tiltak=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
    )
    assert True


def test_virkning_funker_med_manglende_input(
    velfungerende_virkning, df_tidsbruk_passeringer
):
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=df_tidsbruk_passeringer,
        tidsbruk_per_passering_tiltak=df_tidsbruk_passeringer,
        trafikk_ref=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
        trafikk_tiltak=df_tidsbruk_passeringer.iloc[:-1, :]
        .assign(Analysenavn="Test")
        .set_index(FOLSOMHET_KOLONNE, append=True),
    )
    velfungerende_virkning.verdsatt_brutto_ref
    assert True


def test_virkning_feiler_med_ekstra_udefinert_input(
    velfungerende_virkning, df_tidsbruk_passeringer
):
    df_tidsbruk_passeringer = df_tidsbruk_passeringer.reset_index()
    df_tidsbruk_passeringer.loc[
        "Skipstype", len(df_tidsbruk_passeringer)
    ] = "Denne hører ikke hjemme"
    df_tidsbruk_passeringer.set_index(TRAFIKK_COLS)
    with pytest.raises(Exception):
        velfungerende_virkning.beregn(
            tidsbruk_per_passering_ref=df_tidsbruk_passeringer,
            tidsbruk_per_passering_tiltak=df_tidsbruk_passeringer,
            trafikk_ref=df_tidsbruk_passeringer,
            trafikk_tiltak=df_tidsbruk_passeringer,
        )
    assert True


def test_validering_stopper_ikkeunike_skip(df_trafikkgrunnlag_duplikater):
    with pytest.raises(Exception):
        TrafikkGrunnlagSchema.validate(df_trafikkgrunnlag_duplikater)


def test_virkning_feiler_med_ikkeunike_skip(
    velfungerende_virkning, df_trafikkgrunnlag_duplikater
):
    with pytest.raises(Exception):
        velfungerende_virkning.beregn(
            tidsbruk_per_passering_ref=df_trafikkgrunnlag_duplikater,
            tidsbruk_per_passering_tiltak=df_trafikkgrunnlag_duplikater,
            trafikk_ref=df_trafikkgrunnlag_duplikater,
            trafikk_tiltak=df_trafikkgrunnlag_duplikater,
        )


def test_beregn_svar_null_alle_har_data(
    velfungerende_virkning, df_tidsbruk_passeringer
):
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=df_tidsbruk_passeringer,
        tidsbruk_per_passering_tiltak=df_tidsbruk_passeringer,
        trafikk_ref=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
        trafikk_tiltak=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
    )
    assert velfungerende_virkning.verdsatt_netto.sum().sum() == 0


@pytest.mark.parametrize(
    "rentebane, fasit",
    [
        ({year: 0 for year in YEARS}, 0),
        ({year: 0 for year in YEARS + [2011]}, 0),
        ({year: 0 for year in YEARS[:1]}, 0),
    ],
)
def test_beregn_naaverdi_null_alle_har_data(
    velfungerende_virkning, df_tidsbruk_passeringer, rentebane, fasit
):
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=df_tidsbruk_passeringer,
        tidsbruk_per_passering_tiltak=df_tidsbruk_passeringer,
        trafikk_ref=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
        trafikk_tiltak=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
    )
    assert velfungerende_virkning.get_naaverdi(rentebane=rentebane) == fasit


def test_beregn_svar_positiv_naaverdi(velfungerende_virkning, df_tidsbruk_passeringer):
    tidsbruk_ref = df_tidsbruk_passeringer.copy() * 2
    tidsbruk_tiltak = df_tidsbruk_passeringer.copy()
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=tidsbruk_ref,
        tidsbruk_per_passering_tiltak=tidsbruk_tiltak,
        trafikk_ref=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
        trafikk_tiltak=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
    )
    assert velfungerende_virkning.verdsatt_netto.sum().sum() == len(YEARS) * NUM_ROWS


def test_beregn_svar_trafikkoverforing_null_naaverdi(
    velfungerende_virkning, df_tidsbruk_passeringer
):
    tidsbruk_ref = (
        df_tidsbruk_passeringer.copy()
        .reset_index()
        .assign(Rute="b")
        .set_index(TRAFIKK_COLS)
    )
    tidsbruk_tiltak = df_tidsbruk_passeringer.copy()
    trafikk_ref = tidsbruk_ref.copy()
    trafikk_tiltak = tidsbruk_tiltak.copy()
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=tidsbruk_ref,
        tidsbruk_per_passering_tiltak=tidsbruk_tiltak,
        trafikk_ref=trafikk_ref.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
        trafikk_tiltak=trafikk_tiltak.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
    )
    assert velfungerende_virkning.verdsatt_netto.sum().sum() == 0


def test_beregn_svar_trafikkoverforing_positiv_naaverdi(
    velfungerende_virkning, df_tidsbruk_passeringer
):
    tidsbruk_ref = (
        df_tidsbruk_passeringer.copy()
        .reset_index()
        .assign(Rute="b")
        .set_index(TRAFIKK_COLS)
    )
    tidsbruk_tiltak = df_tidsbruk_passeringer.copy()
    trafikk_ref = tidsbruk_ref.copy()
    trafikk_tiltak = tidsbruk_tiltak.copy()
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=tidsbruk_ref * 2,
        tidsbruk_per_passering_tiltak=tidsbruk_tiltak,
        trafikk_ref=trafikk_ref.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
        trafikk_tiltak=trafikk_tiltak.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
    )
    assert velfungerende_virkning.verdsatt_netto.sum().sum() == len(YEARS) * NUM_ROWS

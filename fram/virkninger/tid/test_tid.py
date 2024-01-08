import itertools
import random
from pathlib import Path

import numpy as np
import pandas as pd
import pandera as pa
import pytest

from fram.generelle_hjelpemoduler.konstanter import (
    TRAFIKK_COLS,
    SKIPSTYPER,
    LENGDEGRUPPER_UTEN_MANGLER,
    FOLSOMHET_COLS,
    FOLSOMHET_KOLONNE,
)
from fram.generelle_hjelpemoduler.schemas import TrafikkGrunnlagSchema
from fram.virkninger.tid.verdsetting import tidskalk_funksjoner, _tidskalk_per_skip
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
    dummy_df = df_kalkpris.drop(FOLSOMHET_KOLONNE, axis=1).copy()
    dummy_df["Strekning"] = "a"
    dummy_df["Tiltaksomraade"] = 1
    dummy_df["Tiltakspakke"] = 2
    dummy_df["Analyseomraade"] = "a"
    dummy_df["Rute"] = "a"

    dummy_df = dummy_df.set_index(TRAFIKK_COLS)
    return dummy_df


@pytest.fixture()
def df_trafikkgrunnlag_duplikater(df_tidsbruk_passeringer):
    df = (
        df_tidsbruk_passeringer.copy()
        .reset_index()
        .assign(Skipstype="Cruiseskip", Lengdegruppe="100-150", Analysenavn="Test")
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
    with pytest.raises((pa.errors.SchemaError, pa.errors.SchemaErrors)):
        velfungerende_virkning.beregn(
            tidsbruk_per_passering_ref=df_trafikkgrunnlag_duplikater.droplevel(
                FOLSOMHET_KOLONNE
            ),
            tidsbruk_per_passering_tiltak=df_trafikkgrunnlag_duplikater.droplevel(
                FOLSOMHET_KOLONNE
            ),
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
    trafikk_ref = (
        tidsbruk_ref.copy()
        .assign(Analysenavn="Test")
        .set_index(FOLSOMHET_KOLONNE, append=True)
    )
    trafikk_tiltak = (
        tidsbruk_tiltak.copy()
        .assign(Analysenavn="Test")
        .set_index(FOLSOMHET_KOLONNE, append=True)
    )
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=tidsbruk_ref,
        tidsbruk_per_passering_tiltak=tidsbruk_tiltak,
        trafikk_ref=trafikk_ref,
        trafikk_tiltak=trafikk_tiltak,
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
    trafikk_ref = (
        tidsbruk_ref.copy()
        .assign(Analysenavn="Test")
        .set_index(FOLSOMHET_KOLONNE, append=True)
    )
    trafikk_tiltak = (
        tidsbruk_tiltak.copy()
        .assign(Analysenavn="Test")
        .set_index(FOLSOMHET_KOLONNE, append=True)
    )
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=tidsbruk_ref * 2,
        tidsbruk_per_passering_tiltak=tidsbruk_tiltak,
        trafikk_ref=trafikk_ref,
        trafikk_tiltak=trafikk_tiltak,
    )
    assert velfungerende_virkning.verdsatt_netto.sum().sum() == len(YEARS) * NUM_ROWS


@pytest.fixture()
def kalkpris_df():
    csv_path = Path(__file__).parent / "test_tidskalkulasjonspriser_mikrodata.csv"
    df = (
        pd.read_csv(csv_path, delimiter=",")
        .rename(
            columns={"BT": "grosstonnage", "dodvekt": "dwt", "Lengde": "skipslengde"}
        )
        .assign(Analysenavn="Test")
    )
    return df


def test_tidskost(kalkpris_df):
    for row in kalkpris_df.to_dict("records"):
        kost_fasit = row["tid_kpris"]
        if kost_fasit == 0:
            kost_fasit = np.nan
        kost_predikert = tidskalk_funksjoner(
            row["Skipstype"],
            dwt=row["dwt"],
            grosstonnage=row["grosstonnage"],
            gasskap=None,
            skipslengde=row["skipslengde"],
        )
        assert np.isclose(kost_fasit, kost_predikert, equal_nan=True)


def test_tidskost_df(kalkpris_df):
    kalkpris_df["gasskap"] = 0
    faktisk_tidskost = kalkpris_df.tid_kpris.values
    faktisk_tidskost = np.where(faktisk_tidskost == 0, np.nan, faktisk_tidskost)
    predikert_tidskost = _tidskalk_per_skip(kalkpris_df, utgangsaar=2021, tilaar=2021).values
    assert np.allclose(faktisk_tidskost, predikert_tidskost, equal_nan=True)

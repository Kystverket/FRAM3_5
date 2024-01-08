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
from fram.virkninger.drivstoff.hjelpemodul_drivstofforbruk import get_drivstoffandeler, interpoler_aarvis
from fram.virkninger.tid.verdsetting import tidskalk_funksjoner, _tidskalk_per_skip
from fram.virkninger.drivstoff.virkning import Drivstoff

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
def df_hastighet_passeringer(df_tidsbruk_passeringer):
    df = (df_tidsbruk_passeringer.copy()
          .rename(columns={2026:"Hastighet"})
          .drop(2027, axis=1)
          )
    return df

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
    drivstoff = Drivstoff(beregningsaar=YEARS, tankested="nord", kroneaar=2020)
    return drivstoff


def test_virkning_korrekt_input(velfungerende_virkning, df_tidsbruk_passeringer, df_hastighet_passeringer):

    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=df_tidsbruk_passeringer,
        tidsbruk_per_passering_tiltak=df_tidsbruk_passeringer,
        hastighet_per_passering_ref=df_hastighet_passeringer,
        hastighet_per_passering_tiltak=df_hastighet_passeringer,
        trafikk_ref=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(FOLSOMHET_KOLONNE, append=True),
        trafikk_tiltak=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(FOLSOMHET_KOLONNE, append=True),
    )
    assert True


def test_virkning_funker_med_manglende_input(velfungerende_virkning, df_tidsbruk_passeringer, df_hastighet_passeringer):
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=df_tidsbruk_passeringer,
        tidsbruk_per_passering_tiltak=df_tidsbruk_passeringer,
        hastighet_per_passering_ref=df_hastighet_passeringer,
        hastighet_per_passering_tiltak=df_hastighet_passeringer,
        trafikk_ref=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(FOLSOMHET_KOLONNE, append=True),
        trafikk_tiltak=df_tidsbruk_passeringer.iloc[:-1, :]
        .assign(Analysenavn="Test")
        .set_index(FOLSOMHET_KOLONNE, append=True),
    )
    velfungerende_virkning.verdsatt_brutto_ref
    assert True


def test_virkning_feiler_med_ekstra_udefinert_input(velfungerende_virkning, df_tidsbruk_passeringer, df_hastighet_passeringer):
    df_tidsbruk_passeringer = df_tidsbruk_passeringer.reset_index()
    df_tidsbruk_passeringer.loc["Skipstype", len(df_tidsbruk_passeringer)] = "Denne hører ikke hjemme"
    df_tidsbruk_passeringer.set_index(TRAFIKK_COLS)
    with pytest.raises(Exception):
        velfungerende_virkning.beregn(
            tidsbruk_per_passering_ref=df_tidsbruk_passeringer,
            tidsbruk_per_passering_tiltak=df_tidsbruk_passeringer,
            hastighet_per_passering_ref=df_hastighet_passeringer,
            hastighet_per_passering_tiltak=df_hastighet_passeringer,
            trafikk_ref=df_tidsbruk_passeringer,
            trafikk_tiltak=df_tidsbruk_passeringer,
        )
    assert True


def test_validering_stopper_ikkeunike_skip(df_trafikkgrunnlag_duplikater):
    with pytest.raises(Exception):
        TrafikkGrunnlagSchema.validate(df_trafikkgrunnlag_duplikater)


def test_virkning_feiler_med_ikkeunike_skip(
    velfungerende_virkning, df_trafikkgrunnlag_duplikater, df_hastighet_passeringer
):
    with pytest.raises((pa.errors.SchemaError, pa.errors.SchemaErrors)):
        velfungerende_virkning.beregn(
            tidsbruk_per_passering_ref=df_trafikkgrunnlag_duplikater.droplevel(
                FOLSOMHET_KOLONNE
            ),
            tidsbruk_per_passering_tiltak=df_trafikkgrunnlag_duplikater.droplevel(
                FOLSOMHET_KOLONNE
            ),
            hastighet_per_passering_ref=df_hastighet_passeringer,
            hastighet_per_passering_tiltak=df_hastighet_passeringer,
            trafikk_ref=df_trafikkgrunnlag_duplikater,
            trafikk_tiltak=df_trafikkgrunnlag_duplikater,
        )


def test_beregn_svar_null_alle_har_data(
    velfungerende_virkning, df_tidsbruk_passeringer, df_hastighet_passeringer
):
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=df_tidsbruk_passeringer,
        tidsbruk_per_passering_tiltak=df_tidsbruk_passeringer,
        hastighet_per_passering_ref=df_hastighet_passeringer,
        hastighet_per_passering_tiltak=df_hastighet_passeringer,
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
    velfungerende_virkning, df_tidsbruk_passeringer, df_hastighet_passeringer, rentebane, fasit
):
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=df_tidsbruk_passeringer,
        tidsbruk_per_passering_tiltak=df_tidsbruk_passeringer,
        hastighet_per_passering_ref=df_hastighet_passeringer,
        hastighet_per_passering_tiltak=df_hastighet_passeringer,
        trafikk_ref=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
        trafikk_tiltak=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
    )
    assert velfungerende_virkning.get_naaverdi(rentebane=rentebane) == fasit


def test_beregn_svar_positiv_naaverdi(velfungerende_virkning, df_tidsbruk_passeringer, df_hastighet_passeringer):
    tidsbruk_ref = df_tidsbruk_passeringer.copy() * 2
    tidsbruk_tiltak = df_tidsbruk_passeringer.copy()
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=tidsbruk_ref,
        tidsbruk_per_passering_tiltak=tidsbruk_tiltak,
        hastighet_per_passering_ref=df_hastighet_passeringer,
        hastighet_per_passering_tiltak=df_hastighet_passeringer,
        trafikk_ref=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
        trafikk_tiltak=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
    )
    assert velfungerende_virkning.verdsatt_netto.sum().sum() > 0


def test_volumvirkning(velfungerende_virkning, df_tidsbruk_passeringer, df_hastighet_passeringer):
    tidsbruk_ref = df_tidsbruk_passeringer.copy() * 2
    tidsbruk_tiltak = df_tidsbruk_passeringer.copy()
    velfungerende_virkning.beregn(
        tidsbruk_per_passering_ref=tidsbruk_ref,
        tidsbruk_per_passering_tiltak=tidsbruk_tiltak,
        hastighet_per_passering_ref=df_hastighet_passeringer,
        hastighet_per_passering_tiltak=df_hastighet_passeringer,
        trafikk_ref=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
        trafikk_tiltak=df_tidsbruk_passeringer.assign(Analysenavn="Test").set_index(
            FOLSOMHET_KOLONNE, append=True
        ),
    )
    velfungerende_virkning.volumvirkning_ref
    velfungerende_virkning.volumvirkning_tiltak

def test_get_drivstoffmiks():
    aar = list(range(2022, 2150))
    andeler = get_drivstoffandeler(aar)
    assert np.allclose(andeler.groupby(["Skipstype", "Lengdegruppe"])[aar].sum(), 1)


def test_interpoler_aarvis():
    df = pd.DataFrame(
        {2020: [1, 1, 1, 1, 1, 1], 2030: [2, 2, 2, 2, 2, 2]},
        index=pd.Series(['a', 'b', 'c', 'd', 'e', 'f'],
        name="Indeks")
    ).astype(float)
    output = interpoler_aarvis(df, faste_kolonner=[2020, 2030], siste_kolonne=2060)
    fasit_kolonner = list(range(2020, 2061))
    for col in fasit_kolonner:
        assert len([c for c in output.columns if c == col]) == 1
        if col > 2030:
            pd.testing.assert_series_equal(output[col], df[2030], check_names=False)

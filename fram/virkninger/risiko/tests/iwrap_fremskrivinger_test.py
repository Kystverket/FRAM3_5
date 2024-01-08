import itertools
import random
from pathlib import Path

import pandas as pd
import pytest

from fram.generelle_hjelpemoduler.konstanter import (
    TRAFIKK_COLS,
    FOLSOMHET_COLS,
    SKIPSTYPER,
    LENGDEGRUPPER_UTEN_MANGLER,
    FOLSOMHET_KOLONNE,
)
from fram.virkninger.risiko.hjelpemoduler import iwrap_fremskrivinger

NUM_ROWS = 10
YEARS = list(range(2017, 2051))


@pytest.fixture()
def df_trafikk():
    alle_mulige = list(itertools.product(SKIPSTYPER, LENGDEGRUPPER_UTEN_MANGLER))
    utvalgte = random.sample(alle_mulige, NUM_ROWS)

    skipstyper, lengdegrupper = zip(*utvalgte)
    data = {"Skipstype": skipstyper, "Lengdegruppe": lengdegrupper}
    for year in YEARS:
        data[year] = 1
    df = pd.DataFrame.from_dict(data)
    df["Strekning"] = "a"
    df["Tiltaksomraade"] = "a"
    df["Tiltakspakke"] = 1
    df["Analyseomraade"] = "a"
    df["Rute"] = "a"
    df[FOLSOMHET_KOLONNE] = "Test"
    df = df.set_index(FOLSOMHET_COLS)
    return df


@pytest.fixture()
def trafikk_referanse():
    return (
        pd.read_json(
            Path(__file__).parent / "trafikk_referanse.json",
            dtype={"Analyseomraade": str},
        )
        .assign(Analysenavn="Test")
        .set_index(FOLSOMHET_COLS)
        .rename(columns=lambda col: int(col))
    )


@pytest.fixture()
def df_tidsbruk_passeringer(df_kalkpris):
    dummy_df = df_kalkpris.copy()

    dummy_df = dummy_df.set_index(TRAFIKK_COLS)
    return dummy_df


def test_fremskriving(
    trafikk_referanse,
    risiko_ref,
    risiko_tiltak,
    rute_til_ra,
    hendelser_ref,
    hendelser_tiltak,
):
    h_ref, h_tiltak, h_red = iwrap_fremskrivinger.beregn_risiko(
        trafikk_referanse=trafikk_referanse,
        trafikk_tiltak=trafikk_referanse,
        risiko_ref=risiko_ref,
        risiko_tiltak=risiko_tiltak,
    )
    pd.testing.assert_frame_equal(
        h_ref.rename(columns=lambda col: int(col))[hendelser_ref.columns.to_list()],
        hendelser_ref,
    )
    pd.testing.assert_frame_equal(
        h_tiltak.rename(columns=lambda col: int(col))[
            hendelser_tiltak.columns.to_list()
        ],
        hendelser_tiltak,
    )

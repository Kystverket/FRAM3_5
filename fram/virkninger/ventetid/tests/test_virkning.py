import itertools
from pathlib import Path

import pandas as pd
import pytest
import numpy as np

from fram.generelle_hjelpemoduler.hjelpefunksjoner import _legg_til_kolonne
from fram.generelle_hjelpemoduler.konstanter import (
    SKIPSTYPER,
    LENGDEGRUPPER_UTEN_MANGLER,
    FRAM_DIRECTORY,
    FOLSOMHET_COLS,
    FOLSOMHET_KOLONNE,
)
from fram.virkninger.ventetid.excel import les_ventetidsinput_fra_excel
from fram.virkninger.ventetid.hjelpemoduler import SimuleringsInput
from fram.virkninger.ventetid.virkning import Ventetid

EXCEL_INPUT = FRAM_DIRECTORY / "strekning 11.xlsx"
YEARS = [2018, 2019]


@pytest.fixture
def gyldig_simuleringsinput() -> SimuleringsInput:
    inp = les_ventetidsinput_fra_excel(
        filepath=Path(__file__).parent / "ventetidseksempel.xlsx",
        sheet_name="eksempel 1",
        num_periods=100_000,
    )
    inp.lambda_df = inp.lambda_df.pipe(_legg_til_kolonne, FOLSOMHET_KOLONNE, "test")
    return inp


def test_simuleringsinput_gyldig(gyldig_simuleringsinput):
    assert True


@pytest.mark.parametrize(
    "kat, fasit",
    [
        ("aar", ["2018", "2019"]),
        ("mulige_lop", ["lop1", "lop2"]),
        ("perioder_for_sim", ["morgensommer", "morgenvinter"]),
        ("tidsenhet", 1.0),
        ("num_periods", 100000),
        ("lambda_df", pd.read_json(Path(__file__).parent / "gyldig_lambda_df.json")),
        ("mu_df", pd.read_json(Path(__file__).parent / "gyldig_mu_df.json")),
        (
            "perioder_andel",
            pd.read_json(Path(__file__).parent / "gyldig_perioder_andel.json"),
        ),
        (
            "ovrig_kategori",
            pd.read_json(Path(__file__).parent / "gyldig_ovrig_kategori.json"),
        ),
    ],
)
def test_simuleringsinput_riktige_verdier(gyldig_simuleringsinput, kat, fasit):
    attr = getattr(gyldig_simuleringsinput, kat)
    if kat == "mu_df":
        attr["lop1"] = attr["lop1"].astype(np.int64)
        attr["lop2"] = attr["lop2"].astype(np.int64)
    if isinstance(attr, pd.DataFrame):
        pd.testing.assert_frame_equal(attr.sort_index(axis=1), fasit.sort_index(axis=1))
    else:
        assert attr == fasit


@pytest.mark.parametrize(
    "kat, fasit",
    [
        ("lambda_df", "-3156844472412769668"),
        ("mu_df", "-1713077996185481602"),
        ("perioder_andel", "3113387957041276234"),
        ("ovrig_kategori", "3990618020511184816"),
    ],
)
def test_simuleringsinput_hash_dataframes_konstant(gyldig_simuleringsinput, kat, fasit):
    assert gyldig_simuleringsinput._hash_df(kat) == fasit


def test_simuleringsinput_ovrige_hasher_konstant(gyldig_simuleringsinput):
    assert "".join([str(el) for el in gyldig_simuleringsinput.alpha]) == "11"
    assert "".join(gyldig_simuleringsinput.mulige_lop) == "lop1lop2"
    assert "".join([str(el) for el in gyldig_simuleringsinput.aar]) == "20182019"
    assert (
        "".join(gyldig_simuleringsinput.perioder_for_sim) == "morgensommermorgenvinter"
    )
    assert str(gyldig_simuleringsinput.tidsenhet) == "1.0"
    assert str(gyldig_simuleringsinput.num_periods) == "100000"


def test_konstant_hash_string(gyldig_simuleringsinput):
    assert (
        gyldig_simuleringsinput._hash_string
        == "-3156844472412769668-17130779961854816023113387957041276234399061802051118481611lop1lop220182019morgensommermorgenvinter1.0100000"
    )


@pytest.fixture()
def gyldig_input_df():
    return pd.read_json(
        '{"Strekning":{"0":"Strekning 11"},"Tiltaksomraade":{"0":1},"Tiltakspakke":{"0":11},"Analyseomraade":{"0":"B"},"Rute":{"0":"A"},"Analysenavn":{"0":"test"},"ark_ref":{"0":"ventetid_referanse"},"ark_tiltak":{"0":"ventetid_tiltak"}}'
    )


@pytest.fixture()
def ugyldig_input_df():
    return pd.read_json(
        '{"Tiltaksomraade":{"0":1},"Tiltakspakke":{"0":11},"Analyseomraade":{"0":"1_1"},"Rute":{"0":"A"},"ark_ref":{"0":"ventetid_referanse"},"ark_tiltak":{"0":"ventetid_tiltak"}}'
    )


@pytest.fixture()
def gyldig_kalkpris():
    alle_mulige = list(itertools.product(SKIPSTYPER, LENGDEGRUPPER_UTEN_MANGLER))

    skipstyper, lengdegrupper = zip(*alle_mulige)
    data = {"Skipstype": skipstyper, "Lengdegruppe": lengdegrupper}
    for year in YEARS:
        data[year] = 1.0
    return pd.DataFrame.from_dict(data).assign(Analysenavn="Test")


@pytest.fixture()
def gyldig_trafikkgrunnlag(gyldig_kalkpris):
    data = gyldig_kalkpris.copy()
    data["Strekning"] = "11"
    data["Tiltaksomraade"] = "1"
    data["Tiltakspakke"] = "11"
    data["Analyseomraade"] = "B"
    data["Rute"] = "A"
    data[FOLSOMHET_KOLONNE] = "Test"
    data = data.set_index(FOLSOMHET_COLS)
    return data


@pytest.fixture()
def gyldig_virkning(gyldig_kalkpris, gyldig_trafikkgrunnlag):
    return Ventetid(
        kalkpris_tid=gyldig_kalkpris,
        trafikk_tiltak=gyldig_trafikkgrunnlag,
        trafikk_ref=gyldig_trafikkgrunnlag,
        beregningsaar=YEARS,
        logger=print,
    )


def test_gyldig_vikning(gyldig_virkning):
    assert True


def test_virkning_ref_og_tiltak(
    gyldig_virkning, gyldig_simuleringsinput, gyldig_trafikkgrunnlag
):
    metadata = gyldig_trafikkgrunnlag.reset_index()[
        ["Strekning", "Tiltaksomraade", "Tiltakspakke", "Analyseomraade", "Rute"]
    ]
    gyldig_virkning.beregn(
        simuleringsinput_ref=gyldig_simuleringsinput,
        simuleringsinput_tiltak=gyldig_simuleringsinput,
        metadatakolonner=metadata,
    )
    gyldig_virkning.verdsatt_netto


def test_virkning_bare_ref(
    gyldig_virkning, gyldig_simuleringsinput, gyldig_trafikkgrunnlag
):
    metadata = gyldig_trafikkgrunnlag.reset_index()[
        ["Strekning", "Tiltaksomraade", "Tiltakspakke", "Analyseomraade", "Rute"]
    ]
    gyldig_virkning.beregn(
        simuleringsinput_ref=gyldig_simuleringsinput,
        metadatakolonner=metadata,
    )
    gyldig_virkning.verdsatt_brutto_ref

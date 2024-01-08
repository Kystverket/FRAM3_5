import pandas as pd
import pytest

from fram.generelle_hjelpemoduler.konstanter import FOLSOMHET_KOLONNE
from fram.virkninger.vedlikehold.virkning import Vedlikeholdskostnader


@pytest.fixture
def kostnader_input():
    return pd.DataFrame(
        [["Båke", 10_000, "Test"], ["Stake", 5_000, "Test"], ["Stang", 1_000, "Test"]],
        columns=["Objekttype", "Total", FOLSOMHET_KOLONNE],
    ).set_index(["Objekttype", FOLSOMHET_KOLONNE])


@pytest.fixture
def oppgradering_input():
    return pd.DataFrame(
        [
            ["Båke", 10_000, 5, 20, 2016, "Test"],
            ["Stake", 5_000, 10, 15, 2016, "Test"],
            ["Stang", 1_000, 10, 20, 2016, "Test"],
        ],
        columns=[
            "Objekttype",
            "Total",
            "TG0->TG2",
            "TG1->TG2",
            "Kroneverdi",
            FOLSOMHET_KOLONNE,
        ],
    ).set_index(["Objekttype", FOLSOMHET_KOLONNE])


@pytest.fixture
def objekter_input():
    return pd.DataFrame(
        [["Båke", -1], ["Stake", -1], ["Stake", -1], ["Stang", 0], ["Båke", 1]],
        columns=["Objekttype", "Endring"],
    )


@pytest.fixture
def ingen_objekter_input():
    return pd.DataFrame(
        # [["Båke", 0], ["Stake", 0], ["Stake", 0], ["Stang", 0], ["Båke", 0]],
        columns=["Objekttype", "Endring"],
    )


@pytest.fixture
def ingen_endring_objekter_input():
    return pd.DataFrame(
        # [["Båke", 0], ["Stake", 0], ["Stake", 0], ["Stang", 0], ["Båke", 0]],
        columns=["Objekttype", "Endring"],
    )


@pytest.fixture
def velfungerende_virkning(kostnader_input, oppgradering_input):
    return Vedlikeholdskostnader(
        kostnader=kostnader_input,
        oppgrad=oppgradering_input,
        strekning="Test",
        tiltakspakke=0,
        beregningsaar=[2026, 2027, 2028, 2029],
        ferdigstillelsesaar=2026,
        sluttaar=2030,
        logger=lambda s: s,
    )


def test_velfungerende_virkning(velfungerende_virkning, objekter_input):
    velfungerende_virkning.beregn(objekter_input)
    assert True


def test_virkning_uten_objekter(velfungerende_virkning, ingen_objekter_input):
    velfungerende_virkning.beregn(ingen_objekter_input)
    assert True


def test_virkning_uten_endring(velfungerende_virkning, ingen_endring_objekter_input):
    velfungerende_virkning.beregn(ingen_endring_objekter_input)
    assert True


def test_feil_virkning(objekter_input):
    with pytest.raises(ValueError):
        feil_virkning = Vedlikeholdskostnader(
            kostnader=kostnader_input,
            oppgrad=oppgradering_input,
            strekning="Test",
            tiltakspakke=0,
            beregningsaar=[2026, 2027, 2028, 2029],
            ferdigstillelsesaar=2040,
            sluttaar=2020,
            logger=lambda s: s,
        )
        feil_virkning.beregn(objekter_input)
        assert feil_virkning.verdsatt_netto.sum().sum() == 0

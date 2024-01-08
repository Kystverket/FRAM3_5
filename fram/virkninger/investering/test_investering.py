import numpy as np
import pandas as pd
import pytest

from fram.generelle_hjelpemoduler.konstanter import FOLSOMHET_KOLONNE, KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG
from fram.virkninger.investering.virkning import Investeringskostnader
from datetime import datetime

@pytest.fixture
def investeringskostnader_stor():
    return pd.DataFrame(
        [
            {
                "Tiltaksomraade": -999,
                "Tiltakspakke": 0,
                FOLSOMHET_KOLONNE: "Test",
                "Kroneverdi": 2019,
                "P50 (kroner)": 100,
                "Forventningsverdi (kroner)": 100,
                "Anleggsperiode": 3,
                KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG: 100,
            }
        ]
    )

@pytest.fixture
def investeringskostnader_ny_kolonne():
    return pd.DataFrame(
        [
            {
                "Tiltaksomraade": -999,
                "Tiltakspakke": 0,
                "Investeringstype" : "Utdyping",
                FOLSOMHET_KOLONNE: "Test",
                "Kroneverdi": 2019,
                "P50 (kroner)": 100,
                "Forventningsverdi (kroner)": 100/3,
                "Anleggsperiode": 3,
                KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG: 200,
            },
            {
                "Tiltaksomraade": -999,
                "Tiltakspakke": 0,
                "Investeringstype": "Navigasjonsinnretninger",
                FOLSOMHET_KOLONNE: "Test",
                "Kroneverdi": 2019,
                "P50 (kroner)": 100,
                "Forventningsverdi (kroner)": 100/3,
                "Anleggsperiode": 3,
                KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG: 40,
            },
            {
                "Tiltaksomraade": -999,
                "Tiltakspakke": 0,
                "Investeringstype": "Annet",
                FOLSOMHET_KOLONNE: "Test",
                "Kroneverdi": 2019,
                "P50 (kroner)": 100,
                "Forventningsverdi (kroner)": 100/3,
                "Anleggsperiode": 3,
                KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG: 0,
            }
        ]
    )


@pytest.fixture
def investeringskostnader_liten():
    return pd.DataFrame(
        [
            {
                "Tiltaksomraade": -999,
                "Tiltakspakke": 0,
                FOLSOMHET_KOLONNE: "Test",
                "Kroneverdi": 2019,
                "P50 (kroner)": 50,
                "Forventningsverdi (kroner)": 50,
                "Anleggsperiode":3,
                KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG: 2,
            }
        ]
    )


@pytest.fixture
def investeringskostnader_tidlig():
    return pd.DataFrame(
        [
            {
                "Tiltaksomraade": -999,
                "Tiltakspakke": 0,
                "Kroneverdi": 2019,
                FOLSOMHET_KOLONNE: "Test",
                "P50 (kroner)": 50,
                "Forventningsverdi (kroner)": 50,
                "Anleggsperiode":10,
                KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG: 4
            }
        ]
    )


@pytest.fixture
def beregningsaar():
    return [i for i in range(2020, 2101)]


@pytest.fixture
def velfungerende_virkning(
    beregningsaar,
):
    return Investeringskostnader(
        beregningsaar=beregningsaar,
        ferdigstillelsesaar=2026,
        analysestart=datetime.now().year,
        kroneaar=2019,
        strekning="test",
        logger=lambda x: None,
    )


def test_velfungerende_virkning(velfungerende_virkning, investeringskostnader_stor):
    velfungerende_virkning.beregn(investeringskostnader_stor)

    assert True


def test_velfungerende_virkning_netto(
    velfungerende_virkning, investeringskostnader_stor, investeringskostnader_liten
):
    velfungerende_virkning.beregn(
        investeringskostnader_stor, investeringskostnader_liten
    )

    assert (velfungerende_virkning.verdsatt_netto.sum() <= 0).all()


def test_velfungerende_virkning_netto_null(velfungerende_virkning, investeringskostnader_stor):
    velfungerende_virkning.beregn(investeringskostnader_stor, investeringskostnader_stor)

    assert (velfungerende_virkning.verdsatt_netto.sum() == 0).all()


def test_virkning_feiler_tildig_investeringsaar(
    velfungerende_virkning, investeringskostnader_tidlig
):
    with pytest.raises(Exception):
        velfungerende_virkning.beregn(investeringskostnader_tidlig)

    assert True

def test_virkning_sprer_riktig(velfungerende_virkning, investeringskostnader_stor):
    velfungerende_virkning.beregn(investeringskostnader_stor)
    assert np.isclose(velfungerende_virkning.verdsatt_netto.values.sum(), investeringskostnader_stor['Forventningsverdi (kroner)'].sum()*-1)


def test_bakoverkompatibilitet(velfungerende_virkning, investeringskostnader_stor, investeringskostnader_ny_kolonne):
    velfungerende_virkning.beregn(investeringskostnader_stor)
    v1 = velfungerende_virkning.verdsatt_netto.copy()
    velfungerende_virkning.beregn(investeringskostnader_ny_kolonne)
    v2 = velfungerende_virkning.verdsatt_netto
    assert np.isclose((v1-v2).sum().sum(), 0)

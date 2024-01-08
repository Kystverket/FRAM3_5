from pathlib import Path

import pandas as pd
import pytest

from fram.generelle_hjelpemoduler.konstanter import FRAM_DIRECTORY
from fram.modell import Risiko
from fram.virkninger.risiko.hjelpemoduler import oljeutslipp
from fram.virkninger.risiko.hjelpemoduler.generelle import lag_konsekvensmatrise, hent_ut_konsekvensinput, \
    ARKNAVN_KONSEKVENSER_UTSLIPP
from fram.virkninger.risiko.hjelpemoduler.verdsetting import (
    get_kalkpris_materielle_skader,
    get_kalkpris_helse,
    get_kalkpris_oljeutslipp,
    get_kalkpris_opprenskingskostnader,
)

KRONEAAR = 2024
BEREGNINGSAAR = list(range(2026, 2037))
SLUTTAAR = 2100

EXCEL_INPUT_FILBANE = (
    FRAM_DIRECTORY / "eksempler" / "eksempel_analyser" / "Inputfiler" / "Strekning 11.xlsx"
)


@pytest.fixture
def velfungerende_virkning():
    tidskostnader = pd.read_json(
        Path(__file__).parent / "gyldige_kalkpriser_tid_2021.json"
    ).rename(columns=oljeutslipp._try_make_int).assign(Analysenavn="Test")
    kalkpriser_oljeutslipp = get_kalkpris_oljeutslipp(kroneaar=KRONEAAR, beregningsaar=BEREGNINGSAAR,
                                                        konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP)
    kalkpriser_oljeopprensking = get_kalkpris_opprenskingskostnader(
        kroneaar=KRONEAAR, beregningsaar=BEREGNINGSAAR, konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP
    )
    return Risiko(
        kalkpriser_materielle_skader=get_kalkpris_materielle_skader(
            kroneaar=KRONEAAR, beregningsaar=BEREGNINGSAAR, tidskostnader=tidskostnader,
        ),
        kalkpriser_helse=get_kalkpris_helse(kroneaar=KRONEAAR, siste_aar=SLUTTAAR),
        kalkpriser_oljeutslipp_ref=kalkpriser_oljeutslipp,
        kalkpriser_oljeutslipp_tiltak=kalkpriser_oljeutslipp,
        kalkpriser_oljeopprensking_ref=kalkpriser_oljeopprensking,
        kalkpriser_oljeopprensking_tiltak=kalkpriser_oljeopprensking,
        sarbarhet=pd.read_excel(
            EXCEL_INPUT_FILBANE, sheet_name="Sarbarhet", usecols=list(range(6))
        ),
        beregningsaar=BEREGNINGSAAR,
    )


def test_velfungerende_virkning(velfungerende_virkning):
    velfungerende_virkning
    assert True


def test_virkning_beregner(velfungerende_virkning, hendelser_ref, hendelser_tiltak, velfungerende_konsekvensmatrise):
    velfungerende_virkning.beregn(hendelser_ref=hendelser_ref, hendelser_tiltak=hendelser_tiltak, konsekvensmatrise_ref=velfungerende_konsekvensmatrise, konsekvensmatrise_tiltak=velfungerende_konsekvensmatrise)
    velfungerende_virkning.verdsatt_brutto_ref
    velfungerende_virkning.verdsatt_brutto_tiltak
    velfungerende_virkning.verdsatt_netto
    velfungerende_virkning.volumvirkning_ref
    velfungerende_virkning.volumvirkning_tiltak
    assert True


def test_virkning_beregner_bare_ref(velfungerende_virkning, hendelser_ref, velfungerende_konsekvensmatrise):
    velfungerende_virkning.beregn(hendelser_ref=hendelser_ref, konsekvensmatrise_ref=velfungerende_konsekvensmatrise)
    velfungerende_virkning.verdsatt_brutto_ref
    velfungerende_virkning.volumvirkning_ref
    assert True


def test_virkning_alternativt_oppsett():
    tidskostnader = pd.read_json(
        Path(__file__).parent / "gyldige_kalkpriser_tid_2021.json"
    ).rename(columns=oljeutslipp._try_make_int).assign(Analysenavn="Test")

    risiko = Risiko(
        beregningsaar=BEREGNINGSAAR,
        sarbarhet=pd.read_excel(
            EXCEL_INPUT_FILBANE, sheet_name="Sarbarhet", usecols=list(range(6))
        ),
        kroneaar=KRONEAAR,
        kalkpriser_tid=tidskostnader,
    )
    assert True

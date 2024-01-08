from io import BytesIO

import pandas as pd
import pytest

from fram.virkninger.risiko.hjelpemoduler.generelle import hent_ut_konsekvensinput, lag_konsekvensmatrise
from fram.virkninger.risiko.hjelpemoduler.konsekvensreduksjoner import les_inn_konsekvensmatriser

TP = 10
BERENGINGSAAR = list(range(2020, 2090))

@pytest.fixture
def standard_konsekvensinput():
    return hent_ut_konsekvensinput()

@pytest.fixture
def standard_konsekvensmatrise(standard_konsekvensinput):
    return lag_konsekvensmatrise(standard_konsekvensinput, BERENGINGSAAR)

@pytest.fixture
def gyldig_excelfil(standard_konsekvensinput):
    in_memory_fp = BytesIO()
    writer = pd.ExcelWriter(in_memory_fp)
    standard_konsekvensinput.to_excel(writer, sheet_name="Konsekvensinput referansebanen")
    standard_konsekvensinput.to_excel(writer, sheet_name=f"Konsekvensinput TP {TP}")
    writer.save()
    return pd.ExcelFile(in_memory_fp)

@pytest.fixture
def excelfil_uten_ref():
    standard_konsekvensinput = hent_ut_konsekvensinput()
    in_memory_fp = BytesIO()
    writer = pd.ExcelWriter(in_memory_fp)
    standard_konsekvensinput.to_excel(writer, sheet_name=f"Konsekvensinput TP {TP}")
    writer.save()
    return pd.ExcelFile(in_memory_fp)

@pytest.fixture
def excelfil_uten_tiltak():
    standard_konsekvensinput = hent_ut_konsekvensinput()
    in_memory_fp = BytesIO()
    writer = pd.ExcelWriter(in_memory_fp)
    standard_konsekvensinput.to_excel(writer, sheet_name="Konsekvensinput referansebanen")
    writer.save()
    return pd.ExcelFile(in_memory_fp)


def test_kan_lese_inn_fra_gyldig_excel(gyldig_excelfil, standard_konsekvensmatrise):
    (ref, tiltak) = les_inn_konsekvensmatriser(
        beregningsaar=BERENGINGSAAR,
        excel_inputfil=gyldig_excelfil,
        tiltakspakke=TP,)
    pd.testing.assert_frame_equal(ref, standard_konsekvensmatrise)
    pd.testing.assert_frame_equal(tiltak, standard_konsekvensmatrise)


def test_leser_inn_rett_ref_selv_naar_mangler(excelfil_uten_ref, standard_konsekvensmatrise):
    (ref, tiltak) = les_inn_konsekvensmatriser(
        beregningsaar=BERENGINGSAAR,
        excel_inputfil=excelfil_uten_ref,
        tiltakspakke=TP, )
    pd.testing.assert_frame_equal(ref, standard_konsekvensmatrise)
    pd.testing.assert_frame_equal(tiltak, standard_konsekvensmatrise)


def test_leser_inn_rett_tiltak_selv_naar_mangler(excelfil_uten_tiltak, standard_konsekvensmatrise):
    (ref, tiltak) = les_inn_konsekvensmatriser(
        beregningsaar=BERENGINGSAAR,
        excel_inputfil=excelfil_uten_tiltak,
        tiltakspakke=TP, )
    pd.testing.assert_frame_equal(ref, standard_konsekvensmatrise)
    pd.testing.assert_frame_equal(tiltak, standard_konsekvensmatrise)


def test_leser_inn_med_ulike_beregningsaar(gyldig_excelfil, standard_konsekvensinput):
    beregningsaar = list(range(200, 4000))
    (ref, tiltak) = les_inn_konsekvensmatriser(
        beregningsaar=beregningsaar,
        excel_inputfil=gyldig_excelfil,
        tiltakspakke=TP, )
    fasit = lag_konsekvensmatrise(standard_konsekvensinput, beregningsaar)
    pd.testing.assert_frame_equal(ref, fasit)
    pd.testing.assert_frame_equal(tiltak, fasit)

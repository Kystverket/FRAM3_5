"""
Test for SØA-modulen
"""
import pytest

from fram.modell import FRAM
from fram.generelle_hjelpemoduler.konstanter import FRAM_DIRECTORY, DelvisFRAMFeil

TEST_INPUT_DIRECTORY = FRAM_DIRECTORY.parent / "tests" / "input"
RA_DIR = FRAM_DIRECTORY / "eksempler" / "risikoanalyser"

def test_fram_feiler_uten_trafikk():
    with pytest.raises(DelvisFRAMFeil):
        strekningsfil = TEST_INPUT_DIRECTORY / "strekning 11 ingen trafikk.xlsx"
        modell = FRAM(
            strekningsfil,
            tiltakspakke=11,
            les_RA_paa_nytt=False,
            ra_dir=RA_DIR,
        )
        modell.run(skriv_output=False)


def test_delvis_fram_ok_uten_trafikk():
    strekningsfil = TEST_INPUT_DIRECTORY / "strekning 11 ingen trafikk.xlsx"
    modell = FRAM(
        strekningsfil,
        tiltakspakke=11,
        les_RA_paa_nytt=False,
        ra_dir=RA_DIR,
        delvis_fram=True,
    )
    modell.run(skriv_output=False)
    modell.kontantstrommer()


def test_fram_feiler_uten_trafikkark():
    with pytest.raises(DelvisFRAMFeil):
        strekningsfil = TEST_INPUT_DIRECTORY / "strekning 11 ingen trafikk-ark.xlsx"
        modell = FRAM(
            strekningsfil,
            tiltakspakke=11,
            les_RA_paa_nytt=False,
            ra_dir=RA_DIR,
        )
        modell.run(skriv_output=False)


def test_delvis_fram_ok_uten_trafikkark():
    strekningsfil = TEST_INPUT_DIRECTORY / "strekning 11 ingen trafikk-ark.xlsx"
    modell = FRAM(
        strekningsfil,
        tiltakspakke=11,
        les_RA_paa_nytt=False,
        ra_dir=RA_DIR,
        delvis_fram=True,
    )
    modell.run(skriv_output=False)
    modell.kontantstrommer()


def test_fram_feiler_uten_tidsbesparelser():
    with pytest.raises(DelvisFRAMFeil):
        strekningsfil = TEST_INPUT_DIRECTORY / "strekning 11 ingen tidsbesparelser.xlsx"
        modell = FRAM(
            strekningsfil,
            tiltakspakke=11,
            les_RA_paa_nytt=False,
            ra_dir=RA_DIR,
        )
        modell.run(skriv_output=False)


def test_delvis_fram_ok_uten_tidsbesparelser():
    strekningsfil = TEST_INPUT_DIRECTORY / "strekning 11 ingen tidsbesparelser.xlsx"
    modell = FRAM(
        strekningsfil,
        tiltakspakke=11,
        les_RA_paa_nytt=False,
        ra_dir=RA_DIR,
        delvis_fram=True,
    )
    modell.run(skriv_output=False)
    modell.kontantstrommer()


def test_fram_feiler_uten_drivstoffkostnader():
    with pytest.raises(DelvisFRAMFeil):
        strekningsfil = TEST_INPUT_DIRECTORY / "strekning 11 ingen drivstoff.xlsx"
        modell = FRAM(
            strekningsfil,
            tiltakspakke=11,
            les_RA_paa_nytt=False,
            ra_dir=RA_DIR,
        )
        modell.run(skriv_output=False)


def test_delvis_fram_ok_uten_drivstoffkostnader():
    strekningsfil = TEST_INPUT_DIRECTORY / "strekning 11 ingen drivstoff.xlsx"
    modell = FRAM(
        strekningsfil,
        tiltakspakke=11,
        les_RA_paa_nytt=False,
        ra_dir=RA_DIR,
        delvis_fram=True,
    )
    modell.run(skriv_output=False)
    modell.kontantstrommer()


def test_fram_feiler_uten_investeringsark():
    with pytest.raises(DelvisFRAMFeil):
        strekningsfil = (
            TEST_INPUT_DIRECTORY
            / "strekning 11 ingen drivstoff ingen investering-ark.xlsx"
        )
        modell = FRAM(
            strekningsfil,
            tiltakspakke=11,
            les_RA_paa_nytt=False,
            ra_dir=RA_DIR,
        )
        modell.run(skriv_output=False)


def test_delvis_fram_ok_uten_investeringsark():
    strekningsfil = (
        TEST_INPUT_DIRECTORY / "strekning 11 ingen drivstoff ingen investering-ark.xlsx"
    )
    modell = FRAM(
        strekningsfil,
        tiltakspakke=11,
        les_RA_paa_nytt=False,
        ra_dir=RA_DIR,
        delvis_fram=True,
    )
    modell.run(skriv_output=False)
    modell.kontantstrommer()


@pytest.mark.parametrize(
    "strekningsfil",
    [
        (TEST_INPUT_DIRECTORY / "strekning 11 ingen risiko.xlsx"),
        (TEST_INPUT_DIRECTORY / "strekning 11 ingen risiko-ark.xlsx"),
    ],
)
def test_fram_feiler_uten_risiko(strekningsfil):
    with pytest.raises(DelvisFRAMFeil):
        modell = FRAM(
            strekningsfil,
            tiltakspakke=11,
            les_RA_paa_nytt=False,
            ra_dir=RA_DIR,
        )
        modell.run(skriv_output=False)


@pytest.mark.parametrize(
    "strekningsfil",
    [
        (TEST_INPUT_DIRECTORY / "strekning 11 ingen risiko.xlsx"),
        (TEST_INPUT_DIRECTORY / "strekning 11 ingen risiko-ark.xlsx"),
    ],
)
def test_delvis_fram_ok_uten_risiko(strekningsfil):
    modell = FRAM(
        strekningsfil,
        tiltakspakke=11,
        les_RA_paa_nytt=False,
        ra_dir=RA_DIR,
        delvis_fram=True,
    )
    modell.run(skriv_output=False)
    modell.kontantstrommer()


def test_delvis_fram_anleggsutslipp_uten_traifkk():
    strekningsfil = (TEST_INPUT_DIRECTORY / "strekning 11 anleggsutslipp.xlsx")
    modell = FRAM(
        strekningsfil,
        tiltakspakke=11,
        les_RA_paa_nytt=False,
        ra_dir=RA_DIR,
        delvis_fram=True,
    )
    modell.run(skriv_output=False)
    assert modell.kontantstrommer().reset_index().loc[
        lambda df: df.Virkninger == 'Endring i globale utslipp til luft - anleggsfasen', "Nåverdi levetid"].values[0] < 0

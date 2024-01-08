from unittest.mock import Mock

import pandas as pd
import pytest

from fram.generelle_hjelpemoduler.konstanter import FRAM_DIRECTORY
from fram.virkninger.risiko.hjelpemoduler.generelle import les_inn_hvilke_ra_som_brukes_fra_fram_input
from fram.virkninger.risiko.hjelpemoduler.iwrap_innlesing import Risikoanalyser

RA_DIR = (
    FRAM_DIRECTORY / "eksempler" / "risikoanalyser"
)  # mappen risikoanalyser i fram/eksempler
INPUT_FILBANE = (
    FRAM_DIRECTORY / "eksempler" / "eksempel_analyser" / "Inputfiler" / "Strekning 11.xlsx"
)  # filen 'Strekning 11.xlsx' i fram/eksempel_analyser/Inputfiler


@pytest.fixture()
def ra_ref():
    return pd.read_json(
        '{"Strekning":{"0":"Strekning 11","1":"Strekning 11","2":"Strekning 11","3":"Strekning 11","4":"Strekning 11","5":"Strekning 11","6":"Strekning 11","7":"Strekning 11","8":"Strekning 11","9":"Strekning 11","10":"Strekning 11","11":"Strekning 11"},"Tiltaksomraade":{"0":1,"1":1,"2":1,"3":1,"4":1,"5":1,"6":1,"7":1,"8":1,"9":1,"10":1,"11":1},"Tiltakspakke":{"0":11,"1":11,"2":11,"3":11,"4":11,"5":11,"6":11,"7":11,"8":11,"9":11,"10":11,"11":11},"Analyseomraade":{"0":"1_1","1":"1_1","2":"1_1","3":"1_1","4":"1_1","5":"1_1","6":"1_2","7":"1_2","8":"1_2","9":"1_2","10":"1_3","11":"1_3"},"Rute":{"0":"A","1":"A","2":"B","3":"B","4":"C","5":"C","6":"D","7":"D","8":"E","9":"E","10":"F","11":"F"},"Risikoanalyse":{"0":"risiko_1_1_A0_2017","1":"risiko_1_1_A0_2050","2":"risiko_1_1_A0_2017","3":"risiko_1_1_A0_2050","4":"risiko_1_1_A0_2017","5":"risiko_1_1_A0_2050","6":"risiko_1_2_A0_2017","7":"risiko_1_2_A0_2050","8":"risiko_1_2_A0_2017","9":"risiko_1_2_A0_2050","10":"risiko_1_3_A0_2017","11":"risiko_1_3_A0_2050"},"ra_aar":{"0":2017,"1":2050,"2":2017,"3":2050,"4":2017,"5":2050,"6":2017,"7":2050,"8":2017,"9":2050,"10":2017,"11":2050}}',
        dtype={"Analyseomraade": str},
    )


@pytest.fixture()
def ra_tiltak():
    return pd.read_json(
        '{"Strekning":{"0":"Strekning 11","1":"Strekning 11","2":"Strekning 11","3":"Strekning 11","4":"Strekning 11","5":"Strekning 11","6":"Strekning 11","7":"Strekning 11","8":"Strekning 11","9":"Strekning 11","10":"Strekning 11","11":"Strekning 11"},"Tiltaksomraade":{"0":1,"1":1,"2":1,"3":1,"4":1,"5":1,"6":1,"7":1,"8":1,"9":1,"10":1,"11":1},"Tiltakspakke":{"0":11,"1":11,"2":11,"3":11,"4":11,"5":11,"6":11,"7":11,"8":11,"9":11,"10":11,"11":11},"Analyseomraade":{"0":"1_1","1":"1_1","2":"1_1","3":"1_1","4":"1_1","5":"1_1","6":"1_2","7":"1_2","8":"1_2","9":"1_2","10":"1_3","11":"1_3"},"Rute":{"0":"A","1":"A","2":"B","3":"B","4":"C","5":"C","6":"D","7":"D","8":"E","9":"E","10":"F","11":"F"},"Risikoanalyse":{"0":"risiko_1_1_A1_2017","1":"risiko_1_1_A1_2050","2":"risiko_1_1_A1_2017","3":"risiko_1_1_A1_2050","4":"risiko_1_1_A1_2017","5":"risiko_1_1_A1_2050","6":"risiko_1_2_A1_2017","7":"risiko_1_2_A1_2050","8":"risiko_1_2_A1_2017","9":"risiko_1_2_A1_2050","10":"risiko_1_3_A1_2017","11":"risiko_1_3_A1_2050"},"ra_aar":{"0":2017,"1":2050,"2":2017,"3":2050,"4":2017,"5":2050,"6":2017,"7":2050,"8":2017,"9":2050,"10":2017,"11":2050},"RA_trafikkgrunnlag":{"0":"referanse","1":"referanse","2":"referanse","3":"referanse","4":"referanse","5":"referanse","6":"referanse","7":"referanse","8":"referanse","9":"referanse","10":"referanse","11":"referanse"}}',
        dtype={"Analyseomraade": str},
    )


@pytest.fixture()
def iwrap_reader_full():
    return Risikoanalyser(ra_dir=RA_DIR, logger=Mock(), les_paa_nytt=True)


@pytest.fixture()
def iwrap_reader_cached():
    return Risikoanalyser(ra_dir=RA_DIR, logger=Mock(), les_paa_nytt=False)


def test_innlesing_cached(ra_ref, ra_tiltak, iwrap_reader_cached):
    """ Tester at iwrap-innleseren finner frem til de riktige RA-navnene fra FRAM-inputarket """
    tiltakspakke = 11
    (
        innlest_ra_ref,
        innlest_ra_tiltak,
    ) = les_inn_hvilke_ra_som_brukes_fra_fram_input(
        filbane=INPUT_FILBANE, tiltakspakke=tiltakspakke
    )
    pd.testing.assert_frame_equal(ra_ref, innlest_ra_ref, check_dtype=False)
    pd.testing.assert_frame_equal(ra_tiltak, innlest_ra_tiltak, check_dtype=False)


def test_innlesing_uncached(ra_ref, ra_tiltak, iwrap_reader_full):
    """ Tester at iwrap-innleseren finner frem til de riktige RA-navnene fra FRAM-inputarket """
    tiltakspakke = 11
    (
        innlest_ra_ref,
        innlest_ra_tiltak,
    ) = les_inn_hvilke_ra_som_brukes_fra_fram_input(
        filbane=INPUT_FILBANE, tiltakspakke=tiltakspakke
    )
    pd.testing.assert_frame_equal(ra_ref, innlest_ra_ref, check_dtype=False)
    pd.testing.assert_frame_equal(ra_tiltak, innlest_ra_tiltak, check_dtype=False)


def test_hent_ra_resultater_ref(ra_ref, risiko_ref, iwrap_reader_cached):
    risiko = iwrap_reader_cached.hent_ra_resultater(ra_ref).assign(
        _merge=lambda df: df._merge.astype(str)
    ).assign(Analysenavn="Test")
    pd.testing.assert_frame_equal(risiko_ref, risiko)


def test_hent_ra_resultater_tiltak(ra_ref, risiko_ref, iwrap_reader_cached):
    risiko = iwrap_reader_cached.hent_ra_resultater(ra_ref).assign(
        _merge=lambda df: df._merge.astype(str)
    ).assign(Analysenavn="Test")
    pd.testing.assert_frame_equal(risiko_ref, risiko)

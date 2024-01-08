from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fram.virkninger.risiko.hjelpemoduler import oljeutslipp
from fram.virkninger.risiko.hjelpemoduler.generelle import ARKNAVN_KONSEKVENSER_UTSLIPP
from fram.virkninger.risiko.hjelpemoduler.verdsetting import (
    _verdi_per_skade_mennesker,
    get_kalkpris_helse,
    get_kalkpris_opprenskingskostnader,
    get_kalkpris_oljeutslipp,
    get_kalkpris_materielle_skader,
)

CURRENT_DIR = Path(__file__).parent

# For å gjenskape disse, kjør get_kalkpris_helse(fra, til).to_json(), der de to årene er gitt i variabelnavnet. Ny oppdatering fra Kystverket der kroneår i kalkprisene for vsl og personskader er satt til 2024, kan vi bare teste fra 2024.  

get_kalkpris_helse_2024_2030 = '{"2024":{"Dodsfall":56660000.0,"Personskade":5659174.0},"2025":{"Dodsfall":57169939.9999999925,"Personskade":5710106.5659999996},"2026":{"Dodsfall":57684469.459999986,"Personskade":5761497.5250939988},"2027":{"Dodsfall":58203629.6851399764,"Personskade":5813351.0028198445},"2028":{"Dodsfall":58727462.3523062319,"Personskade":5865671.1618452221},"2029":{"Dodsfall":59256009.5134769827,"Personskade":5918462.2023018282}}'

# get_kalkpris_materielle_skader(2021, list(range(2026, 2101)), tidskostnader=pd.read_json(CURRENT_DIR / "gyldige_kalkpriser_tid_2021.json").rename(columns=oljeutslipp._try_make_int).assign(Analysenavn="Test")).reset_index().to_json("kalkpriser_materielle_skader_2021.json")
# get_kalkpris_opprenskingskostnader(kroneaar=2021, beregningsaar=list(range(2020, 2101)), konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP).to_json("kalkpris_opprensking_2021.json")

@pytest.mark.parametrize(
    "kroneaar, siste_aar, fasit",
    [
        (2024, 2030, get_kalkpris_helse_2024_2030),
    ],
)
def test_get_kalkpris_helse(kroneaar, siste_aar, fasit):
    fasit_df = pd.read_json(fasit)
    fasit_df.index.name = "Konsekvens"
    pd.testing.assert_frame_equal(
        fasit_df.astype(float), get_kalkpris_helse(kroneaar, siste_aar)
    )

def test_feilår_vsl():
    with pytest.raises(ValueError):
        _verdi_per_skade_mennesker("Dødsfall",2027)


#Denne testen har tidligere testet oppjusterer av priser, men oppdatering 10.08 gjør at denne kun kan teste 2024-kroner for VSL. Det er ikke mulig å regne ut VSL i andre kroner  
@pytest.mark.parametrize(
    "omfang, tilaar, fasit",
    [
        ("Dødsfall", 2024, 56660000.0),
        #("Dødsfall", 2025, 57169939.9999999925),
        #("Dødsfall", 2026, 57684469.459999986),
        #("Dødsfall", 2027, 58203629.6851399764),
        #("Dødsfall", 2028, 58727462.3523062319),
        #("Dødsfall", 2029, 59256009.5134769827),
        ("Personskade", 2024, 5659174.0),
        #("Personskade", 2025, 5710106.5659999996),
        #("Personskade", 2026, 5761497.5250939988),
        #("Personskade", 2027, 5813351.0028198445),
        #("Personskade", 2028, 5865671.1618452221),
        #("Personskade", 2029, 5918462.2023018282),
    ],
)
def test_verdi_per_skade_mennesker(omfang, tilaar, fasit):
    assert np.isclose(_verdi_per_skade_mennesker(omfang, tilaar), fasit)


@pytest.mark.parametrize(
    "kroneaar, beregningsaar",
    [(2021, list(range(2020, 2101))), (2019, list(range(2020, 2101)))],
)
def test_get_kalkpris_opprenskingskostnader(kroneaar, beregningsaar):
    fasit = pd.read_json(CURRENT_DIR / f"kalkpris_opprensking_{kroneaar}.json").rename(
        columns=oljeutslipp._try_make_int
    )
    beregnet = get_kalkpris_opprenskingskostnader(kroneaar=kroneaar, beregningsaar=beregningsaar, konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP)
    pd.testing.assert_frame_equal(fasit, beregnet)


def test_get_kalkpris_oljeutslippskostnader():
    fasit = pd.read_json(CURRENT_DIR / "kalkpris_oljeutslipp_2020.json").rename(
        columns=oljeutslipp._try_make_int
    )
    beregnet = get_kalkpris_oljeutslipp(kroneaar=2020, beregningsaar=list(range(2026, 2101)), konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP)
    pd.testing.assert_frame_equal(fasit, beregnet)


def test_get_kalkpris_oljeutslippskostnader():
    tidskostnader = pd.read_json(
        CURRENT_DIR / "gyldige_kalkpriser_tid_2021.json"
    ).rename(columns=oljeutslipp._try_make_int).assign(Analysenavn="Test")
    fasit = (
        pd.read_json(CURRENT_DIR / "kalkpriser_materielle_skader_2021.json")
        .rename(columns=oljeutslipp._try_make_int)
        .assign(Analysenavn="Test")
        .set_index(["Skipstype", "Lengdegruppe", "Hendelsestype"])
    )
    beregnet = get_kalkpris_materielle_skader(2021, list(range(2026, 2101)), tidskostnader=pd.read_json(CURRENT_DIR / "gyldige_kalkpriser_tid_2021.json").rename(columns=oljeutslipp._try_make_int).assign(Analysenavn="Test"))
    pd.testing.assert_frame_equal(fasit, beregnet)

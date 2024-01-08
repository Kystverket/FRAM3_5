"""
For 'konverter_aisyrisk_lengdegrupper':
1. At jeg kan summere hendelser i input og output og se at de er like mange
2. At seilingstid og utseilt distanse er likt i input og output

For fremskrivingen:
1. At output har de samme hendelsene i RA-aaret som inputen
2. At ved konstant trafikk finner jeg like mange hendelser i hvert år
3. At dersom trafikken skaleres med en faktor K, endrer antall hendelser seg med en faktor K
"""
import functools
from pathlib import Path

import pandas as pd
import numpy as np
import pytest

from fram.generelle_hjelpemoduler.konstanter import FRAM_DIRECTORY, FOLSOMHET_KOLONNE
from fram.virkninger.risiko.hjelpemoduler.aisyrisk import konverter_aisyrisk_lengdegrupper, STRIKING_COLUMNS, \
    STRUCK_COLUMNS, GRUNNSTØTING_COLUMNS, fordel_og_fremskriv_ra, _stable_folsomhetsanalyse
from fram.virkninger.risiko.hjelpemoduler.generelle import les_inn_hvilke_ra_som_brukes_fra_fram_input

filnavn = ["Base_VTS.csv", "Base_VTS2.csv", "Base_VTS3.csv"]
kolonnemappere = {
    "striking": STRIKING_COLUMNS,
    "struck": STRUCK_COLUMNS,
    "grunnstøting": GRUNNSTØTING_COLUMNS
}
utseilt_kolonner = ["Sailed_time_hours", "Sailed_distance_nm"]

PATH_TO_FILE = Path(__file__).parent


@functools.lru_cache
def _les_inn_ra(filnavn):
    return pd.read_csv(FRAM_DIRECTORY / "eksempler" / "eksempel_analyser" / "RA" / filnavn, sep=";")


def _legg_til_kolonne(df, kolonnenavn, verdi):
    if callable(verdi):
        df[kolonnenavn] = verdi(df)
    else:
        df[kolonnenavn] = verdi
    return df


def test_innlesing_ra():
    filbane = FRAM_DIRECTORY / "eksempler" / "eksempel_analyser" / "Inputfiler" / "Strekning 14.xlsx"
    types = dict(
        Tiltaksomraade=np.int64,
        Tiltakspakke=np.int64,
        ra_aar=np.int64)

    (ra_ref, ra_tiltak) = les_inn_hvilke_ra_som_brukes_fra_fram_input(filbane=filbane, tiltakspakke=11, arknavn="Aisyrisk referansebanen")
    fasit_ra_ref = pd.read_json(PATH_TO_FILE / "aisyrisk_ra_ref_strekning_11_11.json", dtype={"Analyseomraade": str})
    fasit_ra_tiltak = pd.read_json(PATH_TO_FILE / "aisyrisk_ra_tiltak_strekning_11_11.json", dtype={"Analyseomraade": str})
    pd.testing.assert_frame_equal(ra_ref.astype(types), fasit_ra_ref.astype(types))
    pd.testing.assert_frame_equal(ra_tiltak.astype(types), fasit_ra_tiltak.astype(types))


@pytest.mark.parametrize("aisyrisk_ra_navn, kolonner_raw, kolonne_konvertert", [
    (fil, kolonner_raw, kolonne_konvertert) for kolonne_konvertert, kolonner_raw in kolonnemappere.items() for fil in filnavn
])
def test_konverter_aisyrisk_lengdegrupper_like_mange_hendelser_input_output(aisyrisk_ra_navn, kolonner_raw, kolonne_konvertert):
    raw = _les_inn_ra(aisyrisk_ra_navn)
    konvertert = konverter_aisyrisk_lengdegrupper(raw, kast_ut_andre_skipstyper=False, kast_ut_mangler_lengde=False)
    hendelser_raw = raw[kolonner_raw].sum().sum()
    if kolonne_konvertert in ["striking", "struck"]:
        hendelser_raw /= 2
    hendelser_konvertert = konvertert[kolonne_konvertert].sum()
    assert np.isclose(hendelser_raw, hendelser_konvertert)


@pytest.mark.parametrize("aisyrisk_ra_navn, utseilt_kolonne", [
    (fil, kolonne) for kolonne in utseilt_kolonner for fil in filnavn

])
def test_konverter_aisyrisk_lengdegrupper_utseilt_likt_etter_konvertering(aisyrisk_ra_navn, utseilt_kolonne):
    raw = _les_inn_ra(aisyrisk_ra_navn)
    konvertert = konverter_aisyrisk_lengdegrupper(raw, kast_ut_andre_skipstyper=False, kast_ut_mangler_lengde=False, returner_alle_kolonner=True)
    utseilt_raw = raw[utseilt_kolonne].sum()
    utseilt_konvertert = konvertert[utseilt_kolonne].sum()
    assert np.isclose(utseilt_raw, utseilt_konvertert)


@pytest.mark.parametrize("aisyrisk_ra_navn, kolonne_beregnet", [
    (fil, kolonne) for kolonne in kolonnemappere.keys() for fil in filnavn
])
def test_fordel_og_fremskriv_ra_like_mange_hendelser_input_output(aisyrisk_ra_navn, kolonne_beregnet):
    raw = _les_inn_ra(aisyrisk_ra_navn)
    konvertert = konverter_aisyrisk_lengdegrupper(raw)
    analyseomraade, rute, ra_aar = "1_1", "A", 2019
    trafikk = (
        konvertert
        .reset_index()
        [["Skipstype", "Lengdegruppe"]]
        .assign(
            Analyseomraade=analyseomraade,
            Rute=rute,
            Strekning="A",
            Tiltaksomraade="B",
            Tiltakspakke=11,
            Analysenavn="Dummy"
                )
        .pipe(_legg_til_kolonne, ra_aar, 1)
        .pipe(_legg_til_kolonne, ra_aar+1, 1)
        .set_index(["Strekning", "Tiltaksomraade", "Tiltakspakke", "Analyseomraade", "Rute", "Analysenavn", "Skipstype", "Lengdegruppe"])
    )
    beregnet = fordel_og_fremskriv_ra(konvertert, trafikk=trafikk, beregningsaar=[ra_aar, ra_aar + 1], risikoanalyseaar=ra_aar, risiko_logger=print)
    fasit = konvertert[kolonne_beregnet].sum()
    beregnet_hendelser_ra_aar = beregnet.groupby("Hendelsestype")[ra_aar].sum().to_dict()[kolonne_beregnet.title()]
    assert np.isclose(fasit, beregnet_hendelser_ra_aar)


@pytest.mark.parametrize("aisyrisk_ra_navn, kolonne_beregnet, vekstfaktor", [
    (fil, kolonne, faktor) for faktor in [0, 1, 2, 3, 5] for kolonne in kolonnemappere.keys() for fil in filnavn
])
def test_fordel_og_fremskriv_ra_vekstfaktor_hendelser_lik_vekstfaktor_trafikk(aisyrisk_ra_navn, kolonne_beregnet, vekstfaktor):
    raw = _les_inn_ra(aisyrisk_ra_navn)
    konvertert = konverter_aisyrisk_lengdegrupper(raw)
    analyseomraade, rute, ra_aar = "1_1", "A", 2019
    trafikk = (
        konvertert
        .reset_index()
        [["Skipstype", "Lengdegruppe"]]
        .assign(
            Analyseomraade=analyseomraade,
            Rute=rute,
            Strekning="A",
            Tiltaksomraade="B",
            Tiltakspakke=11,
            Analysenavn="Dummy"
                )
        .pipe(_legg_til_kolonne, ra_aar, 1)
        .pipe(_legg_til_kolonne, ra_aar+1, vekstfaktor)
        .set_index(["Strekning", "Tiltaksomraade", "Tiltakspakke", "Analyseomraade", "Rute", "Analysenavn", "Skipstype", "Lengdegruppe"])
    )
    beregnet = fordel_og_fremskriv_ra(konvertert, trafikk=trafikk, beregningsaar=[ra_aar, ra_aar+1], risikoanalyseaar=ra_aar, risiko_logger=print)
    fasit = konvertert[kolonne_beregnet].sum() * vekstfaktor
    beregnet_hendelser_ra_aar = beregnet.groupby("Hendelsestype")[ra_aar+1].sum().to_dict()[kolonne_beregnet.title()]
    assert np.isclose(fasit, beregnet_hendelser_ra_aar)


@pytest.mark.parametrize("aisyrisk_ra_navn, kolonne_beregnet, _from, _to", [
    (fil, kolonne, _from, _to) for kolonne in kolonnemappere.keys() for fil in filnavn for _from in [0, 1, 4] for _to in [-3, -4, -1]
])
def test_fordel_og_fremskriv_ra_hendelser_uten_trafikk_spres_til_resten(aisyrisk_ra_navn, kolonne_beregnet, _from, _to):
    raw = _les_inn_ra(aisyrisk_ra_navn)
    konvertert = konverter_aisyrisk_lengdegrupper(raw)
    analyseomraade, rute, ra_aar = "1_1", "A", 2019
    folsomheter = ["Dummy1", "Dummy2", "Dummy3"]
    trafikk = (
        konvertert
        .reset_index()
        [["Skipstype", "Lengdegruppe"]]
        .assign(
            Analyseomraade=analyseomraade,
            Rute=rute,
            Strekning="A",
            Tiltaksomraade="B",
            Tiltakspakke=11,
        )
        .pipe(
            _stable_folsomhetsanalyse,
            folsomheter=folsomheter,
            folsomhetsnavn=FOLSOMHET_KOLONNE
        )
        .pipe(_legg_til_kolonne, ra_aar, 1)
        .pipe(_legg_til_kolonne, ra_aar + 1, 1)
        .set_index(["Strekning", "Tiltaksomraade", "Tiltakspakke", "Analyseomraade", "Rute", "Analysenavn", "Skipstype",
                    "Lengdegruppe"])
        .iloc[_from:_to] # Fjerner noen rader med trafikk for å se om fremskrivingen fortsatt gir riktig antall hendelser.
    )
    assert len(trafikk) > 0
    beregnet = fordel_og_fremskriv_ra(konvertert, trafikk=trafikk, beregningsaar=[ra_aar, ra_aar + 1],
                                      risikoanalyseaar=ra_aar, risiko_logger=print)
    fasit = konvertert[kolonne_beregnet].sum() * len(folsomheter)
    beregnet_hendelser_ra_aar = beregnet.groupby("Hendelsestype")[ra_aar].sum().to_dict()[kolonne_beregnet.title()]
    assert np.isclose(fasit, beregnet_hendelser_ra_aar)


@pytest.mark.parametrize("df, folsomheter, folsomhetsnavn", [
    (pd.util.testing.makeDataFrame(), ["abc", 123, "asd", 'aeasd'], 'folsomhetsnavn'),
    (pd.util.testing.makeDataFrame(), ["abc"], 'folsomhetsnavnasdas'),
    (pd.util.testing.makeDataFrame(), [123, 124, 54232], 123),
])
def test_stable_folsomhetsanalyse(df, folsomheter, folsomhetsnavn):
    stablet = _stable_folsomhetsanalyse(df, folsomheter, folsomhetsnavn)
    opprinnelig_lengde = len(df)
    antall_dfs = len(folsomheter)
    gjentakelser = stablet[folsomhetsnavn].value_counts()

    assert len(stablet) == antall_dfs * opprinnelig_lengde
    assert folsomhetsnavn in stablet.columns
    for folsom in folsomheter:
        assert folsom in gjentakelser.index

import numpy as np
import pandas as pd
import pytest

from fram.generelle_hjelpemoduler.konstanter import SKATTEFINANSIERINGSKOSTNAD
from fram.virkninger.kontantstrommer.virkning import Kontantstrommer


@pytest.fixture
def kontantstrom_stor():
    return (
        pd.DataFrame(
            np.ones((5, 75)) * np.arange(1, 6).reshape((5, 1)) * 1e4,
            columns=range(2026, 2101),
        )
        .assign(Kroneverdi=2019)
        .assign(Tiltakspakke=11)
        .assign(Navn=[f"inv_{i}" for i in range(5)])
        .assign(Aktør='Ikke kategorisert')
        .set_index("Navn")
    )


@pytest.fixture
def kontantstrom_liten():
    return (
        pd.DataFrame(
            np.ones((5, 75)) * np.arange(1, 6).reshape((5, 1)) * 1e3,
            columns=range(2026, 2101),
            index=[f"inv_{i}" for i in range(5)],
        )
        .assign(Kroneverdi=2019)
        .assign(Tiltakspakke=11)
        .assign(Navn=[f"inv_{i}" for i in range(5)])
        .assign(Aktør='Ikke kategorisert')
        .set_index("Navn")
    )


@pytest.fixture
def kontantstrom_ugyldig_kroneverdi():
    return (
        pd.DataFrame(
            np.ones((5, 75)) * np.arange(1, 6).reshape((5, 1)) * 1e4,
            columns=range(2026, 2101),
            index=[f"inv_{i}" for i in range(5)],
        )
        .assign(Kroneverdi=2019)
        .assign(Tiltakspakke=11)
        .assign(Navn=[f"inv_{i}" for i in range(5)])
        .assign(Aktør='Ikke kategorisert')
        .set_index("Navn")
    )


@pytest.fixture
def kontantstrom_med_skattekost(kontantstrom_liten):
    kontantstrom_liten["Andel skattefinansieringskostnad"] = 0
    return kontantstrom_liten


def test_velfungerende_virkning(kontantstrom_stor, kontantstrom_liten):
    v = Kontantstrommer(beregningsaar=range(2026, 2101), kroneaar=2020)
    v.beregn(
        ytterlige_kontantstrommer_tiltak=kontantstrom_liten,
        ytterlige_kontantstrommer_ref=kontantstrom_stor,
    )
    assert True


def test_null_virkning(kontantstrom_stor):
    v = Kontantstrommer(beregningsaar=range(2026, 2101), kroneaar=2020)
    v.beregn(
        ytterlige_kontantstrommer_tiltak=kontantstrom_stor,
        ytterlige_kontantstrommer_ref=kontantstrom_stor,
    )
    assert v.verdsatt_netto.sum().sum() == 0


def test_uten_skattefinansieringskostnad(kontantstrom_liten):
    v = Kontantstrommer(beregningsaar=list(range(2026, 2101)), kroneaar=2020)
    v.beregn(
        ytterlige_kontantstrommer_ref=kontantstrom_liten,
        ytterlige_kontantstrommer_tiltak=kontantstrom_liten,
    )
    assert v.verdsatt_netto.reset_index()[SKATTEFINANSIERINGSKOSTNAD].sum() == 0


def test_med_skattefinansieringskostnad(kontantstrom_med_skattekost):
    v = Kontantstrommer(beregningsaar=list(range(2026, 2101)), kroneaar=2020)
    v.beregn(
        ytterlige_kontantstrommer_ref=kontantstrom_med_skattekost,
        ytterlige_kontantstrommer_tiltak=kontantstrom_med_skattekost,
    )
    assert v.verdsatt_netto.reset_index()[SKATTEFINANSIERINGSKOSTNAD].sum() == 0

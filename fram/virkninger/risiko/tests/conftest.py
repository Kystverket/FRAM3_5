from pathlib import Path

import pandas as pd
import pandera as pa
import numpy as np
import pytest
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.konstanter import FOLSOMHET_COLS
from fram.virkninger.felles_hjelpemoduler.schemas import (
    verbose_schema_error,
)
from fram.virkninger.risiko.hjelpemoduler.generelle import lag_konsekvensmatrise, hent_ut_konsekvensinput
from fram.virkninger.risiko.schemas import HendelseSchema, KonsekvensmatriseSchema


BEREGNINGSAAR = list(range(2026, 2037))


@pytest.fixture()
def rute_til_ra():
    return {
        "A": "risiko_1_1_A0_2017",
        "B": "risiko_1_1_A0_2017",
        "C": "risiko_1_1_A0_2017",
        "D": "risiko_1_2_A0_2017",
        "E": "risiko_1_2_A0_2017",
        "F": "risiko_1_3_A0_2017",
    }


@pytest.fixture()
def risiko_ref():
    return pd.read_json(
        Path(__file__).parent / "risiko_ref.json", dtype={"Analyseomraade": str},
    ).assign(Analysenavn="Test")


@pytest.fixture()
def risiko_tiltak():
    return pd.read_json(
        Path(__file__).parent / "risiko_tiltak.json", dtype={"Analyseomraade": str},
    ).assign(Analysenavn="Test")


@verbose_schema_error
@pa.check_types(lazy=True)
@pytest.fixture()
def hendelser_ref() -> DataFrame[HendelseSchema]:
    return (
        pd.read_json(
            Path(__file__).parent / "hendelser_ref.json", dtype={"Analyseomraade": str},
        )
        .assign(Analysenavn="Test")
        .set_index(FOLSOMHET_COLS + ["Risikoanalyse", "Hendelsestype"])
        .rename(columns=lambda col: int(col))
    )


@verbose_schema_error
@pa.check_types(lazy=True)
@pytest.fixture()
def hendelser_tiltak() -> DataFrame[HendelseSchema]:
    return (
        pd.read_json(
            Path(__file__).parent / "hendelser_tiltak.json",
            dtype={"Analyseomraade": str},
        )
        .assign(Analysenavn="Test")
        .set_index(FOLSOMHET_COLS + ["Risikoanalyse", "Hendelsestype"])
        .rename(columns=lambda col: int(col))
    )

@verbose_schema_error
@pa.check_types(lazy=True)
@pytest.fixture
def velfungerende_konsekvensmatrise() -> DataFrame[KonsekvensmatriseSchema]:
    return lag_konsekvensmatrise(hent_ut_konsekvensinput(), BEREGNINGSAAR)


@verbose_schema_error
@pa.check_types(lazy=True)
@pytest.fixture
def konsekvensmatrise_bare_1(velfungerende_konsekvensmatrise) -> DataFrame[KonsekvensmatriseSchema]:
    input = velfungerende_konsekvensmatrise.copy()
    return pd.DataFrame(np.ones(input.values.shape), index=input.index, columns=input.columns)
import pandas as pd
import pytest
from pandera import SchemaModel

from fram.generelle_hjelpemoduler.konstanter import TRAFIKK_COLS, FOLSOMHET_KOLONNE
from fram.generelle_hjelpemoduler.schemas import AggColsSchema
from fram.virkninger.risiko.schemas import (
    HendelseSchema,
    KonsekvensSchema,
    SarbarhetSchema,
    KalkprisHelseSchema,
)

HENDELSE_COLS = TRAFIKK_COLS + ["Hendelsestype", "Risikoanalyse", FOLSOMHET_KOLONNE]
KONSEKVENS_COLS = HENDELSE_COLS + ["Virkningsnavn", "Måleenhet"]


def expect_fail_schema_df(schema: SchemaModel, dataframe: pd.DataFrame):
    """ Metode for å gjøre det enkelt å verifisere at en schema feiler med SchemaError"""
    try:
        schema.validate(dataframe)
        assert False
    except Exception:
        assert True


@pytest.fixture
def df_aggcols():
    df = pd.DataFrame(
        {
            "Strekning": list("abv"),
            "Tiltaksomraade": [1, 2, 3],
            "Tiltakspakke": [1, 2, 3],
            "Analyseomraade": list("sgf"),
            "Rute": list("lkj"),
            "Skipstype": [
                "Bulkskip",
                "Containerskip",
                "Cruiseskip",
            ],
            "Lengdegruppe": [
                "70-100",
                "100-150",
                "150-200",
            ],
            2020: [1, 2, 4],
            2021: [3, 7, 8],
        }
    ).set_index(TRAFIKK_COLS)
    return df


@pytest.fixture
def df_sarbarhet():
    df = pd.DataFrame(
        {
            "Strekning": list("abv"),
            "Tiltaksomraade": [1, 2, 3],
            "Tiltakspakke": [1, 2, 3],
            "Analyseomraade": list("sgf"),
            "Saarbarhet": ["lav", "moderat", "hoy"],
            "Fylke": [
                "Vest-Agder",
                "Ostfold",
                "More og Romsdal",
            ],
        }
    )
    return df


@pytest.fixture
def df_hendelse(df_aggcols):
    df = (
        df_aggcols.reset_index()
        .assign(
            Hendelsestype=["Grunnstøting", "Kontaktskade", "Striking"],
            Risikoanalyse=list(";la"),
            Analysenavn="Test",
        )
        .set_index(HENDELSE_COLS)
    )
    return df


@pytest.fixture
def df_kalkpris_helse():
    df = pd.DataFrame(
        {2020: [123.0, 234.0], 2021: [234.0, 324.0]}, index=["Dodsfall", "Personskade"]
    )
    return df


@pytest.fixture
def df_konsekvens(df_hendelse):
    df = (
        df_hendelse.reset_index()
        .assign(Virkningsnavn=list("l12"), Måleenhet=list("sad"))
        .set_index(KONSEKVENS_COLS)
    )
    return df


def test_AggColsSchema_OK(df_aggcols):
    AggColsSchema.validate(df_aggcols)


def test_AggColsSchema_Fail(df_aggcols):
    df_feil = df_aggcols.reset_index().set_index(TRAFIKK_COLS + [2020])
    expect_fail_schema_df(AggColsSchema, df_feil)


def test_HendelseSchema_OK(df_hendelse):
    HendelseSchema.validate(df_hendelse)


def test_HendelseSchema_OK(df_hendelse):
    HendelseSchema.validate(df_hendelse)


def test_HendelseSchema_Fail_hendelsestype(df_hendelse):
    df = (
        df_hendelse.reset_index()
        .assign(Hendelsestype=list("asd"))
        .set_index(TRAFIKK_COLS + ["Hendelsestype", "Risikoanalyse"])
    )
    expect_fail_schema_df(HendelseSchema, df)


def test_HendelseSchema_Fail(df_hendelse):
    df = df_hendelse.reset_index().set_index(
        TRAFIKK_COLS + ["Hendelsestype", "Risikoanalyse", 2020]
    )
    expect_fail_schema_df(HendelseSchema, df)


def test_KonsekvensSchema_OK(df_konsekvens):
    KonsekvensSchema.validate(df_konsekvens)


def test_KonsekvensSchema_Fail(df_konsekvens):
    df = df_konsekvens.reset_index().set_index(KONSEKVENS_COLS + [2020])
    expect_fail_schema_df(KonsekvensSchema, df)


def test_SarbarhetSchema_OK(df_sarbarhet):
    SarbarhetSchema.validate(df_sarbarhet)


def test_SarbarhetSchema_Fail(df_sarbarhet):
    df_sarbarhet = df_sarbarhet.assign(Fylke=[1, 2, 3])
    expect_fail_schema_df(SarbarhetSchema, df_sarbarhet)


def test_KalkprisHelseSchema_OK(df_kalkpris_helse):
    KalkprisHelseSchema.validate(df_kalkpris_helse)


def test_KalkprisHelseSchema_named_values(df_kalkpris_helse):
    df_named_index = df_kalkpris_helse.assign(
        Konsekvens=lambda df: df.index.values
    ).set_index("Konsekvens", drop=True)
    KalkprisHelseSchema.validate(df_named_index)


def test_KalkprisHelseSchema_Fail_wrong_index_values(df_kalkpris_helse):
    df_fail = (
        df_kalkpris_helse.reset_index()
        .assign(Konsekvens=list("ab"))
        .set_index("Konsekvens")
    )
    expect_fail_schema_df(KalkprisHelseSchema, df_fail)


def test_KalkprisHelseSchema_Fail_no_index(df_kalkpris_helse):
    df_fail = df_kalkpris_helse.reset_index()
    expect_fail_schema_df(KalkprisHelseSchema, df_fail)

import numpy as np
import pandas as pd
import pytest

from fram.virkninger.sedimenter import hjelpemoduler
from fram.virkninger.sedimenter.virkning import Sedimenter

BEREGNINGSAAR = list(range(2026, 2101))


@pytest.fixture
def forurenset_df_1():
    return pd.DataFrame(
        [
            {
                "Utdypingsområde": "A",
                "tilstandsendring": "Rød -> Oransje",
                "kommunenavn": "Moss",
                "Areal (1000 m2)": 20,
            },
            {
                "Utdypingsområde": "B",
                "tilstandsendring": "Oransje -> Gul",
                "kommunenavn": "Hvaler",
                "Areal (1000 m2)": 100,
            },
            {
                "Utdypingsområde": "B",
                "tilstandsendring": "Gul -> Grønn",
                "kommunenavn": "Båtsfjord",
                "Areal (1000 m2)": 10,
            },
        ]
    ).assign(Strekning=0, Tiltaksomraade=1, Tiltakspakke=11, Analyseomraade="0")


@pytest.fixture
def forurenset_df_2():
    return pd.DataFrame(
        [
            {
                "Utdypingsområde": "A",
                "tilstandsendring": "Rød -> Oransje",
                "kommunenavn": "Moss",
                "Areal (1000 m2)": 25,
            },
            {
                "Utdypingsområde": "B",
                "tilstandsendring": "Rød -> Oransje",
                "kommunenavn": "Moss",
                "Areal (1000 m2)": 35,
            },
            {
                "Utdypingsområde": "B",
                "tilstandsendring": "Rød -> Gul",
                "kommunenavn": "Moss",
                "Areal (1000 m2)": 15,
            },
        ]
    ).assign(Strekning=0, Tiltaksomraade=1, Tiltakspakke=11, Analyseomraade="0")


@pytest.fixture
def faktorer():
    return (
        pd.DataFrame()
        .assign(Strekning=0, Tiltaksomraade=1, Tiltakspakke=11, Analyseomraade="0")
        .append(
            pd.DataFrame(
                [
                    {
                        "Utdypingsområde": "A",
                        "tilstandendring": "Rød -> Oransje",
                        "kommunenavn": "Moss",
                        "Areal (1000 m2)": 20,
                    },
                    {
                        "Utdypingsområde": "B",
                        "tilstandendring": "Oransje -> Gul",
                        "kommunenavn": "Hvaler",
                        "Areal (1000 m2)": 100,
                    },
                    {
                        "Utdypingsområde": "B",
                        "tilstandendring": "Gul -> Grønn",
                        "kommunenavn": "Båtsfjord",
                        "Areal (1000 m2)": 10,
                    },
                ]
            )
        )
    )


def test_velfungerende_virkning(forurenset_df_1):
    s = Sedimenter(ferdigstillelsesaar=2026, kroneaar=2020, beregningsaar=BEREGNINGSAAR)
    s.beregn(forurenset_df_1)
    assert True


def test_netto_virkning(forurenset_df_1, forurenset_df_2):
    s = Sedimenter(ferdigstillelsesaar=2026, kroneaar=2020, beregningsaar=BEREGNINGSAAR)
    s.beregn(forurenset_df_1, forurenset_df_2)
    assert True


def test_netto_null(forurenset_df_1, forurenset_df_2):
    s = Sedimenter(ferdigstillelsesaar=2026, kroneaar=2020, beregningsaar=BEREGNINGSAAR)
    s.beregn(forurenset_df_1, forurenset_df_1)
    assert all(s.verdsatt_netto == 0)


def test_faktorer(forurenset_df_1, faktorer):
    s = Sedimenter(ferdigstillelsesaar=2026, kroneaar=2020, beregningsaar=BEREGNINGSAAR)
    s.beregn(forurenset_df_1)

    faktorer = {}
    for idx, row in forurenset_df_1.iterrows():
        faktorer[idx] = hjelpemoduler.get_kroner_sedimenter(
            tilstandsendring=row.tilstandsendring,
            til_kroneaar=2020,
            beregningsaar=[2026, 2027],
            areal=row["Areal (1000 m2)"],
            kroner_sedimenter=s._kroner_sedimenter,
            innbyggere_kommune=s._innbyggere_kommune,
            kommune=row.kommunenavn,
        )
    faktorer = pd.DataFrame(faktorer).T

    assert np.isclose(
        faktorer[2026].values, (3797357.73580898, 2289053.81927024,  131699.59757206)
    ).all()

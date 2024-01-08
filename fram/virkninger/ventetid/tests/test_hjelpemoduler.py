from pathlib import Path

import pytest

from fram.virkninger.ventetid.excel import les_ventetidsinput_fra_excel
from fram.virkninger.ventetid.hjelpemoduler import (
    SimuleringsInput,
    _beregn_tot_ventetid,
)


@pytest.fixture
def gyldig_simuleringsinput() -> SimuleringsInput:
    return les_ventetidsinput_fra_excel(
        filepath=Path(__file__).parent / "ventetidseksempel.xlsx",
        sheet_name="eksempel 1",
        num_periods=100_000,
    )


@pytest.fixture
def simuleringsinput_lambda_1(gyldig_simuleringsinput) -> SimuleringsInput:
    gyldig_simuleringsinput.lambda_df["2018"] = 1
    gyldig_simuleringsinput.lambda_df["2019"] = 1
    gyldig_simuleringsinput.perioder_andel["andel"] = 1 / len(
        gyldig_simuleringsinput.perioder_andel
    )
    return gyldig_simuleringsinput


@pytest.fixture()
def snittventetid_lik_1(gyldig_simuleringsinput):
    snittventetid = gyldig_simuleringsinput.lambda_df.merge(
        right=gyldig_simuleringsinput.perioder_andel, on="periode", how="left"
    )[["Skipstype", "Lengdegruppe", "periode", "andel", "2018", "2019"]].set_index(
        ["Skipstype", "Lengdegruppe", "periode", "andel"]
    )
    snittventetid["2018"] = 1
    snittventetid["2019"] = 1
    return snittventetid


def test_beregn_tot_ventetid(simuleringsinput_lambda_1, snittventetid_lik_1):
    lambda_df = simuleringsinput_lambda_1.lambda_df
    perioder_andel = simuleringsinput_lambda_1.perioder_andel
    tidsenhet = 24
    total_ventetid = _beregn_tot_ventetid(
        lambda_df=lambda_df,
        perioder_andel=perioder_andel,
        snittventetid=snittventetid_lik_1,
        tidsenhet=tidsenhet,
    )
    tot_ventetid_fasit = tidsenhet * 365 / len(perioder_andel)
    assert all(total_ventetid["tot_ventetid_2018"] == tot_ventetid_fasit)
    assert all(total_ventetid["tot_ventetid_2019"] == tot_ventetid_fasit)

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import fram.virkninger.ventetid.hjelpemoduler
from fram.virkninger.ventetid.excel import simulate_excel
from fram.virkninger.ventetid.hjelpemoduler import split_ship_id

EXCEL_INPUT_FILE = Path(__file__).parent / "ventetidseksempel.xlsx"


@pytest.mark.parametrize(
    "mu, id, retning",
    [
        ("mu_1_2", "1", "2"),
        ("mu_a_b", "a", "b"),
        ("mu_a_3", "a", "3"),
        ("mu_3_b", "3", "b"),
    ],
)
def test_mu_ikke_fail(mu, id, retning):
    out = fram.virkninger.ventetid.hjelpemoduler.hent_variabler_fra_mu(mu)
    assert out["id"] == id
    assert out["retning"] == retning


@pytest.mark.parametrize(
    "lbda, aar, periode, retning",
    [
        ("lambda_2018_vinter_nord", 2018, "vinter", "nord"),
        ("lambda_2019_sommer_sør", 2019, "sommer", "sør"),
        ("lambda_2018_2_1", 2018, "2", "1"),
        ("lambda_2019_sommer_2", 2019, "sommer", "2"),
    ],
)
def test_lambda_ikke_fail(lbda, aar, retning, periode):
    out = fram.virkninger.ventetid.hjelpemoduler.hent_variabler_fra_lambda(lbda)
    assert out["aar"] == aar
    assert out["retning"] == retning
    assert out["periode"] == periode


@pytest.mark.parametrize(
    "lbda, aar, periode, retning, feilmelding",
    [
        ("lambda_nord_2018_vinter_nord", 2018, "vinter", "nord", ValueError),
        ("lambda_2018_21", 2018, "2", "1", ValueError),
    ],
)
def test_lambda_skal_faile(lbda, aar, retning, periode, feilmelding):
    with pytest.raises(feilmelding):
        fram.virkninger.ventetid.hjelpemoduler.hent_variabler_fra_lambda(lbda)


def test_at_excel_kan_lese():
    sheet_name = "eksempel 1"

    results = simulate_excel(EXCEL_INPUT_FILE, sheet_name)
    assert results


def test_read_excel_sheet():
    supposed_df = pd.read_json(
        '{"Skipstype":{"0":"Oljetankskip","8":"Oljetankskip","1":"Oljetankskip","9":"Oljetankskip","4":"Oljetankskip","12":"Oljetankskip","5":"Oljetankskip","13":"Oljetankskip","6":"Oljetankskip","14":"Oljetankskip","2":"Oljetankskip","10":"Oljetankskip","7":"Oljetankskip","15":"Oljetankskip","3":"Oljetankskip","11":"Oljetankskip"},"Lengdegruppe":{"0":"0-30","8":"0-30","1":"100-150","9":"100-150","4":"150-200","12":"150-200","5":"200-250","13":"200-250","6":"250-300","14":"250-300","2":"30-70","10":"30-70","7":"300-","15":"300-","3":"70-100","11":"70-100"},"ventetid":{"0":0.0031705962,"8":0.0066781726,"1":0.0032601196,"9":0.0069654662,"4":0.0031705962,"12":0.0065404762,"5":0.0032601196,"13":0.0068683761,"6":0.0032460109,"14":0.0069013253,"2":0.0032460109,"10":0.0067348103,"7":0.0031041557,"15":0.0069146056,"3":0.0031041557,"11":0.0067120939},"aar":{"0":"2018","8":"2019","1":"2018","9":"2019","4":"2018","12":"2019","5":"2018","13":"2019","6":"2018","14":"2019","2":"2018","10":"2019","7":"2018","15":"2019","3":"2018","11":"2019"},"periode":{"0":"morgensommer","8":"morgensommer","1":"morgensommer","9":"morgensommer","4":"morgenvinter","12":"morgenvinter","5":"morgenvinter","13":"morgenvinter","6":"morgenvinter","14":"morgenvinter","2":"morgensommer","10":"morgensommer","7":"morgenvinter","15":"morgenvinter","3":"morgensommer","11":"morgensommer"}}'
    )

    supposed_df["aar"] = supposed_df["aar"].astype(str)
    supposed_df = supposed_df.sort_values(by=["Skipstype", "Lengdegruppe", "periode"])

    sheet_name = "eksempel 1"
    output = simulate_excel(EXCEL_INPUT_FILE, sheet_name, num_periods=300_000)
    df = [
        pd.DataFrame.from_dict(o.data).assign(aar=o.year, periode=o.period)
        for o in output
    ]
    results = (
        pd.concat(df)[["mean_wait_time_per_ship", "aar", "periode"]]
        .reset_index()
        .rename(columns={"index": "ship_id", "mean_wait_time_per_ship": "ventetid"})
        .loc[lambda df: df.ship_id.str.contains("--")]
        .dropna(subset=["ventetid"])
        .set_index("ship_id")
        .pipe(split_ship_id)
        .reset_index()
        .sort_values(by=["Skipstype", "Lengdegruppe", "periode"])
    )

    for col in ["Skipstype", "Lengdegruppe", "periode", "aar"]:
        assert all(results[col].values == supposed_df[col].values)
    for col in ["ventetid"]:
        assert np.allclose(supposed_df[col].values, results[col].values, atol=0.1)

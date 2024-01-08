"""
Test for SØA-modulen
"""
import pandas as pd
import pytest
import numpy as np
from pathlib import Path

from fram.modell import FRAM


FILNAVN_FASIT = Path(__file__).parent / "fasiter.csv"
def fasiter():
    return (
        pd.
        read_csv(FILNAVN_FASIT)
        .loc[lambda df: df.Virkninger != "0"]
        .set_index("Virkninger")
    )


strekningsfil = Path(__file__).parent / "input" / "strekning 11.xlsx"
RA_DIR = Path(__file__).parent.parent / "fram" / "eksempler" / "risikoanalyser"

s = FRAM(
    strekningsfil,
    tiltakspakke=11,
    les_RA_paa_nytt=False,
    ra_dir=RA_DIR,
)
s.run(skriv_output=False)

output = s.kontantstrommer().reset_index().drop('Aktør', axis=1).set_index(['Virkninger'])["Nåverdi levetid"]

rtols = {"Endring i ventetidskostnader": 1e-2}

fasit = fasiter().loc[
    lambda df: ( df.Strekning == "Strekning 11") & (df.Pakke == 11)
    ]["Nåverdi levetid"]

skal_ikke_testes_i_delsum = [
    "rente",
    "diskonteringsfaktor",
    "Samfunnsøkonomisk overskudd",
]
delsumnavn = [val for val in fasit.index.values if val not in skal_ikke_testes_i_delsum]


@pytest.mark.parametrize("indeks", delsumnavn)
def test_soa_delsummer(indeks):
    assert np.isclose(output[indeks], fasit[indeks], rtol=rtols.get(indeks, 1e-5))


def test_soa_totalsum():
    output_uten_ventetid = (
        output["Samfunnsøkonomisk overskudd"] - output["Endring i ventetidskostnader"]
    )
    fasit_uten_ventetid = (
        fasit["Samfunnsøkonomisk overskudd"] - fasit["Endring i ventetidskostnader"]
    )
    assert np.isclose(output_uten_ventetid, fasit_uten_ventetid)

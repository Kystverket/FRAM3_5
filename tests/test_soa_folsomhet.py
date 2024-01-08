"""
Test for SØA-modulen
"""

import pytest
import numpy as np
import pandas as pd
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
    folsomhetsanalyser=True
)
s.run(skriv_output=False)

output_hovedkjoring = s.kontantstrommer().reset_index().drop('Aktør', axis=1).set_index(['Virkninger'])["Nåverdi levetid"]
output_hoy = s.kontantstrommer("følsomhetsanalyse_1.2").reset_index().drop('Aktør', axis=1).set_index(['Virkninger'])["Nåverdi levetid"]
output_lav = s.kontantstrommer("følsomhetsanalyse_0.8").reset_index().drop('Aktør', axis=1).set_index(['Virkninger'])["Nåverdi levetid"]
rtols = {"Endring i ventetidskostnader": 1e-2}

fasit_hovedkjoring= fasiter().loc[
    lambda df: ( df.Strekning == "Strekning 11") & (df.Pakke == 11)
    ]["Nåverdi levetid"]


faktorer_utfall_folsomhet = {
    "Endring i distanseavhengige kostnader":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Endring i forurensede sedimenter":{"hoy":["==", 1.0], "lav": ["==", 1.0]},
    "Endring i globale utslipp til luft":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Endring i lokale utslipp til luft":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Endring i tidsavhengige kostnader":{"hoy":["==", 1.2**2], "lav": ["==", 0.8**2]}, # Fordi både trafikk og tidskostnad øker i denne analysen
    "Endring i vedlikeholdskostnader":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Endring i ventetidskostnader":{"hoy":[">", 1.2], "lav": ["<", 0.8]},
    "Fyrtårn Skarvhaugneset":{"hoy":["==", 1.0], "lav": ["==", 1.0]},
    "Overvåkningskameraer på haugflua-HIB’en":{"hoy":["==", np.nan], "lav": ["==", np.nan]}, # Denne er 0/0
    "Investeringskostnader, annet":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Investeringskostnader, navigasjonsinnretninger":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Investeringskostnader, utdyping":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Ulykker - endring i dødsfall":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Ulykker - endring i forventet opprenskingskostnad ved oljeutslipp":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Ulykker - endring i forventet velferdstap ved oljeutslipp":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Ulykker - endring i personskader":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Ulykker - endring i reparasjonskostnader":{"hoy":["==", 1.2], "lav": ["==", 0.8]},
    "Ulykker - endring i tid ute av drift":{"hoy":["==", 1.2**2], "lav": ["==", 0.8**2]}, # Fordi både trafikk og tidskostnad øker i denne analysen
    "Skattefinansieringskostnader":{"hoy":["==", 1.2], "lav": ["==", 0.8]}}


skal_ikke_testes_i_delsum = [
    "rente",
    "diskonteringsfaktor",
    "Samfunnsøkonomisk overskudd",
]
delsumnavn = [val for val in fasit_hovedkjoring.index.values if val not in skal_ikke_testes_i_delsum]


@pytest.mark.parametrize("indeks", delsumnavn)
def test_soa_delsummer_hovedkjoring(indeks):
    assert np.isclose(output_hovedkjoring[indeks], fasit_hovedkjoring[indeks], rtol=rtols.get(indeks, 1e-5))


@pytest.mark.parametrize("indeks, retning, operator, faktor", [
    (indeks, retning, faktorer_utfall_folsomhet[indeks][retning][0], faktorer_utfall_folsomhet[indeks][retning][1]) for retning in ["hoy", "lav"] for indeks in set(delsumnavn).intersection(set(faktorer_utfall_folsomhet.keys()))
])
def test_folsom_hoy(indeks, retning, operator, faktor):
    if operator == "==":
        assert np.isclose(eval(f"output_{retning}[indeks]/output_hovedkjoring[indeks]"), faktor, equal_nan=True)
    else:
        assert eval(f"output_{retning}[indeks]/output_hovedkjoring[indeks] {operator} {faktor}")


def test_soa_totalsum_hovedkjoring():
    output_uten_ventetid = (
            output_hovedkjoring["Samfunnsøkonomisk overskudd"] - output_hovedkjoring["Endring i ventetidskostnader"]
    )
    fasit_uten_ventetid = (
            fasit_hovedkjoring["Samfunnsøkonomisk overskudd"] - fasit_hovedkjoring["Endring i ventetidskostnader"]
    )
    assert np.isclose(output_uten_ventetid, fasit_uten_ventetid)


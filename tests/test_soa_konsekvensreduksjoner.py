"""
Test for SØA-modulen
"""

import pytest
import numpy as np
from pathlib import Path

from fram.modell import FRAM
from tests.felles import fasiter

strekningsfil = Path(__file__).parent / "input" / "strekning 11-konsekvensreduksjoner.xlsx"
STREKNING = "11-konsekvensreduksjoner"
PAKKE = 11
_fasiter = fasiter()
fasit = _fasiter.loc[
    (_fasiter.Strekning == STREKNING) & (_fasiter.Pakke == PAKKE)
    ].set_index("Virkninger")["Nåverdi levetid"]

RA_DIR = Path(__file__).parent.parent / "fram" / "eksempler" / "risikoanalyser"

s = FRAM(
    strekningsfil,
    tiltakspakke=11,
    les_RA_paa_nytt=False,
    ra_dir=RA_DIR,
)
s.run(skriv_output=False)

output = s.kontantstrommer().reset_index().drop('Aktør', axis=1).set_index(['Virkninger'])["Nåverdi levetid"]

skal_ikke_testes_i_delsum = [
    "rente",
    "diskonteringsfaktor",
]
delsumnavn = [val for val in fasit.index.values if val not in skal_ikke_testes_i_delsum]


@pytest.mark.parametrize("indeks", delsumnavn)
def test_soa_delsummer(indeks):
    assert np.isclose(output[indeks], fasit[indeks], rtol=1e-5)


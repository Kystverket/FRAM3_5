"""
Test for SØA-modulen
"""
from pathlib import Path

import pytest
import numpy as np
from tests.felles import beregn_lonnsomhet, strekning_pakke, fasiter

_fasiter = fasiter()

@pytest.mark.parametrize("strekning, pakke", strekning_pakke)
def test_strekning(strekning, pakke):

    output = beregn_lonnsomhet(strekning, pakke)

    fasit = _fasiter.loc[
        (_fasiter.Strekning == strekning) & (_fasiter.Pakke == pakke)
    ].set_index("Virkninger")["Nåverdi levetid"]

    if "Endring i ventetidskostnader" in output:
        output_uten_ventetid = (
            output["Samfunnsøkonomisk overskudd"]
            - output["Endring i ventetidskostnader"]
        )
    else:
        output_uten_ventetid = output["Samfunnsøkonomisk overskudd"]

    if "Endring i ventetidskostnader" in fasit:
        fasit_uten_ventetid = (
            fasit["Samfunnsøkonomisk overskudd"] - fasit["Endring i ventetidskostnader"]
        )
    else:
        fasit_uten_ventetid = fasit["Samfunnsøkonomisk overskudd"]

    assert np.isclose(output_uten_ventetid, fasit_uten_ventetid)



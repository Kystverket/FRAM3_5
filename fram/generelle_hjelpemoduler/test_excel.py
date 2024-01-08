import pandas as pd
import pytest

from fram.generelle_hjelpemoduler.excel import les_inn_bruttoliste_pakker_skip_lengder
from tests.felles import inputmappe as eksempel_inputmappe, testinputfiler

strekningsfiler = [fil for fil in eksempel_inputmappe.glob("*.xlsx") if not 'fram 3_5' in fil.name]

def fasitfil(navn):
    return testinputfiler / 'ruteoversikter' / f"{navn}.pkl"

def lag_nye_fasiter():
    for fil in strekningsfiler:
        navn = fil.stem
        rutedf = les_inn_bruttoliste_pakker_skip_lengder(fil)
        rutedf.to_pickle(fasitfil(navn))


@pytest.mark.parametrize("fil", strekningsfiler)
def test_ruteinnlesing(fil):
    navn = fil.stem
    rutedf = les_inn_bruttoliste_pakker_skip_lengder(fil)
    fasit = pd.read_pickle(fasitfil(navn))
    pd.testing.assert_frame_equal(rutedf, fasit)

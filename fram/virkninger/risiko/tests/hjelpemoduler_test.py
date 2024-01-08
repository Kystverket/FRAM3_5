import pytest

from fram.virkninger.risiko.hjelpemoduler import (
    generelle as hjelpemoduler,
)

BEREGNINGSAAR = list(range(2026, 2037))


def test_at_kan_hente_konsekvensinput_fra_forutsetningsbok():
    return hjelpemoduler.hent_ut_konsekvensinput()


@pytest.mark.parametrize("beregningsaar", [
    (list(range(2018, 2045))),
    (list(range(2000, 2020))),
    (list(range(2060, 2100))),
    (list(range(2000, 2111)))
])
def test_at_kan_interpolere_med_aar(beregningsaar):
    input = hjelpemoduler.hent_ut_konsekvensinput()
    return hjelpemoduler.lag_konsekvensmatrise(input, beregningsaar)


def test_beregn_helsekonsekvenser(velfungerende_konsekvensmatrise, hendelser_ref):
    return hjelpemoduler._beregn_helsekonsekvenser(hendelser_ref=hendelser_ref,
                                                   konsekvensmatrise_ref=velfungerende_konsekvensmatrise,
                                                   beregningsaar=BEREGNINGSAAR
                                                   )


def test_konsekvensmatrise_all_ones(konsekvensmatrise_bare_1):
    assert (konsekvensmatrise_bare_1.values == 1).all()


def test_rett_beregnet_helsekonsekvenser_konstant(konsekvensmatrise_bare_1, hendelser_ref):
    konsekvenser, _, _ = hjelpemoduler._beregn_helsekonsekvenser(hendelser_ref=hendelser_ref, konsekvensmatrise_ref=konsekvensmatrise_bare_1, beregningsaar=BEREGNINGSAAR)
    cols = konsekvenser.columns
    assert (konsekvenser.reset_index().loc[lambda df: df["Virkningsnavn"] == "Dodsfall"].set_index(
        hendelser_ref.index.names).loc[:, cols].sort_index() == hendelser_ref[cols].sort_index()).all().all()
    assert (konsekvenser.reset_index().loc[lambda df: df["Virkningsnavn"] == "Personskade"].set_index(
        hendelser_ref.index.names).loc[:, cols].sort_index() == hendelser_ref[cols].sort_index()).all().all()


def test_rett_beregnet_helsekonsekvenser_halvering(konsekvensmatrise_bare_1, hendelser_ref):
    halverte_konsekvenser = konsekvensmatrise_bare_1 / 2
    konsekvenser, _, _ = hjelpemoduler._beregn_helsekonsekvenser(hendelser_ref=hendelser_ref, konsekvensmatrise_ref=halverte_konsekvenser, beregningsaar=BEREGNINGSAAR)
    cols = konsekvenser.columns
    assert (konsekvenser.reset_index().loc[lambda df: df["Virkningsnavn"] == "Dodsfall"].set_index(
        hendelser_ref.index.names)[cols].sum().sum()) == hendelser_ref[cols].sum().sum() / 2
    assert (konsekvenser.reset_index().loc[lambda df: df["Virkningsnavn"] == "Personskade"].set_index(
        hendelser_ref.index.names)[cols].sum().sum()) == hendelser_ref[cols].sum().sum() / 2
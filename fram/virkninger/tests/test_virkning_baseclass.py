import pytest

from fram.virkninger.virkning import UdefinertVirkning, Virkninger


def test_udefinert_virkning():
    u = UdefinertVirkning()
    assert repr(u) == "Denne virkningen er ikke initialisert ennå"
    assert str(u) == "Denne virkningen er ikke initialisert ennå"



def test_virkninger_kontainer_kan_opprettes():
    virkninger = Virkninger()
    assert True


def test_virkninger_kontainer_kan_legge_til():
    virkninger = Virkninger()
    virkninger.risiko = '123'
    virkninger.ventetid = 1543
    assert True


def test_virkninger_kontainer_kan_ikke_legge_til_feil():
    with pytest.raises(Exception):
        virkninger = Virkninger()
        virkninger.finnes_ikke = '123'


def test_virkninger_kontainer_kan_iterere():
    virkninger = Virkninger()
    for v in virkninger:
        assert True


def test_virkninger_kontainer_riktig_lengde():
    virkninger = Virkninger()
    virkninger.risiko = '123'
    virkninger.ventetid = 10239

    assert len(virkninger) == 2


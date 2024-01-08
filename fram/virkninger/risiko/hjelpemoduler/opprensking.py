from functools import lru_cache

import pandas as pd

from fram.generelle_hjelpemoduler import kalkpriser
from fram.generelle_hjelpemoduler.hjelpefunksjoner import forutsetninger_soa


# Funksjon for å lese inn riktige tabeller
from fram.virkninger.risiko.hjelpemoduler.generelle import ARKNAVN_KONSEKVENSER_UTSLIPP
from fram.virkninger.risiko.hjelpemoduler.utslipp_felles import _read_table_utslipp, hent_sannsynligheter


def _match_kat_opp(offset, liste):
    """ En hjelpefunksjon for å vise til at i en liste vil første element i listen vise til en tabell med kategori 2-utslipp,
    det andre elementet vise til kategori 3 utslipp og det tredje elementet vise til kategori 4 utslipp.
    """
    if liste.index(offset) == 0:
        return "Kategori 2"
    elif liste.index(offset) == 1:
        return "Kategori 3"
    elif liste.index(offset) == 2:
        return "Kategori 4"


def lag_tabell_utslipp_opp(utslippstype, konsekvenser_utslipp_sheet_name: str, aar=0):
    """
        Henter inn tabeller med ferdigberegnede utfallskategorier (M1, M2, M3, M4, M5) for hver skipstype, lengdegruppe,
        utslippskategori (kategori2, kategori3, kategori4) og hendelsestype (struck, striking, grunnstøting og kontaktskade).
        Leser inn disse tabellene, slår de sammen, og merger med en dataframe med drivstofftype for hver skipstype og lengdegruppe
        """
    # viser til hvor i excelarket de ulike tabellene ligger for bunkers
    if (utslippstype == "Bunkers") & (aar == 2018):
        konsekvenser = {
            "Grunnstøting": [139],
            "Kontaktskade": [160],
            "Striking": [118],
            "Struck": [118],
        }
    if (utslippstype == "Bunkers") & (aar == 2050):
        konsekvenser = {
            "Grunnstøting": [203],
            "Kontaktskade": [224],
            "Striking": [182],
            "Struck": [182],
        }
        # viser til hvor i excelarket de ulike tabellene ligger for last
    elif utslippstype == "Last":
        konsekvenser = {
            "Grunnstøting": [268, 274, 280],
            "Kontaktskade": [288, 294, 300],
            "Striking": [248, 254, 260],
            "Struck": [248, 254, 260],
        }

        # Henter inn de riktige tabellene og gir riktig utslippskategori og hendelsestype.
    dfs = []
    for navn in konsekvenser.keys():
        for offset in konsekvenser[navn]:
            df = (
                _read_table_utslipp(skiprows=offset, utslippstype=utslippstype, konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name)
                .assign(Hendelsestype=navn)
                .assign(Utslippskategori=_match_kat_opp(offset, konsekvenser[navn]))
            )
            dfs.append(df)

    # Gjør om innlesingen til en dataframe
    utslippstabell = pd.melt(
        pd.concat(dfs).rename(columns={"Skipstype Kystverket": "Skipstype"}),
        id_vars=["Skipstype", "Hendelsestype", "Utslippskategori"],
        var_name="Lengdegruppe",
        value_name="Utslippsmengde",
    ).set_index(["Skipstype", "Lengdegruppe", "Hendelsestype"])
    return utslippstabell


@lru_cache()
def hent_kalkpriser(utslippstype: str, kroneaar: int):
    kalkpriser_opp = pd.read_excel(
        forutsetninger_soa(),
        sheet_name="kalkpris_utslipp",
        usecols=list(range(2)),
        skiprows=48,
        nrows=4,
    )
    kroneaar_opprinnelig = 2013
    prisfaktor = kalkpriser.prisjustering(1, kroneaar_opprinnelig, kroneaar)

    if utslippstype == "Bunkers":
        kalkpriser_opp = kalkpriser_opp.loc[
            kalkpriser_opp.Komponent == "Opprensking bunkersolje", "2013-kroner"
        ].values[0]
        kalkpriser_opp = kalkpriser_opp * prisfaktor
    if utslippstype == "Last":
        kalkpriser_opp = kalkpriser_opp.loc[
            (kalkpriser_opp.Komponent == "Opprensking lastolje 0-1000t")
            | (kalkpriser_opp.Komponent == "Opprensking lastolje > 1000t")
        ]
        kalkpriser_opp["2013-kroner"] = kalkpriser_opp["2013-kroner"] * prisfaktor

    return kalkpriser_opp


def bunkers_utslipp_opp(kroneaar: int, konsekvenser_utslipp_sheet_name: str):
    """Funksjon for å sette sammen utslippet fra de som kun har bunkers og de som har last og bunkers."""
    bunkers_utslipp_opp_2018 = (
        lag_tabell_utslipp_opp(utslippstype="Bunkers", aar=2018, konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name)
        .drop("Utslippskategori", axis=1)
        .rename(columns={"Utslippsmengde": "Utslippsmengde_bunkers_2018"})
    )
    bunkers_utslipp_opp_2018["kalkpris_bunker_2018"] = bunkers_utslipp_opp_2018[
        "Utslippsmengde_bunkers_2018"
    ] * hent_kalkpriser("Bunkers", kroneaar=kroneaar)
    bunkers_utslipp_opp_2018 = bunkers_utslipp_opp_2018.reset_index().set_index(
        ["Skipstype", "Lengdegruppe", "Hendelsestype"]
    )

    bunkers_utslipp_opp_2050 = (
        lag_tabell_utslipp_opp(utslippstype="Bunkers", aar=2050, konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name)
        .drop("Utslippskategori", axis=1)
        .rename(columns={"Utslippsmengde": "Utslippsmengde_bunkers_2050"})
    )
    bunkers_utslipp_opp_2050["kalkpris_bunker_2050"] = bunkers_utslipp_opp_2050[
        "Utslippsmengde_bunkers_2050"
    ] * hent_kalkpriser("Bunkers", kroneaar=kroneaar)
    bunkers_utslipp_opp_2050 = bunkers_utslipp_opp_2050.reset_index().set_index(
        ["Skipstype", "Lengdegruppe", "Hendelsestype"]
    )

    bunkers_utslipp_opp = bunkers_utslipp_opp_2018.merge(
        bunkers_utslipp_opp_2050, how="left", left_index=True, right_index=True
    )
    return bunkers_utslipp_opp


def last_utslipp_opp(kroneaar: int, konsekvenser_utslipp_sheet_name: str):

    last_utslipp_opp = (
        lag_tabell_utslipp_opp(utslippstype="Last", konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name)
        .rename(columns={"Utslippsmengde": "Utslippsmengde_last"})
        .reset_index()
        .set_index(["Skipstype", "Lengdegruppe", "Hendelsestype", "Utslippskategori"])
    )

    kalkpris_lav = (
        hent_kalkpriser("Last", kroneaar=kroneaar)
        .loc[
            hent_kalkpriser("Last", kroneaar=kroneaar).Komponent
            == "Opprensking lastolje 0-1000t",
            "2013-kroner",
        ]
        .values[0]
    )
    pris_lav = last_utslipp_opp.copy()
    pris_lav = pris_lav.loc[pris_lav.Utslippsmengde_last <= 1000]
    pris_lav["forventet_pris_last"] = pris_lav * kalkpris_lav

    kalkpris_hoy = (
        hent_kalkpriser("Last", kroneaar=kroneaar)
        .loc[
            hent_kalkpriser("Last", kroneaar=kroneaar).Komponent
            == "Opprensking lastolje > 1000t",
            "2013-kroner",
        ]
        .values[0]
    )
    pris_hoy = last_utslipp_opp.copy()
    pris_hoy = pris_hoy.loc[pris_hoy.Utslippsmengde_last > 1000]
    pris_hoy["forventet_pris_last"] = pris_hoy * kalkpris_hoy

    last_utslipp_opp = (pd.concat((pris_lav, pris_hoy), axis=0)
        .reset_index()
        .set_index(["Utslippskategori", "Hendelsestype"])
    )

    # Henter inn kalk
    sammensatt = last_utslipp_opp.merge(
        hent_sannsynligheter(konsekvenser_utslipp_sheet_name), left_index=True, right_index=True, how="left"
    )
    sammensatt["vektet_pris_2018"] = (
        sammensatt["forventet_pris_last"] * sammensatt["Sannsynlighet2018"]
    )
    sammensatt["vektet_pris_2050"] = (
        sammensatt["forventet_pris_last"] * sammensatt["Sannsynlighet2050"]
    )
    sammensatt = (
        sammensatt.groupby(by=["Skipstype", "Lengdegruppe", "Hendelsestype"])[
            ["vektet_pris_2018", "vektet_pris_2050"]
        ]
        .sum()
        .reset_index()
        .set_index(["Skipstype", "Lengdegruppe", "Hendelsestype"])
    )
    return sammensatt



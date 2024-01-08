"""Hjelpemoduler for kalkpriser for oljeutslipp. Leser fra 'Forutsetninger_FRAM.xlsx' """
import pandas as pd

from fram.generelle_hjelpemoduler import kalkpriser
from fram.generelle_hjelpemoduler.hjelpefunksjoner import forutsetninger_soa
from fram.virkninger.risiko.hjelpemoduler.generelle import ARKNAVN_KONSEKVENSER_UTSLIPP
from fram.virkninger.risiko.hjelpemoduler.utslipp_felles import _read_table_utslipp


def _match_kat(offset, liste):
    """ En hjelpefunksjon for å vise til at i en liste vil første element i listen vise til en tabell med kategori 2-utslipp,
    det andre elementet vise til kategori 3 utslipp og det tredje elementet vise til kategori 4 utslipp.
    """
    if liste.index(offset) == 0:
        return "Kategori 2"
    elif liste.index(offset) == 1:
        return "Kategori 3"
    elif liste.index(offset) == 2:
        return "Kategori 4"


def _drivstoff_bunkers(konsekvenser_utslipp_sheet_name):
    """ Hjelpefunksjon for å hente inn drivstofftyper for de ulike skipstypene fra Excel-boken `Forutsetninger_FRAM.xlsx` """
    drivstoff = pd.melt(
        _read_table_utslipp(skiprows=25, utslippstype="Bunkers", konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name).rename(
            columns={"Skipstype Kystverket": "Skipstype"}
        ),
        id_vars=["Skipstype"],
        var_name="Lengdegruppe",
        value_name="Drivstofftype",
    ).set_index(["Skipstype", "Lengdegruppe"])
    return drivstoff


def _lag_tabell_utslipp(utslippstype: str, konsekvenser_utslipp_sheet_name: str):
    """Henter inn tabeller med ferdigberegnede utfallskategorier (M1, M2, M3, M4, M5) for hver skipstype, lengdegruppe,
        utslippskategori (kategori2, kategori3, kategori4) og hendelsestype (struck, striking, grunnstøting og kontaktskade).
        Leser inn disse tabellene, slår de sammen, og merger med en dataframe med drivstofftype for hver skipstype og lengdegruppe

        Parameters:
            - utslippstype: Enten 'Bunkers' eller 'Last'
            - konsekvenser_utslipp_sheet_name: en trippelkolonseparert string med boknavn og arknavn for konsekvensmatrisene for utslipp. For å bruke standardverdier, angi 'forutsetninger:::konsekvenser_utslipp' (også lagret som en konstant 'ARKNAVN_KONSEKVENSER_UTSLIPP'. Alternativet til 'forutsetinger' er 'input'. Arknavnet kan være hva det vil
        """
    # viser til hvor i excelarket de ulike tabellene ligger for bunkers
    if utslippstype == "Bunkers":
        konsekvenser = {
            "Grunnstøting": [383, 403, 423],
            "Kontaktskade": [445, 465, 485],
            "Striking": [321, 341, 361],
            "Struck": [321, 341, 361],
        }

    # viser til hvor i excelarket de ulike tabellene ligger for last
    elif utslippstype == "Last":
        konsekvenser = {
            "Grunnstøting": [528, 533, 538],
            "Kontaktskade": [545, 550, 555],
            "Striking": [511, 516, 521],
            "Struck": [511, 516, 521],
        }
    else:
        raise KeyError(f"utslippstype må være 'Bunkers' eller 'Last'. Fikk {utslippstype}")

    # Henter inn de riktige tabellene og gir riktig utslippskategori og hendelsestype.
    dfs = []
    for navn in konsekvenser.keys():
        for offset in konsekvenser[navn]:
            df = (
                _read_table_utslipp(skiprows=offset, utslippstype=utslippstype, konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name)
                .assign(Hendelsestype=navn)
                .assign(Utslippskategori=_match_kat(offset, konsekvenser[navn]))
            )
            dfs.append(df)

    # Gjør om innlesingen til en dataframe
    utslippstabell = pd.melt(
        pd.concat(dfs).rename(columns={"Skipstype Kystverket": "Skipstype"}),
        id_vars=["Skipstype", "Hendelsestype", "Utslippskategori"],
        var_name="Lengdegruppe",
        value_name="Utslippsfaktor",
    ).set_index(["Skipstype", "Lengdegruppe"])

    if utslippstype == "Bunkers":
        # merger utslippskategorier og -utfall med drivstofftype
        utslippstabell_bunkers = (
            utslippstabell.merge(
                right=_drivstoff_bunkers(konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name),
                left_index=True,
                right_index=True,
                how="left",
            )
            .reset_index()
            .rename(columns={"Utslippsfaktor": "Utslippsfaktor_bunkers"})
        )
        return utslippstabell_bunkers

    elif utslippstype == "Last":
        utslippstabell_last = (
            utslippstabell.merge(
                right=_drivstoff_bunkers(konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name),
                left_index=True,
                right_index=True,
                how="left",
            )
            .reset_index()
            .assign(Lasttype="D")
            .rename(columns={"Utslippsfaktor": "Utslippsfaktor_last"})
        )
        return utslippstabell_last


def _samlet_tabell_utslipp(konsekvenser_utslipp_sheet_name: str):
    """Funksjon for å sette sammen utslippet fra de som kun har bunkers og de som har last og bunkers."""
    bunkers_utslipp = _lag_tabell_utslipp(utslippstype="Bunkers", konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name).set_index(
        [
            "Skipstype",
            "Lengdegruppe",
            "Hendelsestype",
            "Utslippskategori",
            "Drivstofftype",
        ]
    )
    utslippstabell = bunkers_utslipp.merge(
        _lag_tabell_utslipp(utslippstype="Last", konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name).set_index(
            [
                "Skipstype",
                "Lengdegruppe",
                "Hendelsestype",
                "Utslippskategori",
                "Drivstofftype",
            ]
        ),
        how="left",
        left_index=True,
        right_index=True,
    ).reset_index()
    return utslippstabell


def _kalkpriser_utslipp(var_name: str, kroneaar: int):
    """
    Hjelpefunksjon for å hente ut sårbarhetsmatrisen som viser hvilken kalkulasjonspris ulike kombinasjoner av drivstoff, mengdeutslipp
    og sårbarhet skal ha. Deretter kobler den disse verdiene til kalkulasjonspriser for 17 fylker.
    """
    # Henter inn sårbarhetsmatrisen med såbarhetsnivåer, drivstofftype og utfallskategori
    sarbarhetsmatrise = pd.read_excel(
        forutsetninger_soa(),
        sheet_name="kalkpris_utslipp",
        usecols=list(range(6)),
        skiprows=3,
        nrows=20,
    )
    sarbarhetsmatrise = pd.melt(
        sarbarhetsmatrise,
        id_vars=["Drivstofftype", "Utslippsfaktor"],
        var_name="Saarbarhet",
        value_name="Prisnivå",
    )

    # Henter inn kalkulasjonsprisene for ulike kategorier og fylker
    df_kalkpriser = pd.read_excel(
        forutsetninger_soa(),
        sheet_name="kalkpris_utslipp",
        usecols=list(range(5)),
        skiprows=28,
        nrows=18,
    )
    df_kalkpriser = pd.melt(
        df_kalkpriser, id_vars=["Fylke"], var_name="Prisnivå", value_name="Kalkpris",
    )

    # Legger sammen kalkulasjonspriser for alle sårbarhetsnivåer, fylker og drivstofftyper, skipstyper og lengdegrupper
    df_kalkpriser = (
        df_kalkpriser.merge(sarbarhetsmatrise, how="left")
        .rename(columns={"Drivstofftype": var_name})
        .set_index([var_name, "Utslippsfaktor"])
    )

    # realprisjusterer og kroneprisjusterer verdsettingsfaktorene
    kroneaar_opprinnelig = 2022
    if kroneaar_opprinnelig < kroneaar:
        prisfaktor = kalkpriser.prisjustering(1, kroneaar_opprinnelig, kroneaar)
        realfaktor = kalkpriser.realprisjustering_kalk(1, kroneaar_opprinnelig, kroneaar)
        df_kalkpriser["Kalkpris"] = df_kalkpriser["Kalkpris"] * prisfaktor * realfaktor

    return df_kalkpriser


def _hent_kalkpriser(kroneaar: int, konsekvenser_utslipp_sheet_name: str):
    utslippstabell = (
        _samlet_tabell_utslipp(konsekvenser_utslipp_sheet_name=konsekvenser_utslipp_sheet_name)
        .rename(columns={"Utslippsfaktor_bunkers": "Utslippsfaktor"})
        .set_index(["Drivstofftype", "Utslippsfaktor"])
        .merge(
            _kalkpriser_utslipp("Drivstofftype", kroneaar=kroneaar),
            how="left",
            left_index=True,
            right_index=True,
        )
        .reset_index()
        .rename(
            columns={
                "Prisnivå": "Prisnivå_bunkers",
                "Kalkpris": "Kalkpris_bunkers",
                "Utslippsfaktor": "Utslippsfaktor_bunkers",
                "Utslippsfaktor_last": "Utslippsfaktor",
            }
        )
    )
    utslippstabell["Lasttype"] = utslippstabell["Lasttype"].fillna("Ingen")
    utslippstabell["Utslippsfaktor"] = utslippstabell["Utslippsfaktor"].fillna("Ingen")

    utslippstabell = utslippstabell.reset_index().set_index(
        ["Lasttype", "Utslippsfaktor", "Saarbarhet", "Fylke"]
    )

    priser_last = (
        _kalkpriser_utslipp("Lasttype", kroneaar=kroneaar)
        .reset_index()
        .set_index(["Lasttype", "Utslippsfaktor", "Saarbarhet", "Fylke"])
        .rename(columns={"Prisnivå": "Prisnivå_last", "Kalkpris": "Kalkpris_last"})
    )

    utslippstabell = (
        utslippstabell.merge(priser_last, how="left", right_index=True, left_index=True)
        .reset_index()
        .rename(columns={"Utslippsfaktor": "Utslippsfaktor_last"})
        .set_index(["Utslippskategori", "Hendelsestype"])
        .assign(Kalkpris_last=lambda df: df.Kalkpris_last.fillna(0))
    )
    utslippstabell["Kalkpris"] = (
        utslippstabell["Kalkpris_bunkers"] + utslippstabell["Kalkpris_last"]
    )
    utslippstabell = utslippstabell.drop(["Kalkpris_bunkers", "Kalkpris_last"], axis=1)
    return utslippstabell


def _hent_sannsynligheter():
    "Hjelpefunksjon for å hente ut sannsynligheter for ulike alvorlighetskrader også kalt utslippskategorier."
    sannsynligheter2018 = pd.read_excel(
        forutsetninger_soa(),
        sheet_name="konsekvenser_utslipp",
        usecols=list(range(4)),
        skiprows=7,
        nrows=4,
    )

    sannsynligheter2018 = pd.melt(
        sannsynligheter2018,
        id_vars="Utslippskategori",
        var_name="Hendelsestype",
        value_name="Sannsynlighet2018",
    )

    sannsynligheter2050 = pd.read_excel(
        forutsetninger_soa(),
        sheet_name="konsekvenser_utslipp",
        usecols=list(range(4)),
        skiprows=15,
        nrows=4,
    )

    sannsynligheter2050 = pd.melt(
        sannsynligheter2050,
        id_vars="Utslippskategori",
        var_name="Hendelsestype",
        value_name="Sannsynlighet2050",
    )

    sannsynligheter = sannsynligheter2018.merge(
        sannsynligheter2050, how="outer"
    )
    sannsynligheter = (
        sannsynligheter.append(
            sannsynligheter.loc[
                sannsynligheter.Hendelsestype == "Kollisjon"
            ].replace(to_replace="Kollisjon", value="Struck")
        )
        .replace(to_replace="Kollisjon", value="Striking")
        .set_index(["Utslippskategori", "Hendelsestype"])
    )
    return sannsynligheter


def _try_make_int(string):
    """Hjelpefunksjon for å konvertere årskolonnenavn fra streng til int"""
    try:
        out = int(string)
    except:
        out = string
    return out

import pandas as pd

from fram.generelle_hjelpemoduler.hjelpefunksjoner import forutsetninger_soa
from fram.virkninger.risiko.hjelpemoduler.generelle import ARKNAVN_KONSEKVENSER_UTSLIPP


def _read_table_utslipp(
    skiprows: int, utslippstype: str, konsekvenser_utslipp_sheet_name: str
):
    """
    Funksjon som kun viser til hvilket excelark vi skal lese inn fra excelboken med forutsetninger, og hvor store tabellene den skal
    lese inn. Hvis det er bunkers er det for alle skipstyper, altså 16 rader, mens for last er det kun 2 skipstyper og 2 rader.

    Parameters:
        - skiprows: int, hvor mange rader den skal hoppe over
        - utslippstype: str, enten 'Bunkers' eller 'Last'
        - konsekvenser_utslipp_sheet_name: str, en trippelkolonseparert string med boknavn og arknavn for konsekvensmatrisene for utslipp. For å bruke standardverdier, angi 'forutsetninger:::konsekvenser_utslipp' (også lagret som en konstant 'ARKNAVN_KONSEKVENSER_UTSLIPP'. Alternativet til 'forutsetinger' er 'input'. Arknavnet kan være hva det vil
    """
    if utslippstype == "Bunkers":
        nrows = 16
    elif utslippstype == "Last":
        nrows = 2
    else:
        raise KeyError(f"'utslippstype' må være en av 'Bunkers' eller 'Last'. Fikk {utslippstype}")

    excel_bok, arknavn = konsekvenser_utslipp_sheet_name.split(":::")
    if excel_bok == "forutsetninger":
        excel_bok = forutsetninger_soa()

    df = pd.read_excel(
        excel_bok,
        sheet_name=arknavn,
        usecols=list(range(9)),
        skiprows=skiprows,
        nrows=nrows,
    )
    return df


def hent_sannsynligheter(konsekvenser_utslipp_sheet_name: str):
    "Hjelpefunksjon for å hente ut sannsynligheter for ulike alvorlighetskrader også kalt utslippskategorier."
    excel_bok, arknavn = konsekvenser_utslipp_sheet_name.split(":::")
    if excel_bok == "forutsetninger":
        excel_bok = forutsetninger_soa()

    sannsynligheter2018 = pd.read_excel(
        excel_bok,
        sheet_name=arknavn,
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
        excel_bok,
        sheet_name=arknavn,
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

    sannsynligheter = sannsynligheter2018.merge(sannsynligheter2050, how="outer")
    sannsynligheter = (pd.concat((sannsynligheter, (sannsynligheter.loc[sannsynligheter.Hendelsestype == "Kollisjon"].replace(to_replace="Kollisjon", value="Struck"))),axis=0)
        .replace(to_replace="Kollisjon", value="Striking")
        .set_index(["Utslippskategori", "Hendelsestype"])
    )
    return sannsynligheter
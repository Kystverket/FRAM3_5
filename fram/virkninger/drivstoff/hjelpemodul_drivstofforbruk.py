"""
Inneholder klasse for å lage strekningsspesifikke kalkulasjonspriser
"""

import numpy as np
import pandas as pd

from typing import List, Callable

from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.hjelpefunksjoner import (
    interpoler_linear_vekstfaktor,
    interpoler_produkt_vekstfaktor,
    forut,
)
from fram.generelle_hjelpemoduler.kalkpriser import prisjustering
from fram.generelle_hjelpemoduler.konstanter import FRAM_DIRECTORY
from fram.virkninger.drivstoff.schemas import DrivstoffPerTimeSchema, DrivstoffandelerSchema
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.risiko.hjelpemoduler.generelle import _dropp_overste_kolonnenavnnivaa

FORUTSETNINGER = forut("Forutsetninger")
SKROGFORM = forut("blokkoeffisient", 4)
KONSUM = forut("Virkningsgrad", 4)


KONVERTERER_NYE_TIL_FRAM_DRIVSTOFFTYPER = {
    "Konvensjonell": "MGO og HFO",
    "Strøm": "Elektrisitet",
    "Biodrivstoff": "Karbonnøytrale drivstoff",
    "Hydrogen": "Karbonnøytrale drivstoff",
    "Hydrogenbasert": "Karbonnøytrale drivstoff",
}

r = 0.9


def beregn_drivstofforbruk_i_tonn(hastighet_df, beregningsaar: List[int], logger: Callable = print):

    """
    Hjelpefunksjon til :py:func:`~fram.virkninger.drivstoff.hjelpemodul_drivstofforbruk.get_ettersp_drivstoff_per_time`.
    Beregner drivstofforbruk.
    Args:
        hastighet_df (DataFrame): Deilingshastigheter
        beregningsaar: Årene forbruket skal beregnes for
        logger: Callable for logging

    Returns:
        DataFrame: Drivstofforbruk
    """
    # Beregner energibehov til fremdrift per skipstype, lengdegruppe og rute (merk: dette er uavhengig av energibærer)
    energibehov_fremdrift_per_time = get_energibehov_fremdrift_per_time(
        hastighet_df, beregningsaar, logger=logger
    )
    # Leser inn fremskrevne drivstoffandeler per energibærerer
    fuelmiks_fremdrift = (
        get_drivstoffandeler(beregningsaar)
        .set_index(["Skipstype", "Lengdegruppe", "Drivstofftype"])
        .rename(columns=lambda x: f"andel_{x}")
        .reset_index()
        .set_index(["Skipstype", "Lengdegruppe"])
    )
    koblet_energi_andel = energibehov_fremdrift_per_time.merge(
        right=fuelmiks_fremdrift, left_index=True, right_index=True, how="outer"
    )

    for year in beregningsaar:
        koblet_energi_andel[year] = (
            koblet_energi_andel[f"energibehov_{year}"]
            * koblet_energi_andel[f"andel_{year}"]
        )

    energibehov_per_type_time = (
        koblet_energi_andel.reset_index()
        .set_index(["Skipstype", "Lengdegruppe", "Drivstofftype", "Rute"])[
            beregningsaar
        ]
        .reset_index()
    )

    return energibehov_per_type_time


def konverter_drivstofforbruk_til_MJ(
    drivstofforbruk_per_type_time, beregningsaar: List[int], drivstoffvekter=None
):
    """
    Hjelpefunksjon til :py:func:`~fram.virkninger.drivstoff.hjelpemodul_drivstofforbruk.get_ettersp_drivstoff_per_time`.
    Beregner energibehov i MJ fra drivstofforbruk.
    Args:
        drivstofforbruk_per_type_time (DataFrame): Drivstofforbruk per time for hver skiptype/lengdegruppe/år
        beregningsaar: Årene energibehovet skal beregnes for
        drivstoffvekter (DataFrame): Vektet skipsinformasjon per skiptype og lengdegruppe. Må inneholde kolonnene per skipstype og lengdegruppe

    Returns:
        DataFrame: Energibehov i MJ per skipstype/lengderppe/år
    """

    # Leser inn motoravhengig informasjon som service_speed, motorstørrelse og virkningsgrad
    if drivstoffvekter is None:
        skipsinfo = get_motoravhengig_info()
    else:
        skipsinfo = drivstoffvekter

    energitetthet_mj_per_enhet = {"MGO": 43000, "LNG": 49000, "NOY": 81750, "EL": 1}

    mapping = dict(
        zip(
            ["MGO", "LNG", "NOY", "EL"],
            ["MGO og HFO", "LNG", "Karbonøytrale drivstoff", "Elektrisitet"],
        )
    )

    virkningsgrader = (
        skipsinfo[
            [
                "Virkningsgrad_MGO",
                "Virkningsgrad_LNG",
                "Virkningsgrad_NOY",
                "Virkningsgrad_EL",
            ]
        ]
        .assign(
            Mellomregning_MGO=lambda x: x.Virkningsgrad_MGO
            * energitetthet_mj_per_enhet["MGO"]
        )
        .assign(
            Mellomregning_LNG=lambda x: x.Virkningsgrad_LNG
            * energitetthet_mj_per_enhet["LNG"]
        )
        .assign(
            Mellomregning_NOY=lambda x: x.Virkningsgrad_NOY
            * energitetthet_mj_per_enhet["NOY"]
        )
        .assign(Mellomregning_EL=lambda x: x.Virkningsgrad_EL)
        # For elektrisitet er det ingen mellomregning (enheten er MJ9)
    )

    virkningsgrader_energitetthet = pd.melt(
        virkningsgrader.reset_index(),
        id_vars=["Skipstype", "Lengdegruppe"],
        var_name="Drivstofftype",
        # value_vars=["Virkningsgrad_MGO", "Virkningsgrad_LNG", "Virkningsgrad_NOY", "Virkningsgrad_EL"],
        value_vars=[
            "Mellomregning_MGO",
            "Mellomregning_LNG",
            "Mellomregning_NOY",
            "Mellomregning_EL",
        ],
        value_name="Mellomregning",
    ).assign(
        Drivstofftype=lambda df: df.Drivstofftype.str[14:].map(mapping).astype(str)
    )

    ettersp_drivstoff_per_time = drivstofforbruk_per_type_time.merge(
        right=virkningsgrader_energitetthet,
        on=["Skipstype", "Lengdegruppe", "Drivstofftype"],
    ).set_index(["Skipstype", "Lengdegruppe", "Drivstofftype"])

    for year in beregningsaar:
        ettersp_drivstoff_per_time[year] /= ettersp_drivstoff_per_time[
            "Mellomregning"
        ]  # Funker dette per drivstofftype?

    return ettersp_drivstoff_per_time.drop("Mellomregning", axis=1)


def get_ettersp_drivstoff_per_time(
    beregningsaar: List[int],
    hastighet_df=None,
    drivstoffvekter=None,
    drivstofforbruk_per_type_time=None,
):
    """
    Beregner drivstofforbruk per time (etterspurt mengde) over tid per skipstype, lengdegruppe, drivstofftype og rute.
    Dette omfatter:

    - Trinn 1: Beregner energibehovet til fremdrift, propulsjonseffekten, for en gitt fartøystype, lengdegruppe og rute
    - Trinn 2: Fremskriver energibehovet til 2050 ved hjelp av effektiviseringsfaktor
    - Trinn 3: Fordeler energiforbruket per år på ulike energibærere
    - Trinn 4: Beregner etterspurt mengde drivstoff (MJ for elektrisitet) i markedet per energibærer ved hjelp av virkningsgrader og energitettheter

    Args:
        hastighet_df (DataFrame): Følgende kolonner:

            - Skipstype
            - Lengdegruppe
            - Hastighet (i knop)
            - Rute

        drivstofforbruk_per_type_time (DataFrame): Ferdigberegnet drivstofforbruk per skipstype/lengdegruppe/år. Beregnes hvis ikke oppgitt

        beregningsaar: liste over de årene du vil ha beregnet virkningen for
        drivstoffvekter (DataFrame): dataframe med vektet skipsinformasjon per skiptype og lengdegruppe. Må inneholde kolonnene per skipstype og lengdegruppe:

                        - "service_speed",
                        - "engine_kw_total",
                        - "Virkningsgrad_MGO",
                        - "Virkningsgrad_LNG",
                        - "Virkningsgrad_NOY" og
                        - "Virkningsgrad_EL"

    Returns:
        Dataframe: Etterspurt drivstofforbruk per målt i MJ fremdrift per time vi får

    """
    assert hastighet_df is not None or drivstofforbruk_per_type_time is not None, "Feil i drivstoffberegning: Oppgi enten hastighet eller drivstofforbruk"

    if drivstofforbruk_per_type_time is None:
        drivstofforbruk_per_type_time = beregn_drivstofforbruk_i_tonn(hastighet_df, beregningsaar)

    return konverter_drivstofforbruk_til_MJ(
        drivstofforbruk_per_type_time, beregningsaar, drivstoffvekter=drivstoffvekter
    )


def get_energibehov_fremdrift_per_time(df, beregningsaar: List[int], logger: Callable = print):
    """
    Regner ut energibehovet til fremdrift per time på ulike ruter (merk: dette er uavhengig av energibærer).

    Her gjør vi følgende:

    - Trinn 1: Beregner energibehovet til fremdrift, propulsjonseffekten, for en gitt fartøystype, lengdegruppe og rute
    - Trinn 2: Fremskriver energibehovet til 2050 ved hjelp av effektiviseringsfaktor

    Args:
        df (DataFrame): Følgende kolonner:

            - Skipstype
            - Lengdegruppe
            - Hastighet (i knop)
            - Rute

        beregningsaar: liste over de årene du vil ha beregnet virkningen for
        logger: Callable for å logge

    Returns:
        Dataframe med energibehovet målt i MJ fremdrift per time fremskrevet

    """
    input_df = df.reset_index().set_index(["Skipstype", "Lengdegruppe"])

    skipsinfo = get_motoravhengig_info().dropna(subset=["service_speed"])
    mangler_service_speed = skipsinfo.loc[skipsinfo.service_speed.isna()]
    if len(mangler_service_speed):
        skip = mangler_service_speed[["Skipstype", "Lengdegruppe"]].unique()
        logger(f"Advarsel: Det mangler service_speed for {skip}. Disse vil ikke få beregnet drivstofforbruk riktig.")

    effektivisering = get_effektiviseringsfaktor(beregningsaar).set_index(
        ["Skipstype", "Lengdegruppe"]
    )

    # Looper over rutene og verdsetter drivstoff per rute
    # Disse avhenger av fart og bølger
    outputs = []

    for rute, df in input_df.groupby("Rute"):
        bolgegeo = oversett_rute_til_bolge(rute)

        korreksjonsfaktor = get_korreksjonsfaktor(bolgegeo)

        lastfaktor = (
            (r * df.Hastighet.div(skipsinfo["service_speed"]) ** 3) * korreksjonsfaktor
        ).clip(0.2, 0.9)

        # Dette konverteres først til hvor mange MJ vi må kjøpe, deretter hvor mange MJ fremdrift vi får
        justering_hjelpemotor = (
            1.1  # 1.1 kommer av at dette både er hoved- og hjelpemotor)
        )
        konvertering_kwh_til_mj = 3.6
        ettersp = (
            (
                justering_hjelpemotor
                * skipsinfo["engine_kw_total"]
                * lastfaktor
                * konvertering_kwh_til_mj
            )
            .rename("energibruk_per_time_2018")
            .to_frame()
            .reset_index()
            .assign(Rute=rute)
            .set_index(["Skipstype", "Lengdegruppe", "Rute"])
        )
        outputs.append(ettersp["energibruk_per_time_2018"].to_frame())

    energibehov_fremdrift_per_time_2018 = pd.concat(outputs, axis=0)

    energibehov_fremdrift_per_time = (
        energibehov_fremdrift_per_time_2018["energibruk_per_time_2018"]
        .to_frame()
        .reset_index()
        .merge(right=effektivisering, on=["Skipstype", "Lengdegruppe"])
        .set_index(["Skipstype", "Lengdegruppe"])
    )
    for year in beregningsaar:
        energibehov_fremdrift_per_time[year] *= energibehov_fremdrift_per_time[
            "energibruk_per_time_2018"
        ]  # Funker dette per drivstofftype?

    energibehov_fremdrift_per_time = (
        energibehov_fremdrift_per_time.drop("energibruk_per_time_2018", axis=1)
        .reset_index()
        .set_index(["Skipstype", "Lengdegruppe", "Rute"])
        .rename(columns=lambda x: f"energibehov_{x}")
        .reset_index()
        .set_index(["Skipstype", "Lengdegruppe"])
    )
    return energibehov_fremdrift_per_time


def _vektet_korreksjonsfaktor(bolgegeo: str = None):
    """
    Returnerer en korreksjonsfaktorfunksjon basert på observerte bølgedata
    på den konkrete strekningen. Dersom bølgedata ikke eksisterer så settes
    bølgehøyde- og lengde til null. Vektingen refererer til de lokale bølgeforholdene
    over tid.

    Args:
        bolgegeo: Foreløpig ikke virkning, men satt på vent til bølgemetodikk er implementert.

    Returns:
        NotImplementedError: Denne funksjonen vil lese inn simulerte bølgedata for hver rute, og beregne
        en korreksjonsfaktorfunksjon(skrog), der man har snittet ut bølgedataene
        på riktig måte i forkant.

    """
    if bolgegeo is None:
        # bolgehoyde, bolgelengde = np.ones(100), np.ones(100)
        bolgehoyde, bolgelengde = np.ones(100) * 1.15, np.ones(100)
    else:
        raise NotImplementedError("Har ikke mottatt bølgedata ennå")

    def uvektet_korreksjonsfaktor(skrogform: str, bolgehoyde: float, bolgelengde: float):
        """
        Beregner en korreksjonsfaktor for fartstap i bølger.

        Args:
            skrogform: er enten 0.6, 0.7 eller 0.8. Er en streng
            bolgehøyde:
            bolgelengde:

        Returns:
            float: vektede faktorer
        """
        if skrogform not in ["0.6", "0.7", "0.8"]:
            raise ValueError("Skrogform må være en streng 0.6, 0.7, 0.8")
        konstantledd = {"0.6": -0.23, "0.7": -0.38, "0.8": -0.52}
        helning = {"0.6": 13.8, "0.7": 22.1, "0.8": 30.3}
        out = (
            1 + konstantledd[skrogform] + helning[skrogform] * bolgehoyde / bolgelengde
        )
        return out

    vektede_faktorer = {}
    for skrogform in ["0.6", "0.7", "0.8"]:
        uvektede_faktorer = uvektet_korreksjonsfaktor(
            skrogform, bolgehoyde, bolgelengde
        )
        vektede_faktorer[skrogform] = np.mean(uvektede_faktorer)
    return vektede_faktorer


def get_korreksjonsfaktor(bolgegeo=None):
    """
    Beregner lastfaktoren, som avhenger av skrog og bølger. Alltid mellom 0.2 og 0.9.
    Bølgekorrigeringsfaktoren er satt til 1.15 (bølgehøyde/bølgelengde)

    Args:
        bolgegeo (str): Hvilket sted bølgekjøringene skal hentes fra

    Returns:
        Dataframe: Korreksjonsfaktor.

    """
    vektet_korreksjonsfaktor = _vektet_korreksjonsfaktor(bolgegeo)

    def get_nearest(input):
        """Konverterer floating skrogform til streng for eksakt match seneres"""
        if 0.55 < input < 0.65:
            return "0.6"
        elif input < 0.75:
            return "0.7"
        elif input < 0.85:
            return "0.8"
        else:
            return None

    skipsinfo = SKROGFORM.assign(
        korreksjonsfaktor=lambda x: x.skrogform.map(get_nearest).map(
            vektet_korreksjonsfaktor
        )
    ).set_index(["Skipstype", "Lengdegruppe"])
    if bolgegeo is None:
        skipsinfo["korreksjonsfaktor"] = np.ones(len(skipsinfo)) * 1.15
        return skipsinfo["korreksjonsfaktor"]
    else:
        return skipsinfo["korreksjonsfaktor"]


def get_motoravhengig_info():
    """
    Leser inn motoravhengig informasjon som service_speed, motorstørrelse og virkningsgrad per skipstype og lengdegruppe.
    Virkningsgrader er i wide-format (per energibærerer)

    Returns:
        Dataframe: Service speed, motorstørrelse og virkningsgrad per energibærer for hver skipstype og
        lengdegruppe.

    """

    filbane_drivsoffvekter = (
        FRAM_DIRECTORY
        / "kalkpriser"
        / "tid_drivstoff"
        / "nasjonale_drivstoffvekter.xlsx"
    )

    skipsinfo = pd.read_excel(filbane_drivsoffvekter, sheet_name="Sheet1").set_index(
        ["Skipstype", "Lengdegruppe"]
    )

    for col in [
        "service_speed",
        "engine_kw_total",
        "Virkningsgrad_MGO",
        "Virkningsgrad_LNG",
        "Virkningsgrad_NOY",
        "Virkningsgrad_EL",
    ]:
        assert col in skipsinfo

    return skipsinfo[
        [
            "service_speed",
            "engine_kw_total",
            "Virkningsgrad_MGO",
            "Virkningsgrad_LNG",
            "Virkningsgrad_NOY",
            "Virkningsgrad_EL",
        ]
    ]


def get_effektiviseringsfaktor(beregningsaar: List[int]):
    """
    Hvor mye drivstofforbruket reduseres over tid for ulike skipstyper og lengdegrupper.
    Dette er basert på innspill fra DNV GL der kun teknologiutviklingen er tatt
    hensyn til

    Args:
        beregningsaar: liste over år i analyseperioden.

    Returns:
        DataFrame: Hver kolonne er en effektiviseringsfaktor for
        hvert år fra 2018 til 2101. Verdiene varierer med ulike skipstyper
        og lengdegrupper

    """
    effektivisering_2050 = pd.melt(
        forut("Drivstoffeffektivisering", 10).drop("Variabel", axis=1),
        id_vars=["Skipstype"],
        var_name="Lengdegruppe",
        value_name="eff_reduksjon_2050",
    )
    effektivisering_2050["eff_2050"] = 1 - effektivisering_2050["eff_reduksjon_2050"]

    faktorer_for_2050 = interpoler_produkt_vekstfaktor(
        grunnaar=2018,
        verdi_grunnaar=np.ones(len(effektivisering_2050)),
        sluttaar=2050,
        verdi_sluttaar=effektivisering_2050.eff_2050.values,
    )

    df = pd.concat([effektivisering_2050, faktorer_for_2050], axis=1).sort_values(
        by=["Skipstype", "Lengdegruppe"]
    )
    for year in range(2051, max(beregningsaar) + 1):
        df[year] = df["eff_2050"]

    return df.drop(["eff_2050", "eff_reduksjon_2050"], axis=1)


def get_kr_per_enhet_drivstoff(kroneaar: int, beregningsaar: List[int]):
    """
    Drivstoffpriser per enhet drivstoff for en strekning.
    Pris per MJ er multiplisert med energitetthet for å få pris per enhet drivstoff.
    Skiller mellom priser i 2018 og 2050 der det kun er karbonøytrale drivstoff som har endrede priser over perioden.

    Args:
        kroneaar: Kroneåret du vil ha for de kalkprisene virkningen beregner selv
        beregningsaar: liste over de årene du vil ha beregnet virkningen for

    Returns:
        DataFrame: Drivstoffprisen varierer med følgende parametere:

        - Skipstype: En av Kystverkets skipstyper
        - Lengdegruppe: En av lengdegruppene
        - Tankersted:

            - SØR: sør for Trondheim
            - NORD: nord for Trondheim
            - INT: internasjonalt

        - Fueltype: Hvilken fueltype du ser på. Har priser for følgende typer:

            - MGO og HFO
            - Elektrisitet
            - LNG
            - Karbonøytrale drivstoff

    """

    drivstoffpriser = (
        forut("Drivstoffpriser", 7)
        .rename(columns={2018: "pris_2018", 2050: "pris_2050"})
        .assign(
            pris_2018=lambda x: prisjustering(
                belop=x.pris_2018,
                utgangsaar=int(x.Kroneverdi.values[0]),
                tilaar=kroneaar,
            )
        )
        .assign(
            pris_2050=lambda x: prisjustering(
                belop=x.pris_2050,
                utgangsaar=int(x.Kroneverdi.values[0]),
                tilaar=kroneaar,
            )
        )
    )

    aarlige_priser = interpoler_produkt_vekstfaktor(
        grunnaar=2018,
        verdi_grunnaar=drivstoffpriser.pris_2018.values,
        sluttaar=2050,
        verdi_sluttaar=drivstoffpriser.pris_2050.values,
    )
    priser = pd.concat([drivstoffpriser, aarlige_priser], axis=1, sort=False).drop(
        ["pris_2018", "pris_2050", "gammel lengdegruppe", "Kroneverdi"], axis=1
    )
    for year in range(2051, max(beregningsaar) + 1):
        priser[year] = priser[2050]
    return priser


@verbose_schema_error
def get_drivstoffandeler(beregningsaar: List[int]) -> DataFrame[DrivstoffandelerSchema]:
    """
    Fuelmiksen for ulike skipstyper og lengdegrupper hvert år fremover.
    Altså andelen av skipene som bruker ulike typer drivstoff.

    Args:
        beregningsaar: liste over de årene du vil ha beregnet virkningen for

    Returns:
        DataFrame: Hver kolonne er et år fra 2018 til 2101.
        Hver rad spesifiserer en skipstype, lengdegruppe og fuel type.

    """
    innlest = (
        forut("Drivstoffmiks", 13)
        .assign(Drivstofftype = lambda df: df["Drivstofftype kategori 1"].map(KONVERTERER_NYE_TIL_FRAM_DRIVSTOFFTYPER))
    )
    eksisterende_aar = sorted(innlest["År"].unique())
    siste_aar = max(max(beregningsaar), max(eksisterende_aar))
    skal_droppes = ["Drivstofftype kategori 1", "Drivstofftype kategori 2", "Modus", "Område"]
    interpolert = (
        pd.melt(
            innlest.loc[lambda df: (df.Modus == "Seilas") & (df["Område"] == "Territorial")].drop(skal_droppes, axis=1),
            id_vars=["Skipstype", "Drivstofftype", "År"],
            var_name="Lengdegruppe",
            value_name="andel_fuel",
        )
        .assign(Lengdegruppe=lambda df: df.Lengdegruppe.str.replace("m", "").str.strip().str.replace("  -", "-"))
        .groupby(["Skipstype", "Lengdegruppe", "Drivstofftype", "År"])
        .sum()
        .unstack("År")
        .pipe(_dropp_overste_kolonnenavnnivaa)
        .pipe(
            interpoler_aarvis,
            faste_kolonner=eksisterende_aar,
            siste_kolonne=siste_aar
        )
    )
    assert np.allclose(interpolert.groupby(["Skipstype", "Lengdegruppe"])[beregningsaar].sum(), 1)
    output = interpolert.reset_index()
    DrivstoffandelerSchema.validate(output)
    return output

def utslipp_til_luft_per_time(hastighetsmatrise, beregningsaar: List[int]):
    """
    Beregner utslipp til luft per time for gitt hastighet. Beregner utslipp
    av NOx, PM10 of CO2. Funksjonen henter etterspurt drivstoff per time og ganger med
    kilogram utslipp per enhet drivstoff.
    Har multiplisert kg utslipp per MJ med energitetthet for å få kg utslipp per enhet drivstoff.

    Args:
        hastighetsmatrise (DataFrame): Matrise over hastighet per rute for ulike skipstyper og lengdegrupper
        beregningsaar: liste over de årene du vil ha beregnet virkningen for

    Returns:
        Dataframe: Utslipp til luft (KG) per time fordelt på ulike type utslipp og ulike skipstyper, ruter
        og lengdegrupper.

    """
    # Etterspurt mengde drivstoff per time
    ettersp_drivstoff_per_time = (
        get_ettersp_drivstoff_per_time(beregningsaar,hastighetsmatrise)
        .reset_index()
        .set_index(["Skipstype", "Lengdegruppe", "Drivstofftype", "Rute"])
        .rename(columns=lambda x: f"drivstoff_{x}")
        .reset_index()
    )

    kg_per_enhet_raw = pd.pivot_table(
        forut("Utslippluft", antall_kolonner=3).rename(columns={"År": "aar"}),
        values="kg/enhet",
        index=["Drivstofftype", "Type"],
        columns="aar",
    )

    kg_per_enhet = (
        interpoler_linear_vekstfaktor(
            grunnaar=2018,
            verdi_grunnaar=kg_per_enhet_raw[2018].values,
            sluttaar=2050,
            verdi_sluttaar=kg_per_enhet_raw[2050].values,
        )
        .set_index(kg_per_enhet_raw.index)
        .rename(columns=lambda x: f"kg_{x}")
        .reset_index()
    )
    for year in range(2051, 2140):
        kg_per_enhet[f"kg_{year}"] = kg_per_enhet["kg_2050"]

    kg_per_time = ettersp_drivstoff_per_time.merge(
        right=kg_per_enhet, on="Drivstofftype"
    )
    for year in beregningsaar:
        kg_per_time[year] = kg_per_time[f"kg_{year}"] * kg_per_time[f"drivstoff_{year}"]
    kg_per_time = kg_per_time.groupby(["Skipstype", "Lengdegruppe", "Rute", "Type"])[
        beregningsaar
    ].sum()

    return kg_per_time


def oversett_rute_til_bolge(rute):
    """
    IKKE I BRUK: Oversetter en gitt rute til et område vi har hentet bolgedata fra
    """
    return None

def interpoler_aarvis(df, faste_kolonner, siste_kolonne):
    """
    Interploerer mellom alle år i df (gitt ved listen faste kolonner) og forlenger site år til siste_kolonne

    Benyttes til å omdanne drivstoffmiksen med kolonner for e.g. 2019, 2026 og 2040 til å ha alle år fra og med
    2019 til og med 2100 ved å skrive `interpoler_aarvis(df, [2019, 2026, 2040], 2100)`.


    Args:
        df: DataFramen med dataen du vil interpolere
        faste_kolonner: kolonnene du vil interpolere lineært mellom
        siste_kolonne: kolonnen du vil strekke resultatet til, der siste år i faste_kolonner gjentas konstant til siste_kolonne

    Returns:

    """
    alle_kolonner = list(range(min(faste_kolonner), siste_kolonne + 1))
    interpolert = []
    for (lav, hoy) in zip(faste_kolonner[:-1], faste_kolonner[1:]):
        interpolert.append(interpoler_linear_vekstfaktor(
            grunnaar=lav,
            verdi_grunnaar=df[lav].astype(float).values,
            sluttaar=hoy,
            verdi_sluttaar=df[hoy].astype(float).values,
        )
        )
    for year in range(max(faste_kolonner)+1, siste_kolonne + 1):
        interpolert.append(pd.Series(df[max(faste_kolonner)].astype(float).values, name=year))
    ferdig = (
        pd.concat([df.reset_index()] + interpolert, axis=1)
        .set_index(df.index.names)
        .loc[:, lambda df: ~df.columns.duplicated()]
        [alle_kolonner]
    )
    return ferdig


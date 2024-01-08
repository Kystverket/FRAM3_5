"""Her ligger kode for innlesing av IWRAP-filer og for å omsette disse i faktiske hendelser basert på trafikk"""
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from pandas import ExcelFile

from fram.generelle_hjelpemoduler.konstanter import LENGDEGRUPPER_UTEN_MANGLER
from fram.virkninger.risiko.hjelpemoduler import generelle as generelle_hjelpemoduler


class Risikoanalyser:
    def __init__(self, ra_dir: Path, les_paa_nytt: bool = False, logger: callable = None):
        """Klasse for å lese inn og holde styr på risikoanalysene

        Risikoanalysene mottas i standardformaterte Excel-ark. Vi leser dem inn, og masserer dem slik at de passer
            i videre SØA-beregninger. Denne klassen kan lese inn, enten fra råkjøringer eller fra mellomlagret fil

        Args:
            les_paa_nytt: Angir om du skal tvinge til å lese på nytt selv om den skulle finne mellomlagrede
            RA-innlesinger
            logger: En logger du eventuelt vil logge til. Praktisk når denne kalles fra SØA-klassen som allerede logger
        """
        if logger is None:
            import logging as logger
        self.logger = logger

        self.les_paa_nytt = les_paa_nytt

        self.ra_dir = ra_dir
        self.ra = self.get_risikoanalyser(
            mappe_til_ra=self.ra_dir, les_paa_nytt=les_paa_nytt
        )

    def __repr__(self):
        return f"Risikoanalyser(les_på_nytt={self.les_paa_nytt})"

    def __call__(self, risikoanalysenavn: Union[str, list] = None):
        """Henter inn risikoanalysene, enten noen eller alle

        Args:
            risikoanalysenavn: En ra, eller en liste med raer du ønsker å hente ut. Default er None,
                hvilket betyr at alle hentes.
        """
        if risikoanalysenavn is None:
            relevante_ra = self.ra
        else:
            if isinstance(risikoanalysenavn, str):
                risikoanalysenavn = [risikoanalysenavn]
            for navn in risikoanalysenavn:
                if navn not in list(self.ra):
                    raise KeyError(
                        f"Finner ikke {navn} blant risikoanalysene. Må du kanskje lese dem inn på nytt?"
                    )
            relevante_ra = self.ra[risikoanalysenavn]
        return relevante_ra

    def get_risikoanalyser(self, mappe_til_ra, les_paa_nytt):
        """Leser inn alle risikoanalysene i 'mappe_til_ra' og returnerer en df

        Denne looper over alle filene i mappen, og alle arkene i hver fil, og leser dem inn. Henter ut `jobname`,
        `year` og hendelsene. Disse to parameterne vil unikt definere en RA.

        Args:
            mappe_til_ra (pathlib.Path): Bane til der RA-filene ligger
            les_paa_nytt (bool): Hvorvidt vi tvinger til å lese på nytt selv om det finnes mellomlagrede

        Returns:
            DataFrame: Standardformatert dataframe med alle de funnede ra, der kolonnene jobname og year er lagt til
        """
        # Sjekker først om det finnes en forhåndsinnlest RA, det sparer tid
        RA_FERDIGLEST = self.ra_dir / "innlest_ra.json"
        if (not les_paa_nytt) and RA_FERDIGLEST.is_file():
            self.logger.info("    Leser risikoanalyser fra mellomlagret json-fil")
            risikoanalyser = pd.read_json(RA_FERDIGLEST).sort_index()
            return risikoanalyser

        self.logger.info(
            "    Leser risikoanalyser på nytt fra underliggende excel-filer"
        )

        # Ellers looper den over alle RAene i mappen, og alle arkene med "Frekvens IWRAP" i navnet sitt, og leser dem inn

        risikoanalyser = []
        for file in mappe_til_ra.rglob("*.xlsx"):
            wb = pd.ExcelFile(file)
            sheetnames = wb.sheet_names
            for sheet in sheetnames:
                if "Frekvens IWRAP" in sheet:
                    jobname, year = wb.parse(
                        sheet, usecols=[1], skiprows=2, nrows=2, header=None
                    )[1].values
                    year = int(year)
                    df = Risikoanalyser.parse_RA_output(wb, sheet).assign(
                        jobname=jobname, aar=year
                    )
                    risikoanalyser.append(df)

        risikoanalyser = pd.concat(risikoanalyser, sort=False).reset_index(drop=True)

        risikoanalyser.to_json(RA_FERDIGLEST)

        return risikoanalyser

    @staticmethod
    def parse_RA_output(excelfil: Union[str, Path, ExcelFile], arknavn: str):
        """Leser inn ett risikoanalyseark fra DNV GL, på avtalt format

        Henter ut antall grunnstøtinger og kontaktskader. For kollisjoner vil vi ha både striking og struck. Ettersom
        vi i et par ark oppgavet feil summeringsformler, leser vi selv ut summen fra arkene. Det vil si at striking
        er summen av alle ganger et skip kjører på andre skip, mens struck er summen av alle de gangene et skip blir
        påkjørt av andre.

        Args:
            excelfil: Filbanen til excel-filen fra risikoanalysen
            arknavn: Arket vi skal lese inn fra

        Returns:
            DataFrame: Standardformatert dataframe med risikoanalysene for det angitte excelarket.
        """

        hendelsesliste = {
            # "Struck": (26, 16, 8),
            # "Striking": (57, 16, 8),
            "Grunnstøting": (77, 16, 9),
            "Kontaktskade": (108, 16, 9),
        }
        dfs = []
        for hendelse, (skiprows, nrows, usecols) in hendelsesliste.items():
            df = (
                pd.read_excel(
                    excelfil,
                    sheet_name=arknavn,
                    skiprows=skiprows,
                    nrows=nrows,
                    usecols=list(range(usecols)),
                )
                .rename(columns={"Skipstype Kystverket": "Skipstype"})
                .assign(Hendelsestype=hendelse)
            )
            for l in LENGDEGRUPPER_UTEN_MANGLER:
                if l not in df.columns:
                    raise KeyError(
                        f"Finner ikke lengdegruppe {l} i {hendelse} RA {excelfil} ark {arknavn}"
                    )
            dfs.append(df)
        # Leser inn den utvidede matrisen for å lage våre egne summer for striking og struck
        utvidet_matrise = pd.read_excel(
            excelfil,
            sheet_name=arknavn,
            skiprows=139,
            nrows=145,
            usecols=list(range(146)),
        ).fillna(method="ffill")
        utvidet_matrise.columns = (
            pd.Series(utvidet_matrise.columns)
            .where(lambda x: ~x.str.contains("Unnamed"), np.nan)
            .fillna(method="ffill")
            .fillna({0: "Skipstype", 1: "Lengdegruppe"})
        )
        struck = (
            utvidet_matrise.set_index(["Skipstype", "Lengdegruppe"])
            .iloc[1:]
            .sum(axis=1)
            .to_frame()
            .unstack(-1)
            .pipe(generelle_hjelpemoduler._dropp_overste_kolonnenavnnivaa)
            .pipe(generelle_hjelpemoduler._erstatt_lengdegrupper)
            .reset_index()
            .fillna(0)
            .assign(Hendelsestype="Struck")
        )

        striking = utvidet_matrise.T.reset_index()
        striking.iloc[0, 1] = "Lengdegruppe"
        striking.columns = striking.iloc[0]
        striking = (
            striking.iloc[2:]
            .set_index(["Skipstype", "Lengdegruppe"])
            .sum(axis=1)
            .to_frame()
            .unstack()
            .pipe(generelle_hjelpemoduler._dropp_overste_kolonnenavnnivaa)
            .pipe(generelle_hjelpemoduler._erstatt_lengdegrupper)
            .reset_index()
            .fillna(0)
            .assign(Hendelsestype="Striking")
        )
        risikoanalyser = pd.concat(dfs + [striking, struck], sort=False, axis=0)

        risikoanalyser = pd.melt(
            risikoanalyser,
            id_vars=["Hendelsestype", "Skipstype"],
            value_vars=LENGDEGRUPPER_UTEN_MANGLER,
            var_name="Lengdegruppe",
            value_name="Hendelser",
        ).reset_index(drop=True)

        return risikoanalyser

    def hent_ra_resultater(self, ra_navn):
        """Henter risikoanalysene basert på de jobnamene som er angitt i SØA-inputen"""

        # Kobler på
        koblet = (
            ra_navn.dropna()
            .merge(
                right=self(),
                left_on=["Risikoanalyse", "ra_aar"],
                right_on=["jobname", "aar"],
                how="left",
                indicator=True,
            )
            .dropna()
        )
        # Sjekk at alle matchet, ellers blir det feilmelding
        if not koblet._merge.value_counts()["both"] == len(koblet):
            mangler = koblet.reset_index().loc[
                lambda df: df._merge != "both",
                ["Skipstype", "Lengdegruppe", "Risikoanalyse", "jobname"],
            ]
            print(mangler)
            raise KeyError("Fant ikke RA for alle de angitte risikoanalysenavnene")

        # Hvis den finner de gamle lengdegruppene i RAene, gir den en advarsel
        if "21-28" in koblet.Lengdegruppe.unique():
            self.logger.warning(
                "RAene inneholder de gamle lengdegruppene. Dette er feil! \n Disser er antakelig lest inn fra mellomlagret json-fil. Slett denne og les inn på nytt fra Excel\n"
            )

        return koblet



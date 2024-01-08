"""Inneholder klasse for å gjøre SØA farledsanalyser
"""
import io
import logging
import os
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Union, Optional, List

import numpy as np
import pandas as pd
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler import excel as hjelpemoduler_excel
from fram.generelle_hjelpemoduler import trafikk as hjelpemoduler_trafikk
from fram.generelle_hjelpemoduler.excel import (
    _fra_excel,
    _fyll_ut_fra_alle,
    _lag_excel_forside,
)
from fram.generelle_hjelpemoduler.hjelpefunksjoner import (
    lag_kontantstrom,
    forut,
    get_forut_verdi,
    _legg_til_kolonne,
    legg_til_kolonne_hvis_mangler
)
from fram.generelle_hjelpemoduler.kalkpriser import diskontering
from fram.generelle_hjelpemoduler.konstanter import (
    VIRKNINGSNAVN,
    SKATTEFINANSIERINGSKOSTNAD,
    LENGDEGRUPPER,
    SKIPSTYPER,
    FRAM_DIRECTORY,
    TRAFIKK_COLS,
    DelvisFRAMFeil,
    FOLSOMHETSVARIABLER,
    FOLSOMHET_COLS,
    FOLSOMHET_KOLONNE,
    FOLSOM_KARBON_HOY,
    FOLSOM_KARBON_LAV,
    AKTØR_VIRKNING_MAPPING,
    KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG,
    KOLONNENAVN_STREKNING,
)
from fram.generelle_hjelpemoduler.version import __version__
from fram.virkninger.drivstoff.virkning import Drivstoff
from fram.virkninger.investering.hjelpemoduler import legg_til_utslipp_hvis_mangler
from fram.virkninger.investering.virkning import Investeringskostnader
from fram.virkninger.kontantstrommer.virkning import Kontantstrommer
from fram.virkninger.risiko.hjelpemoduler import iwrap_fremskrivinger
from fram.virkninger.risiko.hjelpemoduler.aisyrisk import konverter_aisyrisk_lengdegrupper, fordel_og_fremskriv_ra
from fram.virkninger.risiko.hjelpemoduler.fellesoppsett_kalkpriser import les_inn_kalkpriser_utslipp
from fram.virkninger.risiko.hjelpemoduler.generelle import les_inn_hvilke_ra_som_brukes_fra_fram_input
from fram.virkninger.risiko.hjelpemoduler.iwrap_innlesing import Risikoanalyser
from fram.virkninger.risiko.hjelpemoduler.konsekvensreduksjoner import les_inn_konsekvensmatriser
from fram.virkninger.risiko.hjelpemoduler.verdsetting import (
    get_kalkpris_materielle_skader,
    get_kalkpris_helse,
)
from fram.virkninger.risiko.schemas import HendelseSchema
from fram.virkninger.risiko.virkning import Risiko
from fram.virkninger.sedimenter.virkning import Sedimenter
from fram.virkninger.tid.hjelpemoduler import fremskriv_konstant_tidsbruk_per_passering
from fram.virkninger.tid.verdsetting import get_kalkpris_tid
from fram.virkninger.tid.virkning import Tidsbruk
from fram.virkninger.utslipp_til_luft.virkning import Utslipp_til_luft
from fram.virkninger.vedlikehold.virkning import Vedlikeholdskostnader
from fram.virkninger.ventetid.excel import les_ventetidsinput_fra_excel
from fram.virkninger.ventetid.virkning import Ventetid
from fram.virkninger.virkning import Virkninger

from fram.virkninger.kontantstrommer.hjelpemoduler import legg_til_aktør_hvis_mangler


class FRAM:
    def __init__(
        self,
        strekning: Union[str, Path] = None,
        tiltakspakke: int = 1,
        sammenstillingsaar: Optional[int] = None,
        ferdigstillelsesaar: Optional[int] = None,
        analyseperiode: Optional[int] = None,
        levetid: Optional[int] = None,
        trafikkgrunnlagsaar: Optional[int] = 2019,
        sluttaar: Optional[int] = None,
        andre_skip_til_null: Optional[bool] = True,
        delvis_fram: bool = False,
        logging_level: str = "DEBUG",
        ra_dir: Optional[Union[str, Path]] = None,
        aisyrisk_input=False,
        les_RA_paa_nytt: bool = False,
        folsomhetsanalyser: Optional[Union[bool, Iterable]] = False,
    ):
        """
        Setter opp den samfunnsøkonomiske analysen for den angitte strekningen. Foretar datavalidering og
        fremskriver trafikk, trafikale endringer og risikoendringer basert på tilhørende standardisert input.
        Inputen må foreligge i et Excel-ark med stram formatering. Et eksempel på denne kan fås ved å
        initialisere klassen uten strekningsargumentet.

        For å ser mer dokumentasjon om modellen - sjekk: http://tinyurl.com/framdokumentasjon

        Modellen beregner følgende virkninger:

        - Distanseavhengige kostnader
        - Tidsavhengige kostnader
        - Lokale utslipp til luft (PM10 og NOX)
        - Globale utslipp til luft (CO2)
        - Oppgraderings- og vedlikeholdskostnader av merker
        - Investeringskostnader
        - Skattefinansieringskostnader
        - ulykkeskostnader ved grunnstøting, kontatkskade og kollisjoner:
            - Reparasjonskostnader som følge av materielle skader
            - Tid ute av drift som følge av materielle skader
            - Personskader
            - Dødsfall
            - Utslipp av olje og opprenskingskostnader
        - Nytte ved opprensking av forurensede sedimenter

        Args:
            - strekning:
                En streng eller en filbane. Strenger konverteres til filbaner. Den forventer
                at filen den finner der, følger formateringsreglene. Husk at filen må ha samme navn
                som strekningen spesifisert i excelarket.
            - tiltakspakke:
                Int, hvilken tiltakspakke (fane i input-arket) vi skal beregne
                effekter på. Default er 1.
            - sammenstillingsaar:
                Int, det året vi diskonterer til. Default er sammenstillingsåret
                spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram. Dersom verdi i initalisering vil denne overskrive det som ligger i excelfilen.
            - ferdigstillelsesår:
                Int, åpningsåret, det året tiltakene er ferdigstilt,
                og derfor det året vi teller nytte fra. Default er forutsetning
                spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram. Dersom verdi i initalisering vil denne overskrive det som ligger i excelfilen.
            - analysepeperiode:
                Int, bestemmer hvor stor andel av nytten som havner "før" restverdi. FRAM regner nytte over hele levetiden, men deler det opp i nåverdi
                over analyseperioden og en resterverdi. Default er forutsetning spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram.
            - levetid:
                Antall års levetid for tiltaket, altså perioden det vil regnes
                virkninger for (både analyseperiode og restverdi)
            - trafikkgrunnlagsaar:
                Int, det året trafikktellingene er basert på. Default er at dette hentes fra inputboken for strekningen. Ellers defaulter den til 2019.
            - andre_skip_til_null:
                Bool, hvorvidt vi nuller alle skip i skipstypen 'Annet'. Default er
                true.
            - delvis_fram:
                Hvorvidt det er meningen, og dermed tillatt, å kjøre en FRAM uten at det defineres trafikk, tidsavhengige,
                distanseavhengige og risiko
            - logging_level:
                Justerer hvor mye output du vil ha fra prosessen. Ved vanlig drift
                er 'INFO' ok. Mulige verdier er 'DEBUG', 'INFO', 'WARNING', 'ERROR', og 'CRITICAL'
            - ra_dir:
                pathlib.Path som peker til hvor RA-filene fra IWRAP ligger. Defaulter til banen der Excel-input ligger,
                og mappen risikoanalyser ved siden av Excel-filen
            - les_RA_paa_nytt:
                Hvorvidt IWRAP-RA skal tvangsleses fra underliggende excel-filer, default er False
            - folsomhetsanalyser:
                Hvorvidt følsomhetsanalyser skal kjøres. Kan også være en liste med egendefinerte faktorer som skal ganges
                inn i input for hver virkning, eller en dict med analysenavn som nøkler og en dict med variabelnavn som
                nøkler og faktorer som verdier som verdier.
                Standard hvis True oppgis med hhv. 0.8 og 1.2 for alle variabler.

        """
        # Versjonen av FRAM du er på. Oppdateres ved oppdateringer
        self.version = "FRAM" + __version__

        # legger til faktorer for følsomhetsanalyser
        self._faktorer = {
            "standardkjøring": dict(
                zip(FOLSOMHETSVARIABLER, [1 for _ in range(len(FOLSOMHETSVARIABLER))])
            ),
            FOLSOM_KARBON_HOY: dict(
                zip(FOLSOMHETSVARIABLER, [1 for _ in range(len(FOLSOMHETSVARIABLER))])
            ),
            FOLSOM_KARBON_LAV: dict(
                zip(FOLSOMHETSVARIABLER, [1 for _ in range(len(FOLSOMHETSVARIABLER))])
            ),
        }
        self.oppdater_faktorer(folsomhetsanalyser)

        # initialiserer objektvariabler
        self.trafikk_referanse = None
        self.trafikk_tiltak = None
        self.overforing = None
        self.prognoser = None
        self._fremskrevet_tid_ref = None
        self._fremskrevet_tid_tiltak = None
        self._hastighet_ref = None
        self._hastighet_tiltak = None
        self.hendelser_ref = None
        self.hendelser_tiltak = None
        self.fremskrevet_hendelsesreduksjon = None
        self.konsekvensmatrise_ref = None
        self.konsekvensmatrise_tiltak = None
        self.utslipp_anleggsfasen = None

        self.virkninger: Virkninger = Virkninger()

        self.aisyrisk_input = aisyrisk_input
        self.les_RA_paa_nytt = les_RA_paa_nytt

        # Setter opp logging
        self._set_up_logger(logging_level=logging_level)

        input_filbane = hjelpemoduler_excel._parse_strekning(strekning)

        # Lagrer filbanen og strekningsnavnet på self
        self.input_filbane = pd.ExcelFile(input_filbane)
        self.strekning = input_filbane.stem
        self.tiltakspakke = tiltakspakke
        self.tiltaksomraade = None
        self.analyseomraader = sorted(
            hjelpemoduler_excel
            .les_inn_bruttoliste_pakker_skip_lengder(
                self.input_filbane
            )
            .reset_index()
            .loc[lambda df: df.Tiltakspakke == self.tiltakspakke]
            .Analyseomraade.unique()
        )
        self.andre_skip_til_null = andre_skip_til_null
        self.delvis_fram = delvis_fram

        # Perioder - antall år
        self.analyseperiode_lengde = analyseperiode or int(get_forut_verdi("Analyseperiode"))
        self.levetid_lengde = levetid or int(get_forut_verdi("Levetid"))

        # Årstall
        self.kroneaar = int(get_forut_verdi("Kroneår"))
        self.sammenstillingsaar = sammenstillingsaar or int(get_forut_verdi("Sammenstillingsår"))
        self.ferdigstillelsesaar = ferdigstillelsesaar or int(get_forut_verdi("Ferdigstillelsesår"))
        self.analysestart = datetime.now().year
        try:
            self.trafikkgrunnlagsaar = int(
            str(_fra_excel(self.input_filbane, "Trafikkgrunnlag").columns.tolist()[-1]).replace("Pass_", ""))
        except ValueError as e:
            if not self.delvis_fram:
                raise DelvisFRAMFeil(f"Finner ikke arket Trafikkgrunlag for å kunne lese ut trafikkgrunnlagsåret")
            self.trafikkgrunnlagsaar = trafikkgrunnlagsaar

        self.sluttaar = self.ferdigstillelsesaar + self.levetid_lengde
        self.analyseperiode_slutt = self.ferdigstillelsesaar + self.analyseperiode_lengde

        # Årstallsrekker
        self.trafikkaar = list(range(self.trafikkgrunnlagsaar, self.sluttaar))
        self.beregningsaar = list(range(self.ferdigstillelsesaar, self.sluttaar))

        self.levetid = list(range(self.analysestart, self.sluttaar))
        self.analyseperiode = list(range(self.analysestart, self.analyseperiode_slutt))

        if ra_dir is None:
            self.ra_dir = input_filbane.parent / "risikoanalyser"
        else:
            self.ra_dir = Path(ra_dir)

        self._infologger(
            f"Dette er {self.version}, Kystverkets beregningsverktøy for samfunnsøkonomiske analyser."
        )

        self._infologger(
            f"Setter opp SØA for strekning {self.strekning} og tiltakspakke {self.tiltakspakke}"
        )


        tankested = hjelpemoduler_excel.les_inn_tankested(self.input_filbane, self.logger.warning)
        self.tankested = tankested

        self._infologger("Ferdig satt opp")

    def oppdater_faktorer(self, faktorer):
        if not faktorer:
            return

        if isinstance(faktorer, dict):
            for key, val in faktorer.items():
                assert isinstance(val, dict) and all(
                    [key in FOLSOMHETSVARIABLER for key in val.keys()]
                ), f"Følsomhetsvariablene må være en av {FOLSOMHETSVARIABLER}"

                # legg til ikke-oppgitte faktorer
                for var in [
                    var for var in FOLSOMHETSVARIABLER if var not in val.keys()
                ]:
                    val[var] = 1

            self._faktorer.update(faktorer)

            return

        if isinstance(faktorer, Iterable):
            for faktor in faktorer:
                self._faktorer.update(
                    {
                        f"følsomhetsanalyse_{faktor}": dict(
                            [(var, faktor) for var in FOLSOMHETSVARIABLER]
                        )
                    }
                )

            return

        for faktor in [0.8, 1.2]:
            self._faktorer.update(
                {
                    f"følsomhetsanalyse_{faktor}": dict(
                        [(var, faktor) for var in FOLSOMHETSVARIABLER]
                    )
                }
            )

    def gang_inn_faktorer(self, df, folsomhetsvariabel: str, kolonner: List[str] = None, sett_index: bool = True):
        """
        Funksjon for å gange inn følsomhetsvariabler i en dataframe
        Args:
            df (DataFrame): DataFramen som skal oppdateres
            folsomhetsvariabel: navnet på følsomhetsvariablen som skal ganges inn
            kolonner: Hvis oppgitt, kolonnene som skal ganges inn.
            sett_index: Hvorvidt den nye kolonnen skal legges til i indeksen

        Returns:
            DataFrame: input-dataframen duplisert én gang per tilhørende faktor og med en følsomhetskolonne
        """

        assert (
            folsomhetsvariabel in FOLSOMHETSVARIABLER
        ), f"{folsomhetsvariabel} er ikke en gyldig følsomhetsvariabel"

        if kolonner is None:
            kolonner = df.columns

        df_out = pd.DataFrame()

        for analyse, faktordict in self._faktorer.items():
            faktor = faktordict[folsomhetsvariabel]
            df_faktor = df.copy()
            df_faktor[kolonner] = df_faktor[kolonner] * faktor
            df_faktor[FOLSOMHET_KOLONNE] = analyse
            df_out = pd.concat((df_out, df_faktor), axis=0)

        if sett_index:
            df_out = df_out.set_index(FOLSOMHET_KOLONNE, append=True)

        return df_out

    def __repr__(self):
        return f"FRAM(strekning='{self.strekning}', tiltakspakke={self.tiltakspakke})"

    def __str__(self):
        return f"SØA-beregning for '{self.strekning}'"

    def _set_up_logger(self, logging_level: str):
        """
        Oppretter en logger for modulen. Brukes til å rapportere til stdout ("print") hva som skjer underveis
        mens modellen kjører. Veldig praktisk

        Args:
            logging_level: Gyldig logging level. Default er "DEBUG"
        """
        self.logger = logging.getLogger(str(id(self)))
        level = logging.getLevelName(logging_level)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.logger.setLevel(level)

        # Logger til stdout (altså konsollen)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self._log_capture_string = io.StringIO()
        ch = logging.StreamHandler(self._log_capture_string)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def _infologger(self, message: str):
        """
        Hjelpemetode som logger bare hvis ikke i følsomhetsanalyse

        Denne brukes for å slippe veldig mange loggemeldinger når man kjører følsomhetsanalyse (hvor hver metode
        kalles mange ganger).

        Args:
            message: meldingen som skal sendes til loggeren.
        """
        self.logger.info(message)

    def _logg_ny_virkning(self, virknignsnavn):
        self._infologger(f"--- {virknignsnavn} ---")

    def _virkningslogger(self, virkningsnavn):
        return lambda s: self._infologger(f"  {virkningsnavn}: {s}")

    @property
    def log(self):
        log = self._log_capture_string.getvalue()
        return log.split("\n")

    @property
    def verdsatt_netto(self):
        if len(self.virkninger) == 0 :
            self._infologger("Advarsel: Ingen virkninger funnet")
            return pd.DataFrame()

        verdsatt_netto = pd.concat(
            [v.verdsatt_netto for v in self.virkninger], axis=0, sort=True
        )
        return verdsatt_netto.query("Analysenavn!='Alle'").append(
            pd.concat(
                [
                    verdsatt_netto.query("Analysenavn=='Alle'")
                    .droplevel(FOLSOMHET_KOLONNE)
                    .assign(Analysenavn=analyse)
                    for analyse in self._faktorer.keys()
                ]
            ).set_index(FOLSOMHET_KOLONNE, append=True)
        )

    def _prep_volumvirkning(self, navn: str):
        """ Hjelpemetode som sammenstiller volimvirkninger fra alle virkningene til en felles for hele modellen

        Parameters
        navn: streng som enten er 'volumvirkning_ref' eller 'volumvirkning_tiltak'
        """
        if len(self.virkninger) == 0 or all([getattr(v, navn) is None for v in self.virkninger]):
            self._infologger("Advarsel: Ingen volumvirkninger funnet")
            return pd.DataFrame()

        try:
            return pd.concat(
                [
                    getattr(v, navn)
                    for v in self.virkninger
                    if getattr(v, navn) is not None
                ] + [
                    (
                        self.trafikk_referanse
                        .copy()
                        .assign(Virkningsnavn="Trafikk", Måleenhet="Antall passeringer")
                        .set_index(["Virkningsnavn", "Måleenhet"], append=True)
                    )

                ]  if self.trafikk_referanse is not None else [],
                axis=0,
                sort=True,
            )
        except ValueError:
            return pd.DataFrame()

    @property
    def volumvirkning_ref(self):
        return self._prep_volumvirkning(navn='volumvirkning_ref')

    @property
    def volumvirkning_tiltak(self):
        return self._prep_volumvirkning(navn='volumvirkning_tiltak')

    def kontantstrommer(self, analyse: str = "standardkjøring", aktør_ytterligere_mapping = {'Virkning 1': 'Det offentlige'}):
        """
        Setter sammen diskonterte kontantstrømmer med alle virkningene i modellen. Legger deretter inn aktørinndeling for standardvirkningene i FRAM.

        Args:
            analyse: Navnet på analysen som kontantstrømmer skal hentes for. "standardkjøring" er analysen med alle
                     følsomhetsfaktorer lik 1.
            aktør_ytterligere_mapper: en dictionary med aktørinndeling for kontantstrømmer som ikke er standardvirkninger i fram.

        Returns:
            DataFrame: Kontantstrømmene lagt ut i tid horisontalt, med totalrad nederst
        """
        self._infologger(f"Setter opp kontantstrømmer for {analyse}")

        if analyse not in self._faktorer.keys():
            self._infologger("Fant ikke analyse '{analyse}'")
            return

        diskonteringsfaktorer = diskontering(
            sammenstillingsaar=self.sammenstillingsaar,
            fra_aar=self.analysestart,
            til_aar=self.sluttaar,
        )

        analyseperiode = self.analyseperiode

        # Disse er alle ferdig realprisjusterte, men ikke-diskonterte!
        # Her bruker vi levetiden i stedet for beregningsaar, fordi
        # noen kostnader påløper før første beregningsaar
        verdier = (
            self.verdsatt_netto.query(f"Analysenavn=='{analyse}'")
            .droplevel(FOLSOMHET_KOLONNE)
            .reindex(self.levetid, fill_value=0, axis="columns")
            .groupby(VIRKNINGSNAVN)[self.levetid]
            .sum()
        )
        tidsserier = {
            idx: verdier.loc[idx].to_frame(idx) for idx in verdier.index.values
        }
        # Looper over tidsseriene og beregner nåverdi
        naaverdier = {
            navn: lag_kontantstrom(
                tidsserie, navn, diskonteringsfaktorer, self.levetid, analyseperiode
            )
            for navn, tidsserie in tidsserier.items()
        }
        # Setter dem sammen til en serie kontantstrømmer vi skal bruke


        kontantstr = (
            pd.concat(naaverdier, axis=1, sort=False)
            .reset_index()
            .rename(columns={"index": "År"})
            .set_index("År")
            .T.fillna(0)
        )
        kontantstr = (
            diskonteringsfaktorer.reindex(kontantstr.columns)
            .fillna(0)
            .T.append(kontantstr, sort=False)
            # Legger inn skattekostnader
            .append(
                kontantstr.multiply(
                    self.verdsatt_netto.reset_index()
                    .groupby(VIRKNINGSNAVN)[SKATTEFINANSIERINGSKOSTNAD]
                    .mean(),
                    axis=0,
                )
                .fillna(0)
                .multiply(0.2)
                .sum(axis=0)
                .rename(SKATTEFINANSIERINGSKOSTNAD),
                sort=False,
            )
            .fillna(0)
        )

        # Summerer over alle postene
        kontantstr = kontantstr.append(
            kontantstr.drop(["rente", "diskonteringsfaktor"], axis=0)
            .sum(axis=0)
            .rename("Samfunnsøkonomisk overskudd"),
            sort=False,
        )[["Nåverdi levetid"] + ["Nåverdi analyseperiode"] + self.levetid]

        aktør_total_mapping = AKTØR_VIRKNING_MAPPING.copy()
        aktør_total_mapping.update(aktør_ytterligere_mapping)

        kontantstr = (kontantstr
                        .reset_index()
                        .rename({'index':'Virkninger'}, axis=1)
                        .assign(Aktør = lambda df: df.Virkninger.map(aktør_total_mapping))
                        .set_index(['Aktør', 'Virkninger'])
        )

        return kontantstr

    def run(self, skriv_output: Union[bool,Path,str] = True):
        """
        Kjører SØA og skriver output

        Kaller alle virkningsmetodene:

        - :meth:`FRAM.beregn_trafikk`
        - :meth:`FRAM.beregn_tidsbruk`
        - :meth:`FRAM.beregn_drivstoff`
        - :meth:`FRAM.beregn_risiko`
        - :meth:`FRAM.beregn_utslipp_til_luft`
        - :meth:`FRAM.beregn_ventetid`
        - :meth:`FRAM.beregn_vedlikehold`
        - :meth:`FRAM.beregn_andre_kontantstrommer`
        - :meth:`FRAM.beregn_investeringskostnader` og
        - :meth:`FRAM.beregn_sedimenter`.

        Hvis 'skriv_output' er True, kaller den også :meth:`FRAM.skriv_output`

        Args:
            skriv_output: Hvorvidt det skal skrives output til Excel av kjøringen
        """

        self.beregn_trafikk()
        self.beregn_investeringskostnader()
        self.beregn_tidsbruk()
        self.beregn_drivstoff()
        self.beregn_utslipp_til_luft()
        self.beregn_risiko()
        self.beregn_ventetid()
        self.beregn_vedlikehold()
        self.beregn_andre_kontantstrommer()
        self.beregn_sedimenter()

        self.skriv_output(skriv_output)
        self._infologger("Ferdig beregnet")

    def beregn_trafikk(self):
        """
        Funksjon som beregner forventet trafikk i tiltaks- og referansebane.

        Leser først inn trafikk i grunlagsåret (2019) fra excel. Begrenser til relevant tiltakspakke, forkaster
        trafikkgrunnlaget for skipstypen "Annet" da vi ikke har kalkulasjonspriser for denne skipstypen for alle virkninger.

        Deretter leses grunnprognosene inn, og disse justeres dersom det er fylt inn informasjon fra "Prognoser justert"
        i excel input. Dersom relevant oppdateres prognosene. Deretter leses trafikkoverføringene fra excel input for ruter der man
        forventer trafikkoverføring som følge av tiltakene.

        Til slutt settes alt dette sammen for å lage forventet trafikk i referansebanen og tiltaksbanen.

        Beregner trafikk i referansebanen og trafikk i tiltaksbanen gitt grunnprognoser, justerte prognoser og forventet trafikkoverføring.

        """
        self._logg_ny_virkning("Trafikkgrunnlag og -fremskriving")
        trafikk_logger = self._virkningslogger("Trafikk")
        trafikk_logger("Leser inn grunnlaget")

        if not all(
            [
                ark in self.input_filbane.sheet_names
                for ark in ["Ruteoversikt", "Trafikkgrunnlag", "Grunnprognoser"]
            ]
        ):
            if self.delvis_fram:
                return
            raise DelvisFRAMFeil(
                f"Finner ikke angitt trafikk for tiltakspakke {self.tiltakspakke}"
            )
        trafikk_grunnlagsaar = (
            hjelpemoduler_excel.les_inn_bruttoliste_pakker_skip_lengder(
                self.input_filbane
            )
            .join(_fra_excel(self.input_filbane, "Trafikkgrunnlag"), how="outer")
            .dropna(
                axis=1, how="all"
            )  # Kaste ut tomme kolonner som er feilinnlest fra Excel
            .query("Skipstype != 'Mangler'")
            .query("Tiltakspakke == @self.tiltakspakke")
            .rename(columns={"Pass_2019": 2019, "Pass_2017":2017})
            .pipe(self.gang_inn_faktorer, "Trafikkvolum")
            .dropna()  # Kaster ut rader uten trafikk
        )
        if (len(trafikk_grunnlagsaar) == 0) or trafikk_grunnlagsaar.empty:
            if self.delvis_fram:
                return
            else:
                raise DelvisFRAMFeil(
                    f"Finner ikke angitt trafikk for tiltakspakke {self.tiltakspakke}"
                )

        if self.andre_skip_til_null:
            trafikk_grunnlagsaar = trafikk_grunnlagsaar.query(
                "Skipstype != 'Annet'"
            ).query("Lengdegruppe != 'Mangler lengde'")
            trafikk_logger(
                "Forkaster trafikkgrunnlaget for skipstypen 'Annet' og lengdegruppen 'Mangler lengde'"
            )

        # Leser inn grunnprognosene
        trafikk_logger("Leser inn prognosene")
        grunnprognoser = (
            pd.read_excel(self.input_filbane, sheet_name="Grunnprognoser")
            .assign(
                Lengdegruppe=lambda x: x.Lengdegruppe.str.replace(" ", "").replace(
                    "Manglerlengde", "Mangler lengde"
                )
            )
            .pipe(
                # Etterhvert som de gamle tiltakspakkene blir gamle, har de ikke prognoser for de siste årene av analyseperioden.
                # Vi fyller nå på med nullprognoser på slutten for å sikre at modellen ikke feiler
                legg_til_kolonne_hvis_mangler,
                kolonnenavn=self.trafikkaar,
                fyllverdi=0.0
            )
            .set_index(["Skipstype", "Lengdegruppe"])[self.trafikkaar]
            .astype(float)
            .pipe(lambda x: x + 1)
        )
        grunnprognoser = grunnprognoser.reset_index()
        grunnprognoser.loc[
            grunnprognoser.Lengdegruppe == ">300", "Lengdegruppe"
        ] = "300-"
        grunnprognoser = grunnprognoser.set_index(["Skipstype", "Lengdegruppe"])[
            self.trafikkaar
        ]
        # i RA er det lagt inn at lengdegruppe > 300 er 300-

        prognoser = (
            trafikk_grunnlagsaar.reset_index()
            .drop(self.trafikkgrunnlagsaar, axis=1)
            .merge(
                right=grunnprognoser,
                left_on=["Skipstype", "Lengdegruppe"],
                right_index=True,
                how="left",
            )
            .assign(Tiltaksomraade=lambda x: x.Tiltaksomraade.astype(int))
            .set_index(FOLSOMHET_COLS, drop=True)
            .dropna()
        )
        # Fyller på med spesifikke prognoser dersom angitt
        spesifikke_prognoser = (
            pd.read_excel(self.input_filbane, sheet_name="Prognoser justert")
            .set_index(TRAFIKK_COLS)
            .pipe(lambda x: x + 1)
            .dropna(axis=1, how="all")
            .dropna(how="all")
        )
        if len(spesifikke_prognoser) > 0:
            prognoser.update(spesifikke_prognoser)

        prognoser = prognoser.reset_index()
        prognoser.loc[prognoser.Lengdegruppe == ">300", "Lengdegruppe"] = "300-"
        prognoser = prognoser.set_index(FOLSOMHET_COLS)

        hjelpemoduler_trafikk.valider_at_prognoser_for_all_trafikk(
            trafikk_grunnlagsaar=trafikk_grunnlagsaar, prognoser=prognoser
        )
        self.prognoser = prognoser

        # Leser inn trafikkoverføring
        trafikk_logger("Leser inn trafikkoverføringene")
        overforing = _fra_excel(
            filbane=self.input_filbane,
            ark=f"Tiltakspakke {self.tiltakspakke}",
            skiprows=1,
            usecols=range(10),
        ).reset_index()

        if len(overforing.dropna()) > 0:
            self.overforing = (
                overforing.pipe(
                    _fyll_ut_fra_alle, kolonne="Skipstype", fyllverdier=SKIPSTYPER
                )
                .pipe(
                    _fyll_ut_fra_alle,
                    kolonne="Lengdegruppe",
                    fyllverdier=LENGDEGRUPPER,
                )
                .set_index(TRAFIKK_COLS, drop=True)
            )

        trafikk_logger("Fremskriver og overfører")
        if len(trafikk_grunnlagsaar) == 0 or len(self.prognoser) == 0:
            if self.delvis_fram:
                self._infologger(
                    "  Kjører videre uten trafikkgrunnlag. Svært få virkninger kan beregnes"
                )
                return
            else:
                raise DelvisFRAMFeil(
                    "Det er ikke tillatt å mangle trafikkgrunnlag med mindre 'delvis_fram' er angitt som input til FRAM"
                )

        (
            self.trafikk_referanse,
            self.trafikk_tiltak,
        ) = hjelpemoduler_trafikk.fremskriv_trafikk(
            trafikk_grunnlagsaar=trafikk_grunnlagsaar,
            prognoser=self.prognoser,
            overforing=self.overforing,
            trafikkaar=self.trafikkaar,
            ferdigstillelsesaar=self.ferdigstillelsesaar,
            rute_til_analyseomraade=dict(
                zip(
                    hjelpemoduler_excel.les_inn_bruttoliste_pakker_skip_lengder(
                        self.input_filbane
                    )
                    .reset_index()
                    .Rute.values,
                    hjelpemoduler_excel.les_inn_bruttoliste_pakker_skip_lengder(
                        self.input_filbane
                    )
                    .reset_index()
                    .Analyseomraade.values,
                )
            ),
            tiltakspakke=self.tiltakspakke,
        )

        self.tiltaksomraade = self.trafikk_tiltak.reset_index().Tiltaksomraade.unique()[0]

    def beregn_ventetid(self, num_periods_to_simulate: int = 100_000, seed: int = 1):
        # Ventetidssituasjon - Lager en dataframe med input-ark-par til ventetidsberegninger
        """
        Funksjon for å beregne ventetid og verdsette endringen i ventetid.
        Leser først inn ventetidssituasjoner fra Excel. Deretter tilpasses inputen slik at man kan beregne forventet
        ventetid i referanse- og tiltaksbanen, og deretter verdsette denne ventetiden.

        Bruker beregningsmetodikk fra: :py:.*?:`~fram.virkninger.ventetid`

        Bruker informasjon om tidsavhengige kalkulasjonspriser, trafikk i referanse- og tiltaksbanen og beregningsår fra
        FRAM:

        - Tidsavhengige kalkulasjonspriser: self.kalkpriser_tid
        - Trafikk referanse: self.trafikk_referanse
        - Trafikk tiltak: self.trafikk_tiltak
        - beregningsaar: self.beregningsaar

        Beregner verdsatt endring i ventetid.

        Args:
            num_periods_to_simulate: Antall trekninger. Defaulter til 100 000.
            seed: Seed til psedutilfeldig tallgenerator for å sikre gjenskapbare simuleringer. Defaulter til 1.


        """
        self._logg_ny_virkning("Ventetid")
        ventetid_logger = self._virkningslogger("Ventetid")

        if not any(["ventetid" in ark for ark in self.input_filbane.sheet_names]):
            ventetid_logger(
                "Fant ingen ventetidsark oppgitt i input. Beregner videre uten ventetid"
            )
            return

        if self.trafikk_referanse is None:
            ventetid_logger(
                "Kan ikke beregne ventetid uten trafikk i (minst) referansebanen. Beregner videre uten ventetid"
            )
            return

        ventetid_logger("Leser inn ventetidssituasjoner fra Excel")
        ventetid_input = hjelpemoduler_excel.les_inn_ventetidssituasjoner_fra_excel(
            self.input_filbane, self.tiltakspakke
        ).merge(
            right=self.trafikk_referanse.reset_index()[
                [
                    "Strekning",
                    "Tiltaksomraade",
                    "Tiltakspakke",
                    "Analyseomraade",
                    "Rute",
                ]
            ].drop_duplicates(),
            on="Rute",
            how="left",
        )[
            [
                "Strekning",
                "Tiltaksomraade",
                "Tiltakspakke",
                "Analyseomraade",
                "Rute",
                "ark_ref",
                "ark_tiltak",
            ]
        ]

        try:
            antall_ventetidssituasjoner = ventetid_input.shape[0]
        except:
            antall_ventetidssituasjoner = 0
        ventetid_logger(
            f"Fant {antall_ventetidssituasjoner} ventetidssituasjoner angitt"
        )
        if antall_ventetidssituasjoner == 0:
            ventetid_logger("Beregner ikke ventetidgst")
            return

        ventetidsvirkning = Ventetid(
            kalkpris_tid=self.kalkpriser_tid,
            trafikk_ref=self.trafikk_referanse,
            trafikk_tiltak=self.trafikk_tiltak,
            beregningsaar=self.beregningsaar,
            logger=ventetid_logger,
        )

        for index, row in ventetid_input.iterrows():
            ark_ref = row["ark_ref"]
            ark_tiltak = row["ark_tiltak"]
            simuleringsinput_ref = les_ventetidsinput_fra_excel(
                filepath=self.input_filbane,
                sheet_name=ark_ref,
                num_periods=num_periods_to_simulate,
            )
            simuleringsinput_tiltak = les_ventetidsinput_fra_excel(
                filepath=self.input_filbane,
                sheet_name=ark_tiltak,
                num_periods=num_periods_to_simulate,
            )

            simuleringsinput_ref.lambda_df = simuleringsinput_ref.lambda_df.pipe(
                self.gang_inn_faktorer,
                "Trafikkvolum",
                [str(i) for i in self.beregningsaar],
            )
            simuleringsinput_tiltak.lambda_df = simuleringsinput_tiltak.lambda_df.pipe(
                self.gang_inn_faktorer,
                "Trafikkvolum",
                [str(i) for i in self.beregningsaar],
            )

            ventetidsvirkning.beregn(
                simuleringsinput_ref=simuleringsinput_ref,
                simuleringsinput_tiltak=simuleringsinput_tiltak,
                seed=seed,
                metadatakolonner=ventetid_input.loc[
                    index,
                    [
                        "Strekning",
                        "Tiltaksomraade",
                        "Tiltakspakke",
                        "Analyseomraade",
                        "Rute",
                    ],
                ]
                .to_frame()
                .T,
            )

        self.virkninger.ventetid = ventetidsvirkning

    def beregn_sedimenter(self):
        """
        Beregner og verdsetter opprenskning av forurensede sedimenter. Henter inn informasjon om forurensede sedimenter
        fra excel input.

        Bruker beregningsmetodikk fra: :py:.*?:`~fram.virkninger.sedimenter`

        Bruker informasjon om ferdigstillelsesår, beregningsår og kroneår fra FRAM:

        - Ferdigstillelsesår: self.ferdigstillelsesaar
        - Kroneverdi: self.kroneaar
        - beregningsaar: self.beregningsaar

        Beregner verdsatt endring i opprenskning av forurensede sedimenter

        """
        self._logg_ny_virkning("Forurensede sedimenter")
        sediment_logger = self._virkningslogger("Forurensede sedimenter")
        sediment_logger("Leser inn fra Excel")
        try:
            sedimenter = pd.read_excel(
                self.input_filbane,
                sheet_name="Forurensede sedimenter",
                usecols=list(range(8)),
            )
            sedimenter = sedimenter.query("Tiltakspakke == @self.tiltakspakke")
        except:
            sedimenter = None
        if sedimenter is None or len(sedimenter) == 0:
            sediment_logger(
                "NB! Fant ingen info om forurensede sedimenter. Beregner videre uten"
            )
            return

        self.virkninger.forurensede_sedimenter = Sedimenter(
            ferdigstillelsesaar=self.ferdigstillelsesaar,
            beregningsaar=self.beregningsaar,
            kroneaar=self.kroneaar,
            logger=sediment_logger,
            tiltakspakke=self.tiltakspakke,
            tiltaksomraade=self.tiltaksomraade
        )
        self.virkninger.forurensede_sedimenter.beregn(sedimenter)

    def beregn_andre_kontantstrommer(self):
        """
        Funksjon for å ta inn andre kontantstrømmer i FRAM-analysen. Funksjonen henter inn kontantstrømmene fra
        excel input. Deretter tilpasses kontantstrømmen til forutsetninger fra fram.

        Bruker beregningsmetodikk fra: :py:.*?:`~fram.virkninger.kontantstrommer`

        Bruker informasjon om strekning, beregningsår og kroneår fra FRAM:

        - Ferdigstillelsesår: self.ferdigstillelsesaar
        - Strekning: self.strekning
        - beregningsaar: self.beregningsaar

        Beregner verdsatt endring i andre kontantstrømmer

        """
        self._logg_ny_virkning("Andre kontantstrømmer")
        kontantstrom_logger = self._virkningslogger("Andre kontantstrømmer")
        kontantstrom_logger(
            "Leser inn eventuelle manuelt innlagte kontantstrømmer fra Excel-arket"
        )
        try:
            ytterlige_kontantstrommer = pd.read_excel(
                self.input_filbane, sheet_name="Kontantstrømmer", index_col=0
            ).query("Tiltakspakke == @self.tiltakspakke")
            aars_cols = [
                col for col in ytterlige_kontantstrommer.columns if str(col).isnumeric()
            ]
            ytterlige_kontantstrommer[aars_cols] = (
                ytterlige_kontantstrommer[aars_cols].astype(float).fillna(0)
            )
            self.n_kontantstrommer = len(ytterlige_kontantstrommer)

            ytterlige_kontantstrommer = (legg_til_aktør_hvis_mangler(ytterlige_kontantstrommer))
            self.aktør_ytterligere_mapping = ytterlige_kontantstrommer['Aktør'].to_dict()
        except:
            self.n_kontantstrommer = 0
            kontantstrom_logger(
                "Fant ingen ytterligere kontantstrømmer i Excel-arket. Beregner videre uten"
            )
            self.aktør_ytterligere_mapping = {}
            return

        if self.n_kontantstrommer == 0:
            return

        kontantstrom_logger(
            f"Fikk lest inn {len(ytterlige_kontantstrommer)} kontantstrømmer fra inputarket"
        )

        self.virkninger.andre_kontantstrommer = Kontantstrommer(
            beregningsaar=self.levetid,
            kroneaar=self.kroneaar,
            strekning=self.strekning,
            logger=kontantstrom_logger,
            tiltaksomraade=self.tiltaksomraade
        )
        self.virkninger.andre_kontantstrommer.beregn(ytterlige_kontantstrommer)

    def beregn_investeringskostnader(self):
        """
        Funksjon for å innhente investeringerkostnader. Henter inn  investeringskostnader fra excel input. Deretter
        brukes informasjon fra excel til å fordele totale investeringskostnader på anleggsår.
        Viktig å påpeke at funksjonen ikke beregner forventede investeringskostnader da dette inngår som input. Det
        funksjonen gjør er å tilpasse disse til FRAM-analyse.

        Bruker beregningsmetodikk fra: :py:.*?:`~fram.virkninger.investering`


        Beregner verdsatt endring i investeringskostnader

        """
        self._logg_ny_virkning("Investeringskostnader")
        investering_logger = self._virkningslogger("Investeringskostnader")

        if "Investeringskostnader" not in self.input_filbane.sheet_names:
            investering_logger(
                "NB! Fant ingen investeringskostnader angitt. Beregner uten investeringskostnader"
            )
            return

        inv_kost = (
            pd.read_excel(
                self.input_filbane, "Investeringskostnader", skiprows=1, usecols="A:H"
            )
            .dropna(how="all")
            .pipe(legg_til_utslipp_hvis_mangler)
            .pipe(
                self.gang_inn_faktorer,
                "Investeringskostnader",
                ["Forventningsverdi (kroner)"],
                False,
            )
            .fillna({
                KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG: 0,
            })
            .astype(
                {
                    "Tiltaksomraade": np.int64,
                    "Tiltakspakke": np.int64,
                    "Kroneverdi": np.int64,
                    KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG: float
                })
        )

        if not 'Anleggsperiode' in inv_kost.columns:
            inv_kost = (inv_kost
                        .assign(Anleggsperiode = lambda x: x['Siste år med kostnader']- x['Første år med kostnader'] + 1)
                        .drop({'Siste år med kostnader', 'Første år med kostnader'}, axis=1))

        inv_kost = (inv_kost
                    .astype({'Anleggsperiode':np.int64}))[['Tiltaksomraade', 'Tiltakspakke', 'P50 (kroner)', 'Forventningsverdi (kroner)', KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG, 'Kroneverdi', 'Anleggsperiode', 'Analysenavn']]

        self.anleggsperiode = inv_kost['Anleggsperiode'].max()

        if (inv_kost is None) or (len(inv_kost) == 0):
            investering_logger(
                "NB! Fant ingen investeringskostnader angitt. Beregner uten investeringskostnader"
            )
            return

        self.virkninger.investeringskostnader = Investeringskostnader(
            beregningsaar=list(range(self.ferdigstillelsesaar-1-inv_kost["Anleggsperiode"].min(),max(self.beregningsaar),)
            ),
            kroneaar=self.kroneaar,
            ferdigstillelsesaar=self.ferdigstillelsesaar,
            analysestart=self.analysestart,
            strekning=self.strekning,
            logger=investering_logger,
        )

        self.virkninger.investeringskostnader.beregn(
            inv_kost.loc[inv_kost.Tiltakspakke == self.tiltakspakke]
        )

        self.utslipp_anleggsfasen = self.virkninger.investeringskostnader.utslipp_anleggsfasen

    def beregn_vedlikehold(self):
        """
        Funksjon som beregner og verdsetter endring i vedlikeholdskostnader.

        Funksjonen henter inn informasjon fra excel input om endring i antall merker i tiltaksbanen. Deretter hentes
        kalkulasjonspriser inn, og endringen verdsettes.


        Bruker beregningsmetodikk fra: :py:.*?:`~fram.virkninger.vedlikehold`

        Bruker informasjon om kalkulasjonspriser fra Forutsetninger_FRAM.xlsx i tillegg til strekning, tiltakspakke,
         beregningsaar, ferdigstillelsesår, sluttår fra FRAM:

        - Ferdigstillelsesår: self.ferdigstillelsesaar
        - beregningsaar: self.beregningsaar
        - strekning: self.strekning
        - tiltakspakke: self.tiltakspakke
        - sluttaar: self.sluttaar

        Beregner verdsatt endring i vedlikeholdskostnader.

        """
        self._logg_ny_virkning("Vedlikeholdskostnader")
        vedlikehold_logger = self._virkningslogger("Vedlikeholdskostnader")

        vedlikehold_logger(
            "Leser inn oversikt over merkeinstallasjoner til vedlikeholdskostnadene"
        )
        if (
            "tiltakspunktnavn" in pd.read_excel(
                self.input_filbane,
                sheet_name=f"Tiltakspakke {self.tiltakspakke}",
                usecols=[26,27],
            )

        ):
            vedlikehold_logger(
                "NB! Fant ingen objekter til vedlikehold angitt. Beregner uten vedlikeholdskostnader"
            )
            return

        merker = pd.read_excel(
            self.input_filbane,
            sheet_name=f"Tiltakspakke {self.tiltakspakke}",
            skiprows=1,
            usecols=list(range(27, 32)),
        ).loc[lambda x: ~x.Objekttype.isin([np.nan, "Ikke merke"])]

        if len(merker) == 0:
            vedlikehold_logger(
                "NB! Fant ingen merker og installasjoner. Det beregnes ikke vedlikeholdskostnader"
            )
            return

        kostnader = (
            forut("kalkpris_vedlikehold")[["Objekttype", "Total"]]
            .dropna(subset=["Objekttype"])
            .assign(Objekttype=lambda df: df.Objekttype.str.strip())
            .set_index("Objekttype")
            .pipe(self.gang_inn_faktorer, "Vedlikehold")
        )

        oppgrad = (
            forut("kalkpris_oppgradering", antall_kolonner=9)
            .dropna(subset=["TG0->TG2"], axis=0)
            .pipe(self.gang_inn_faktorer, "Vedlikehold", ["Total"], sett_index=False)
            .assign(Objekttype=lambda df: df.Objekttype.str.strip())
            .set_index(["Objekttype", FOLSOMHET_KOLONNE])
        )

        self.virkninger.vedlikehold = Vedlikeholdskostnader(
            kostnader=kostnader,
            oppgrad=oppgrad,
            strekning=self.strekning,
            tiltakspakke=self.tiltakspakke,
            beregningsaar=self.beregningsaar,
            ferdigstillelsesaar=self.ferdigstillelsesaar,
            sluttaar=self.sluttaar,
            logger=vedlikehold_logger,
            tiltaksomraade=self.tiltaksomraade
        )

        self.virkninger.vedlikehold.beregn(merker)

    def beregn_utslipp_til_luft(self):
        """
        Funksjon som beregner og verdsetter endring i utslipp til luft.

        Bruker beregningsmetodikk fra: :py:.*?:`~fram.virkninger.utslipp_til_luft`

        Bruker informasjon om beregningsaar, kroneaar, tidsbruk per passering, hastighet og trafikk i tiltaks- og referansebane fra FRAM:
        - beregningsaar: self.beregningsaar
        - kroneår: self.kroneaar
        - tidsbruk per passering i referansebanen: self._fremskrevet_tid_ref
        - tidsbruk per passering i tiltaksbanen: self._fremskrevet_tid_tiltak
        - hastighet i referansebanen: self._hastighet_ref
        - hastighet i tiltaksbanen: self._hastighet_tiltak
        - trafikk_ref: self.trafikk_referanse
        - trafikk_tiltak: self.trafikk_tiltak

        Beregner verdsatt endring i utslipp til luft.

        """
        self._logg_ny_virkning("Utslipp til luft")
        utslipp_logger = self._virkningslogger("Utslipp til luft")
        if self.trafikk_referanse is None and self.utslipp_anleggsfasen is None:
            utslipp_logger(
                "Kan ikke beregne utslipp til luft uten trafikk og uten utslipp i anleggsfasen. Fortsetter uten utslipp til luft"
            )
            return
        elif self._fremskrevet_tid_ref is None and self.utslipp_anleggsfasen is None:
            utslipp_logger(
                "Kan ikke beregne utslipp til luft uten at det er beregnet tidsbruk og uten utslipp i anleggsfasen. Fortsetter uten utslipp til luft"
            )
            return
        elif self._hastighet_ref is None and self.utslipp_anleggsfasen is None:
            utslipp_logger(
                "Kan ikke beregne utslipp til luft uten hastighetsberegninger og uten utslipp i anleggsfasen. Fortsetter uten utslipp til luft"
            )
            return

        self.virkninger.utslipp_til_luft = Utslipp_til_luft(
            trafikkaar=self.beregningsaar,
            alle_aar=self.levetid,
            kroneaar=self.kroneaar,
            logger=utslipp_logger,
        )

        if self.utslipp_anleggsfasen is None:
            _utslipp_anleggsfasen = None
        else:
            _utslipp_anleggsfasen = (
                self.utslipp_anleggsfasen
                .pipe(
                    _legg_til_kolonne,
                    KOLONNENAVN_STREKNING,
                    self.strekning
                )
                .pipe(
                    _legg_til_kolonne,
                    "Analyseomraade",
                    "Alle"
                )
                .pipe(
                    _legg_til_kolonne,
                    "Rute",
                    "Alle"
                )
                .pipe(
                    _legg_til_kolonne,
                    "Skipstype",
                    "Anleggsfasen"
                )
                .pipe(
                    _legg_til_kolonne,
                    "Lengdegruppe",
                    "Anleggsfasen"
                )
                .pipe(
                    _legg_til_kolonne,
                    "Type",
                    "CO2"
                )
            )

        self.virkninger.utslipp_til_luft.beregn(
            tidsbruk_per_passering_ref=self._fremskrevet_tid_ref,
            tidsbruk_per_passering_tiltak=self._fremskrevet_tid_tiltak,
            hastighet_per_passering_ref=self._hastighet_ref,
            hastighet_per_passering_tiltak=self._hastighet_tiltak,
            trafikk_ref=self.trafikk_referanse,
            trafikk_tiltak=self.trafikk_tiltak,
            utslipp_anleggsfasen=_utslipp_anleggsfasen
        )

    def beregn_tidsbruk(self):
        """
        Funksjon som beregner og verdsetter endring i tidsavhengige kostnader. Henter inn seilingstid i referanse- og
        tiltaksbanen fra input excel.

        Bruker deretter nasjonale  mmsi-vekter til å beregne tidsavhengige kalkulasjonspriser.

        Bruker beregningsmetodikk fra: :py:.*?:`~fram.virkninger.tid`

        I tillegg til MMSI-vektetene, brukers informasjon om kroneår, beregningsaar, tidsbruk per passering og trafikk i tiltaks- og referansebane fra FRAM:
        - Kroneverdi: self.kroneaar
        - beregningsaar: self.beregningsaar
        - tidsbruk_per_passering_ref: self._fremskrevet_tid_ref
        - tidsbruk_per_passering_tiltak: self._fremskrevet_tid_tiltak
        - trafikk_ref: self.trafikk_referanse
        - trafikk_tiltak: self.trafikk_tiltak

        Beregner verdsatt endring i tidsavhengige kostnader

        """
        self._logg_ny_virkning("Tidsavhengige kostnader")
        tidsbruk_logger = self._virkningslogger("Tidsavhengige kostnader")
        if self.trafikk_referanse is None:
            tidsbruk_logger(
                "Kan ikke beregne tidsavhengige kostnader uten trafikk. Fortsetter uten tidsavhengige kostnader"
            )
            return

        elif "Seilingstid referansebanen" not in self.input_filbane.sheet_names:
            if self.delvis_fram:
                tidsbruk_logger(
                    "Fant ingen data for seilingstid i referansebanen. Fortsetter uten tidsavhengige kostnader"
                )
                return

            raise DelvisFRAMFeil(
                "Kan ikke sette opp FRAM uten angitt tidsbruk med mindre arumentet 'delvis_fram' er angitt"
            )

        # Leser inn tid brukt i referansebanen
        tidsbruk_logger("Leser inn seilingstid (tid brukt) fra Excel")
        innlest_tid_hastighet = _fra_excel(
            self.input_filbane, "Seilingstid referansebanen"
        ).reset_index()

        tid_brukt_ref = (
            innlest_tid_hastighet.drop("Hastighet", axis=1)
            .pipe(_fyll_ut_fra_alle, kolonne="Skipstype", fyllverdier=SKIPSTYPER)
            .pipe(
                _fyll_ut_fra_alle,
                kolonne="Lengdegruppe",
                fyllverdier=LENGDEGRUPPER,
            )
            .set_index(TRAFIKK_COLS, drop=True)
        )

        # Leser inn tid brukt og hastighet i tiltaksbanen. Beholder fra referansebanen for alle som ikke er spesifisert i itlak
        tid_brukt_tiltak = (
            _fra_excel(
                filbane=self.input_filbane,
                ark=f"Tiltakspakke {self.tiltakspakke}",
                skiprows=1,
                usecols=list(range(11, 20)),
            )
            .reset_index()
            .dropna(subset=["Tidsbruk"])
        )

        tid_brukt_tiltak = (
            tid_brukt_tiltak.drop("Hastighet", axis=1)
            .pipe(_fyll_ut_fra_alle, kolonne="Skipstype", fyllverdier=SKIPSTYPER)
            .pipe(
                _fyll_ut_fra_alle,
                kolonne="Lengdegruppe",
                fyllverdier=LENGDEGRUPPER,
            )
            .astype({"Tiltakspakke": np.int64, "Tiltaksomraade": np.int64})
            .set_index(TRAFIKK_COLS, drop=True)
            .dropna()
        )

        mappe_kalkpriser = (
            FRAM_DIRECTORY
            / "kalkpriser"
            / "tid_drivstoff"
        )

        try:
            filbane_ferdigberegnet_kalkpriser = sorted(mappe_kalkpriser.glob("nasjonale_tidskostnader_*"))[-1]

        except:
            raise DelvisFRAMFeil(f"Du trenger nasjonale kalkulasjonspriser for både tids- og distanseavhengige kostnader. For å estimere disse må funksjonen benyttes `from fram.generelle_hjelpemoduler.beregn_kalkpriser import beregn` benyttes.")

        kroneaar_kalkpriser = int(os.path.basename(filbane_ferdigberegnet_kalkpriser).split("_")[2][:-5])

        tidsbruk_logger(f"Finner nasjonale tidskostnader oppgitt i {str(kroneaar_kalkpriser)} kroner")

        self.kalkpriser_tid = (
            get_kalkpris_tid(
                filbane_tidskost=filbane_ferdigberegnet_kalkpriser,
                til_kroneaar=self.kroneaar,
                beregningsaar=self.beregningsaar,
                opprinnelig_kroneaar=kroneaar_kalkpriser,
            )
            .set_index(["Skipstype", "Lengdegruppe"])
            .pipe(self.gang_inn_faktorer, "Tidskostnader")
            .reset_index()
        )

        tid_brukt_ref = tid_brukt_ref.query(f"""Tiltakspakke=={self.tiltakspakke}""")
        if len(tid_brukt_tiltak) == 0:
            tid_brukt_tiltak = tid_brukt_ref.copy()

        if len(tid_brukt_ref) == 0 or len(tid_brukt_tiltak) == 0:
            if self.delvis_fram:
                tidsbruk_logger(
                    "Finner ikke tidsbruk angitt. Beregner videre uten tidsavhengige kostnader"
                )
                return
            else:
                raise DelvisFRAMFeil(
                    "Kan ikke sette opp FRAM uten angitt tidsbruk med mindre arumentet 'delvis_fram' er angitt"
                )

        self._fremskrevet_tid_ref = fremskriv_konstant_tidsbruk_per_passering(
            tid_brukt_ref["Tidsbruk"], self.trafikkaar
        )
        self._fremskrevet_tid_tiltak = fremskriv_konstant_tidsbruk_per_passering(
            tid_brukt_tiltak["Tidsbruk"], self.trafikkaar
        )

        self.virkninger.tidsbruk = Tidsbruk(
            kalkulasjonspriser=self.kalkpriser_tid,
            beregningsaar=self.beregningsaar,
            logger=tidsbruk_logger,
        )

        if self.virkninger.tidsbruk:
            self.virkninger.tidsbruk.beregn(
                tidsbruk_per_passering_ref=self._fremskrevet_tid_ref,
                tidsbruk_per_passering_tiltak=self._fremskrevet_tid_tiltak,
                trafikk_ref=self.trafikk_referanse,
                trafikk_tiltak=self.trafikk_tiltak,
            )

    def beregn_drivstoff(self):
        """
        Funksjon som beregner og verdsetter endring i distanseavhengige kostnader. Henter inn seilingstid og hastighet i referanse- og
        tiltaksbanen fra input excel.

        Bruker beregningsmetodikk fra: :py:.*?:`~fram.virkninger.drivstoff`

        I tillegg til MMSI-vektetene, brukers informasjon om tankersted kroneår, beregningsaar, tidsbruk per passering, hastighet og trafikk i tiltaks- og referansebane fra FRAM:

        - tankested: self.tankested
        - Kroneverdi: self.kroneaar
        - beregningsaar: self.beregningsaar
        - tidsbruk_per_passering_ref: self._fremskrevet_tid_ref
        - tidsbruk_per_passering_tiltak: self._fremskrevet_tid_tiltak
        - hastighet per passering referansebanen: self._hastighet_ref
        - hastighet per passering tiltaksbanen: self._hastighet_tiltak
        - trafikk_ref: self.trafikk_referanse
        - trafikk_tiltak: self.trafikk_tiltak

        Beregner verdsatt endring i distanseavhengige kostnader

        """
        self._logg_ny_virkning("Drivstoff")
        drivstoff_logger = self._virkningslogger("Drivstoff")
        if self.trafikk_referanse is None:
            drivstoff_logger(
                "Kan ikke beregne drivsstofforbruk uten trafikk. Fortsetter uten drivsstofforbruk"
            )
            return
        elif self._fremskrevet_tid_ref is None:
            drivstoff_logger(
                "Kan ikke beregne drivsstofforbruk uten at det er beregnet tidsbruk. Fortsetter uten drivsstofforbruk"
            )
            return
        elif "Seilingstid referansebanen" not in self.input_filbane.sheet_names:
            if self.delvis_fram:
                drivstoff_logger(
                    "Fant ingen data for seilingstid i referansebanen. Fortsetter uten drivstofforbruk"
                )
                return

            raise DelvisFRAMFeil(
                "Kan ikke sette opp FRAM uten angitt tidsbruk med mindre arumentet 'delvis_fram' er angitt"
            )

        # Leser inn tid brukt i referansebanen
        drivstoff_logger("  Leser inn hastighet fra Excel")
        tid_hastighet_innlest = _fra_excel(
            self.input_filbane, "Seilingstid referansebanen"
        ).reset_index()

        hastighet_ref = (
            tid_hastighet_innlest.drop("Tidsbruk", axis=1)
            .pipe(_fyll_ut_fra_alle, kolonne="Skipstype", fyllverdier=SKIPSTYPER)
            .pipe(
                _fyll_ut_fra_alle,
                kolonne="Lengdegruppe",
                fyllverdier=LENGDEGRUPPER,
            )
            .set_index(TRAFIKK_COLS, drop=True)
            .dropna(axis=1, how="all")
            .dropna()
        )

        _hastighet_tiltak = (
            (
                _fra_excel(
                    filbane=self.input_filbane,
                    ark=f"Tiltakspakke {self.tiltakspakke}",
                    skiprows=1,
                    usecols=list(range(11, 20)),
                )
                .reset_index()
                .dropna(subset=["Tidsbruk"])
            )
            .drop("Tidsbruk", axis=1)
            .pipe(_fyll_ut_fra_alle, kolonne="Skipstype", fyllverdier=SKIPSTYPER)
            .pipe(
                _fyll_ut_fra_alle,
                kolonne="Lengdegruppe",
                fyllverdier=LENGDEGRUPPER,
            )
            .astype({"Tiltakspakke": np.int64, "Tiltaksomraade": np.int64})
            .set_index(TRAFIKK_COLS, drop=True)
            .dropna(axis=1, how="all")
            .dropna()
        )
        hastighet_tiltak = hastighet_ref.copy()
        hastighet_tiltak.update(_hastighet_tiltak)
        hastighet_tiltak = hastighet_tiltak.dropna()
        if (
            (len(hastighet_tiltak) == 0)
            or (len(hastighet_ref) == 0)
            or hastighet_ref.empty
            or hastighet_tiltak.empty
        ):
            if self.delvis_fram:
                drivstoff_logger(
                    "Finner ikke distanseavhengige kostnader anitt. Beregner videre uten distanseavhengige kostnader"
                )
                return
            else:
                raise DelvisFRAMFeil(
                    "Kan ikke sette opp FRAM uten drivstoffavhengige kostnader med mindre 'delvis_fram' er angitt"
                )
        self._hastighet_ref = hastighet_ref
        self._hastighet_tiltak = hastighet_tiltak

        self.virkninger.drivstoff = Drivstoff(
            beregningsaar=self.beregningsaar,
            tankested=self.tankested,
            kroneaar=self.kroneaar,
            logger=drivstoff_logger,
        )

        self.virkninger.drivstoff.beregn(
            tidsbruk_per_passering_ref=self._fremskrevet_tid_ref,
            tidsbruk_per_passering_tiltak=self._fremskrevet_tid_tiltak,
            hastighet_per_passering_ref=self._hastighet_ref,
            hastighet_per_passering_tiltak=self._hastighet_tiltak,
            trafikk_ref=self.trafikk_referanse,
            trafikk_tiltak=self.trafikk_tiltak,
        )

    def beregn_risiko(self):
        """
        Funksjon som beregner og verdsetter endring i risikovirkninger knyttet til helse, materielle skader og oljeutslipp.
        Funksjonen leser inn risikoanalyser fra angitt filbane (self.ra_dir). Disse er i utgangspunktet oppgitt i excel, og
        vil ta lang til å kjøre. Dersom risikoanalysene ikke er lest inn i tidligere kjøringer, mellomlagres en .json-fil
        med alle hendelser.

        Når risikoanalysene er lest inn fra ra_dir sammenlignes jobnames med de som er spesifisert som relevante i excel input.

        Deretter benyttes beregningsmetodikk for intrapolering- og ekstrapolering av hendelsene mellom de to riskoårene,
        omregning fra antall hendelser til konsekvenser som deretter verdsettes fra: :py:.*?:`~fram.virkninger.risiko`

        I tillegg til innleste risikoanalyser brukes informasjon om trafikk i tiltaks- og referansebanen, kroneår, beregningsår og strekningsivse
        kalkulasjonspriser for tidsavhengige kostnader fra fram:

        - trafikk_referanse: self.trafikk_referanse
        - trafikk_tiltak: self.trafikk_tiltak
        - kroneaar: self.kroneaar
        - beregningsaar: self.beregningsaar
        - tidskostnader: self.kalkpriser_tid

        Beregner verdsatt endring i risikovirkninger knyttet til helse, materielle skader og oljeutslipp (utslipp og opprenskning).

        """
        self._logg_ny_virkning("Risiko")
        risiko_logger = self._virkningslogger("Risiko")
        if self.trafikk_referanse is None:
            risiko_logger(
                "Kan ikke beregne risikovirkninger uten trafikk. Fortsetter uten risikovirkninger"
            )
            return

        if ("Risikoanalyser referansebanen" not in self.input_filbane.sheet_names and "Aisyrisk referansebanen" not in self.input_filbane.sheet_names):
            if self.delvis_fram:
                risiko_logger(
                    "Finner ikke korrekte risikovirkninger angitt. Beregner videre uten risikovirkninger"
                )
                return
            else:
                raise DelvisFRAMFeil(
                    "Kan ikke sette opp FRAM uten korrekte risikovirkninger med mindre 'delvis_fram' er angitt"
                )

        if self.aisyrisk_input == False: # Her lages self.hendelser_ref, self.hendelser_tiltak, self.fremskrevet_hendelsesreduksjon hvis iwrap
            risiko_logger(f"Leser inn RA fra angitt filbane {self.ra_dir}")

            # Leser inn risikoanalysenavnene
            (ra_ref, ra_tiltak,) = les_inn_hvilke_ra_som_brukes_fra_fram_input(
                self.input_filbane, self.tiltakspakke
            )
            if ra_ref is None:
                if self.delvis_fram:
                    risiko_logger(
                        "Finner ikke korrekte risikovirkninger angitt. Beregner videre uten risikovirkninger"
                    )
                    return
                else:
                    raise DelvisFRAMFeil(
                        "Kan ikke sette opp FRAM uten korrekte risikovirkninger med mindre 'delvis_fram' er angitt"
                    )

            # Sett opp en IWRAP reader
            self._iwrap_reader = Risikoanalyser(
                ra_dir=self.ra_dir, logger=self.logger, les_paa_nytt=self.les_RA_paa_nytt
            )
            risiko_logger("Sammenstiller de risikoanalysene som er påkrevd for analysen")
            # Leser inn selve risikoberegningene, basert på risikoanalysenavnene
            risiko_ref = self._iwrap_reader.hent_ra_resultater(ra_ref).pipe(
                self.gang_inn_faktorer, "Ulykkesfrekvens", ["Hendelser"], False
            )
            risiko_tiltak = self._iwrap_reader.hent_ra_resultater(ra_tiltak).pipe(
                self.gang_inn_faktorer, "Ulykkesfrekvens", ["Hendelser"], False
            )

            risiko_logger("Fremskriver IWRAP-hendelser")
            (
                self.hendelser_ref,
                self.hendelser_tiltak,
                self.fremskrevet_hendelsesreduksjon,
            ) = iwrap_fremskrivinger.beregn_risiko(
                trafikk_referanse=self.trafikk_referanse,
                trafikk_tiltak=self.trafikk_tiltak,
                risiko_ref=risiko_ref,
                risiko_tiltak=risiko_tiltak,
            )

        else: # Altså self.aisyrisk_input == True. Her lages self.hendelser_ref, self.hendelser_tiltak, self.fremskrevet_hendelsesreduksjon hvis aisyrisk
            risiko_logger("Kjører analyse med aisyrisk_input")

            # Leser inn risikoanalysenavnene
            (self.ra_ref, self.ra_tiltak,) = les_inn_hvilke_ra_som_brukes_fra_fram_input(
                self.input_filbane, self.tiltakspakke, arknavn="Aisyrisk referansebanen"
            )

            # Lager hendelsesmatrisene ved å loope gjennom alle analyseområdene

            metaframe_index = pd.concat((self.ra_ref,self.ra_tiltak), axis=0).Risikoanalyse.dropna().unique()

            risiko_logger("Leser inn alle RA-filene")
            samlet_ra_fil = []

            for risikoanalyse in metaframe_index:
                try:
                    ra_fil = pd.read_csv(self.ra_dir / (risikoanalyse + '.csv'),
                                         sep=';')  # Prøv å lese med semikolon-separator
                except:
                    ra_fil = pd.read_csv(self.ra_dir / (risikoanalyse + '.csv'),
                                         sep=',')  # Hvis ikke, prøv kolon-separator
                ra_fil = ra_fil.assign(risikoanalysenavn=risikoanalyse)
                samlet_ra_fil.append(ra_fil)
            samlet_ra_fil = pd.concat(samlet_ra_fil, axis=0, ignore_index=True)

            risiko_logger("Fremskriver hendelser")

            hendelser_ref = []
            hendelser_tilt = []

            for i in range(0, len(self.ra_ref)):
                rute = self.ra_ref.copy().reset_index().at[i, 'Rute']
                analyseomraade = self.ra_ref.copy().reset_index().at[i, 'Analyseomraade']

                # Henter ut hvilke RAer som skal brukes
                relevant_ra_ref = samlet_ra_fil.loc[samlet_ra_fil.risikoanalysenavn == self.ra_ref.at[i, "Risikoanalyse"]]
                relevant_ra_tilt = samlet_ra_fil.loc[
                    samlet_ra_fil.risikoanalysenavn == self.ra_tiltak.at[i, "Risikoanalyse"]]

                # Konverterer aisyrisk risikogruppene til korrekte skip
                aisy_ra_skipstyper_ref = konverter_aisyrisk_lengdegrupper(relevant_ra_ref)
                aisy_ra_skipstyper_tilt = konverter_aisyrisk_lengdegrupper(relevant_ra_tilt)

                hendelser_ref_short = fordel_og_fremskriv_ra(
                    aisy_ra_skipstyper_ref,
                    strekning=self.strekning,
                    tiltakspakke=self.tiltakspakke,
                    tiltaksomraade=self.tiltaksomraade,
                    beregningsaar=self.beregningsaar,
                    risiko_logger=risiko_logger,
                    trafikk=self.trafikk_referanse,
                    rute=rute,
                    analyseomraade=analyseomraade,
                    risikoanalysenavn=self.ra_ref.at[i, 'Risikoanalyse'],
                    risikoanalyseaar=self.ra_ref.at[i, 'ra_aar'],
                    tiltak_eller_ref="referansebanen"
                )

                # Her forutsetter vi at RA-ene er kjørt på tiltakstrafikkgrunnlaget. Det kan endres i en fremtidig kjøring.
                hendelser_tilt_short = fordel_og_fremskriv_ra(
                    aisy_ra_skipstyper_tilt,
                    strekning=self.strekning,
                    tiltakspakke=self.tiltakspakke,
                    tiltaksomraade=self.tiltaksomraade,
                    beregningsaar=self.beregningsaar,
                    risiko_logger=risiko_logger,
                    trafikk=self.trafikk_tiltak,
                    rute=rute,
                    analyseomraade=analyseomraade,
                    risikoanalysenavn=self.ra_tiltak.at[i, 'Risikoanalyse'],
                    risikoanalyseaar=self.ra_tiltak.at[i, 'ra_aar'],
                    tiltak_eller_ref="tiltaksbanen"
                )

                hendelser_ref.append(hendelser_ref_short)

                hendelser_tilt.append(hendelser_tilt_short)

            self.hendelser_ref = pd.concat(hendelser_ref, axis=0).fillna(0)  # Må fillna 0 i cruise-versjonen, ikke i 3.4
            self.hendelser_tiltak = pd.concat(hendelser_tilt, axis=0).fillna(0)  # Må fillna 0 i cruise-versjonen, ikke i 3.4

            HendelseSchema.validate(self.hendelser_ref)
            HendelseSchema.validate(self.hendelser_tiltak)

            self.fremskrevet_hendelsesreduksjon = self.hendelser_ref.subtract(self.hendelser_tiltak, fill_value=0)
            HendelseSchema.validate(self.fremskrevet_hendelsesreduksjon)

        # Tilbake igjen til felles kode

        # Sjekker om det er angitt spesifikke konsekvensmatriser for referanse- eller tiltaksbanen, leser inn og bruker
        (self.konsekvensmatrise_ref, self.konsekvensmatrise_tiltak) = les_inn_konsekvensmatriser(
            beregningsaar=self.beregningsaar,
            excel_inputfil=self.input_filbane,
            tiltakspakke=self.tiltakspakke,
            logger=risiko_logger
        )

        risiko_logger("Henter inn konsekvenser og kalkpriser for utslipp")
        (kalkpris_oljeutslipp_ref,
         kalkpris_oljeutslipp_tiltak,
         kalkpris_oljeopprensking_ref,
         kalkpris_oljeopprensking_tiltak) = les_inn_kalkpriser_utslipp(
            kroneaar=self.kroneaar,
            beregningsaar=self.beregningsaar,
            excel_inputfil=str(Path(self.input_filbane)),
            tiltakspakke=self.tiltakspakke,
            analyseomraader=self.analyseomraader,
            logger=risiko_logger
        )

        sarbarhet = (
            pd.read_excel(
                self.input_filbane, sheet_name="Sarbarhet", usecols=list(range(6))
            )
            .dropna(how="all")
            .astype({"Tiltaksomraade": np.int64, "Tiltakspakke": np.int64})
        )

        self.virkninger.risiko = Risiko(
            kalkpriser_materielle_skader=get_kalkpris_materielle_skader(
                kroneaar=self.kroneaar,
                beregningsaar=self.beregningsaar,
                tidskostnader=self.kalkpriser_tid,
            ),
            kalkpriser_helse=get_kalkpris_helse(
                kroneaar=self.kroneaar, siste_aar=self.sluttaar
            ),
            kalkpriser_oljeutslipp_ref=kalkpris_oljeutslipp_ref,
            kalkpriser_oljeutslipp_tiltak=kalkpris_oljeutslipp_tiltak,
            kalkpriser_oljeopprensking_ref=kalkpris_oljeopprensking_ref,
            kalkpriser_oljeopprensking_tiltak=kalkpris_oljeopprensking_tiltak,
            sarbarhet=sarbarhet,
            beregningsaar=self.beregningsaar,
            logger=risiko_logger,
        )

        self.virkninger.risiko.beregn(
            hendelser_ref=self.hendelser_ref,
            hendelser_tiltak=self.hendelser_tiltak,
            konsekvensmatrise_ref=self.konsekvensmatrise_ref,
            konsekvensmatrise_tiltak=self.konsekvensmatrise_tiltak,
        )

    def klargjor_output_kontantstrommer(self):
        """
        Funksjon som klargjør og skriver resultater til excel. Funksjonen leser først inn
        kontantstrømmer. Deretter gjøres formatering for fin excel output, og denne skrives deretter
        til en excelbok i en mappe som ligger plassert samme sted som inputboken, og har navnet "Output XX", der
        xx er tiltakspakken som ble kjørt.

        Returns:
            Excelbok: Denne funksjonen lager en excelbok som heter Resultater XX med kontantstrømmene og forsiden.

        """
        filnavn = os.path.join(
            self.output_filepath, f"Resultater {self.tiltakspakke}.xlsx"
        )

        # Lager en pandas excel writer ved å bruke XlsxWriter som engine
        writer = pd.ExcelWriter(filnavn, engine="xlsxwriter")

        for analyse in self._faktorer.keys():
            arknavn = analyse
            if analyse == "standardkjøring":
                arknavn = "Resultater"

            # Fikser format på DataFrame
            resultater = self.kontantstrommer(analyse, self.aktør_ytterligere_mapping)

            # Konverterer dataframe til excel writer objekt
            resultater.to_excel(writer, sheet_name=arknavn)

            # Definerer excelark og excelbok
            workbook = writer.book
            worksheet = writer.sheets[arknavn]

            # Definerer formater på bok og ark nivå
            bold = workbook.add_format({"bold": True})
            nummerformat_tusenskille = workbook.add_format({"num_format": "#,##0"})

            # Setter bredde på kolonnene
            worksheet.set_row(
                20 + self.n_kontantstrommer,
                None,
                bold,
            )
            worksheet.set_column("A:A", 35, None)
            worksheet.set_row(1, None, bold)
            worksheet.set_row(2, None, bold)
            worksheet.set_column("B:B", 30, nummerformat_tusenskille)
            worksheet.set_column("C:C", 30, nummerformat_tusenskille)

            worksheet.set_column("D:EE", 11, nummerformat_tusenskille)

        writer.save()

        _lag_excel_forside(
            filepath=filnavn,
            strekning=self.strekning,
            tiltakspakke=self.tiltakspakke,
            version=self.version,
            log=self.log,
            input_filbane=self.input_filbane.__fspath__(),
        )

    def klargjor_output_detaljert(self):
        """
        Funksjon som klargjør og skriver detaljerte resultater til excel. Funksjonen leser først inn volumvirkninger i
        referanse- og tiltaksbanen i tillegg til nettovirkninger disaggert på rute-nivå per skipstype og lengdegruppe.
        Deretter gjøres formatering for fin excel output, og denne skrives deretter til en excelbok i en mappe som l
        igger plassert samme sted som inputboken, og har navnet "Output XX", der xx er tiltakspakken som ble kjørt.

        Returns:
            Excelbok: Denne funksjonen lager en excelbok som heter "Detaljerte resultater XX" med volumvirkninger for referanse-
            og tiltakbanen i tillegg til disaggregerte nettovirkninger.

        """
        filnavn = (
            self.output_filepath / f"Detaljerte resultater {self.tiltakspakke}.xlsx"
        )

        # Fikser format på DataFrame

        volumvirkninger_ref = self.volumvirkning_ref.reset_index()
        volumvirkninger_tiltak = self.volumvirkning_tiltak.reset_index()
        verdsatt_netto = self.verdsatt_netto.reset_index()

        # Lager en pandas excel writer ved å bruke XlsxWriter som engine
        writer = pd.ExcelWriter(filnavn, engine="xlsxwriter")

        # Konverterer dataframe til excel writer objekt
        volumvirkninger_ref.to_excel(writer, sheet_name="Volumvirkninger ref")
        volumvirkninger_tiltak.to_excel(writer, sheet_name="Volumvirkninger tiltak")
        verdsatt_netto.to_excel(writer, sheet_name="Verdsatte nettovirkninger")
        #
        writer.save()

    def skriv_output(self, folder: Union[bool, str, Path] = False):
        """
        Skriver output fra kjøringen til en mappe.

        Mappen heter "Output xx", der XX er tiltakspakken som har blitt kjørt. I mappen finner man følgende output:

        - Resultater XX.xlsx: Neddiskonterte kontantstrømmer og forside
        - Detaljerte resultater XX.xlsx. Volumvirkninger for referanse- og tiltaksbane i tillegg til disaggregerte kontantstrømmer på rutenivå per skipstype og lengdegruppe

        Args:
            folder: Mappe der du vi ha skrevet outputmappe til, hvis True så skrives det til mappen til self.input_filbane

        """

        if not folder:
            return

        self._infologger("Sammenstiller og skriver output")

        if isinstance(folder,str) or isinstance(folder,Path):
            filbane = Path(folder)
        elif isinstance(self.input_filbane, (str, Path)):
            filbane = Path(self.input_filbane).parent
        elif isinstance(self.input_filbane, pd.ExcelFile):
            filbane = Path(self.input_filbane.__fspath__()).parent
        else:
            self._infologger("Noe er galt. Skriver ingen output.")
            return

        mappenavn = f"Output {self.tiltakspakke}"

        filbane_output = filbane / mappenavn
        if not filbane_output.is_dir():
            filbane_output.mkdir()

        self.output_filepath = filbane_output

        self.klargjor_output_kontantstrommer()

        self.klargjor_output_detaljert()



if __name__ == "__main__":
    s = FRAM(
        FRAM_DIRECTORY
        / "eksempler"
        / "eksempel_analyser"
        / "Inputfiler"
        / "Strekning 11-anleggsutslipp.xlsx",
        # / "Strekning 11.xlsx",
        tiltakspakke=11,
        folsomhetsanalyser=True,
        ra_dir=FRAM_DIRECTORY / "eksempler" / "eksempel_analyser" / "RA",
        delvis_fram=True,
        aisyrisk_input=False, # For aisyrisk, 
        trafikkgrunnlagsaar=2019,
    )
    s.run(skriv_output=False)
"""
============================================
Ekstra kontantstrømmer
============================================

I samfunnsøkonomiske analyser for Kystverket kan det oppstå virkninger av enkelte tiltak som enten beregnes med en annen
metodikk enn metodikken som ligger til grunn i FRAM, eller det er virkninger som ikke inngår i en standard FRAM-analyse.
For å håndere dette, og samtidig sikre at virkningene benytter samme generelle forutsetninger som øvrige virkninger i
analysen (diskonteringsrente, sammenstillingsår osv.) har vi gjort det mulig å legge inn kontaktstrømmene i FRAM.

For å legge til slike kontantstrømmer må man legge inn kontantstrømmen på endringsform - altså endringen fra referansebanen.
Det er viktig at netto kostnadsvirkninger legges til som en kostnad (-) og netto nyttevirkninger legge til som en positiv
virkning (+). Ettersom FRAm-modellen sjekker at alle virkninger beregnes i samme kroneår, må det også spesifiseres
hvilket kroneår kontantstrømmen er oppgitt i. Dersom kroneåret avviker fra øvrige virkninger vil kontantstrømmen justeres.

For å gjøre dette trenger du en dataframe med følgende kolonner: 
    Navn: navn på virkningen. 
    Tiltakspakke: tiltakspakkenavn. 
    Kroneverdi: Prisår for virkningen. 
    Aktør: liste som tar verdiene: "Trafikanter og transportbrukere", "Det offentlige", "Samfunnet for øvrig", "Operatører", 'Ikke kategorisert' 
    Andel skattefinanseringskostnad: tar verdi mellom 0 og 1, avhengig av hvor stor andel av virkningen det skal beregnes skattefinanseringskostnader av. 

============================================
Ekstra kontantstrømmer
============================================

"""

from typing import List, Callable

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.hjelpefunksjoner import fyll_indeks, _legg_til_kolonne, legg_til_kolonne_hvis_mangler
from fram.generelle_hjelpemoduler.konstanter import (
    VERDSATT_COLS,
    SKATTEFINANSIERINGSKOSTNAD,
)
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.kontantstrommer.hjelpemoduler import (
    prisjuster_kontantstrom,
    legg_til_skattefinansieringskostnad_hvis_mangler,
    legg_til_aktør_hvis_mangler,
)
from fram.virkninger.kontantstrommer.schemas import KontanstromSchema
from fram.virkninger.virkning import Virkning


class Kontantstrommer(Virkning):
    def __init__(
        self,
        beregningsaar: List[int],
        kroneaar: int,
        strekning: str = "Mangler",
        tiltaksomraade: int = -1,
        logger: Callable = lambda x: None,
    ):
        """
        Klasse for generiske kontantstrømmer. Baserer seg på et inputark som inneholder
        navn på kontantstrømmen, tiltakspakke, kroneår, og kr per år i en periode som
        inneholder beregningstiden.

        Args:
            beregningsaar:  Årene som kontantstrømmene skal regnes over. Kontantstrøm oppgitt etter denne perioden ignoreres.
            kroneaar:       Prosjektets kroneår.
            strekning:      Strekningen (FRAM) prosjektet gjelder for.
            tiltaksomraade: Tiltaksområdet virkningen beregnes for (kun til indeksering av output)
            logger:         Funksjon å skrive loggen til.
        """

        self.logger = logger
        self.logger("Setter opp virkning")
        self.strekning = strekning
        self.beregningsaar = beregningsaar
        self.kroneaar = kroneaar
        self.tiltaksomraade = tiltaksomraade

        self._verdsatt_kontantstrom_ref = None
        self._verdsatt_kontantstrom_tiltak = None

    @verbose_schema_error
    @pa.check_types(lazy=True)
    def beregn(
        self,
        ytterlige_kontantstrommer_tiltak: DataFrame[KontanstromSchema],
        ytterlige_kontantstrommer_ref: DataFrame[KontanstromSchema] = None,
    ):
        """
        Funksjon for klargjøring av øvrige kontantstrømmer. Legger
        også til skattefinanseringskostnad dersom dette er relevant

        Args:
            ytterlige_kontantstrommer_tiltak: df med kontantstrømmer i tiltaksbanen
            ytterlige_kontantstrommer_ref: df med kontantstrømmer i referansebanen.

        """

        self.n_kontantstrommer = len(ytterlige_kontantstrommer_tiltak)
        self.logger("Beregner og sammenstiller")
        ytterlige_kontantstrommer_tiltak = (legg_til_skattefinansieringskostnad_hvis_mangler(ytterlige_kontantstrommer_tiltak))
        
        if ytterlige_kontantstrommer_ref is not None:
            ytterlige_kontantstrommer_ref = (legg_til_skattefinansieringskostnad_hvis_mangler(ytterlige_kontantstrommer_ref))
        self.n_kontantstrommer = len(ytterlige_kontantstrommer_tiltak)

        self._verdsatt_kontantstrom_tiltak = (
            ytterlige_kontantstrommer_tiltak.pipe(
                prisjuster_kontantstrom, self.kroneaar
            )
            .drop("Kroneverdi", axis=1)
            .pipe(
                fyll_indeks,
                Strekning=self.strekning,
                Tiltaksomraade=self.tiltaksomraade,
                Virkningsnavn="Navn",
            )
            .reset_index()
            .pipe(
                _legg_til_kolonne,
                SKATTEFINANSIERINGSKOSTNAD,
                lambda df: df["Andel skattefinansieringskostnad"],
            )
            .pipe(
                legg_til_kolonne_hvis_mangler,
                kolonnenavn=self.beregningsaar,
                fyllverdi=0.0
            )
            .drop("Andel skattefinansieringskostnad", axis=1)
            .set_index(VERDSATT_COLS)[self.beregningsaar]
            .astype(float)
        )

        if ytterlige_kontantstrommer_ref is not None:

            self._verdsatt_kontantstrom_ref = (
                ytterlige_kontantstrommer_ref.pipe(
                    prisjuster_kontantstrom, self.kroneaar
                )
                .drop("Kroneverdi", axis=1)
                .pipe(
                    fyll_indeks,
                    Strekning=self.strekning,
                    Tiltaksomraade=self.tiltaksomraade,
                    Virkningsnavn="Navn",
                )
                .reset_index()
                .pipe(
                    _legg_til_kolonne,
                    SKATTEFINANSIERINGSKOSTNAD,
                    lambda df: df["Andel skattefinansieringskostnad"],
                )
                .drop("Andel skattefinansieringskostnad", axis=1)
                .set_index(VERDSATT_COLS)[self.beregningsaar]
                .astype(float)
            )

            mangler_i_ref = self._verdsatt_kontantstrom_tiltak.loc[
                lambda df: ~df.index.isin(self._verdsatt_kontantstrom_ref.index)
            ].index

            mangler_i_tiltak = self._verdsatt_kontantstrom_ref.loc[
                lambda df: ~df.index.isin(self._verdsatt_kontantstrom_tiltak.index)
            ].index

            self._verdsatt_kontantstrom_ref = pd.concat([
                self._verdsatt_kontantstrom_ref,
                (pd.DataFrame(
                    index=mangler_i_ref,
                    columns=self._verdsatt_kontantstrom_tiltak.columns)
                .fillna(0)
                .astype(float))
            ],
                axis=0)

            self._verdsatt_kontantstrom_tiltak = pd.concat(
                [self._verdsatt_kontantstrom_tiltak,
                    pd.DataFrame(
                        index=mangler_i_tiltak,
                        columns=self._verdsatt_kontantstrom_tiltak.columns,
                    )
                    .fillna(0)
                    .astype(float)
                 ],
                axis=0
                )
            
        else:
            self._verdsatt_kontantstrom_ref = (
                pd.DataFrame(
                    columns=self._verdsatt_kontantstrom_tiltak.columns,
                    index=self._verdsatt_kontantstrom_tiltak.index,
                )
                .fillna(0)
                .astype(float)
            )

    def _get_verdsatt_brutto_ref(self):
        return self._verdsatt_kontantstrom_ref

    def _get_verdsatt_brutto_tiltak(self):
        return self._verdsatt_kontantstrom_tiltak

    def _get_volum_ref(self):
        return None

    def _get_volum_tiltak(self):
        return None

"""
=====================
Investeringskostnader
=====================

Investeringskostnadene er basert på forventningsverdier fra prosjektledere i Kystverkets regionskontorer.
Den samfunnsøkonomiske beregningsmodellen tar utgangspunkt i disse estimatene sammen med forventet anleggsperiode,
og beregner de årlige investeringskostnadene. Det er lagt til grunn at investeringskostnadene fordeler seg likt over de
ulike årene det tar før investeringen er ferdigstilt.
På samme måte kan det legges inn CO2-utslipp i anleggsfasen som spres flatt utover
anleggsperioden, før de fanges opp av virkningen Utslipp til luft, og verdsettes på linje med utslipp fra skipstrafikken.

=========================================
Virkningsklasse for investeringskostnader
=========================================

"""
from typing import List, Callable, Optional

import pandas as pd
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.hjelpefunksjoner import fyll_indeks, _legg_til_kolonne
from fram.generelle_hjelpemoduler.konstanter import (
    SKATTEFINANSIERINGSKOSTNAD,
    VERDSATT_COLS, KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG,
)
from fram.generelle_hjelpemoduler.schemas import UtslippAnleggsfasenSchema
from fram.virkninger.investering.hjelpemoduler import (
    prisjuster_investeringskostnader,
    spre_investeringskostnader,
    fyll_beregningsaar,
    sikre_bakoverkompatibilitet_investtype, spre_kostnader,
)
from fram.virkninger.investering.schemas import InvesteringskostnadSchema
from fram.virkninger.virkning import Virkning

VIRKNINGSNAVN = "Investeringskostnader"


class Investeringskostnader(Virkning):
    def __init__(
        self,
        beregningsaar: List[int],
        ferdigstillelsesaar: int,
        analysestart: int, #TODO: virkningen sjekker det og sier ifra. da burde den feile.
        kroneaar: int,
        strekning: str = None,
        logger: Callable = print,
    ):
        """
        Klasse for beregning av investeringskostnader.

        Args:
            - beregningsaar: Liste med år som beregningen skal gjøres for
            - ferdigstillelsesaar: Året med første nyttevirkning (året før blir siste år med investeringskostnader)
            - analysestart: året analysen starter fra (differansen mellom dette året og ferdigstillelsesåret kan ikke være mindre enn angitt anleggsperiode)
            - kroneaar: Året prisene er satt til
            - strekning: Navnet på strekningen analysen gjøres på
            - logger: Metode for loggføring
        """
        self.logger = logger
        self.logger("Setter opp virkning")

        self.beregningsaar = beregningsaar
        self.ferdigstillelsesaar = ferdigstillelsesaar
        self.analysestart = analysestart
        self.kroneaar = kroneaar
        self.strekning = strekning

        self._investeringskostnader_ref = None
        self._investeringskostnader_tiltak = None

        self.utslipp_anleggsfasen: Optional[UtslippAnleggsfasenSchema] = None

    def _klargjor_investeringskostnader(
        self,
        investeringskostnader: DataFrame[InvesteringskostnadSchema],
        beregningsaar: List[int],
        ferdigstillelsesaar: int,
        analysestart: int, 
    ):
        """
        Metode som pakker inn hjelpemetodene som brukes på referanse og tiltaks-
        investeringskostnader. Prisjusterer og sprer kostnadene utover beregningsårene

        Args:
            investeringskostnader: DataFrame med investeringskostnader.
            beregningsaar: Liste med år som beregningen skal gjøres for
            ferdigstillelsesaar: Året med første nyttevirkning (altså blir året før siste året investeringen gjennomføres)

        Returns:
            DataFrame: Investeringskostnader, prisjustert og spredt over beregningsårene
        """
        investeringskostnader = prisjuster_investeringskostnader(
            investeringskostnader, self.kroneaar
        )

        investeringskostnader = spre_investeringskostnader(
            investeringskostnader, "Forventningsverdi (kroner)", ferdigstillelsesaar, analysestart,
        ).assign(
            Investeringstype=lambda df: df.Investeringstype.map(
                lambda x: f"Investeringskostnader, {x.lower()}"
            )
        )

        investeringskostnader = fyll_beregningsaar(investeringskostnader, beregningsaar)
        investeringskostnader = (
            fyll_indeks(
                investeringskostnader,
                Strekning=self.strekning,
                Virkningsnavn="Investeringstype",
            )
            .reset_index()
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 1)
            .set_index(VERDSATT_COLS)
        )

        return -investeringskostnader.astype(float)

    def beregn(
        self,
        investeringskostnader_tiltak: DataFrame[InvesteringskostnadSchema],
        investeringskostnader_ref: DataFrame[InvesteringskostnadSchema] = None,
    ):
        """
        Metode for å spre og prisjustere investeringskostnader
        Args:
            investeringskostnader_tiltak: Investeringskostnadene i tiltaksscenariet
            investeringskostnader_ref: Investeringskostnadene i referansescenariet

        """

        self.logger("Beregner og verdsetter")
        investeringskostnader_tiltak = sikre_bakoverkompatibilitet_investtype(
            investeringskostnader_tiltak
        )

        InvesteringskostnadSchema.validate(investeringskostnader_tiltak)
        if investeringskostnader_ref is not None:
            investeringskostnader_ref = sikre_bakoverkompatibilitet_investtype(
                investeringskostnader_ref
            )

            InvesteringskostnadSchema.validate(investeringskostnader_ref)

        _utslipp_anleggsfasen = (
            spre_investeringskostnader(
                investeringskostnader_tiltak.pipe(
                    _legg_til_kolonne,
                    KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG,
                    lambda df: df[KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG] * 1_000 #Konverterer tonn innlest til kg for verdsetting
                ),
                KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG,
                self.ferdigstillelsesaar,
                self.analysestart,
            )
            .drop("Investeringstype", axis=1)
            .groupby(["Tiltaksomraade", "Tiltakspakke","Analysenavn"])
            .sum()
        )
        if _utslipp_anleggsfasen.sum().sum() == 0:
            self.utslipp_anleggsfasen = None
        else:
            _utslipp_anleggsfasen = _utslipp_anleggsfasen.reset_index()
            UtslippAnleggsfasenSchema.validate(_utslipp_anleggsfasen)
            self.utslipp_anleggsfasen = _utslipp_anleggsfasen

        self._investeringskostnader_tiltak = self._klargjor_investeringskostnader(
            investeringskostnader_tiltak, self.beregningsaar, self.ferdigstillelsesaar, self.analysestart,
        )
        if investeringskostnader_ref is None:
            self._investeringskostnader_ref = (
                pd.DataFrame(
                    index=self._investeringskostnader_tiltak.index,
                    columns=self._investeringskostnader_tiltak.columns,
                )
                .fillna(0)
                .astype(float)
            )

        else:
            self._investeringskostnader_ref = self._klargjor_investeringskostnader(
                investeringskostnader_ref, self.beregningsaar, self.ferdigstillelsesaar, self.analysestart,
            ).astype(float)

    def _get_verdsatt_brutto_ref(self):
        return self._investeringskostnader_ref

    def _get_verdsatt_brutto_tiltak(self):
        return self._investeringskostnader_tiltak

    def _get_volum_ref(self):
        return None

    def _get_volum_tiltak(self):
        return None

"""
============================================
Endret utslipp til luft
============================================
Verdsettingsfaktorer for lokale utslipp til luft er basert på verdsettingsfaktorer i Kystverkets veileder. Når det
gjelder globale utslipp, følger disse R-109/2021 med en hovedprisbane og to følsomhetsbaner.

Justeringsfaktor for å fremskrive utslippsfaktorer frem til 2050
---------------------------------------------------------------------------------

Kun utslipp fra bruk av drivstoffet på skipet er medregnet, ikke utslipp i forbindelse med produksjon.

MGO og HFO:

- PM10: følgende referanse er brukt «EMEP/EEA air pollutant emission inventory guidebook 2016». Nivået for 2018 er basert på gjennomsnittet av PM10 verdien for HFO og MGO. Verdien for 2050 er satt basert på kun MGO. Nox er antatt til 45 kg/tonn fuel i 2018 og 5 kg/tonn fuel i 2050.  For CO2 er antagelsen 3.2 kg/kg fuel i 2018 og 2050.

LNG:

- PM10: verdiene for LNG er hentet fra «The Norwegian Emission Inventory 2016 Documentation of methodologies for estimating emissions of greenhouse gases and long-range transboundary air pollutants». Nox fra LNG er antatt ca. 10 % av Nox sammenlignet med MGO og HFO. CO2 verdien er satt til 2,75 kg/kg fuel.  Alle utslippsverdiene for LNG er antatt like i 2018 og 2050.

Karbonnøytrale:

- Utslippene for karbonnøytralt er basert på en antagelse om at drivstoffmiksen vil være 50 % hydrogen, 25 % LBG og 25 % biodiesel.

Elektrisitet:

- Elektrisitet er antatt nullutslipp.

============================================
Virkningsklassen utslipp til luft
============================================
"""


from typing import List, Callable

import pandera as pa
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.hjelpefunksjoner import _legg_til_kolonne
from fram.generelle_hjelpemoduler.konstanter import (
    VERDSATT_COLS,
    VOLUM_COLS,
    SKATTEFINANSIERINGSKOSTNAD,
    KOLONNENAVN_VOLUM_MAALEENHET,
    KOLONNENAVN_VOLUMVIRKNING,
)
from fram.generelle_hjelpemoduler.schemas import (
    TrafikkGrunnlagSchema, TidsbrukPerPassSchema, UtslippAnleggsfasenSchema,
)
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.utslipp_til_luft import hjelpemoduler
from fram.virkninger.utslipp_til_luft.hjelpemoduler import utslippstype_til_maaleenhet
from fram.virkninger.utslipp_til_luft.schemas import (
    HastighetsSchema,
    KalkprisSchema,
)
from fram.virkninger.virkning import Virkning


class Utslipp_til_luft(Virkning):
    def __init__(
        self, trafikkaar: List[int], alle_aar: List[int], kroneaar: int, logger: Callable = print,
    ):
        """
        Klasse for beregning av utslipp for luft. Beregningen er i stor grad basert på metodikk i
        Kystverkets veileder i samfunnsøkonomiske analyser.

        Virkningen forutsetter at du har beregnet tidsbruk og hastighet per passering for ulike skipstyper og
        lengdegrupper på rett format gruppert etter skipstype og lengdegruppe. I tillegg har virkningen behov for at
        man har identifisert total trafikk (antall passeringer) for både tiltaksbanen og referansebanen.
        Virkningen vil selv benytte nasjonale kalkulasjonspriser for verdsettelse.

        Args:
            trafikkaar: liste over de årene du vil ha beregnet utslippsendringer fra trafikk for
            alle_aar: liste over alle årene det skal beregnes utslipp for (også anleggsperioden)
            kroneaar: Kroneåret du vil ha for de kalkprisene virkningen beregner selv
            logger: Hvor du vil at virkningen skal logge til. Defaulter til 'print'

        """

        self.logger = logger
        self.logger("Setter opp virkning")
        self.trafikkkaar = trafikkaar
        self.alle_aar = alle_aar
        self._verdsatt_luftutslipp_ref = None
        self._verdsatt_luftutslipp_tiltak = None
        self._verdsatt_luftutslipp_netto = None
        self._volumvirkning_ref = None
        self._volumvirkning_tiltak = None
        self.kroneaar = kroneaar

    @verbose_schema_error
    @pa.check_types(lazy=True)
    def beregn(
        self,
        tidsbruk_per_passering_ref: DataFrame[TidsbrukPerPassSchema] = None,
        tidsbruk_per_passering_tiltak: DataFrame[TidsbrukPerPassSchema] = None,
        hastighet_per_passering_ref: DataFrame[HastighetsSchema] = None,
        hastighet_per_passering_tiltak: DataFrame[HastighetsSchema] = None,
        trafikk_ref: DataFrame[TrafikkGrunnlagSchema] = None,
        trafikk_tiltak: DataFrame[TrafikkGrunnlagSchema] = None,
        kalkpris_utslipp_til_luft: DataFrame[KalkprisSchema] = None,
        utslipp_anleggsfasen: DataFrame[UtslippAnleggsfasenSchema] = None
    ):
        """
        Beregner utslipp til luft og verdsetter dette.

        Krever som input at du har en dataframe med seilingstid og hastighet i referansebanen. Du må også ha en
        tilsvarende dataframe for tiltaksbanen.

        Verdier vil være tilgjengelige på `.volumvirkning_ref`, `.volumsvirkning_tiltak`, `.verdsatt_brutto_ref`,
        `.verdsatt_brutto_tiltak` og `.verdsatt_netto`.

        Args:
            tidsbruk_per_passering_ref: Tidsbruk per passering i referansebanen. Påkrevd.
            tidsbruk_per_passering_tiltak: Gyldig dataframe med tidsbruk per passering i tiltaksbanen. Påkrevd.
            hastighet_per_passering_ref: Gyldig dataframe med hastighet i referansebanen. Påkrevd.
            hastighet_per_passering_tiltak: Gyldig dataframe med hastighet i tiltaksbanen. Påkrevd.
            trafikk_ref: Gyldig dataframe med trafikk i referansebanen. Påkrevd.
            trafikk_tiltak: Gyldig dataframe med trafikk i tiltaksbanen. Påkrevd.
            kalkpris_utslipp_til_luft: Valgfritt. Kan legge ved egne kalkpriser gitt streng formatering.
            utslipp_anleggsfasen: Valgfritt. Kan legge ved utslipp i anleggsfasen for å få fanget dem også

        Returns:
            Dataframe med verdsatte kontantstrømmer per skipstype og lengdegruppe

        """

        self.logger("Beregner og verdsetter")

        if tidsbruk_per_passering_ref is None:
            total_tidsbruk_ref = None
        else:
            total_tidsbruk_ref = tidsbruk_per_passering_ref.multiply(
                trafikk_ref, axis=0
            ).fillna(0)

        if tidsbruk_per_passering_tiltak is None:
            total_tidsbruk_tiltak = None
        else:
            total_tidsbruk_tiltak = tidsbruk_per_passering_tiltak.multiply(
                trafikk_tiltak, axis=0
            ).fillna(0)

        (
            _verdsatt_luftutslipp_ref,
            _verdsatt_luftutslipp_tiltak,
            _volumvirkning_ref,
            _volumvirkning_tiltak,
        ) = hjelpemoduler.verdsett_utslipp_til_luft(
            total_tidsbruk_ref,
            total_tidsbruk_tiltak,
            hastighet_per_passering_ref,
            hastighet_per_passering_tiltak,
            self.trafikkkaar,
            self.alle_aar,
            self.kroneaar,
            kalkpris_utslipp_til_luft,
            utslipp_anleggsfasen=utslipp_anleggsfasen
        )

        self._verdsatt_luftutslipp_tiltak = (
            _verdsatt_luftutslipp_tiltak
            .dropna(subset=["Virkningsnavn"])
            .pipe(
                _legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0
            )
            .fillna(0)
            .groupby(VERDSATT_COLS)
            .sum(numeric_only=True)[self.alle_aar]
            .multiply(-1)
        )

        if _verdsatt_luftutslipp_ref is not None:
            self._verdsatt_luftutslipp_ref = (
                _verdsatt_luftutslipp_ref
                .dropna(subset=["Virkningsnavn"])
                .pipe(
                    _legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0
                )
                .fillna(0)
                .groupby(VERDSATT_COLS)
                .sum(numeric_only=True)[self.alle_aar]
                .multiply(-1)
            )
        else:
            # Nå er det ikke verdsatt noe brutto for referansebanen. Legger til en tom dataframe for å unngå følgefeil
            self._verdsatt_luftutslipp_ref = self._verdsatt_luftutslipp_tiltak.copy().iloc[0:0]

        self._volumvirkning_tiltak = (
            _volumvirkning_tiltak.rename(columns={"Utslipp": "Virkningsnavn"})
            .pipe(
                _legg_til_kolonne,
                KOLONNENAVN_VOLUM_MAALEENHET,
                lambda df: df.Virkningsnavn.map(utslippstype_til_maaleenhet),
            )
            .pipe(
                _legg_til_kolonne,
                KOLONNENAVN_VOLUMVIRKNING,
                lambda df: df.Virkningsnavn.map(
                    hjelpemoduler.utslippstype_til_virknignsnavn
                ),
            )
            .groupby(VOLUM_COLS)
            .sum()[self.alle_aar]
        )

        if _volumvirkning_ref is not None:
            self._volumvirkning_ref = (
                _volumvirkning_ref.rename(columns={"Utslipp": "Virkningsnavn"})
                .pipe(
                    _legg_til_kolonne,
                    KOLONNENAVN_VOLUM_MAALEENHET,
                    lambda df: df.Virkningsnavn.map(utslippstype_til_maaleenhet),
                )
                .pipe(
                    _legg_til_kolonne,
                    KOLONNENAVN_VOLUMVIRKNING,
                    lambda df: df.Virkningsnavn.map(
                        hjelpemoduler.utslippstype_til_virknignsnavn
                    ),
                )
                .groupby(VOLUM_COLS)
                .sum()[self.alle_aar]
            )
        # else:
        # Nå er det ikke beregnet noe brutto for referansebanen. Legger til en tom dataframe for å unngå følgefeil
        #     self._volumvirkning_ref = self._volumvirkning_tiltak.copy().iloc[0:0]

    def _get_verdsatt_brutto_ref(self):
        return self._verdsatt_luftutslipp_ref

    def _get_verdsatt_brutto_tiltak(self):
        return self._verdsatt_luftutslipp_tiltak

    def _get_volum_ref(self):
        return self._volumvirkning_ref

    def _get_volum_tiltak(self):
        return self._volumvirkning_tiltak

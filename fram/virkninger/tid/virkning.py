"""
============================================
Endret tidsavhengige kostnader
============================================

I samfunnsøkonomiske analyser legger vi til grunn at tid alltid vil ha en alternativ anvendelse. Det innebærer at
aktørene alltid oppnår nyttevirkninger ved spart tid. Skipenes tidskostnader kan deles inn i tre deler, tidskostnader til:

- Mannskap
- Gods
- Andre tidsavhengige kostnader (forsikringer, vedlikehold, lager og administrasjon)

Tidskostnader til mannskap og andre tidsavhengige kostnader håndteres gjennom kalkulasjonsprisene for skip.
Tidskostnader for gods og passasjerer er ikke inkludert i kalkulasjonsprisene. I modellen beregnes kun tidsavhengige
kostnader for skipet. I tråd med Kystverkets veileder i samfunnsøkonomiske analyser verdsettes seilingstid etter
skipstype og skipsstørrelse. Kalkulasjonsprisene avhenger av skipstype, dødvektstonn (dwt), bruttotonnasje (bt),
gasskapasitet eller lengde på skipet.

I Kystverkets veileder (Kystverket, 2018) er det oppgitt tidsavhengige kostnader for en rekke ulike skipstyper.
Ettersom Kystverket har endret skipskategoriseringen for enkelte av skipstypene og det i etterkant at veilederen har
fremkommet ny informasjon, har vi oppdatert disse verdsettingsfaktorene. Verdsettingsfaktorene lagt til grunn i
modellen er gitt i tabellen under:



Tabell 1: Kalkulasjonspriser for tidsavhengige kostnader

+-------------------------+---------------------------+--------------------+
| Skiptsype               | Kroner per time (2021-kr) | Kilde              |
+=========================+===========================+====================+
| Oljetankskip            | 0.011*dwt+4269            | TØI (2021)         |
+-------------------------+---------------------------+--------------------+
| Kjemikalie-/Produktskip | 0.0823* dwt + 2161,3      | TØI (2021)         |
+-------------------------+---------------------------+--------------------+
| Gasstankskip            | 0.1001*gasskap + 3969,4   | TØI (2021)         |
+-------------------------+---------------------------+--------------------+
| Bulkskip                | 0,0427*dwt+1049,9         | TØI (2021)         |
+-------------------------+---------------------------+--------------------+
| Stykkgods-/Roro-skip    | 0,186*dwt+74,535          | TØI (2021)         |
+-------------------------+---------------------------+--------------------+
| Containerskip           | 0,0681*dwt+2235,7         | TØI (2021)         |
+-------------------------+---------------------------+--------------------+
| Passasjerbåt            | 1.0237*BT+2660.1          | Grønland (2013)    |
+-------------------------+---------------------------+--------------------+
| Passasjerskip/Roro      | 1.0237*BT+2660.1          | Grønland (2013)    |
+-------------------------+---------------------------+--------------------+
| Cruiseskip              | 1.0237*BT+2660.1          | Grønland (2013)    |
+-------------------------+---------------------------+--------------------+
| Offshore supplyskip	  | (dwt/4000)*3994           | TØI (2021)         |
+-------------------------+---------------------------+--------------------+
| Andre offshorefartøy	  | (dwt/4000)*3994           | TØI (2021)         |
+-------------------------+---------------------------+--------------------+
| Brønnbåt            	  | 2,076*BT+414,01           | Grønland (2013)    |
+-------------------------+---------------------------+--------------------+
| Slepefartøy         	  | (dwt/4000)*17752          | Kystverket (2018)  |
+-------------------------+---------------------------+--------------------+
| Andre servicefartøy     | 2,076*BT+414,01           | Grønland (2013)    |
+-------------------------+---------------------------+--------------------+
| Fiskefartøy ∈ [0;13}    | 496                       | Kystverket (2023)  |
+-------------------------+---------------------------+--------------------+
| Fiskefartøy ∈ [13;28]   | 92*lengde - 731           | Kystverket (2023)  |
+-------------------------+---------------------------+--------------------+
| Fiskefartøy ∈ [28;100]  | 152*lengde - 2 487        | Kystverket (2023)  |
+-------------------------+---------------------------+--------------------+

For å estimere representative tidsavhengige kostnader tar modellen utgangspunkt i
funksjonene i tabellen over, og beregner kostnader for alle unike skip som har befunnet seg innenfor Norges
territoralgrense fra 2017 til 2019. Etter at tidskostnadene per unike mmsi er beregnet, lager modellen gjennomsnittlige
verdsettingsfaktorer for unike skipstyper og lengdegrupper vektet etter et estimat på hvor ofte ulike skip innenfor
de ulike skipstypene og lengdegruppene befinner seg innenfor Norges territoralgrense. Dette estimatet er
basert på antall AIS-punkter skipet er observert i løpet av den representative perioden. Det betyr at dersom det
for eksempel har passert et relativt stort skip innenfor en skipskategori og lengdegruppe kun en gang i løpet av
perioden, mens det ellers passerer mindre skip innen samme skipskategori, så vil kalkulasjonsprisen for det store
skipet vektes ned i den gjennomsnittlige kalkulasjonsprisen.
Videre legger modellen opp til at disse verdsettingsfaktorene, beregnet til kroner per time, legges sammen med antall
timer endret seilingstid for de ulike skipstypene og lengdegruppene samt antall passeringer som får denne endrede
seilingstiden. I henhold til de generelle forutsetningene for modellen oppjusterer verdsettingsfaktorene med faktisk
realprisvekst fra 2021 til det relevante kroneåret, og KPI-justeres.


============================================
Virkningsklassen tidsavhengige kostnader
============================================

"""
from typing import List, Callable

import pandera as pa
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.hjelpefunksjoner import _legg_til_kolonne
from fram.generelle_hjelpemoduler.konstanter import (
    VERDSATT_COLS,
    SKATTEFINANSIERINGSKOSTNAD,
    KOLONNENAVN_VOLUMVIRKNING,
    KOLONNENAVN_VOLUM_MAALEENHET,
    VOLUM_COLS,
    FOLSOMHET_COLS,
    FOLSOMHET_KOLONNE,
)
from fram.generelle_hjelpemoduler.schemas import (
    TidsbrukPerPassSchema,
    TrafikkGrunnlagSchema,
)
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.tid.hjelpemoduler import (
    multipliser_venstre_hoyre,
    sjekk_alle_koblet,
)
from fram.virkninger.tid.schemas import KalkprisTidSchema
from fram.virkninger.virkning import Virkning

VIRKNINGSNAVN = "Endring i tidsavhengige kostnader"


class Tidsbruk(Virkning):
    @verbose_schema_error
    def __init__(
        self,
        beregningsaar: List[int],
        kalkulasjonspriser: DataFrame[KalkprisTidSchema],
        logger: Callable = print,
    ):
        """
        Klasse for beregning av tidsavhengige kostnader. Beregningen er i stor grad basert på metodikk i
        Kystverkets veileder i samfunnsøkonomiske analyser, men oppdaterte kalkulasjonspriser for enkelte skipstyper
        og lengdegrupper.
        Virkningen forutsetter at du har beregnet tidsbruk per passering for ulike skipstyper og
        lengdegrupper på rett format gruppert etter skipstype og lengdegruppe før og etter tiltak. I tillegg har
        virkningen behov for at man har identifisert total trafikk (antall passeringer) for både tiltaksbanen og
        referansebanen. Man kan også legge ved kalkulasjonspriser

        Args:
            beregningsaar: liste over de årene du vil ha beregnet virkningen for
            logger: Hvor du vil at virkningen skal logge til. Defaulter til 'print'
            kalkulasjonspriser: Tidsavhengige kalkulasjonsproser
        """
        self.logger = logger
        self.logger("Setter opp virkning")
        self.beregningsaar = beregningsaar
        KalkprisTidSchema.validate(kalkulasjonspriser)
        self.verdsettingsfaktorer = kalkulasjonspriser.set_index(
            ["Skipstype", "Lengdegruppe", FOLSOMHET_KOLONNE]
        )

        self._verdsatt_tidskostnad_ref = None
        self._verdsatt_tidskostnad_tiltak = None
        self._verdsatt_tidskostnad_netto = None

    @verbose_schema_error
    @pa.check_types(lazy=True)
    def beregn(
        self,
        tidsbruk_per_passering_ref: DataFrame[TidsbrukPerPassSchema],
        tidsbruk_per_passering_tiltak: DataFrame[TidsbrukPerPassSchema],
        trafikk_ref: DataFrame[TrafikkGrunnlagSchema],
        trafikk_tiltak: DataFrame[TrafikkGrunnlagSchema],
    ):
        """
        Beregner tidsbruken og verdsetter dette forbruket.

        Virkningen forutsetter at du har beregnet tidsbruk per passering og antall passeringer for ulike skipstyper og
        lengdegrupper på rett format gruppert etter skipstype og lengdegruppe for referanse- og tiltaksbanen.
        Virkningen vil selv benytte nasjonale kalkulasjonspriser for verdsettelse.

        Args:
            tidsbruk_per_passering_ref: Tidsbruk per passering i referansebanen over år. Påkrevd.
            tidsbruk_per_passering_tiltak: Gyldig dataframe med tidsbruk per passering i tiltaksbanen over år. Påkrevd.
            trafikk_ref: Gyldig dataframe med trafikk i referansebanen over år. Påkrevd.
            trafikk_tiltak:  Gyldig dataframe med trafikk i tiltaksbanen over år. Påkrevd.

        Returns:
            Dataframe med verdsatte kontantstrømmer per skipstype og lengdegruppe

        """
        self.logger("Beregner og verdsetter")

        total_tidsbruk_ref = (
            tidsbruk_per_passering_ref.multiply(trafikk_ref, axis=0, fill_value=0)[
                self.beregningsaar
            ]
            .reset_index()
            .dropna()
            .set_index(FOLSOMHET_COLS)
        )
        total_tidsbruk_tiltak = (
            tidsbruk_per_passering_tiltak.multiply(
                trafikk_tiltak, axis=0, fill_value=0
            )[self.beregningsaar]
            .reset_index()
            .dropna()
            .set_index(FOLSOMHET_COLS)
        )

        self._volum_ref = (
            total_tidsbruk_ref.reset_index()
            .pipe(_legg_til_kolonne, KOLONNENAVN_VOLUMVIRKNING, "Tidsbruk")
            .pipe(_legg_til_kolonne, KOLONNENAVN_VOLUM_MAALEENHET, "Timer")
            .set_index(VOLUM_COLS)[self.beregningsaar]
        )
        self._volum_tiltak = (
            total_tidsbruk_tiltak.reset_index()
            .pipe(_legg_til_kolonne, KOLONNENAVN_VOLUMVIRKNING, "Tidsbruk")
            .pipe(_legg_til_kolonne, KOLONNENAVN_VOLUM_MAALEENHET, "Timer")
            .set_index(VOLUM_COLS)[self.beregningsaar]
        )

        self.total_tidsbesparelse = total_tidsbruk_ref.subtract(
            total_tidsbruk_tiltak, fill_value=0
        )

        self._verdsatt_tidskostnad_ref = (
            multipliser_venstre_hoyre(
                total_tidsbruk_ref[self.beregningsaar].reset_index(),
                self.verdsettingsfaktorer[self.beregningsaar].reset_index(),
                ["Skipstype", "Lengdegruppe", FOLSOMHET_KOLONNE],
                self.beregningsaar,
            )
            .pipe(
                sjekk_alle_koblet,
                feilmelding="Mangler tidsverdsettingsfaktorer for noen skipstyper/lengdegrupper som har trafikk",
                lete_kolonner=[str(col) + "_x" for col in self.beregningsaar],
                unntak="Lengdegruppe",
                unntak_verdi="Mangler lengde",
            )
            .assign(Virkningsnavn=VIRKNINGSNAVN)
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0)
            .set_index(VERDSATT_COLS)[self.beregningsaar]
            .fillna(0)
            .multiply(-1)
        )

        self._verdsatt_tidskostnad_tiltak = (
            multipliser_venstre_hoyre(
                total_tidsbruk_tiltak[self.beregningsaar].reset_index(),
                self.verdsettingsfaktorer[self.beregningsaar].reset_index(),
                ["Skipstype", "Lengdegruppe", FOLSOMHET_KOLONNE],
                self.beregningsaar,
            )
            .pipe(
                sjekk_alle_koblet,
                feilmelding="Mangler tidsverdsettingsfaktorer for noen skipstyper/lengdegrupper som har trafikk",
                lete_kolonner=[str(col) + "_x" for col in self.beregningsaar],
                unntak="Lengdegruppe",
                unntak_verdi="Mangler lengde",
            )
            .assign(Virkningsnavn=VIRKNINGSNAVN)
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0)
            .set_index(VERDSATT_COLS)[self.beregningsaar]
            .fillna(0)
            .multiply(-1)
        )

        self._verdsatt_tidskostnad_netto = self._verdsatt_tidskostnad_ref.subtract(
            self._verdsatt_tidskostnad_tiltak, fill_value=0
        )

    def _get_verdsatt_brutto_ref(self):
        return self._verdsatt_tidskostnad_ref

    def _get_verdsatt_brutto_tiltak(self):
        return self._verdsatt_tidskostnad_tiltak

    def _get_volum_ref(self):
        return self._volum_ref

    def _get_volum_tiltak(self):
        return self._volum_tiltak

"""
============================================
Endret ulykkesrisiko
============================================

Enkelte tiltak vil påvirke ulykkesrisikoen for grunnstøtinger, kollisjoner og kontaktskader. Endret ulykkesrisiko påvirker aktørene og samfunnet som følge av at lavere risiko kan bidra til færre ulykker. Den samfunnsøkonomiske verdien av færre ulykker som beregnes i modellen er:

-	Reduserte reparasjonskostnader
-	Reduserte kostnader ved at skipet er ute av drift
-	Reduserte opprenskningskostnader i tilfelle utslipp
-	Reduserte skader på natur, miljø og friluftsliv/rekreasjon i tilfelle utslipp
-	Færre dødsfall og personskader

Den nautiske risikoanalysen estimerer ulykkesfrekvenser for de ulike tiltakene og nullalternativet. Vi antar at verdien av risikoreduksjonen tilfaller norske aktører og dermed i sin helhet skal inkluderes i analysen.

På denne siden redegjør vi først for hva de ulike virkningene innebærer, før vi nederst forklarer hvordan endringen i antall hendelser er beregnet, og grensesnittet mellom den nautiske risikoanalysen og FRAM.

Reparasjonskostnader og tid ute av drift
----------------------------------------

Modellen beregner endringer i materielle skader (tid ute av drift og reparasjonskostnader) i tråd med metodikken angitt i Kystverkets veileder for samfunnsøkonomiske analyser. Det har imidlertid kommet oppdaterte anslag på enhetsanslagene på antall timer ute av drift og reparasjonskostnader ved kollisjon, grunnstøting og kontaktskader. Anslagene som ligger til grunn i modellen er basert på estimater fra Propel (2019) med justeringer foretatt av Kystverket.

Personskader og dødsfall
----------------------------------------

Ikke alle ulykker medfører personskader og dødsfall. I modellen beregnes forventet endring i antall dødsfall og personskader basert på:
-	Sannsynligheten for dødsfall og personskade gitt en ulykke for ulike typer ulykker (kollisjoner, kontaktskader og grunnstøtinger)
-	Antall personskader/dødsfall gitt en ulykke med personskader/dødsfall (kollisjoner, kontaktskader og grunnstøtinger)

Input for å beregne de to overstående faktorene er basert på DNV GLs konsekvensmodell. Verdsettingen av tapte menneskeliv og personskader er vist i tabellen under.

.. list-table:: Verdsettingsfaktorer tapte menneskeliv og personskader. Statens vegvesen (2018)
   :widths: 30 30 15 25
   :header-rows: 1

   * - Hendelse
     - Verdsettingsfaktorer
     - Kroneverdi
     - Kilde
   * - Kr per tapte menneskeliv
     - 30 200 000
     - 2016
     - Statens vegvesen (2018)
   * - Kr per personskade
     - 3 000 000
     - 2016
     - Statens vegvesen (2018)



Velferdsutslipp av olje
----------------------------------------
Velferdsutslipp av olje er basert på metodikk beskrevet i Kystverkets veileder i samfunnsøkonomiske analyser. Kalkulasjonsprisen for utslipp av olje avhenger av geografisk plassering (fylke), miljøsårbarhet i området, utslippsmengder og type oljeutslipp.
Modellen tar utgangspunkt i forventede utslippsmengder for bunkers- og lastolje, og kategoriserer disse innenfor ulike intervaller i tråd med eksisterende metodikk. Modellen bruker informasjon om forventede utslippsmengder og type drivstoff fra DNVs konsekvensmodell.
Deretter identifiseres riktig kalkulasjonspris for oljeutslippet, gitt et oljeutslipp, ved å innhente informasjon om geografisk plassering av det forventede utslippet, miljøsårbarheten i området og type drivstoff som slippes ut. Vi har brukt havmiljo.no/kart til å identifisere hvilke ressurser (fugler, sjøpattedyr, naturtyper) og arter som er sårbare for akutt oljeforurensning. Sårbarhetsvurderingene er foretatt av miljøforvaltningen og det rapporteres verdier for hver måned. Vi har identifisert den ressursen/arten som har størst miljøsårbarhet innenfor tiltakspakkens område, og deretter valgt den høyeste månedsverdien for den ressursen/arten. Miljøsårbarhetsverdien er deretter klassifisert etter fire kategorier (lav, moderat, høy, svært høy).
Kalkulasjonsprisene for utslipp er basert på informasjon fra Kystverkets veileder i samfunnsøkonomiske analyser. Når riktig kalkulasjonspris gitt overnevnte faktorer er identifisert, multipliseres denne med forventet antall hendelser fra risikoanalysene og sannsynligheten for at hendelsen er en hendelse med oljeutslipp. Vi har antatt at på lik linje som for drivstoff, vil det være endringer i drivstoffsammensetningen fremover. Vi har derfor justert for dette ved å justere sannsynligheten for utslipp med nedgangen i drivstoff som medfører utslipp.

Opprenskingskostnader
----------------------------------------
Opprenskingskostnadene estimeres basert på forventet utslippsmengder fra DNV GLs konsekvensmodell. Verdsettingsfaktorene som er lagt til grunn er hentet fra Kystverkets veileder i samfunnsøkonomiske analyser.



Forholdet mellom de nautiske risikoanalysene og FRAM
---------------------------------------------
I de aller fleste tilfeller, og i alle versjoner av FRAM før 3.5, ble risikoanalysene utført i programmet IWRAP. Fra IWRAP genereres et sett med resultatfiler, som måler frekvenser (absolutt antall hendelser) per år, på rutenivå.
Det genereres frekvenser fra IWRAP for to såkalte RA-år. Disse filene leses så inn i FRAM og omdannes til prognostiserte hendelser for alle analyseårene.
Innlesing skjer ved hjelp av kode i filen `~fram.virkninger.risiko.hjelpemoduler.generelle` og fremskrivingen ved hjelp av `~fram.virkninger.risiko.hjelpemoduler.iwrap_fremskrivinger`.

I FRAM 3.5 introduserte vi muligheten til å også benytte risikoanalyser beregnet i verktøyet AISyRISK. I dette verktøyet genereres det frekvenser kun for ett RA-år. I AISyRISK benyttes en annen kategorisering etter
skipstype og lengdegruppe enn det som gjøres i FRAM og IWRAP. Disse må derfor konverteres for å kunne benyttes inn i FRAM. Konverteringsmatrisene ligger i boken `Forutsetninger_FRAM.xlsx` i fanene
`aisyrisk_skipstypekonvertering` og `aisyrisk_lengdekonvertering`. For å benytte AISyRISK-kjøringer må det angis ved initialisering av FRAM (`aisyrisk_input=True`).
Risikokjøringen leses da inn av kode i filen `~fram.virkninger.risiko.hjelpemoduler.generelle` og konvertering og fremskrivingen skjer ved hjelp av kode i filen
`~fram.virkninger.risiko.hjelpemoduler.aisyrisk`.

I alle tilfeller fremskrives grunnstøtinger lineært med trafikken, altså med en konstant hendelsessannsynlighet per passering i FRAM.
Kollisjoner håndteres ulikt, avhengig av hvilken risikomodell som er bemyttet.

Når IWRAP er benyttet for å beregne risikoeffekter, fremskrives antall hendelser som en kvadratisk funksjon av trafikken:
Antall hendelser i år :math:`t, H_t = P_t*T_t`, der P_t er
hendelsessannsynligheten i år t og T_t er trafikk i år t. Antar at
:math:`P_t = P_startaar * ( 1 + \\beta * ( (T_t - T_startaar)/(T_fremtidsaar - T_startaar) ))`, slik at hendelsessannsynligheten er
lineær i trafikken, og går fra P_startaar til P_fremtidsaar.
P_t er lik P_startaar i startaar og P_fremtidsaar i fremtidsaar. Hvis vi løser dette uttrykket for :math:`\\beta` i fremtidsåret, får vi
:math:`\\beta = (P_fremtidsaar - P_startaar)/P_startaar`

Når AISyRISK er benyttet, foreligger det kun én RA, og vi har ikke informasjon til å beregne parameterne i den kvadratiske funksjonen over. Det regner derfor ut
én konstant hendelsessannsynlighet per FRAM-passering, og antall kollisjoner fremskrives så proporsjonalt med trafikken, :math:`t, H_t = P_r*T_t`, der P_r er
hendelsessannsynligheten i RA-året r og T_t er trafikk i år t.


Konsekvensreduserende tiltak
---------------------------------------------
Det er siden `FRAM_cruise` lagt til rette for konsekvensreduserende tiltak. For å kunne gjennomføre slike, må man angi konsekvensmatriser, enten for skade/dødsfall, eller utslipp.

For skade/dødsfall angis disse i form av konkrete sannsynligheter for hhv dødsfall og skade, og forventet antall dødsfall/skade gitt at
minst én slik inntreffer. Defaultverdier ligger lagret i `Forutsetninger_SOA.xlsx`, og kan hentes ut ved `~fram.virkninger.risiko.hjelpemoduler.generelle.hent_ut_konsekvensinput`, som tar et valgfritt argument `excel_filbane`, slik at du kan lagre filen til enklere bruk.
For å vurdere konsekvensreduserende tiltak, må det legges et ark med tilsvarende format i input-boken din. Et ark `Konsekvensinput referansebanen` overstyrer referansebanekonsekvensene, mens et ark `Konsekvensinput TP {tiltakspakke}` overstyrer for tiltakspakken.
Når det først angis konsekvensmatrise for enten ref eller tiltak, må det angis for alle skip, lengder og ruter. Default-inputen har bare id-kolonnene Skipstype, Lengdegruppe og Hendelse. Dersom man vil differensiere per Analyseomraade eller Rute, kan man legge til
denne kolonnen, og angi fulle konsekvensinputer for hvert Analyseomraade eller hver Rute. Hvis man ikke angir det ene nivået, antas det at man vil ha like verdier for alle disse. (Hvis man legger inn kolonnen Analyseomraade, med to verdier for de to analyseområdene
sine, men ikke angir kolonnen Rute, forutsetter FRAM at du vil ha like konsekvenser på alle ruter i hvert analyseområde.)


For utslippskonsekvenser må man først finne ut av hvilke analyseområder man vil endre utslippskonsekvensene for, og om man vil endre for referanse, tiltak eller begge. For hvert analyseområde og hver ref/tiltak man vil endre,
 må man i input-boken legge inn fullverdige utslippskonsekvensark på nøyaktig samme format som arket `konsekvenser_utslipp` i booken `Forutsetninger_SOA.xlsx`. For at FRAM skal finne disse, må arknavnene angis i kolonne AR:AT
 i arket for den aktuelle tiltakspakken. Se eksempel i `tests/input/strekning 11-konsekvensreduksjon.xlsx`. For de analyseområdene og de ref/tiltaks-banene der brukeren ikke har angitt noe, benyttes standard fra FRAM.

Trafikkgrunnlag når AISyRisk skal benyttes
---------------------------------------------
I AISyRISK er det utseilt distanse som benyttes til å måle trafikkvolumet, ikke antall passeringer som i IWRAP/FRAM. Det innebærer at analytiker må ta ekstra hensyn
når det skal gjennomføres analyser med der AISyRISK benyttes. Videre opererer AISyRISK på et rutenett, der trafikken telles innad i hver rute. For å gjøre gode
samfunnsøkonomiske analyser der FRAM og AISyRISK benyttes, må man første definere analyseområder i FRAM som korresponderer til én eller flere celler i
rutenettet som benyttes av AISyRISK. Deretter leser man inn AISyRISK-resultatene og tildeler analyseområde til hver celle i AISyRISK-outputen.

For å generere et trafikkgrunnlag, må man konvertere utseilt distanse til et mål på antall passeringer. Én mulighet her å hente AIS-data på haleformat
og telle antall haler som har passsert gjennom hvert analyseområde i trafikkgrunnlagsåret. Da vektes hver hale likt. En annen mulighet er å hente AIS-data
på punktformat og telle antall punkter. Da vekter man tid brukt i analyseområdet, med ulik vekt per passering. Hvilken metodikk det er mest hensiktsmessig
å benytte, avhenger av andre deler av analysen. Dersom man for eksempel har tidsbruk per passering og skal analysere endringer i denne, vil AIS-punkter
være en dårlig trafikkenhet. Da vil antall haler være et bedre mål på trafikkarbeidet. Med mindre man har behov for trafikkgrunnlaget til bruk i andre
deler av analysen, anbefales det at man benytter antall AIS-punkter innenfor analyseområdet som trafikkmål når man bruker AISyRISK som risikomodell.


============================================
Virkningsklassen Risiko
============================================


"""

from typing import List, Optional, Callable

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.konstanter import VOLUM_COLS
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.risiko.hjelpemoduler import generelle as hjelpemoduler
from fram.virkninger.risiko.hjelpemoduler.generelle import ARKNAVN_KONSEKVENSER_UTSLIPP
from fram.virkninger.risiko.hjelpemoduler.verdsetting import (
    get_kalkpris_materielle_skader,
    get_kalkpris_helse,
    get_kalkpris_oljeutslipp,
    get_kalkpris_opprenskingskostnader,
)
from fram.virkninger.risiko.schemas import (
    HendelseSchema,
    SarbarhetSchema,
    KalkprisHelseSchema,
    KalkprisMaterielleSchema,
    KalkprisOljeutslippSchema,
    KalkprisOljeopprenskingSchema, KonsekvensmatriseSchema,
)
from fram.virkninger.tid.schemas import KalkprisTidSchema
from fram.virkninger.virkning import Virkning


class Risiko(Virkning):
    @verbose_schema_error
    def __init__(
        self,
        beregningsaar: List[int],
        sarbarhet: DataFrame[SarbarhetSchema],
        kalkpriser_materielle_skader: Optional[
            DataFrame[KalkprisMaterielleSchema]
        ] = None,
        kalkpriser_helse: Optional[DataFrame[KalkprisHelseSchema]] = None,
        kalkpriser_oljeutslipp_ref: Optional[DataFrame[KalkprisOljeutslippSchema]] = None,
        kalkpriser_oljeutslipp_tiltak: Optional[DataFrame[KalkprisOljeutslippSchema]] = None,
        kalkpriser_oljeopprensking_ref: Optional[
            DataFrame[KalkprisOljeopprenskingSchema]
        ] = None,
        kalkpriser_oljeopprensking_tiltak: Optional[
            DataFrame[KalkprisOljeopprenskingSchema]
        ] = None,
        kalkpriser_tid: Optional[DataFrame[KalkprisTidSchema]] = None,
        kroneaar: Optional[int] = None,
        logger: Callable = print,
    ):
        """
        Virkning for å beregne de risikoavhengige virkningene knyttet til helse, materielle skader og oljeutslipp

        Virkningen forutsetter at du har beregnet hendelser på rett format, gruppert etter grunnstøting, kontaktskade,
        striking (kollisjon) og struck (kollisjon). Virkningen behøver også rett definerte kalkulasjonspriser, ferdig
        realprisjustert. Ved beregning krever virkningen at man angir både antall hendelser og en konsekvensmatrise som
        konverterer fra hendelser til konsekvenser, både personskader, dødsfall, reparasjonskostnader, kostnader til tid ute av drift,
        velferdstapet ved oljeutslipp og opprenskingskostnaden ved disse. Dette må angis for referansebanen, og kan
        angis for tiltaksbanen hvis man ønsker å analysere en endring.

        Args:
            beregningsaar: liste over de årene du vil ha beregnet virkningen for
            sarbarhet: en dataframe med sårbarhetsvurdering for de berørte områdene
            kalkpriser_materielle_skader: Valgri. Hvis angitt, må det være en gyldig dataframe med kalkpriser for materielle skader
            kalkpriser_helse: Valgri. Hvis angitt, må det være en gyldig dataframe med kalkpriser for helse
            kalkpriser_oljeutslipp_ref: Valgri. Hvis angitt, må det være en gyldig dataframe med kalkpriser for oljeutslipp
            kalkpriser_oljeutslipp_tiltak: Valgri. Hvis angitt, må det være en gyldig dataframe med kalkpriser for oljeutslipp
            kalkpriser_oljeopprensking_ref: Valgri. Hvis angitt, må det være en gyldig dataframe med kalkpriser for oljeopprensking
            kalkpriser_oljeopprensking_tiltak: Valgri. Hvis angitt, må det være en gyldig dataframe med kalkpriser for oljeopprensking
            kalkpriser_tid: Valgri. Hvis angitt, må det være en gyldig dataframe med kalkpriser for tidsbruk. Hvis de andre kalkprisene ikke er angitt, må denne være angitt, slik at de andre kan beregnes korrekt.
            kroneaar: Kroneåret du vil ha for de kalkprisene virkningen beregner selv
            logger: Hvor du vil at virkningen skal logge til. Defaulter til 'print'
        """
        self.logger = logger
        self.logger("Setter opp virkning")
        if kalkpriser_materielle_skader is None:
            assert (
                kalkpriser_tid is not None
            ), "Når du ikke har angitt 'kalkpris_materielle_skader', må du angi 'kalkpriser_tid'"
            KalkprisTidSchema.validate(kalkpriser_tid)
            kalkpriser_materielle_skader = get_kalkpris_materielle_skader(
                kroneaar=kroneaar,
                beregningsaar=beregningsaar,
                tidskostnader=kalkpriser_tid,
            )
        self.kalkpriser_materielle_skader = kalkpriser_materielle_skader
        if kalkpriser_helse is None:
            kalkpriser_helse = get_kalkpris_helse(
                kroneaar=kroneaar, siste_aar=beregningsaar[-1]
            )
        self.kalkpriser_helse = kalkpriser_helse

        if kalkpriser_oljeutslipp_ref is None:
            self.logger(
                "Fikk ikke kalkpriser for oljeutslipp i referansebanen. Bruker standardpriser med konsekvensmatrise fra FRAMs standardforutsetninger")
            if kroneaar is None:
                raise KeyError("Kan ikke hente kalkpriser fra Risiko-virkningen uten angitt kroneaar.")
            kalkpriser_oljeutslipp_ref = get_kalkpris_oljeutslipp(kroneaar=kroneaar, beregningsaar=beregningsaar,
                                                                  konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP)
        self.kalkpriser_oljeutslipp_ref = kalkpriser_oljeutslipp_ref
        if kalkpriser_oljeutslipp_tiltak is None:
            self.logger(
                "Fikk ikke kalkpriser for oljeutslipp i tiltaksbanen. Bruker standardpriser med konsekvensmatrise fra FRAMs standardforutsetninger")
            kalkpriser_oljeutslipp_tiltak = get_kalkpris_oljeutslipp(kroneaar=kroneaar, beregningsaar=beregningsaar,
                                                                     konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP)
        self.kalkpriser_oljeutslipp_tiltak = kalkpriser_oljeutslipp_tiltak

        if kalkpriser_oljeopprensking_ref is None:
            self.logger(
                "Fikk ikke kalkpriser for oljeopprensking i referansebanen. Bruker standardpriser med konsekvensmatrise fra FRAMs standardforutsetninger")
            kalkpriser_oljeopprensking_ref = get_kalkpris_opprenskingskostnader(
                kroneaar=kroneaar, beregningsaar=beregningsaar,
                konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP
            )
        self.kalkpriser_oljeopprensking_ref = kalkpriser_oljeopprensking_ref

        if kalkpriser_oljeopprensking_tiltak is None:
            self.logger(
                "Fikk ikke kalkpriser for oljeopprensking i tiltaksbanen. Bruker standardpriser med konsekvensmatrise fra FRAMs standardforutsetninger")
            kalkpriser_oljeopprensking_tiltak = get_kalkpris_opprenskingskostnader(
                kroneaar=kroneaar, beregningsaar=beregningsaar,
                konsekvenser_utslipp_sheet_name=ARKNAVN_KONSEKVENSER_UTSLIPP
            )
        self.kalkpriser_oljeopprensking_tiltak = kalkpriser_oljeopprensking_tiltak

        self.sarbarhet = sarbarhet

        self.beregningsaar = beregningsaar

        self._volumvirkning_ref = []
        self._volumvirkning_tiltak = []

        self._verdsatt_risiko_ref = []
        self._verdsatt_risiko_tiltak = []

        SarbarhetSchema.validate(self.sarbarhet, lazy=True)
        KalkprisMaterielleSchema.validate(self.kalkpriser_materielle_skader, lazy=True)
        KalkprisHelseSchema.validate(self.kalkpriser_helse, lazy=True)
        KalkprisOljeutslippSchema.validate(self.kalkpriser_oljeutslipp_ref, lazy=True)
        KalkprisOljeutslippSchema.validate(self.kalkpriser_oljeutslipp_tiltak, lazy=True)
        KalkprisOljeopprenskingSchema.validate(
            self.kalkpriser_oljeopprensking_ref, lazy=True
        )
        KalkprisOljeopprenskingSchema.validate(
            self.kalkpriser_oljeopprensking_tiltak, lazy=True
        )

    @pa.check_types(lazy=True)
    def beregn(
        self,
        hendelser_ref: DataFrame[HendelseSchema],
        konsekvensmatrise_ref: DataFrame[KonsekvensmatriseSchema],
        hendelser_tiltak: Optional[DataFrame[HendelseSchema]] = None,
        konsekvensmatrise_tiltak: Optional[DataFrame[KonsekvensmatriseSchema]] = None,
    ):
        """
        Beregner alle risikokonsekvensene og verdsetter dem

        Krever som input at du har en dataframe med hendelser i referansebanen og en konsekvensmatrise som konverterer
        hendelser til konsekvenser. Hvis du analyserer effekten av et tiltak, må du også ha en tilsvarende dataframe
        for tiltaksbanen. Stegene i beregn-funksjonen er som følger:

        1. Beregner helsekonsekvenser ved hjelp av :py:func:`~fram.virkninger.risiko.hjelpemoduler.generelle._beregn_helsekonsekvenser`
        2. Beregner og verdsetter materielle skader ved hjelp av :py:func:`~fram.virkninger.risiko.hjelpemoduler.generelle.verdsett_materielle_skader`
        3. Verdsetter helsekonsekvensene ved hjelp av :py:func:`~fram.virkninger.risiko.hjelpemoduler.generelle.verdsett_helse`
        4. Verdsetter oljeutslipp ved hjelp av :py:func:`~fram.virkninger.risiko.hjelpemoduler.generelle.verdsett_oljeutslipp`
        5. Beregner og vedsetter opprenskingskostnader etter oljeutslipp ved hjelp av :py:func:`~fram.virkninger.risiko.hjelpemoduler.generelle.verdsett_opprenskingskostnader`

        Verdier vil være tilgjengelig på `.volumvirkning_ref`, `.volumvirkning_tiltak`, `.verdsatt_brutto_ref`,
        `.verdsatt_brutto_tiltak` og `.verdsatt_netto`.

        Args:
            hendelser_ref: Gyldig dataframe med hendelser i referansebanen. Påkrevd
            hendelser_tiltak: Gyldig dataframe med hendelser i referansebanen. Valgfritt

        """
        self.logger("Beregner og verdsetter")

        self._volumvirkning_ref.append(
            hendelser_ref.reset_index()
            .assign(
                Virkningsnavn=lambda df: "Hendelser - " + df.Hendelsestype,
                Måleenhet="Antall",
            )
            .drop(["Risikoanalyse", "Hendelsestype"], axis=1)
            .set_index(VOLUM_COLS)
        )

        self.logger("  Helsekonsekvenser")
        (
            helsekonsekvenser_ref,
            helsekonsevenser_tiltak,
            helsekonsekvenser_endring,
        ) = hjelpemoduler._beregn_helsekonsekvenser(
            hendelser_ref=hendelser_ref,
            hendelser_tiltak=hendelser_tiltak,
            konsekvensmatrise_ref=konsekvensmatrise_ref,
            konsekvensmatrise_tiltak=konsekvensmatrise_tiltak,
            beregningsaar=self.beregningsaar,
        )
        self.logger("  Verdsetter materielle skader")
        (
            mat_verdsatt_ref,
            mat_verdsatt_tiltak,
            _,
        ) = hjelpemoduler.verdsett_materielle_skader(
            hendelser_ref=hendelser_ref,
            hendelser_tiltak=hendelser_tiltak,
            kroner_hendelser=self.kalkpriser_materielle_skader,
            beregningsaar=self.beregningsaar,
        )
        self.logger("  Verdsetter helse")
        (helse_verdsatt_ref, helse_verdsatt_tiltak) = hjelpemoduler.verdsett_helse(
            konsekvenser_ref=helsekonsekvenser_ref,
            konsekvenser_tiltak=helsekonsevenser_tiltak,
            verdsettingsfaktorer=self.kalkpriser_helse,
            beregningsaar=self.beregningsaar,
        )
        self.logger("  Verdsetter oljeutslippskostnader")
        (
            oljeutslipp_verdsatt_ref,
            oljeutslipp_verdsatt_tiltak,
            utvalgte_oljeverdsettingsfaktorer,
        ) = hjelpemoduler.verdsett_oljeutslipp(
            hendelser_ref=hendelser_ref,
            hendelser_tiltak=hendelser_tiltak,
            kalkulasjonspriser_ref=self.kalkpriser_oljeutslipp_ref,
            kalkulasjonspriser_tiltak=self.kalkpriser_oljeutslipp_tiltak,
            sarbarhet=self.sarbarhet,
            beregningsaar=self.beregningsaar,
        )
        self.logger("  Verdsetter oljeopprenskingskostander")
        (
            kroner_opprensking_ref,
            kroner_opprensking_tiltak,
            utvalgt_verdsett_opprensking,
        ) = hjelpemoduler.verdsett_opprenskingskostnader(
            hendelser_ref=hendelser_ref,
            hendelser_tiltak=hendelser_tiltak,
            kalkulasjonspriser_ref=self.kalkpriser_oljeopprensking_ref,
            kalkulasjonspriser_tiltak=self.kalkpriser_oljeopprensking_tiltak,
            beregningsaar=self.beregningsaar,
        )
        self.logger("  Sammenstiller på klassen")
        self._volumvirkning_ref.append(
            helsekonsekvenser_ref.reset_index()
            .drop(["Hendelsestype", "Risikoanalyse"], axis=1)
            .groupby(VOLUM_COLS)
            .sum()
        )
        self._verdsatt_risiko_ref.append(mat_verdsatt_ref.multiply(-1))
        self._verdsatt_risiko_ref.append(helse_verdsatt_ref.multiply(-1))
        self._verdsatt_risiko_ref.append(oljeutslipp_verdsatt_ref.multiply(-1))
        self._verdsatt_risiko_ref.append(kroner_opprensking_ref.multiply(-1))

        self.utvalgte_oljeverdsettingsfaktorer = utvalgte_oljeverdsettingsfaktorer
        self.utvalgte_oljeopprenskingsfaktorer = utvalgt_verdsett_opprensking

        if hendelser_tiltak is not None:
            self._volumvirkning_tiltak.append(
                helsekonsevenser_tiltak.reset_index()
                .drop(["Hendelsestype", "Risikoanalyse"], axis=1)
                .groupby(VOLUM_COLS)
                .sum()
            )
            self._volumvirkning_tiltak.append(
                hendelser_tiltak.reset_index()
                .assign(
                    Virkningsnavn=lambda df: "Hendelser - " + df.Hendelsestype,
                    Måleenhet="Antall",
                )
                .drop(["Risikoanalyse", "Hendelsestype"], axis=1)
                .set_index(VOLUM_COLS)
            )

            self._verdsatt_risiko_tiltak.append(mat_verdsatt_tiltak.multiply(-1))
            self._verdsatt_risiko_tiltak.append(helse_verdsatt_tiltak.multiply(-1))
            self._verdsatt_risiko_tiltak.append(
                oljeutslipp_verdsatt_tiltak.multiply(-1)
            )
            self._verdsatt_risiko_tiltak.append(kroner_opprensking_tiltak.multiply(-1))

    def _beregn_materielle(self):
        pass

    def _beregn_olje(self):
        pass

    def _get_verdsatt_brutto_ref(self):
        return pd.concat(self._verdsatt_risiko_ref, axis=0)

    def _get_verdsatt_brutto_tiltak(self):
        return pd.concat(self._verdsatt_risiko_tiltak, axis=0)

    def _get_volum_ref(self):
        return (
            pd.concat(self._volumvirkning_ref, axis=0)
            .groupby(VOLUM_COLS)[self.beregningsaar]
            .sum()
        )

    def _get_volum_tiltak(self):
        return (
            pd.concat(self._volumvirkning_tiltak, axis=0)
            .groupby(VOLUM_COLS)[self.beregningsaar]
            .sum()
        )

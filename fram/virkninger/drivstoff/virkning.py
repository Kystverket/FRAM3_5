"""
============================================
Endret distanseavhengige kostnader
============================================
Beregning av distanseavhengige kostnader i Kystverkets analyser består utelukkende av drivstoffkostnader. Beregningen i
FRAM-modellen er i stor grad basert på metodikk i Kystverkets veileder i samfunnsøkonomiske analyser (Kystverket 2018),
men vi har gjort enkelte oppdateringer av forutsetningene som ligger til grunn. For det første legger ikke eksisterende
metodikk i veilederen opp til framskrivninger av drivstofforbruket over tid. Ettersom det forventes store endringer i
både teknologi og type drivstoff fremover, og de samfunnsøkonomiske virkningene vurderes over en periode på 75 år, har
vi lagt til grunn framskrivninger av hvilke drivstoff/energibærere som antas benyttet fremover med tilhørende forbruk.

I de følgende avsnittene oppsummerer vi antagelser, vurderinger og referanser som ligger til grunn for beregningene.
Fremtidig forbruk, miks og priser på drivstoff for skipsflåten er både komplekst og forbundet med usikkerhet.
Det har derfor vært nødvendig å gjøre forenklinger og antagelser knyttet til drivstoffet. Disse er ansett å gi
tilstrekkelig nøyaktighet for bruk i de samfunnsøkonomiske beregningene. De ulike variablene knyttet til drivstoffet er
gitt i form av verdier i skipsmatrisene (skipstype og størrelse) som blir benyttet i analysene. Sensitivitetsanalyser i
de samfunnsøkonomiske analysene er forutsatt benyttet for å håndtere usikkerheten og avdekke sensitiviteter knyttet til
de ulike nøkkelparameterne som er gitt. De forenklingene, antagelser og tilpasninger som er gjort i dette
prosjektarbeidet er tilpasset anvendelsen til samfunnsøkonomiske analyser av farledstiltak og datagrunnlaget og
konklusjoner må derfor ikke benyttes til andre formål. Grunnlaget er utarbeidet av DNV GL og dokumentert i et teknisk
notat, se DNV GL (2020).

Fremgangsmåten for å prissette drivstoffkostnader kan oppsummeres gjennom følgende trinn:

- Trinn 1: Beregner energibehovet til fremdrift, propulsjonseffekten, for en gitt fartøystype og størrelse.
- Trinn 2: Fremskriver energibehovet til 2050 ved hjelp av effektiviseringsfaktor.
- Trinn 3: Fordeler energiforbruket per år på ulike energibærere.
- Trinn 4: Beregner etterspurt mengde drivstoff (MJ for elektrisitet) i markedet per energibærer.
- Trinn 5: Beregne totale drivstoffkostnader per seilingstime.

I det påfølgende vil vi gå gjennom trinnene, samt hvilke kilder og input som inngår i de enkelte trinnene.


Trinn 1: Beregner energibehovet for en gitt fartøystype, lengdegruppe og rute
---------------------------------------------------------------------------------
Her beregner vi energibehovet i megajoule (MJ) per seilingstime direkte ved hjelp av ligningen nedenfor. Dette er en
forenkling av tidligere benyttet metode, som beregnet energibehovet via drivstoffbehovet, under en antakelse om at alle
skip i dag benytter MGO/HFO.

:math:`\\frac{Energiforbruk}{seilingstime}=1,1*3,6*Motorstørrelse[kW]*(\\frac{obs hastighet}{servicehastighet})^3*k`

I formelen over er:

- Lastfaktor ∈[0.2,0.9]
- r  settes til 0,9
- k=1+z(hs, l, b) ∈[1,2] er en korreksjonsfaktor for fartstap i bølger
- 1,1 representerer en korreksjonsfaktor for hjelpemotor
- 3,6 representerer konvertering fra kW til MJ

Dette gir oss energiforbruk per seilingstime totalt. Denne størrelsen er uavhengig av drivstofftype.

**Lastfaktor**

Lastfaktoren er en korreksjonsfaktor som korrigerer for at servicehastigheten normalt tilsvarer 70-80 prosent av
maksimal motoreffekt. Uten denne korreksjonsfaktoren ville vi antatt at servicehastighet tilsvarer 100 prosent
motoreffekt, men et skip skal kunne holde servicehastigheten uten å måtte kjøre på 100 prosent motorbelastning.
*k* er en korreksjonsfaktor for fartstap i bølger. Korreksjonsfaktoren avhenger blant annet av skipenes blokkoeffisient.
I Kystverkets veileder er det fylt ut antagelser om blokkoeffisienter for ulike skipstyper og lengdegrupper.
Det manglet imidlertid informasjon for enkelte skipstypene. For å håndtere dette, ble de resterende blokkoeffisientene
hentet inn basert på evaluering av skip fra de ulike kategoriene på
Sea-web: https://intranet.dnvgl.com/customersandservices/Pages/market-intelligence-databases.aspx,
samt validert mot statistikken i boken Leander (2012). Valideringen viste god overenstemmelse.

Trinn 2: Fremskrive energiforbruk til 2050 ved hjelp av effektiviseringsfaktor
---------------------------------------------------------------------------------
Med utgangspunkt i effektiviseringsfaktorer dokumentert i DNV GL (2020) antar vi at alle skipstyper og lengdegrupper er
20 prosent mer energieffektive i 2050. Effektiviseringsfaktoren implementeres lineært over perioden. Dette gir
energibehovet som brukes til fremdrift, propulsjonseffekten, for hvert år i det relevante tidsrommet.

**Energieffektivitet (reduksjon frem til 2050 i drivstofforbruk tonn per time)**

Her er det tatt utgangspunkt i rapporten «Maritime Forecast to 2050 – Energy Transition Outlook 2018» av DNV GL (2018a). I
denne rapporten er det gjort beregninger av energieffektivitet frem mot 2050 både med og uten fartsreduksjon. Som input
i matrisen er det brukt uten fartsreduksjon da slik fartsreduksjon blir hensyntatt andre steder i modellen. Antagelsen
basert på beregningene gjort av teamet bak denne rapporten er en forbedring av energieffektivitet på 20 prosent. Dette
kan variere fra skipstype til skipstype, men det finnes ikke tilstrekkelig grunnlag for å differensiere for det i 2050
per dags dato.

Trinn 3: Fordele energiforbruket per år på ulike energibærere
---------------------------------------------------------------------------------
Det forventes en vridning fra MGO og HFO over til andre energibærere over tid. Her legges et sett med forutsetninger om
drivstoffsammensetning i 2050 til grunn (DNV GL, 2020). Vridningen implementeres lineært over perioden.

**Andelen skip som bruker ulike typer drivstoff**

For 2018 er det antatt at alle skipstyper bruker MGO og HFO. Da andelen skip som bruker andre typer drivstoff i 2018 er
så liten som den er, så er det vurdert at det er neglisjerbart i denne sammenhengen.  Det er gjort en vurdering av at de
skipene som opererer i «deep sea»-segmentet vil ha så liten påvirkning at det er neglisjerbart i denne sammenhengen, da
estimert energimix for «deep sea» i 2050 er veldig likt «short sea». Derfor er fordelingen for 2050 anslått av
«Maritime Forecast to 2050 – Energy Transition Outlook 2018» av DNV GL  for «Shipping energy mix 2050, short sea». Det
er videre antatt i grunnlaget for de samfunnsøkonomiske analysene at fordelingen av ulike typer drivstoff blir likt
fordelt over alle skipstyper. Beregning av forbruket av ulike drivstoff er basert på omregning fra tradisjonelt
drivstoff, hensyntatt energitetthet i drivstoffet og virkningsgrad i energiproduksjonen.

Trinn 4: Beregner etterspurt mengde drivstoff i markedet per energibærer
---------------------------------------------------------------------------------
Neste steg er å beregne etterspurt mengde drivstoff i markedet per energibærer (MJ for skip som går på elektrisitet).
Energitetthet og virkningsgrad i formelen er drivstoffspesifikke og presenteres nærmere nedenfor.

:math:`SFOC=drivstofforbruk[\\frac{tonn}{seilingstime}]=\\frac{Energibruk}{(energitetthet[MJ/tonn]*virkningsgrad)}`

I formelen over er:

- Energitetthet = (Nedre brennverdi) er en fysisk størrelse (se tabell under)
- Virkningsgrad = er satt av alder/størrelse på fartøy (se tabeller under)

**Drivstoffavhengige virkningsgrader og energitetthet**

Drivstofforbruket, for skip som går på MGO og HFO, til de forskjellige skipstypene og størrelsene er hentet fra tabell
2-3 i rapporten: «Environmental Accounting System For Ships Based on AIS Ship Movement Tracking» produsert av
DNV GL på vegne av Kystverket i 2008. Denne tabellen viser spesifikt drivstofforbruk på hovedmotor for skip grovt delt
inn i motorstørrelse og alder. Tabellen er basert på antagelsen om at alle «slow speed» og «medium speed» motorer
konsumerer «residual» drivstoff. Videre er det antatt at alle «high speed» motorer konsumerer «destillater».En
underliggende tabell, som er brukt som input i beregningene til tabell 2-3 viser prosentvis fordeling av «high»,
«medium» og «slow speed» motorer for forskjellige skipstyper og størrelser. Denne fordelingen er gjort basert på en
analyse av 48 790 skip i Lloyds Fairplay i 2008.  Fordelingen av «high», «medium» og «slow speed» i dagens skipsflåte
kan være annerledes enn i 2008, noe som vil påvirke drivstofforbruket presentert i tabellen, men det er ansett at
tilnærmingen er tilstrekkelig representativ for dette formålet. Tabellen nedenfor viser energitettheten oppgitt i
gigajoule per tonn drivstoff.

**Tabell 1: Energitetthet gigajoule per tonn drivstoff**

+--------------------------+-----------------+
| Drivstofftype            | Energitetthet   |
+==========================+=================+
| MGO og HFO               | 43 GJ/tonn      |
+--------------------------+-----------------+
| LNG og LBG               | 59 GJ/tonn      |
+--------------------------+-----------------+
| Hydrogen                 | 120 GJ/tonn     |
+--------------------------+-----------------+
| Biodiesel                | 35 GJ/tonn      |
+--------------------------+-----------------+
| Karbonnøytrale drivstoff | 81,75 GJ/tonn   |
+--------------------------+-----------------+

**Tabell 2: Virkningsgrader for MGO og HFO**

+-------------------+--------------+--------------+--------------+
| Alder fartøy (år) | >5000kW      | 5000-15000kW | >15000Kw     |
+===================+==============+==============+==============+
| <1984             | 0,37         | 0,39         | 0,41         |
+-------------------+--------------+--------------+--------------+
| 1984-2000         | 0,41         | 0,43         | 0,45         |
+-------------------+--------------+--------------+--------------+
| >2000             | 0,43         | 0,45         | 0,48         |
+-------------------+--------------+--------------+--------------+

*Energitetthet olje: 43 [GJ/tonn] eller 11900 [kwh/tonn]*

**Tabell 3: Virkningsgrader LNG og LBG**

+-------------------+--------------+--------------+--------------+
| Alder fartøy (år) | >5000kW      | 5000-15000kW | >15000Kw     |
+===================+==============+==============+==============+
| >2000             | 0,42         | 0,45         | 0,47         |
+-------------------+--------------+--------------+--------------+

*Energitetthet LNG: 49 [GJ/tonn] eller 13700 [kWh/tonn]*

**Tabell 4: Virkningsgrader hydrogen**

+-------------------+--------------+--------------+--------------+
| Alder fartøy (år) | >5000kW      | 5000-15000kW | >15000Kw     |
+===================+==============+==============+==============+
| >2020             | 0,5          | 0,5          | 0,5          |
+-------------------+--------------+--------------+--------------+

*Energitetthet Hydrogen: 120 [GJ/tonn] eller 33300 [kWh/tonn]*

**Tabell 5: Virkningsgrader elektrisk drift**

+-------------------+---------------------------+
| Alder fartøy (år) | Alle motorstørrelser      |
+===================+===========================+
| Alle skip         | 0,9                       |
+-------------------+---------------------------+


Trinn 5: Beregne drivstoffkostnader per seilingstime
---------------------------------------------------------------------------------

Drivstoffkostnader per seilingstime per drivstofftype beregnes ved å multiplisere sammen drivstofforbruket per
drivstofftype med de respektive prisene på drivstoff. Til slutt beregner vi totale drivstoffkostnader per seilingstime
ved å summere på tvers av drivstofftypene. Det vi da sitter igjen med er drivstoffkostnader per seilingstime for hver
skipstype, lengdegruppe og år. Ved variasjon i bølgeforhold vil disse også være lokasjonsspesifikke.

**Geografisk bunkring**

Ettersom drivstoffpriser varierer mellom ulike deler av Norge, og mellom ulike land har vi foretatt antagelser på hvor
skipene i de ulike områdene bunkrer. For geografisk bunkring er det antatt at alle skip alltid vil fylle så langt sør
de kan, basert på antagelsen om at prisene er lavere jo lengre sør man fyller. Det er lagt til grunn at alternativene
er å fylle i følgende områder:

- Geografisk område nord for Trondheim – bunkring i Tromsø benyttes som grunnlag.
- Geografisk område sør for Trondheim – bunkring i Bergen benyttes som grunnlag.

Internasjonalt område:
Rotterdam er brukt som grunnlag. Følgende er antatt for bunkringsstrategi:

    - Skipsstørrelse 0-100 meter: Det er lagt til grunn en antagelse om et operasjonsmønster som tilsier at alle skip under 100 meter fyller i regionen de operer.
    - Skipsstørrelse 100-150 meter: Det er antatt et operasjonsmønster som innebærer at 30 % fyller sør for Bergen, mens de resterende 70 % fyller internasjonalt. Ingen skip fyller i nord. Unntakene er: Offshore supplyskip, Andre offshorefartøy, Brønnbåt, Slepefartøy, Andre servicefartøy og Fiskefartøy. Alle disse skipene antas å fylle 100 % innenfor sin egen region.
    - Skipsstørrelse >150 meter: Det antas at alle skip over 150 meter fyller internasjonalt. Unntakene er: Offshore supplyskip, Andre offshorefartøy, Brønnbåt, Slepefartøy, Andre servicefartøy og Fiskefartøy Alle disse skipene antas å fylle 100 % innenfor sin egen region.

**Drivstoffpriser for ulike energibærere**

Det er store usikkerheter knyttet til drivstoffpriser, både markedsmessig, og som følge av reguleringer og andre
tiltak. Dette kan føre til store og uforutsigbare endringer som gjør at det ikke er vurdert som hensiktsmessig og anta
prisutvikling frem mot 2050. Det er derfor lagt til grunn at historiske priser benyttes uendret for hele
analyseperioden, bortsett fra for hydrogen, se nedenfor. Verdikjedetapet fra produksjon av de forskjellige drivstoffene
er ikke hensyntatt. Valutainformasjon brukt i konverteringen fra USD til NOK er hentet fra Norges Bank.
Konsumprisindeksen er hentet fra SSB.

MGO og HFO:

- Bergen: MGO og HFO. Det er tatt gjennomsnittpris per måned fra april 2008 til oktober 2018 fra bunkerindex.com. Månedlig gjennomsnitt av NOK per USD er brukt i de respektive månedene for å finne pris i NOK per tonn i alle måneder. Deretter er det brukt en deflator beregnet fra konsumprisindeksen fra SSB for å få alle prisene i 2020 kroner. Tilslutt er det tatt gjennomsnitt av alle månedene. Merk at i Bergen er kun MGO brukt da HFO ikke er tilgjengelig.
- Tromsø: MGO og HFO. Det er tatt gjennomsnittpris per måned fra mai 2010 til oktober 2018 fra bunkerindex.com. Månedlig gjennomsnitt av NOK per USD er brukt i de respektive månedene for å finne pris i NOK per tonn i alle måneder. Deretter er det brukt en deflator beregnet fra konsumprisindeksen fra SSB for å få alle prisene i 2020 kroner. Tilslutt er det tatt gjennomsnitt av alle månedene. Merk at i Tromsø er kun MGO brukt da HFO ikke er tilgjengelig.
- Rotterdam: MGO og HFO. Det er tatt gjennomsnittpris per måned fra snitt fra april 2008 til oktober 2018 fra bunkerindex.com. Dette er gjort for MGO, IFO180 og IFO380.  Månedlig gjennomsnitt av NOK per USD er brukt i de respektive månedene for å finne pris i NOK per tonn i alle måneder. Deretter er gjennomsnittsprisen regnet ut per bunkerstype. Deretter er det brukt en deflator beregnet fra konsumprisindeksen fra SSB for å få alle prisene i 2020 kroner. Til slutt er gjennomsnittet av MGO, IFO180 og IFO380 beregnet.

LNG:

- LNG pris hentet fra rapporten «Kartlegging av Utslippskutt i Maritim Næring – Analyse av klimagassutslipp fra innenriks skipstrafikk» utarbeidet av DNV GL (2018b). Pris på LNG estimert i rapporten er antatt å være pris i Bergen. Videre er det antatt 5 prosent billigere i Rotterdam og 5 prosent dyrere i Tromsø, på grunn av ulike transportkostnader. Prisen på LNG antas konstant i perioden 2018-2030 i DNV GL (2018b). I input til matrisen blir det videre gjort en antagelse om at prisen holdes konstant til 2050.

Karbonnøytrale:

- Priser for karbonnøytralt drivstoff er basert på en antagelse om at drivstoffmiksen vil være 50 prosent hydrogen, 25 prosent LBG og 25 prosent biodiesel. Prisene er hentet fra DNV GL (2018b). Med referanse til samme rapport, er det kun hydrogen som antas å variere i pris fra 2018 til 2050.

Elektrisitet:

- Pris er hentet fra DNV GL (2018b).

Representative distanseavhengige kostnader
---------------------------------------------------------------------------------
For å estimere representative distanseavhengige kostander i de strekningsvise analysene tar modellen utgangspunkt i
funksjonene over, og beregner drivstofforbruk for alle unike skip som har passert gjennom området i perioden.
I beregningen av drivstofforbruk brukes informasjon om alder, motorstørrelse og servicehastighet for et representativt
skip for hver kombinasjon av skipstype og lengdegruppe. Antall AIS-punkter per mmsi brukes som vekt for å beregne
nasjonale representative verdier for virkningsgrad, motorstørrelse og servicehastighet per skipstype og lengdegruppe.
Det betyr at dersom det for eksempel har passert et relativt stort skip innenfor en skipskategori og lengdegruppe kun
en gang i løpet av perioden, mens det ellers passerer mindre skip innen samme skipskategori, så vil verdiene for det
store skipet vektes ned i de gjennomsnittlige verdiene nasjonalt. Disse representative verdiene brukes i neste omgang t
il å beregne drivstofforbruk per skip for strekningen.


============================================
Virkningsklassen Distanseavhengige kostnader
============================================
"""


from typing import List, Callable

import numpy as np
import pandera as pa
import pandas as pd
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
    TrafikkGrunnlagSchema,
    TidsbrukPerPassSchema,
)
from fram.virkninger.drivstoff import hjelpemoduler
from fram.virkninger.drivstoff.schemas import HastighetsSchema
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.virkning import Virkning
from fram.virkninger.drivstoff.hjelpemodul_drivstofforbruk import beregn_drivstofforbruk_i_tonn, \
    get_kr_per_enhet_drivstoff

VIRKNINGSNAVN = "Endring i distanseavhengige kostnader"


class Drivstoff(Virkning):
    def __init__(
        self,
        beregningsaar: List[int],
        tankested: List[str],
        kroneaar: int,
        logger: Callable = print,
    ):

        """
        Klasse for beregning av distanseavhengige kostnader. Beregningen er i stor grad basert på metodikk i
        Kystverkets veileder i samfunnsøkonomiske analyser.

        Virkningen forutsetter at du har beregnet tidsbruk og hastighet per passering for ulike skipstyper og
        lengdegrupper på rett format gruppert etter skipstype og
        lengdegruppe. I tillegg har virkningen behov for at man har identifisert total trafikk (antall passeringer)
        for både tiltaksbanen og referansebanen.
        Virkningen vil selv benytte nasjonale kalkulasjonspriser for verdsettelse.

        Args:
            beregningsaar: liste over de årene du vil ha beregnet virkningen for
            tankested: Liste over tankersted for tanking nasjonalt. Tar enten verdien "nord" eller "sør". Definert som nord eller sør for Trondheim. Modellen beregner selv internasjonale priser for tanking internasjonalt basert på forhåndbestemte antagelser.
            kroneaar: Kroneåret du vil ha for de kalkprisene virkningen beregner selv
            logger: Hvor du vil at virkningen skal logge til. Defaulter til 'print'

        """

        self.logger = logger
        self.logger("Setter opp virkning")
        self.beregningsaar = beregningsaar
        self.tankested = tankested
        self._verdsatt_drivstoffkostnad_ref = None
        self._verdsatt_drivstoffkostnad_tiltak = None
        self._verdsatt_drivstoffkostnad_netto = None
        self._volumvirkning_ref = []
        self._volumvirkning_tiltak = []
        self.kroneaar = kroneaar

    @verbose_schema_error
    @pa.check_types(lazy=True)
    def beregn(
        self,
        tidsbruk_per_passering_ref: DataFrame[TidsbrukPerPassSchema],
        tidsbruk_per_passering_tiltak: DataFrame[TidsbrukPerPassSchema],
        hastighet_per_passering_ref: DataFrame[HastighetsSchema],
        hastighet_per_passering_tiltak: DataFrame[HastighetsSchema],
        trafikk_ref: DataFrame[TrafikkGrunnlagSchema],
        trafikk_tiltak: DataFrame[TrafikkGrunnlagSchema],
    ):
        """
        Beregner drivstofforbruket og verdsetter dette forbruket.

        Krever som input at du har en dataframe med seilingstid og hastighet i referansebanen. Du må også ha en
        tilsvarende dataframe for tiltaksbanen. Stegene i beregn-funksjonen er som følger:

        1. Trinn 1: Beregner energibehovet til fremdrift, propulsjonseffekten, for en gitt fartøystype og størrelse
        2. Trinn 2: Fremskriver energibehovet til 2050 ved hjelp av effektiviseringsfaktor
        3. Trinn 3: Fordeler energiforbruket per år på ulike energibærere
        4. Trinn 4: Beregner etterspurt mengde drivstoff (MJ for elektrisitet) i markedet per energibærer
        5. Trinn 5: Beregne totale drivstoffkostnader per seilingstime

        Verdier vil være tilgjengelige på `.volumvirkning_ref`, `.volumsvirkning_tiltak`, `.verdsatt_brutto_ref`,
        `.verdsatt_brutto_tiltak` og `.verdsatt_netto`.

        Args:
            tidsbruk_per_passering_ref: Tidsbruk per passering i referansebanen. Påkrevd.
            tidsbruk_per_passering_tiltak: Gyldig dataframe med tidsbruk per passering i tiltaksbanen. Påkrevd.
            hastighet_per_passering_ref:  Gyldig dataframe med hastighet i referansebanen. Påkrevd.
            hastighet_per_passering_tiltak:  Gyldig dataframe med hastighet i tiltaksbanen. Påkrevd.
            trafikk_ref: Gyldig dataframe med trafikk i referansebanen. Påkrevd.
            trafikk_tiltak:  Gyldig dataframe med trafikk i tiltaksbanen. Påkrevd.

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

        drivstofforbruk_per_time_ref = beregn_drivstofforbruk_i_tonn(hastighet_per_passering_ref, self.beregningsaar, logger=self.logger)
        drivstofforbruk_per_time_tiltak = beregn_drivstofforbruk_i_tonn(hastighet_per_passering_tiltak, self.beregningsaar, logger=self.logger)

        ettersp_drivstoff_per_time_ref = hjelpemoduler.beregn_drivstofforbruk_per_time(
            self.beregningsaar, drivstofforbruk_per_type_time=drivstofforbruk_per_time_ref
        )
        ettersp_drivstoff_per_time_tiltak = hjelpemoduler.beregn_drivstofforbruk_per_time(
            self.beregningsaar, drivstofforbruk_per_type_time=drivstofforbruk_per_time_tiltak
        )

        (
            _verdsatt_drivstoffkostnad_ref,
            _verdsatt_drivstoffkostnad_tiltak,
        ) = hjelpemoduler.verdsett_drivstoff(
            tid_ref=total_tidsbruk_ref,
            tid_tiltak=total_tidsbruk_tiltak,
            hastighet_ref=hastighet_per_passering_ref,
            hastighet_tiltak=hastighet_per_passering_tiltak,
            beregningsaar=self.beregningsaar,
            kroneaar=self.kroneaar,
            tankested=self.tankested,
            drivstoff_per_time_ref=ettersp_drivstoff_per_time_ref,
            drivstoff_per_time_tiltak=ettersp_drivstoff_per_time_tiltak,
        )

        self._verdsatt_drivstoffkostnad_ref = (
            _verdsatt_drivstoffkostnad_ref.assign(Virkningsnavn=VIRKNINGSNAVN)
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0.0)
            .set_index(VERDSATT_COLS)[self.beregningsaar]
            .multiply(-1)
        )
        self._verdsatt_drivstoffkostnad_tiltak = (
            _verdsatt_drivstoffkostnad_tiltak.assign(Virkningsnavn=VIRKNINGSNAVN)
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0.0)
            .set_index(VERDSATT_COLS)[self.beregningsaar]
            .multiply(-1)
        )

        self._verdsatt_drivstoffkostnad_netto = (
            self._verdsatt_drivstoffkostnad_ref.subtract(
                self._verdsatt_drivstoffkostnad_tiltak, fill_value=0
            )
        )

        antall_beregningsaar = len(self.beregningsaar)
        self._volum_ref = (
            hastighet_per_passering_ref.reset_index()
            .pipe(
                _legg_til_kolonne,
                self.beregningsaar,
                lambda df: np.repeat(
                    df["Hastighet"].astype(float).values[:, np.newaxis],
                    antall_beregningsaar,
                    axis=1,
                ),
            )
            .pipe(
                _legg_til_kolonne,
                KOLONNENAVN_VOLUMVIRKNING,
                "Gjennomsnittlig hastighet",
            )
            .pipe(_legg_til_kolonne, KOLONNENAVN_VOLUM_MAALEENHET, "Knop")
            .pipe(_legg_til_kolonne, FOLSOMHET_KOLONNE, "Alle")
            .set_index(VOLUM_COLS)[self.beregningsaar]
        )
        self._volum_tiltak = (
            hastighet_per_passering_tiltak.reset_index()
            .pipe(
                _legg_til_kolonne,
                self.beregningsaar,
                lambda df: np.repeat(
                    df["Hastighet"].astype(float).values[:, np.newaxis],
                    antall_beregningsaar,
                    axis=1,
                ),
            )
            .pipe(
                _legg_til_kolonne,
                KOLONNENAVN_VOLUMVIRKNING,
                "Gjennomsnittlig hastighet",
            )
            .pipe(_legg_til_kolonne, KOLONNENAVN_VOLUM_MAALEENHET, "Knop")
            .pipe(_legg_til_kolonne, FOLSOMHET_KOLONNE, "Alle")
            .set_index(VOLUM_COLS)[self.beregningsaar]
        )

        total_tidsbruk_ref_temp = (total_tidsbruk_ref.multiply(drivstofforbruk_per_time_ref.set_index(["Skipstype","Lengdegruppe","Drivstofftype","Rute"]),fill_value=0,)
                                .reset_index()
                                .dropna(how="any")
                                .assign(
                                        Virkningsnavn=lambda df: "Drivstofforbruk - " + df.Drivstofftype,
                                        Måleenhet=lambda df: df.Drivstofftype.map(
                                            {
                                                "Elektrisitet": "MJ",
                                                "Karbonnøytrale drivstoff": "Tonn",
                                                "LNG": "Tonn",
                                                "MGO og HFO": "Tonn",
                                            }
                                        ),)
                                .drop("Drivstofftype",axis=1)
                                .set_index(VOLUM_COLS)
                                )


        self._volum_ref = pd.concat((self._volum_ref, total_tidsbruk_ref_temp), axis=0)


        total_tidsbruk_tiltak_temp = (total_tidsbruk_tiltak.multiply(drivstofforbruk_per_time_tiltak.set_index(["Skipstype","Lengdegruppe","Drivstofftype","Rute"]),fill_value=0,)
                                    .reset_index()
                                    .dropna(how="any")
                                    .assign(
                                        Virkningsnavn=lambda df: "Drivstofforbruk - " + df.Drivstofftype,
                                        Måleenhet=lambda df: df.Drivstofftype.map(
                                            {
                                                "Elektrisitet": "MJ",
                                                "Karbonnøytrale drivstoff": "Tonn",
                                                "LNG": "Tonn",
                                                "MGO og HFO": "Tonn",
                                            }
                                        ),)
                                    .drop("Drivstofftype", axis=1)
                                    .set_index(VOLUM_COLS)
                                    )
                                    
        self._volum_tiltak = pd.concat((self._volum_tiltak, total_tidsbruk_tiltak_temp), axis=0)

    def _get_verdsatt_brutto_ref(self):
        return self._verdsatt_drivstoffkostnad_ref

    def _get_verdsatt_brutto_tiltak(self):
        return self._verdsatt_drivstoffkostnad_tiltak

    def _get_volum_ref(self):
        return self._volum_ref

    def _get_volum_tiltak(self):
        return self._volum_tiltak

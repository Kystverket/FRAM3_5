"""
============================================
Ventetidskostnader
============================================


Enkelte steder kan kapasitetsbegrensninger føre til ventetid. Dette gjelder særlig ved for lav havnekapasitet eller
smale og lite fremkommelige farleder. Modellen inneholder en modul for beregning av redusert ventetid ved
kapasitetsøkninger. Modellen antar at skip anløper uniformt over et tidsintervall, og fremskriver kødannelse og
ventetid over hele analyseperioden basert på angitte anløpsfrekvenser. Dersom sesong- og tidsvariasjoner er viktig,
kan det defineres anløpsfrekvenser som er sesong- og tidspunktsavhengige, for eksempel «sommermorgen» og «vinternatt».
Modellen håndterer også at skip i mange tilfeller anløper en trang farled fra to ulike sider, og at ventetiden dermed
avhenger av retningen på skipet som kom før deg; man kan som hovedregel seile tettere på forrige skip dersom dette
seilte i samme retning som deg. Rent modellteknisk er dette en køprosess med følgende egenskaper:

- Det antas at alle skipstyper og lengdegrupper anløper i henhold til en Poisson-prosess der den skipsspesifikke anløpsraten kan gjøres avhengig av år, årstid, tid på døgnet og anløpsretning
- Det kan spesifiseres opptil flere flaskehalser (kaiavsnitt, farleder) som hver kan ha sin egen behandlingskapasitet (lossetid, gjennomseilingstid)
- Hver flaskehals kan kun håndtere ett skip av gangen
- Skip danner kø (på hver side av flaskehalsen hvis det angis to anløpsretninger) og betjenes etter førstemann til mølla-prinsippet
- Det er ingen begrensninger på lengden på køen, ingen skip blir avvist
- Kømodellen kjøres for hver spesifisert periode (kombinasjon av år, årstid og tid på døgnet) og beregner gjennomsnittlig ventetid i en stabil likevekt for et slikt system for hver periode, og så aggregert til hvert år.
- Selve algoritmen for beregning av kø og ventetid er beskrevet inngående under klassen, se :py:meth:`~fram.virkninger.ventetid.virkning.Ventetid.beregn`

Selve ventetiden verdsettes på samme måte som de tidsavhengige kostnadene, som angitt i :py:.*?:`~fram.virkninger.tid.virkning`


============================================
Virkningsklassen Ventetid
============================================

"""
from copy import copy
from typing import List, Callable, Dict, Optional

import pandas as pd
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.hjelpefunksjoner import _legg_til_kolonne
from fram.generelle_hjelpemoduler.konstanter import FOLSOMHET_KOLONNE, FOLSOMHET_COLS
from fram.generelle_hjelpemoduler.schemas import (
    TrafikkGrunnlagSchema,
    VerdsattSchema,
    VolumSchema,
)
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.tid.schemas import KalkprisTidSchema
from fram.virkninger.ventetid.hjelpemoduler import (
    _verdsett_ventetid,
    _fordel_og_prep_ventetid,
    SimuleringsInput,
)
from fram.virkninger.ventetid.ventetidssituasjon import Ventetidssituasjon
from fram.virkninger.virkning import Virkning


class Ventetid(Virkning):
    def __init__(
        self,
        kalkpris_tid: DataFrame[KalkprisTidSchema],
        trafikk_ref: DataFrame[TrafikkGrunnlagSchema],
        trafikk_tiltak: DataFrame[TrafikkGrunnlagSchema],
        beregningsaar: List[int],
        logger: Callable = print,
    ):

        """
        Virkningsklasse for å beregne kødannelse og ventetider i referanse- og tiltaksbanen.

        Virkningen kan kun settes opp ved hjelp av ferdiggenerert input, i form av en gyldig :class:`~fram.virkninger.ventetid.hjelpemoduler.SimuleringsInput`. Denne kan enten settes opp manuelt eller genereres fra en gyldig Excel-input ved hjelp av funksjonsn :meth:`~fram.virkninger.ventetid.excel.les_ventetidsinput_fra_excel`

        Som beregningsbeholder benyttes klassen :class:`~fram.virkninger.ventetid.ventetidssituasjon.Ventetidssituasjon`. Beregningsmodellen som benyttes er :meth:`~fram.virkninger.ventetid.computation.simulate_multiship_multiple_bottlenecks_two_directions`.

        Fordi hver tiltakspakke kan inneholde flere ventetidssituasjoner, må `beregn`-metoden kalles én gang per ventetidssituasjon. Output akkumuleres i standardvariablene for volumvirkninger og verdsatte virkninger. I tillegg akkumuleres ventetidssituasjonene i en dictionary på `Ventetid._ventetidssituasjoner`, der nøklene ruter og verdiene er objekter av klassen :class:`~fram.virkninger.ventetid.ventetidssituasjon.Ventetidssituasjon`. Det kan altså kun være én ventetidssituasjon per rute.

        Selve beregningen foretas ved :meth:`Ventetid.beregn`

        Args:
            kalkpris_tid: Gyldig kalkulasjonspris for tidkostnader, kroner per time
            trafikk_ref: Gyldig trafikkgrunnlag i referansebanen, som brukes for å fordele skip i øvrig-kategorien utover skipsmatrisen
            trafikk_tiltak: Gyldig trafikkgrunnlag i tiltaksbanen, som brukes for å fordele skip i øvrig-kategorien utover skipsmatrisen
            beregningsaar: Liste over de årene du vil ha beregnet virkningen for
            logger: Hvor det logges til
        """
        self.logger = logger
        self.logger("Setter opp virkning")
        KalkprisTidSchema.validate(kalkpris_tid)
        TrafikkGrunnlagSchema.validate(trafikk_ref)
        TrafikkGrunnlagSchema.validate(trafikk_tiltak)
        self.kalkpris_tid = kalkpris_tid
        self.trafikk_ref = trafikk_ref
        self.trafikk_tiltak = trafikk_tiltak
        self.beregningsaar = beregningsaar

        self._brutto_ventetid_ref: List[DataFrame[VolumSchema]] = []
        self._brutto_ventetid_tiltak: List[DataFrame[VolumSchema]] = []

        self._verdsatt_brutto_ref: List[DataFrame[VerdsattSchema]] = []
        self._verdsatt_brutto_tiltak: List[DataFrame[VerdsattSchema]] = []

        self._ventetidssituasjoner: Dict[str, Ventetidssituasjon] = {}

    @verbose_schema_error
    def beregn(
        self,
        simuleringsinput_ref: SimuleringsInput,
        metadatakolonner,
        simuleringsinput_tiltak: Optional[SimuleringsInput] = None,
        seed: int = 1,
    ):
        """
        Metode for å kjøre selve ventetidsberegninger.

        Samlet ventetid i referanse- og tiltaksbanen lagres til `Ventetid.volumvirkning_ref` og `Ventetid.volumvirkning_tiltak`.
        Verdsatt ventetid, både brutto i referanse, og tiltaksbanen, og netto, lagres til henholdsvis `Ventetid.verdsatt_brutto_ref`,
        `Ventetid.verdsatt_brutto_tiltak` og `Ventetid.verdsatt_netto`

        I tillegg til den rene ventetidsberegningen, fordeles også ventetiden utover de skipstyper man har angitt at
        ligger i kategorien "Øvrige fartøy" med lengedegruppen "Alle". Her fordeles samlet ventetid for denne gruppen
        utover de ulike skipstypene man har angitt at faller i denne kategorien, proporsjonalt med antall passeringer
        disse skipene har på ruten ventetidsområdet ligger i, i trafikkgrunnlaget.

        Fordi ventetidsberegningene kan ta flere minutter, mellomlagrer modellen alle beregninger basert på imputen
        den gis, hvilken seed som settes og antall perioder som simuleres. Det vil si at så lenge disse tre beholdes
        uendret, vil modellen bare slå opp i en katalog over ferdigberegnede kjøringer og returnere denne.
        En fordel ved dette er at ventetidsberegningene kan kjøres uavhengig av selve modellkjøringen, og ved kjøring
        slås det bare opp i ferdigkjørte ventetidsberegninger. For å beregne ventetid behøves ventetidsarket og
        fremskrevet trafikk. Følgende tre modellkall er derfor nok til at ventetidsberegningene er unnagjort, inkludert verdsetting:
        Først `FRAM()`, så `FRAM.fremskriv_trafikk()` og til sist `FRAM.beregn_ventetid()`.

        Algoritmen er basert på Queue departure computation (Ebert & al., 2017), som finnes her: https://arxiv.org/abs/1703.02151

        1. Det trekkes en lang vektor med tilfeldig tid mellom hvert anløp, `interarrival_times`, simulert for hver skipstype, basert på deres lambda (som angir forventet antall anløp per tidsenhet for den enkelte skipstype)
        2. Vi regner ut anløpstidene som den kumulative summen av tid mellom hvert anløp, `arrival_times`
        3. Dette settes sammen til en dataframe, som så stables oppå hverandre for alle skipstyper og lengdegrupper, til en kjempelang dataframe
        4. Denne sorteres deretter etter anløpstid, slik at alle skipene ligger kronologisk i den rekkefølgen de anløper, med tilhørende anløpstid
        5. Vi klipper denne nedenfra slik at de skipene, som et resultat av den tilfeldige simuleringen, anløper etter simuleringsperioden (for eksempel 10 000 dager), klippes vekk. Vi står da igjen med alle de skipene som anløper innenfor simuleringsperioden.
        6. Vi trekker gjennomseilingstid, `service_times` for hvert skip, basert på de angitte myene (enten lik for alle skip, skipsavhengig eller skips- og flaskehalsavhengig). `mu` angir forventet antall skip som kan håndteres av flaskehalsen per tidsperiode.
        7. For at det skal gå raskere å gjennomføre køsimuleringen, setter vi opp en rekke tomme vektorer med riktig lengde. Da holder datamaskinen av minne til å fylle disse raskt med innhold etterpå. I tilfellet flere skip, flere flaskehalser og mulig rabatt ved å seile etter hverandre i samme retning, gjelder dette `service_start_times`, `service_times`, `completion_times`, `bottleneck_chosen`, `bottleneck_busy_until` og `last_ship_direction`.
        8. Vi looper over hver anløp og beregner ventetid. Dette gjøres på følgende måte:
            a. Et skip som anløper, velger den flaskehalsen (hvis flere) som har en gjennomseilingstid slik at skipet først blir ferdig. Det kan være den med kortest gjennomseilingstid hvis ingen kø, eller en med lengre gjennomseilingstid hvis køen der er tilstrekkelig kort til at det er bedre å seile lenger for å slippe å vente, eller dersom det kan seile tett på skipet foran seg der, men må vente på et skip i motgående retning et annet sted. Valgt flaskehals omtales som `bottleneck_chosen`.
            b. Skipets `service_start_time` blir da det tidspunktet det kan begynne å seile gjennom flaskehalsen. Det er det tidspunktet som kommer sist i tid av 1) når skipet kommer til ventestedet, og 2) når flaskehalsen blir ledig
            c. Den valgte flaskehalsen blir da opptatt til skipet har seilt gjennom, potensielt korrigert for at neste skip kan seile før du er helt gjennom, dersom dette kommer i samme retning. Dette betegnes som `bottleneck_busy_until`, og er det som bestemmer om det oppstår kø: Dersom `bottleneck_busy_until` er senere enn anløpstidspunktet til det neste skipet, må det neste skipet vente. Når mange skip kommer tett etter hverandre, vil det hope seg opp kø, og det er lenge til flaskehalsen blir ledig.
            d. Skipet er ferdig behandlet når det har seilt gjennom flaskehalsen. Lagres som `completion_times`.
            e. Total tid for skipet gjennom ventetidsområdet (`total_times`) blir da `completion_times` minus `arrival_times`, mens ventetiden blir total tid fratrukket gjennomseilingstiden: `wait_times` = `total_times` - `service_times`.

    Denne algoritmen gjøres litt enklere dersom det bare er en skipstype, bare en flaskehals, bare en retning eller det ikke gis rabatt for å seile i samme retning. Grunnalgoritmen er likevel den samme.

    Args:
        simuleringsinput_ref: gyldig simuleringsinput
        simuleringsinput_tiltak: gyldig simuleringsinput
        metadatakolonner: Verdier til kolonnene Strekning, Tiltaksomraade, Tiltakspakke, Analyseomraade og Rute
        seed: Seed til psedutilfeldig tallgenerator for å sikre gjenskapbare simuleringer
        """
        for kjoring in simuleringsinput_ref.lambda_df.reset_index()[FOLSOMHET_KOLONNE].unique():
            s_ref = copy(simuleringsinput_ref)
            s_ref.lambda_df = s_ref.lambda_df.reset_index().loc[lambda df: df[FOLSOMHET_KOLONNE] == kjoring]
            s_tiltak = copy(simuleringsinput_tiltak)
            if simuleringsinput_tiltak is not None:
                s_tiltak.lambda_df = s_tiltak.lambda_df.reset_index().loc[lambda df: df[FOLSOMHET_KOLONNE] == kjoring]

            ventetidssit = Ventetidssituasjon(
                simuleringsinput_ref=s_ref,
                simuleringsinput_tiltak=s_tiltak,
                logger=self.logger,
                seed=seed,
            )
            self._ventetidssituasjoner[metadatakolonner.Rute.values[0]] = ventetidssit

            # Fordeler ventetid i øvrig-kategorien ut på skipsmatrisen i henhold til det relevante trafikkgrunnlaget
            tot_ventetid_tiltakspakke_ref = _fordel_og_prep_ventetid(
                trafikkgrunnlag=self.trafikk_ref.reset_index().loc[lambda df: df[FOLSOMHET_KOLONNE] == kjoring].set_index(FOLSOMHET_COLS),
                ovrig_kategori=s_ref.ovrig_kategori,
                total_ventetid=ventetidssit.total_ventetid_ref,
                beregningsaar=self.beregningsaar,
                metadatakolonner=metadatakolonner,
                logger=self.logger,
            )

            self._brutto_ventetid_ref.append(tot_ventetid_tiltakspakke_ref)
            # Verdsetter ventetiden
            self._verdsatt_brutto_ref.append(
                _verdsett_ventetid(
                    ventetid=tot_ventetid_tiltakspakke_ref,
                    kalkpris_ventetid=self.kalkpris_tid,
                    beregningsaar=self.beregningsaar,
                ).multiply(-1)
            )

            if simuleringsinput_tiltak is not None:
                # Fordeler ventetid i øvrig-kategorien ut på skipsmatrisen i henhold til det relevante trafikkgrunnlaget
                tot_ventetid_tiltakspakke_tiltak = _fordel_og_prep_ventetid(
                    trafikkgrunnlag=self.trafikk_tiltak.reset_index().loc[lambda df: df[FOLSOMHET_KOLONNE] == kjoring].set_index(FOLSOMHET_COLS),
                    ovrig_kategori=s_tiltak.ovrig_kategori,
                    total_ventetid=ventetidssit.total_ventetid_tiltak,
                    beregningsaar=self.beregningsaar,
                    metadatakolonner=metadatakolonner,
                    logger=self.logger,
                )#.pipe(_legg_til_kolonne, FOLSOMHET_KOLONNE, kjoring)
                self._brutto_ventetid_tiltak.append(tot_ventetid_tiltakspakke_tiltak)
                # Verdsetter ventetiden
                self._verdsatt_brutto_tiltak.append(
                    _verdsett_ventetid(
                        ventetid=tot_ventetid_tiltakspakke_tiltak,
                        kalkpris_ventetid=self.kalkpris_tid,
                        beregningsaar=self.beregningsaar,
                    ).multiply(-1)#.pipe(_legg_til_kolonne, FOLSOMHET_KOLONNE, kjoring)
                )

    def _get_verdsatt_brutto_ref(self):
        return pd.concat(self._verdsatt_brutto_ref, axis=0, sort=False)

    def _get_verdsatt_brutto_tiltak(self):
        if len(self._verdsatt_brutto_tiltak) == 0:
            return None
        return pd.concat(self._verdsatt_brutto_tiltak, axis=0, sort=False)

    def _get_volum_ref(self):
        return pd.concat(self._brutto_ventetid_ref, axis=0, sort=False)

    def _get_volum_tiltak(self):
        if len(self._brutto_ventetid_tiltak) == 0:
            return None
        return pd.concat(self._brutto_ventetid_tiltak, axis=0, sort=False)

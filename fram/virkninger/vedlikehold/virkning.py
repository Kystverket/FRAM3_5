from typing import Callable, List

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.hjelpefunksjoner import fyll_indeks, _legg_til_kolonne, legg_til_kolonne_hvis_mangler
from fram.generelle_hjelpemoduler.konstanter import (
    SKATTEFINANSIERINGSKOSTNAD,
    VERDSATT_COLS,
    FOLSOMHET_KOLONNE,
)
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.vedlikehold.hjelpemoduler import (
    vedlikeholdspriser_per_aar,
    verdsett_vedlikeholdskostnader,
)
from fram.virkninger.vedlikehold.schemas import (
    VedlikeholskostnaderSchema,
    OppgraderingskostnaderSchema,
    VedlikeholdsobjekterSchema,
)
from fram.virkninger.virkning import Virkning

"""
============================================
Vedlikeholdskostnader
============================================

Navigasjonsinnretninger (merker) forringes over tid, og det utføres periodiske tilsyn, reparasjoner og vedlikehold med
disse navigasjonsinnretningene ved behov. Hvis tiltaksalternativet innebærer installasjon og/eller endring av merker,
vil dette endre de utgifter til årlig tilsyn/inspeksjon, vedlikehold og fornying av navigasjonsmerkene.

I arbeidet med de samfunnsøkonomiske analysene har det fremkommet nye og oppdaterte estimater på vedlikeholdskostnader.
Anslagene som ligger til grunn er basert på kostnadsdata levert av Senter for farled, fyr og merker i Kystverket, og er
bearbeidet av DNV GL (2016) og Senter for transportplanlegging, plan og utredning i Kystverket. Kostnadene varierer
mellom ulike typer navigasjonsinnretninger, og er delt i årlige kostnader og oppgraderingskostnader som foretas innenfor
større tidsintervaller.

Når det gjelder oppgraderingskostnadene så er det lagt til grunn at det foretas oppgraderinger når innretningen har en
tilstandsgrad 2. Nye navigasjons-installasjoner har tilstandsgrad 0, og det tar mellom 10 til 20 år før tilstandsgraden
faller til tilstandsgrad 2. Når det gjennomføres oppgraderinger ved tilstandsgrad 2, vil navigasjonsinnretningen oppnå en
tilstandsgrad 1. Det vil ta mellom fem og ti år før navigasjonsinstallasjonen igjen har en tilstandsgrad 2. I modellen
har vi lagt til grunn at alle eksisterende navigasjonsinstallasjoner er halvveis i perioden mellom tilstandsgrad 1 og
tilstandsgrad 2.


============================================
Virkningsklassen Vedlikeholdskostnader
============================================


"""


class Vedlikeholdskostnader(Virkning):
    @verbose_schema_error
    def __init__(
        self,
        strekning: str,
        tiltakspakke: int,
        kostnader: DataFrame[VedlikeholskostnaderSchema] = None,
        oppgrad: DataFrame[OppgraderingskostnaderSchema] = None,
        beregningsaar: List[int] = None,
        ferdigstillelsesaar: int = None,
        sluttaar: int = None,
        tiltaksomraade: int = -1,
        logger: Callable = None,
    ):
        """
        Virkningsklasse for vedlikeholdskostnader.

        Beregner prisjusterte kostnader for periodiske oppgraderinger og vedlikehold av merker, spredt utover beregningsårene.
        Forutsetninger: Kalkulasjonspriser for hhv. vedlikehold og oppgradering, samt beregningsår.

        Vedlikeholdskostnader er løpende, årlige kostnader for hvert objekt.
        Oppgraderinger er periodiske kostnader, oppgitt som en endring mellom tilstandsgrader (TG0, TG1 eller TG2).
        TG0 representerer nye objekter, TG2 er objekter som behøver oppgradering, og TG1 er tidligere oppgraderte,
        funksjonelle objekter. Periodene mellom oppgraderinger kan være 5, 10, 15, eller 20 år.

        Objektene i begge DataFramene må være blant dem med oppgitte kalkulasjonspriser.

        Args:
            strekning: Strekningsnummer for den tilhørende analysen
            tiltakspakke: Tiltakspakken for den tilhørende analysen
            kostnader: Løpende, årlige vedlikeholdskostnader
            oppgrad: Oppgraderingskostnader og -perioder
            beregningsaar: Årene kostnader skal beregnes for
            ferdigstillelsesaar: Året tiltaket er ferdigstilt
            sluttaar: Siste år med kostnader
            tiltaksomraade: tiltaksområdet virkningen beregnes for (kun til indeksering av output)
            logger: Kanal for loggføring

        """

        self.logger = logger
        self.logger("Setter opp virkning")
        if ferdigstillelsesaar > sluttaar:
            raise ValueError(f"ferdigstillelsesaar kan ikke være senere enn sluttår. Fikk {ferdigstillelsesaar} og {sluttaar}")

        self.strekning = strekning
        self.tiltakspakke = tiltakspakke
        self.tiltaksomraade = tiltaksomraade

        self.beregningsaar = beregningsaar
        self.ferdigstillelsesaar = ferdigstillelsesaar
        self.sluttaar = sluttaar
        self.kostnader = kostnader
        self.oppgradering = oppgrad

        VedlikeholskostnaderSchema.validate(self.kostnader)
        OppgraderingskostnaderSchema.validate(self.oppgradering)

        self._verdsatt_vedlikehold_ref = None
        self._verdsatt_vedlikehold_tiltak = None

    @verbose_schema_error
    @pa.check_types(lazy=True)
    def beregn(
        self,
        vedlikeholdsobjekter: DataFrame[VedlikeholdsobjekterSchema],
    ):

        """
        Funksjon som beregner effekter og verdsetter. Trenger en datafram som viser endring i antall innretninger som
        følge av tiltaket per type navigasjonsinnretning. Funksjonen bruker deretter denne endringen sammen med
        kalkulasjonspriser for vedlikehodskostnader per innretning til å verdsette.

        Args:
            vedlikeholdsobjekter: DataFrame som viser endringen i antall av hver
                                         objekttype for hver tiltakspakke. Dataframen
                                         kan være på mikronivå (alstå endring per tiltakspunkt)
                                         eller summeres for hele tiltakspakken. Det
                                         viktigste er at dataframen inneholder en kolonne
                                         "Objekttype" og at det videre er spesifisert
                                         endring i antall av denne objekttypen under kolonnen "Endring".
                                         Negativ verdi i "Endring" betyr færre antall av denne typen.
            priser_ref: DataFrame med priser som samsvarer med prisjusterte kostnader
                               forbundet med hver objekttype i tiltaksscenariet.
            priser_tiltak: DataFrame med priser som samsvarer med prisjusterte kostnader
                                  forbundet med hver objekttype i referansescenariet.
        """
        self.logger("Beregner og verdsetter")
        vedlikeholdsobjekter_ref = (
            vedlikeholdsobjekter.loc[vedlikeholdsobjekter.Endring < 0]
            .assign(Endring=lambda df: df.Endring * (-1))
            .set_index("Objekttype")
        )

        vedlikeholdsobjekter_tiltak = vedlikeholdsobjekter.loc[
            vedlikeholdsobjekter.Endring > 0
        ].set_index("Objekttype")

        priser_ref = (
            vedlikeholdspriser_per_aar(
                self.kostnader,
                self.oppgradering,
                beregningsaar=self.beregningsaar,
                startaar=self.ferdigstillelsesaar,
                sluttaar=self.sluttaar,
                tiltaksalternativ="ref",
            )
            .reset_index()
            .set_index("Objekttype")
            # .reindex(list(vedlikeholdsobjekter_ref.index.values)*self.kostnader.reset_index().Analysenavn.nunique())
            # .set_index(FOLSOMHET_KOLONNE, append=True)
        )

        temp_ref = pd.DataFrame()
        for analyse in priser_ref.Analysenavn.unique():

            priser_temp = priser_ref.query(f"Analysenavn=='{analyse}'").reindex(vedlikeholdsobjekter_ref.index.values)

            temp_ref = pd.concat((temp_ref, priser_temp), axis=0)

        priser_ref = temp_ref.set_index(FOLSOMHET_KOLONNE, append=True)

        priser_tiltak = (
            vedlikeholdspriser_per_aar(
                self.kostnader,
                self.oppgradering,
                beregningsaar=self.beregningsaar,
                startaar=self.ferdigstillelsesaar,
                sluttaar=self.sluttaar,
                tiltaksalternativ="tiltak",
            )
            .reset_index()
            .set_index("Objekttype")
        )

        temp_tiltak = pd.DataFrame()
        for analyse in priser_tiltak.Analysenavn.unique():
            temp_tiltak = pd.concat((temp_tiltak,
                priser_tiltak.query(f"Analysenavn=='{analyse}'").reindex(
                    vedlikeholdsobjekter_tiltak.index.values
                )),axis=0
            )

        priser_tiltak = temp_tiltak.set_index(FOLSOMHET_KOLONNE, append=True)

        kr_ref = (
            verdsett_vedlikeholdskostnader(
                vedlikeholdsobjekter_ref,
                priser_ref,
                self.beregningsaar,
            )
            .reset_index()
            .groupby(FOLSOMHET_KOLONNE)
            .sum(numeric_only=True)
            #           .to_frame()
            .pipe(
                fyll_indeks,
                Strekning=self.strekning,
                Tiltakspakke=self.tiltakspakke,
                Tiltaksomraade=self.tiltaksomraade,
                Virkningsnavn="Endring i vedlikeholdskostnader",
            )
            .reset_index()
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 1)
            .set_index(VERDSATT_COLS)
        )

        kr_tiltak = (
            verdsett_vedlikeholdskostnader(
                vedlikeholdsobjekter_tiltak,
                priser_tiltak,
                self.beregningsaar,
            )
            .reset_index()
            .groupby(FOLSOMHET_KOLONNE)
            .sum(numeric_only=True)
            .pipe(
                fyll_indeks,
                Strekning=self.strekning,
                Tiltakspakke=self.tiltakspakke,
                Tiltaksomraade=self.tiltaksomraade,
                Virkningsnavn="Endring i vedlikeholdskostnader",
            )
            .reset_index()
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 1)
            .set_index(VERDSATT_COLS)
        )

        if len(kr_ref) > 0:
            self._verdsatt_vedlikehold_ref = (
                kr_ref
                .pipe(
                    legg_til_kolonne_hvis_mangler,
                    kolonnenavn=self.beregningsaar,
                    fyllverdi=0.0
                )
                [self.beregningsaar]
            )
        else:
            self._verdsatt_vedlikehold_ref = kr_ref
        if len(kr_tiltak) > 0:
            self._verdsatt_vedlikehold_tiltak = (
                kr_tiltak
                .pipe(
                    legg_til_kolonne_hvis_mangler,
                    kolonnenavn=self.beregningsaar,
                    fyllverdi=0.0
                )
                [self.beregningsaar]
            )
        else:
            self._verdsatt_vedlikehold_tiltak = kr_ref

    def _get_verdsatt_brutto_ref(self):
        return -self._verdsatt_vedlikehold_ref

    def _get_verdsatt_brutto_tiltak(self):
        return -self._verdsatt_vedlikehold_tiltak

    def _get_volum_ref(self):
        return None

    def _get_volum_tiltak(self):
        return None

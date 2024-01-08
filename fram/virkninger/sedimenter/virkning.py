"""
============================================
Opprenskning av forurensede sedimenter
============================================


Kystverkets tiltak består oftest i mudring (utdyping) i havner og farleder med den hensikt å forbedre fremkommeligheten
og sikkerheten for skipstrafikken. I mange tilfeller vil slike tiltak berøre forurensede sedimenter som så fjernes og
deponeres på en trygg måte. Dette gir positive miljøvirkninger som en ekstra nytte av Kystverkets tiltak. Modellen
beregner også samfunnsøkonomiske nytteeffekter av opprenskning av forurensede sedimenter ved utdyping av et område.
Verdsettingsfaktorene er hentet fra verdsettingsstudien gjennomført av Lindhjem m.fl. (2020), og realprisjusteres som
øvrige miljøvirkninger. Beregningsmetodikken legger opp til at omfanget av nytteeffekten varierer med størrelsen på
utdypingsområdet (innenfor fire intervaller) og tilstandsendringen utdypingen medfører. Tabellen under viser
gjennomsnittlig betalingsvillighet per husholdning for alle tiltaksscenariene.


*Tabell 1: Gjennomsnittlig betalingsvillighet per husholdning for alle tiltaksscenarier, innplassering i
miljøforbedringskategorier og gjennomsnittlig betalingsvillighet på tvers av scenarier for hver kategori.
Oppgitt i 2019-kroner. Kilde: Lindhjem m.fl. (2020)*

+----------------------+-----------------+------------------+--------------------+
| Miljøforbedring      | Areal (1000 kvm)| Klassendring     | BV per husholdning |
+======================+=================+==================+====================+
| Liten                | 20 - 150        |Rød til Oransje   |                    |
+                      |                 +------------------+                    +
+                      |                 |Oransje til Gul   |        850         |
+                      |                 +------------------+                    +
+                      |                 |Gul til Grønn     |                    |
+                      +-----------------+------------------+                    +
|                      | 150 - 400       |Rød til Oransje   |                    |
+----------------------+-----------------+------------------+--------------------+
| Middels              | 20 - 150        |Rød til Gul       |                    |
+                      |                 +------------------+                    +
+                      |                 |Oransje til Grønn |                    |
+                      +-----------------+------------------+                    +
+                      | 150 - 400       |Oransje til Gul   |                    |
+                      |                 +------------------+                    +
+                      |                 |Gul til Grønn     |        950         |
+                      +-----------------+------------------+                    +
+                      | >400            |Rød til Oransje   |                    |
+----------------------+-----------------+------------------+--------------------+
| Stor                 | 20 - 150        |Rød til Grønn     |                    |
+                      +-----------------+------------------+                    +
+                      | 150 - 400       |Rød til Gul       |                    |
+                      |                 +------------------+                    +
+                      |                 |Oransje til Grønn |        1200        |
+                      +-----------------+------------------+                    +
+                      | >400            |Oransje til Gul   |                    |
+                      |                 +------------------+                    +
+                      |                 |Gul til Grønn     |                    |
+----------------------+-----------------+------------------+--------------------+
| Svært stor           | 150 - 400       |Rød til Grønn     |                    |
+                      +-----------------+------------------+                    +
+                      | >400            |Rød til Gul       |                    |
+                      |                 +------------------+                    +
+                      |                 |Rød til Grønn     |        1700        |
+                      |                 +------------------+                    +
+                      |                 |Oransje til Grønn |                    |
+----------------------+-----------------+------------------+--------------------+

Modellen benytter denne matrisen sammen med informasjon som hentes inn fra inputarket i den spesifikke analyse.
I tillegg bruker modellen informasjon om antall husholdninger i de ulike kommunene.

============================================
Virkningsklassen forurensede sedimenter
============================================

"""

from typing import List, Callable

import pandas as pd
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.hjelpefunksjoner import (
    fyll_indeks,
    _legg_til_kolonne,
    forut,
)
from fram.generelle_hjelpemoduler.konstanter import (
    SKATTEFINANSIERINGSKOSTNAD,
    VERDSATT_COLS,
)
from fram.virkninger.sedimenter import hjelpemoduler
from fram.virkninger.sedimenter.schemas import ForurensingSchema
from fram.virkninger.virkning import Virkning

VIRKNINGSNAVN = "Endring i forurensede sedimenter"


class Sedimenter(Virkning):
    def __init__(
        self,
        ferdigstillelsesaar: int,
        beregningsaar: List[int],
        kroneaar: int,
        tiltaksomraade: int = -1,
        tiltakspakke: int = -1,
        logger: Callable = print,
    ):
        """
        Klasse for beregning av forurensede sedimenter ved utdypingstiltak.

        Trenger informasjon om tilstand i utdypingsområdet før og etter tiltak. Man må også oppgi informasjon
        om området areal befinner seg i.

        Args:
            ferdigstillelsesaar: året tiltaket har første nyttevirkning
            beregningsaar: liste over beregningsaar
            kroneaar: kroneverdi år
            tiltaksomraade: tiltaksområdet virkningen beregnes for (kun til indeksering av output)
            tiltakspakke: tiltakspakken virkningen beregnes for (kun til indeksering av output)
            logger: Hvor du vil at virkningen skal logge til. Defaulter til 'print'
        """

        self.tiltakspakke = tiltakspakke
        self.tiltaksomraade = tiltaksomraade
        self.logger = logger
        self.logger("Setter opp virkning")
        self._sedimenter_verdsatt_tiltak = None
        self._sedimenter_verdsatt_ref = None
        self.ferdigstillelsesaar = ferdigstillelsesaar
        self.beregningsaar = beregningsaar
        self._kroner_sedimenter = forut("Forurensede sedimenter", 4)
        self.kroneaar = kroneaar
        self._innbyggere_kommune = forut("Befolkning kommune", 2)

    def verdsett_forurensede_sedimenter(self, forurenset):
        """
        Funksjon som verdsetter opprenskning av forurensede sedimenter ved utdypings-
        tiltak. Henter inn informasjon om tilstand i utdypingsområdet før og etter
        tiltak, kommunen utdypingstiltaket befinner seg i og areal på området som
        blir utdypet (1000 m2). Dette hentes  fra inputarket. Tilstand før og etter sammen med størrelsen på
        området bestemmer relevant verdsettingsfaktor som hentes fra :py:func:`~fram.virkninger.sedimenter.hjelpemoduler.get_kroner_sedimenter`.
        Denne verdsettingsfaktoren er betalingsvillighet per husholdning.
        For å finne antall husholdninger benyttes befolkningsdata fra kommunen tiltaket befinner
        seg i, i 2019, og dette befolkningstallet deles deretter på gjennomsnittlig antall personer i
        husholdningen (hentet fra SSB, hardkodet til 2,16).

        Verdsettingen er en engangssum for total betalingsvillighet i ferdigstillelsesåret.

        Args:
            forurenset: df med tilstand, areal og kommune. Streng formatering
        """

        # Henter først inn relevante verdsettingsfaktorer
        faktorer = {}
        for idx, row in forurenset.iterrows():
            faktorer[idx] = hjelpemoduler.get_kroner_sedimenter(
                tilstandsendring=row.tilstandsendring,
                areal=row["Areal (1000 m2)"],
                kroner_sedimenter=self._kroner_sedimenter,
                innbyggere_kommune=self._innbyggere_kommune,
                kommune=row.kommunenavn,
                til_kroneaar=self.kroneaar,
                beregningsaar=self.beregningsaar,
            )
        faktorer = pd.DataFrame(faktorer).T

        # Kobler på
        forurenset = forurenset.merge(
            faktorer, how="left", left_index=True, right_index=True
        )

        # Henter ut relevant informasjon og summerer vertikalt til kun en rad
        # return forurenset[self.ferdigstillelsesaar].to_frame().sum().to_frame().T

        # den aller dummeste hacken
        forurenset[
            [aar for aar in self.beregningsaar if aar != self.ferdigstillelsesaar]
        ] = 0
        return forurenset[self.beregningsaar].sum().to_frame().T.astype(float)

    def beregn(
        self,
        forurenset_tiltak: DataFrame[ForurensingSchema],
        forurenset_ref: DataFrame[ForurensingSchema] = None,
    ):
        """
        Henter inn tilstandsendring og verdsetter dette. Bruker funksjonen :py:func:`~fram.virkninger.sedimenter.virkning.Sedimenter.verdsett_forurensede_sedimenter`
        for henholdsvis tiltaksbanen og referansebanen
        Args:
            forurenset_tiltak: tilstand i utdypingsområdet etter tiltak
            forurenset_ref:  tilstand i utdypingsområdet før tiltak.

        Returns:
            beregnet og verdsatt endring i forurensede sedimenter

        """
        self.logger("Beregner og verdsetter")
        self._sedimenter_verdsatt_tiltak = (
            self.verdsett_forurensede_sedimenter(forurenset_tiltak)
            .pipe(
                fyll_indeks,
                Virkningsnavn=VIRKNINGSNAVN,
                Tiltaksomraade=self.tiltaksomraade,
                Tiltakspakke=self.tiltakspakke,
            )
            .reset_index()
            .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0)
            .set_index(VERDSATT_COLS)
        )

        if forurenset_ref is not None:
            self._sedimenter_verdsatt_ref = (
                self.verdsett_forurensede_sedimenter(forurenset_ref)
                .pipe(
                    fyll_indeks,
                    Virkningsnavn=VIRKNINGSNAVN,
                    Tiltaksomraade=self.tiltaksomraade,
                    Tiltakspakke=self.tiltakspakke,
                )
                .reset_index()
                .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0)
                .set_index(VERDSATT_COLS)
            )

        else:
            self._sedimenter_verdsatt_ref = (
                pd.DataFrame(
                    columns=self._sedimenter_verdsatt_tiltak.columns,
                    index=self._sedimenter_verdsatt_tiltak.index,
                )
                    .fillna(0.0)
                    .pipe(
                    fyll_indeks,
                    Virkningsnavn=VIRKNINGSNAVN,
                    Tiltaksomraade=self.tiltaksomraade,
                    Tiltakspakke=self.tiltakspakke,
                )
                    .reset_index()
                    .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0)
                    .set_index(VERDSATT_COLS)
            )

    def _get_verdsatt_brutto_ref(self):
        return self._sedimenter_verdsatt_ref

    def _get_verdsatt_brutto_tiltak(self):
        return self._sedimenter_verdsatt_tiltak

    def _get_volum_ref(self):
        return None

    def _get_volum_tiltak(self):
        return None

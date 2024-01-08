from abc import abstractmethod, ABC
from dataclasses import dataclass, astuple
from typing import Optional

import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.schemas import (
    VerdsattSchema,
    VolumSchema,
)
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error


class Virkning(ABC):
    """Dette er en baseclass som alle virkninger i FRAM skal arve fra.

    At det er en baseclass betyr at den stiller en del krav til hvordan er virkning skal se ut
    for at den skal bli akseptert som en ekte virkning, og den sikrer at alle virkningene har
    felles grenesnitt/API-er som man (og FRAM) kan benytte.

    For det første krever den at alle virkninger implementerer en metode `beregn`, som er den metoden
    man kaller for å "kjøre virkningen", det vil som regel si å beregne en effekt og verdsette den.

    For det andre implementerer den egenskapene (properties) `verdsatt_brutto_ref`, `verdsatt_brutto_tiltak`
    og `verdsatt_netto`. Disse returnerer pandas `DataFrames` som alle automatisk valideres mot schemaet
    :py:meth:`~fram.generelle_hjelpemoduler.schemas.VerdsattSchema`. På samme måte implementerer den `volumvirkning_ref`
    og `volumvirkning_tiltak`, som valideres mot schemaet :py:meth:`~fram.generelle_hjelpemoduler.schemas.VolumSchema`.

    Måten den løser dette på, er ved å hente verdier fra noen underliggende funksjoner (e.g. `_get_verdsatt_brutto_ref`)
    som den krever at utvikleren må implementere når man lager en ny virkning.

    """

    @property
    @abstractmethod
    def beregn(self):
        pass

    @property
    @verbose_schema_error
    @pa.check_types(lazy=True)
    def verdsatt_brutto_ref(self) -> DataFrame[VerdsattSchema]:
        return self._get_verdsatt_brutto_ref()

    @abstractmethod
    def _get_verdsatt_brutto_ref(self) -> DataFrame[VerdsattSchema]:
        return None

    @property
    @verbose_schema_error
    @pa.check_types(lazy=True)
    def verdsatt_brutto_tiltak(self) -> DataFrame[VerdsattSchema]:
        return self._get_verdsatt_brutto_tiltak()

    @abstractmethod
    def _get_verdsatt_brutto_tiltak(self) -> DataFrame[VerdsattSchema]:
        return None

    @property
    @verbose_schema_error
    @pa.check_types(lazy=True)
    def volumvirkning_ref(self) -> Optional[DataFrame[VolumSchema]]:
        return self._get_volum_ref()

    @abstractmethod
    def _get_volum_ref(self) -> Optional[DataFrame[VolumSchema]]:
        return None

    @property
    @verbose_schema_error
    @pa.check_types(lazy=True)
    def volumvirkning_tiltak(self) -> Optional[DataFrame[VolumSchema]]:
        return self._get_volum_tiltak()

    @abstractmethod
    def _get_volum_tiltak(self) -> Optional[DataFrame[VolumSchema]]:
        return None

    @property
    @verbose_schema_error
    @pa.check_types(lazy=True)
    def verdsatt_netto(self) -> DataFrame[VerdsattSchema]:
        """ Verdsatt nettovirkning. Positive verdier er gevinster, negative er kostnader"""
        return self.verdsatt_brutto_tiltak.subtract(
            self.verdsatt_brutto_ref, fill_value=0
        )

    def get_naaverdi(self, rentebane=None):
        """Returnerer neddiskontert nåverdi med renter som angitt i rentebanen, for hvert år i rentebanen


        Args:
            rentebane: mapping fra aar til renteverdi
        """
        rentebane = rentebane or self.rentebane
        if isinstance(rentebane, dict):
            rentebane = pd.Series(rentebane)
        if rentebane is None:
            raise KeyError(
                f"Kan ikke beregne nåverdi for {self} uten en rentebane. Det har ikke blitt opprettet en ved init og det ble ikke angitt en i kallet til '{self}.get_naaverdi'"
            )
        return self.verdsatt_netto.sum(axis=0).multiply(rentebane, fill_value=0).sum()

    def __repr__(self):
        return f"{self.__class__.__name__}"


_VIRKNING_UDEFINERT = "Denne virkningen er ikke initialisert ennå"

class UdefinertVirkning:
    """En placeholder som legges i FRAM inntil den enkelte virkningen har blitt definert.

    Denne kan man se helt bort fra når man forsøker å forstå modellen, den er bare der for
    at det skal ligge en standardverdi i klassen `Virkninger` når denne initialiseres.
    """
    def __repr__(self):
        return _VIRKNING_UDEFINERT

@dataclass(slots=True)
class Virkninger:
    """Hjelpeklasse for å samle virkningene til FRAM. Gjør det lettere å slå dem opp med e.g. `modell.virkninger.risiko`

    I tillegg implementerer den to støttefunksjoner som er nyttige. For det første kan man iterere over den,
    det vil si at man kan si `for virkning in fram.virkninger` og så får man hver virkning i retur i loopen.
    For det andre implementerer den lengdeoperatoren, slik at man kan se hvor mange virkninger som er definert.
    Før man setter opp noen virkninger vil lengden være null, e.g. `v = Virkninger(); len(v)` vil gi 0.
    Når to virkninger er definert, for eksempel tidsbruk og drivstoff, vil lengden være 2.


    Utover dette utfører denne ingen funksjonalitet og behøver ikke forstås for å bruke FRAM.
    """
    andre_kontantstrommer: Virkning = _VIRKNING_UDEFINERT
    drivstoff: Virkning = _VIRKNING_UDEFINERT
    forurensede_sedimenter: Virkning = _VIRKNING_UDEFINERT
    investeringskostnader: Virkning = _VIRKNING_UDEFINERT
    risiko: Virkning = _VIRKNING_UDEFINERT
    tidsbruk: Virkning = _VIRKNING_UDEFINERT
    utslipp_til_luft: Virkning = _VIRKNING_UDEFINERT
    vedlikehold: Virkning = _VIRKNING_UDEFINERT
    ventetid: Virkning = _VIRKNING_UDEFINERT

    def __iter__(self):
        return iter([v for v in astuple(self) if not v == _VIRKNING_UDEFINERT])

    def __len__(self):
        return len([el for el in iter(self)])

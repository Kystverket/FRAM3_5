import pandera as pa
from pandera.typing import Series, Index

MULIGE_OBJEKTER = [
    "Lyktehus på stativ",
    "Lyktehus på søyle",
    "Lyktehus på underbygning",
    "Lyktehus på varde",
    "HIB på stativ",
    "HIB på søyle",
    "HIB på stang",
    "HIB på varde",
    "IB på stativ",
    "IB på søyle",
    "IB på stang",
    "IB på varde",
    "Lanterne på stativ",
    "Lanterne på søyle",
    "Lanterne på stang",
    "Lanterne på varde",
    "Lysbøye i glassfiber",
    "Lysbøye i stål",
    "Båke",
    "Stake",
    "Stang",
    "Varde",
    "Fyrstasjon",
]


class VedlikeholskostnaderSchema(pa.SchemaModel):
    """
    Validerer at innholdet i årskolonnene er ikke-negative tall. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ==================  ===============  ============
    *Objekttype*        *Analysenavn*           Total
    ==================  ===============  ============
    Lyktehus på stativ   Hovedscenario            200
    Lyktehus på stativ   Hovedscenario            200
    Lanterne på stativ   Hovedscenario            200
    ==================  ===============  ============

    """

    Objekttype: Index[str] = pa.Field(isin=MULIGE_OBJEKTER)
    Analysenavn: Index[str] = pa.Field(coerce=True)
    Total: Series[float] = pa.Field(ge=0, coerce=True, nullable=True)


class OppgraderingskostnaderSchema(pa.SchemaModel):
    """
    Skjema for oppgraderingskostnader. Må være oppgitt som positive tall. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ==============  ===============  =======  ============  ============  ============
    *Objekttype*    *Analysenavn*      Total      TG0->TG2      TG1->TG2    Kroneverdi
    ==============  ===============  =======  ============  ============  ============
    IB på varde                                          1           4.5          1991
    HIB på stang                                         1        1.7976          2078
    HIB på stativ                                        1      2.111635          1953
    ==============  ===============  =======  ============  ============  ============

    """

    Objekttype: Index[str] = pa.Field(isin=MULIGE_OBJEKTER)
    Analysenavn: Index[str] = pa.Field(coerce=True)
    Total: Series[float] = pa.Field(ge=0, coerce=True, nullable=True)
    tg0tg2: Series[float] = pa.Field(ge=0, coerce=True, alias="TG0->TG2")
    tg1tg2: Series[float] = pa.Field(ge=0, coerce=True, alias="TG1->TG2")
    Kroneverdi: Series[int] = pa.Field(ge=1900, le=2100, coerce=True)


class VedlikeholdsobjekterSchema(pa.SchemaModel):
    """
    Skjema for vedlikeholdsobjekter. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ==================  =========
      *None*  Objekttype            Endring
    ========  ==================  =========
           0  Lyktehus på stativ          0
           1  Lyktehus på stativ          0
           2  Lyktehus på stativ          0
    ========  ==================  =========

    """

    Objekttype: Series[str] = pa.Field(isin=MULIGE_OBJEKTER)
    Endring: Series[int] = pa.Field(coerce=True)



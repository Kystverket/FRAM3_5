import pandera as pa
from pandera.typing import Index, Series

from fram.generelle_hjelpemoduler.konstanter import LENGDEGRUPPER, SKIPSTYPER
from fram.generelle_hjelpemoduler.schemas import NumeriskeIkkeNegativeKolonnerSchema


class VekterSchema(pa.SchemaModel):
    """
    Schema for drivstoffvekter. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ====================  ================  ===============  =================  ===================  ===================  ===================  ==================
    *Skipstype*           *Lengdegruppe*      service_speed    engine_kw_total    Virkningsgrad_MGO    Virkningsgrad_LNG    Virkningsgrad_NOY    Virkningsgrad_EL
    ====================  ================  ===============  =================  ===================  ===================  ===================  ==================
    Andre offshorefartøy  0-30                          0                    0                    0                    0                    0                   0
    Andre offshorefartøy  0-30                          0                    0                    0                    0                    0                   0
    Andre offshorefartøy  0-30                          0                    0                    0                    0                    0                   0
    ====================  ================  ===============  =================  ===================  ===================  ===================  ==================

    """

    Skipstype: Index[str] = pa.Field(isin=SKIPSTYPER)
    Lengdegruppe: Index[str] = pa.Field(isin=LENGDEGRUPPER)
    service_speed: Series[float] = pa.Field(coerce=True)
    engine_kw_total: Series[float] = pa.Field(coerce=True)
    Virkningsgrad_MGO: Series[float] = pa.Field(coerce=True)
    Virkningsgrad_LNG: Series[float] = pa.Field(coerce=True)
    Virkningsgrad_NOY: Series[float] = pa.Field(coerce=True)
    Virkningsgrad_EL: Series[float] = pa.Field(coerce=True)


class HastighetsSchema(pa.SchemaModel):
    """
    Schema for drivstoffvekter. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ====================  ================  ===========
    *Rute*    *Skipstype*           *Lengdegruppe*      Hastighet
    ========  ====================  ================  ===========
    ..        Andre offshorefartøy  0-30                        0
    ..        Andre offshorefartøy  0-30                        0
    ..        Andre offshorefartøy  0-30                        0
    ========  ====================  ================  ===========

    """
    Rute: Index[str]
    Skipstype: Index[str] = pa.Field(isin=SKIPSTYPER)
    Lengdegruppe: Index[str] = pa.Field(isin=LENGDEGRUPPER)
    Hastighet: Series[float] = pa.Field(coerce=True)


class TankeSchema(pa.SchemaModel):
    """
    Schema for tankested. Må være en streng og ta verdiene "sør", "nord" eller "int",
    """
    Tankested: str = pa.Field(isin=["sør", "nord", "int"])


class KrPerDrivstoffSchema(pa.SchemaModel):
    """
    Schema for kroner per drivstoff.  Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ====================  ================  ========  =================
    *Skipstype*           *Lengdegruppe*    *Sted*    *Drivstofftype*
    ====================  ================  ========  =================
    Andre offshorefartøy  0-30              sør       MGO og HFO
    Andre offshorefartøy  0-30              sør       MGO og HFO
    Andre offshorefartøy  0-30              sør       MGO og HFO
    ====================  ================  ========  =================

    """
    Skipstype: Index[str] = pa.Field(isin=SKIPSTYPER)
    Lengdegruppe: Index[str] = pa.Field(isin=LENGDEGRUPPER)
    Sted: Index[str] = pa.Field(isin=["sør", "nord", "int"])
    Drivstofftype: Index[str] = pa.Field(
        isin=["MGO og HFO", "Elektrisitet", "LNG", "Karbonøytrale drivstoff"]
    )


class DrivstoffPerTimeSchema(pa.SchemaModel):
    """
    Schema for drivstoff per time. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ================  =================
    *Skipstype*    *Lengdegruppe*    *Drivstofftype*
    =============  ================  =================
    Fiskefartøy    250-300           Elektrisitet
    Bulkskip       30-70             Elektrisitet
    Bulkskip       0-30              Elektrisitet
    =============  ================  =================

    """
    Skipstype: Index[str] = pa.Field(isin=SKIPSTYPER)
    Lengdegruppe: Index[str] = pa.Field(isin=LENGDEGRUPPER)
    Drivstofftype: Index[str] = pa.Field(
        isin=["MGO og HFO", "Elektrisitet", "LNG", "Karbonøytrale drivstoff"]
    )


class DrivstoffandelerSchema(NumeriskeIkkeNegativeKolonnerSchema):
    """
    Schema for drivstoffandeler over tid. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ================  =================
    Skipstype      Lengdegruppe      Drivstofftype
    =============  ================  =================
    Fiskefartøy    250-300           Elektrisitet
    Bulkskip       30-70             Elektrisitet
    Bulkskip       0-30              Elektrisitet
    =============  ================  =================

    """
    Skipstype: Series[str] = pa.Field(isin=SKIPSTYPER)
    Lengdegruppe: Series[str] = pa.Field(isin=LENGDEGRUPPER)
    Drivstofftype: Series[str] = pa.Field(
        isin=["MGO og HFO", "Elektrisitet", "LNG", "Karbonnøytrale drivstoff"]
    )

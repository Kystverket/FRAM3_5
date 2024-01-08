import pandera as pa
from pandera.typing import Index, Series

from fram.generelle_hjelpemoduler.konstanter import LENGDEGRUPPER, SKIPSTYPER


class KalkprisSchema(pa.SchemaModel):
    """
    Kalkpris-schema for kalkpriser på utslipp til luft. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  =========
      *None*  Utslipp
    ========  =========
           0  PM10
           1  NOX
           2  CO2
    ========  =========

    """

    Utslipp: Series[str] = pa.Field(isin=["CO2", "NOX", "PM10"])


class VekterSchema(pa.SchemaModel):
    """
    Kalkpris-schema for drivstoffvekter. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ====================  ================  ===============  =================  ===================  ===================  ===================  ==================
    *Skipstype*           *Lengdegruppe*      service_speed    engine_kw_total    Virkningsgrad_MGO    Virkningsgrad_LNG    Virkningsgrad_NOY    Virkningsgrad_EL
    ====================  ================  ===============  =================  ===================  ===================  ===================  ==================
    Andre servicefartøy   0-30                -2.80068e+75        -0.99999              0.5                  0.99999                  0.99999        1.5
    Containerskip         0-30                -3.40282e+38         2.22045e-16         -3.11369e+16         -1.17549e-38             -1.9            7.42704e+113
    Stykkgods-/Roro-skip  0-30                 1.79769e+308        1.1                 -2.22045e-16         -1.17549e-38              0.5            0.333333
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
    Kalkpris-schema for hastighet. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ==================  ================  ===========
    *Rute*    *Skipstype*         *Lengdegruppe*      Hastighet
    ========  ==================  ================  ===========
        A     Passasjerskip/Roro  70-100            4.67901e+16
        A     Passasjerskip/Roro  70-100            2.89144e+16
        A     Passasjerskip/Roro  70-100            0.5
    ========  ==================  ================  ===========

    """
    Rute: Index[str]
    Skipstype: Index[str] = pa.Field(isin=SKIPSTYPER)
    Lengdegruppe: Index[str] = pa.Field(isin=LENGDEGRUPPER)
    Hastighet: Series[float] = pa.Field(coerce=True)


class TankeSchema(pa.SchemaModel):
    """

    Tankested må ta verdiene "sør", "nord" og "int".

    """
    Tankested: str = pa.Field(isin=["sør", "nord", "int"])


class KrPerDrivstoffSchema(pa.SchemaModel):
    """
    Kalkpris-schema for drivstoff. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

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
    Schema for drivstoff. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ===================  ================  =================
    *Skipstype*          *Lengdegruppe*    *Drivstofftype*
    ===================  ================  =================
    Offshore supplyskip  0-30              MGO og HFO
    Offshore supplyskip  0-30              MGO og HFO
    Offshore supplyskip  0-30              MGO og HFO
    ===================  ================  =================

    """
    Skipstype: Index[str] = pa.Field(isin=SKIPSTYPER)
    Lengdegruppe: Index[str] = pa.Field(isin=LENGDEGRUPPER)
    Drivstofftype: Index[str] = pa.Field(
        isin=["MGO og HFO", "Elektrisitet", "LNG", "Karbonøytrale drivstoff"]
    )
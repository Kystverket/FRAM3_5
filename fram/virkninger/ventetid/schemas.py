import pandera as pa
from pandera.typing import Series

from fram.generelle_hjelpemoduler.konstanter import ALLE, LENGDEGRUPPER, SKIPSTYPER
from fram.generelle_hjelpemoduler.schemas import NumeriskeIkkeNegativeKolonnerSchema


class VentetidInputSchema(pa.SchemaModel):
    """
    Schema for ventetidinngangsverdier. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ===========  ================  ==============  ================  ======  =========  ============
      *None*  Strekning      Tiltaksomraade    Tiltakspakke  Analyseomraade    Rute    ark_ref    ark_tiltak
    ========  ===========  ================  ==============  ================  ======  =========  ============
           0                              0               0
           1                              0               0
           2                              0               0
    ========  ===========  ================  ==============  ================  ======  =========  ============

    """
    Strekning: Series[str]
    Tiltaksomraade: Series[int]
    Tiltakspakke: Series[int]
    Analyseomraade: Series[str]
    Rute: Series[str]
    ark_ref: Series[str]
    ark_tiltak: Series[str]

    class Config:
        name = "Schema for ventetid input. Strengene i 'ark_ref' og 'ark_tiltak' må finnes i Excel-inputboken"
        strict = True


class VentetidLambdaSchema(NumeriskeIkkeNegativeKolonnerSchema):
    """
    Schema for Lambda-verdiene. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ==============  ====================  ===========  =========  ==========  ======  ======  ======  ======  ======
      *None*  Lengdegruppe    Skipstype             direction    periode    ship_ids      2020    2021    2022    2023    2024
    ========  ==============  ====================  ===========  =========  ==========  ======  ======  ======  ======  ======
           0  0-30            Andre offshorefartøy                                           0       0       0       0       0
           1  0-30            Andre offshorefartøy                                           0       0       0       0       0
           2  0-30            Andre offshorefartøy                                           0       0       0       0       0
    ========  ==============  ====================  ===========  =========  ==========  ======  ======  ======  ======  ======

    """
    Lengdegruppe: Series[str] = pa.Field(isin=LENGDEGRUPPER + [ALLE])
    Skipstype: Series[str] = pa.Field(isin=SKIPSTYPER + ["Øvrige fartøy"])
    direction: Series[
        str
    ]  # Inntil to ulike retninger hvis du modellerer en flaskehals i en led
    periode: Series[str]  # Flere perioder hvis du deler døgnet i ulike perioder
    ship_ids: Series[
        str
    ]  # For å unikt identifisere hvert skip. For eksempel 'Skipstype'--'Lengdegruppe'


class VentetidMuSchema(pa.SchemaModel):
    """
    Schema for Mu-verdiene. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ==============  ====================  ===========  ==========
      *None*  Lengdegruppe    Skipstype             direction    ship_ids
    ========  ==============  ====================  ===========  ==========
           0  0-30            Andre offshorefartøy  0
           1  0-30            Andre offshorefartøy
           2  0-30            Andre offshorefartøy
    ========  ==============  ====================  ===========  ==========

    """
    Lengdegruppe: Series[str] = pa.Field(isin=LENGDEGRUPPER + [ALLE])
    Skipstype: Series[str] = pa.Field(isin=SKIPSTYPER + ["Øvrige fartøy"])
    direction: Series[
        str
    ]  # Inntil to ulike retninger hvis du modellerer en flaskehals i en led
    ship_ids: Series[
        str
    ]  # For å unikt identifisere hvert skip. For eksempel 'Skipstype'--'Lengdegruppe'
    # I tillegg behoves noen lopskolonner. Disse navngis fritt


class PerioderAndelSchema(pa.SchemaModel):
    """
    Schema for perioder. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  =========  =======
      *None*  periode      andel
    ========  =========  =======
           0  0                0
           1                   0
           2                   0
    ========  =========  =======

    """
    periode: Series[str]
    andel: Series[float]


class OvrigKategoriSchema(pa.SchemaModel):
    """
    Schema for perioder. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ==============  ====================
      *None*  Lengdegruppe    Skipstype
    ========  ==============  ====================
           0  0-30            Andre offshorefartøy
           1  0-30            Andre offshorefartøy
           2  0-30            Andre offshorefartøy
    ========  ==============  ====================

    """

    Lengdegruppe: Series[str] = pa.Field(isin=LENGDEGRUPPER)
    Skipstype: Series[str] = pa.Field(isin=SKIPSTYPER)




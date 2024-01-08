from typing import Optional

import pandera as pa
from pandera.typing import Index, Series

from fram.generelle_hjelpemoduler.konstanter import LENGDEGRUPPER, SKIPSTYPER, ALLE, FYLKER
from fram.generelle_hjelpemoduler.schemas import (
    AggColsSchema,
    NumeriskeIkkeNegativeKolonnerSchema,
    SkipstypeLengdegrupppeSchema,
    FolsomColsSchema
)


class _HendelsetypeSchema(pa.SchemaModel):
    """

    Må ta index med navn "Hendelsestype" som tar følgende strengverdier
    "Grunnstøting", "Kontaktskade", "Striking", Struck".

    """
    Hendelsestype: Index[str] = pa.Field(
        isin=["Grunnstøting", "Kontaktskade", "Striking", "Struck"]
    )


class HendelseSchema(FolsomColsSchema):

    """

    Schema for hendelser. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ==================  ================  ==================  ========  ====================  ================  ===============  =================  =================
    *Strekning*      *Tiltaksomraade*    *Tiltakspakke*  *Analyseomraade*    *Rute*    *Skipstype*           *Lengdegruppe*    *Analysenavn*    *Risikoanalyse*    *Hendelsestype*
    =============  ==================  ================  ==================  ========  ====================  ================  ===============  =================  =================
    ..                              0                 0                                Andre offshorefartøy  0-30                                                  Grunnstøting
    ..                              0                 0                                Andre offshorefartøy  0-30                                                  Grunnstøting
    ..                              0                 0                                Andre offshorefartøy  0-30                                                  Grunnstøting
    =============  ==================  ================  ==================  ========  ====================  ================  ===============  =================  =================

    """
    Risikoanalyse: Index[str]
    Hendelsestype: Index[str] = pa.Field(
        isin=["Grunnstøting", "Kontaktskade", "Striking", "Struck"]
    )

    class Config:
        name = "Schema for fremskrevede hendelser"
        multiindex_ordered = False

class AISyRISKKonvertertSchema(pa.SchemaModel):
    """
    Schema for innlest og lengde- og typekonvertert AISyRISK. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.
    [["Skipstype", "Lengdegruppe", "Analyseomraade", "striking", "struck", "kontaktskade", "grunnstøting"]]

    ========  ====================  ==============  ===============  ===============  ===============  ===============  ===============
      *None*  Skipstype             Lengdegruppe    Analyseomraade    striking         struck          kontaktstkade    grunnstøting
    ========  ====================  ==============  ===============  ===============  ===============  ===============  ===============
           0  Andre offshorefartøy  0-30            1_1              0.9123           0.9123           0.9123           0.9123
           1  Andre offshorefartøy  0-30            1_1              1231.1           1231.1           1231.1           1231.1
           2  Andre offshorefartøy  0-30            1_2              123.123          123.123          123.123          123.123
    ========  ====================  ==============  ===============  ===============  ===============  ===============  ===============

    """
    Skipstype: Series[str] = pa.Field(isin=SKIPSTYPER + [ALLE])
    Lengdegruppe: Series[str] = pa.Field(isin=LENGDEGRUPPER + [ALLE])
    Analyseomraade: Series[str] = pa.Field(coerce=True)
    striking: Series[float] = pa.Field(coerce=True)
    struck: Series[float] = pa.Field(coerce=True)
    kontaktskade: Series[float] = pa.Field(coerce=True)
    grunnstøting: Series[float] = pa.Field(coerce=True)


class IwrapRASchema(pa.SchemaModel):
    """
    Schema for Iwrapinnlesning. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ===========  ================  ==============  ================  ======  ====================  ==============  ===============  ===============  ===========  =====  ========  =========
      *None*  Strekning      Tiltaksomraade    Tiltakspakke  Analyseomraade    Rute    Skipstype             Lengdegruppe    Risikoanalyse    Hendelsestype      Hendelser    aar    ra_aar  jobname
    ========  ===========  ================  ==============  ================  ======  ====================  ==============  ===============  ===============  ===========  =====  ========  =========
           0  0                           0               0                            Andre offshorefartøy  0-30                             Grunnstøting               0      0         0
           1                              0               0                            Andre offshorefartøy  0-30                             Grunnstøting               0      0         0
           2                              0               0                            Andre offshorefartøy  0-30                             Grunnstøting               0      0         0
    ========  ===========  ================  ==============  ================  ======  ====================  ==============  ===============  ===============  ===========  =====  ========  =========

    """
    Strekning: Series[str] = pa.Field(coerce=True)
    Tiltaksomraade: Series[int] = pa.Field(coerce=True)
    Tiltakspakke: Series[int] = pa.Field(coerce=True)
    Analyseomraade: Series[str] = pa.Field(coerce=True)
    Rute: Series[str]
    Skipstype: Series[str] = pa.Field(isin=SKIPSTYPER + [ALLE])
    Lengdegruppe: Series[str] = pa.Field(isin=LENGDEGRUPPER + [ALLE])
    Risikoanalyse: Series[str]
    Hendelsestype: Series[str] = pa.Field(
        isin=["Grunnstøting", "Kontaktskade", "Striking", "Struck"]
    )
    Hendelser: Series[float]
    aar: Series[int] = pa.Field(coerce=True)
    ra_aar: Series[int] = pa.Field(coerce=True)
    jobname: Series[str]


class KonsekvensSchema(HendelseSchema):
    """
    Schema for konsekvenser. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ==================  ================  ==================  ========  ====================  ================  ===============  =================  =================  =================  =============
    *Strekning*      *Tiltaksomraade*    *Tiltakspakke*  *Analyseomraade*    *Rute*    *Skipstype*           *Lengdegruppe*    *Analysenavn*    *Risikoanalyse*    *Hendelsestype*    *Virkningsnavn*    *Måleenhet*
    =============  ==================  ================  ==================  ========  ====================  ================  ===============  =================  =================  =================  =============
    ..                              0                 0                                Andre offshorefartøy  0-30                                                  Grunnstøting
    ..                              0                 0                                Andre offshorefartøy  0-30                                                  Grunnstøting
    ..                              0                 0                                Andre offshorefartøy  0-30                                                  Grunnstøting
    =============  ==================  ================  ==================  ========  ====================  ================  ===============  =================  =================  =================  =============

    """
    Virkningsnavn: Index[str]
    Måleenhet: Index[str]

    class Config:
        name = "Schema for fremskrevede helsekonsekvenser"
        multiindex_ordered = False

class KonsekvensmatriseSchema(NumeriskeIkkeNegativeKolonnerSchema):
    """
    Schema for konsekvenser. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    """
    # TODO: Mangler tabelleksempel
    Strekning: Optional[Series[str]]
    Tiltaksomraade: Optional[Series[int]]
    Tiltakspakke: Optional[Series[int]]
    Analyseomraade: Optional[Series[str]]
    Rute: Optional[Series[str]]
    Skipstype: Index[str] = pa.Field(isin=SKIPSTYPER + [ALLE])
    Lengdegruppe: Index[str] = pa.Field(isin=LENGDEGRUPPER + [ALLE])
    Konsekvens: Index[str] = pa.Field(isin=["Dodsfall", "Personskade"])
    Hendelsestype: Index[str] = pa.Field(
        isin=["Grunnstøting", "Kontaktskade", "Striking", "Struck"]
    )

class KonsekvensinputSchema(pa.SchemaModel):
    """
    Schema for konsekvensinput, det brukeren kan angi ved konsekvensreduserende tiltak.
    Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    """
    # TODO: Mangler tabelleksempel
    Skipstype: Series[str] = pa.Field(isin=SKIPSTYPER)
    Lengdegruppe: Series[str] = pa.Field(isin=LENGDEGRUPPER)
    Hendelsestype: Series[str] = pa.Field(
        isin=["Grunnstøting", "Kontaktskade", "Striking", "Struck"]
    )
    Aar: Series[int]
    ant_dodsfall: Series[float] = pa.Field(alias="Antall dodsfall hvis dodsfall")
    ant_skade: Series[float] = pa.Field(alias="Antall personskade hvis personskade")
    sanns_dodsfall: Series[float] = pa.Field(alias="Sannsynlighet Dodsfall")
    sanns_skade: Series[float] = pa.Field(alias="Sannsynlighet Personskade")

class KonsekvensmatriseSchema(NumeriskeIkkeNegativeKolonnerSchema):
    """
    Schema for konsekvenser. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ====================  ================  =================  ======  ======  ======  ======  ======
    *Skipstype*           *Lengdegruppe*    *Hendelsestype*      2020    2021    2022    2023    2024
    ====================  ================  =================  ======  ======  ======  ======  ======
    Andre offshorefartøy  0-30              Grunnstøting            0       0       0       0       0
    Andre offshorefartøy  0-30              Grunnstøting            0       0       0       0       0
    Andre offshorefartøy  0-30              Grunnstøting            0       0       0       0       0
    ====================  ================  =================  ======  ======  ======  ======  ======

    """
    Skipstype: Index[str] = pa.Field(isin=SKIPSTYPER + [ALLE])
    Lengdegruppe: Index[str] = pa.Field(isin=LENGDEGRUPPER + [ALLE])
    Hendelsestype: Index[str] = pa.Field(
        isin=["Grunnstøting", "Kontaktskade", "Striking", "Struck"]
    )


class SarbarhetSchema(pa.SchemaModel):
    """
    Schema for Sårbarhet. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ===========  ================  ==============  ================  ============  =======
      *None*  Strekning      Tiltaksomraade    Tiltakspakke  Analyseomraade    Saarbarhet    Fylke
    ========  ===========  ================  ==============  ================  ============  =======
           0  0                           0               0                    lav
           1                              0               0                    lav
           2                              0               0                    lav
    ========  ===========  ================  ==============  ================  ============  =======

    """
    Strekning: Series[str] = pa.Field(coerce=True)
    Tiltaksomraade: Series[int] = pa.Field(coerce=True)
    Tiltakspakke: Series[int] = pa.Field(coerce=True)
    Analyseomraade: Series[str] = pa.Field(coerce=True)
    Saarbarhet: Series[str] = pa.Field(isin=["lav", "moderat", "hoy", "svaart hoy"])
    Fylke: Series[str] = pa.Field(isin=FYLKER)


class KalkprisHelseSchema(NumeriskeIkkeNegativeKolonnerSchema):
    """
    Schema for kalkpriser helse. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ======  ======  ======  ======  ======
    *None*      2020    2021    2022    2023    2024
    ========  ======  ======  ======  ======  ======
    Dodsfall       0       0       0       0       0
    Dodsfall       0       0       0       0       0
    Dodsfall       0       0       0       0       0
    ========  ======  ======  ======  ======  ======

    """
    Konsekvens: Index[str] = pa.Field(isin=["Dodsfall", "Personskade"])


class KalkprisMaterielleSchema(
    NumeriskeIkkeNegativeKolonnerSchema,
    SkipstypeLengdegrupppeSchema,
    _HendelsetypeSchema,
):
    """
    Schema for kalkpriser materielle skader. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =================  ====================  ================  ======  ======  ======  ======  ======
    *Hendelsestype*    *Skipstype*           *Lengdegruppe*      2020    2021    2022    2023    2024
    =================  ====================  ================  ======  ======  ======  ======  ======
    Grunnstøting       Andre offshorefartøy  0-30                   0       0       0       0       0
    Grunnstøting       Andre offshorefartøy  0-30                   0       0       0       0       0
    Grunnstøting       Andre offshorefartøy  0-30                   0       0       0       0       0
    =================  ====================  ================  ======  ======  ======  ======  ======

    """
    class Config:
        multiindex_ordered = False


class _OljeSchema(NumeriskeIkkeNegativeKolonnerSchema):
    """
    Schema for kalkpriser materielle skader. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ====================  ==============  ===============  ======  ======  ======  ======  ======
      *None*  Skipstype             Lengdegruppe    Hendelsestype      2020    2021    2022    2023    2024
    ========  ====================  ==============  ===============  ======  ======  ======  ======  ======
           0  Andre offshorefartøy  0-30            Grunnstøting          0       0       0       0       0
           1  Andre offshorefartøy  0-30            Grunnstøting          0       0       0       0       0
           2  Andre offshorefartøy  0-30            Grunnstøting          0       0       0       0       0
    ========  ====================  ==============  ===============  ======  ======  ======  ======  ======

    """

    Skipstype: Series[str] = pa.Field(isin=SKIPSTYPER)
    Lengdegruppe: Series[str] = pa.Field(isin=LENGDEGRUPPER)
    Hendelsestype: Series[str] = pa.Field(
        isin=["Grunnstøting", "Kontaktskade", "Striking", "Struck"]
    )


class KalkprisOljeutslippSchema(_OljeSchema):
    """
    Schema for kalkpriser oljeutslipp. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ====================  ==============  ===============  ============  =======  ======  ======  ======  ======  ======
      *None*  Skipstype             Lengdegruppe    Hendelsestype    Saarbarhet    Fylke      2020    2021    2022    2023    2024
    ========  ====================  ==============  ===============  ============  =======  ======  ======  ======  ======  ======
           0  Andre offshorefartøy  0-30            Grunnstøting                                 0       0       0       0       0
           1  Andre offshorefartøy  0-30            Grunnstøting                                 0       0       0       0       0
           2  Andre offshorefartøy  0-30            Grunnstøting                                 0       0       0       0       0
    ========  ====================  ==============  ===============  ============  =======  ======  ======  ======  ======  ======

    """
    Saarbarhet: Series[str]
    Fylke: Series[str]


class KalkprisOljeopprenskingSchema(_OljeSchema):
    pass


if __name__ == "__main__":
    schema = AggColsSchema.to_schema()
    print(schema)
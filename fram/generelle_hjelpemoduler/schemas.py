from typing import Optional

import pandas as pd
import pandera as pa
from pandera.typing import Series, Index, String

from fram.generelle_hjelpemoduler.konstanter import (
    VIRKNINGSNAVN,
    SKATTEFINANSIERINGSKOSTNAD,
    KOLONNENAVN_VOLUMVIRKNING,
    KOLONNENAVN_VOLUM_MAALEENHET,
    ALLE,
    LENGDEGRUPPER,
    SKIPSTYPER,
)


class NumeriskeKolonnerSchema(pa.SchemaModel):
    col_2018: Optional[Series[float]] = pa.Field(alias=2018)
    col_2019: Optional[Series[float]] = pa.Field(alias=2019)
    col_2020: Optional[Series[float]] = pa.Field(alias=2020)
    col_2021: Optional[Series[float]] = pa.Field(alias=2021)
    col_2022: Optional[Series[float]] = pa.Field(alias=2022)
    col_2023: Optional[Series[float]] = pa.Field(alias=2023)
    col_2024: Optional[Series[float]] = pa.Field(alias=2024)
    col_2025: Optional[Series[float]] = pa.Field(alias=2025)
    col_2026: Optional[Series[float]] = pa.Field(alias=2026)
    col_2027: Optional[Series[float]] = pa.Field(alias=2027)
    col_2028: Optional[Series[float]] = pa.Field(alias=2028)
    col_2029: Optional[Series[float]] = pa.Field(alias=2029)
    col_2030: Optional[Series[float]] = pa.Field(alias=2030)
    col_2031: Optional[Series[float]] = pa.Field(alias=2031)
    col_2032: Optional[Series[float]] = pa.Field(alias=2032)
    col_2033: Optional[Series[float]] = pa.Field(alias=2033)
    col_2034: Optional[Series[float]] = pa.Field(alias=2034)
    col_2035: Optional[Series[float]] = pa.Field(alias=2035)
    col_2036: Optional[Series[float]] = pa.Field(alias=2036)
    col_2037: Optional[Series[float]] = pa.Field(alias=2037)
    col_2038: Optional[Series[float]] = pa.Field(alias=2038)
    col_2039: Optional[Series[float]] = pa.Field(alias=2039)
    col_2040: Optional[Series[float]] = pa.Field(alias=2040)
    col_2041: Optional[Series[float]] = pa.Field(alias=2041)
    col_2042: Optional[Series[float]] = pa.Field(alias=2042)
    col_2043: Optional[Series[float]] = pa.Field(alias=2043)
    col_2044: Optional[Series[float]] = pa.Field(alias=2044)
    col_2045: Optional[Series[float]] = pa.Field(alias=2045)
    col_2046: Optional[Series[float]] = pa.Field(alias=2046)
    col_2047: Optional[Series[float]] = pa.Field(alias=2047)
    col_2048: Optional[Series[float]] = pa.Field(alias=2048)
    col_2049: Optional[Series[float]] = pa.Field(alias=2049)
    col_2050: Optional[Series[float]] = pa.Field(alias=2050)
    col_2051: Optional[Series[float]] = pa.Field(alias=2051)
    col_2052: Optional[Series[float]] = pa.Field(alias=2052)
    col_2053: Optional[Series[float]] = pa.Field(alias=2053)
    col_2054: Optional[Series[float]] = pa.Field(alias=2054)
    col_2055: Optional[Series[float]] = pa.Field(alias=2055)
    col_2056: Optional[Series[float]] = pa.Field(alias=2056)
    col_2057: Optional[Series[float]] = pa.Field(alias=2057)
    col_2058: Optional[Series[float]] = pa.Field(alias=2058)
    col_2059: Optional[Series[float]] = pa.Field(alias=2059)
    col_2060: Optional[Series[float]] = pa.Field(alias=2060)
    col_2061: Optional[Series[float]] = pa.Field(alias=2061)
    col_2062: Optional[Series[float]] = pa.Field(alias=2062)
    col_2063: Optional[Series[float]] = pa.Field(alias=2063)
    col_2064: Optional[Series[float]] = pa.Field(alias=2064)
    col_2065: Optional[Series[float]] = pa.Field(alias=2065)
    col_2066: Optional[Series[float]] = pa.Field(alias=2066)
    col_2067: Optional[Series[float]] = pa.Field(alias=2067)
    col_2068: Optional[Series[float]] = pa.Field(alias=2068)
    col_2069: Optional[Series[float]] = pa.Field(alias=2069)
    col_2070: Optional[Series[float]] = pa.Field(alias=2070)
    col_2071: Optional[Series[float]] = pa.Field(alias=2071)
    col_2072: Optional[Series[float]] = pa.Field(alias=2072)
    col_2073: Optional[Series[float]] = pa.Field(alias=2073)
    col_2074: Optional[Series[float]] = pa.Field(alias=2074)
    col_2075: Optional[Series[float]] = pa.Field(alias=2075)
    col_2076: Optional[Series[float]] = pa.Field(alias=2076)
    col_2077: Optional[Series[float]] = pa.Field(alias=2077)
    col_2078: Optional[Series[float]] = pa.Field(alias=2078)
    col_2079: Optional[Series[float]] = pa.Field(alias=2079)
    col_2080: Optional[Series[float]] = pa.Field(alias=2080)
    col_2081: Optional[Series[float]] = pa.Field(alias=2081)
    col_2082: Optional[Series[float]] = pa.Field(alias=2082)
    col_2083: Optional[Series[float]] = pa.Field(alias=2083)
    col_2084: Optional[Series[float]] = pa.Field(alias=2084)
    col_2085: Optional[Series[float]] = pa.Field(alias=2085)
    col_2086: Optional[Series[float]] = pa.Field(alias=2086)
    col_2087: Optional[Series[float]] = pa.Field(alias=2087)
    col_2088: Optional[Series[float]] = pa.Field(alias=2088)
    col_2089: Optional[Series[float]] = pa.Field(alias=2089)
    col_2090: Optional[Series[float]] = pa.Field(alias=2090)
    col_2091: Optional[Series[float]] = pa.Field(alias=2091)
    col_2092: Optional[Series[float]] = pa.Field(alias=2092)
    col_2093: Optional[Series[float]] = pa.Field(alias=2093)
    col_2094: Optional[Series[float]] = pa.Field(alias=2094)
    col_2095: Optional[Series[float]] = pa.Field(alias=2095)
    col_2096: Optional[Series[float]] = pa.Field(alias=2096)
    col_2097: Optional[Series[float]] = pa.Field(alias=2097)
    col_2098: Optional[Series[float]] = pa.Field(alias=2098)
    col_2099: Optional[Series[float]] = pa.Field(alias=2099)
    col_2100: Optional[Series[float]] = pa.Field(alias=2100)
    col_2101: Optional[Series[float]] = pa.Field(alias=2101)
    col_2102: Optional[Series[float]] = pa.Field(alias=2102)
    col_2103: Optional[Series[float]] = pa.Field(alias=2103)
    col_2104: Optional[Series[float]] = pa.Field(alias=2104)
    col_2105: Optional[Series[float]] = pa.Field(alias=2105)
    col_2106: Optional[Series[float]] = pa.Field(alias=2106)
    col_2107: Optional[Series[float]] = pa.Field(alias=2107)
    col_2108: Optional[Series[float]] = pa.Field(alias=2108)
    col_2109: Optional[Series[float]] = pa.Field(alias=2109)
    col_2110: Optional[Series[float]] = pa.Field(alias=2110)
    col_2111: Optional[Series[float]] = pa.Field(alias=2111)
    col_2112: Optional[Series[float]] = pa.Field(alias=2112)
    col_2113: Optional[Series[float]] = pa.Field(alias=2113)
    col_2114: Optional[Series[float]] = pa.Field(alias=2114)
    col_2115: Optional[Series[float]] = pa.Field(alias=2115)
    col_2116: Optional[Series[float]] = pa.Field(alias=2116)
    col_2117: Optional[Series[float]] = pa.Field(alias=2117)
    col_2118: Optional[Series[float]] = pa.Field(alias=2118)
    col_2119: Optional[Series[float]] = pa.Field(alias=2119)
    col_2120: Optional[Series[float]] = pa.Field(alias=2120)
    col_2121: Optional[Series[float]] = pa.Field(alias=2121)
    col_2122: Optional[Series[float]] = pa.Field(alias=2122)
    col_2123: Optional[Series[float]] = pa.Field(alias=2123)
    col_2124: Optional[Series[float]] = pa.Field(alias=2124)
    col_2125: Optional[Series[float]] = pa.Field(alias=2125)
    col_2126: Optional[Series[float]] = pa.Field(alias=2126)
    col_2127: Optional[Series[float]] = pa.Field(alias=2127)
    col_2128: Optional[Series[float]] = pa.Field(alias=2128)
    col_2129: Optional[Series[float]] = pa.Field(alias=2129)

    class Config:
        strict = False


class NumeriskeIkkeNegativeKolonnerSchema(pa.SchemaModel):
    col_2020: Optional[Series[float]] = pa.Field(alias=2020, ge=0)
    col_2021: Optional[Series[float]] = pa.Field(alias=2021, ge=0)
    col_2022: Optional[Series[float]] = pa.Field(alias=2022, ge=0)
    col_2023: Optional[Series[float]] = pa.Field(alias=2023, ge=0)
    col_2024: Optional[Series[float]] = pa.Field(alias=2024, ge=0)
    col_2025: Optional[Series[float]] = pa.Field(alias=2025, ge=0)
    col_2026: Optional[Series[float]] = pa.Field(alias=2026, ge=0)
    col_2027: Optional[Series[float]] = pa.Field(alias=2027, ge=0)
    col_2028: Optional[Series[float]] = pa.Field(alias=2028, ge=0)
    col_2029: Optional[Series[float]] = pa.Field(alias=2029, ge=0)
    col_2030: Optional[Series[float]] = pa.Field(alias=2030, ge=0)
    col_2031: Optional[Series[float]] = pa.Field(alias=2031, ge=0)
    col_2032: Optional[Series[float]] = pa.Field(alias=2032, ge=0)
    col_2033: Optional[Series[float]] = pa.Field(alias=2033, ge=0)
    col_2034: Optional[Series[float]] = pa.Field(alias=2034, ge=0)
    col_2035: Optional[Series[float]] = pa.Field(alias=2035, ge=0)
    col_2036: Optional[Series[float]] = pa.Field(alias=2036, ge=0)
    col_2037: Optional[Series[float]] = pa.Field(alias=2037, ge=0)
    col_2038: Optional[Series[float]] = pa.Field(alias=2038, ge=0)
    col_2039: Optional[Series[float]] = pa.Field(alias=2039, ge=0)
    col_2040: Optional[Series[float]] = pa.Field(alias=2040, ge=0)
    col_2041: Optional[Series[float]] = pa.Field(alias=2041, ge=0)
    col_2042: Optional[Series[float]] = pa.Field(alias=2042, ge=0)
    col_2043: Optional[Series[float]] = pa.Field(alias=2043, ge=0)
    col_2044: Optional[Series[float]] = pa.Field(alias=2044, ge=0)
    col_2045: Optional[Series[float]] = pa.Field(alias=2045, ge=0)
    col_2046: Optional[Series[float]] = pa.Field(alias=2046, ge=0)
    col_2047: Optional[Series[float]] = pa.Field(alias=2047, ge=0)
    col_2048: Optional[Series[float]] = pa.Field(alias=2048, ge=0)
    col_2049: Optional[Series[float]] = pa.Field(alias=2049, ge=0)
    col_2050: Optional[Series[float]] = pa.Field(alias=2050, ge=0)
    col_2051: Optional[Series[float]] = pa.Field(alias=2051, ge=0)
    col_2052: Optional[Series[float]] = pa.Field(alias=2052, ge=0)
    col_2053: Optional[Series[float]] = pa.Field(alias=2053, ge=0)
    col_2054: Optional[Series[float]] = pa.Field(alias=2054, ge=0)
    col_2055: Optional[Series[float]] = pa.Field(alias=2055, ge=0)
    col_2056: Optional[Series[float]] = pa.Field(alias=2056, ge=0)
    col_2057: Optional[Series[float]] = pa.Field(alias=2057, ge=0)
    col_2058: Optional[Series[float]] = pa.Field(alias=2058, ge=0)
    col_2059: Optional[Series[float]] = pa.Field(alias=2059, ge=0)
    col_2060: Optional[Series[float]] = pa.Field(alias=2060, ge=0)
    col_2061: Optional[Series[float]] = pa.Field(alias=2061, ge=0)
    col_2062: Optional[Series[float]] = pa.Field(alias=2062, ge=0)
    col_2063: Optional[Series[float]] = pa.Field(alias=2063, ge=0)
    col_2064: Optional[Series[float]] = pa.Field(alias=2064, ge=0)
    col_2065: Optional[Series[float]] = pa.Field(alias=2065, ge=0)
    col_2066: Optional[Series[float]] = pa.Field(alias=2066, ge=0)
    col_2067: Optional[Series[float]] = pa.Field(alias=2067, ge=0)
    col_2068: Optional[Series[float]] = pa.Field(alias=2068, ge=0)
    col_2069: Optional[Series[float]] = pa.Field(alias=2069, ge=0)
    col_2070: Optional[Series[float]] = pa.Field(alias=2070, ge=0)
    col_2071: Optional[Series[float]] = pa.Field(alias=2071, ge=0)
    col_2072: Optional[Series[float]] = pa.Field(alias=2072, ge=0)
    col_2073: Optional[Series[float]] = pa.Field(alias=2073, ge=0)
    col_2074: Optional[Series[float]] = pa.Field(alias=2074, ge=0)
    col_2075: Optional[Series[float]] = pa.Field(alias=2075, ge=0)
    col_2076: Optional[Series[float]] = pa.Field(alias=2076, ge=0)
    col_2077: Optional[Series[float]] = pa.Field(alias=2077, ge=0)
    col_2078: Optional[Series[float]] = pa.Field(alias=2078, ge=0)
    col_2079: Optional[Series[float]] = pa.Field(alias=2079, ge=0)
    col_2080: Optional[Series[float]] = pa.Field(alias=2080, ge=0)
    col_2081: Optional[Series[float]] = pa.Field(alias=2081, ge=0)
    col_2082: Optional[Series[float]] = pa.Field(alias=2082, ge=0)
    col_2083: Optional[Series[float]] = pa.Field(alias=2083, ge=0)
    col_2084: Optional[Series[float]] = pa.Field(alias=2084, ge=0)
    col_2085: Optional[Series[float]] = pa.Field(alias=2085, ge=0)
    col_2086: Optional[Series[float]] = pa.Field(alias=2086, ge=0)
    col_2087: Optional[Series[float]] = pa.Field(alias=2087, ge=0)
    col_2088: Optional[Series[float]] = pa.Field(alias=2088, ge=0)
    col_2089: Optional[Series[float]] = pa.Field(alias=2089, ge=0)
    col_2090: Optional[Series[float]] = pa.Field(alias=2090, ge=0)
    col_2091: Optional[Series[float]] = pa.Field(alias=2091, ge=0)
    col_2092: Optional[Series[float]] = pa.Field(alias=2092, ge=0)
    col_2093: Optional[Series[float]] = pa.Field(alias=2093, ge=0)
    col_2094: Optional[Series[float]] = pa.Field(alias=2094, ge=0)
    col_2095: Optional[Series[float]] = pa.Field(alias=2095, ge=0)
    col_2096: Optional[Series[float]] = pa.Field(alias=2096, ge=0)
    col_2097: Optional[Series[float]] = pa.Field(alias=2097, ge=0)
    col_2098: Optional[Series[float]] = pa.Field(alias=2098, ge=0)
    col_2099: Optional[Series[float]] = pa.Field(alias=2099, ge=0)
    col_2100: Optional[Series[float]] = pa.Field(alias=2100, ge=0)
    col_2101: Optional[Series[float]] = pa.Field(alias=2101, ge=0)
    col_2102: Optional[Series[float]] = pa.Field(alias=2102, ge=0)
    col_2103: Optional[Series[float]] = pa.Field(alias=2103, ge=0)
    col_2104: Optional[Series[float]] = pa.Field(alias=2104, ge=0)
    col_2105: Optional[Series[float]] = pa.Field(alias=2105, ge=0)
    col_2106: Optional[Series[float]] = pa.Field(alias=2106, ge=0)
    col_2107: Optional[Series[float]] = pa.Field(alias=2107, ge=0)
    col_2108: Optional[Series[float]] = pa.Field(alias=2108, ge=0)
    col_2109: Optional[Series[float]] = pa.Field(alias=2109, ge=0)
    col_2110: Optional[Series[float]] = pa.Field(alias=2110, ge=0)
    col_2111: Optional[Series[float]] = pa.Field(alias=2111, ge=0)
    col_2112: Optional[Series[float]] = pa.Field(alias=2112, ge=0)
    col_2113: Optional[Series[float]] = pa.Field(alias=2113, ge=0)
    col_2114: Optional[Series[float]] = pa.Field(alias=2114, ge=0)
    col_2115: Optional[Series[float]] = pa.Field(alias=2115, ge=0)
    col_2116: Optional[Series[float]] = pa.Field(alias=2116, ge=0)
    col_2117: Optional[Series[float]] = pa.Field(alias=2117, ge=0)
    col_2118: Optional[Series[float]] = pa.Field(alias=2118, ge=0)
    col_2119: Optional[Series[float]] = pa.Field(alias=2119, ge=0)
    col_2120: Optional[Series[float]] = pa.Field(alias=2120, ge=0)
    col_2121: Optional[Series[float]] = pa.Field(alias=2121, ge=0)
    col_2122: Optional[Series[float]] = pa.Field(alias=2122, ge=0)
    col_2123: Optional[Series[float]] = pa.Field(alias=2123, ge=0)
    col_2124: Optional[Series[float]] = pa.Field(alias=2124, ge=0)
    col_2125: Optional[Series[float]] = pa.Field(alias=2125, ge=0)
    col_2126: Optional[Series[float]] = pa.Field(alias=2126, ge=0)
    col_2127: Optional[Series[float]] = pa.Field(alias=2127, ge=0)
    col_2128: Optional[Series[float]] = pa.Field(alias=2128, ge=0)
    col_2129: Optional[Series[float]] = pa.Field(alias=2129, ge=0)

    class Config:
        strict = False


class SkipstypeLengdegrupppeSchema(pa.SchemaModel):
    """
    Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ====================  ================
    *Skipstype*           *Lengdegruppe*
    ====================  ================
    Andre offshorefartøy  0-30
    Andre offshorefartøy  0-30
    Andre offshorefartøy  0-30
    ====================  ================

    """
    Skipstype: Index[str] = pa.Field(isin=SKIPSTYPER + [ALLE])
    Lengdegruppe: Index[str] = pa.Field(isin=LENGDEGRUPPER + [ALLE])


class AggColsSchema(pa.SchemaModel):
    """
    Hjelpeschema med indeksene vi trenger for å identifisere en bestemt verdi i bl.a. VerdsattSchema. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ==================  ================  ==================  ========  ====================  ================
    *Strekning*      *Tiltaksomraade*    *Tiltakspakke*  *Analyseomraade*    *Rute*    *Skipstype*           *Lengdegruppe*
    =============  ==================  ================  ==================  ========  ====================  ================
    ..                              0                 0                                Andre offshorefartøy  0-30
    ..                              0                 0                                Andre offshorefartøy  0-30
    ..                              0                 0                                Andre offshorefartøy  0-30
    =============  ==================  ================  ==================  ========  ====================  ================

    """

    Strekning: Index[str] = pa.Field(coerce=True)
    Tiltaksomraade: Index[int] = pa.Field(coerce=True)
    Tiltakspakke: Index[int] = pa.Field(coerce=True)
    Analyseomraade: Index[str] = pa.Field(coerce=True)
    Rute: Index[str] = pa.Field(coerce=True)
    Skipstype: Index[str] = pa.Field(isin=SKIPSTYPER + [ALLE])
    Lengdegruppe: Index[str] = pa.Field(isin=LENGDEGRUPPER + [ALLE])

    class Config:
        name = "StandardSchema med indekser"
        multiindex_strict = True
        multiindex_ordered = False


class FolsomColsSchema(AggColsSchema):
    """

    Hjelpeschema med indeksene vi trenger for å identifisere en bestemt verdi i bl.a. VerdsattSchema,
    samt analysenavn

    Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ==================  ================  ==================  ========  ====================  ================  ===============
    *Strekning*      *Tiltaksomraade*    *Tiltakspakke*  *Analyseomraade*    *Rute*    *Skipstype*           *Lengdegruppe*    *Analysenavn*
    =============  ==================  ================  ==================  ========  ====================  ================  ===============
    ..                              0                 0                                Andre offshorefartøy  0-30
    ..                              0                 0                                Andre offshorefartøy  0-30
    ..                              0                 0                                Andre offshorefartøy  0-30
    =============  ==================  ================  ==================  ========  ====================  ================  ===============

    """

    Analysenavn: Index[String] = pa.Field(coerce=True)

    class Config:
        name = "Skjema med standardindekser samt følsomhetsfaktor"
        multiindex_strict = True
        multiindex_ordered = False


class TrafikkGrunnlagSchema(FolsomColsSchema, NumeriskeIkkeNegativeKolonnerSchema):
    """

    Trafikkgrunnlag: Riktige indekser og ikke-negative Floats i cellene. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ==================  ================  ==================  ========  ====================  ================  ===============  ======  ======  ======  ======  ======
    *Strekning*      *Tiltaksomraade*    *Tiltakspakke*  *Analyseomraade*    *Rute*    *Skipstype*           *Lengdegruppe*    *Analysenavn*      2018    2019    2020    2021    2022
    =============  ==================  ================  ==================  ========  ====================  ================  ===============  ======  ======  ======  ======  ======
    ..                              0                 0                                Andre offshorefartøy  0-30                                    0       0       0       0       0
    ..                              0                 0                                Andre offshorefartøy  0-30                                    0       0       0       0       0
    ..                              0                 0                                Andre offshorefartøy  0-30                                    0       0       0       0       0
    =============  ==================  ================  ==================  ========  ====================  ================  ===============  ======  ======  ======  ======  ======

    """

    class Config:
        name = "TrafikkGrunnlagSchema"
        multiindex_strict = True

    @pa.dataframe_check
    def ingen_duplikater_i_indeks(cls, df: pd.DataFrame) -> bool:
        return 1 - any(df.index.duplicated())


class TrafikkOverforingSchema(AggColsSchema):
    """

    Trafikkoverføring: Benyttes til å oversette referansetrafikk til tiltakstrafikk. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ==================  ================  ==================  ========  ====================  ================  ==========  ================  ================
    *Strekning*      *Tiltaksomraade*    *Tiltakspakke*  *Analyseomraade*    *Rute*    *Skipstype*           *Lengdegruppe*    Til_rute      Andel_overfort    Overfort_innen
    =============  ==================  ================  ==================  ========  ====================  ================  ==========  ================  ================
    ..                              0                 0                                Andre offshorefartøy  0-30                                         0                 0
    ..                              0                 0                                Andre offshorefartøy  0-30                                         0                 0
    ..                              0                 0                                Andre offshorefartøy  0-30                                         0                 0
    =============  ==================  ================  ==================  ========  ====================  ================  ==========  ================  ================
    """

    Til_rute: Series[str] = pa.Field(coerce=True)
    Andel_overfort: Series[float]
    Overfort_innen: Series[int] = pa.Field(coerce=True)


class TidsbrukPerPassSchema(AggColsSchema, NumeriskeIkkeNegativeKolonnerSchema):
    """

    Tidsbruk per passering: Riktige indekser og ikke-negative Floats i cellene
    Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ==================  ================  ==================  ========  ====================  ================  ======  ======  ======
    *Strekning*      *Tiltaksomraade*    *Tiltakspakke*  *Analyseomraade*    *Rute*    *Skipstype*           *Lengdegruppe*      2020    2021    2022
    =============  ==================  ================  ==================  ========  ====================  ================  ======  ======  ======
    ..                              0                 0                                Andre offshorefartøy  0-30                   0       0       0
    ..                              0                 0                                Andre offshorefartøy  0-30                   0       0       0
    ..                              0                 0                                Andre offshorefartøy  0-30                   0       0       0
    =============  ==================  ================  ==================  ========  ====================  ================  ======  ======  ======

    """

    class Config:
        name = "TidsbrukPerPassSchema"


class PrognoseSchema(TrafikkGrunnlagSchema):
    """

    Gyldige prognoser: Numeriske ikke-negative verdier, indeks gitt ved TRAFIKK_COLS. Floats i cellene
    Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ==================  ================  ==================  ========  ====================  ================  ===============  ======  ======  ======  ======  ======
    *Strekning*      *Tiltaksomraade*    *Tiltakspakke*  *Analyseomraade*    *Rute*    *Skipstype*           *Lengdegruppe*    *Analysenavn*      2018    2019    2020    2021    2022
    =============  ==================  ================  ==================  ========  ====================  ================  ===============  ======  ======  ======  ======  ======
    ..                              0                 0                                Andre offshorefartøy  0-30                                    0       0       0       0       0
    ..                              0                 0                                Andre offshorefartøy  0-30                                    0       0       0       0       0
    ..                              0                 0                                Andre offshorefartøy  0-30                                    0       0       0       0       0
    =============  ==================  ================  ==================  ========  ====================  ================  ===============  ======  ======  ======  ======  ======

    """

    pass


class VerdsattSchema(AggColsSchema, NumeriskeKolonnerSchema):
    """

    Alle verdsatte-dataframes må følge dette schemaet. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ==================  ================  ==================  ========  ====================  ================  =================  ================================  ===============  ======  ======  ======  ======  ======
    *Strekning*      *Tiltaksomraade*    *Tiltakspakke*  *Analyseomraade*    *Rute*    *Skipstype*           *Lengdegruppe*    *Virkningsnavn*      *Skattefinansieringskostnader*  *Analysenavn*      2018    2019    2020    2021    2022
    =============  ==================  ================  ==================  ========  ====================  ================  =================  ================================  ===============  ======  ======  ======  ======  ======
    ..                              0                 0                                Andre offshorefartøy  0-30                                                                0                        0       0       0       0       0
    ..                              0                 0                                Andre offshorefartøy  0-30                                                                0                        0       0       0       0       0
    ..                              0                 0                                Andre offshorefartøy  0-30                                                                0                        0       0       0       0       0

    =============  ==================  ================  ==================  ========  ====================  ================  =================  ================================  ===============  ======  ======  ======  ======  ======

    """

    virkning: Index[str] = pa.Field(alias=VIRKNINGSNAVN)
    skattekost: Index[float] = pa.Field(alias=SKATTEFINANSIERINGSKOSTNAD, coerce=True)
    Analysenavn: Index[str] # ville arvet FolsomCols, men det virker som at det er en bug i pandera som det umulig

    @pa.check(SKATTEFINANSIERINGSKOSTNAD, name="verdier mellom null og en")
    def verdier_null_en(cls, ser: Series[float]) -> Series[bool]:
        return pd.to_numeric(ser).between(0, 1, inclusive="both")

    class Config:
        strict = True


class VolumSchema(FolsomColsSchema, NumeriskeKolonnerSchema):
    """
    Alle volumvirknings-dataframes må følge dette schemaet. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    =============  ==================  ================  ==================  ========  ====================  ================  ===============  =================  =============  ======  ======  ======  ======  ======
    *Strekning*      *Tiltaksomraade*    *Tiltakspakke*  *Analyseomraade*    *Rute*    *Skipstype*           *Lengdegruppe*    *Analysenavn*    *Virkningsnavn*    *Måleenhet*      2018    2019    2020    2021    2022
    =============  ==================  ================  ==================  ========  ====================  ================  ===============  =================  =============  ======  ======  ======  ======  ======
    ..                              0                 0                                Andre offshorefartøy  0-30                                                                      0       0       0       0       0
    ..                              0                 0                                Andre offshorefartøy  0-30                                                                      0       0       0       0       0
    ..                              0                 0                                Andre offshorefartøy  0-30                                                                      0       0       0       0       0
    =============  ==================  ================  ==================  ========  ====================  ================  ===============  =================  =============  ======  ======  ======  ======  ======

    """

    volum_virkning: Index[str] = pa.Field(alias=KOLONNENAVN_VOLUMVIRKNING)
    volum_maaleenhet: Index[str] = pa.Field(alias=KOLONNENAVN_VOLUM_MAALEENHET)

    class Config:
        strict = True
        multiindex_ordered = False

class UtslippAnleggsfasenSchema(NumeriskeIkkeNegativeKolonnerSchema):
    """
    Angir CO2-utslipp i anleggsfasen målt i tonn CO2-e per år

    ================== ================== ================ ======  ======  ======  ======  ======
      *Tiltaksomraade* *Tiltakspakke*      *Analysenavn*   2018    2019    2020    2021    2022
    ================== ================== ================ ======  ======  ======  ======  ======
                   0         0               hovedkjøring    0       0       0       0       0
                   0         0               følsom1         0       0       0       0       0
                   0         0               følsom2         0       0       0       0       0
    ================== ================== ================ ======  ======  ======  ======  ======
    """
    Tiltaksomraade: Series[int] = pa.Field(coerce=True)
    Tiltakspakke: Series[int] = pa.Field(coerce=True)
    Analysenavn: Series[String] = pa.Field(coerce=True)


def generer_docstring_til_schema_dokumentasjon(schema: pa.SchemaModel) -> str:
    from tabulate import tabulate
    eksempel_df = schema.example(size=3)
    index_cols = [col for col in eksempel_df.index.names]
    int_cols = sorted([col for col in eksempel_df.columns if str(col).isnumeric()])
    ovrige_cols = [col for col in eksempel_df.columns if col not in int_cols]
    nye_cols = ovrige_cols + int_cols[:5]
    eksempel_df = eksempel_df[nye_cols].reset_index()
    output_kolonnenavn = [f"*{col}*" for col in index_cols] + nye_cols
    string_repr_of_dataframe = tabulate(eksempel_df, headers=output_kolonnenavn, showindex=False, tablefmt="rst")
    header = f"Pandera Schemamodel"
    return header + "\n" + "\n" + string_repr_of_dataframe




if __name__ == "__main__":
    schema = VolumSchema.to_schema()
    print(generer_docstring_til_schema_dokumentasjon(schema))
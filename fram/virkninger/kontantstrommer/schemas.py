from typing import Optional

import pandera as pa
from pandera.typing import Series

from fram.generelle_hjelpemoduler.schemas import NumeriskeKolonnerSchema


class KontanstromSchema(NumeriskeKolonnerSchema):
    """

    Schema for kontantstrømmer. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ============  ==================================  ==============  ============  ============  =============  ===========  =======
    *None*    Kroneverdi    Andel skattefinansieringskostnad    Aktør           2018          2019           2020         2021     2022
    ========  ============  ==================================  ==============  ============  ============  =============  ===========  =======
           0          2062                                   0  Det offentlige  -1e+07         3.50808e-99  -3.40282e+38   3.40282e+38  0.5
           1          2007                                   1  Det offentlige                 9.4338e+258   0             1.28029e+252  2.00001      0.99999
           2          1983                                   1  Det offentlige   1e-05        -0.99999       1.5           0.333333     1e+07
    ========  ============  ==================================  ==============  ============  =============  ===========  =======

    """

    Kroneverdi: Series[int] = pa.Field(gt=1950, lt=2100, coerce=True)
    Aktør: Series[str] = pa.Field(
        isin=["Trafikanter og transportbrukere", "Det offentlige", "Samfunnet for øvrig", "Operatører", 'Ikke kategorisert']
    )
    andel_skatt: Optional[Series[int]] = pa.Field(
        isin=[0, 1], alias="Andel skattefinansieringskostnad"
    )

import pandera as pa
from pandera.typing import Series

from fram.generelle_hjelpemoduler.konstanter import ALLE, LENGDEGRUPPER, SKIPSTYPER
from fram.generelle_hjelpemoduler.schemas import NumeriskeIkkeNegativeKolonnerSchema


class KalkprisTidSchema(NumeriskeIkkeNegativeKolonnerSchema):
    """
    Gyldig kalkulasjonspriser for tid. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ===================  ==============  ===========  ===========  ======  ============  =======
      *None*  Skipstype            Lengdegruppe           2020         2021    2022          2023     2024
    ========  ===================  ==============  ===========  ===========  ======  ============  =======
           0  Gasstankskip         0-30            8.29861e-44  1.1           1e+07  5.36094e+16   2.00001
           1  Offshore supplyskip  0-30            1e-05        1.19209e-07   1.1    0             0.99999
           2  Brønnbåt             0-30            4.89534e+16  1.17549e-38   1.1    1.79769e+308  2.00001
    ========  ===================  ==============  ===========  ===========  ======  ============  =======

    """

    Skipstype: Series[str] = pa.Field(isin=SKIPSTYPER + [ALLE])
    Lengdegruppe: Series[str] = pa.Field(isin=LENGDEGRUPPER + [ALLE])

    class Config:
        name = "Schema for kalkpriser tid"



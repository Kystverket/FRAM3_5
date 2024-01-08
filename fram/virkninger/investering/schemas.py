import pandas as pd
import pandera as pa
from pandera.typing import Series


class InvesteringskostnadSchema(pa.SchemaModel):
    """
    Schema for DataFrame fra et riktig formattert investeringskostark. Tabellen under viser et eksempel på en slik dataframe. Tabelloversikt i kursiv er indekser.

    ========  ================  ====================  ==================  ==============  ============================  =========================
      *None*  Tiltaksomraade            Tiltakspakke  Investeringstype      P50 (kroner)    Forventningsverdi (kroner)    Anleggsperiode
    ========  ================  ====================  ==================  ==============  ============================  =========================
           0                0                    10             Utdyping             100                          100                           5
           1                0                    10                Annet             100                          100                           1
    ========  ================  ====================  ==================  ==============  ============================  =========================

    - Investeringstype: 'str', tar verdiene ["Utdyping", "Navigasjonsinnretninger", "Annet"]

    """

    Tiltaksomraade: Series[str] = pa.Field(coerce=True)
    Tiltakspakke: Series[int] = pa.Field(coerce=True)
    Investeringstype: Series[str] = pa.Field(
        isin=["Utdyping", "Navigasjonsinnretninger", "Annet"]
    )
    p50: Series[float] = pa.Field(
        alias="P50 (kroner)", coerce=True, nullable=True
    )
    forventning: Series[float] = pa.Field(
        alias="Forventningsverdi (kroner)", ge=0, coerce=True
    )
    anleggsperiode: Series[int] = pa.Field(
        alias="Anleggsperiode", gt=0, coerce=True
    )





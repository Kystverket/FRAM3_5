import pandas as pd

from fram.generelle_hjelpemoduler.hjelpefunksjoner import forut


def get_virkningsgrad(alder: int, kW: int, drivstofftype: str):
    """
    Henter inn informasjon om virkningsgrad som angir.

    Args:
      alder: Alder på hovedmotor (år bygget)
      kW: motorstrørrelse på hovedmotor. Finnes i beriket skipsdata
      drivstofftype: drivstofftype

    Returns:
        float: Returnerer riktig virkningsgrad verdi basert på alder og motorstørrelse.

    """
    KONSUM = forut("Virkningsgrad", 4)  # # Erstatter "KONSUM = forut("SFOC", 3)"

    if alder < 1984:
        data = KONSUM.loc[(KONSUM["Alder"] == "<1984")]
        if kW < 5000:
            return data.loc[
                (KONSUM["kW"] == "<5000")
                & (KONSUM["Drivstofftype"] == drivstofftype),
                "Virkningsgrad",
            ].values[0]
        elif 5000 <= kW <= 15000:
            return data.loc[
                (KONSUM["kW"] == "5000-15000")
                & (KONSUM["Drivstofftype"] == drivstofftype),
                "Virkningsgrad",
            ].values[0]
        elif kW > 15000:
            return data.loc[
                (KONSUM["kW"] == ">15000")
                & (KONSUM["Drivstofftype"] == drivstofftype),
                "Virkningsgrad",
            ].values[0]
    if 1984 <= alder <= 2000:
        data = KONSUM.loc[(KONSUM["Alder"] == "1984-2000")]
        if kW < 5000:
            return data.loc[
                (KONSUM["kW"] == "<5000")
                & (KONSUM["Drivstofftype"] == drivstofftype),
                "Virkningsgrad",
            ].values[0]
        elif 5000 <= kW <= 15000:
            return data.loc[
                (KONSUM["kW"] == "5000-15000")
                & (KONSUM["Drivstofftype"] == drivstofftype),
                "Virkningsgrad",
            ].values[0]
        elif kW > 15000:
            return data.loc[
                (KONSUM["kW"] == ">15000")
                & (KONSUM["Drivstofftype"] == drivstofftype),
                "Virkningsgrad",
            ].values[0]
    if alder > 2000:
        data = KONSUM.loc[(KONSUM["Alder"] == ">2000")]
        if kW < 5000:
            return data.loc[
                (KONSUM["kW"] == "<5000")
                & (KONSUM["Drivstofftype"] == drivstofftype),
                "Virkningsgrad",
            ].values[0]
        elif 5000 <= kW <= 15000:
            return data.loc[
                (KONSUM["kW"] == "5000-15000")
                & (KONSUM["Drivstofftype"] == drivstofftype),
                "Virkningsgrad",
            ].values[0]
        elif kW > 15000:
            return data.loc[
                (KONSUM["kW"] == ">15000")
                & (KONSUM["Drivstofftype"] == drivstofftype),
                "Virkningsgrad",
            ].values[0]
    else:
        return 0


def virkningsgrad(virkning_df, drivstofftype: str):
    """
    Henter virkningsgrad for ulike skip i en dataframe

    Args:
        virkning_df (DataFrame): Dataframe som må ha kolonne 'year_built' og 'engine_kw_total'
        drivstofftype: drivstofftype

    Returns:
        DataFrame: Verdier for virkningsgrad for ulike skip gitt ulike "year_built" og "engine_kw_total"

    """
    if not isinstance(virkning_df, pd.DataFrame):
        raise ValueError("df må være en pandas DataFrame")
    for col in ["year_built", "engine_kw_total"]:
        if col not in list(virkning_df):
            raise KeyError(f"df må ha en kolonne {col}")
    drivstoff = virkning_df.apply(
        lambda x: get_virkningsgrad(  # Erstatter "get_SFOC"-Funksjonen
            alder=x["year_built"],
            kW=x["engine_kw_total"],
            drivstofftype=drivstofftype,
        ),
        axis=1,
    )
    return drivstoff
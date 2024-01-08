import pandas as pd

from tests.felles import strekning_pakke, beregn_lonnsomhet, FILNAVN_FASIT

# LAG NY FASIT FOR RESULTATER
def lag_ny_fasit():
    gammel_fasit_navn = FILNAVN_FASIT.parent / 'fasiter-kopi.csv'
    gammel_fasit_navn.write_text(FILNAVN_FASIT.read_text())
    fasit = []
    for strekning, pakke in strekning_pakke:
        print(strekning, pakke)
        output = beregn_lonnsomhet(strekning, pakke).to_frame()
        fasit.append(output.assign(Strekning=strekning, Pakke=pakke))

    df = pd.concat(fasit, axis=0, sort=False)
    df.reset_index().rename(columns={"index": "Virkninger"}).to_csv(FILNAVN_FASIT)


# +
# Sammenligne fasiter
def les_inn_fasit(filnavn):
    return (
        pd
        .read_csv(filnavn, index_col=0)
        .loc[lambda df: ~df.Virkninger.isin(["rente", "diskonteringsfaktor"])]
        .set_index(["Strekning", "Pakke", "Virkninger"])
    )


def sammenligne_fasiter():

    return (
        les_inn_fasit("fasiter-kopi.csv")
        .rename(columns={"Nåverdi levetid": "Gammel"})
        .merge(
            right=les_inn_fasit("fasiter.csv").rename(columns={"Nåverdi levetid": "Ny"}),
            left_index=True,
            right_index=True
        )
        .assign(
            Endring_ny_minus_gammel = lambda df: df["Ny"] - df["Gammel"],
            Endring_pst = lambda df: df["Endring_ny_minus_gammel"] / df["Gammel"]
        )
        .query("Endring_ny_minus_gammel != 0")
        .sort_values(by="Endring_pst")
    )



# LAG NY FASIT - TIDSKOSTNADER


from fram.virkninger.tid.verdsetting import tidskalk_funksjoner

def lag_ny_fasit_tidskostnader():
    fasit = (pd.read_csv(FILNAVN_FASIT.parent.parent / "fram" / "virkninger" / "tid" / "test_tidskalkulasjonspriser_mikrodata.csv")
            .rename(columns={"BT": "grosstonnage", "dodvekt": "dwt", "Lengde": "skipslengde"})
            .assign(Analysenavn="Test")
            )

    fasit["tid_kpris"] = fasit.apply(lambda x: tidskalk_funksjoner(Skipstype=x["Skipstype"],
                                                       dwt=x["dwt"],
                                                       grosstonnage=x["grosstonnage"],
                                                       gasskap=x["gasskap"],
                                                       skipslengde=x["skipslengde"]),axis=1)
    fasit = fasit[['dwt', "Skipstype", "skipslengde", "gasskap", "Analysenavn", "grosstonnage", 'tid_kpris']]

    fasit.to_csv(FILNAVN_FASIT.parent.parent / "fram" / "virkninger" / "tid" / "test_tidskalkulasjonspriser_mikrodata.csv", sep=",")



if __name__ == "__main__":
    lag_ny_fasit()



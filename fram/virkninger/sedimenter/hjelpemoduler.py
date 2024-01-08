import pandas as pd

from fram.generelle_hjelpemoduler.kalkpriser import get_vekstfaktor, realprisjustering_kalk, prisjustering


def get_kroner_sedimenter(tilstandsendring, areal, kroner_sedimenter, til_kroneaar, beregningsaar,innbyggere_kommune=None, kommune=None):
    """
    Henter inn informasjon om verdsettingsfaktorer lik kroner per husholdning for
    verdsetting av opprenskning av forurensede sedimenter i et utdypingsområde.
    Disse blir både krone- og realprisjustert. Verdsettingsstudien tok utgangspunkt i diskrete arealer. I modellen
    har vi interpolert verdsettingsfaktorene slik at større arealer alltid har høyere verdi, opp til den øvre
    terskelen på 400 (1000 m2). Etter 400 (1000 m2) har vi lagt til grunn konstant verdsettingsfaktor i tråd med
    verdsettingsstudien

    Args:
        tilstandsendring: endring i tilstand (rød, oransje, gul og grønn) i tilstandsområdet, på formatet (Før -> Etter)
        areal: antall 1000-kvadratmeter tiltaksareal.
        kommune: navn på kommunen som området befinner seg i.
    return:
        Df med verdsettingsfaktorer for ulike arealintervaller, kommuner og tilstandsendringer.
    """

    tilstand_for, tilstand_etter = tilstandsendring.split(" -> ")

    if areal < 0:
        raise ValueError("Areal må være positivt")
    elif areal <= 150:
        areal_bin = "20-150"
    elif areal <= 400:
        areal_bin = "150-400"
    else:
        areal_bin = ">400"

    if areal_bin == "20-150":
        terskel = 85
    elif areal_bin == "150-400":
        terskel = 275
    else:
        terskel = areal

    if areal < 85:
        kroner = lookup_kroner_sedimenter(
            kroner_sedimenter, tilstand_for, tilstand_etter, areal_bin
        ) * (areal / terskel)
    elif areal < 275:
        kroner_lav = lookup_kroner_sedimenter(
            kroner_sedimenter, tilstand_for, tilstand_etter, "20-150"
        )
        kroner_hoy = lookup_kroner_sedimenter(
            kroner_sedimenter, tilstand_for, tilstand_etter, "150-400"
        )
        kroner = kroner_lav + (areal - 85) / (275 - 85) * (kroner_hoy - kroner_lav)
    elif areal <= 400:
        kroner_lav = lookup_kroner_sedimenter(
            kroner_sedimenter, tilstand_for, tilstand_etter, "150-400"
        )
        kroner_hoy = lookup_kroner_sedimenter(
            kroner_sedimenter, tilstand_for, tilstand_etter, ">400"
        )
        kroner = kroner_lav + (areal - 275) / (400 - 275) * (kroner_hoy - kroner_lav)
    else:
        kroner = lookup_kroner_sedimenter(
            kroner_sedimenter, tilstand_for, tilstand_etter, areal_bin
        )

    kroner_sedimenter = (
        pd.Series({"kroner_sedimenter": kroner}, name="kroner")
        .to_frame()
        .assign(
            kroner=lambda df: df.kroner.map(
                lambda x: realprisjustering_kalk(belop=x, utgangsaar=2019)
            )
            * prisjustering(1, 2019)
        )
    )
    kroner_sedimenter[til_kroneaar] = kroner_sedimenter["kroner"]
    for year in range(til_kroneaar + 1, max(beregningsaar)):
        kroner_sedimenter[year] = kroner_sedimenter[year - 1] * (
            1 + get_vekstfaktor(year)
        )

    kolonner = list(range(til_kroneaar, max(beregningsaar)))
    kroner = kroner_sedimenter.loc[:, kolonner]

    HUSHOLDNINGSSTØRRELSE = 2.16

    if kommune is not None and innbyggere_kommune is not None:
        ant_innbyggere = get_innbyggere_kommune(innbyggere_kommune, kommune)
        kroner = kroner * ant_innbyggere / HUSHOLDNINGSSTØRRELSE

    return kroner.to_dict(orient="records")[0]


def lookup_kroner_sedimenter(
    kroner_sedimenter, tilstand_før, tilstand_etter, areal_bin
):
    """
    Hjelpefunksjon for raskere oppslag i dataframe
    """
    return kroner_sedimenter.loc[
        lambda df: (df.tilstand_før == tilstand_før)
        & (df.tilstand_etter == tilstand_etter)
        & (df["Areal (1000 m2)"] == areal_bin),
        "verdsettingsfaktor_tall",
    ].values[0]

def get_innbyggere_kommune(innbyggere_kommune, kommnunenavn):
    """
    Hjelpefunkjson for å lese inn relevante kommuner og befolkningstall. Henter fra kommuneinndeling per 2019, og
    henter inn befolkningstall i 2019.
    """
    try:
        antall = innbyggere_kommune.loc[
            lambda df: df.komm_navn == kommnunenavn, "personer_2019"
        ].values[0]
    except:
        raise ValueError(f"Fant ikke kommune {kommnunenavn} i forutsetningsarket")
    return antall
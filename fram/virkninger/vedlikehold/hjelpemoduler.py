import pandas as pd

from fram.generelle_hjelpemoduler.kalkpriser import prisjustering
from fram.generelle_hjelpemoduler.konstanter import FOLSOMHET_KOLONNE

def verdsett_vedlikeholdskostnader(
    vedlikeholdsobjekter,
    priser,
    beregningsaar,
):
    """
    Regner ut vedlikeholdskostnadene til oppgitte objekter i beregningsårene.

    Args:
        vedlikeholdsobjekter: Objekttyper og antall (nye) objekter
        priser: Vedlikeholdskostnader forbundet med hver objekttype
        beregningsaar: Årene kostnadene skal beregnes for

    Returns:
        DataFrame: Vedlikeholdskostnadene for hver objekttype
    """
    # analyser = priser.reset_index().Analysenavn.values
    df_out = pd.DataFrame(
        columns=["Objekttype", FOLSOMHET_KOLONNE] + beregningsaar
    ).set_index(["Objekttype", FOLSOMHET_KOLONNE])
    for analyse in priser.reset_index().Analysenavn.unique():
        df_mellom = (priser.query(f"Analysenavn=='{analyse}'")
            .reset_index()
            .set_index("Objekttype")[beregningsaar]
            .multiply(vedlikeholdsobjekter["Endring"], axis=0)
            .assign(Analysenavn=analyse)
            .set_index(FOLSOMHET_KOLONNE, append=True))


        df_out = pd.concat((df_out, df_mellom), axis=0)
    return df_out


def vedlikeholdspriser_per_aar(
    kostnader,
    oppgrad,
    beregningsaar,
    startaar=2018,
    sluttaar=2018,
    tiltaksalternativ="ref",
    tilaar=None,
):
    """
    Fremskriver Kystverkets vedlikeholds- og oppgraderingskostnader for
    navigasjonsinnretninger. Antar at nye merker har TG0, og at eksisterende merker er midt mellom
    to perioder TG1 og TG2. Prisjusteres til tilaar.

    Args:
        kostnader: Løpende vedlikeholdskostnader per objekttype
        oppgrad: Kostnader ved oppgraderinger per objekttype
        beregningsaar:eregningsår: Årene som skal verdsettes
        startaar: Første år med vedlikeholdskostnader
        sluttaar: Siste år med kostnader
        tiltaksalternativ: Tar veridene "ref" eller "tiltak"
        tilaar: kroneaar. Deault er None og da leses KRONEAAR i fram/Forutsetninger_FRAM.xlsx inn som predefinert kroneår.

    Returns:
        Dataframe med vedlikeholdskostnader (kr per år) over tid fordelt på ulike objekttyper.
    """

    if tiltaksalternativ not in ["ref", "tiltak"]:
        raise KeyError(
            f"tiltaksalternativ må være en av 'ref' eller 'tiltak', ikke {tiltaksalternativ}"
        )

    for year in range(startaar, sluttaar + 1):
        kostnader[year] = kostnader["Total"]
    vedlikehold = kostnader.drop("Total", axis=1)

    if tiltaksalternativ == "ref":
        referanse = oppgrad.copy().assign(
            oppgradert=lambda df: beregningsaar[0] - df["TG1->TG2"] // 2
        )
        for year in beregningsaar:
            referanse[year] = (
                (year - referanse["oppgradert"]) % referanse["TG1->TG2"] == 0
            ) * referanse["Total"]
        oppgradering = (
            referanse.reset_index()
            .groupby(["Objekttype", FOLSOMHET_KOLONNE])[beregningsaar]
            .sum()
        )

    elif tiltaksalternativ == "tiltak":
        tiltak = oppgrad.copy().assign(oppgradert=startaar)
        for year in beregningsaar:
            forste_oppgrad = tiltak["oppgradert"] + tiltak["TG0->TG2"]
            tiltak[year] = (
                (
                    (
                        ((year - forste_oppgrad) % tiltak["TG1->TG2"] == 0)
                        & (year - forste_oppgrad >= 0)
                    )
                )
            ).clip(0, 1) * tiltak["Total"]
        oppgradering = (
            tiltak.reset_index()
            .groupby(["Objekttype", FOLSOMHET_KOLONNE])[beregningsaar]
            .sum()
        )
    else:
        raise KeyError(
            "Noe er galt, er ikke 'tiltaksalternativ' en av 'ref' eller 'tiltak'??"
        )
        # oppgradering = [list(range(startaar, sluttaar + 1))]
    kostnader = vedlikehold + oppgradering

    kroneaar = int(oppgrad.Kroneverdi.values[0])

    prisfaktor = prisjustering(1, kroneaar, tilaar)
    kostnader = kostnader * prisfaktor

    return kostnader

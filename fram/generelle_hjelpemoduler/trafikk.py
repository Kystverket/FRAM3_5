from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.konstanter import (
    SKIPSTYPER,
    LENGDEGRUPPER,
    TRAFIKK_COLS,
    FOLSOMHET_COLS
)
from fram.generelle_hjelpemoduler.schemas import (
    TrafikkGrunnlagSchema,
    TrafikkOverforingSchema,
    PrognoseSchema,
)
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error


@verbose_schema_error
def fremskriv_trafikk(
    trafikk_grunnlagsaar: DataFrame[TrafikkGrunnlagSchema],
    prognoser: DataFrame[PrognoseSchema],
    overforing: Optional[DataFrame[TrafikkOverforingSchema]],
    trafikkaar: List[int],
    ferdigstillelsesaar: int,
    rute_til_analyseomraade: Dict[int, str],
    tiltakspakke: int,
) -> Tuple[DataFrame[TrafikkGrunnlagSchema], DataFrame[TrafikkGrunnlagSchema]]:
    """
    Fremskriver trafikken for både referansebanen og tiltaksbanen. For referansebanen leses trafrikkgrunnlaget
    inn, og fremskrives med prognoser. For tiltaksbanen så fremskrifves trafikken på samme
    måte som referansebanen dersom det ikke er trafikkoverføring, men dersom det er trafikkoverføringe
    så brukes overforingsmatrisen før prognosene benyttes til fremskriving.

    Args:
        trafikk_grunnlagsaar: Dataframe med passeringer i grunnlagsåret fordelt
          på Strekning, Tiltaksomraade, Tiltakspakke, Analyseomraade, Rute, Skipstype og
          Lengdegruppe. Grunnlagsåret er den eneste kolonnen
        prognoser: Dataframe med prognoser fra grunnlagsåret og frem til sluttår fordelt
          på Strekning, Tiltaksomraade, Tiltakspakke, Analyseomraade, Rute, Skipstype og
          Lengdegruppe.
        overforing: Overføringsmatrise for å overføre trafikk fra ref til tiltak
        trafikkaar: Liste med årene det skal beregnes trafikk for
        folsom_trafikkvolum: Multiplikasjonsfaktor som ganges inn med beregnet trafikk
        ferdigstillelsesaar: Når pakken åpnes. Benyttes for å overføre all trafikk i riktig år dersom det mangler i input
        rute_til_analyseomraade: Mapping fra rute til analyseområde for å fylle ut riktig i overføringen
        tiltakspakke: Hvilken tiltakspakke vi jobber med

    Returns:
        En tuple med trafikkgrunnlag for trafikk_referanse og trafikk_tiltak
    """
    TrafikkGrunnlagSchema.validate(trafikk_grunnlagsaar)
    PrognoseSchema.validate(prognoser)
    if overforing is not None:
        TrafikkOverforingSchema.validate(overforing)

    # Kobler prognosene på
    trafikk_referanse = trafikk_grunnlagsaar.merge(
        right=prognoser.rename(columns=lambda x: "prog_" + str(x)),
        left_index=True,
        right_index=True,
        how="left",
    )

    for year in trafikkaar:
        trafikk_referanse[year + 1] = trafikk_referanse[year].multiply(
            trafikk_referanse[f"prog_{year}"]
        )
        trafikk_referanse = trafikk_referanse.drop(f"prog_{year}", axis=1)

    trafikk_tiltak = _beregn_overfort_trafikk(
        trafikk_referanse=trafikk_referanse,
        overforing=overforing,
        siste_overforingsaar=ferdigstillelsesaar,
        trafikkaar=trafikkaar,
        rute_til_analyeomraade=rute_til_analyseomraade,
        tiltakspakke=tiltakspakke,
    )

    return (trafikk_referanse, trafikk_tiltak)


@verbose_schema_error
@pa.check_types(lazy=True)
def _beregn_overfort_trafikk(
    trafikk_referanse: DataFrame[TrafikkGrunnlagSchema],
    overforing: Optional[DataFrame[TrafikkOverforingSchema]],
    siste_overforingsaar: int,
    trafikkaar: List[int],
    rute_til_analyeomraade: Dict[int, str],
    tiltakspakke: int,
) -> DataFrame[TrafikkGrunnlagSchema]:
    """Hjelpefunksjon for å beregne trafikk på rutene etter overføringen
    som finner sted som følge av tiltaket. Er ikke ment å kalles på av eksterne

    Returns:
        DataFrame med gyldig trafikkgrunnlag i tiltaksbanen
    """
    # Hvis det ikke er angitt overføring, returnere trafikken i referansebanen
    if (overforing is None) or (len(overforing) == 0):
        return trafikk_referanse

    relevante_ruter = list(
        trafikk_referanse.reset_index()
        .loc[lambda df: df.Tiltakspakke == tiltakspakke]
        .Rute.unique()
    )
    overf_beregnet = []
    over = overforing.reset_index()
    for rute in relevante_ruter:
        for skipstype in SKIPSTYPER:
            for lengdegruppe in LENGDEGRUPPER:
                manglende_overf = (
                    1
                    - over.loc[
                        (over["Rute"] == rute)
                        & (over["Skipstype"] == skipstype)
                        & (over["Lengdegruppe"] == lengdegruppe),
                        "Andel_overfort",
                    ].sum()
                )
                overf_beregnet.append(
                    {
                        "Rute": rute,
                        "Skipstype": skipstype,
                        "Lengdegruppe": lengdegruppe,
                        "Andel_overfort": manglende_overf,
                    }
                )

    over = (
        pd.DataFrame(overf_beregnet)
        .assign(Til_rute=lambda x: x.Rute)
        .merge(
            right=trafikk_referanse.reset_index()[
                [
                    "Strekning",
                    "Tiltakspakke",
                    "Tiltaksomraade",
                    "Analyseomraade",
                    "Rute",
                ]
            ].drop_duplicates(),
            left_on="Rute",
            right_on="Rute",
            how="left",
        )
        .merge(
            right=overforing.reset_index()[
                ["Skipstype", "Lengdegruppe", "Rute", "Overfort_innen"]
            ],
            on=["Skipstype", "Lengdegruppe", "Rute"],
            how="left",
        )
    )

    overforing = pd.concat([overforing.reset_index(), over], axis=0, sort=False).assign(
        Overfort_innen=lambda x: x.Overfort_innen.fillna(siste_overforingsaar)
    )

    gal_overforing = (
        overforing.groupby(["Skipstype", "Lengdegruppe", "Rute"])[["Andel_overfort"]]
        .sum()
        .query("Andel_overfort != 1")
    )
    if len(gal_overforing) > 0:
        print(gal_overforing)
        raise ValueError(
            "Feil i beregning av trafikkoverføring. Noen skip blir borte eller lagt til"
        )
    # Kobler overføringsandelene på trafikken
    step1 = (
        trafikk_referanse.reset_index()
        .merge(
            right=overforing.reset_index(),
            on=TRAFIKK_COLS,
            how="left",
        )
    )

    #

    # Multipliserer inn overføringsandelene, med lineær innføring
    step2 = step1.copy()
    for year in trafikkaar:
        opprinnelig = step2[year] * (step2["Rute"] == step2["Til_rute"])
        etter_overforing = step2[year].multiply(step2["Andel_overfort"], axis=0)
        vekt = np.clip(
            (year + 1 - siste_overforingsaar)
            / (step2["Overfort_innen"] - siste_overforingsaar + 1),
            0,
            1,
        )
        step2[year] = (1 - vekt) * opprinnelig + vekt * etter_overforing

    # Collapser og summerer over hvor trafikken kommer fra, slik at vi
    # får en rad per skipstype, lengde og rute
    step3 = (
        step2.drop("Rute", axis=1)
        .rename(columns={"Til_rute": "Rute"})
        .drop("Analyseomraade", axis=1)
        .assign(Analyseomraade=lambda df: df.Rute.map(rute_til_analyeomraade))
        .groupby(FOLSOMHET_COLS)[trafikkaar]
        .sum()
    )

    return step3


@verbose_schema_error
@pa.check_types(lazy=True)
def valider_at_prognoser_for_all_trafikk(
    trafikk_grunnlagsaar: DataFrame[TrafikkGrunnlagSchema],
    prognoser: DataFrame[PrognoseSchema],
):
    koblet = trafikk_grunnlagsaar.merge(
        right=prognoser,
        left_index=True,
        right_index=True,
        how="outer",
        indicator=True,
    )
    trafikk_uten_prognoser = koblet.loc[koblet["_merge"] == "left_only"]
    prognoser_uten_trafikk = koblet.loc[koblet["_merge"] == "right_only"]

    ant_trafikk_uten_prognoser = len(trafikk_uten_prognoser)
    if ant_trafikk_uten_prognoser > 0:
        formatert_feil = "\n".join(
            [str(entry) for entry in trafikk_uten_prognoser.index]
        )
        raise ValueError(
            f"Det mangler prognoser for {ant_trafikk_uten_prognoser} skipstyper/lengdegrupper/ruter. Kan ikke fortsette. Dette gjelder \n {formatert_feil}"
        )

    ant_prognoser_uten_trafikk = len(prognoser_uten_trafikk)
    if ant_prognoser_uten_trafikk > 0:
        raise ValueError(
            f"Det mangler trafikk for {ant_prognoser_uten_trafikk} skipstyper/lengdegrupper/ruter hvor du har prognoser. Disse settes til null."
        )

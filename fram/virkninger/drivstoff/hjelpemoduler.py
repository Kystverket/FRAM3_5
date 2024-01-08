from typing import List

import pandas as pd
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.konstanter import (
    SKIPSTYPER,
    LENGDEGRUPPER,
    FOLSOMHET_KOLONNE,
)

from fram.generelle_hjelpemoduler.schemas import TidsbrukPerPassSchema

from fram.virkninger.drivstoff.hjelpemodul_drivstofforbruk import (
    get_ettersp_drivstoff_per_time,
    get_kr_per_enhet_drivstoff,
)
from fram.virkninger.drivstoff.schemas import (
    HastighetsSchema,
    TankeSchema,
    VekterSchema,
    DrivstoffPerTimeSchema,
    KrPerDrivstoffSchema,
)


def beregn_drivstofforbruk_per_time(
    beregningsaar: List[int],
    hastighet_df: DataFrame[HastighetsSchema] = None,
    drivstoffvekter=None,
    drivstofforbruk_per_type_time=None,
):
    """
    Beregner drivstofforbruk per time (etterspurt mengde målt i megajoule per time) over tid per skipstype, lengdegruppe, drivstofftype og rute. Forutsetningene er hentet fra
    forutsetninger tilknyttet FRAM-modellen. Beregningen av drivstofforbuk per time foretas på følgende måte:

    - Trinn 1: Beregner energibehovet til fremdrift, propulsjonseffekten, for en gitt fartøystype, lengdegruppe og rute
    - Trinn 2: Fremskriver energibehovet til 2050 ved hjelp av effektiviseringsfaktor
    - Trinn 3: Fordeler energiforbruket per år på ulike energibærere
    - Trinn 4: Beregner etterspurt mengde drivstoff (MJ for elektrisitet) i markedet per
               energibærer ved hjelp av virkningsgrader og energitettheter

    Args:
        hastighet_df: En dataframe med følgende kolonner:

            - Skipstype: Kystverkets skipskategorier
            - Lengdegruppe: Kystverkets lengdegruppekategorier
            - Hastighet: knop
            - Rute

        drivstoffvekter (DataFrame): En dataframe med følgende kolonner:

            - Skipstype: Kystverkets skipskategorier
            - Lengdegruppe: Kystverkets lengdegruppekategorier
            - service_speed:
            - engine_kw_total:
            - Virkningsgrad_MGO:
            - Virkningsgrad_LNG:
            - Virkningsgrad_NOY:
            - Virkningsgrad_EL:

        beregningsaar: liste med år man vil beregne effekter for

    Returns:
        Dataframe: Etterspurt drivstofforbruk målt i MJ fremdrift per time vi får
    """

    ettersp_drivstoff_per_time = get_ettersp_drivstoff_per_time(
        beregningsaar,
        hastighet_df=hastighet_df,
        drivstofforbruk_per_type_time=drivstofforbruk_per_type_time,
        drivstoffvekter=drivstoffvekter,
    )

    return ettersp_drivstoff_per_time


def beregn_kr_per_drivstoff(tankested: List[TankeSchema], kroneaar: int, beregningsaar: List[int]):
    """
    Drivstoffpriser per enhet drivstoff (Kr per Megajoule)
    Pris per MJ er multiplisert med energitetthet for å få pris per enhet drivstoff.
    Skiller mellom priser i 2018 og 2050 der det kun er karbonøytrale drivstoff som har endrede priser over perioden.

    Args:
        kroneaar: Kroneåret du ønsker prisene prisjustert til
        tankested: Tar verdien nord, sør eller int
        beregningsaar: Tidsperiode man ønsker å vurdere effekter over.

    Returns:
        DataFrame: En dataframe der drivstoffprisen varierer med følgende parametere:

            - Skipstype: En av Kystverkets skipstyper
            - Lengdegruppe: En av lengdegruppene
            - Tankersted:

                - sør: sør for Trondheim
                - nord: nord for Trondheim
                - int: internasjonalt

            - Fueltype: Hvilken fueltype du ser på. Har priser for følgende typer:

                - MGO og HFO
                - Elektrisitet
                - LNG
                - Karbonøytrale drivstoff

    """

    sted = tankested

    kr_per_enhet_drivstoff = get_kr_per_enhet_drivstoff(kroneaar, beregningsaar).query(
        "Sted == @sted"
    )

    return kr_per_enhet_drivstoff


def beregn_kr_per_time(
    hastighet: DataFrame[HastighetsSchema],
    tankested: List[TankeSchema],
    kroneaar: int,
    beregningsaar: List[int],
    drivstoff_per_time: DataFrame[DrivstoffPerTimeSchema] = None,
    kr_per_enhet_drivstoff: DataFrame[KrPerDrivstoffSchema] = None,
):
    """
    Henter inn og beregner distanseavhengige kalkulasjonspriser for ulike skip, ulike steder i Norge.
    Drivstoffkostnadene er produktet av:

    - kr per tonn drivstoff (vektet etter andeler)
    - Drivstofforbruket per time:

       -    effektivisering av drivstofforbruket over tid
       -    Motoravhengig, bølgeuahvengig komponent (reflekteres også i virkningsgrad)
       -    Skrogavhengig, bølgeavhengig komponent

    Hastigheten er unik for den enkelte skipstype og lengdegruppe på den enkelte rute. Bølgene er like for alle skip på
    hver rute. All annen skipsspesifikk informasjon representeres som et vektet snitt av informasjonen om skipene som
    har vært observert nasjonalt innad i skipstypene og lengdegruppene.

    Args:
        hastighet: df med skipstype, lengdegruppe, rute og hastighet
        tankested: tankested. Tar verdiene:

                    - sør: sør for Trondheim
                    - nord: nord for Trondheim
                    - int: internasjonalt

        kroneaar: Kroneår de vil ha prisene oppgitt i
        drivstoff_per_time: df med skipstype, lengdegruppe, drivstofftype per år
        kr_per_enhet_drivstoff: df med priser

    Returns:
        DataFrame: Setter sammen produktet av kroner per drivstofforbruk og drivstofforbruk per time. Får altså kroner per time.

    """
    if drivstoff_per_time is None:
        ettersp_drivstoff_per_time = beregn_drivstofforbruk_per_time(
            hastighet, beregningsaar
        )

    else:
        ettersp_drivstoff_per_time = drivstoff_per_time

    if kr_per_enhet_drivstoff is None:
        kr_per_enhet_drivstoff = beregn_kr_per_drivstoff(
            tankested, kroneaar, beregningsaar
        )

    kr_per_enhet_drivstoff = (
        ettersp_drivstoff_per_time.reset_index()[
            ["Rute", "Skipstype", "Lengdegruppe", "Drivstofftype"]
        ]
        .merge(
            kr_per_enhet_drivstoff,
            on=["Skipstype", "Lengdegruppe", "Drivstofftype"],
            how="outer",
        )
        .set_index(["Skipstype", "Lengdegruppe", "Drivstofftype", "Rute"])
    )

    kr_per_time = (
        ettersp_drivstoff_per_time["Rute"]
        .copy()
        .to_frame()
        .reset_index()
        .set_index(["Skipstype", "Lengdegruppe", "Drivstofftype", "Rute"])
    )
    ettersp_drivstoff_per_time = ettersp_drivstoff_per_time.reset_index().set_index(
        ["Skipstype", "Lengdegruppe", "Drivstofftype", "Rute"]
    )

    for year in beregningsaar:
        kr_per_time[year] = (
            ettersp_drivstoff_per_time[year] * kr_per_enhet_drivstoff[year]
        )

    kr_per_time = (
        kr_per_time.reset_index().groupby(["Skipstype", "Lengdegruppe", "Rute"]).sum(numeric_only=True)
    )
    return kr_per_time


def verdsett_drivstoff(
    tid_ref: DataFrame[TidsbrukPerPassSchema],
    tid_tiltak: DataFrame[TidsbrukPerPassSchema],
    hastighet_ref: DataFrame[HastighetsSchema],
    hastighet_tiltak: DataFrame[HastighetsSchema],
    beregningsaar: List[int],
    kroneaar: int,
    tankested: List[TankeSchema],
    kr_per_drivstoff=None,
    drivstoff_per_time_ref=None,
    drivstoff_per_time_tiltak=None,
):
    """
    Funksjon som verdsetter drivstofforbruket for den enkelte skipstypen i den enkelte rute. Henter inn tidsbruk
    (timer) og hastighet (knop) i referanse- og tiltaksbanen. Deretter ganges dette med get_kroner_per_time() fra
    drivstoffklassen.

    Args:
        tid_ref: Tidsbruk per passering i referansebanen. Påkrevd.
        tid_tiltak: Gyldig dataframe med tidsbruk per passering i tiltaksbanen. Påkrevd.
        hastighet_ref: Gyldig dataframe med hastighet i referansebanen. Påkrevd.
        hastighet_tiltak: Gyldig dataframe med hastighet i tiltaksbanen. Påkrevd.
        beregningsaar: liste over de årene du vil ha beregnet virkningen for
        kroneaar: Kroneår de vil ha prisene oppgitt i.
        tankested: Liste over tankersted for tanking nasjonalt. Tar enten verdien "nord" eller "sør". Definert som nord eller sør for Trondheim. Modellen beregner selv internasjonale priser for tanking internasjonalt basert på forhåndbestemte antagelser.
        kr_per_drivstoff (DataFrame): dataframe med kroner per drivstoff
        drivstoff_per_time_ref (DataFrame): dataframe med drivstofforbruk per time i referansebanen
        drivstoff_per_time_tiltak (DataFrame): dataframe med drivstofforbruk per time i tiltak

    Returns:
        DataFrame: Returnerer en dataframe med endring i drivstoffkostnader per rute, skipstype og lengdegruppe.

    """
    if hastighet_tiltak is None or len(hastighet_tiltak) == 0:
        null_df = pd.DataFrame()
        for analyse in tid_tiltak.analysenavn.unique():
            null_df = null_df.append(
                pd.DataFrame(
                    index=pd.MultiIndex.from_product(
                        [SKIPSTYPER, LENGDEGRUPPER], names=["Skipstype", "Lengdegruppe"]
                    ),
                    columns=beregningsaar,
                )
                .assign(Analysenavn=analyse)
                .fillna(0)
            )

        return null_df

    kr_per_time_ref = beregn_kr_per_time(
        hastighet_ref.reset_index(),
        tankested=tankested,
        kroneaar=kroneaar,
        beregningsaar=beregningsaar,
        drivstoff_per_time=drivstoff_per_time_ref,
        kr_per_enhet_drivstoff=kr_per_drivstoff,
    )

    kr_per_time_tiltak = beregn_kr_per_time(
        hastighet_tiltak.reset_index(),
        tankested=tankested,
        kroneaar=kroneaar,
        beregningsaar=beregningsaar,
        drivstoff_per_time=drivstoff_per_time_tiltak,
        kr_per_enhet_drivstoff=kr_per_drivstoff,
    )

    def _multipliser_kr_timer(tid, kr_per_time):
        """
        Hjelpemetode for å multiplisere sammen tidsbruk og kr per time for hhv referansebanen og tiltaksbanen

        """
        # Merger tidsbruk ogverdsettingsfaktor
        koblet = (
            tid.rename(columns=lambda x: "timer_" + str(x))
            .reset_index()
            .merge(
                right=kr_per_time.rename(
                    columns=lambda x: "kr_" + str(x)
                ).reset_index(),
                on=["Skipstype", "Lengdegruppe", "Rute"],
                how="left",
            )
            .set_index(
                [
                    "Strekning",
                    "Tiltaksomraade",
                    "Tiltakspakke",
                    "Analyseomraade",
                    "Rute",
                    "Skipstype",
                    "Lengdegruppe",
                    FOLSOMHET_KOLONNE,
                ]
            )
        ).dropna(axis=0, how="any")
        # Multipliserer sammmen for å verdsette
        for year in beregningsaar:
            koblet[year] = koblet[f"timer_{year}"] * koblet[f"kr_{year}"]
        koblet = koblet[beregningsaar]

        return koblet

    kr_ref = _multipliser_kr_timer(
        tid=tid_ref, kr_per_time=kr_per_time_ref
    ).reset_index()

    kr_tiltak = _multipliser_kr_timer(
        tid=tid_tiltak, kr_per_time=kr_per_time_tiltak
    ).reset_index()

    return kr_ref, kr_tiltak

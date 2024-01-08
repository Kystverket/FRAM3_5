from typing import Tuple, Optional, Union, List

import pandas as pd
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.konstanter import (
    FOLSOMHET_COLS,
    FOLSOMHET_KOLONNE, KOLONNENAVN_STREKNING, KOLONNENAVN_TILTAKSOMRAADE, KOLONNENAVN_TILTAKSPAKKE,
)
from fram.generelle_hjelpemoduler.schemas import TrafikkGrunnlagSchema
from fram.virkninger.felles_hjelpemoduler.schemas import verbose_schema_error
from fram.virkninger.risiko.schemas import HendelseSchema, IwrapRASchema
from fram.virkninger.tid.hjelpemoduler import multipliser_venstre_hoyre


@verbose_schema_error
def beregn_risiko(
    trafikk_referanse: DataFrame[TrafikkGrunnlagSchema],
    risiko_ref: DataFrame[IwrapRASchema],
    trafikk_tiltak: Optional[DataFrame[TrafikkGrunnlagSchema]] = None,
    risiko_tiltak: Optional[DataFrame[IwrapRASchema]] = None,
) -> Tuple[
    DataFrame[HendelseSchema],
    Optional[DataFrame[HendelseSchema]],
    Optional[DataFrame[HendelseSchema]],
]:
    """
    Beregner kollisjoner og grunnstøtinger (hendelser) basert på trafikkgrunnlaget og de hendelsene som er beregnet i RA.

    Grunnstøtinger fremskrives lineært med trafikken, mens kollisjoner fremskrives kvadratiske med trafikken. I
    referansebanen er antall hendelser av hver type konsistent med antall hendelser slik de fremkommer i de
    risikoanalysene som er lagt til grunn. Se for øvrig :meth:`iwrap_fremskriving._fremskriv_hendelser`.

    Ved trafikkoverføring oppstår det en situasjon der RA er gjennomført på trafikken i referansebanen, mens det
    i tiltaksbanen vil kunne være et annet trafikkgrunnlag. For grunnstøtinger, som fremskrives lineært med
    trafikken, er dette håndtert ved å regne ut grunnstøtingsfrekvensen, eller -sannsynligheten, på
    referansebanetrafikken, og så multiplisere denne med tiltaksbanetrafikken, alt per skipstype og lengdegruppe.
    For kollisjoner, som er antatt kvadratiske i trafikken, er den kvadratiske formelen beregnet med utgangspunkt i
    referansebanetrafikken og RA-kollisjonene. Disse fremskrives så med trafikken i tiltaksbanen. Det betyr at
    antall kollisjoner i tiltaksbanen er høyere (lavere) enn i referansebanen hvis det er flere (færre) skip enn i
    referansebanen. Dersom antall skip i tiltaksbanen i 2040 er lik antall skip i referansebanen i 2030, vil antall
    kollisjoner også være likt mellom de to.



    Args:
        trafikk_referanse: Gyldig trafikkgrunnlag i referansebanen
        trafikk_tiltak: Gyldig trafikkgrunnlag i tiltaksbanen. Valgfri. Påkrevd hvis det skal beregnes nettoeffekt
        risiko_ref: Gyldig RA-output på rett format. Påkrevd
        risiko_tiltak: Gyldig RA-output på rett format. Valgfri. Påkrevd hvis det skal beregnes nettoeffekt
        folsom_trafikkvolum: Tall som angir hvorvidt trafikkvolumet skal være as is eller økes/reduseres i følsomhetsanalyse
        folsom_ulykkesfrekvens: Tall som angir hvorvidt ulykkesfrekvensen skal være as is eller økes/reduseres i følsomhetsanalyse

    Returns:
        Tre dataframes med beregnede hendelser i hhv ref, tiltak og netto
    """
    TrafikkGrunnlagSchema.validate(trafikk_referanse)
    IwrapRASchema.validate(risiko_ref)
    # Interpoler og fremskriv hendelser basert på utviklingen i trafikken
    # Herunder å fordele hendelsene ned fra RA-oppløsning til rute-oppløsning
    ra_startaar, ra_fremtidsaar = risiko_ref.ra_aar.min(), risiko_ref.ra_aar.max()

    map_ra_til_rute = dict(
        zip(
            risiko_ref.query("ra_aar == @ra_startaar").Rute,
            risiko_ref.query("ra_aar == @ra_startaar").Risikoanalyse,
        )
    )
    trafikkaar = sorted(
        list(
            set(trafikk_referanse.columns.to_list()).intersection(
                set(trafikk_tiltak.columns.to_list())
            )
        )
    )
    hendelser_ref = _fremskriv_hendelser(
        grunnlagstrafikk=trafikk_referanse,
        hendelsestrafikk=trafikk_referanse,
        beregnet_risiko=risiko_ref,
        STARTAAR=ra_startaar,
        FREMTIDSAAR=ra_fremtidsaar,
        map_ra_til_rute=map_ra_til_rute,
        trafikkaar=trafikkaar,
        referanse_eller_tiltak="referanse"
    )
    HendelseSchema.validate(hendelser_ref)
    if trafikk_tiltak is not None:
        TrafikkGrunnlagSchema.validate(trafikk_tiltak)
        IwrapRASchema.validate(risiko_tiltak)

        # For hendelser i tiltaksbanen må vi først sjekke hvilket trafikkgrunnlag som er benyttet der.
        if "Tiltak" in risiko_tiltak.RA_trafikkgrunnlag.unique():
            # Her er det RAer der det er angitt 'tiltak' som trafikkgrunnlag
            ruter_med_alt_trafikk = risiko_tiltak.loc[
                risiko_tiltak.RA_trafikkgrunnlag == "Tiltak", "Rute"
            ].unique()
            # Henter trafikkgrunnlaget for disse fra 'trafikk_tiltak'
            oppdatert_trafikkgrunnlag = (
                trafikk_tiltak.reset_index()
                .loc[lambda x: x.Rute.isin(ruter_med_alt_trafikk)]
                .set_index(FOLSOMHET_COLS)
            )
            # Kaster samtidig disse ut fra opprinnelig trafikkgrunnlag
            opprinnelig_trafikkgrunnlag = (
                trafikk_referanse.copy()
                .reset_index()
                .loc[lambda x: ~x.Rute.isin(ruter_med_alt_trafikk)]
                .set_index(FOLSOMHET_COLS)
            )
            # Slår dem sammen
            oppdatert_trafikkgrunnlag = pd.concat(
                [oppdatert_trafikkgrunnlag, opprinnelig_trafikkgrunnlag],
                axis=0,
                sort=True,
            )
        else:
            # Ingen RA med 'tiltak' som trafikkgrunnlag. Bruker 'trafikk_referanse' for alle
            oppdatert_trafikkgrunnlag = trafikk_referanse.copy()

        # Fremskriver hendelser
        hendelser_tiltak = _fremskriv_hendelser(
            grunnlagstrafikk=oppdatert_trafikkgrunnlag,
            hendelsestrafikk=trafikk_tiltak,
            beregnet_risiko=risiko_tiltak,
            STARTAAR=ra_startaar,
            FREMTIDSAAR=ra_fremtidsaar,
            map_ra_til_rute=map_ra_til_rute,
            trafikkaar=trafikkaar,
            referanse_eller_tiltak="tiltak"
        )

        # Tvinger tiltaksomraade og tiltakspakke tilbake som int
        hendelser_tiltak = (
            hendelser_tiltak.reset_index()
            .assign(
                Tiltaksomraade=lambda df: df.Tiltaksomraade.astype(int),
                Tiltakspakke=lambda df: df.Tiltakspakke.astype(int),
            )
            .set_index(FOLSOMHET_COLS + ["Risikoanalyse", "Hendelsestype"])
        )
        hendelsesreduksjon = (
            hendelser_ref.subtract(hendelser_tiltak, fill_value=0)
        ).fillna(0)
        HendelseSchema.validate(hendelser_tiltak)
        HendelseSchema.validate(hendelsesreduksjon)
    else:
        hendelser_tiltak = None
        hendelsesreduksjon = None

    return hendelser_ref, hendelser_tiltak, hendelsesreduksjon


def _fremskriv_hendelser(
    grunnlagstrafikk,
    hendelsestrafikk,
    beregnet_risiko,
    STARTAAR: int,
    FREMTIDSAAR: int,
    map_ra_til_rute,
    trafikkaar,
    referanse_eller_tiltak: str
) -> DataFrame[HendelseSchema]:
    """Hjelpemetode som foretar fremskrivingen av beregnet_risiko basert på trafikk

    Fremskriver grunnstøtinger og kontaktskader lineært med skipenes egen trafikk, mens kollisjoner fremskrives
    først kvadratisk samlet for alle skipstypene innen hver RA, deretter fordeles kollisjonene ned på hver enkelt skipstype
    proporsjonalt med deres andel av trafikken.

    Underveis i arbeidet med SØA-modellen ble det diskutert en rekke
    ulike alternativer, og vi falt med på denne til sist. Hovedutfordringen er at vi må unngå at skip ikke
    kolliderer med andre skip som ikke lenger er der. Anta at alle andre skip enn Hurtigruta forsvant fra en ellers
    trafikkert led. Da vil Hurtigruta kollidere mye sjeldnere fordi de andre skipstypene er borte. Det er altså
    en samavhengighet mellom Hurtigrutas kollisjoner og trafikken til de andre skipstypene. Det tar vi høyde for med
    metoden vi har valgt. Totalt antall hendelser blir likt som i RA i de to RA-årene, interpoleres mellom disse
    årene og vokser med trafikken etter siste RA-år. På grunn av den proporsjonale fordelingen av hendelser, vil
    ikke antall hendelser per skipstype stemme eksakt med RA i de to RA-årene.

    Analyseenheten er analyseområdet til den enkelte risikoanalyse.
    Det er ment at dette skal samsvare med analyseområdene i SØA, men det kan ikke garaneteres med mindre
    SØA-analytiker og risikoanalytiker koordinerer analyseområdene godt. I SØA-modellen er dette håndtert ved
    at hver `rute` mappes til en, og bare en, risikoanalyse. Trafikken summeres da opp over alle rutene som dekkes
    av den enkelte RA, og dette blir da analyseenheten. Koordineringsjobben mot RA består i å definere de rutene
    som inngår i hver RA, og påse at trafikkgrunnlaget for de berørte rutene summeres opp til trafikkgrunnlaget som
    benyttes av/i RA.



    Args:
      grunnlagstrafikk: Den trafikken RAen er basert på. Vil i de aller fleste tilfeller være trafikken i referansebanen
      hendelsestrafkk: Den trafikken som skal brukes for å predikere hendelser. Vil alltid være referanse i referansebanen og tiltak i tiltaksbanen
      beregnet_risiko: Hendelsene slik beregnet i RA for de to årene STARTAAR og FREMTIDSAAR (risikoanalyseaar og ra_fremtidsaar)
      STARTAAR: Første RA-år
      FREMTIDSAAR: Andre RA-år
      trafikkar: Liste med de årene det skal gjøres fremskrives hendelser for. Disse må finnes i grunnlagstrafikken
      referanse_eller_tiltak: Hvorvidt man analyserer referanse eller tiltak, for å kunne gi gode feilmeldinger
    """

    for aar in [STARTAAR, FREMTIDSAAR]:
        if aar not in beregnet_risiko["ra_aar"].unique():
            melding = f"Finner ikke {aar} som RA-år i risikokjøringen som er gitt som input i fremskrivingen for {referanse_eller_tiltak}. "
            melding += f"Kan du ha angitt feil RA-er i arket for {referanse_eller_tiltak}banen? "
            raise KeyError(melding)

    AGG_COLS = FOLSOMHET_COLS + ["Risikoanalyse"]
    grunnlagstrafikk = (
        grunnlagstrafikk.reset_index()
        .assign(Risikoanalyse=lambda df: df.Rute.map(map_ra_til_rute))
        .groupby(AGG_COLS)[trafikkaar]
        .sum()
    )

    hendelsestrafikk = (
        hendelsestrafikk.reset_index()
        .assign(Risikoanalyse=lambda df: df.Rute.map(map_ra_til_rute))
        .groupby(AGG_COLS)[trafikkaar]
        .sum()
    )
    # Nå har vi RA på analyseomraade-nivå og trafikk på rutenivå. I FRAM3.3 og tidligere, aggregerte vi trafikken
    # opp på analyseområdenivå for å matche trafikk og RA. Fra og med FRAM3.4, der vi ønsker all verdsatt output på
    # samme format, sprer vi heller hendelsene ned på ruter. Dette gjør vi ved å benytte trafikkandelen til hver rute,
    # for hver skipstype og lengdegruppe, innad i hvert analyseomraade.
    trafikkandeler = hendelsestrafikk.groupby(
        [
            KOLONNENAVN_STREKNING,
            KOLONNENAVN_TILTAKSOMRAADE,
            KOLONNENAVN_TILTAKSPAKKE,
            "Analyseomraade",
            "Skipstype",
            "Lengdegruppe",
            "Risikoanalyse",
            FOLSOMHET_KOLONNE,
        ]
    )[trafikkaar].transform(lambda x: x / x.sum())
    beregnet_risiko = (
        beregnet_risiko.assign(Risikoanalyse=lambda df: df.Rute.map(map_ra_til_rute))
        .groupby(AGG_COLS + ["Hendelsestype", "aar"])["Hendelser"]
        .first()
        .unstack(-1)
        .reset_index()
        .set_index(AGG_COLS)
        .rename(columns={STARTAAR: f"RA_{STARTAAR}", FREMTIDSAAR: f"RA_{FREMTIDSAAR}"})
    )

    # Lag faktorer
    linear = beregnet_risiko.query(
        "Hendelsestype in ['Grunnstøting', 'Kontaktskade']"
    ).copy()
    quadratic = beregnet_risiko.query("Hendelsestype in ['Striking', 'Struck']").copy()
    predikert_linear = _fremskriv_lineart_individuell_trafikk(
        grunnlagstrafikk, hendelsestrafikk, linear, STARTAAR, AGG_COLS, trafikkaar
    )
    predikert_kvadratisk = _fremskriv_kvadratisk_aggregert_trafikk(
        grunnlagstrafikk,
        hendelsestrafikk,
        quadratic,
        STARTAAR,
        FREMTIDSAAR,
        AGG_COLS,
        trafikkaar,
    )
    # Her sprer vi etter trafikkandelene
    predikerte_hendelser = multipliser_venstre_hoyre(
        pd.concat(
            [predikert_linear, predikert_kvadratisk], axis=0, sort=True
        ).reset_index(),
        trafikkandeler.reset_index(),
        AGG_COLS,
        trafikkaar,
    ).set_index(AGG_COLS + ["Hendelsestype"])[trafikkaar]

    return predikerte_hendelser


def _fremskriv_lineart_individuell_trafikk(
    grunnlagstrafikk: DataFrame[TrafikkGrunnlagSchema],
    hendelsestrafikk: DataFrame[TrafikkGrunnlagSchema],
    beregnet_risiko: DataFrame[IwrapRASchema],
    STARTAAR: int,
    AGG_COLS: List[Union[str, int]],
    trafikkaar: List[int],
):
    """Den som skriver frem grunnstøtinger og kontaktskader, som er lineære i egen trafikk


    Disse er lineære i trafikken og avhenger kun av egen trafikk, ikke av totalen. Her må hver rad i trafikk
    være observasjoner for en enkelt skipstype og lengdegruppe, summert over alle ruter som inngår i
    den relevante RA. Beregnet risiko gjelder hver skipstype og lengdegruppe, for hver RA.
    Beregningen foretas ved å først dele antall hendelser på antall passeringer, deretter gange denne
    sannsynligheten ut for alle år.

    Args:
        grunnlagstrafikk: Gyldig trafikkgrunnlag
        hendelsestrafikk: Gyldig trafikkgrunnlag
        beregnet_risiko: Gyldig RA-grunnlag
        STARTAAR: Første RA-år
        AGG_COLS: De kolonnene det skal aggregeres over/summeres opp til
        trafikkar: Liste med de årene det skal gjøres fremskrives hendelser for. Disse må finnes i grunnlagstrafikken
    """

    hendelsestrafikk_per_ra = (
        hendelsestrafikk.reset_index().groupby(AGG_COLS)[trafikkaar].sum()
    )
    grunnlagstrafikk_per_ra = (
        grunnlagstrafikk.reset_index().groupby(AGG_COLS)[trafikkaar].sum()
    )
    koblet = (
        hendelsestrafikk_per_ra.copy()
        .merge(right=beregnet_risiko, left_index=True, right_index=True, how="left")
        .merge(
            right=grunnlagstrafikk_per_ra[[STARTAAR]].rename(
                columns={STARTAAR: f"grunnlag_{STARTAAR}"}
            ),
            left_index=True,
            right_index=True,
        )
    )

    koblet["sannsynlighet"] = koblet[f"RA_{STARTAAR}"] / koblet[f"grunnlag_{STARTAAR}"]
    predikerte_hendelser = koblet.copy()
    for year in trafikkaar:
        predikerte_hendelser[year] = (
            predikerte_hendelser["sannsynlighet"] * predikerte_hendelser[year]
        )
    predikerte_hendelser = predikerte_hendelser.reset_index().set_index(
        AGG_COLS + ["Hendelsestype"]
    )[trafikkaar]
    return predikerte_hendelser


def _fremskriv_kvadratisk_aggregert_trafikk(
    grunnlagstrafikk: DataFrame[TrafikkGrunnlagSchema],
    hendelsestrafikk: DataFrame[TrafikkGrunnlagSchema],
    beregnet_risiko: DataFrame[IwrapRASchema],
    STARTAAR: int,
    FREMTIDSAAR: int,
    AGG_COLS: List[Union[str, int]],
    trafikkaar: List[int],
):
    """Den som skriver frem kollisjoner.
    Disse er antatt kvadratiske i trafikken og avhenger av samlet trafikk. Hvert skip tilskrives kollisjoner proporsjonalt med deres andel av trafikken.

    Antall hendelser i år :math:`t, H_t = P_t*T_t`, der P_t er
    hendelsessannsynligheten i år t og T_t er trafikk i år t. Antar at
    :math:`P_t = P_startaar * ( 1 + \\beta * ( (T_t - T_startaar)/(T_fremtidsaar - T_startaar) ))`, slik at hendelsessannsynligheten er
    lineær i trafikken, og går fra P_startaar til P_fremtidsaar.
    P_t er lik P_startaar i startaar og P_fremtidsaar i fremtidsaar. Hvis vi løser dette uttrykket for :math:`\\beta` i fremtidsåret, får vi
    :math:`\\beta = (P_fremtidsaar - P_startaar)/P_startaar`


    Args:
        grunnlagstrafikk: Gyldig trafikkgrunnlag
        hendelsestrafikk: Gyldig trafikkgrunnlag
        beregnet_risiko: Gyldig RA-grunnlag
        STARTAAR: Første RA-år
        FREMTIDSAAR: Andre RA-år
        AGG_COLS: De kolonnene det skal aggregeres over/summeres opp til
        trafikkar: Liste med de årene det skal gjøres fremskrives hendelser for. Disse må finnes i grunnlagstrafikken
    """
    # Aggregerer trafikken og hendelsene over alle skipstyper og lengdegrupper
    # Kobler på grunnlagstrafikken i STARTAAR og FREMTIDSAAR for å beregne koeffisientene
    agg_trafikk = (
        hendelsestrafikk.reset_index()
        .loc[lambda x: x.Skipstype != "Annet"]
        .loc[lambda x: x.Lengdegruppe != "Mangler lengde"]
        .groupby(["Risikoanalyse", FOLSOMHET_KOLONNE])[trafikkaar]
        .sum()
    ).merge(
        right=grunnlagstrafikk.reset_index()
        .loc[lambda x: x.Skipstype != "Annet"]
        .loc[lambda x: x.Lengdegruppe != "Mangler lengde"]
        .groupby(["Risikoanalyse", FOLSOMHET_KOLONNE])[[STARTAAR, FREMTIDSAAR]]
        .sum()
        .rename(columns=lambda aar: f"grunnlag_{aar}"),
        left_index=True,
        right_index=True,
    )

    beregnet_risiko = (
        beregnet_risiko.reset_index()
        .loc[lambda x: x.Skipstype != "Annet"]
        .loc[lambda x: x.Lengdegruppe != "Mangler lengde"]
        .groupby(["Risikoanalyse", "Hendelsestype", FOLSOMHET_KOLONNE])[
            [f"RA_{STARTAAR}", f"RA_{FREMTIDSAAR}"]
        ]
        .sum()
        .reset_index()
        .set_index(["Risikoanalyse", FOLSOMHET_KOLONNE])
    )
    # Kobler disse sammen
    quadratic = agg_trafikk.copy().merge(
        right=beregnet_risiko, left_index=True, right_index=True, how="left"
    )

    # Forhåndsberegner hendelsessannsynlighetene (hendelser per passering)
    for year in [STARTAAR, FREMTIDSAAR]:
        quadratic[f"p_{year}"] = quadratic[f"RA_{year}"] / quadratic[f"grunnlag_{year}"]

    # Beta er da gitt ved formelen i docstringen
    quadratic["beta"] = (
        quadratic[f"p_{FREMTIDSAAR}"] - quadratic[f"p_{STARTAAR}"]
    ) / quadratic[f"p_{STARTAAR}"]
    # Beregnser så hendelsene hvert år ved å først beregne den kvadratiske faktoren det året, så hendelsessannsynligheten og så gange med fremskrivingstrafikken
    p_grunnlagsaar = quadratic[f"p_{STARTAAR}"]
    oppdaterte_sannsynligheter = {}
    oppdaterte_totalanslag = {}
    for year in trafikkaar:

        faktor = ((quadratic[year] - quadratic[f"grunnlag_{STARTAAR}"])/ (quadratic[f"grunnlag_{FREMTIDSAAR}"] - quadratic[f"grunnlag_{STARTAAR}"])).fillna(0)
        oppdaterte_sannsynligheter[f"p_{year}"] = (p_grunnlagsaar * (1 + quadratic["beta"] * faktor)).clip(0, 1)
        oppdaterte_totalanslag[year] = quadratic[year] * oppdaterte_sannsynligheter[f"p_{year}"]
    quadratic = pd.concat([quadratic.drop(trafikkaar, axis=1), pd.DataFrame(oppdaterte_sannsynligheter), pd.DataFrame(oppdaterte_totalanslag)], axis=1)

        #quadratic = pd.concat([quadratic.drop(trafikkaar, axis=1), pd.DataFrame(oppdaterte_sannsynligheter), pd.DataFrame(oppdaterte_totalanslag)], axis=1)
    # Regner ut trafikkandelen til det enkelte skip innen hver RA, for å fordele hendelsene ned på skipene
    trafikkandeler = hendelsestrafikk.div(
        hendelsestrafikk.groupby(["Risikoanalyse", FOLSOMHET_KOLONNE])[trafikkaar].sum()
    )[trafikkaar].rename(columns=lambda x: f"andel_{x}")

    predikerte_hendelser = quadratic.reset_index().merge(
        right=trafikkandeler.reset_index(),
        left_on=["Risikoanalyse", FOLSOMHET_KOLONNE],
        right_on=["Risikoanalyse", FOLSOMHET_KOLONNE],
        how="left",
    )
    for year in trafikkaar:
        predikerte_hendelser[year] = (
            predikerte_hendelser[year] * predikerte_hendelser[f"andel_{year}"]
        )
    predikerte_hendelser = predikerte_hendelser.reset_index().set_index(
        AGG_COLS + ["Hendelsestype"]
    )[trafikkaar]

    return predikerte_hendelser

import warnings
from typing import List

import numpy as np
import pandas as pd
import pandera as pa
from pandera.typing import DataFrame

from fram.generelle_hjelpemoduler.hjelpefunksjoner import _legg_til_kolonne
from fram.generelle_hjelpemoduler.konstanter import (
    VERDSATT_COLS,
    VIRKNINGSNAVN,
    SKATTEFINANSIERINGSKOSTNAD,
    KOLONNENAVN_VOLUMVIRKNING,
    KOLONNENAVN_VOLUM_MAALEENHET,
    FOLSOMHET_COLS,
    FOLSOMHET_KOLONNE,
)
from fram.generelle_hjelpemoduler.schemas import VolumSchema
from fram.virkninger.felles_hjelpemoduler.schemas import (
    verbose_schema_error,
)
from fram.virkninger.tid.schemas import KalkprisTidSchema
from fram.virkninger.ventetid.schemas import (
    VentetidLambdaSchema,
    VentetidMuSchema,
    PerioderAndelSchema,
    OvrigKategoriSchema,
)

SKIP_LENGDE_SPLITTER = "--"

AGG_COLS_VOLUM_VENTETID = FOLSOMHET_COLS + [
    KOLONNENAVN_VOLUMVIRKNING,
    KOLONNENAVN_VOLUM_MAALEENHET,
]


def cut_at_first_missing_obs(df, col):
    any_missing = df[col].isnull().sum() > 0
    if not any_missing:
        return df
    return df.iloc[: df[col].isnull().values.argmax()]


def hent_variabler_fra_mu(mu):
    assert (
        mu.count("_") == 2
    ), f"Her er mu-kolonnen feilspesifisert. Må være på formatet 'mu_id_retning'. Fikk {mu}"
    fikk_mu, id, retning = mu.split("_")
    assert (
        fikk_mu == "mu"
    ), f"Her er mu-kolonnen feilspesifisert. Må være på formatet 'mu_id_retning'. Fikk {mu}"
    return {"id": id, "retning": retning}


def hent_variabler_fra_lambda(lbda):
    if lbda.count("_") != 3:
        raise ValueError(
            f"Her er lambda-kolonnen feilspesifisert. Må være på formatet 'lambda_år_retning_periode'. Fikk {lbda}"
        )
    fikk_lbda, aar, periode, retning = lbda.split("_")
    if fikk_lbda != "lambda":
        raise ValueError(
            f"Her er lambda-kolonnen feilspesifisert. Må være på formatet 'lambda_år_retning_periode'. Fikk {lbda}"
        )
    try:
        aar = int(aar)
    except:
        raise ValueError(
            f"Klarte ikke lese år som heltall fra lambdakolonnen. Fikk følgende lambda-kolonne: {lbda}"
        )
    return {"aar": aar, "retning": retning, "periode": periode}


def max_or_nan(array):
    try:
        out = array.max()
    except ValueError:
        out = np.NaN
    return out


def robust_mean(array):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        out = array.mean()
    return out


def set_columns(df, kolonner):
    """ Setter kolonner som de nye kolonnene i df """
    df = df.copy()
    df.columns = kolonner
    return df


def drop_multilevel_column(df):
    df = df.copy()
    cols = [col[1] for col in df.columns]
    df.columns = cols
    return df


def split_ship_id(df, new_cols=["Skipstype", "Lengdegruppe"]):
    index_cols = list(df.index.names)
    index_cols.remove("ship_id")
    df = df.reset_index().copy()
    df = df.merge(
        right=(
            df["ship_id"]
            .str.split(SKIP_LENGDE_SPLITTER, expand=True)
            .pipe(set_columns, new_cols)
        ),
        left_index=True,
        right_index=True,
    )
    return df.set_index(new_cols + index_cols).drop("ship_id", axis=1)


def _fordel_ovrig(
    rute: str,
    trafikkgrunnlag: pd.DataFrame,
    skip_i_ovrig: pd.DataFrame,
    ventetid: pd.DataFrame,
    beregningsaar: List[int],
    logger=print,
):
    """Hjelpefunksjon for å spre ut "øvrig-kategrien" i ventetidsinputen utover de riktige skipstypene proporsjonalt med deres faktiske trafikkgrunnlag

    Args
    rute: Hvilken rute ventetidssituasjonen ligger på
    trafikkgrunnlag: Gyldig trafikkgrunnlag som er representativt for denne ruten og ventetidssituasjonen
    skip_i_ovrig: Hvilke skip som inngår i øvrig
    ventetid: Dataframe med totale ventetider per skipstype og lengedgruppe, herunder øvrig-kategorien
    """
    trafikk_aktuell_rute = (
        trafikkgrunnlag.reset_index()
        .loc[lambda df: df.reset_index()["Rute"] == rute]
        .drop(
            columns=[
                "Strekning",
                "Tiltaksomraade",
                "Tiltakspakke",
                "Analyseomraade",
                "Rute",
            ]
        )
        .set_index([FOLSOMHET_KOLONNE, "Skipstype", "Lengdegruppe"])
        .rename(columns=lambda x: f"trafikk_{x}")
        .reset_index()
    )
    ventetid = ventetid.reset_index()

    # Behandler først de skip- og lengdegrupper som er spesifisert i inputarket
    spes_koblet = trafikk_aktuell_rute[
        [FOLSOMHET_KOLONNE, "Skipstype", "Lengdegruppe"]
    ].merge(ventetid, on=["Skipstype", "Lengdegruppe"], how="inner")

    # Fordeler øvrig-kategorien på spesifiserte skip- og lengdegrupper som finnes i trafrikkgrunnlaget
    # Kobler først liste med skip som inngår i øvrig-kategorien, spesifisert i input-arket, med trafikkgrunnlag på ruten
    skip_i_ovrig = trafikk_aktuell_rute.merge(
        skip_i_ovrig, on=["Skipstype", "Lengdegruppe"], indicator=True, how="right"
    )
    manglende_skip_ventetid_trafikk = (
        len(skip_i_ovrig)
        - skip_i_ovrig.loc[skip_i_ovrig["_merge"] == "both"].count()[0]
    )
    if manglende_skip_ventetid_trafikk > 0:
        logger(
            f"Feilmelding: Det er {manglende_skip_ventetid_trafikk} skip som har blitt borte mellom ventetidsberegningen og koblingen mot trafikkgrunnlaget. Har du benyttet feil trafikkgrunnlag? Eller plassert ventetidssituasjonen i feil rute? Du har brukt ruten {rute}. Dette tallet burde være null."
        )

    # Kobler med ventetid - ønsker å beholde
    ovrig_koblet = (
        skip_i_ovrig.loc[skip_i_ovrig["_merge"] == "both"]
        .drop(columns="_merge")
        .merge(
            ventetid[["Skipstype", "Lengdegruppe"]],
            on=["Skipstype", "Lengdegruppe"],
            how="left",
        )  # Sjekk denne er riktig
        .assign(ny_merge_skipstype="Øvrige fartøy")
        .assign(ny_merge_lengdegruppe="Alle")
        .merge(
            ventetid,
            left_on=["ny_merge_skipstype", "ny_merge_lengdegruppe"],
            right_on=["Skipstype", "Lengdegruppe"],
        )
        .drop(columns=["Skipstype_y", "Lengdegruppe_y"])
        .rename(columns={"Skipstype_x": "Skipstype", "Lengdegruppe_x": "Lengdegruppe"})
    )

    for year in beregningsaar:
        ovrig_koblet[year] = (
            ovrig_koblet.set_index([FOLSOMHET_KOLONNE, "Skipstype", "Lengdegruppe"])[
                f"trafikk_{year}"
            ]
            / ovrig_koblet.groupby(FOLSOMHET_KOLONNE)[f"trafikk_{year}"].sum()
            * ovrig_koblet.set_index([FOLSOMHET_KOLONNE, "Skipstype", "Lengdegruppe"])[
                f"tot_ventetid_{year}"
            ].values
        ).values

    tot_ventetid_alle = (
        ovrig_koblet[[FOLSOMHET_KOLONNE, "Skipstype", "Lengdegruppe"] + beregningsaar]
        .set_index([FOLSOMHET_KOLONNE, "Skipstype", "Lengdegruppe"])
        .rename(columns=lambda x: f"tot_ventetid_{x}")
        .reset_index()
        #.append(spes_koblet, sort=True)
    )
    tot_ventetid_alle = pd.concat([tot_ventetid_alle, spes_koblet], axis=0, sort=True)

    return tot_ventetid_alle


def _fordel_og_prep_ventetid(
    trafikkgrunnlag,
    ovrig_kategori,
    total_ventetid,
    beregningsaar,
    metadatakolonner,
    logger,
):
    rute = metadatakolonner["Rute"].values[0]
    return (
        _fordel_ovrig(
            rute=rute,
            trafikkgrunnlag=trafikkgrunnlag,
            skip_i_ovrig=ovrig_kategori,
            ventetid=total_ventetid,
            beregningsaar=beregningsaar,
            logger=logger,
        )
        .assign(Rute=rute)
        .merge(right=metadatakolonner, on="Rute", how="left")
        .pipe(_legg_til_kolonne, KOLONNENAVN_VOLUMVIRKNING, "Ventetid")
        .pipe(_legg_til_kolonne, KOLONNENAVN_VOLUM_MAALEENHET, "Timer")
        .set_index(AGG_COLS_VOLUM_VENTETID)
        .rename(
            columns=lambda s: int(s.strip("tot_ventetid_"))
            if "tot_ventetid_" in s
            else s
        )[beregningsaar]
    )


@verbose_schema_error
@pa.check_types(lazy=True)
def _beregn_tot_ventetid(
    lambda_df: DataFrame[VentetidLambdaSchema],
    perioder_andel: DataFrame[PerioderAndelSchema],
    snittventetid,
    tidsenhet,
):
    lambda_df = lambda_df.merge(right=perioder_andel, on="periode", how="left").rename(
        columns=lambda col: f"lambda_{col}" if str(col).isnumeric() else col
    )
    # Ganger lambda med andeler, tidsenheter og antall døgn for å få trafikk i løpet av året
    skal_ganges_sammen = lambda_df.columns.where(
        lambda_df.columns.str.contains("lambda")
    ).dropna()  # Liste er kun liste over alle variablene som skal ganges sammen
    lambda_df[skal_ganges_sammen] = (
        lambda_df[skal_ganges_sammen].multiply(lambda_df["andel"], axis="index")
        * tidsenhet
        * 365
    )

    # Merger på trafikk for å estimere total ventetid
    trafikk_til_ventetid = lambda_df.drop(columns=["andel"])

    ventetid_per_tidsenhet = snittventetid.rename(
        columns=lambda x: f"ventetid_per_tidsenhet_{x}"
    ).reset_index()

    koblet = ventetid_per_tidsenhet.merge(
        right=trafikk_til_ventetid, on=["Skipstype", "Lengdegruppe", "periode"]
    )

    beregnings_aar = [
        str(col).strip("lambda_") for col in lambda_df.columns if "lambda" in str(col)
    ]
    for year in beregnings_aar:
        koblet[year] = (
            koblet[f"ventetid_per_tidsenhet_{year}"] * koblet[f"lambda_{year}"]
        )

    total_ventetid = (
        koblet.reset_index()
        .set_index(["Skipstype", "Lengdegruppe", "periode"])[beregnings_aar]
        .rename(columns=lambda x: f"tot_ventetid_{x}")
        .reset_index()
        .fillna(0)
        .groupby(["Skipstype", "Lengdegruppe"])
        .sum()  # Summerer på tvers av tidsperioder
    )

    return total_ventetid


@verbose_schema_error
@pa.check_types(lazy=True)
def _verdsett_ventetid(
    ventetid: DataFrame[VolumSchema],
    kalkpris_ventetid: DataFrame[KalkprisTidSchema],
    beregningsaar: List[int],
    virkningsnavn="Endring i ventetidskostnader",
):
    """
    Verdsetter ventetiden, dersom denne finnes. Benytter de samme verdsettingsfaktorene som for tid for øvrig.

    Består kun av multiplisering av den beregnede ventetiden med verdsettingsfaktorene.

    Skriver de verdsatte bruttoventetidene i referanse- og tiltaksbanen til henholdsvis `FRAM.kr_ventetid_ref` og `FRAM.kr_ventetid_tiltak`.

    Returns:
        Pandas DataFrame med differansen i verdsatt ventetid for hver skipstype, lengdegruppe og rute.
    """

    kalkpris_ventetid = (
        kalkpris_ventetid.set_index(["Skipstype", "Lengdegruppe", FOLSOMHET_KOLONNE])
        .rename(columns=lambda x: f"kalkpris_{x}")
        .reset_index()
    )

    # verdsetter referansebanen
    koblet = ventetid.reset_index().merge(
        kalkpris_ventetid,
        on=["Skipstype", "Lengdegruppe", FOLSOMHET_KOLONNE],
        how="left",
    )
    for year in beregningsaar:
        koblet[year] = koblet[year] * koblet[f"kalkpris_{year}"]
    return (
        koblet.pipe(_legg_til_kolonne, VIRKNINGSNAVN, virkningsnavn)
        .pipe(_legg_til_kolonne, SKATTEFINANSIERINGSKOSTNAD, 0)
        .set_index(VERDSATT_COLS)[beregningsaar]
    )


class Output:
    def __init__(self, year, period, data):
        self.year = year
        self.period = period
        self.data = data


class SimuleringsInput:
    @verbose_schema_error
    @pa.check_types(lazy=True)
    def __init__(
        self,
        lambda_df: DataFrame[VentetidLambdaSchema],
        mu_df: DataFrame[VentetidMuSchema],
        alpha: List[float],
        mulige_lop: List[str],
        aar: List[int],
        perioder_for_sim: List[str],
        perioder_andel: DataFrame[PerioderAndelSchema],
        ovrig_kategori: DataFrame[OvrigKategoriSchema],
        tidsenhet: float,
        num_periods: int,
    ):
        for lop in mulige_lop:
            if not lop in mu_df.columns:
                raise KeyError(
                    f"Fant ikke {lop} som kolonne i 'mu_df'. Da kan ikke simuleringen kjøre"
                )
        self.lambda_df = lambda_df
        self.mu_df = mu_df
        self.alpha = alpha
        self.mulige_lop = mulige_lop
        self.aar = aar
        self.perioder_for_sim = perioder_for_sim
        self.perioder_andel = perioder_andel
        self.ovrig_kategori = ovrig_kategori
        self.tidsenhet = tidsenhet
        self.num_periods = num_periods
        self.validate()

    def _hash_df(self, df_name_on_self):
        return str(pd.util.hash_pandas_object(getattr(self, df_name_on_self)).sum())

    @property
    def _hash_string(self):
        """ Hashed representation of all the attributes on self"""
        return "".join(
            [
                self._hash_df("lambda_df"),
                self._hash_df("mu_df"),
                self._hash_df("perioder_andel"),
                self._hash_df("ovrig_kategori"),
                "".join([str(el) for el in self.alpha]),
                "".join(self.mulige_lop),
                "".join([str(el) for el in self.aar]),
                "".join(self.perioder_for_sim),
                str(self.tidsenhet),
                str(self.num_periods),
            ]
        )

    def __repr__(self):
        return "Simuleringsinput"

    def validate(self):
        assert self.alpha
        assert self.mulige_lop
        assert self.aar
        assert self.perioder_for_sim
        assert self.num_periods

        VentetidLambdaSchema.validate(self.lambda_df)
        VentetidMuSchema.validate(self.mu_df)

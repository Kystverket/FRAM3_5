import shelve
from multiprocessing import cpu_count
from multiprocessing.pool import Pool
from pathlib import Path
from typing import Union, List, Callable

import numpy as np
import pandas as pd

from fram.virkninger.ventetid.computation import (
    simulate_multiship_multiple_bottlenecks_two_directions,
)
from fram.virkninger.ventetid.hjelpemoduler import (
    cut_at_first_missing_obs,
    SKIP_LENGDE_SPLITTER,
    set_columns,
    Output,
    SimuleringsInput,
)
from fram.generelle_hjelpemoduler.excel import vask_kolonnenavn_for_exceltull

MAKS_ANTALL_LØP = 15
SKIPROWS_FØR_MU_OG_LAMBDA = 18 + MAKS_ANTALL_LØP
SKIPROWS_FØR_LØP_OG_ALPHA = 13
SKIPROWS_FØR_DEFINISJONER = 7
PERIODETABELL_STARTKOLONNE = 5
LAMBDA_DF_STARTKOLONNE = 9 + MAKS_ANTALL_LØP
OVRIG_TABELL_STARTKOLONNE = 4 + MAKS_ANTALL_LØP


def les_ventetidsinput_fra_excel(
    filepath: Union[str, Path], sheet_name: str, num_periods: int = 100_000,
) -> SimuleringsInput:
    """Funksjon for å lese inn ventetidsinput fra et formatert Excel-ark.

    Det er strenge regler for formatering av Excel-arket. Det ligger eksempler både her under virkninger/ventetid/tests,
    og sammen med øvrige eksempelanalyser for FRAM. Arket trenger ikke bo i en FRAM-bok, men kan gjøre det.
    Når arket er lest inn, kan output fra funksjonen mates inn i simuleringsfunksjonen
    :meth:`simulate_from_simuleringsinput` eller :meth:`cached_simulate_from_simuleringsinput`

    Args:
        filepath: Bane til filen der ventetidsarket ligger
        sheet_name: Arknavnet til ventetidsarket
        seed: Seed til generatoren av pseudotilfeldige tall
        num_periods: Antall perioder det skal simuleres over. Defaulter til 100 000
        logger: Hvor du vil ha logget underveis. Defaulter til print
    """

    # Leser inn overordnede definisjoner som en dict. Har keys 'Tiltakspakke', 'Problemområde_id' og 'Antall løp'
    definisjoner = pd.read_excel(
        filepath, sheet_name, usecols=[0, 1], skiprows=SKIPROWS_FØR_DEFINISJONER
    ).iloc[:3]
    definisjoner = dict(
        zip(definisjoner.iloc[:, 0].values, definisjoner.iloc[:, 1].values)
    )

    # Leser inn de mulige løpene og deres alpha
    lopsnummer = (
        pd.read_excel(
            filepath, sheet_name, usecols=[0, 1], skiprows=SKIPROWS_FØR_LØP_OG_ALPHA
        )
        .pipe(cut_at_first_missing_obs, "Løpnummer")
        .sort_values(by="Løpnummer")
    )
    mulige_lop = sorted(list(lopsnummer["Løpnummer"].dropna().values))
    alpha = list(lopsnummer["Alpha"].dropna().values)
    assert len(alpha) == len(
        mulige_lop
    ), f"Noe er galt med tabellen med løpnummer. Ikke like mange alpha og løpnummer?"
    assert (
        len(mulige_lop) == definisjoner["Antall løp"]
    ), f"Antall løp fra tabellen med løpnummer ({len(mulige_lop)}) matcher ikke angitt antall løp i celle B10 ({definisjoner['Antall løp']})"

    retninger = (
        pd.read_excel(
            filepath,
            sheet_name,
            usecols=[3],
            skiprows=SKIPROWS_FØR_LØP_OG_ALPHA,
            nrows=3,
        )
        .pipe(cut_at_first_missing_obs, "Retninger")
        .to_dict(orient="list")["Retninger"]
    )

    assert (
        len(retninger) <= 2
    ), f"Kan ha maksimalt to retninger, fant {len(retninger)} i tabellen i cellene D14:D16"

    perioder = (
        pd.read_excel(
            filepath,
            sheet_name,
            usecols=[5, 6],
            skiprows=SKIPROWS_FØR_LØP_OG_ALPHA,
            nrows=6,
        )
        .pipe(cut_at_first_missing_obs, "Periode")
        .pipe(set_columns, ["periode", "andel"])
    )

    assert np.isclose(
        perioder["andel"].sum(), 1, atol=0.01
    ), f"De ulike periodenes andeler av året må summeres til 1 (cellene G15:G20)"
    assert len(perioder.periode.unique()) == len(
        perioder.periode
    ), f"Du har gjentatt minst en periode mer enn en gang (cellene F15:F20)"

    # Leser inn mu fra tabellen og lager en matrise klar for simulering
    use_cols_mus = list(range(3 + definisjoner["Antall løp"]))
    mu_df = (
            pd.read_excel(
                filepath,
                sheet_name=sheet_name,
                usecols=use_cols_mus,
                skiprows=SKIPROWS_FØR_MU_OG_LAMBDA,
            )
            .pipe(vask_kolonnenavn_for_exceltull)
            .pipe(
                cut_at_first_missing_obs, "Skipstype"
            )  # Kutter ved første manglende skipstype
            .dropna(axis="columns", how="all")
            .assign(
                ship_ids=lambda df: df.Skipstype
                + SKIP_LENGDE_SPLITTER
                + df.Lengdegruppe
            )
            .sort_values(by="ship_ids")
        ).rename(columns={"Retning": "direction"})

    mu_cols = [col for col in mu_df.columns if "mu" in str(col)]
    mu_df.columns = [str(col).replace("mu_", "") for col in mu_df.columns.tolist()]
    mu_ids = sorted([col.replace("mu_", "") for col in mu_cols])
    assert (
        mu_ids == mulige_lop
    ), f"Ikke samsvar mellom mulige løpsnumre (rad 13) ({mulige_lop}) og løpsnumre utlest fra tabellen (rad og utover) ({mu_ids})"

    ship_ids = sorted(mu_df.ship_ids.unique())

    # Starter på lambda-innlesingen

    lambda_df = (pd.read_excel(
                    filepath,
                    sheet_name=sheet_name,
                    skiprows=SKIPROWS_FØR_MU_OG_LAMBDA)
                    .iloc[: , LAMBDA_DF_STARTKOLONNE:]
            .pipe(vask_kolonnenavn_for_exceltull)
            .pipe(
                cut_at_first_missing_obs, "Skipstype"
            )  # Kutter ved første manglende skipstype
            .dropna(axis="columns", how="all")
            .assign(
                ship_ids=lambda df: df.Skipstype
                + SKIP_LENGDE_SPLITTER
                + df.Lengdegruppe
            )
            .sort_values(by="ship_ids")
    )
    

    aar = [
        str(col).strip("lambda_") for col in lambda_df.columns if "lambda" in str(col)
    ]
    lambda_df = (
        lambda_df.rename(columns={"Retning": "direction", "Periode": "periode"})
        .rename(columns=lambda col: str(col).replace("lambda_", ""))
        .sort_values(by=["ship_ids", "direction"])
        .dropna(subset=aar, how="all")
    )
    lambda_df[aar] = lambda_df[aar].astype(float)
    lambda_ship_ids = sorted(lambda_df.ship_ids.unique())

    assert (
        ship_ids == lambda_ship_ids
    ), f"Det er ikke samsvar mellom mu og lambda i inputarket {filepath} {sheet_name}"

    tidsenhet = float(
        pd.read_excel(filepath, sheet_name, usecols=[1], skiprows=10).values[0][0]
    )

    ovrig_kategori = (
        pd.read_excel(
            filepath,
            sheet_name,
            usecols=list(
                range(OVRIG_TABELL_STARTKOLONNE, OVRIG_TABELL_STARTKOLONNE + 2)
            ),
            skiprows=SKIPROWS_FØR_MU_OG_LAMBDA,
        )
        .pipe(vask_kolonnenavn_for_exceltull)
        .pipe(
            cut_at_first_missing_obs, "Skipstype"
        )  # Kutter ved første manglende skipstype
    )

    perioder_for_sim = sorted(
        list(set(perioder.periode.values).intersection(set(lambda_df.periode.values)))
    )

    if len(perioder_for_sim) == 0:
        raise ValueError(
            "Ingen overlapp mellom periodene i celle F15:F20 og periodene i kolonne AB. Er de kanskje feilstavet?"
        )

    return SimuleringsInput(
        lambda_df=lambda_df,
        mu_df=mu_df,
        alpha=alpha,
        mulige_lop=mulige_lop,
        aar=aar,
        perioder_for_sim=perioder_for_sim,
        tidsenhet=tidsenhet,
        ovrig_kategori=ovrig_kategori,
        perioder_andel=perioder,
        num_periods=num_periods,
    )


def simulate_excel(
    filepath: Union[str, Path], sheet_name: str, num_periods: int = 100_000,
):
    sim_input = les_ventetidsinput_fra_excel(
        filepath=filepath, sheet_name=sheet_name, num_periods=num_periods,
    )
    return simulate_from_simuleringsinput(sim_input)


def simulate_from_simuleringsinput(
    sim_input: SimuleringsInput, seed: int = 1
) -> List[Output]:
    """Kjører en simulering av ventetidsberegning. I utgangspunktet kun ment å benyttes av :class:'~fram.virkninger.ventetid.ventetidssituasjon.Ventetidssituasjon'

    Kan benyttes alene, men det anbefales ikke, fordi den gir output som kan være vanskelig å tolke. Den omtalte klassen
    `Ventetidssituasjon` gir output på et lettere tolkbart format. Ved simulering, benyttes funksjonen
    :meth:`~fram.virkninger.ventetid.computation.simulate_multiship_multiple_bottlenecks_two_directions`

    Args:
        sim_input: En gyldig simuleringsinput.
        seed: Seed til generatoren av pseudotilfeldige tall
    """
    keep_cols = ["ship_ids", "Skipstype", "Lengdegruppe", "direction", "periode"]
    common_input_args = (
        sim_input.lambda_df,
        sim_input.mu_df,
        sim_input.mulige_lop,
        sim_input.alpha,
        sim_input.num_periods,
        keep_cols,
        seed,
    )

    args = [
        (year, periode,) + common_input_args
        for year in sim_input.aar
        for periode in sim_input.perioder_for_sim
    ]
    # Prøver multiprosessering først
    try:
        with Pool(cpu_count() - 1) as p:
            outputs = p.map(_sim_unit_unpack_args, args)
    except:
        outputs = [_sim_unit_unpack_args(arg) for arg in args]
    return outputs


def cached_simulate_from_simuleringsinput(
    sim_input: SimuleringsInput, seed: int = None, logger: Callable = print
) -> List[Output]:
    """En wrapper rundt simulate_from_simuleringsinput som sjekker om input er likt som forrige gang. I så fall henter den bare ferdiglagret output i stedet for å kjøre simuleringene på nytt"""
    # Lager først en hash - altså en unik streng - for all input. Hvis input er lik, er hashen lik
    current_path = Path(__file__).parent
    shelve_path = current_path / "mellomlagret_ventetid"
    lookup_string = f"{sim_input._hash_string}-{str(seed)}-{str(sim_input.num_periods)}"

    # Sjekker så om dette inputarket allerede har en mellomlagret ventetidsberegning. Bruker i så fall den
    with shelve.open(str(shelve_path)) as db:
        try:
            output = db[lookup_string]
            logger(
                f"Simuleringsinputen er lik som en tidligere input. Benytter mellomlagret ventetidsberegning i {shelve_path}"
            )
        except:
            logger(
                f"Fant ikke mellomlagret ventetidsberegning som kunne benyttes. Beregner på nytt. Skal simulere over {len(sim_input.aar)} år og {len(sim_input.perioder_for_sim)} perioder hvert år"
            )
            # Beregner da manuelt
            output = simulate_from_simuleringsinput(sim_input, seed=seed)
            # Skriver til mellomlagringen
            db[lookup_string] = output

    return output


def _sim_unit_unpack_args(args):
    """Hjelpefunksjon for hjelpefunksjonen for simulering. Eneste funksjon er å pakke ut argumentene fra en tuple"""
    return _sim_unit(*args)


def _sim_unit(
    year, periode, lambda_df, mu_df, mulige_lop, alpha, periods, keep_cols, seed
):
    """Hjelpefunksjon som kjører simuleringen for ett år og en periode. Skilt ut for å kunne parallelliseres"""
    # Tar bare med de skipene som har positiv lambda
    sim_df = (
        lambda_df.loc[
            (lambda_df.periode == periode) & (lambda_df[year] > 0), keep_cols + [year]
        ]
        .copy()
        .merge(
            right=mu_df,
            on=["Skipstype", "Lengdegruppe", "direction", "ship_ids"],
            how="left",
        )
    )
    mus = sim_df[mulige_lop].values

    data = simulate_multiship_multiple_bottlenecks_two_directions(
        lbdas=sim_df[year].values,
        ship_ids=sim_df["ship_ids"].values,
        directions=sim_df["direction"].values,
        alpha=alpha,
        mus=mus,
        bottleneck_ids=mulige_lop,
        num_periods=periods,
        seed=seed,
    )
    output = Output(year, periode, data)

    return output

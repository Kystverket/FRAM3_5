from typing import Optional, List

import pandas as pd

from fram.virkninger.ventetid.excel import (
    cached_simulate_from_simuleringsinput,
)
from fram.virkninger.ventetid.hjelpemoduler import (
    drop_multilevel_column,
    split_ship_id,
    _beregn_tot_ventetid,
    Output,
    SimuleringsInput,
)

NUM_PERIODS = 100_000
SEED = 1


class Ventetidssituasjon:
    def __init__(
        self,
        simuleringsinput_ref: SimuleringsInput,
        simuleringsinput_tiltak: Optional[SimuleringsInput] = None,
        seed: int = 1,
        logger=print,
    ):
        """
        Beholder for ventetidsberegninger og wrapper rundt de underliggende kø-algoritmene. Output sammenstilles
        på klassen. Algoritmen som benyttes er :meth:`~fram.ventetid.computation.simulate_multiship_multiple_bottlenecks_two_directions`.

        Modellen kan benyttes frittstående på enten referanseinput eller både referanse- og tiltaksinput, men er primært
        ment benyttet som et ledd i de samfunnsøkonomiske beregningene. Modellen kalles på av den dedikerte virkningen
        :class:`~fram.virkninger.ventetid.virkning.Ventetid`
        gjennom metoden :meth:`~fram.fram.FRAM.beregn_ventetid`.

        Alle relevante metoder kjøres ved init. Den mest relevante outputen ligger på `Ventetidssituasjon.total_ventetid_ref` og
        `Ventetidssituasjon.total_ventetid_tiltak`.

        Det foretas ingen verdsetting i denne modellen, det gjennomføres i virkningen.

        Modellen mellomlagrer alle beregninger basert på innholdet inputen den gis, hvilken seed som settes og antall perioder som simuleres. Det vil si at så lenge disse tre beholdes uendret, vil modellen bare slå opp i en katalog over ferdigberegnede kjøringer og returnere denne.
        """
        self.logger = logger
        self.periode_andel = simuleringsinput_ref.perioder_andel

        self._output_ref = cached_simulate_from_simuleringsinput(
            sim_input=simuleringsinput_ref, seed=seed, logger=self.logger
        )
        self.tidsenhet_ref = simuleringsinput_ref.tidsenhet
        self._common_df_ref = self._build_common_df(self._output_ref)
        self.mean_wait_time_ref = self._get_df_ship("ref", "mean_wait_time_per_ship")
        self.total_ventetid_ref = _beregn_tot_ventetid(
            simuleringsinput_ref.lambda_df,
            simuleringsinput_ref.perioder_andel,
            self.mean_wait_time_ref,
            self.tidsenhet_ref,
        )
        self.ventesit_over_ett_minutt_antall_per_periode_ref = (
            self._get_yearly_common_df("ref", "waiting_incidents_per_period_just")
        )
        self.ventesit_over_ett_minutt_varighet_ref = self._get_yearly_common_df(
            "ref", "mean_wait_time_just"
        )

        if simuleringsinput_tiltak is not None:
            self._output_tiltak = cached_simulate_from_simuleringsinput(
                sim_input=simuleringsinput_tiltak, seed=seed, logger=self.logger
            )
            self.tidsenhet_tiltak = simuleringsinput_tiltak.tidsenhet
            self._common_df_tiltak = self._build_common_df(self._output_tiltak)
            self.mean_wait_time_tiltak = self._get_df_ship(
                "tiltak", "mean_wait_time_per_ship"
            )
            self.total_ventetid_tiltak = _beregn_tot_ventetid(
                simuleringsinput_tiltak.lambda_df,
                simuleringsinput_tiltak.perioder_andel,
                self.mean_wait_time_tiltak,
                self.tidsenhet_tiltak,
            )
            self.ventesit_over_ett_minutt_antall_per_periode_tiltak = (
                self._get_yearly_common_df(
                    "tiltak", "waiting_incidents_per_period_just"
                )
            )
            self.ventesit_over_ett_minutt_varighet_tiltak = self._get_yearly_common_df(
                "tiltak", "mean_wait_time_just"
            )

    def _build_common_df(self, output: List[Output]):
        df = [
            pd.DataFrame.from_dict(o.data).assign(aar=o.year, periode=o.period)
            for o in output
        ]
        return pd.concat(df)

    def _get_df_common(self, tiltak):
        attr_name = f"_common_df_{tiltak}"
        if not hasattr(self, attr_name):
            setattr(
                self,
                attr_name,
                self._build_common_df(getattr(self, f"_output_{tiltak}")),
            )
        return getattr(self, attr_name)

    def _get_df_ship(self, tiltak, variable):
        df = (
            self._get_df_common(tiltak)[[variable, "aar", "periode"]]
            .reset_index()
            .rename(columns={"index": "ship_id"})
            .merge(
                right=self.periode_andel,
                left_on="periode",
                right_on="periode",
                how="left",
            )
            .loc[lambda df: df.ship_id.str.contains("--")]
            .set_index(["ship_id", "periode", "andel", "aar"])
            .unstack()
            .pipe(drop_multilevel_column)
            .dropna(subset=["2018"])
            .pipe(split_ship_id)
        )

        return df

    def _get_df_bottleneck(self, tiltak, variable):
        df = (
            self._get_df_common(tiltak)[[variable, "aar", "periode"]]
            .reset_index()
            .rename(columns={"index": "bottleneck_id"})
            .set_index(["bottleneck_id", "periode", "aar"])
            .unstack()
            .pipe(drop_multilevel_column)
            .dropna(subset=["2018"])
        )

        return df

    def _get_df_agg(self, tiltak, variable):
        df = (
            self._get_df_common(tiltak)
            .reset_index()
            .drop_duplicates(subset=["aar", "periode"])
            .set_index(["aar", "periode"])[variable]
            .sort_index()
        )

        return df

    def _get_yearly_common_df(self, tiltak, variable):
        df = (
            self._get_df_common(tiltak)[["periode", "aar", variable]]
            .drop_duplicates(subset=["periode", "aar"])
            .reset_index()
            .drop("index", axis="columns")
            .set_index(["periode", "aar"])
            .unstack()
            .pipe(drop_multilevel_column)
        )

        return df

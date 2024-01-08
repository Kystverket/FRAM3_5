"""
Inneholder en rekke ulike funksjoner for å simulere køer, avhengig av om du har én skipstype eller flere, én flaskehals eller flere, om skipene kommer i én retning (som vil være tilfellet hvis du modellerer en kai) eller to (som vil være tilfellet i et trangt sund.)

De enkelte funksjonene bygger alle på den samme underliggende algoritmen, som er forklart her. I tillegg er hver enkelt funksjon dokumentert for seg.

I "vanlig" bruk vil man som oftest benytte kømodellen slik den er gjort tilgjengelig for SØA-modellen. Denne er dokumentert separat og grundig for seg.

Algoritmen er basert på Queue departure computation (Ebert & al., 2017), som finnes her: https://arxiv.org/abs/1703.02151

1. Det trekkes en lang vektor med tilfeldig tid mellom hvert anløp, `interarrival_times`, simulert for hver skipstype, basert på deres lambda (som angir forventet antall anløp per tidsenhet for den enkelte skipstype)
2. Vi regner ut anløpstidene som den kumulative summen av tid mellom hvert anløp, `arrival_times`
3. Dette settes sammen til en dataframe, som så stables oppå hverandre for alle skipstyper og lengdegrupper, til en kjempelang dataframe
4. Denne sorteres deretter etter anløpstid, slik at alle skipene ligger kronologisk i den rekkefølgen de anløper, med tilhørende anløpstid
5. Vi klipper denne nedenfra slik at de skipene, som et resultat av den tilfeldige simuleringen, anløper etter simuleringsperioden (for eksempel 10 000 dager), klippes vekk. Vi står da igjen med alle de skipene som anløper innenfor simuleringsperioden.
6. Vi trekker gjennomseilingstid, `service_times` for hvert skip, basert på de angitte myene (enten lik for alle skip, skipsavhengig eller skips- og flaskehalsavhengig). `mu` angir forventet antall skip som kan håndteres av flaskehalsen per tidsperiode.
7. For at det skal gå raskere å gjennomføre køsimuleringen, setter vi opp en rekke tomme vektorer med riktig lengde. Da holder datamaskinen av minne til å fylle disse raskt med innhold etterpå. I tilfellet flere skip, flere flaskehalser og mulig rabatt ved å seile etter hverandre i samme retning, gjelder dette `service_start_times`, `service_times`, `completion_times`, `bottleneck_chosen`, `bottleneck_busy_until` og `last_ship_direction`.
8. Vi looper over hver anløp og beregner ventetid. Dette gjøres på følgende måte:
   a. Et skip som anløper, velger den flaskehalsen (hvis flere) som har en gjennomseilingstid slik at skipet først blir ferdig. Det kan være den med kortest gjennomseilingstid hvis ingen kø, eller en med lengre gjennomseilingstid hvis køen der er tilstrekkelig kort til at det er bedre å seile lenger for å slippe å vente, eller dersom det kan seile tett på skipet foran seg der, men må vente på et skip i motgående retning et annet sted. Valgt flaskehals omtales som `bottleneck_chosen`.
   b. Skipets `service_start_time` blir da det tidspunktet det kan begynne å seile gjennom flaskehalsen. Det er det tidspunktet som kommer sist i tid av 1) når skipet kommer til ventestedet, og 2) når flaskehalsen blir ledig
   c. Den valgte flaskehalsen blir da opptatt til skipet har seilt gjennom, potensielt korrigert for at neste skip kan seile før du er helt gjennom, dersom dette kommer i samme retning. Dette betegnes som `bottleneck_busy_until`, og er det som bestemmer om det oppstår kø: Dersom `bottleneck_busy_until` er senere enn anløpstidspunktet til det neste skipet, må det neste skipet vente. Når mange skip kommer tett etter hverandre, vil det hope seg opp kø, og det er lenge til flaskehalsen blir ledig.
   d. Skipet er ferdig behandlet når det har seilt gjennom flaskehalsen. Lagres som `completion_times`.
   e. Total tid for skipet gjennom ventetidsområdet (`total_times`) blir da `completion_times` minus `arrival_times`, mens ventetiden blir total tid fratrukket gjennomseilingstiden: `wait_times` = `total_times` - `service_times`.

Denne algoritmen gjøres litt enklere dersom det bare er en skipstype, bare en flaskehals, bare en retning eller det
ikke gis rabatt for å seile i samme retning. Grunnalgoritmen er likevel den samme.

"""
from typing import List, Optional, Union

import numpy as np
import pandas as pd

from fram.virkninger.ventetid.hjelpemoduler import (
    max_or_nan,
    robust_mean,
    SKIP_LENGDE_SPLITTER,
)

SHIP_SEPARATOR = "--"
MU_ZERO_REPLACEMENT = 1e-8


def simulate_single_ship_single_bottleneck(
    lbda: float, mu: float, num_periods: int = 10_000, threshold: float = 0.0
):
    """
    Simulerer en kø med én type skip og én flakehals
    
    Denne implementeringen avviker fra den generelle algoritmen ved at det kun tillates ett skip, én flaskehals og én retning. Skipet kan da ikke velge flaskehals, og det er ingen forskjell på skip i ulike retninger.


    Args:
        lbda: Angir gjennomsnittlig antall anløp per tidsenhet. Anløpene vil være Poisson-fordelt i modellen, det vil si at det i gjennomsnitt er like lang tid mellom hvert anløp
        mu: Angir hvor mange skip som kan behandles av flaskehalsen per tidsenhet (seile gjennom hvis en trang farled, losses i havn hvis det er en kai, etc.)
        num_periods: Hvor mange perioder du ønsker å simulere. For at de store talls lov skal gjelde må du kjøre mer enn én periode. Anbefaler minst 10 000, som er default
        threshold: En terskel du kan angi, for å få rapportert kun de skipene som venter minst så lenge. Angis som andeler av tidsenheten du implisitt har antatt

    """
    lbda = float(lbda)
    mu = float(mu)

    # Trekker tid mellom anløp og seilingstid fra de rette fordelingene
    interarrival_times = np.random.exponential(1 / lbda, int(num_periods * lbda * 1.5))
    # Faktiske anløpstider er da cumsum av tid mellom anløp
    arrival_times = np.cumsum(interarrival_times)

    # Beholder bare anløpstider innenfor det antall perioder vi skal simulere
    arrival_times = arrival_times[arrival_times < num_periods]
    num_arrivals = len(arrival_times)

    service_times = np.random.exponential(1 / mu, num_arrivals)

    # Tomme vektorer for å lagre når skipene får seile gjennom, og når de er ferdige
    service_start_times = np.empty_like(arrival_times)
    completion_times = np.empty_like(arrival_times)

    # Første skipet seiler direkte gjennom uten ventetid
    service_start_times[0] = arrival_times[0]
    completion_times[0] = arrival_times[0] + service_times[0]
    # Øvrige skip seiler gjennom så fort de kommer, eller når forrige er ferdig hvis det er senere i dig
    for k in range(1, num_arrivals):
        service_start_times[k] = max(completion_times[k - 1], arrival_times[k])
        completion_times[k] = service_start_times[k] + service_times[k]

    # Regner ut de tallene vi ønsker oss

    total_times = completion_times - arrival_times
    wait_times = service_start_times - arrival_times

    num_waiting_incidents = np.sum(wait_times > 0)

    wait_times_just = np.where(wait_times > threshold, wait_times, 0)
    num_waiting_incidents_just = np.sum(wait_times_just > 0)

    share_busy = service_times.sum() / completion_times.max()

    # For å regne ut antall skip i kø på ethvert tidspunkt må vi trikse litt med anløps- og gjennomseilingstidspunktene
    wait_time_start = pd.Series(
        index=arrival_times[service_start_times > arrival_times],
        data=1,
        name="line_length",
    )
    wait_time_end = pd.Series(
        index=service_start_times[service_start_times > arrival_times],
        data=-1,
        name="line_length",
    )

    waits = (
        pd.concat([wait_time_start, wait_time_end], axis=0)
        .sort_index()
        .to_frame()
        .reset_index()
        .rename(columns={"index": "time_stamp"})
        .assign(num_in_line=lambda df: df.line_length.cumsum())
        # Setter inn en første rad for å få med at det var null kø før det første skipet anløp
        .pipe(
            lambda df: pd.concat(
                [
                    pd.DataFrame(
                        [{"time_stamp": 0, "line_length": 0, "num_in_line": 0}]
                    ),
                    df,
                ],
                ignore_index=True,
                sort=True,
            )
        )
        .assign(duration=lambda df: df.time_stamp.shift(-1) - df.time_stamp)
    )

    # Summerer all tid tilbrakt med hver kølengde
    waits_agg = waits.groupby("num_in_line").duration.sum()
    # Snittkølengden er vektet etter tid tilbrakt med hver kølengde
    mean_line_length = np.average(waits_agg.index.values, weights=waits_agg.values)

    max_line_length = waits_agg.index.max()

    out = {
        "mean_wait_time": robust_mean(wait_times),
        "max_wait_time": max_or_nan(wait_times),
        "mean_total_time": robust_mean(total_times),
        "max_total_time": max_or_nan(total_times),
        "mean_service_time": robust_mean(service_times),
        "max_service_time": max_or_nan(service_times),
        "mean_length_line": mean_line_length,
        "max_length_line": max_line_length,
        "mean_server_occupation": robust_mean(share_busy),
        "waiting_incidents_per_period": num_waiting_incidents / arrival_times[-1],
        "prob_cust_must_wait": num_waiting_incidents / num_arrivals,
    }

    if threshold > 0:
        out["mean_wait_time_just"] = robust_mean(wait_times_just)
        out["waiting_incidents_per_period_just"] = (
            num_waiting_incidents_just / num_periods
        )
        out["prob_cust_must_wait_just"] = num_waiting_incidents_just / num_arrivals

    return out


def simulate_multiship_single_bottleneck(
    lbdas: List[float],
    mus: List[float],
    ship_ids: Optional[List[str]] = None,
    num_periods: int = 10_000,
    threshold: float = 0,
):
    """Simulerer en kø med flere ulike typer skip, men én flaskehals

    Denne skiller seg fra ett skip, én flaskehals, én retning, kun ved at det er flere ulike skip. Når deres
    anløpstider først er trukket, fungerer algoritmen som om det kun var én skipstype. Output kan imidlertid
    rapporteres per skipstype

    Args:
        lbdas: Angir gjennomsnittlig antall anløp per tidsenhet. Dette er en liste med en float
            for hver skipstype du vil simulere. Anløpene vil være Poisson-fordelt i modellen, det vil si at det
            i gjennomsnitt er like lang tid mellom hvert anløp for den enkelte skipstype
        mus: Angir hvor mange skip som kan behandles av flaskehalsen per tidsenhet (seile gjennom hvis en
            trang farled, losses i havn hvis det er en kai, etc.). Dette er en liste med en float for hver skipstype
            du vil simulere. Må være like lang som `lbdas`
        ship_ids: En liste med ider for hver skipstype, for å kunne identifisere hvilke skip som venter
            hvor lenge i output. Må være like lang som `lbdas`
        num_periods: Hvor mange perioder du ønsker å simulere. For at de store talls lov skal gjelde må du
            kjøre mer enn én periode. Anbefaler minst 10 000, som er default
        threshold: En terskel du kan angi, for å få rapportert kun de skipene som venter minst så lenge.
            Angis som andeler av tidsenheten du implisitt har antatt

    """

    lbdas = [float(lbda) for lbda in lbdas]
    mus = [float(mu) for mu in mus]
    if ship_ids is None:
        ship_ids = [str(tall) for tall in range(len(lbdas))]

    assert (
        len(lbdas) == len(mus) == len(ship_ids)
    ), "lbdas, mus og ship_ids må ha samme lengde"
    dfs = []
    for ship, lbda, mu in zip(ship_ids, lbdas, mus):
        df = pd.DataFrame(
            {
                "interarrival_times": np.random.exponential(
                    1 / lbda, int(num_periods * min(lbdas))
                ),
                "service_times": np.random.exponential(
                    1 / mu, int(num_periods * min(lbdas))
                ),
                "ship_id": ship,
            }
        ).assign(arrival_times=lambda df: df.interarrival_times.cumsum())
        dfs.append(df)

    df = (
        pd.concat(dfs, ignore_index=True, sort=False)
        .sort_values(by="arrival_times")
        .reset_index(drop=True)
        .query("arrival_times < @num_periods")
    )
    num_arrivals = len(df)

    # Henter ut anløpstallene og gjenbruker mye av algoritmen fra ettskipstilfellet
    arrival_times = df.arrival_times.values
    service_times = df.service_times.values

    # Tomme vektorer for å lagre når skipene får seile gjennom, og når de er ferdige
    service_start_times = np.empty_like(arrival_times)
    completion_times = np.empty_like(arrival_times)

    # Første skipet seiler direkte gjennom uten ventetid
    service_start_times[0] = arrival_times[0]
    completion_times[0] = arrival_times[0] + service_times[0]
    # Øvrige skip seiler gjennom så fort de kommer, eller når forrige er ferdig hvis det er senere i dig
    for k in range(1, num_arrivals):
        service_start_times[k] = max(completion_times[k - 1], arrival_times[k])
        completion_times[k] = service_start_times[k] + service_times[k]

    # Regner ut de tallene vi ønsker oss
    total_times = completion_times - arrival_times
    wait_times = total_times - service_times

    df = (
        df.assign(service_start_times=service_start_times)
        .assign(completion_times=completion_times)
        .assign(total_times=total_times)
        .assign(wait_times=wait_times)
    )

    num_waiting_incidents = np.sum(wait_times > 0)

    wait_times_just = np.where(wait_times > threshold, wait_times, 0)
    num_waiting_incidents_just = np.sum(wait_times_just > 0)

    share_busy = service_times.sum() / completion_times.max()

    # For å regne ut antall skip i kø på ethvert tidspunkt må vi trikse litt med anløps- og gjennomseilingstidspunktene
    wait_time_start = pd.Series(
        index=arrival_times[service_start_times > arrival_times],
        data=1,
        name="line_length",
    )
    wait_time_end = pd.Series(
        index=service_start_times[service_start_times > arrival_times],
        data=-1,
        name="line_length",
    )

    waits = (
        pd.concat([wait_time_start, wait_time_end], axis=0)
        .sort_index()
        .to_frame()
        .reset_index()
        .rename(columns={"index": "time_stamp"})
        .assign(num_in_line=lambda df: df.line_length.cumsum())
        # Setter inn en første rad for å få med at det var null kø før det første skipet anløp
        .pipe(
            lambda df: pd.concat(
                [
                    pd.DataFrame(
                        [{"time_stamp": 0, "line_length": 0, "num_in_line": 0}]
                    ),
                    df,
                ],
                ignore_index=True,
                sort=True,
            )
        )
        .assign(duration=lambda df: df.time_stamp.shift(-1) - df.time_stamp)
    )

    # Summerer all tid tilbrakt med hver kølengde
    waits_agg = waits.groupby("num_in_line").duration.sum()
    # Snittkølengden er vektet etter tid tilbrakt med hver kølengde
    mean_line_length = np.average(waits_agg.index.values, weights=waits_agg.values)

    max_line_length = waits_agg.index.max()

    out = {
        "mean_wait_time": robust_mean(wait_times),
        "max_wait_time": max_or_nan(wait_times),
        "mean_total_time": robust_mean(total_times),
        "max_total_time": max_or_nan(total_times),
        "mean_service_time": robust_mean(service_times),
        "max_service_time": max_or_nan(service_times),
        "mean_length_line": mean_line_length,
        "max_length_line": max_line_length,
        "mean_server_occupation": robust_mean(share_busy),
        "waiting_incidents_per_period": num_waiting_incidents / arrival_times[-1],
        "prob_cust_must_wait": num_waiting_incidents / num_arrivals,
    }

    # Gjsn ventetid per skip av hver type
    out["mean_wait_time_per_ship"] = df.groupby("ship_id").wait_times.mean().to_dict()

    if threshold > 0:
        out["mean_wait_time_just"] = robust_mean(wait_times_just)
        out["waiting_incidents_per_period_just"] = (
            num_waiting_incidents_just / num_periods
        )
        out["prob_cust_must_wait_just"] = num_waiting_incidents_just / len(wait_times)

    return out


def simulate_multiship_multiple_bottlenecks(
    lbdas: List[float],
    mus: np.array,
    ship_ids: Optional[List[str]] = None,
    bottleneck_ids: Optional[List[str]] = None,
    num_periods: int = 10_000,
    threshold: float = 0,
):
    """Simulerer en kø med flere ulike typer skip, og flere mulige flaskehalser å velge

    Denne algoritmen er i svært stor grad lik den generelle som er definert øverst i denne filen. Det eneste
    som skiller den fra det generelle tilfellet, er at det kun finnes én retning, og at flaskehalsen da er opptatt
    like lenge hver gang et skip er i gjennomseiling.

    Args:
        lbdas: Angir gjennomsnittlig antall anløp per tidsenhet. Dette er en liste med en float
            for hver skipstype du vil simulere. Anløpene vil være Poisson-fordelt i modellen, det vil si at det
            i gjennomsnitt er like lang tid mellom hvert anløp for den enkelte skipstype
        mus: Angir hvor mange skip som kan behandles av flaskehalsen per tidsenhet (seile gjennom hvis en
            trang farled, losses i havn hvis det er en kai, etc.).  En matrise som har høyden til `lbdas`
            og bredden lik antall flaskehalser. Element (2, 3) er altså hvor lang tid flaskehals 3 bruker på å behandle
            skip 2. Disse kan være like, enten for alle skip, for alle flaskehalser, eller for både alle skip og alle
            flaskehalser. I output vil skipene bli indeksert med navnene sine (se `ship_ids`), mens flaskehalsene blir
            indeksert med `bottleneck_ids`. Begge disse har default verdi (0, 1, 2, ...)
        ship_ids: En liste med ider for hver skipstype, for å kunne identifisere hvilke skip som venter
            hvor lenge i output. Må være like lang som `lbdas`. Defaulter til (0, 1, 2, ...)
        bottleneck_ids: En liste med ider for hver flaskehals, for å kunne identifisere hvor ofte hver
            flaskehals er opptatt. Må være like lang som bredden på `mus`. Defaulter til (0, 1, 2, ...)
        num_periods: Hvor mange perioder du ønsker å simulere. For at de store talls lov skal gjelde må du
            kjøre mer enn én periode. Anbefaler minst 10 000, som er default
        threshold: En terskel du kan angi, for å få rapportert kun de skipene som venter minst så lenge.
            Angis som andeler av tidsenheten du implisitt har antatt
    """
    implicit_num_ships = len(lbdas)
    if len(mus.shape) > 1:
        implicit_num_bottlenecks = mus.shape[1]
    elif implicit_num_ships > 1:
        implicit_num_bottlenecks = 1
    else:
        implicit_num_bottlenecks = len(mus)

    # Kan ikke ha mu = 0, det innebærer at skip ikke kan seile der. Hvis mu er null for alle flaskehalser for et skip,
    # gir vi feilmelding. Hvis mu er null for noen, men ikke alle, flaskehalser for et skip, setter vi mu svært liten
    zero_row = np.zeros(implicit_num_bottlenecks)
    feilmelding = False
    if implicit_num_bottlenecks == 1:
        feilmelding = mus[0] == 0
    elif implicit_num_ships == 1:
        feilmelding = any((mus[:] == 0))
    else:
        feilmelding = any((mus[:] == zero_row).all(1))
    if feilmelding:
        raise ValueError(
            "Du har angitt minst ett skip som ikke kan passere gjennom noen flaskehalser (mu=0 for alle flaskehalser for minst ett skip) - det gir uendelig lang kø."
        )
    mus[mus == 0] = 1e-15

    if ship_ids is None:
        ship_ids = [str(num) for num in range(len(lbdas))]
    if bottleneck_ids is None:
        bottleneck_ids = [str(num) for num in range(implicit_num_bottlenecks)]
    assert implicit_num_ships == len(ship_ids), "lbdas og ship_ids må ha samme lengde"
    assert implicit_num_bottlenecks == len(
        bottleneck_ids
    ), "mus og bottleneck_ids må ha samme lengde"

    # Trekker anløpstider og får rett rekkefølge på skipene
    dfs = []
    for (ship_idx, ship_id), lbda in zip(enumerate(ship_ids), lbdas):
        df = pd.DataFrame(
            {
                "interarrival_times": np.random.exponential(
                    1 / lbda, int(num_periods / min(lbdas))
                ),
                "ship_id": ship_id,
                "ship_idx": ship_idx,
            }
        ).assign(arrival_times=lambda df: df.interarrival_times.cumsum())
        dfs.append(df)
    df = (
        pd.concat(dfs, ignore_index=True, sort=False)
        .sort_values(by="arrival_times")
        .reset_index(drop=True)
        .query("arrival_times < @num_periods")
    )
    num_arrivals = len(df)

    # Henter ut anløpstallene og gjenbruker mye av algoritmen fra ettskipstilfellet
    arrival_times = df.arrival_times.values

    # Trekker så en random matrise for hvert anløp, der hver matrise har størrelse (N_skip, N_flaskehalser)
    gross_service_times = np.random.exponential(
        1 / mus, (num_arrivals, implicit_num_ships, implicit_num_bottlenecks)
    )
    # Henter så ut en vektor for hvert anløp, for det skipet som har det anløpet. Matrisen har da størrelse (N_flaskehalser, num_arrivals)
    gross_service_times = gross_service_times[
        np.array(range(num_arrivals)), np.array(df.ship_idx.values), :
    ].T
    assert gross_service_times.shape == (implicit_num_bottlenecks, num_arrivals)

    # Tomme vektorer for å lagre når skipene får seile gjennom, når de er ferdige og hvilken flaskehals de brukte
    service_start_times = np.empty_like(arrival_times)
    service_times = np.empty_like(arrival_times)
    completion_times = np.empty_like(arrival_times)  # d
    bottleneck_chosen = np.empty_like(arrival_times)  # p
    bottleneck_busy_until = np.zeros(implicit_num_bottlenecks)  # b

    # Første skipet seiler direkte gjennom uten ventetid
    # Øvrige skip seiler gjennom så fort de kommer, eller når forrige er ferdig hvis det er senere i dig
    for k in range(num_arrivals):
        current_service_times = gross_service_times[:, k]
        possible_start_times = np.maximum(arrival_times[k], bottleneck_busy_until)
        chosen_bottleneck = np.argmin(possible_start_times + current_service_times)
        actual_service_time = current_service_times[chosen_bottleneck]
        start_service = possible_start_times[chosen_bottleneck]

        bottleneck_chosen[k] = chosen_bottleneck
        service_start_times[k] = start_service
        bottleneck_busy_until[chosen_bottleneck] = start_service + actual_service_time
        completion_times[k] = start_service + actual_service_time
        service_times[k] = actual_service_time

    # Regner ut de tallene vi ønsker oss
    total_times = completion_times - arrival_times
    wait_times = total_times - service_times

    df = (
        df.assign(service_start_times=service_start_times)
        .assign(completion_times=completion_times)
        .assign(total_times=total_times)
        .assign(wait_times=wait_times)
        .assign(service_times=service_times)
        .assign(bottleneck_id=[bottleneck_ids[int(b)] for b in bottleneck_chosen])
    )

    num_waiting_incidents = np.sum(wait_times > 0)

    wait_times_just = np.where(wait_times > threshold, wait_times, 0)
    num_waiting_incidents_just = np.sum(wait_times_just > 0)

    share_busy = service_times.sum() / completion_times.max() / implicit_num_bottlenecks

    # For å regne ut antall skip i kø på ethvert tidspunkt må vi trikse litt med anløps- og gjennomseilingstidspunktene
    wait_time_start = pd.Series(
        index=arrival_times[service_start_times > arrival_times],
        data=1,
        name="line_length",
    )
    wait_time_end = pd.Series(
        index=service_start_times[service_start_times > arrival_times],
        data=-1,
        name="line_length",
    )

    waits = (
        pd.concat([wait_time_start, wait_time_end], axis=0)
        .sort_index()
        .to_frame()
        .reset_index()
        .rename(columns={"index": "time_stamp"})
        .assign(num_in_line=lambda df: df.line_length.cumsum())
        # Setter inn en første rad for å få med at det var null kø før det første skipet anløp
        .pipe(
            lambda df: pd.concat(
                [
                    pd.DataFrame(
                        [{"time_stamp": 0, "line_length": 0, "num_in_line": 0}]
                    ),
                    df,
                ],
                ignore_index=True,
                sort=True,
            )
        )
        .assign(duration=lambda df: df.time_stamp.shift(-1) - df.time_stamp)
    )

    # Summerer all tid tilbrakt med hver kølengde
    waits_agg = waits.groupby("num_in_line").duration.sum()
    # Snittkølengden er vektet etter tid tilbrakt med hver kølengde
    mean_line_length = np.average(waits_agg.index.values, weights=waits_agg.values)

    max_line_length = waits_agg.index.max()

    out = {
        "mean_wait_time": robust_mean(wait_times),
        "max_wait_time": max_or_nan(wait_times),
        "mean_total_time": robust_mean(total_times),
        "max_total_time": max_or_nan(total_times),
        "mean_service_time": robust_mean(gross_service_times),
        "max_service_time": max_or_nan(gross_service_times),
        "mean_length_line": mean_line_length,
        "max_length_line": max_line_length,
        "mean_server_occupation": share_busy,
        "waiting_incidents_per_period": num_waiting_incidents / arrival_times[-1],
        "prob_cust_must_wait": num_waiting_incidents / num_arrivals,
    }

    # Gjsn ventetid per skip av hver type
    out["mean_wait_time_per_ship"] = df.groupby("ship_id").wait_times.mean().to_dict()

    # Gjsn opptattid per flaskehals
    out["mean_share_busy_per_bottleneck"] = (
        df.groupby("bottleneck_id")
        .service_times.sum()
        .div(completion_times.max())
        .to_dict()
    )

    if threshold > 0:
        out["mean_wait_time_just"] = robust_mean(wait_times_just)
        out["waiting_incidents_per_period_just"] = (
            num_waiting_incidents_just / num_periods
        )
        out["prob_cust_must_wait_just"] = num_waiting_incidents_just / len(wait_times)

    return out


def simulate_multiship_single_bottleneck_alternate_directions(
    lbdas: List[float],
    mus: List[float],
    ship_ids: List[str],
    directions: List[str],
    alpha: float,
    num_periods: int,
    threshold: float = 0,
):
    """Simulerer en kø med flere ulike typer skip, men én flaskehals. Skip kan komme i inntil to ulike retninger


        Denne algoritmen er i svært stor grad lik den generelle som er definert øverst i denne filen. Det eneste
        som skiller den fra det generelle tilfellet, er at det kun finnes én flaskehals, slik at man ikke kan velge
        mellom ulike flaskehalser. Ellers er algoritmen fullspecket, med mulighet for rabatt for ettergående skip
        som seiler i samme retning. I flaskehalsen antar vi at når to
        skip kommer etter hverandre i samme retning, kan det bakre skipet begynne seilasen når skipet foran har seilt
        en andel alpha av flaskehalsen. Da åpnes altså leden opp for neste skip - men bare hvis de seiler i samme retning.

         Args:
            lbdas: Angir gjennomsnittlig antall anløp per tidsenhet. Dette er en liste med en float
                for hver skipstype du vil simulere. Anløpene vil være Poisson-fordelt i modellen, det vil si at det
                i gjennomsnitt er like lang tid mellom hvert anløp for den enkelte skipstype
            mus: Angir hvor mange skip som kan behandles av flaskehalsen per tidsenhet (seile gjennom hvis en
                trang farled, losses i havn hvis det er en kai, etc.). Dette er en liste med en float for hver skipstype
                du vil simulere. Må være like lang som `lbdas`
            ship_ids: En liste med ider for hver skipstype, for å kunne identifisere hvilke skip som venter
                hvor lenge i output. Må være like lang som `lbdas`
            directions: En liste med retning for hver skipstype, for å kunne ha skip i ulike retninger. Skip
                som seiler i samme retning kan gå med mindre tid seg imellom enn skip i motsatt retning, angitt ved
                rabatten `alpha`
            alpha: Angir hvor stor andel av flaskehalsen et skip må ha seilt gjennom, før et skip bak (i samme
                retning) kan få lov til å begynne seilasen. `alpha=1` impliserer ingen rabatt. `alpha=0` innebærer at
                to skip i samme retning kan seile umiddelbart etter hverandre, mens ved skip i motsatt retning, vil
                flaskehalsen være låst i hele gjennomseilingstiden `1/mu`.
            num_periods: Hvor mange perioder du ønsker å simulere. For at de store talls lov skal gjelde må du
                kjøre mer enn én periode. Anbefaler minst 10 000, som er default
            threshold: En terskel du kan angi, for å få rapportert kun de skipene som venter minst så lenge.
                Angis som andeler av tidsenheten du implisitt har antatt (døgn)
        """

    assert (
        len(lbdas) == len(mus) == len(ship_ids) == len(directions)
    ), "lbdas, mus, ship_ids og directions må ha samme lengde"
    dfs = []
    for ship, lbda, mu, direction in zip(ship_ids, lbdas, mus, directions):
        df = pd.DataFrame(
            {
                "interarrival_times": np.random.exponential(
                    1 / lbda, int(num_periods * min(lbdas))
                ),
                "direction": direction,
                "mu": mu,
                "sailing_times": np.random.exponential(
                    1 / mu, int(num_periods * min(lbdas))
                ),
                "ship_id": ship,
            }
        ).assign(arrival_times=lambda df: df.interarrival_times.cumsum())
        dfs.append(df)

    df = (
        pd.concat(dfs, ignore_index=True, sort=False)
        .sort_values(by="arrival_times")
        .reset_index(drop=True)
        .query("arrival_times < @num_periods")
        .assign(
            alternating_direction=lambda df: df.direction != df.direction.shift(-1)
        )  # Alternating hvis neste ikke er lik denne retningen
        .assign(alpha=lambda df: np.where(df.alternating_direction.values, 1, alpha))
        .eval("server_occupied_times = sailing_times * alpha")
    )
    num_arrivals = len(df)

    # Henter ut anløpstallene og gjenbruker mye av algoritmen fra ettskipstilfellet
    arrival_times = df.arrival_times.values
    server_occupied_times = df.server_occupied_times.values
    sailing_times = df.sailing_times

    # Tomme vektorer for å lagre når skipene får seile gjennom, og når de er ferdige
    service_start_times = np.empty_like(arrival_times)
    completion_times = np.empty_like(arrival_times)
    server_busy_intil = np.zeros_like(arrival_times)

    # Skip seiler gjennom så fort de kommer, eller når forrige er ferdig hvis det er senere i dig
    for k in range(num_arrivals):
        service_start_times[k] = max(server_busy_intil[k - 1], arrival_times[k])
        completion_times[k] = (
            service_start_times[k] + sailing_times[k]
        )  # Skipet er ferdig når det er ferdig
        server_busy_intil[k] = (
            service_start_times[k] + server_occupied_times[k]
        )  # Flaskehalsen er ledig når alpha-korreksjonen sier at det er det

    # Regner ut de tallene vi ønsker oss
    total_times = completion_times - arrival_times
    wait_times = service_start_times - arrival_times

    df = (
        df.assign(service_start_times=service_start_times)
        .assign(completion_times=completion_times)
        .assign(total_times=total_times)
        .assign(wait_times=wait_times)
    )

    num_waiting_incidents = np.sum(wait_times > 0)

    wait_times_just = np.where(wait_times > threshold, wait_times, 0)
    num_waiting_incidents_just = np.sum(wait_times_just > 0)

    share_busy = server_occupied_times.sum() / completion_times.max()

    # For å regne ut antall skip i kø på ethvert tidspunkt må vi trikse litt med anløps- og gjennomseilingstidspunktene
    wait_time_start = pd.Series(
        index=arrival_times[service_start_times > arrival_times],
        data=1,
        name="line_length",
    )
    wait_time_end = pd.Series(
        index=service_start_times[service_start_times > arrival_times],
        data=-1,
        name="line_length",
    )

    waits = (
        pd.concat([wait_time_start, wait_time_end], axis=0)
        .sort_index()
        .to_frame()
        .reset_index()
        .rename(columns={"index": "time_stamp"})
        .assign(num_in_line=lambda df: df.line_length.cumsum())
        # Setter inn en første rad for å få med at det var null kø før det første skipet anløp
        .pipe(
            lambda df: pd.concat(
                [
                    pd.DataFrame(
                        [{"time_stamp": 0, "line_length": 0, "num_in_line": 0}]
                    ),
                    df,
                ],
                ignore_index=True,
                sort=True,
            )
        )
        .assign(duration=lambda df: df.time_stamp.shift(-1) - df.time_stamp)
    )

    # Summerer all tid tilbrakt med hver kølengde
    waits_agg = waits.groupby("num_in_line").duration.sum()
    # Snittkølengden er vektet etter tid tilbrakt med hver kølengde
    mean_line_length = np.average(waits_agg.index.values, weights=waits_agg.values)

    max_line_length = waits_agg.index.max()

    out = {
        "mean_wait_time": robust_mean(wait_times),
        "max_wait_time": max_or_nan(wait_times),
        "mean_total_time": robust_mean(total_times),
        "max_total_time": max_or_nan(total_times),
        "mean_service_time": robust_mean(sailing_times),
        "max_service_time": max_or_nan(sailing_times),
        "mean_length_line": mean_line_length,
        "max_length_line": max_line_length,
        "mean_server_occupation": robust_mean(share_busy),
        "waiting_incidents_per_period": num_waiting_incidents / arrival_times[-1],
        "prob_cust_must_wait": num_waiting_incidents / num_arrivals,
    }

    # Gjsn ventetid per skip av hver type
    out["mean_wait_time_per_ship"] = df.groupby("ship_id").wait_times.mean().to_dict()

    # Gjsn ventetid per retning
    out["mean_wait_time_per_direction"] = (
        df.groupby("direction").wait_times.mean().to_dict()
    )

    if threshold > 0:
        out["mean_wait_time_just"] = robust_mean(wait_times_just)
        out["waiting_incidents_per_period_just"] = (
            num_waiting_incidents_just / num_periods
        )
        out["prob_cust_must_wait_just"] = num_waiting_incidents_just / len(wait_times)

    return out


def simulate_multiship_multiple_bottlenecks_two_directions(
    lbdas: List[float],
    mus: Union[np.array, List[float]],
    directions: Optional[List[str]] = None,
    alpha: Optional[List[float]] = None,
    ship_ids: Optional[List[str]] = None,
    bottleneck_ids: Optional[List[str]] = None,
    num_periods: int = 10_000,
    threshold: float = 1 / 60,
    seed: int = 1,
):
    """Simulerer en kø med flere ulike typer skip, og flere mulige flaskehalser å velge. Skip kan komme i inntil to ulike retninger

    Dette er den fulle algoritmen som beskrevet øverst i filen, og inspirert av denne artikkelen:
    https://arxiv.org/pdf/1703.02151.pdf
    Dersom to etterfølgende skip kommer i ulike retninger, tar gjennomseilingen lenger tid enn hvis de kommer i
    samme rekkefølge. Dette er parametrisert på følgende måte:
    `mu` er definert basert på gjennomseilingstiden, her tas ikke kø og simultanitet med i bildet.
    I flaskehalsen antar vi at når to skip kommer etter hverandre i samme retning, kan det bakre skipet begynne
    seilasen når skipet foran har seilt en andel alpha av flaskehalsen. Da åpnes altså leden opp for neste
    skip - men bare hvis de seiler i samme retning.


    Args:
        lbdas: Angir gjennomsnittlig antall anløp per tidsenhet. Dette er en liste med en float
            for hver skipstype du vil simulere. Anløpene vil være Poisson-fordelt i modellen, det vil si at det
            i gjennomsnitt er like lang tid mellom hvert anløp for den enkelte skipstype
        mus: Angir hvor mange skip som kan behandles av flaskehalsen per tidsenhet (seile gjennom hvis en
            trang farled, losses i havn hvis det er en kai, etc.).  En matrise som har høyden til `lbdas`
            og bredden lik antall flaskehalser. Element (2, 3) er altså hvor lang tid flaskehals 3 bruker på å behandle
            skip 2. Disse kan være like, enten for alle skip, for alle flaskehalser, eller for både alle skip og alle
            flaskehalser. I output vil skipene bli indeksert med navnene sine (se `ship_ids`), mens flaskehalsene blir
            indeksert med `bottleneck_ids`. Begge disse har default verdi (0, 1, 2, ...)
        ship_ids: En liste med ider for hver skipstype, for å kunne identifisere hvilke skip som venter
            hvor lenge i output. Må være like lang som `lbdas`. Defaulter til (0, 1, 2, ...)
        bottleneck_ids: En liste med ider for hver flaskehals, for å kunne identifisere hvor ofte hver
            flaskehals er opptatt. Må være like lang som bredden på `mus`. Defaulter til (0, 1, 2, ...)
        directions: En liste med retning for hver skipstype, for å kunne ha skip i ulike retninger. Skip
            som seiler i samme retning kan gå med mindre tid seg imellom enn skip i motsatt retning, angitt ved
            rabatten `alpha`. Default er at alle skip kommer i samme retning.
        alpha: Angir hvor stor andel av flaskehalsen et skip må ha seilt gjennom, før et skip bak (i samme
            retning) kan få lov til å begynne seilasen. `alpha=1` impliserer ingen rabatt. `alpha=0` innebærer at
            to skip i samme retning kan seile umiddelbart etter hverandre, mens ved skip i motsatt retning, vil
            flaskehalsen være låst i hele gjennomseilingstiden `mu`. `alpha` er en liste med en parameter per flaskehals,
            total lengde må være lik antall flaskehalser. Defalut er `alpha=1` for alle flaskehalser, altså ingen
            rabatt ved å seile i samme retning
        num_periods: Hvor mange perioder du ønsker å simulere. For at de store talls lov skal gjelde må du
            kjøre mer enn én periode. Anbefaler minst 10 000, som er default
        threshold: En terskel du kan angi, for å få rapportert kun de skipene som venter minst så lenge.
            Angis som andeler av tidsenheten du implisitt har antatt (døgn)
        seed: Seed som setter random state for numpy. For å kunne gjenskape simuleringer.
    """
    np.random.seed(seed)
    if isinstance(mus, list):
        mus = np.array(mus)

    if len(lbdas) > 1:
        implicit_num_ships, implicit_num_bottlenecks = mus.shape
    else:
        implicit_num_ships = len(lbdas)
        implicit_num_bottlenecks = len(mus)

    # Hvis det ikke er angitt alpha, settes denne til 1 (ingen rabatt) for alle flaskehalser
    if alpha is None:
        alpha = [1] * implicit_num_bottlenecks

    if ship_ids is None:
        ship_ids = [str(num) for num in range(len(lbdas))]
    if bottleneck_ids is None:
        bottleneck_ids = [str(num) for num in range(implicit_num_bottlenecks)]
    assert implicit_num_ships == len(ship_ids), "lbdas og ship_ids må ha samme lengde"
    assert implicit_num_bottlenecks == len(
        bottleneck_ids
    ), "mus og bottleneck_ids må ha samme lengde"
    assert implicit_num_bottlenecks == len(
        alpha
    ), "Det må være like mange alpha som flaskehalser"

    # Hvis det ikke er angitt directions, settes disse like, og til noe vilkårlig
    if directions is None:
        directions = ["Ingen retning"] * implicit_num_ships

    # Lager et direction map for å kunne ha retningene som heltall for mer effektiv simulering
    direction_map = {}
    idx = 0
    for el in directions:
        if el not in direction_map:
            direction_map[el] = idx
            idx += 1
    assert (
        len(direction_map) <= 2
    ), f"Kan ikke ha flere enn to retninger, fikk {list(direction_map.keys())}"

    # Lager unik kombinasjon av skipstype og retning for riktig oppslag i mu
    ship_directions = [
        ship_id + direction for ship_id, direction in zip(ship_ids, directions)
    ]

    # Erstatter alle null-muer med svakt positiv, ellers knekker simuleringen. Poenget er
    # at mu blir så liten at seilingstiden blir så lang at ingen velger den leden hvis de kan unngå det.
    mus = np.where(mus > 0, mus, MU_ZERO_REPLACEMENT)

    # Trekker anløpstider og får rett rekkefølge på skipene
    dfs = []
    for ship_id, lbda, direction, (ship_idx, ship_direction) in zip(
        ship_ids, lbdas, directions, enumerate(ship_directions)
    ):
        # Tar ikke med skip som ikke anløper
        if lbda == 0:
            raise ValueError(
                f"Fikk en lambda som er null - det går ikke. Det gjelder skipet {ship_id} i retning {direction}"
            )
        direction_id = direction_map.get(direction)
        df = (
            pd.DataFrame(
                {
                    "interarrival_times": np.random.exponential(
                        1 / lbda, int(2 * num_periods * lbda)
                    ),
                    "ship_id": ship_id,
                    "ship_idx": ship_idx,
                    "direction": direction,
                    "direction_id": direction_id,
                    "ship_id_direction": ship_direction,
                }
            )
            .assign(arrival_times=lambda df: df.interarrival_times.cumsum())
            .query("arrival_times < @num_periods")
        )
        dfs.append(df)
    df = (
        pd.concat(dfs, ignore_index=True, sort=False)
        .sort_values(by="arrival_times")
        .reset_index(drop=True)
        .assign(
            alternating_direction=lambda df: df.direction != df.direction.shift(-1)
        )  # Alternating hvis neste ikke er lik denne retningen
    )
    num_arrivals = len(df)

    # Henter ut anløpstallene og gjenbruker mye av algoritmen fra ettskipstilfellet
    arrival_times = df.arrival_times.values
    arrival_directions = df.direction_id.values
    ship_idxs = df.ship_idx.values

    # Setter opp alpha på en matriseform som er hensiktsmessig for simulering
    applied_alpha = np.array(
        [alpha, np.ones_like(alpha)]
    ).T  # [[alpha0, 1], [alpha1, 1], [alpha2, 1]] etc
    _alpha_row_idx = np.array(
        list(range(len(alpha)))
    )  # Bare en hjelpevektor for indeksering - har ingen betydning

    # Seilingstiden er gitt ved 1/mu. Ingen stokastikk eller simulering her
    gross_service_times = 1 / mus  # med dimensjoner (num_ship, num_bottlenecks)
    if len(gross_service_times.shape) == 1:
        gross_service_times = np.reshape(
            gross_service_times, (gross_service_times.size, 1)
        )

    # Tomme vektorer for å lagre når skipene får seile gjennom, når de er ferdige og hvilken flaskehals de brukte
    service_start_times = np.empty_like(arrival_times)
    service_times = np.empty_like(arrival_times)
    completion_times = np.empty_like(arrival_times)  # d
    bottleneck_chosen = np.empty_like(arrival_times)  # p
    bottleneck_busy_until = np.zeros(implicit_num_bottlenecks)  # b
    last_ship_direction = np.zeros(
        implicit_num_bottlenecks, dtype=np.int8
    )  # Antar at alle flaskehalser har et skip i retning 0 ved start - liten simuleringsfeil som ikke har noe å si

    # Første skipet seiler direkte gjennom uten ventetid
    # Øvrige skip seiler gjennom så fort de kommer, eller når forrige er ferdig hvis det er senere i dig
    for k in range(num_arrivals):
        current_direction = arrival_directions[k]
        current_ship_idx = ship_idxs[k]
        current_service_times = gross_service_times[current_ship_idx, :]
        alpha_correction = applied_alpha[
            _alpha_row_idx, (last_ship_direction - current_direction)
        ]  # Sjekker om du skal få en alfa-korreksjon.
        # Dette avhenger av om forrige skip seilte samme retning som deg, da er (last_ship_direction - current_direction) = 0, og den henter den første kolonnen i matrisen applied_alpha

        # Alpha-korreksjonen kommer bare inn i hvor lenge flaskehalsen blir opptatt, ikke i ditt valg nå.
        possible_start_times = np.maximum(arrival_times[k], bottleneck_busy_until)
        chosen_bottleneck = np.argmin(possible_start_times + current_service_times)

        # Men alpha teller ikke med på servicetiden skipet opplever
        actual_service_time = current_service_times[chosen_bottleneck]
        start_service = possible_start_times[chosen_bottleneck]

        bottleneck_chosen[k] = chosen_bottleneck
        service_start_times[k] = start_service
        bottleneck_busy_until[chosen_bottleneck] = (
            start_service
            + actual_service_time
            * alpha_correction[
                chosen_bottleneck
            ]  # Alpha teller med på hvor lenge neste er opptatt
        )
        last_ship_direction[chosen_bottleneck] = current_direction
        completion_times[k] = start_service + actual_service_time
        service_times[k] = actual_service_time

    # Regner ut de tallene vi ønsker oss
    total_times = completion_times - arrival_times
    wait_times = total_times - service_times

    df = (
        df.assign(service_start_times=service_start_times)
        .assign(completion_times=completion_times)
        .assign(total_times=total_times)
        .assign(wait_times=wait_times)
        .assign(service_times=service_times)
        .assign(bottleneck_id=[bottleneck_ids[int(b)] for b in bottleneck_chosen])
    )

    num_waiting_incidents = np.sum(wait_times > 0)

    wait_times_just = np.where(wait_times > threshold, wait_times, 0)
    num_waiting_incidents_just = np.sum(wait_times_just > 0)

    share_busy = service_times.sum() / completion_times.max() / implicit_num_bottlenecks

    # For å regne ut antall skip i kø på ethvert tidspunkt må vi trikse litt med anløps- og gjennomseilingstidspunktene
    wait_time_start = pd.Series(
        index=arrival_times[service_start_times > arrival_times],
        data=1,
        name="line_length",
    )
    wait_time_end = pd.Series(
        index=service_start_times[service_start_times > arrival_times],
        data=-1,
        name="line_length",
    )

    waits = (
        pd.concat([wait_time_start, wait_time_end], axis=0)
        .sort_index()
        .to_frame()
        .reset_index()
        .rename(columns={"index": "time_stamp"})
        .assign(num_in_line=lambda df: df.line_length.cumsum())
        # Setter inn en første rad for å få med at det var null kø før det første skipet anløp
        .pipe(
            lambda df: pd.concat(
                [
                    pd.DataFrame(
                        [{"time_stamp": 0, "line_length": 0, "num_in_line": 0}]
                    ),
                    df,
                ],
                ignore_index=True,
                sort=True,
            )
        )
        .assign(duration=lambda df: df.time_stamp.shift(-1) - df.time_stamp)
    )

    # Summerer all tid tilbrakt med hver kølengde
    waits_agg = waits.groupby("num_in_line").duration.sum()
    # Snittkølengden er vektet etter tid tilbrakt med hver kølengde
    try:
        mean_line_length = np.average(waits_agg.index.values, weights=waits_agg.values)
    except ZeroDivisionError:
        mean_line_length = 0

    max_line_length = waits_agg.index.max()

    out = {
        "mean_wait_time": robust_mean(wait_times),
        "max_wait_time": max_or_nan(wait_times),
        "mean_total_time": robust_mean(total_times),
        "max_total_time": max_or_nan(total_times),
        "mean_service_time": robust_mean(gross_service_times[:]),
        "max_service_time": max_or_nan(gross_service_times[:]),
        "mean_length_line": mean_line_length,
        "max_length_line": max_line_length,
        "mean_server_occupation": robust_mean(share_busy),
        "waiting_incidents_per_period": num_waiting_incidents / arrival_times[-1],
        "prob_cust_must_wait": num_waiting_incidents / num_arrivals,
        "num_arrivals": num_arrivals,
        "last_arrival_time": arrival_times[-1],
        "num_incidents": num_waiting_incidents,
    }

    # Gjsn ventetid per skip av hver type
    out["mean_wait_time_per_ship"] = df.groupby("ship_id").wait_times.mean().to_dict()

    # Gjsn totaltid per skip av hver type
    out["mean_total_time_per_ship"] = df.groupby("ship_id").total_times.mean().to_dict()

    # Gjsn servicetid per skip av hver type
    out["mean_service_time_per_ship"] = (
        df.groupby("ship_id").service_times.mean().to_dict()
    )

    out["mean_incidents_per_period_per_ship"] = (
        df.groupby("ship_id")
        .wait_times.agg(lambda wait_times: np.mean(wait_times > 0))
        .to_dict()
    )

    # Gjsn ventetid per retning
    out["mean_wait_time_per_direction"] = (
        df.groupby("direction").wait_times.mean().to_dict()
    )

    # Gjsn opptattid per flaskehals
    out["mean_share_busy_per_bottleneck"] = (
        df.groupby("bottleneck_id")
        .service_times.sum()
        .div(completion_times.max())
        .to_dict()
    )

    out["passings_per_bottleneck_per_period"] = (
        df.groupby("bottleneck_id")
        .service_times.count()
        .div(arrival_times[-1])
        .to_dict()
    )

    out["passings_per_bottleneck_per_ship_per_period"] = (
        df.assign(
            ship_bottleneck=lambda df: df.ship_id
            + SKIP_LENGDE_SPLITTER
            + df.bottleneck_id
        )
        .groupby("ship_bottleneck")
        .service_times.count()
        .div(arrival_times[-1])
        .to_dict()
    )

    # Andel alternerende retninger per flaskehals
    out["mean_share_alternating_directions"] = (
        df.groupby("bottleneck_id").alternating_direction.mean().to_dict()
    )

    if threshold > 0:
        out["mean_wait_time_just"] = robust_mean(wait_times_just)
        out["waiting_incidents_per_period_just"] = (
            num_waiting_incidents_just / num_periods
        )
        out["prob_cust_must_wait_just"] = num_waiting_incidents_just / len(wait_times)
        out["num_incidents_just"] = num_waiting_incidents_just
        out["mean_incidents_just_per_period_per_ship"] = (
            df.groupby("ship_id")
            .wait_times.agg(lambda wait_times: np.mean(wait_times > threshold))
            .to_dict()
        )

    return out


# if __name__ == "__main__":
# do_examples_no_excel()
# lbda = 1
# mu = 2
# num_periods = 100_000
# np.random.seed(1)
# model_output = simulate_multiship_multiple_bottlenecks_two_directions(
#     lbdas=[lbda, lbda],
#     mus=np.array([[mu, mu], [mu, mu]]),
#     ship_ids=["Tankskip", "Cruiseskip"],
#     bottleneck_ids=["Vestre", "Østre"],
#     directions=["nord", "sor"],
#     alpha=[1, 1],
#     num_periods=num_periods,
# )
# mean_wait_time = model_output["mean_wait_time"]
# riktig_svar = 0.1667
# print()
# print()
# print("Output er", mean_wait_time)
# print("For to skip med lambda=1 og to flaskehalser med mu=2 skulle det ha vært", riktig_svar)
# print("Jeg har pleid å få 0.06")

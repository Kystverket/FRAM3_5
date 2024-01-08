import numpy as np
import pytest
from numpy.random import exponential

from fram.virkninger.ventetid import computation


# Riktige svar i testene er hentet herfra: https://www.supositorio.com/rcalc/rcalclite.htm


@pytest.mark.parametrize(
    "lbda, mu, average_wait, server_occupancy",
    [(1, 2, 0.5, 0.5), (0.3, 2, 0.0882, 0.15), (0.3, 1, 0.4286, 0.3)],
)
def test_ett_skip_en_flaskehals(lbda, mu, average_wait, server_occupancy):
    model_output = computation.simulate_multiship_multiple_bottlenecks(
        lbdas=[lbda], mus=np.array([mu]), num_periods=1_000_000,
    )
    assert np.isclose(model_output["mean_wait_time"], average_wait, atol=0.01)
    assert np.isclose(
        model_output["mean_server_occupation"], server_occupancy, atol=0.01
    )


@pytest.mark.parametrize(
    "lbdas, mu, average_wait, server_occupancy",
    [([0.1, 0.2], 1, 0.4286, 0.3), ([0.1, 0.1, 0.3], 2, 0.1667, 0.25)],
)
def test_to_skip_en_flaskehals_i_ettskipsmodellen(
    lbdas, mu, average_wait, server_occupancy
):
    model_output = computation.simulate_single_ship_single_bottleneck(
        sum(lbdas), mu, num_periods=1_000_000
    )
    assert np.isclose(model_output["mean_wait_time"], average_wait, atol=0.01)
    assert np.isclose(
        model_output["mean_server_occupation"], server_occupancy, atol=0.01
    )


@pytest.mark.parametrize(
    "lbdas, mu, average_wait, server_occupancy",
    [([0.1, 0.2], 1, 0.4286, 0.3), ([0.1, 0.1, 0.3], 2, 0.1667, 0.25)],
)
def test_to_skip_en_flaskehals(lbdas, mu, average_wait, server_occupancy):
    model_output = computation.simulate_multiship_multiple_bottlenecks(
        lbdas=lbdas, mus=np.array([mu]), num_periods=1_000_000,
    )
    assert np.isclose(model_output["mean_wait_time"], average_wait, atol=0.01)
    assert np.isclose(
        model_output["mean_server_occupation"], server_occupancy, atol=0.01
    )


# Det finnes ikke analytisk løsning for modell med ulike mu. For å teste, hacker vi da den funksjonen som trekker
# seilingstid, slik at den blir lik for alle flaskehalser for hvert skip.
@pytest.fixture
def mock_exponential(monkeypatch):
    """np.random.exponential() mocked to return matrices with identical columns"""

    def custom_random_exponential(par, shape):
        matrix = exponential(par, shape)
        if isinstance(shape, tuple):
            if len(shape) == 2:
                for col in range(1, shape[1]):
                    matrix[:, col] = matrix[:, 0]
            if len(shape) == 3:
                for col in range(1, shape[2]):
                    matrix[:, :, col] = matrix[:, :, 0]
        return matrix

    monkeypatch.setattr(np.random, "exponential", custom_random_exponential)


@pytest.mark.parametrize(
    "lbda, mus, average_wait, server_occupancy",
    [
        (1, [2, 2], 0.033, 0.25),
        (0.3, [1, 1], 0.023, 0.15),
        (2, [2, 2, 2], 0.0227, 0.333),
    ],
)
def test_ett_skip_to_flaskehalser(
    mock_exponential, lbda, mus, average_wait, server_occupancy
):
    np.random.seed(1)
    model_output = computation.simulate_multiship_multiple_bottlenecks(
        lbdas=[lbda], mus=np.array(mus), num_periods=1_000_000,
    )
    assert np.isclose(model_output["mean_wait_time"], average_wait, atol=0.01)
    assert np.isclose(
        model_output["mean_server_occupation"], server_occupancy, atol=0.01
    )


@pytest.mark.parametrize(
    "lbdas, mus, average_wait, directions, alpha",
    [
        (
            [1, 1],
            [3, 3],
            0.6667,
            ["nord", "nord"],
            1,
        ),  # Som om to skip og en flaskehals
        ([1, 1], [3, 3], 0.6667, ["nord", "sor"], 1),  # Som om to skip og en flaskehals
        (
            [1, 1],
            [3, 3],
            0.16667,
            ["nord", "sor"],
            0,
        ),  # Som om bare halvparten av skipene kom (de andre seiler gratis gjennom), altså ett skip og en flaskehals
    ],
)
def test_to_skip_en_flaskehals_to_retninger(
    lbdas, mus, average_wait, directions, alpha
):
    output = computation.simulate_multiship_single_bottleneck_alternate_directions(
        lbdas=lbdas,
        mus=mus,
        ship_ids=["forste", "andre"],
        directions=directions,
        alpha=alpha,
        num_periods=1_000_000,
    )
    assert np.isclose(output["mean_wait_time"], average_wait, atol=0.01)


@pytest.mark.parametrize(
    "lbdas, mus, average_wait, directions, alpha",
    [
        (
            [1, 1],
            [3, 3],
            [0.1667, 0.6667],
            ["nord", "sor"],
            0.5,
        ),  # Når to etterfølgende kan seile med halvparten av flaskehalsen som avstand, skal køen være nærmere full rabatt enn null rabatt, på grunn av konveksiteten i kø-prosessen
    ],
)
def test_to_skip_en_flaskehals_to_retninger_mellomlosninger(
    lbdas, mus, average_wait, directions, alpha
):
    output = computation.simulate_multiship_single_bottleneck_alternate_directions(
        lbdas=lbdas,
        mus=mus,
        ship_ids=["forste", "andre"],
        directions=directions,
        alpha=alpha,
        num_periods=100_000,
    )
    assert output["mean_wait_time"] < np.mean(average_wait)


@pytest.mark.parametrize(
    "lbdas, mus, directions, alpha, average_wait",
    [
        (
            [1, 1],
            np.array([[2, 2], [2, 2]]),
            ["n", "s"],
            [1, 1],
            0.1667 / 2,
        ),  # Som om to skip og to flaskehalser, retning spiller ingen rolle
        (
            [0.2, 1.8],
            np.array([[2, 2], [2, 2]]),
            ["n", "s"],
            [1, 1],
            0.1667 / 2,
        ),  # Som om to skip og to flaskehalser, retning spiller ingen rolle
        (
            [1, 1],
            np.array([[2, 2], [2, 2]]),
            ["n", "n"],
            [1, 1],
            0.1667 / 2,
        ),  # Som om to skip og to flaskehalser, retning spiller ingen rolle
        (
            [1, 1],
            np.array([[2, 2], [2, 2]]),
            None,
            None,
            0.1667 / 2,
        ),  # Tester defaultene. Skal være samme retning og alpha = 1
        (
            [1, 1],
            np.array([[2], [2]]),
            ["n", "s"],
            [0],
            0.5 / 2,
        ),  # Som om bare halvparten av skipene kom (de andre seiler gratis gjennom), altså ett skip og en flaskehalser
        (
            [1, 1],
            np.array([[2, 2], [2, 2]]),
            ["n", "s"],
            [0, 0],
            0.03 / 2,
        ),  # Ved at sørgående velger den ene og nordgående den andre leden, trenger de aldri stå i kø når de kan gå så tett de bare vil.
        (
            [1],
            [2],
            None,
            None,
            0.5 / 2,
        ),  # Tester at modellen også kan brukes på det aller enkleste caset
    ],
)
def test_to_skip_to_flaskehalser_to_retninger(
    mock_exponential, lbdas, mus, directions, alpha, average_wait
):
    np.random.seed(1)
    model_output = computation.simulate_multiship_multiple_bottlenecks_two_directions(
        lbdas=lbdas, mus=mus, directions=directions, alpha=alpha, num_periods=300_000,
    )
    mean_wait_time = model_output["mean_wait_time"]
    assert np.isclose(mean_wait_time, average_wait, atol=0.01)


@pytest.mark.parametrize(
    "lbdas, mus, directions, alpha, average_wait",
    [
        (
            [1, 1],
            np.array([[2, 2], [2, 2]]),
            ["n", "s"],
            [0.5, 0.5],
            [0.0333, 0.1667],
        ),  # Når alpha er snittet av 0 og 1, vil gjennomsnittlig ventetid være lavere enn snittet av ventetiden ved null og en, pga konveksiteten til køen.
    ],
)
def test_to_skip_to_flaskehalser_to_retninger_mellomlosninger(
    mock_exponential, lbdas, mus, directions, alpha, average_wait
):
    model_output = computation.simulate_multiship_multiple_bottlenecks_two_directions(
        lbdas=lbdas, mus=mus, directions=directions, alpha=alpha, num_periods=200_000,
    )
    mean_wait_time = model_output["mean_wait_time"]
    assert mean_wait_time < np.mean(average_wait)


# Her tests vi at simuleringen funker når vi stenger den ene flaskehalsen for noen skip ved å sette mu til null.
@pytest.mark.parametrize(
    "lbdas, mus, directions, alpha, average_wait",
    [
        (
            [1, 1],
            np.array([[2, 0.00000001], [0.00000001, 2]]),
            ["n", "n"],
            [1, 1],
            0.5 / 2,
        ),
        # Blokker den ene flaskehalsen for hvert skip - altså som om ett skip og en flaskehals
        ([1, 1], np.array([[2, 0], [0, 2]]), ["n", "n"], [1, 1], 0.5 / 2),
        # Blokker den ene flaskehalsen for hvert skip - altså som om ett skip og en flaskehals
    ],
)
def test_to_skip_to_flaskehalser_to_retninger_uten_mock(
    lbdas, mus, directions, alpha, average_wait
):
    model_output = computation.simulate_multiship_multiple_bottlenecks_two_directions(
        lbdas=lbdas, mus=mus, directions=directions, alpha=alpha, num_periods=300_000,
    )
    mean_wait_time = model_output["mean_wait_time"]
    assert np.isclose(mean_wait_time, average_wait, atol=0.01)


@pytest.mark.parametrize(
    "lbdas, mus, directions, average_wait",
    [
        (
            [0.5, 0.5, 0.5, 0.5],
            np.array([[2, 2], [2, 2], [2, 2], [2, 2]]),
            ["nord", "sor", "nord", "sor"],
            0.09,
        ),
        (
            [0.8, 0.8, 0.8, 0.8],
            np.array([[2, 2], [2, 2], [2, 2], [2, 2]]),
            ["nord", "sor", "nord", "sor"],
            0.45,
        ),
    ],
)
def tester_mot_excel(lbdas, mus, directions, average_wait):
    model_output = computation.simulate_multiship_multiple_bottlenecks_two_directions(
        lbdas=lbdas, mus=mus, directions=directions, alpha=[1, 1], num_periods=300_000,
    )
    mean_wait_time = model_output["mean_wait_time"]
    assert np.isclose(mean_wait_time, average_wait, atol=0.03)


def test_nytt_lop_gir_kortere_ko():
    lbdas = [0.5, 0.5, 0.5, 0.5]
    mu = 2
    mus_ref = np.array([[mu], [mu], [mu], [mu]])
    directions = ["nord", "sor", "nord", "sor"]
    mus_tiltak = np.array([[mu, mu], [mu, mu], [mu, mu], [mu, mu]])

    sim_ref = computation.simulate_multiship_multiple_bottlenecks_two_directions(
        lbdas=lbdas, mus=mus_ref, directions=directions, alpha=[1], num_periods=200_000,
    )

    sim_tiltak = computation.simulate_multiship_multiple_bottlenecks_two_directions(
        lbdas=lbdas,
        mus=mus_tiltak,
        directions=directions,
        alpha=[1, 1],
        num_periods=200_000,
    )

    assert sim_ref["mean_wait_time"] > sim_tiltak["mean_wait_time"]


def tester_seilingstid_lik_paa_tvers():
    lbdas = [0.5, 0.5, 0.5, 0.5]
    mu = 2
    mus_ref = np.array([[mu], [mu], [mu], [mu]])
    directions = ["nord", "sor", "nord", "sor"]
    mus_tiltak = np.array([[mu, mu], [mu, mu], [mu, mu], [mu, mu]])

    sim_ref = computation.simulate_multiship_multiple_bottlenecks_two_directions(
        lbdas=lbdas, mus=mus_ref, directions=directions, alpha=[1], num_periods=200_000,
    )

    sim_tiltak = computation.simulate_multiship_multiple_bottlenecks_two_directions(
        lbdas=lbdas,
        mus=mus_tiltak,
        directions=directions,
        alpha=[1, 1],
        num_periods=200_000,
    )

    assert sim_ref["mean_total_time"] > sim_tiltak["mean_total_time"]


def test_lavere_alpha_gir_kortere_ko():
    lbdas = [0.5, 0.5, 0.5, 0.5]
    mu = 2
    directions = ["nord", "sor", "nord", "sor"]
    mus = np.array([[mu, mu], [mu, mu], [mu, mu], [mu, mu]])
    outputs = {
        "1_1": computation.simulate_multiship_multiple_bottlenecks_two_directions(
            lbdas=lbdas,
            mus=mus,
            directions=directions,
            alpha=[1, 1],
            num_periods=200_000,
        )["mean_wait_time"],
        "05_1": computation.simulate_multiship_multiple_bottlenecks_two_directions(
            lbdas=lbdas,
            mus=mus,
            directions=directions,
            alpha=[0.5, 1],
            num_periods=200_000,
        )["mean_wait_time"],
        "05_05": computation.simulate_multiship_multiple_bottlenecks_two_directions(
            lbdas=lbdas,
            mus=mus,
            directions=directions,
            alpha=[0.5, 0.5],
            num_periods=200_000,
        )["mean_wait_time"],
        "0_0": computation.simulate_multiship_multiple_bottlenecks_two_directions(
            lbdas=lbdas,
            mus=mus,
            directions=directions,
            alpha=[0, 0],
            num_periods=200_000,
        )["mean_wait_time"],
    }
    assert outputs["05_1"] < outputs["1_1"]
    assert outputs["05_05"] < outputs["05_1"]
    assert outputs["0_0"] < outputs["05_05"]

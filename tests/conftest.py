collect_ignore = ["setup.py"]

def pytest_addoption(parser):
    parser.addoption("--testtype", action="store", default="liten_test")
    parser.addoption("--les_RA_paa_nytt", action="store", default=False)


def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    option_value = metafunc.config.option.testtype
    if "testtype" in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("testtype", [option_value])

    option_value = metafunc.config.option.les_RA_paa_nytt
    if "les_RA_paa_nytt" in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("les_RA_paa_nytt", [option_value])

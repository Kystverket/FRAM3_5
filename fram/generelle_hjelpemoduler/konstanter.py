import os
from pathlib import Path

KOLONNENAVN_TILTAKSPAKKE = "Tiltakspakke"
KOLONNENAVN_TILTAKSOMRAADE = "Tiltaksomraade"
KOLONNENAVN_STREKNING = "Strekning"

TRAFIKK_COLS = [
    KOLONNENAVN_STREKNING,
    KOLONNENAVN_TILTAKSOMRAADE,
    KOLONNENAVN_TILTAKSPAKKE,
    "Analyseomraade",
    "Rute",
    "Skipstype",
    "Lengdegruppe",
]
FOLSOMHET_KOLONNE = "Analysenavn"
FOLSOMHET_COLS = TRAFIKK_COLS + [FOLSOMHET_KOLONNE]

FOLSOMHETSVARIABLER = [
    "Investeringskostnader",
    "Vedlikehold",
    "Trafikkvolum",
    "Ulykkesfrekvens",
    "Tidskostnader",
    "Drivstoff",
]
FOLSOM_KARBON_HOY = "høy karbonprisbane"
FOLSOM_KARBON_LAV = "lav karbonprisbane"

VIRKNINGSNAVN = "Virkningsnavn"
SKATTEFINANSIERINGSKOSTNAD = "Skattefinansieringskostnader"

KOLONNENAVN_VOLUMVIRKNING = "Virkningsnavn"
KOLONNENAVN_VOLUM_MAALEENHET = "Måleenhet"
VIRKNINGSNAVN_UTSLIPP_ANLEGG = "Endring i globale utslipp til luft - anleggsfasen"
KOLONNENAVN_INNLESING_UTSLIPP_ANLEGG = "tonn CO2 anleggsfasen"

VOLUM_COLS = FOLSOMHET_COLS + [
    KOLONNENAVN_VOLUMVIRKNING,
    KOLONNENAVN_VOLUM_MAALEENHET,
]
VERDSATT_COLS = TRAFIKK_COLS + [
    VIRKNINGSNAVN,
    SKATTEFINANSIERINGSKOSTNAD,
    FOLSOMHET_KOLONNE,
]
VERDSATT_COLS_STRING_VALUES = [
    KOLONNENAVN_STREKNING,
    "Analyseomraade",
    "Rute",
    "Skipstype",
    "Lengdegruppe",
    VIRKNINGSNAVN,
    FOLSOMHET_KOLONNE,
]
VERDSATT_COLS_INT_VALUES = [KOLONNENAVN_TILTAKSOMRAADE, KOLONNENAVN_TILTAKSPAKKE]
VERDSATT_COLS_FLOAT_VALUES = [SKATTEFINANSIERINGSKOSTNAD]
for col in VERDSATT_COLS:
    assert (
        (col in VERDSATT_COLS_INT_VALUES)
        or (col in VERDSATT_COLS_STRING_VALUES)
        or (col in VERDSATT_COLS_FLOAT_VALUES)
    )
MISSING_SKIPSTYPE = "Mangler"
MISSING_LENGDE = "Mangler lengde"
ALLE = "Alle"
ALLE_INT = -999
LENGDEGRUPPER = [
    "0-30",
    "30-70",
    "70-100",
    "100-150",
    "150-200",
    "200-250",
    "250-300",
    "300-",
    MISSING_LENGDE,
]
SKIPSTYPER = [
    "Andre offshorefartøy",
    "Andre servicefartøy",
    "Annet",
    "Brønnbåt",
    "Bulkskip",
    "Containerskip",
    "Cruiseskip",
    "Fiskefartøy",
    "Gasstankskip",
    "Kjemikalie-/Produktskip",
    "Offshore supplyskip",
    "Oljetankskip",
    "Passasjerbåt",
    "Passasjerskip/Roro",
    "Slepefartøy",
    "Stykkgods-/Roro-skip",
]

_SKIPSTYPER_SORTERT = [
    "Alle",
    "Oljetankskip",
    "Kjemikalie-/Produktskip",
    "Gasstankskip",
    "Bulkskip",
    "Stykkgods-/Roro-skip",
    "Containerskip",
    "Passasjerbåt",
    "Passasjerskip/Roro",
    "Cruiseskip",
    "Offshore supplyskip",
    "Andre offshorefartøy",
    "Brønnbåt",
    "Slepefartøy",
    "Andre servicefartøy",
    "Fiskefartøy",
    "Annet",
]
LENGDEGRUPPER_UTEN_MANGLER = [l for l in LENGDEGRUPPER if "Mangler" not in l]


if os.getenv("CI"):  # Til ære for github actions
    FRAM_DIRECTORY = Path(os.environ["GITHUB_WORKSPACE"]) / "fram"
else:
    FRAM_DIRECTORY = Path(__file__).parent.parent  # Peker til mappen fram


FYLKER = [
    'Ostfold', 
    'Akershus', 
    'Oslo', 
    'Buskerud', 
    'Vestfold', 
    'Telemark', 
    'Aust-Agder', 
    'Vest-Agder', 
    'Rogaland', 
    'Hordaland', 
    'Sogn og Fjordane', 
    'More og Romsdal', 
    'Sor-Trondelag',
    'Nord-Trondelag', 
    'Nordland', 
    'Troms ',
    'Finnmark',  
    'Svalbard', ]

class DelvisFRAMFeil(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


AKTØR_VIRKNING_MAPPING = {
        'Endring i forurensede sedimenter':'Samfunnet for øvrig',
        'Endring i globale utslipp til luft':'Samfunnet for øvrig',
        'Endring i lokale utslipp til luft':'Samfunnet for øvrig',
        VIRKNINGSNAVN_UTSLIPP_ANLEGG:'Samfunnet for øvrig',
        'Endring i distanseavhengige kostnader':'Trafikanter og transportbrukere',
        'Endring i tidsavhengige kostnader':'Trafikanter og transportbrukere',
        'Endring i ventetidskostnader':'Trafikanter og transportbrukere',
        'Endring i vedlikeholdskostnader':'Det offentlige',
        'Investeringskostnader, annet':'Det offentlige',
        'Investeringskostnader, navigasjonsinnretninger':'Det offentlige',
        'Investeringskostnader, utdyping':'Det offentlige',
        'Ulykker - endring i dødsfall':'Samfunnet for øvrig',
        'Ulykker - endring i forventet opprenskingskostnad ved oljeutslipp':'Samfunnet for øvrig',
        'Ulykker - endring i forventet velferdstap ved oljeutslipp':'Samfunnet for øvrig',
        'Ulykker - endring i personskader':'Samfunnet for øvrig',
        'Ulykker - endring i reparasjonskostnader':'Samfunnet for øvrig',
        'Ulykker - endring i tid ute av drift':'Samfunnet for øvrig',
        'Skattefinansieringskostnader':'Samfunnet for øvrig',
    }
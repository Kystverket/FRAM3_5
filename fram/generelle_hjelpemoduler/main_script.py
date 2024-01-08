from pathlib import Path
from typing import Optional

import typer


def main(
    filbane: Path = typer.Option(..., help="Filbanen til gyldig FRAM inputfil"),
    tiltakspakke: int = typer.Option(
        ..., help="Hvilken tiltakspakke i inputfilen du ønsker å få analysert"
    ),
    output_filbane: Path = typer.Option(
        None,
        help="Hvilken filbane (mappe) du vil lagre output til. Default er Output (streknignsnavn) ved siden av inputfilen din.",
    ),
    ra_dir: Path = typer.Option(
        None,
        help="Hvor risikoanalysene er å finne. Default er i en mappe 'risikoanalyser' ved siden av inputfilen din",
    ),
    les_RA_paa_nytt: bool = typer.Option(
        False,
        help="Hvorvidt du vil tvinge at den skal lese RA på nytt selv om den finner en ferdiginnlest ra json-fil",
    ),
    trafikkgrunnlagsaar: int = typer.Option(
        2019, help="Hvilket år du har trafikkgrunnlag i"
    ),
    sammenstillingsaar: Optional[int] = typer.Option(
        None, help="Sammenstillingsåret i analysen din"
    ),
    ferdigstillelsesaar: Optional[int] = typer.Option(
        None, help="Ferdigstillelsesåret i analysen din"
    ),
    analyseperiode: Optional[int] = typer.Option(
        None, help="Lengden på analyseperioden din. Default er 75 år (NTP)"
    ),
    levetid: Optional[int] = typer.Option(
        None, help="Levetiden som skal benyttes (det blir restverdi hvis levetid > analyseperiode"
    ),
    delvis_fram: Optional[bool] = typer.Option(
        False, help="Hvorvidt det skal kjøres en delvis fram-analyse"
    ),
    aisyrisk_input: Optional[bool] = typer.Option(
        False, help="Hvorvidt AISyRISK er benyttet som risikomodell"
    ),
    andre_skip_til_null: bool = typer.Option(
        True,
        help="Hvorvidt skip av typen 'Andre' nulles i trafikkgrunnlaget. Default er sant",
    ),
):
    """
    Mulighet til å kjøre FRAM fra kommandolinjen uten å åpne Python. Godt egnet hvis du ikke trenger noe postprosessering eller interaktivitet. Det vil lagres en output-fil i henhold til FRAMs outputrutiner.
    """
    from fram.modell import FRAM

    fram_modell = FRAM(

        strekning=filbane,
        tiltakspakke=tiltakspakke,
        sammenstillingsaar=sammenstillingsaar,
        ferdigstillelsesaar=ferdigstillelsesaar,
        analyseperiode=analyseperiode,
        trafikkgrunnlagsaar=trafikkgrunnlagsaar,
        levetid=levetid,
        andre_skip_til_null=andre_skip_til_null,
        delvis_fram=delvis_fram,
        ra_dir=ra_dir,
        aisyrisk_input=aisyrisk_input,
        les_RA_paa_nytt=les_RA_paa_nytt,
    )
    if output_filbane is None:
        output_filbane = True
    fram_modell.run(skriv_output=output_filbane)

def run():
    typer.run(main)

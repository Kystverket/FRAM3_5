import functools
from typing import Callable

import pandera as pa


def verbose_schema_error(func: Callable) -> Callable:
    """Hjelpedecorator for å gi mer informasjon om hva Pandera feiler på, og i hvilken klasse/funksjon"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (pa.errors.SchemaErrors, pa.errors.SchemaError) as error:
            try:
                schema_name = error.schema.name
            except:
                schema_name = "Ikke angitt navn"
            error_summary: str = str(error.args[0]).split("Schema Error Summary")[0]
            line_sep = "\n-------------------- \n"
            hvilke_feil = "\n\n\nHvilke feil ble funnet? " + line_sep
            hvor_er_feil = "\n\n\nHvor er feilene funnet?" + line_sep
            ny_feilmelding = f"\nFeilmelding fra Pandera i funksjonen {func.__qualname__} med schemaet {schema_name}: \n {error_summary} {hvilke_feil} {error.failure_cases} {hvor_er_feil} {error.data}"
            error.args = (ny_feilmelding,)
            raise error
        except Exception as e:
            raise e

    return wrapper

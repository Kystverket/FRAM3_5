"""
Denne modulen inneholder hele SØA-modellen med tilhørende støttefunksjoner. Det eneste brukeren trenger å forholde seg
til i normal bruk er klassene `FRAM` og `KalkPriser`, dokumentert på denne siden. De som vil videre kan lese om
drivstoffberegninger, RA-innlesing, ytterligere om kalkulasjonspriser eller andre støttefunksjoner.
"""
from fram.generelle_hjelpemoduler.version import __version__
from .modell import FRAM
from .virkninger.drivstoff.virkning import Drivstoff
from .virkninger.investering.virkning import Investeringskostnader
from .virkninger.kontantstrommer.virkning import Kontantstrommer
from .virkninger.risiko.virkning import Risiko
from .virkninger.sedimenter.virkning import Sedimenter
from .virkninger.tid.virkning import Tidsbruk
from .virkninger.utslipp_til_luft.virkning import Utslipp_til_luft
from .virkninger.vedlikehold.virkning import Vedlikeholdskostnader
from .virkninger.ventetid.virkning import Ventetid
from .generelle_hjelpemoduler import main_script

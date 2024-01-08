# Cacher fremhenting av netto lønnsomhet. Tester om python-versjon er 3.8 eller nyere, ellers en liten hack

try:
    from functools import cached_property as lazy_property
except ImportError:
    from functools import lru_cache
    from functools import wraps

    def lazy_property(f):
        return property(lru_cache()(f))

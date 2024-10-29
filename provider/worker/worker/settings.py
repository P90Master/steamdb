from enum import Enum


class CountryCodes(Enum):
    united_states = 'US'
    russia = 'RU'


class CountryCodeCurrencyMapping(Enum):
    @classmethod
    def get(cls, code):
        return cls[code].value if code in cls.__members__ else None

    US = 'USD'
    RU = 'RUB'


DEFAULT_COUNTRY_CODE = CountryCodes.united_states.value

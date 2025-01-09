from enum import Enum


class CountryCodes(Enum):
    united_states = "US"
    china = "CN"
    japan = "JP"
    germany = "DE"
    india = "IN"
    united_kingdom = "GB"
    france = "FR"
    italy = "IT"
    canada = "CA"
    south_korea = "KR"
    russia = "RU"
    brazil = "BR"
    australia = "AU"
    spain = "ES"
    mexico = "MX"
    indonesia = "ID"
    netherlands = "NL"
    switzerland = "CH"
    sweden = "SE"
    belgium = "BE"
    austria = "AT"
    argentina = "AR"
    norway = "NO"
    czech_republic = "CZ"


class CountryCodeSteamCurrencyMapping(Enum):
    @classmethod
    def get(cls, code):
        return cls[code].value if code in cls.__members__ else None

    US = "USD"
    CN = "CNY"
    JP = "JPY"
    DE = "EUR"
    IN = "INR"
    GB = "GBP"
    FR = "EUR"
    IT = "EUR"
    CA = "CAD"
    KR = "KRW"
    RU = "RUB"
    BR = "BRL"
    AU = "AUD"
    ES = "EUR"
    MX = "MXN"
    ID = "IDR"
    NL = "EUR"
    CH = "CHF"
    SE = "SEK"
    BE = "EUR"
    AT = "EUR"
    AR = "USD"
    NO = "NOK"
    CZ = "CZK"

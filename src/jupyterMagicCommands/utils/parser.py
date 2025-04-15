import logging

def parse_logLevel(loglevel: str) -> int:
    numeric_level = getattr(logging, loglevel.upper(), None)
    if numeric_level is None:
        try:
            numeric_level = int(loglevel)
        except Exception as e:
            raise ValueError(f"Can't parse a valid loglevel from: {loglevel}. The logLevel should either a string or an integer. The valid log levels are: {', '.join([l for l in logging._nameToLevel.keys()])}")
    return numeric_level
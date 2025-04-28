class FileSystemMode:

    def __init__(self, mode: int):
        if mode is not None:
            if not isinstance(mode, int):
                raise ValueError("mode should be an integer")
            if mode < 0 or mode > 0o777:
                raise ValueError("mode should be between 0 and 0o777")
        self.mode = mode

    def to_octal(self) -> int:
        """
        Convert the mode to octal

        Example: 0o777 -> 777
                 0o644 -> 644
        """
        return int(oct(self.mode).strip("0o"))

    def to_decimal(self) -> int:
        """
        Convert the mode to decimal

        Example: 0o777 -> 0o777
                 0o644 -> 0o644
        """
        return self.mode

    @classmethod
    def from_string(cls, mode: str):
        return cls(int(mode, 8))

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, FileSystemMode):
            return False
        return self.mode == value.mode

    def __hash__(self) -> int:
        return hash(self.mode)
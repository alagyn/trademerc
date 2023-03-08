# Utilities for printing tabular data
import sys
from typing import TextIO, Tuple, Optional, List


class Column:
    def __init__(self,
                 header: str,
                 width: int,
                 formatStr: str,
                 fill: str = "",
                 headerAlign: str = "^",
                 valueAlign: str = "^"
                 ) -> None:
        self.header = header.strip()
        self.trueWidth = max(width, len(header))
        self.headerAlign = headerAlign
        self.formatStr = formatStr
        self.fill = fill
        self.valueAlign = valueAlign

    def valFmt(self) -> str:
        return f":{self.fill}{self.valueAlign}{self.trueWidth}{self.formatStr}"


class FloatColumn(Column):
    def __init__(self, header: str,
                 width: int,
                 precision: int,
                 fill: str = "",
                 headerAlign: str = "^",
                 valueAlign: str = "^"
                 ) -> None:
        super().__init__(header,
                         width,
                         f".{precision}f",
                         fill=fill,
                         headerAlign=headerAlign,
                         valueAlign=valueAlign
                         )
        # Add one for decimal
        self.trueWidth += precision + 1


class Tumble:
    def __init__(self, columns: List[Column], printHeader=False, stream: Optional[TextIO] = None) -> None:
        """
        Create a new table to format

        columns: list of tuples (column name: str, max width, format type)
        """

        self._format_str = ''
        self._header = ''
        self._stream: TextIO = stream if stream is not None else sys.stdout

        # Init lists
        header_vals = [""] * len(columns)
        format_vals = [""] * len(columns)
        line_vals = [""] * len(columns)

        for idx, col in enumerate(columns):
            name_fmt = f'| {{:{col.headerAlign}{col.trueWidth}s}} '
            header_vals[idx] = name_fmt.format(col.header)
            format_vals[idx] = f'| {{{col.valFmt()}}} '
            line_vals[idx] = f'|{"-" * (len(header_vals[idx]) - 1)}'

        self._header = "".join(header_vals) + "|\n" + "".join(line_vals) + "|"
        self._format_str = "".join(format_vals).strip() + " |"

        if printHeader:
            self.print_header()

    def print_header(self) -> None:
        print(self._header, file=self._stream)

    def header(self) -> str:
        return self._header

    def row(self, *values) -> str:
        return self._format_str.format(*values)

    def print_row(self, *values) -> None:
        print(self.row(*values), file=self._stream)

import dataclasses
import subprocess
from typing import List


@dataclasses.dataclass
class Result:
    filename: str
    page_number: str
    match: str


def parse(s: str):
    f = s.split(":")
    return Result(
        filename=f[0].strip(),
        page_number=int(f[1]),
        match=f[2].strip()
    )


def search(path: str, term: str) -> List[Result]:
    output = subprocess.check_output(
        ["pdfgrep", "-r", "-i", "-n", term, path]
    ).decode("utf-8")
    lns = output.split("\n")
    rs = list(
        map(
            parse,
            filter(
                lambda x: x.strip() != '',
                lns
            )
        )
    )
    return rs


def activate_pdf(result: Result, query: str):
    # search all windows
    try:
        by_class = subprocess.check_output(
            ["xdotool", "search", "--onlyvisible", "--class", "evince"]
        ).decode("utf-8").strip().split("\n")
    except subprocess.CalledProcessError:
        by_class = []

    # activate if already there
    for c in by_class:
        name = subprocess.check_output(
            ["xdotool", "getwindowname", c]
        ).decode("utf-8").strip()

        file_name = result.filename.split("/").pop()
        if name == file_name:
            subprocess.check_output(
                ["xdotool", "windowactivate", c]
            )
            return

    subprocess.check_output(
        ["setsid", "flatpak", "run", "org.gnome.Evince", "-p",
         result.page_number, "-l", query, result.filename]
    )


activate_pdf(
    Result(
        filename="/home/till/Uni/WISE 21-22/Altklausuren/gbs/exam-2020.pdf",
        page_number="17",
        match="Multiple Choice"
    ),
    "multiple choice"
)

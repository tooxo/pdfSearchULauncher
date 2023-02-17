import dataclasses
import json
import subprocess
from typing import Dict, List

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.ExtensionCustomAction import \
    ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import \
    RenderResultListAction
from urllib import request


def http_request(page: str):
    ret = request.urlopen(page)
    by = ret.read()
    return by.decode()


@dataclasses.dataclass
class Result:
    filename: str
    page_number: str
    match: str


def parse(s: str):
    f = s.split(":")
    return Result(
        filename=f[0].strip(),
        page_number=f[1],
        match=f[2].strip()
    )


def search(path: str, term: str) -> List[Result]:
    try:
        output = subprocess.check_output(
            ["pdfgrep", "-r", "-i", "-n", term, path, "--cache"],
            timeout=5
        ).decode("utf-8")
    except subprocess.CalledProcessError:
        return []
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
        if name.startswith(file_name):
            subprocess.check_output(
                ["xdotool", "windowactivate", c]
            )
            return

    subprocess.check_output(
        ["setsid", "flatpak", "run", "org.gnome.Evince", "-p",
         result.page_number, "-l", query, result.filename]
    )


class DemoExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class ItemEnterEventListener(EventListener):
    def on_event(self, event: ItemEnterEvent, extension):
        # event is instance of ItemEnterEvent

        (result, query) = event.get_data()
        activate_pdf(result, query)


class KeywordQueryEventListener(EventListener):
    def on_event(self, event: KeywordQueryEvent, extension: Extension):
        path = extension.preferences["path"]
        try:
            items = []
            pdfs = search(path, event.get_argument())

            pdfs = list(pdfs)[:10]

            if len(pdfs) == 0:
                return RenderResultListAction(
                    [
                        ExtensionResultItem(
                            icon='images/icon.png',
                            name="no results found",
                            description="",
                            on_enter=HideWindowAction()
                        )
                    ]

                )

            for i in pdfs:
                items.append(
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name=i.match,
                        description=i.filename + ":P" + i.page_number,
                        on_enter=ExtensionCustomAction(
                            (i, event.get_argument()),
                            keep_app_open=False
                        )
                    )
                )

            return RenderResultListAction(items)
        except BaseException as e:
            return RenderResultListAction(
                [
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name="error searching pdfs",
                        description=e,
                        on_enter=HideWindowAction()
                    )
                ]
            )


if __name__ == '__main__':
    DemoExtension().run()

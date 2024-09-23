from contextlib import suppress
from datetime import datetime
from filelock import FileLock as fileLock
from json import dumps as jsondumps, load as jsonload
from math import floor
from os import makedirs
from os.path import dirname, abspath, join as joinPath
from re import match as matchRegEx
from shutil import get_terminal_size as getTerminalSize
from time import sleep
from typing import Any as anyType

root: str = dirname(abspath(__file__))

terminalWidth: int = getTerminalSize().columns
notesjsonlock: fileLock = fileLock(joinPath(root, "notes.json.lock"))
cache: dict[int, anyType] = {}
#! reserved cache: 0,2,3
def millisecondstoSeconds(milliseconds: int) -> float:
    return milliseconds / 1000
mitse = millisecondstoSeconds

class cli:
    def parseInputString(input: str) -> tuple[str, list[str], str]:
        regExPatterns: dict[str, str] = {
            "command": r"(\w+)",
            "options": r"((?:\s+-\w+)*)?",
            "body": r"(\s+.*)?"
        }
        regExPatterns["full"] = regExPatterns["command"] + regExPatterns["options"] + regExPatterns["body"]
        parsedString = matchRegEx(regExPatterns["full"], input)
        if parsedString != None:
            command: str = parsedString.group(1)
            if parsedString.group(2) != None:
                options: list[str] = parsedString.group(2).split(" ")
            else: options: list[str] = []
            if parsedString.group(3) != None:
                body: str = parsedString.group(3)
            else: body: str = ""
        elif parsedString == None:
            command: str = ""
            options: list[str] = []
            body: str = ""
        return command, options, body
    def processUserInput(input: str) -> None:
        command, commandOptions, commandBody = cli.parseInputString(input)
        if command == "notes":
            print(desktopnotes.loadNotes(input))
        elif command == "note":
            desktopnotes.newNote(commandOptions, commandBody)
        elif command == "delnote":
            desktopnotes.deleteNote(commandBody)
        elif command == "backup":
            desktopnotes.backupNotes(commandOptions)
        elif "q" in command:
            quit()
class desktopnotes:
    def build() -> None:
        makedirs(joinPath(root, "backups"), exist_ok=1)
        with suppress(FileExistsError): open(joinPath(root, "notes.json"), "x").close()
        desktopnotes.initiatejson()
    def backupNotes(commandOptions: list[str]) -> None:
        with notesjsonlock:
            if "-txt" in commandOptions:
                with open(joinPath(root, "backups", f"{datetime.now().strftime('%d-%m-%Y (%H-%M-%S)')}.txt"), "wt", encoding="utf-8") as backuptxt:
                    backuptxt.write(desktopnotes.loadNotes().strip("_").removeprefix("\n").removesuffix("\n"))
            else:
                with open(joinPath(root, "notes.json"), "rt", encoding="utf-8") as notesjson:
                    notes: str = notesjson.read()
                with open(joinPath(root, "backups", f"{datetime.now().strftime('%d-%m-%Y (%H-%M-%S)')}.json"), "wt", encoding="utf-8") as backupjson:
                    backupjson.write(notes)
    def deleteNote(commandBody: str) -> None:
        if "all" in commandBody:
            with notesjsonlock:
                with open(joinPath(root, "notes.json"), "wt", encoding="utf-8") as notesjson:
                    notesjson.write()
            desktopnotes.initiatejson()
        elif "all" not in commandBody:
            commandBody: list[str] = commandBody.split(" ")
            cache[0] = set()
            for eachString in commandBody:
                try:
                    cache[0].add(int(eachString))
                except ValueError:
                    pass
            commandBody: set[str] = {str(eachInteger) for eachInteger in cache[0]}
            with notesjsonlock:
                with open(joinPath(root, "notes.json"), "rt", encoding="utf-8") as notesjson:
                    notes: dict[str, dict[str, str]] = jsonload(notesjson)
                for eachString in commandBody:
                    if eachString in notes:
                        notes.pop(eachString)
                with open(joinPath(root, "notes.json"), "wt", encoding="utf-8") as notesjson:
                    notesjson.write(jsondumps(notes, indent=4))
    def initiatejson() -> None:
        with notesjsonlock:
            try:
                with open(joinPath(root, "notes.json"), "rt", encoding="utf-8") as notesjson:
                    notes: str = notesjson.read()
            except FileNotFoundError:
                open(joinPath(root, "notes.json"), "x").close()
            if len(notes) < 2:
                with open(joinPath(root, "notes.json"), "wt", encoding="utf-8") as notesjson:
                    notesjson.write("{}")
    def loadNotes(input: str = False) -> str:
        with notesjsonlock:
            with open(joinPath(root, "notes.json"), "rt", encoding="utf-8") as notesjson:
                notes: dict[str, dict[str, str]] = jsonload(notesjson)
        if notes:
            output: str = ""
            output += "_" * terminalWidth + "\n"
            output += " " * floor(terminalWidth / 2 - 3) + "Notes:\n\n"
            for eachNoteIndex, eachNote in notes.items():
                for eachFlag in eachNote["flags"]:
                    output += " " + eachFlag
                output += " | " + eachNoteIndex + " |" + eachNote["body"] + "\n\n"
            output = output.removesuffix("\n")
            output += "_" * terminalWidth
        elif not notes and not input:
            output: str = "Nothing noted.\n"
        elif not notes and input:
            output: str = "\nNothing noted.\n"
        return output
    def newNote(commandOptions: list[str], commandBody: str) -> None:
        if commandBody == "":
            return
        commandOptions: list[str] = desktopnotes.transformOptionstoFlags(commandOptions)
        if len(commandOptions) < 1:
            commandOptions: list[str] = [""]
        with notesjsonlock:
            with open(joinPath(root, "notes.json"), "rt", encoding="utf-8") as notesjson:
                notes: dict[str, dict[str, str]] = jsonload(notesjson)
            newNoteIndex: int = max([int(eachKey) for eachKey in list(notes.keys())], default=0) + 1
            notes[newNoteIndex] = {
                "flags": commandOptions,
                "body": commandBody
            }
            with open(joinPath(root, "notes.json"), "wt", encoding="utf-8") as notesjson:
                notesjson.write(jsondumps(notes, indent=4))
        print()
    def transformOptionstoFlags(options: list[str]) -> list[str]:
        cache[2] = []
        cache[3] = set()
        for eachOption in options:
            if eachOption.lower() not in cache[3]:
                if "-i" in eachOption:
                    cache[3].update(["-i", "-id", "-ide", "-idea"])
                    cache[2].append("IDEA")
                elif "-t" in eachOption:
                    cache[3].update(["-t", "-to", "-tod", "-todo"])
                    cache[2].append("TODO")
        options: list[str] = cache[2]
        return options
    def unlaunch(delay: int = 1000):
        sleep(mitse(delay))
        quit()

desktopnotes.build()
print(desktopnotes.loadNotes())
desktopnotes.initiatejson()

userInput: str = input(">")

while True:
    cli.processUserInput(userInput)
    userInput: str = input(">")
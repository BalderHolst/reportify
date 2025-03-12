#!/usr/bin/env python

import sys
import os
import subprocess
import re

############### CONFIGURATION ##############

SECTION_LABEL = "SECTION"
TITLE_LABEL = "TITLE"
AUTHOR_LABEL = "AUTHOR"
DATE_LABEL = "DATE"
SHOW_CODE_LABEL = "SHOW"
SPAN_LABEL = "SPAN"
CAPTURE_CODE_LABEL = "CAPTURE"
OUTPUT_CODE_LABEL = "OUTPUT"

COMMENT_PREFIX = "//!"

SPAN_BOX_COLOR = "green"
CODE_BOX_COLOR = "blue"
OUTPUT_BOX_COLOR = "orange"

############## IMPLEMENTATION ##############

HEADER = f"""\
#define {SECTION_LABEL}(S) std::cout << "\\n{SECTION_LABEL}: " << (S) << std::endl;
#define {TITLE_LABEL}(S)
#define {AUTHOR_LABEL}(S)
#define {DATE_LABEL}(S)
#define {SHOW_CODE_LABEL} std::cout << "\\n{SHOW_CODE_LABEL}" << std::endl;
#define {CAPTURE_CODE_LABEL} std::cout << "\\n{CAPTURE_CODE_LABEL}" << std::endl;
#define {OUTPUT_CODE_LABEL} std::cout << "\\n{OUTPUT_CODE_LABEL}" << std::endl;
#define {SPAN_LABEL}(TITLE, FILE, START, END) std::cout << "\\n{SPAN_LABEL}: " << (TITLE) << ":" << (FILE) << ":" << (START) << ":" << (END) << std::endl;\
"""

def error(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def trim_empty_lines(lines: list[str]) -> list[str]:
    if len(lines) == 0: return
    start = 0
    end = len(lines)
    while lines[start].strip() == "" and start < end - 1: start += 1
    while lines[end-1].strip() == "" and start < end - 1: end -= 1
    return lines[start:end]

class Block:
    def to_tex(self) -> str:
        raise NotImplementedError()

class Text(Block):
    text: str

    def __init__(self, text: str):
        self.text = text

    def to_tex(self) -> str:
        return self.text

class Box(Block):
    title: str
    code: str
    lang: str
    color: str
    linenos: bool

    def __init__(self, title: str, code: str, lang: str, color: str, linenos: int = True):
        self.title = title
        self.code = code
        self.lang = lang
        self.color = color
        self.linenos = linenos

    def to_tex(self) -> str:

        s = ""
        s += f"\\begin{{tcolorbox}}[enhanced, title=\\hspace{{-10pt}}\\vspace{{-2pt}}{self.title}\\vphantom{{g}}, colback={self.color}!10, title style={{baseline}}, boxsep=8pt, coltitle=black, fonttitle=\\bfseries, colbacktitle={self.color}!30, colframe=black, arc=2mm, boxrule=0.8pt, listing only, breakable]"
        s += f"\\begin{{minted}}[fontsize=\\footnotesize, autogobble, numbersep=6pt,"
        if self.linenos: s += "linenos, "
        s += f"breaklines, breakanywhere]{{{self.lang}}}\n"
        s += "\n".join(self.code).strip('\n')
        s += "\n\\end{minted}\n"
        s += "\\end{tcolorbox}\n"
        return s.strip()

class SpanBox(Box):
    def __init__(self, title: str, code: str, lang: str = "c++"):
        super().__init__(title, code, lang, SPAN_BOX_COLOR)

class CodeBox(Box):
    def __init__(self, code: str, lang: str = "c++"):
        super().__init__("Code", code, lang, CODE_BOX_COLOR)

class OutputBox(Box):
    def __init__(self, output: str):
        super().__init__("Output", output, "text", OUTPUT_BOX_COLOR, linenos=False)

class Section(Block):
    title: str

    def __init__(self, title: str):
        self.title = title

    def to_tex(self) -> str:
        return f"\\section*{{{self.title}}}"

class Document:
    title: str | None
    author: str | None
    date: str | None
    intro: str | None
    blocks: list[Block]

    def __init__(self, title=None, author=None, date=None):
        self.title = title
        self.author = author
        self.date = date
        self.blocks = []

    def gather_metadata(self, source_lines: list[str]):
        for line in source_lines:
            line = line.strip()

            # Title label
            m = re.match(f'^{TITLE_LABEL}' + r'\("(.+)"\)', line)
            if m:
                if self.title:
                    error(f"WARNING: Title already set to '{self.title}'. Overriding with '{m.group(1)}'")
                self.title = m.group(1)

            # Author label
            m = re.match(f'^{AUTHOR_LABEL}' + r'\("(.+)"\)', line)
            if m:
                if self.author:
                    error(f"WARNING: Author already set to '{self.author}'. Overriding with '{m.group(1)}'")
                self.author = m.group(1)

            # Date label
            m = re.match(f'^{DATE_LABEL}' + r'\("(.+)"\)', line)
            if m:
                if self.date:
                    error(f"WARNING: Date already set to '{self.date}'. Overriding with '{m.group(1)}'")
                self.date = m.group(1)

    @classmethod
    def from_source_and_output(cls, source: str, output: str):
        doc = cls()

        source_lines = source.split('\n')
        output_lines = output.split('\n')

        doc.gather_metadata(source_lines)

        source_cursor = 0
        output_cursor = 0

        code_start = None
        output_start = None

        while source_cursor < len(source_lines):
            source_line = source_lines[source_cursor].strip()

            # Parse SECTION statements in source code

            section_match = re.match(f'^{SECTION_LABEL}' + r'\("(.+)"\)', source_line)
            if section_match:
                title = section_match.group(1)
                doc.blocks.append(Section(title))

            # Parse latex comments
            elif source_line.startswith(COMMENT_PREFIX):
                latex = source_line[len(COMMENT_PREFIX):].strip()

                # Append to previous text item if it is a text item
                if len(doc.blocks) > 0 and isinstance(doc.blocks[-1], Text):
                    doc.blocks[-1].text += "\n" + latex
                else:
                    doc.blocks.append(Text(latex))

            # Parse SPAN statements in source code
            elif source_line.startswith(f"{SPAN_LABEL}"):

                # Find the SPAN statement in the output
                while not output_lines[output_cursor].strip().startswith(f"{SPAN_LABEL}"):
                    output_cursor += 1

                output_line = output_lines[output_cursor].strip()[len(SPAN_LABEL)+1:].strip()

                parts = output_line.split(':')

                [title, file, start, end] = parts

                with open(file, 'r') as f:
                    code = f.readlines()[int(start)-1:int(end)]

                code = [l.strip("\n") for l in code]

                doc.blocks.append(SpanBox(title, code))

            # Parse SHOW statements in source code
            elif source_line.startswith(f"{SHOW_CODE_LABEL}"):

                # Find statement SHOW in the output
                while not output_lines[output_cursor].strip().startswith(f"{SHOW_CODE_LABEL}"):
                    output_cursor += 1

                # Mark starting points
                code_start = source_cursor
                output_start = output_cursor

            # Parse CAPTURE statements in source code
            elif source_line.startswith(f"{CAPTURE_CODE_LABEL}"):

                # Find the CAPTURE statement in the output
                while not output_lines[output_cursor].strip().startswith(f"{CAPTURE_CODE_LABEL}"):
                    output_cursor += 1

                # Mark starting points
                code_start = None
                output_start = output_cursor


            # Parse OUTPUT statements in source code
            elif source_line.startswith(f"{OUTPUT_CODE_LABEL}"):

                # Find the OUTPUT statement in the output
                while not output_lines[output_cursor].strip().startswith(f"{OUTPUT_CODE_LABEL}"):
                    output_cursor += 1

                if code_start is not None:
                    doc.blocks.append(CodeBox(source_lines[code_start+1:source_cursor]))

                if output_start is not None:
                    doc.blocks.append(OutputBox(output_lines[output_start+1:output_cursor]))

                code_start = None
                output_start = None

            source_cursor += 1

        if code_start is not None:
            doc.blocks.append(CodeBox(source_lines[code_start+1:]))

        if output_start is not None:
            doc.blocks.append(OutputBox(output_lines[output_start+1:]))

        return doc


    def to_tex(self) -> str:

        preamble =  f"""\
\\documentclass[12pt]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{minted}}
\\usepackage[most]{{tcolorbox}}
\\tcbuselibrary{{listingsutf8}}
\\setlength{{\\parindent}}{{0pt}}
"""

        title = ""
        if self.title:
            title += f"{{\\huge {self.title}}}\n" + "\\vspace{3mm}\n\n"
        else:
            error("WARNING: No title set")

        if self.author:
            title += f"{{\\large \\textsl{{{self.author}}}}}\n" + "\\vspace{1mm}\n\n"

        if self.date:
            title += f"{self.date}\n"

        title += "\\vspace{11mm}\n"

        contents = "\n\n".join([b.to_tex() for b in self.blocks])

        return f"""\
{preamble}
\\begin{{document}}
\\begin{{center}}
{title}
\\end{{center}}
{contents}
\\end{{document}}
"""


    def __repr__(self):
        return f"Document[{len(self.sections)}]"

def usage(program: str):
    error(f'Usage: {program} [OPTIONS] <source.c> <executable>')
    error()
    error(f'Options:')
    error(f'  -h, --help            Display this help message')
    error(f'  -g, --generate-header Generate header file')

def main():
    [program, *args] = sys.argv

    while args and args[0].startswith('-'):
        option = args.pop(0)
        match option:
            case '-h' | '--help':
                usage(program)
                sys.exit(0)
            case '-g' | '--generate-header':
                print(HEADER)
                sys.exit(0)
            case _:
                error(f"Unknown option: {option}\n")
                usage(program)
                sys.exit(1)

    if len(args) < 2:
        error("Not enough arguments\n")
        usage(program)
        sys.exit(1)


    source_path, executable_path = args

    if not os.path.exists(source_path):
        error(f"Source file '{source_path}' does not exist")
        sys.exit(1)

    if not os.path.exists(executable_path):
        error(f"Executable file '{executable_path}' does not exist")
        sys.exit(1)

    # Convert executable to absolute path
    executable_path = os.path.abspath(executable_path)

    with open(source_path, 'r') as source:
        source = source.read()

    # Run executable and capture output
    proc = subprocess.run([executable_path], stdout=subprocess.PIPE)

    output = proc.stdout.decode('utf-8')

    document = Document.from_source_and_output(source, output)

    latex = document.to_tex()

    print(latex)


if __name__ == '__main__':
    main()

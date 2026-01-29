from contextlib import redirect_stderr

import pymupdf  # PyMuPDF
import pymupdf.layout
import pymupdf4llm
import re
import json
import http.server
import socketserver
from pathlib import Path
from pprint import pprint


file = 'assets/Ontwerpnotulen openbare zitting-1.pdf'

doc = pymupdf.open(file)

if not open("assets/Ontwerpnotulen openbare zitting-1.json"):
    external_file = pymupdf4llm.to_json(doc, header=False, footer=False, show_progress=True)
    suffix = ".json" # or ".json" or ".txt"
    Path(doc.name).with_suffix(suffix).write_bytes(external_file.encode())

pattern_gr_code = r"\b\d{4}_[A-Za-z]{2}_\d{5}\b"

headers = [
    "status",
    "beschrijving",
    "besluit",
    "bijlagen"
]

ignore = [
    'page-footer',
    'page-header',
    'picture'
]


class VotePoint:

    status = []
    beschrijving = []
    besluit = []
    bijlagen = []

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {
            self.name: {
                "status": self.status,
                "beschrijving": self.beschrijving,
                "besluit": self.besluit,
                "bijlagen": self.bijlagen,
            }
        }

    def __str__(self):
        return json.dumps(self.to_dict())

info = {}
collect_text = False
current_point = None
current_subtitle = None

def process_page(page):
    global collect_text
    global info
    global current_point
    global current_subtitle

    page = page["boxes"]
    zittingen = []

    for box in page:
        openbare_zitting = []

        if box['boxclass'] in ignore:
            continue

        if box['boxclass'] == 'section-header':
            line = parse_box(box)
            if collect_text:
                # nieuwe hoofding gedetecteerd, dus collect text moet weer op false
                if re.match(r"^\d+\s+[^.:]", line):
                    collect_text = False
                elif line.lower() not in headers:
                    getattr(info[current_point], current_subtitle.lower()).append(line)
                else:
                    current_subtitle = line

            # start van een belangrijk agendapunt
            if re.match(r"^\d+\s+[^.:]", line):
                match = re.search(pattern_gr_code, line)
                if match:
                    gr_code = match.group()
                    current_point = gr_code
                    info[current_point] = VotePoint(line)
                else:
                    continue
                collect_text = True

        if box['boxclass'] == 'text':
            line = parse_box(box)
            if collect_text:
                getattr(info[current_point], current_subtitle.lower()).append(line)
        if len(openbare_zitting) > 0:
            zittingen.append(openbare_zitting)
    return zittingen

def parse_box(box):
    box_string = ""
    for textlines in box['textlines']:
        textline_total = ""
        for spans in textlines['spans']:
            textline_total += spans['text']
        textline_total = re.sub(r"(\d)([A-Za-z])", r"\1 \2", textline_total)
        box_string += textline_total
    return box_string


def process_json(json_file):
    with open(json_file) as json_file:
        data = json.load(json_file)

        zittingen = []
        for page in data["pages"]:
            result = process_page(page)

            if len(result) > 0:
                zittingen.extend(result)
        collect_text = False


    json.dump([info[x].to_dict() for x in info], open("assets/out/out.json", "w"))

    for punt in info:
        print(str(info[punt]))
        #print(zittingen)

process_json("assets/Ontwerpnotulen openbare zitting-1.json")

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    # Start the server and keep it running until you stop the script
    httpd.serve_forever()

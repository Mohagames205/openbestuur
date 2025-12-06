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

collect_text = False


def process_page(page):
    global collect_text
    page = page["boxes"]
    zittingen = []

    for box in page:
        openbare_zitting = []
        info_zitting = []


        if box['boxclass'] in ignore:
            continue

        #print(box['boxclass'])

        if box['boxclass'] == 'section-header':
            line = parse_box(box)
            if collect_text:
                if re.match(r"^\d+\s+[^.:]", line):
                    collect_text = False
                else:
                    print(line)

            # start van een belangrijk agendapunt
            if re.match(r"^\d+\s+[^.:]", line):
                print(line)
                collect_text = True

        if box['boxclass'] == 'text':
            line = parse_box(box)
            if collect_text:
                print(line)


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
        for page in data["pages"] :
            result = process_page(page)

            if len(result) > 0:
                zittingen.extend(result)
        collect_text = False

        #print(zittingen)

process_json("assets/Ontwerpnotulen openbare zitting-1.json")

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    # Start the server and keep it running until you stop the script
    httpd.serve_forever()

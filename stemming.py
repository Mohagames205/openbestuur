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


def process_page(page):
    page = page["boxes"]
    zittingen = []
    for box in page:
        collect_text = False
        collect_info = False

        openbare_zitting = []
        info_zitting = []
        if box['boxclass'] == 'section-header':
            line = parse_box(box)


            # start van een belangrijk agendapunt
            if re.match(r"^\d+\s+[^.:]", line):
                collect_text = True
                print(line)

        if collect_text:




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

        #print(zittingen)

process_json("assets/Ontwerpnotulen openbare zitting-1.json")

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    # Start the server and keep it running until you stop the script
    httpd.serve_forever()

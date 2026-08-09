"""One-shot default-browser map picker for CityGen.

It is intentionally an ephemeral browser callback, not a persistent bridge or
3ds Max service. The browser posts the selected coordinates to localhost and
this module writes ``citygen-map-result.json`` for the Max UI to consume.
"""

from __future__ import annotations

import json
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs


RESULT_FILE_NAME = "citygen-map-result.json"


def result_path() -> Path:
    return Path(tempfile.gettempdir()) / RESULT_FILE_NAME


def open_picker() -> Path:
    output = result_path()
    output.unlink(missing_ok=True)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            body = _PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            size = int(self.headers.get("Content-Length", "0"))
            values = parse_qs(self.rfile.read(size).decode("utf-8"))
            payload = {"latitude": float(values["latitude"][0]), "longitude": float(values["longitude"][0]), "label": values.get("label", ["Selected site"])[0]}
            output.write_text(json.dumps(payload), encoding="utf-8")
            self.send_response(204)
            self.end_headers()
            threading.Thread(target=self.server.shutdown, daemon=True).start()

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    webbrowser.open(f"http://127.0.0.1:{server.server_port}")
    return output


_PAGE = """<!doctype html><html><head><meta charset=\"utf-8\"><title>CityGen Map Picker</title><style>html,body,#map{height:100%;margin:0}#bar{position:fixed;z-index:2;left:12px;top:12px;background:#fff;padding:10px;border-radius:4px}</style><link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\"></head><body><div id=\"bar\"><input id=\"label\" value=\"Selected site\"><button onclick=\"choose()\">Use this site</button></div><div id=\"map\"></div><script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script><script>let p=[25.2048,55.2708],m=L.map('map').setView(p,13),marker=L.marker(p,{draggable:true}).addTo(m);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors'}).addTo(m);m.on('click',e=>{p=[e.latlng.lat,e.latlng.lng];marker.setLatLng(p)});marker.on('dragend',e=>{let q=e.target.getLatLng();p=[q.lat,q.lng]});function choose(){fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'latitude='+p[0]+'&longitude='+p[1]+'&label='+encodeURIComponent(document.getElementById('label').value)}).then(()=>document.body.innerHTML='<p>Site sent to CityGen. You may close this tab.</p>')}</script></body></html>"""

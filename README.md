# KoSa

**A home assistant you can run on your laptop, with no hardware and nothing to pay for.**
I built this project as a solo endevour over the past year to bring to life a long standing idea, using it as a canvas to pratice and compile everything I have been learning over the years into a genuine useful application. Because development started locally, I am only just now migrating the codebase to version control and github.

## Project Evolution
* Phase 1: text/voice terminal assistant
* Phase 2: Envionment simulation (mapping spoken commands to actions in simulated environment)

Early prototype (v0.1).

KoSa controls a simulated house, talks back in plain sentences, keeps a catalogue of your books, recognises visitors at the door, and can drive real devices through a USB board when you have one.

<!-- docs/screenshot.png -->

## What is real and what is simulated

| Feature | Status |
|---|---|
| Home model (rooms, lights, fans, door locks), floor-plan interface | Real. The house itself is virtual. |
| Safety rules (confirm before unlocking, guest/owner roles, emergency lock-down) | Real |
| Chat assistant with natural replies | Real |
| Voice ("Hey KoSa"), spoken replies | Real, through the browser (Chrome or Edge). Chrome may send audio to Google's speech service. |
| Word Bank (your own words, nicknames, phrases, mishearing fixes) | Real |
| Personal library (add, search, locate books) | Real |
| Face recognition at the door | Real. Photos are matched on your computer with OpenCV (YuNet + SFace). See limits below. |
| Door camera feed | You supply the image (upload a photo or use your webcam). No live IP/doorbell camera yet. |
| Summaries and stories | Needs [Ollama](https://ollama.com) running locally. Answers are labelled AI-generated and may contain errors. |
| USB hardware control | Experimental. The code is tested against simulated boards, not yet against real hardware. |

## Quick start

Requires Python 3.10 or newer (developed on 3.12). Voice needs Chrome or Edge.

```
pip install -r requirements.txt
python models/download_models.py     # models (optional)
python run.py                        # opens http://localhost:8000
```

`run.py` opens `http://localhost:8000` for you. Do not open `static/index.html` directly: the page needs the Python server.


## Face recognition

On the **Door camera** page, add a person with a name and a photo (upload one, or use your webcam). Then give KoSa a visitor photo. It finds the face, compares it with the people it knows and announces the result.

Limitations:
- It compares one photo per person, so side angles, glasses and poor light lower accuracy.
- It is **not security-grade**, and a printed photo can fool it. Do not use it to protect anything important.
- Photos and face data stay in `KoSa.db` on your machine.
- Without the models KoSa still runs; the camera page tells you what is missing.

## Connecting real hardware (experimental)

See [`hardware/README.md`](hardware/README.md). In short: upload `hardware/KoSa_device/KoSa_device.ino` to an Arduino-style board, plug it in, and pair a device on the **Devices** page. You can test without a board using `python hardware/fake_board.py` or the free Wokwi simulator.



## Project layout

```
core.py        commands, replies and safety checks
server.py      web API
library.py     book catalogue
wordbank.py    the user's own vocabulary
faces.py       people and face recognition
drivers.py     USB serial layer
llm.py         optional Ollama connection
home.json      the house (edit it to build your own)
run.py         starts the server and opens the browser
static/        web interface (HTML, CSS, JavaScript)
hardware/      board firmware, fake board, Wokwi project
models/        face model downloader
tests/         automated tests
```

## Tests

```
pip install -r requirements-dev.txt
python -m pytest
```

The suite covers replies, safety rules, the Word Bank, the library, the serial layer (against a pretend board) and the API. Face tests run only when the models are downloaded. `tests/data/astronaut.jpg` is a public-domain NASA photograph, included with scikit-image, used to test face matching.

## Roadmap

Real doorbell/IP camera input, more than one photo per person, Wi-Fi boards (ESP32), servo and sensor support, a layout editor for the house.

## Privacy

Everything runs locally. The only optional network use is the browser's speech recognition and a local Ollama server you run yourself.

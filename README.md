# nlpartgenerator (Text2Art)

A Flask web app that generates AI artwork from text prompts. A user submits a
name, email, and one or more text prompts through a simple web form; the
request is queued in MongoDB, and a separate background worker process picks
up queued jobs, generates an image using the [pixray](https://github.com/pixray/pixray)
text-to-image pipeline (VQGAN/CLIP-based), watermarks the result, and emails
the finished image back to the user.

## What it actually does

- `app.py` is a small Flask app with three real routes:
  - `GET /` — renders `templates/home.html`, a form (name, email, prompts,
    aspect ratio, quality, publish flag).
  - `POST /generate` — reads the form fields, inserts a "queue" document into
    MongoDB via `src/text2art/utils.py`, and flashes a message with an
    estimated wait time (`queue_no * 4` hours).
  - `GET /images/<filename>` — serves a generated image file from
    `data/output/`.
- `worker.py` runs as a separate long-lived process (see `Procfile`). It polls
  the MongoDB `users` collection for the oldest queued job, calls
  `src/text2art/maintenance.py:generate()` to run the pixray pipeline, applies
  a watermark to the output image, records the result in an `images`
  collection, and emails the image to the requester via Gmail SMTP.
- Image generation itself is delegated to the vendored `pixray/` library
  (which in turn vendors `CLIP/` and `taming-transformers/`), driven with a
  fixed `textoff` vector-prompt setting and an iteration count read from
  `config.yaml`.

## Tech stack

- **Backend**: Python 3.9, Flask, Gunicorn (see `runtime.txt`, `gunicorn_config.py`)
- **Queue/state**: MongoDB (via `pymongo`), no Redis/RQ usage found despite
  `redis`/`rq` being listed in `requirements.txt`
- **Art generation**: [pixray](https://github.com/pixray/pixray) (VQGAN,
  CLIP, taming-transformers), PyTorch/torchvision, Pillow
- **Email**: `smtplib` over Gmail SMTP (`smtp.gmail.com:465`)
- **Frontend**: server-rendered Jinja templates (`templates/home.html`,
  `templates/galary.html`) with Bootstrap 5 via CDN
- **Deployment target**: Heroku-style (`Procfile`, `runtime.txt`, `nltk.txt`
  all follow that convention)

## Features (inferred from code)

- Text-to-art submission form (name, email, prompt text, aspect ratio,
  quality, optional "publish")
- Queue-position feedback with a rough time estimate shown to the user
- Background worker that generates one image per queued job using pixray
- Watermarking of generated images before delivery
- Email delivery of the finished artwork to the submitter
- Endpoint to download/serve a generated image by filename
- A gallery template (`templates/galary.html`) exists but currently has no
  content/routes wired to it — `app.py` has a commented-out `/load` route
  that would have paginated a gallery via `get_imgages()`

## Project structure

```
app.py                     Flask web app (routes: /, /generate, /images/<file>)
worker.py                  Background job processor (polls Mongo, generates + emails art)
config.yaml                App config: secret key, email creds, Mongo URI, model iteration count
gunicorn_config.py         Gunicorn bind/worker settings
Procfile                   Heroku process types: web (gunicorn) + worker (python worker.py)
runtime.txt / nltk.txt     Python version / NLTK corpora for Heroku buildpacks
requirements.txt           Combined dependency list (torch, pixray deps, flask, pymongo, etc.)
src/
  basic_func.py             YAML config loader (get_value)
  text2art/
    utils.py                 Mongo setup, queueing, image listing helpers
    maintenance.py            Watermarking, email sending, pixray generation call
templates/
  home.html                  Main submission form page
  galary.html                 Gallery page (currently empty/unused)
pixray/                    Vendored pixray library (VQGAN/CLIP/line/pixel drawers)
CLIP/                       Vendored OpenAI CLIP repo
taming-transformers/         Vendored CompVis taming-transformers repo
```

## Setup / Installation

This project targets Python 3.9 and requires a MongoDB instance and a Gmail
account for outbound mail.

```bash
# 1. Create and activate a virtualenv (Python 3.9)
python3.9 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

`requirements.txt` pulls in heavy ML dependencies (PyTorch, CLIP,
taming-transformers, diffvg-related packages) and several git-based installs,
so first install can be slow and some packages (e.g. `diffvg`) require manual
build steps documented inline in `requirements.txt`.

Configure `config.yaml` before running:

```yaml
SECRET_KEY: '<flask-secret-key>'
EMAIL:
  address: <gmail-address>
  password: <gmail-app-password>
MONGODB_SETTINGS:
  db_link: <mongodb-connection-string>
MODEL:
  iteration: 1
```

**Note:** the `config.yaml` checked into this repo currently contains a live
MongoDB connection string and credentials in plaintext. Those should be
rotated and the file replaced with environment variables or a local,
git-ignored config before this project is used for anything real.

## Usage

Run the web app and the worker as two separate processes — they share the
Mongo `users` collection as a queue:

```bash
# Web server
python app.py                # dev server, or:
gunicorn --worker-tmp-dir /dev/shm --config gunicorn_config.py app:app

# Worker (separate process/terminal)
python worker.py
```

Then visit the app, submit the form at `/`, and the worker will pick up the
job, generate an image with pixray, watermark it, and email it to the
address provided.

## Notes / Status

This is a small, experimental personal project rather than a finished
product:

- No tests are present for the app/worker code (the only `tests/` directory
  belongs to the vendored `CLIP` dependency).
- The gallery feature is incomplete — the template exists but the route to
  populate/paginate it is commented out in `app.py`.
- `requirements.txt` lists `redis` and `rq` but neither is actually used
  anywhere in the code — queueing is done directly through MongoDB documents
  with a `status` field.
- The worker's polling loop (`while True` with a tight retry on empty queue)
  has no sleep/backoff, so it will busy-loop when idle.
- Secrets (Mongo URI, email password) are stored in a committed
  `config.yaml` rather than environment variables — this should be fixed
  before any real deployment.
- `pixray/`, `CLIP/`, and `taming-transformers/` are vendored copies of
  third-party repositories, not original code in this project.

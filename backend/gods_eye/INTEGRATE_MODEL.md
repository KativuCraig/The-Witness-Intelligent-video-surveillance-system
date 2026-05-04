## Integrating your YOLOv8 model into a Django backend (Windows PowerShell)

This document describes a plausible, minimal path to integrate the working model in this repo into a Django backend using a separate virtual environment.

### Goals / contract
- Input: image(s) or video file uploaded via HTTP (REST API).
- Output: JSON with detections (boxes, classes, confidences) and optionally annotated image/video.
- Success: endpoint returns inference results within usable latency; long jobs run asynchronously.

### Quick overview (high level)
1. Create a separate venv and install Python dependencies.
2. Add a new Django app (e.g., `inference`) with an API endpoint for inference.
3. Implement a model loader singleton/service that lazy-loads the YOLOv8 weights (`best.pt`) and exposes a predict() method.
4. Implement request handlers: small images -> synchronous; large videos/batches -> enqueue with Celery.
5. Wire media storage, config, and deployment notes (GPU vs CPU).

---

## 1) Create a new venv (PowerShell)
Run from project root in PowerShell:

```powershell
# create a venv called .venv_inference and activate it
python -m venv .venv_inference
.\.venv_inference\Scripts\Activate.ps1

# upgrade pip and install requirements (see notes for GPU)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you have an NVIDIA GPU and want GPU-accelerated inference, follow the official PyTorch install instructions and install the CUDA-enabled torch wheel, e.g. from https://pytorch.org. Replace the `torch` and `torchvision` lines above with the recommended commands from PyTorch's site.

## 2) Add a Django app and basic wiring
Inside your Django project:
- Create an app: `python manage.py startapp inference`.
- Add `'inference'` and `'rest_framework'` to `INSTALLED_APPS` in `settings.py`.
- Configure media storage (for uploaded files): set `MEDIA_ROOT` and `MEDIA_URL`.

Example minimal `settings.py` additions:

```python
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Optional: load environment variables
from dotenv import load_dotenv
load_dotenv()
```

## 3) Model loader service (singleton)
Create `inference/service.py` (example snippet):

```python
# inference/service.py
from ultralytics import YOLO
import threading

class YOLOModel:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, weights_path: str):
        self.model = YOLO(weights_path)

    @classmethod
    def get_instance(cls, weights_path: str = "runs/detect/The_Witness/violence_model/weights/best.pt"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = YOLOModel(weights_path)
        return cls._instance

    def predict(self, source, imgsz=640, conf=0.25):
        # returns ultralytics Results object
        return self.model.predict(source=source, imgsz=imgsz, conf=conf)
```

Notes:
- Lazy-loading keeps startup time small; model loads on first request.
- Ensure `weights_path` points to your `best.pt` in the repo (`runs/detect/.../weights/best.pt`).

## 4) API endpoint (synchronous for images)
Create a DRF view in `inference/views.py`:

- Accept `multipart/form-data` file uploads (image/video) or URL.
- For images: call `YOLOModel.get_instance().predict()` and transform results to JSON.
- For videos or long jobs: enqueue to Celery and return job id.

Example simplified view (concept):

```python
# inference/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .service import YOLOModel

class InferenceView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'file required'}, status=status.HTTP_400_BAD_REQUEST)

        # save to disk (media) or pass file-like object directly
        path = save_temp_file(file)
        model = YOLOModel.get_instance()
        results = model.predict(source=path)

        # convert results to JSON-friendly structure
        out = []
        for r in results:
            boxes = []
            for box in r.boxes:
                boxes.append({
                    'xyxy': box.xyxy.tolist(),
                    'conf': float(box.conf[0]),
                    'class': int(box.cls[0])
                })
            out.append({'boxes': boxes})

        return Response({'results': out})
```

(Implement `save_temp_file` to store uploads into `MEDIA_ROOT` and manage cleanup.)

## 5) Asynchronous processing (videos, batches)
For video processing or long-running jobs, use Celery + Redis:
- Configure `celery.py` at the project root.
- Create a Celery task that loads the same `YOLOModel.get_instance()` and runs inference.
- Enqueue video jobs from the API and return a task id. Provide a status endpoint to fetch results when ready.

Add to `requirements.txt`: `celery` and `redis`. Start a Redis server (or use a hosted redis) and run a worker locally:

```powershell
# start worker (PowerShell)
celery -A your_project_name worker --loglevel=info
```

## 6) Tests and quick local run
- Create unit tests for `service.py` and API endpoints. Test with a small sample image.
- Run Django server:

```powershell
python manage.py migrate
python manage.py runserver
```

## 7) Deployment notes
- For production, consider containerizing the Django app and optionally the model server (separate microservice) to isolate GPU dependencies.
- If using GPU, base the Docker image on an appropriate CUDA image and install the matching torch wheel.
- Use a process manager (Gunicorn + nginx) and ensure static/media files served securely (S3 or similar recommended for large uploads).

## Edge cases & tips
- Large video files: chunking and streaming are better than loading whole file into memory.
- Concurrency: limit number of concurrent inferences if using CPU-only server.
- Memory: free intermediate tensors (torch.cuda.empty_cache()) after GPU inference.
- Version compatibility: match `torch`/`torchvision` to `ultralytics` expectations.

## Optional next steps / enhancements
- Create a dedicated microservice just for inference with a minimal API (faster restarts, independent scaling).
- Add model versioning and a small admin UI to switch weights.
- Add structured logging and metrics (Prometheus + Grafana).

---

## Files referenced in this guide
- `runs/detect/.../weights/best.pt` (your trained weights in this repo)
- `requirements.txt` (created alongside this doc)
- Django app: `inference/` (create in your project)

## Helpful PowerShell snippets
```powershell
# create venv, activate, install deps
python -m venv .venv_inference
.\.venv_inference\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# run server
python manage.py migrate; python manage.py runserver
```

## Completion summary
This guide gives a practical step-by-step path to integrate your YOLOv8 model into a Django backend, with recommendations for synchronous and asynchronous inference, venv setup, and deployment notes. Follow it incrementally: get the synchronous image endpoint working first, then add video/Celery features.

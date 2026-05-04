# 🎥 The Witness — Intelligent video surveillance

> **AI-assisted monitoring** for live and uploaded video: detect violence, weapons, and theft-related activity; log incidents; alert security operators on the **web dashboard** and **mobile receiver** (push notifications).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🔗 **Repository:** [github.com/KativuCraig/The-Witness-Intelligent-video-surveillance-system](https://github.com/KativuCraig/The-Witness-Intelligent-video-surveillance-system)

---

## 📁 Repository layout

This project is split into two apps:

| Folder        | Stack        | Description                                      |
| ------------- | ------------ | ------------------------------------------------ |
| 📂 `backend/` | Django + DRF | API, detection pipeline hooks, auth, media, FCM  |
| 📂 `frontend/` | Angular      | Admin & security operator dashboard              |

> 💡 **Mapping from this workspace:** your Django project may live in a folder called `gods_eye` inside `backend`. For GitHub, put **everything that sits next to `manage.py`** into the repo’s **`backend/`** folder, and put your Angular app (where `angular.json` lives) into **`frontend/`**.  
> Example: `YourRepo/backend/manage.py` ✅ · `YourRepo/frontend/angular.json` ✅

> 🔗 **Remote:** push to [github.com/KativuCraig/The-Witness-Intelligent-video-surveillance-system](https://github.com/KativuCraig/The-Witness-Intelligent-video-surveillance-system).

---

## ✨ Features

- 🔍 **Detection pipeline** — Violence, weapon, and robbery/theft-style alerts from video (live stream or upload).
- 📋 **Incidents & evidence** — Timestamped incidents with frame evidence and confidence scores.
- 🔔 **Alerts** — In-app lists + Firebase Cloud Messaging for mobile security users.
- ✅ **Operator workflow** — Confirm / dismiss incidents (acknowledged / resolved) from web or companion app.
- 👥 **Roles** — `ADMIN`, `SECURITY`, `VIEWER` with route guards on the frontend and permissions on the API.

---

## 🛠️ Tech stack

| Layer    | Technologies                                      |
| -------- | ------------------------------------------------- |
| Backend  | Python, Django, Django REST Framework, OpenCV, Ultralytics (YOLO), Firebase Admin (optional) |
| Frontend | Angular, TypeScript, RxJS                         |
| Mobile   | Ionic / Angular (receiver app in sibling folder) |

---

## 📋 Prerequisites

- 🐍 **Python 3.10+** (recommended)
- 📗 **Node.js 20+** and **npm** (match `packageManager` in `frontend/package.json` if possible)
- 🎮 **Optional:** CUDA-capable GPU + matching **PyTorch** wheels for faster inference
- 🔥 **Optional:** Firebase **service account JSON** for push notifications

---

## 🚀 Backend setup (`backend/`)

From the repo root (adjust if your Django folder name differs):

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

1. **Environment** — Copy `.env.example` to `.env` if you add one, or set variables as documented in `gods_eye/settings.py` (e.g. `FCM_CREDENTIALS_PATH`, `CORS_ALLOWED_ORIGINS`).
2. **Database** — Default is SQLite (`db.sqlite3`). Run migrations:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

3. **ML weights** — Place YOLO checkpoints under `models/v2/` as expected by settings (weapon / violence / robbery classifiers). Large `.pt` files are **gitignored**; ship them via secure storage or your own release bundle.
4. **Run server**

   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

API base URL for the frontend defaults to `http://127.0.0.1:8000/api` — adjust `frontend` config if needed.

---

## 🌐 Frontend setup (`frontend/`)

```bash
cd frontend
npm install
npm start
# open http://localhost:4200
```

- Edit **`src/app/core/config/api.config.ts`** if your API is not on `http://127.0.0.1:8000`.
- Ensure Django **`CORS`** allows your Angular origin (e.g. `http://localhost:4200`).

---

## 📱 Mobile receiver (optional)

A companion **Ionic** app can register device tokens and receive **FCM** alerts. Build/run from your mobile project folder; point it at the same API URL.

---

## 🔐 Security notes (important)

- **Never commit** `.env`, database files, `media/` uploads, or Firebase JSON keys.
- **Production:** use a real DB, HTTPS, strong secrets, and restrict `ALLOWED_HOSTS` / CORS.
- **Authorization:** real enforcement is on the **API**; the Angular app only hides UI by role.

---

## 📜 License

This project is licensed under the **MIT License** — see the [`LICENSE`](LICENSE) file in the GitHub repository.

---

## 🙏 Acknowledgements

Built for coursework / demonstration of **intelligent video surveillance** workflows: detection, alerting, and human-in-the-loop review.

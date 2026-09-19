# Run and host Ramsey

## Local development

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
.venv\Scripts\python.exe -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Configure Firebase for sign-in, Browserbase for recipe acquisition, and Backboard/voice provider access for AI features. Use a random `SESSION_SECRET`. Keep `.env` and service-account credentials out of Git. The homepage is `/`, desktop companion `/app/`, and health endpoint `/health`.

For LAN use, enter the desktop's reachable address in Quest, then the pairing code from the signed-in desktop session. `localhost` on Quest points to the headset, not the desktop. Release builds require HTTPS.

## Container

```sh
docker build -t ramsey .
docker run --rm -p 8000:8000 --env-file .env ramsey
```

The root Dockerfile runs one worker. Active cooking sessions, pairing grants and kitchen labels are held in process memory; restarting loses them. Persistent local memory/cache files need a mounted `backend/data` directory. Mount Firebase service credentials separately when required.

Deploy behind HTTPS for remote access. No cloud host or tunnel has been provisioned by these instructions. The desktop must remain reachable if it hosts the backend; wireless Quest use is not offline AI.

## Verification

`python -m pytest backend/tests -q` runs fake-provider tests. A health response only proves the HTTP service is running. Rehearse sign-in, recipe search, pairing, voice and camera separately with their actual services. See [build plan](../docs/build-plan.md) and [judge guide](../docs/judging.md).

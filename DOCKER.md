# Running Accelnomics DocuMind AI on a company server

For the person who runs the server (IT). Staff only open the address in a browser or with the desktop icon.

## What you need on the server
- Docker with Docker Compose.
- Internet **once**, to download the app's base images and the two models (about 5 to 6 GB). After that it works offline.
- A GPU is optional but makes answers much faster (NVIDIA Container Toolkit needed).

## First start
1. Copy the project folder to the server (without `data`, `.venv`, `node_modules`, or any password file).
2. In the project folder:
   ```
   copy .env.example .env        (Linux/Mac: cp .env.example .env)
   docker compose up -d --build
   ```
   With an NVIDIA GPU use instead:
   ```
   docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
   ```
3. Wait for the models to download. Watch with: `docker compose logs -f models`  (it ends when both are installed).
4. Create the first admin (the password is asked, not shown):
   ```
   docker compose exec app python create_user.py admin1 --role admin
   ```
5. Create staff, one command each:
   ```
   docker compose exec app python create_user.py anu --role staff --dept HR
   ```
6. Open `http://localhost:8000` on the server and sign in as the admin. Upload documents on the Documents page.

## Letting employees in
- In `.env` set `BIND=0.0.0.0`, then `docker compose up -d`.
- Employees open `http://SERVER-NAME:8000`. **Plain HTTP is not safe for real use.** Use HTTPS:
  ```
  docker compose --profile https up -d
  ```
  Set `DOMAIN` in `.env` to the server's name. The included certificate is self-made, so browsers warn until you replace it with the company certificate (see `Caddyfile`). When you use HTTPS keep `BIND=127.0.0.1` so people can only reach the app through Caddy.

## Daily life
| Task | Command |
| --- | --- |
| Is it running? | `docker compose ps` |
| Look at logs | `docker compose logs -f app` |
| Stop | `docker compose down` (data is kept) |
| Update after a code change | `docker compose up -d --build` |
| Forgotten password | `docker compose exec app python create_user.py USERNAME --role staff --dept HR` |

It restarts by itself after a reboot.

## Backups
Everything that matters is in the Docker volume `documind_data` (database, vectors, uploaded files). Copy it regularly to another machine, and test a restore:
```
docker run --rm -v documind_data:/data -v "$PWD":/backup alpine tar czf /backup/documind-backup.tgz -C /data .
```
(The volume name may have the project folder name in front of it: check with `docker volume ls`.)

## Honest limits
Prototype: not audited or certified. One shared SQLite file, so it suits tens of users, not thousands. No single sign-on yet. Measure speed with your real number of users before rollout.

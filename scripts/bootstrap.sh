#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${MOVU_REPO_URL:-https://github.com/wangkeyu-u/Movu.git}"
BRANCH="${MOVU_BRANCH:-main}"

if [ -z "${MOVU_DIR:-}" ] && [ -f "package.json" ] && [ -f "scripts/dev.mjs" ]; then
  TARGET_DIR="."
else
  TARGET_DIR="${MOVU_DIR:-Movu}"
fi

need_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    echo "Install it, then run this bootstrap command again." >&2
    exit 1
  fi
}

need_command git
need_command docker
need_command curl

ensure_docker_available() {
  if docker info >/dev/null 2>&1; then
    return
  fi

  local docker_context=""
  docker_context="$(docker context show 2>/dev/null || true)"

  if [ "$docker_context" = "colima" ] && command -v colima >/dev/null 2>&1; then
    echo "Docker is unavailable and the active context is Colima. Starting Colima..."
    colima start
    docker info >/dev/null
    return
  fi

  echo "Docker is not running." >&2
  echo "Start Docker Desktop, OrbStack, or Colima, then run this bootstrap command again." >&2
  if [ -n "$docker_context" ]; then
    echo "Current Docker context: $docker_context" >&2
  fi
  exit 1
}

wait_for_backend() {
  local api_origin="${MOVU_API_ORIGIN:-http://127.0.0.1:8000}"
  local deadline=$((SECONDS + 120))

  until curl -fsS "$api_origin/health" >/dev/null 2>&1; do
    if [ "$SECONDS" -ge "$deadline" ]; then
      echo "Backend did not become healthy at $api_origin/health" >&2
      exit 1
    fi
    sleep 1
  done
}

echo "MovU bootstrap"
echo "Repository: $REPO_URL"
echo "Directory:  $TARGET_DIR"
echo ""

if [ -d "$TARGET_DIR/.git" ]; then
  echo "Existing MovU checkout found. Updating..."
  git -C "$TARGET_DIR" fetch origin "$BRANCH"
  git -C "$TARGET_DIR" checkout "$BRANCH"
  git -C "$TARGET_DIR" pull --ff-only origin "$BRANCH"
elif [ -e "$TARGET_DIR" ]; then
  echo "Target path exists but is not a git repository: $TARGET_DIR" >&2
  echo "Move it away or set MOVU_DIR to another path." >&2
  exit 1
else
  echo "Cloning MovU..."
  git clone --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR"
fi

cd "$TARGET_DIR"

if [ "${MOVU_INSTALL_NODE_DEPS:-0}" = "1" ]; then
  need_command node
  need_command npm
  echo ""
  echo "Installing local Node dependencies..."
  npm run setup
fi

if [ "${MOVU_SKIP_START:-0}" = "1" ]; then
  echo ""
  echo "Bootstrap completed. Start later with:"
  echo "cd $TARGET_DIR && bash scripts/bootstrap.sh"
  exit 0
fi

echo ""
echo "Starting MovU..."
ensure_docker_available
docker compose up --build -d
wait_for_backend

echo "Seeding local development data..."
docker compose exec -T backend python -m app.db.seed

docker compose ps

echo ""
echo "MovU is running:"
echo "- User app:        http://localhost:5174"
echo "- Admin dashboard: http://localhost:5173"
echo "- Backend API:     http://localhost:8000"
echo ""
echo "Sample login:"
echo "- Admin: admin@taylors.edu.my / Password123"
echo "- Rider: aina@sd.taylors.edu.my / Password123"
echo "- Driver: daniel@sd.taylors.edu.my / Password123"
echo ""
echo "Useful commands:"
echo "- cd $TARGET_DIR && docker compose logs -f"
echo "- cd $TARGET_DIR && docker compose down"

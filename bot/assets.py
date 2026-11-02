"""
Gets the textures the videos use straight from Mojang: downloads the official Minecraft client
jar for the latest release (once - it's cached) and pulls out the mob and block textures.
"""
import io
import json
import os
import urllib.request
import zipfile

from PIL import Image

CACHE = os.environ.get("TEXTURE_CACHE", os.path.join(os.path.dirname(__file__), "..", ".texture-cache"))
MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

BLOCKS = [
    "block/grass_block_top.png", "block/dirt.png", "block/stone_bricks.png", "block/sand.png",
    "block/netherrack.png", "block/soul_sand.png", "block/blackstone.png", "block/nether_bricks.png",
    "block/obsidian.png", "block/oak_planks.png", "block/end_stone.png", "block/deepslate_tiles.png",
]


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "mob-shorts-bot"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def latest_release() -> str:
    return json.loads(_get(MANIFEST))["latest"]["release"]


def _client_jar(version: str) -> str:
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"client-{version}.jar")
    if os.path.exists(path):
        return path
    manifest = json.loads(_get(MANIFEST))
    entry = next(v for v in manifest["versions"] if v["id"] == version)
    meta = json.loads(_get(entry["url"]))
    data = _get(meta["downloads"]["client"]["url"])
    with open(path, "wb") as f:
        f.write(data)
    return path


class Textures:
    """Lookup of textures by their path under assets/minecraft/textures/."""

    def __init__(self, files: dict):
        self.files = files                      # relative path -> bytes
        self._by_name = {}
        for p in files:
            self._by_name.setdefault(os.path.basename(p), []).append(p)

    def get(self, rel: str):
        """Exact path first; if Mojang moved the file, find it by name in a similar folder."""
        data = self.files.get(rel)
        if data is None:
            name = os.path.basename(rel)
            folder = rel.split("/")[0]
            options = [p for p in self._by_name.get(name, []) if p.startswith(folder + "/")]
            if not options:
                return None
            data = self.files[sorted(options, key=len)[0]]
        return Image.open(io.BytesIO(data)).convert("RGBA")

    @classmethod
    def load(cls, version: str | None = None) -> "Textures":
        override = os.environ.get("TEXTURE_DIR")  # a folder of PNGs laid out like textures/
        if override:
            files = {}
            for root, _, names in os.walk(override):
                for n in names:
                    if n.endswith(".png"):
                        full = os.path.join(root, n)
                        rel = os.path.relpath(full, override).replace(os.sep, "/")
                        with open(full, "rb") as f:
                            files[rel] = f.read()
            return cls(files)

        version = version or latest_release()
        prefix = "assets/minecraft/textures/"
        files = {}
        with zipfile.ZipFile(_client_jar(version)) as jar:
            for n in jar.namelist():
                if n.startswith(prefix + "entity/") or n.startswith(prefix + "block/"):
                    if n.endswith(".png"):
                        files[n[len(prefix):]] = jar.read(n)
        return cls(files)

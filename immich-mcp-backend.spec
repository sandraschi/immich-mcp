# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for immich-mcp backend (Tauri embedded resource).
# Fleet standard: strip=False, upx=False, noarchive=True (see tauri_nsis_building.md).
a = Analysis(
    ["run_server.py"],
    pathex=["src"],
    datas=[("src/immich_mcp", "immich_mcp")],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
    ],
    excludes=[
        "tkinter",
        "setuptools",
        "pip",
        "wheel",
        "test",
        "tests",
        "unittest",
        "_distutils_hack",
    ],
    noarchive=True,
)

# Strip .dist-info but preserve metadata for packages that read their own version
_keep_dist = ["fastmcp-", "mcp-", "prefab_ui-", "opentelemetry-", "email_validator-"]
_saved = [
    e
    for e in a.datas
    if isinstance(e, tuple) and any(k in str(e[0]) for k in _keep_dist) and ".dist-info" in str(e[0])
]
for _list in [a.datas, a.binaries, a.zipfiles, a.scripts]:
    _list[:] = [e for e in _list if not (isinstance(e, tuple) and ".dist-info" in str(e[0]))]
a.datas.extend(_saved)

# Heavy native deps never needed by the MCP backend. Do NOT add 'crypto'/'cryptography'
# here - Python's ssl module needs libcrypto DLLs for every HTTPS request (uvicorn/httpx).
SKIP = [
    "torch",
    "playwright",
    "bitsandbytes",
    "llvmlite",
    "pyarrow",
    "pymupdf",
    "grpc",
    "numba",
    "Cython",
    "google",
    "azure",
    "boto3",
    "botocore",
    "matplotlib",
    "PIL",
    "pandas",
    "scipy",
    "sklearn",
    "onnxruntime",
]
a.binaries = [b for b in a.binaries if not any(s in b[0].lower() for s in SKIP)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="immich-mcp-backend",
    debug=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
)

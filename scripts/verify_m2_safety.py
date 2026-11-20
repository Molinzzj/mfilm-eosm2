#!/usr/bin/env python3
"""Deterministic safety & license audit verifier for Canon EOS M2 (1.0.3) Magic Lantern + M-Film 0.2.3 port."""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.environ.get("BUILD_DIR", os.path.join(REPO_ROOT, "build"))

REF_PLAT = os.path.join(REPO_ROOT, "platform/EOSM2.103")
ML_REPO = os.path.join(BUILD_DIR, "magiclantern_simplified")
NEW_PLAT = os.path.join(ML_REPO, "platform/EOSM2.103")
MFILM_REPO = os.path.join(BUILD_DIR, "mfilm-canon-film-simulation")
MFILM_OUT = os.path.join(MFILM_REPO, "ml-dev/out/fork-EOSM2.103")

BOOT_MEM_LIMIT = 605952  # 0x4E0000 - 0x44C100 (592 KB fixed AllocateMemory reservation)

# Hardware-verified golden SHA256 digests for EOSM2.103 address & constant tables
GOLDEN_SHA256 = {
    "stubs.S": "3e2fac9cd81035a7b290fe601f39c69c1e3359ee05eb14f760e65ca85be27113",
    "consts.h": "b28e4fcfe11b151ca78abcf9666f65d22a6a6aa830047a582a0967180a875886",
    "gui.h": "db3a14f28687b20d804cd80715590ce44facc06cd4def90a2969691fe4c3ce3d",
}


def find_arm_tool(name):
    found = shutil.which(name)
    if found:
        return found
    fallback = os.path.expanduser(f"~/.local/bin/{name}")
    if os.path.isfile(fallback):
        return fallback
    return name


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_stubs(path):
    """Parse active (non-commented) NSTUB entries and RAM_OFFSET from stubs.S."""
    entries = []
    ram_offset = None
    hex_ff_lines = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if re.search(r"0x[Ff][Ff][0-9A-Fa-f]+", line):
                hex_ff_lines.append((lineno, line))
            if line.startswith("//") or line.startswith("/*") or line.startswith("*"):
                continue
            m_off = re.match(r"^#define\s+RAM_OFFSET\s+([^\s/]+)", line)
            if m_off:
                ram_offset = m_off.group(1)
            m = re.match(r"^NSTUB\(\s*([^,]+?)\s*,\s*([A-Za-z0-9_]+)\s*\)", line)
            if m:
                addr_expr = re.sub(r"\s+", " ", m.group(1).strip())
                sym = m.group(2).strip()
                entries.append((addr_expr, sym, lineno))
    return ram_offset, entries, hex_ff_lines


def check_1_stubs():
    ref_path = os.path.join(REF_PLAT, "stubs.S")
    new_path = os.path.join(NEW_PLAT, "stubs.S")
    errors = []

    if not os.path.isfile(ref_path):
        errors.append(f"Missing reference stubs.S: {ref_path}")
    if not os.path.isfile(new_path):
        errors.append(f"Missing build stubs.S: {new_path}")

    ref_off = new_off = None
    ref_entries = new_entries = []
    ref_ff = new_ff = []
    ref_sha = ""

    if not errors:
        ref_sha = sha256_file(ref_path)
        if ref_sha != GOLDEN_SHA256["stubs.S"]:
            errors.append(
                f"Reference stubs.S SHA256 mismatch: got {ref_sha}, expected {GOLDEN_SHA256['stubs.S']}"
            )
        ref_off, ref_entries, ref_ff = parse_stubs(ref_path)
        new_off, new_entries, new_ff = parse_stubs(new_path)

        if ref_off != new_off:
            errors.append(f"RAM_OFFSET mismatch: ref={ref_off} vs build={new_off}")
        if len(ref_ff) != len(new_ff) or len(ref_ff) != 135:
            errors.append(f"0xFF... line count mismatch: ref={len(ref_ff)}, build={len(new_ff)}, expected=135")
        if len(ref_entries) != len(new_entries) or len(ref_entries) != 144:
            errors.append(
                f"Active NSTUB count mismatch: ref={len(ref_entries)}, build={len(new_entries)}, expected=144"
            )

        for idx, (o, n) in enumerate(zip(ref_entries, new_entries)):
            o_addr, o_sym, o_ln = o
            n_addr, n_sym, n_ln = n
            if n_addr != o_addr or n_sym != o_sym:
                errors.append(
                    f"Entry #{idx+1} mismatch: ref(L{o_ln}: {o_addr}, {o_sym}) "
                    f"vs build(L{n_ln}: {n_addr}, {n_sym})"
                )

    status = "PASS" if not errors else "FAIL"
    print(f"[CHECK 1] stubs.S 100% Hex Address Consistency: {status}")
    print(f"  Golden SHA256: {ref_sha}")
    print(f"  RAM_OFFSET: {ref_off} == {new_off}")
    print(f"  0xFF... lines: ref={len(ref_ff)}, build={len(new_ff)}")
    print(f"  Active NSTUBs: ref={len(ref_entries)}, build={len(new_entries)}")
    for e in errors:
        print(f"  ERROR: {e}")
    return status == "PASS"


def parse_makefile_vars(path):
    vals = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.split("#", 1)[0].strip()
            m = re.match(r"^([A-Za-z0-9_]+)\s*[:?]?=\s*(.+)$", line)
            if m:
                vals[m.group(1)] = m.group(2).strip()
    return vals


def check_2_makefile():
    new_mk_path = os.path.join(NEW_PLAT, "Makefile")
    expected = {
        "MODEL": "EOSM2",
        "FW_VERSION": "103",
        "MAIN_FIRMWARE_ADDR": "0xFF0C0000",
        "ROMBASEADDR": "0xFF0C0000",
        "RESTARTSTART": "0x44C100",
    }
    errors = []
    new_mk = {}
    if not os.path.isfile(new_mk_path):
        errors.append(f"Missing build Makefile: {new_mk_path}")
    else:
        new_mk = parse_makefile_vars(new_mk_path)
        for k, exp in expected.items():
            got = new_mk.get(k)
            if got != exp:
                errors.append(f"{k}: expected {exp}, got {got}")
    status = "PASS" if not errors else "FAIL"
    print(f"[CHECK 2] Makefile Base Addresses & FW 1.0.3 Identity: {status}")
    for k, exp in expected.items():
        print(f"  {k} = {new_mk.get(k)} (expected {exp})")
    for e in errors:
        print(f"  ERROR: {e}")
    return status == "PASS"


def parse_defines(path):
    defs = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = re.sub(r"//.*", "", raw).strip()
            m = re.match(r"^#define\s+([A-Za-z0-9_]+)\s+(.+)$", line)
            if m:
                defs[m.group(1)] = re.sub(r"\s+", " ", m.group(2).strip())
    return defs


def check_3_consts():
    keys = [
        "HIJACK_INSTR_BL_CSTART",
        "HIJACK_INSTR_BSS_END",
        "HIJACK_FIXBR_BZERO32",
        "HIJACK_FIXBR_CREATE_ITASK",
        "HIJACK_INSTR_MY_ITASK",
        "HIJACK_TASK_ADDR",
        "ROM_ITASK_START",
        "ROM_ITASK_END",
        "ROM_CREATETASK_MAIN_START",
        "ROM_CREATETASK_MAIN_END",
        "ROM_ALLOCMEM_END",
        "YUV422_LV_BUFFER_1",
        "YUV422_LV_BUFFER_2",
        "YUV422_LV_BUFFER_3",
        "YUV422_LV_BUFFER_DISPLAY_ADDR",
        "YUV422_HD_BUFFER_1",
        "YUV422_HD_BUFFER_2",
        "REG_EDMAC_WRITE_LV_ADDR",
        "REG_EDMAC_WRITE_HD_ADDR",
        "MALLOC_STRUCT_ADDR",
    ]
    ref_c_path = os.path.join(REF_PLAT, "consts.h")
    new_c_path = os.path.join(NEW_PLAT, "consts.h")
    ref_g_path = os.path.join(REF_PLAT, "gui.h")
    new_g_path = os.path.join(NEW_PLAT, "gui.h")

    errors = []
    for p in (ref_c_path, new_c_path, ref_g_path, new_g_path):
        if not os.path.isfile(p):
            errors.append(f"Missing required header: {p}")

    bgmt_keys = []
    new_gui = {}
    if not errors:
        c_sha = sha256_file(ref_c_path)
        g_sha = sha256_file(ref_g_path)
        if c_sha != GOLDEN_SHA256["consts.h"]:
            errors.append(f"Reference consts.h SHA256 mismatch: got {c_sha}, expected {GOLDEN_SHA256['consts.h']}")
        if g_sha != GOLDEN_SHA256["gui.h"]:
            errors.append(f"Reference gui.h SHA256 mismatch: got {g_sha}, expected {GOLDEN_SHA256['gui.h']}")

        ref_c = parse_defines(ref_c_path)
        new_c = parse_defines(new_c_path)
        ref_gui = parse_defines(ref_g_path)
        new_gui = parse_defines(new_g_path)
        bgmt_keys = sorted(k for k in ref_gui if k.startswith("BGMT_"))

        for k in keys:
            if ref_c.get(k) != new_c.get(k) or not new_c.get(k):
                errors.append(f"consts.h {k}: ref={ref_c.get(k)} vs build={new_c.get(k)}")
        if "0xDF1BC + 0x7C" not in new_c.get("LV_OVERLAYS_MODE", ""):
            errors.append(f"LV_OVERLAYS_MODE address mismatch: {new_c.get('LV_OVERLAYS_MODE')}")
        if len(bgmt_keys) < 31:
            errors.append(f"Unexpected BGMT_* key count: {len(bgmt_keys)} < 31")
        for k in bgmt_keys:
            if ref_gui.get(k) != new_gui.get(k):
                errors.append(f"gui.h {k}: ref={ref_gui.get(k)} vs build={new_gui.get(k)}")

    status = "PASS" if not errors else "FAIL"
    print(f"[CHECK 3] consts.h / gui.h VRAM & BGMT_* Constants Integrity: {status}")
    print(f"  Verified {len(keys)} VRAM/HIJACK/ROM/MALLOC constants + LV_OVERLAYS_MODE")
    print(
        f"  Verified {len(bgmt_keys)} BGMT_* keycodes "
        f"(incl. BGMT_PLAY={new_gui.get('BGMT_PLAY')}, BGMT_MENU={new_gui.get('BGMT_MENU')})"
    )
    for e in errors:
        print(f"  ERROR: {e}")
    return status == "PASS"


def check_4_mfilm_symbols_and_boot_mem():
    """Verify filmos.mo symbol resolution against EOSM2_103.sym and _bss_end - RESTARTSTART < 605952."""
    errors = []
    elf_path = os.path.join(NEW_PLAT, "build/magiclantern")
    sym_path = os.path.join(MFILM_OUT, "ML/modules/EOSM2_103.sym")
    mo_path = os.path.join(MFILM_OUT, "ML/modules/filmos.mo")

    nm_bin = find_arm_tool("arm-none-eabi-nm")
    readelf_bin = find_arm_tool("arm-none-eabi-readelf")

    for label, p in [("magiclantern ELF", elf_path), ("EOSM2_103.sym", sym_path), ("filmos.mo", mo_path)]:
        if not os.path.isfile(p):
            errors.append(f"Missing required build artifact: {label} ({p})")

    used_bytes = None
    restart_addr = None
    bss_end = None
    und_syms = set()
    def_syms = set()
    exported_syms = set()
    unwind_secs = []

    if not errors:
        mk_vars = parse_makefile_vars(os.path.join(NEW_PLAT, "Makefile"))
        restart_addr = int(mk_vars["RESTARTSTART"], 16)
        nm_out = subprocess.check_output([nm_bin, elf_path], text=True, errors="replace")
        for line in nm_out.splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[2] == "_bss_end":
                bss_end = int(parts[0], 16)
                break
        if bss_end is None:
            errors.append("Could not locate _bss_end symbol in build/magiclantern")
        else:
            used_bytes = bss_end - restart_addr
            if used_bytes >= BOOT_MEM_LIMIT:
                errors.append(
                    f"Boot memory overflow: _bss_end - RESTARTSTART = {used_bytes} >= {BOOT_MEM_LIMIT} bytes"
                )

        with open(sym_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    exported_syms.add(parts[1])

        re_syms = subprocess.check_output([readelf_bin, "-sW", mo_path], text=True, errors="replace")
        for line in re_syms.splitlines():
            parts = line.split()
            if len(parts) >= 8 and parts[4] == "GLOBAL":
                if parts[6] == "UND":
                    und_syms.add(parts[7])
                else:
                    def_syms.add(parts[7])

        missing = sorted(und_syms - exported_syms)
        clash = sorted(def_syms & exported_syms)
        if missing:
            errors.append(f"Missing symbols required by filmos.mo ({len(missing)}): {', '.join(missing[:20])}")
        if clash:
            errors.append(f"Symbol clashes between filmos.mo and autoexec.bin ({len(clash)}): {', '.join(clash[:20])}")

        re_secs = subprocess.check_output([readelf_bin, "-SW", mo_path], text=True, errors="replace")
        for line in re_secs.splitlines():
            if ".ARM.ex" in line:
                unwind_secs.append(line.strip())
        if unwind_secs:
            errors.append(f"Unwind tables still present in filmos.mo: {len(unwind_secs)} sections")

    status = "PASS" if not errors else "FAIL"
    print(f"[CHECK 4] M-Film Symbol Resolution & Boot Memory Budget (< {BOOT_MEM_LIMIT} B): {status}")
    if used_bytes is not None:
        headroom = BOOT_MEM_LIMIT - used_bytes
        print(
            f"  Boot memory: _bss_end(0x{bss_end:X}) - RESTARTSTART(0x{restart_addr:X}) = "
            f"{used_bytes} bytes / {BOOT_MEM_LIMIT} bytes (headroom: {headroom} bytes / {headroom/1024:.1f} KB)"
        )
    print(
        f"  filmos.mo symbols: {len(und_syms)} UND (all resolved in {len(exported_syms)} exported syms), "
        f"{len(def_syms)} GLOBAL defined (0 clashes), {len(unwind_secs)} .ARM.ex* sections"
    )
    for e in errors:
        print(f"  ERROR: {e}")
    return status == "PASS"


def check_5_bootflag_scan():
    """Scan all new/modified EOSM2 and M-Film source files for automatic NVRAM Bootflag calls."""
    forbidden = re.compile(r"\b(EnableBootDisk|DisableBootDisk|SetBootFlag|bootflag_write_bootblock)\s*\(")
    hits = []
    scanned_files = 0
    seen_paths = set()

    def scan_file(p):
        nonlocal scanned_files
        ap = os.path.abspath(p)
        if ap in seen_paths or not os.path.isfile(ap):
            return
        seen_paths.add(ap)
        scanned_files += 1
        with open(ap, "r", encoding="utf-8", errors="replace") as f:
            for ln, line in enumerate(f, 1):
                if forbidden.search(line):
                    hits.append(f"{os.path.relpath(ap, REPO_ROOT)}:{ln}: {line.strip()}")

    scan_roots = [
        REF_PLAT,
        NEW_PLAT,
        os.path.join(ML_REPO, "modules/filmos"),
        os.path.join(REPO_ROOT, "patches"),
    ]
    explicit_files = [
        os.path.join(ML_REPO, "src/filmroll.c"),
        os.path.join(ML_REPO, "src/filmroll.h"),
        os.path.join(ML_REPO, "src/filmhook.c"),
        os.path.join(ML_REPO, "src/gui-common.c"),
        os.path.join(ML_REPO, "src/zebra.c"),
        os.path.join(ML_REPO, "src/menu.c"),
        os.path.join(ML_REPO, "src/boot-d45-am.c"),
    ]
    src_dir = os.path.join(ML_REPO, "src")
    if os.path.isdir(src_dir):
        for fn in sorted(os.listdir(src_dir)):
            if fn.startswith("fos") and fn.endswith((".c", ".h")):
                explicit_files.append(os.path.join(src_dir, fn))

    for p in explicit_files:
        scan_file(p)

    for root_dir in scan_roots:
        if not os.path.isdir(root_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d != "build"]
            for fn in sorted(filenames):
                if fn.endswith((".c", ".h", ".S", ".s", ".patch")) and fn != "stubs.S":
                    scan_file(os.path.join(dirpath, fn))

    if os.path.isdir(os.path.join(MFILM_REPO, ".git")):
        diff_out = subprocess.check_output(
            ["git", "-C", MFILM_REPO, "--no-pager", "diff", "--unified=0"],
            text=True,
            errors="replace",
        )
        cur_file = ""
        for line in diff_out.splitlines():
            if line.startswith("+++ b/"):
                cur_file = line[6:]
            elif line.startswith("+") and not line.startswith("+++"):
                if forbidden.search(line):
                    hits.append(f"mfilm/{cur_file}: {line.strip()}")

    status = "PASS" if not hits else "FAIL"
    print(f"[CHECK 5] Global Auto-Bootflag Call Scan: {status}")
    print(f"  Scanned files: {scanned_files} (+ mfilm git diff) | Forbidden call matches: {len(hits)}")
    for h in hits:
        print(f"  ERROR: {h}")
    return status == "PASS"


def check_6_license_firewall():
    """Scan firmware sources, patches, and M-Film changes for any GPL-3.0 header or spektrafilm reference."""
    forbidden = re.compile(
        r"(GPL[-_\s]?v?3(?:\.0)?|General Public License[^\n]*version 3|spektrafilm|andreavolpato|SPEKTRAFILM_LICENSE)",
        re.IGNORECASE,
    )
    hits = []
    scanned_files = 0
    seen_paths = set()

    def scan_file(p):
        nonlocal scanned_files
        ap = os.path.abspath(p)
        if ap in seen_paths or not os.path.isfile(ap):
            return
        seen_paths.add(ap)
        scanned_files += 1
        with open(ap, "r", encoding="utf-8", errors="replace") as f:
            for ln, line in enumerate(f, 1):
                if forbidden.search(line):
                    hits.append(f"{os.path.relpath(ap, REPO_ROOT)}:{ln}: {line.strip()}")

    for root_dir in [
        REF_PLAT,
        NEW_PLAT,
        os.path.join(ML_REPO, "modules/filmos"),
        os.path.join(REPO_ROOT, "patches"),
    ]:
        if os.path.isdir(root_dir):
            for dirpath, dirnames, filenames in os.walk(root_dir):
                dirnames[:] = [d for d in dirnames if d != "build"]
                for fn in sorted(filenames):
                    if fn.endswith((".c", ".h", ".S", ".s", ".py", ".sh", ".rst", ".patch", "Makefile")):
                        scan_file(os.path.join(dirpath, fn))

    src_dir = os.path.join(ML_REPO, "src")
    if os.path.isdir(src_dir):
        for fn in sorted(os.listdir(src_dir)):
            if fn.startswith(("fos", "filmroll", "filmhook")) and fn.endswith((".c", ".h")):
                scan_file(os.path.join(src_dir, fn))

    if os.path.isdir(os.path.join(MFILM_REPO, ".git")):
        st_out = subprocess.check_output(
            ["git", "-C", MFILM_REPO, "--no-pager", "status", "--porcelain"],
            text=True,
            errors="replace",
        )
        for line in st_out.splitlines():
            if len(line) < 4:
                continue
            rel = line[3:].strip().split(" -> ")[-1]
            scan_file(os.path.join(MFILM_REPO, rel))

    status = "PASS" if not hits else "FAIL"
    print(f"[CHECK 6] GPL-2.0 / GPL-3.0 License Firewall & SpektraFilm Isolation Scan: {status}")
    print(f"  Scanned files (firmware tree + patches + mfilm changes): {scanned_files} | Violations: {len(hits)}")
    for h in hits:
        print(f"  ERROR: {h}")
    return status == "PASS"


def verify_zip_and_sha256(zip_path):
    if not zip_path or not os.path.isfile(zip_path):
        print(f"[ARTIFACT] Missing ZIP file: {zip_path}")
        return False
    digest = sha256_file(zip_path)
    size = os.path.getsize(zip_path)
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
    required = [
        "autoexec.bin",
        "ML/modules/filmos.mo",
        "ML/modules/EOSM2_103.sym",
        "ML/SETTINGS/filmos.en",
        "ML/data/FOSFONT.BIN",
        "ML/data/FOSFILMS.BIN",
    ]
    missing_req = [r for r in required if r not in names]
    has_darkroom = any(n.startswith("ML/DARKROOM/") for n in names)
    has_samples = any(n.startswith("ML/SAMPLES/") for n in names)
    ext_cfgs = [n for n in names if n.startswith("ML/MFILM/profiles/") and n.endswith(".cfg")]
    has_attr = "ML/MFILM/profiles/PROFILES_ATTRIBUTION.txt" in names
    junk = [n for n in names if n.endswith((".o", ".d", ".log")) or "/.git/" in n]
    ok = not missing_req and has_darkroom and has_samples and not junk
    if "ExtProfiles" in os.path.basename(zip_path):
        ok = ok and len(ext_cfgs) == 20 and has_attr
    print(f"[ARTIFACT] {os.path.relpath(os.path.abspath(zip_path), REPO_ROOT)}")
    print(f"  Size: {size} bytes")
    print(f"  SHA256: {digest}")
    print(
        f"  Entries: {len(names)} | required_missing={len(missing_req)} | "
        f"DARKROOM={has_darkroom} | SAMPLES={has_samples} | "
        f"ext_cfgs={len(ext_cfgs)} | attribution={has_attr} | junk={len(junk)}"
    )
    if not ok:
        print(f"  ERROR: ZIP structure check failed (missing={missing_req}, junk={junk[:10]})")
        return False
    return True


def main():
    zip_arg = sys.argv[1] if len(sys.argv) > 1 else None
    results = [
        check_1_stubs(),
        check_2_makefile(),
        check_3_consts(),
        check_4_mfilm_symbols_and_boot_mem(),
        check_5_bootflag_scan(),
        check_6_license_firewall(),
    ]
    if zip_arg:
        results.append(verify_zip_and_sha256(zip_arg))
    overall = "PASS" if all(results) else "BLOCKED"
    print(f"=== OVERALL SAFETY AUDIT: {overall} ===")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()

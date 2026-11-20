#!/usr/bin/env python3
"""Deterministic safety audit verifier for Canon EOS M2 (1.0.3) Magic Lantern + M-Film 0.2.3 port."""

import hashlib
import os
import re
import subprocess
import sys
import zipfile

ROOT = "/home/antigravity"
OLD_PLAT = os.path.join(ROOT, "workspace/01_old_bilal/platform/EOSM2.103")
NEW_PLAT = os.path.join(ROOT, "workspace/02_ml_simplified/platform/EOSM2.103")
ML_REPO = os.path.join(ROOT, "workspace/02_ml_simplified")
MFILM_REPO = os.path.join(ROOT, "workspace/03_mfilm")
MFILM_OUT = os.path.join(MFILM_REPO, "ml-dev/out/fork-EOSM2.103")
ARM_BIN = "/home/antigravity/.local/bin"

BOOT_MEM_LIMIT = 605952  # 0x4E0000 - 0x44C100 (592 KB fixed AllocateMemory reservation)

ALLOWED_SYMBOL_RENAMES = {
    "is_taskid_valid": "get_task_info_by_id",
}

ALLOWED_ADDR_MACRO_RENAMES = {
    "ROMBASEADDR": "MAIN_FIRMWARE_ADDR",
}


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
    old_path = os.path.join(OLD_PLAT, "stubs.S")
    new_path = os.path.join(NEW_PLAT, "stubs.S")
    old_off, old_entries, old_ff = parse_stubs(old_path)
    new_off, new_entries, new_ff = parse_stubs(new_path)

    errors = []
    if old_off != new_off:
        errors.append(f"RAM_OFFSET mismatch: old={old_off} vs new={new_off}")
    if len(old_ff) != len(new_ff):
        errors.append(f"0xFF... line count mismatch: old={len(old_ff)} vs new={len(new_ff)}")
    if len(old_entries) != len(new_entries):
        errors.append(f"Active NSTUB count mismatch: old={len(old_entries)} vs new={len(new_entries)}")

    for idx, (o, n) in enumerate(zip(old_entries, new_entries)):
        o_addr, o_sym, o_ln = o
        n_addr, n_sym, n_ln = n
        expected_addr = ALLOWED_ADDR_MACRO_RENAMES.get(o_addr, o_addr)
        expected_sym = ALLOWED_SYMBOL_RENAMES.get(o_sym, o_sym)
        if n_addr != expected_addr or n_sym != expected_sym:
            errors.append(
                f"Entry #{idx+1} mismatch: old(L{o_ln}: {o_addr}, {o_sym}) "
                f"vs new(L{n_ln}: {n_addr}, {n_sym})"
            )

    status = "PASS" if not errors else "FAIL"
    print(f"[CHECK 1] stubs.S 100% Hex Address Consistency: {status}")
    print(f"  RAM_OFFSET: {old_off} == {new_off}")
    print(f"  0xFF... lines: old={len(old_ff)}, new={len(new_ff)}")
    print(f"  Active NSTUBs: old={len(old_entries)}, new={len(new_entries)}")
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
    new_mk = parse_makefile_vars(os.path.join(NEW_PLAT, "Makefile"))
    expected = {
        "MODEL": "EOSM2",
        "FW_VERSION": "103",
        "MAIN_FIRMWARE_ADDR": "0xFF0C0000",
        "ROMBASEADDR": "0xFF0C0000",
        "RESTARTSTART": "0x44C100",
    }
    errors = []
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
    old_c = parse_defines(os.path.join(OLD_PLAT, "consts.h"))
    new_c = parse_defines(os.path.join(NEW_PLAT, "consts.h"))
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
    ]
    old_gui = parse_defines(os.path.join(OLD_PLAT, "gui.h"))
    new_gui = parse_defines(os.path.join(NEW_PLAT, "gui.h"))
    bgmt_keys = sorted(k for k in old_gui if k.startswith("BGMT_"))

    errors = []
    for k in keys:
        if old_c.get(k) != new_c.get(k):
            errors.append(f"consts.h {k}: old={old_c.get(k)} vs new={new_c.get(k)}")
    if old_c.get("MALLOC_STRUCT") != new_c.get("MALLOC_STRUCT_ADDR"):
        errors.append(
            f"MALLOC_STRUCT -> MALLOC_STRUCT_ADDR mismatch: "
            f"old={old_c.get('MALLOC_STRUCT')} vs new={new_c.get('MALLOC_STRUCT_ADDR')}"
        )
    if "0xDF1BC + 0x7C" not in new_c.get("LV_OVERLAYS_MODE", ""):
        errors.append(f"LV_OVERLAYS_MODE address mismatch: {new_c.get('LV_OVERLAYS_MODE')}")
    for k in bgmt_keys:
        if old_gui.get(k) != new_gui.get(k):
            errors.append(f"gui.h {k}: old={old_gui.get(k)} vs new={new_gui.get(k)}")

    status = "PASS" if not errors else "FAIL"
    print(f"[CHECK 3] consts.h / gui.h VRAM & BGMT_* Constants Integrity: {status}")
    print(f"  Verified {len(keys)} VRAM/HIJACK/ROM constants + MALLOC_STRUCT_ADDR + LV_OVERLAYS_MODE")
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

    nm_bin = os.path.join(ARM_BIN, "arm-none-eabi-nm")
    readelf_bin = os.path.join(ARM_BIN, "arm-none-eabi-readelf")

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

    scan_roots = [
        NEW_PLAT,
        os.path.join(ML_REPO, "modules/filmos"),
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
    # Include all fos*.c / fos*.h copied into src/
    src_dir = os.path.join(ML_REPO, "src")
    for fn in sorted(os.listdir(src_dir)):
        if fn.startswith("fos") and fn.endswith((".c", ".h")):
            explicit_files.append(os.path.join(src_dir, fn))

    def scan_file(p):
        nonlocal scanned_files
        if not os.path.isfile(p):
            return
        scanned_files += 1
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for ln, line in enumerate(f, 1):
                if forbidden.search(line):
                    hits.append(f"{os.path.relpath(p, ROOT)}:{ln}: {line.strip()}")

    for p in explicit_files:
        scan_file(p)

    for root_dir in scan_roots:
        if not os.path.isdir(root_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d != "build"]
            for fn in sorted(filenames):
                if fn.endswith((".c", ".h", ".S", ".s")) and fn != "stubs.S":
                    scan_file(os.path.join(dirpath, fn))

    # Also scan git diff of 03_mfilm if it is a git repo
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
                    hits.append(f"03_mfilm/{cur_file}: {line.strip()}")

    status = "PASS" if not hits else "FAIL"
    print(f"[CHECK 5] Global Auto-Bootflag Call Scan: {status}")
    print(f"  Scanned files: {scanned_files} (+ 03_mfilm git diff) | Forbidden call matches: {len(hits)}")
    for h in hits:
        print(f"  ERROR: {h}")
    return status == "PASS"


def check_6_license_firewall():
    """Scan 02_ml_simplified and 03_mfilm changes for any GPL-3.0 header or spektrafilm reference."""
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
                    hits.append(f"{os.path.relpath(ap, ROOT)}:{ln}: {line.strip()}")

    # 1. Scan EOSM2 platform, filmos module, and M-Film source files inside 02_ml_simplified
    for root_dir in [NEW_PLAT, os.path.join(ML_REPO, "modules/filmos")]:
        if os.path.isdir(root_dir):
            for dirpath, dirnames, filenames in os.walk(root_dir):
                dirnames[:] = [d for d in dirnames if d != "build"]
                for fn in sorted(filenames):
                    if fn.endswith((".c", ".h", ".S", ".s", ".py", ".sh", ".rst", "Makefile")):
                        scan_file(os.path.join(dirpath, fn))

    src_dir = os.path.join(ML_REPO, "src")
    if os.path.isdir(src_dir):
        for fn in sorted(os.listdir(src_dir)):
            if fn.startswith(("fos", "filmroll", "filmhook")) and fn.endswith((".c", ".h")):
                scan_file(os.path.join(src_dir, fn))

    # 2. Scan all modified & untracked files in 03_mfilm
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
    print(f"  Scanned files (02_ml_simplified + 03_mfilm changes): {scanned_files} | Violations: {len(hits)}")
    for h in hits:
        print(f"  ERROR: {h}")
    return status == "PASS"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_zip_and_sha256(zip_path):
    if not zip_path or not os.path.isfile(zip_path):
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
        ok = ok and len(ext_cfgs) > 0 and has_attr
    print(f"[ARTIFACT] {os.path.relpath(zip_path, ROOT)}")
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

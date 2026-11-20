#!/usr/bin/env python3
"""Deterministic safety audit verifier for Canon EOS M2 (1.0.3) Magic Lantern + M-Film port.

Performs 5 mandatory static/binary safety gates before any real-camera SD card test:
  1. stubs.S hex address consistency (against reference stubs.S if provided)
  2. Makefile base addresses & Firmware 1.0.3 identity lock
  3. consts.h / gui.h VRAM, HIJACK, and BGMT_* keycode integrity
  4. M-Film filmos.mo symbol resolution, zero unwind tables, and boot memory budget (< 605952 B)
  5. Global automatic NVRAM Bootflag call scan (must be 0 matches)
  + Optional SD card ZIP structure & SHA256 verification
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BOOT_MEM_LIMIT = 605952  # 0x4E0000 - 0x44C100 (592 KB fixed AllocateMemory reservation)

ALLOWED_SYMBOL_RENAMES = {
    "is_taskid_valid": "get_task_info_by_id",
}

ALLOWED_ADDR_MACRO_RENAMES = {
    "ROMBASEADDR": "MAIN_FIRMWARE_ADDR",
}

EXPECTED_MAKEFILE = {
    "MODEL": "EOSM2",
    "FW_VERSION": "103",
    "MAIN_FIRMWARE_ADDR": "0xFF0C0000",
    "ROMBASEADDR": "0xFF0C0000",
    "RESTARTSTART": "0x44C100",
}

PROTECTED_CONST_KEYS = [
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


def check_1_stubs(new_plat, old_plat=None):
    new_path = os.path.join(new_plat, "stubs.S")
    new_off, new_entries, new_ff = parse_stubs(new_path)
    errors = []

    if new_off != "(0xFFD1F0E4-0x1900)":
        errors.append(f"Unexpected RAM_OFFSET: {new_off} (expected (0xFFD1F0E4-0x1900))")
    if len(new_ff) != 135:
        errors.append(f"Unexpected 0xFF... line count: {len(new_ff)} (expected 135)")
    if len(new_entries) != 144:
        errors.append(f"Unexpected active NSTUB count: {len(new_entries)} (expected 144)")

    if old_plat and os.path.isfile(os.path.join(old_plat, "stubs.S")):
        old_off, old_entries, old_ff = parse_stubs(os.path.join(old_plat, "stubs.S"))
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
                    f"Entry #{idx + 1} mismatch: old(L{o_ln}: {o_addr}, {o_sym}) "
                    f"vs new(L{n_ln}: {n_addr}, {n_sym})"
                )

    status = "PASS" if not errors else "FAIL"
    print(f"[CHECK 1] stubs.S Hex Address Consistency: {status}")
    print(f"  RAM_OFFSET: {new_off}")
    print(f"  0xFF... lines: {len(new_ff)} | Active NSTUBs: {len(new_entries)}")
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


def check_2_makefile(new_plat):
    new_mk = parse_makefile_vars(os.path.join(new_plat, "Makefile"))
    errors = []
    for k, exp in EXPECTED_MAKEFILE.items():
        got = new_mk.get(k)
        if got != exp:
            errors.append(f"{k}: expected {exp}, got {got}")
    status = "PASS" if not errors else "FAIL"
    print(f"[CHECK 2] Makefile Base Addresses & FW 1.0.3 Identity: {status}")
    for k, exp in EXPECTED_MAKEFILE.items():
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


def check_3_consts(new_plat, old_plat=None):
    new_c = parse_defines(os.path.join(new_plat, "consts.h"))
    new_gui = parse_defines(os.path.join(new_plat, "gui.h"))
    bgmt_keys = sorted(k for k in new_gui if k.startswith("BGMT_"))
    errors = []

    for k in PROTECTED_CONST_KEYS:
        if k not in new_c:
            errors.append(f"consts.h missing protected key: {k}")

    if "0xDF1BC + 0x7C" not in new_c.get("LV_OVERLAYS_MODE", ""):
        errors.append(f"LV_OVERLAYS_MODE address mismatch: {new_c.get('LV_OVERLAYS_MODE')}")
    if new_gui.get("BGMT_PLAY") != "0xb":
        errors.append(f"BGMT_PLAY unexpected value: {new_gui.get('BGMT_PLAY')}")
    if new_gui.get("BGMT_MENU") != "0x6":
        errors.append(f"BGMT_MENU unexpected value: {new_gui.get('BGMT_MENU')}")

    if old_plat and os.path.isfile(os.path.join(old_plat, "consts.h")):
        old_c = parse_defines(os.path.join(old_plat, "consts.h"))
        old_gui = parse_defines(os.path.join(old_plat, "gui.h"))
        for k in PROTECTED_CONST_KEYS:
            if old_c.get(k) != new_c.get(k):
                errors.append(f"consts.h {k}: old={old_c.get(k)} vs new={new_c.get(k)}")
        if old_c.get("MALLOC_STRUCT") != new_c.get("MALLOC_STRUCT_ADDR"):
            errors.append(
                f"MALLOC_STRUCT -> MALLOC_STRUCT_ADDR mismatch: "
                f"old={old_c.get('MALLOC_STRUCT')} vs new={new_c.get('MALLOC_STRUCT_ADDR')}"
            )
        for k in sorted(k for k in old_gui if k.startswith("BGMT_")):
            if old_gui.get(k) != new_gui.get(k):
                errors.append(f"gui.h {k}: old={old_gui.get(k)} vs new={new_gui.get(k)}")

    status = "PASS" if not errors else "FAIL"
    print(f"[CHECK 3] consts.h / gui.h VRAM & BGMT_* Constants Integrity: {status}")
    print(f"  Verified {len(PROTECTED_CONST_KEYS)} VRAM/HIJACK/ROM constants + MALLOC_STRUCT_ADDR + LV_OVERLAYS_MODE")
    print(
        f"  Verified {len(bgmt_keys)} BGMT_* keycodes "
        f"(incl. BGMT_PLAY={new_gui.get('BGMT_PLAY')}, BGMT_MENU={new_gui.get('BGMT_MENU')})"
    )
    for e in errors:
        print(f"  ERROR: {e}")
    return status == "PASS"


def check_4_mfilm_symbols_and_boot_mem(ml_plat_dir, mfilm_out_dir):
    """Verify filmos.mo symbol resolution against EOSM2_103.sym and _bss_end - RESTARTSTART < 605952."""
    elf_path = os.path.join(ml_plat_dir, "build/magiclantern")
    sym_path = os.path.join(mfilm_out_dir, "ML/modules/EOSM2_103.sym")
    mo_path = os.path.join(mfilm_out_dir, "ML/modules/filmos.mo")

    nm_bin = shutil.which("arm-none-eabi-nm")
    readelf_bin = shutil.which("arm-none-eabi-readelf")

    if not (os.path.isfile(elf_path) and os.path.isfile(sym_path) and os.path.isfile(mo_path)):
        print("[CHECK 4] M-Film Symbol Resolution & Boot Memory Budget: SKIP (build artifacts not present)")
        return True

    errors = []
    if not nm_bin or not readelf_bin:
        errors.append("arm-none-eabi-nm and arm-none-eabi-readelf must be in PATH to inspect ELF/module binaries")

    used_bytes = None
    restart_addr = None
    bss_end = None
    und_syms = set()
    def_syms = set()
    exported_syms = set()
    unwind_secs = []

    if not errors:
        mk_vars = parse_makefile_vars(os.path.join(ml_plat_dir, "Makefile"))
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
            f"{used_bytes} bytes / {BOOT_MEM_LIMIT} bytes (headroom: {headroom} bytes / {headroom / 1024:.1f} KB)"
        )
    print(
        f"  filmos.mo symbols: {len(und_syms)} UND (all resolved in {len(exported_syms)} exported syms), "
        f"{len(def_syms)} GLOBAL defined (0 clashes), {len(unwind_secs)} .ARM.ex* sections"
    )
    for e in errors:
        print(f"  ERROR: {e}")
    return status == "PASS"


def check_5_bootflag_scan(new_plat, ml_repo=None, patches_dir=None):
    """Scan EOSM2 platform files, patches, and optional ML tree for automatic NVRAM Bootflag calls."""
    forbidden = re.compile(r"\b(EnableBootDisk|DisableBootDisk|SetBootFlag|bootflag_write_bootblock)\s*\(")
    hits = []
    scanned_files = 0

    def scan_file(p):
        nonlocal scanned_files
        if not os.path.isfile(p):
            return
        scanned_files += 1
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for ln, line in enumerate(f, 1):
                if forbidden.search(line):
                    hits.append(f"{os.path.relpath(p, REPO_ROOT)}:{ln}: {line.strip()}")

    for dirpath, dirnames, filenames in os.walk(new_plat):
        dirnames[:] = [d for d in dirnames if d != "build"]
        for fn in sorted(filenames):
            if fn.endswith((".c", ".h", ".S", ".s")) and fn != "stubs.S":
                scan_file(os.path.join(dirpath, fn))

    if patches_dir and os.path.isdir(patches_dir):
        for fn in sorted(os.listdir(patches_dir)):
            if fn.endswith(".patch"):
                scan_file(os.path.join(patches_dir, fn))

    if ml_repo and os.path.isdir(ml_repo):
        src_dir = os.path.join(ml_repo, "src")
        for fn in ["filmroll.c", "filmroll.h", "filmhook.c", "gui-common.c", "zebra.c", "menu.c", "boot-d45-am.c"]:
            scan_file(os.path.join(src_dir, fn))
        if os.path.isdir(src_dir):
            for fn in sorted(os.listdir(src_dir)):
                if fn.startswith("fos") and fn.endswith((".c", ".h")):
                    scan_file(os.path.join(src_dir, fn))
        mod_dir = os.path.join(ml_repo, "modules/filmos")
        if os.path.isdir(mod_dir):
            for dirpath, dirnames, filenames in os.walk(mod_dir):
                dirnames[:] = [d for d in dirnames if d != "build"]
                for fn in sorted(filenames):
                    if fn.endswith((".c", ".h")):
                        scan_file(os.path.join(dirpath, fn))

    status = "PASS" if not hits else "FAIL"
    print(f"[CHECK 5] Global Auto-Bootflag Call Scan: {status}")
    print(f"  Scanned files: {scanned_files} | Forbidden call matches: {len(hits)}")
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
        print(f"[ARTIFACT] ERROR: ZIP file not found: {zip_path}")
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
    junk = [n for n in names if n.endswith((".o", ".d", ".log")) or "/.git/" in n]
    ok = not missing_req and has_darkroom and has_samples and not junk
    print(f"[ARTIFACT] {zip_path}")
    print(f"  Size: {size} bytes")
    print(f"  SHA256: {digest}")
    print(
        f"  Entries: {len(names)} | required_missing={len(missing_req)} | "
        f"DARKROOM={has_darkroom} | SAMPLES={has_samples} | junk={len(junk)}"
    )
    if not ok:
        print(f"  ERROR: ZIP structure check failed (missing={missing_req}, junk={junk[:10]})")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Canon EOS M2 (1.0.3) Magic Lantern + M-Film safety auditor")
    parser.add_argument("zip_file", nargs="?", help="Optional M-Film SD card ZIP archive to verify")
    parser.add_argument("--platform-dir", default=os.path.join(REPO_ROOT, "platform/EOSM2.103"),
                        help="Path to ported platform/EOSM2.103 directory")
    parser.add_argument("--ref-platform-dir", default=None,
                        help="Optional path to original EOSM2.103 reference directory for diff check")
    parser.add_argument("--ml-repo", default=os.path.join(REPO_ROOT, "build/magiclantern_simplified"),
                        help="Optional path to built magiclantern_simplified checkout")
    parser.add_argument("--mfilm-out", default=os.path.join(REPO_ROOT, "build/mfilm-canon-film-simulation/ml-dev/out/fork-EOSM2.103"),
                        help="Optional path to M-Film build output directory")
    args = parser.parse_args()

    ml_plat_dir = os.path.join(args.ml_repo, "platform/EOSM2.103")
    results = [
        check_1_stubs(args.platform_dir, args.ref_platform_dir),
        check_2_makefile(args.platform_dir),
        check_3_consts(args.platform_dir, args.ref_platform_dir),
        check_4_mfilm_symbols_and_boot_mem(ml_plat_dir, args.mfilm_out),
        check_5_bootflag_scan(args.platform_dir, args.ml_repo, os.path.join(REPO_ROOT, "patches")),
    ]
    if args.zip_file:
        results.append(verify_zip_and_sha256(args.zip_file))

    overall = "PASS" if all(results) else "BLOCKED"
    print(f"=== OVERALL SAFETY AUDIT: {overall} ===")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()

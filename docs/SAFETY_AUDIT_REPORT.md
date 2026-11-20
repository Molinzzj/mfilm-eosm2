# SAFETY_AUDIT_REPORT.md — Canon EOS M2 (1.0.3) 六项确定性安全与协议合规审计报告

> **最终结论**：**`PASS`**（6 项强制安全与协议合规门禁 + 成品 ZIP 结构核验全部通过，允许交付 `dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`）

---

## 一、 审计执行命令

```bash
python3 /home/antigravity/workspace/tools/verify_m2_safety.py /home/antigravity/dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
```

## 二、 脚本原始 `stdout` 输出（未经人工删改）

```text
[CHECK 1] stubs.S 100% Hex Address Consistency: PASS
  RAM_OFFSET: (0xFFD1F0E4-0x1900) == (0xFFD1F0E4-0x1900)
  0xFF... lines: old=135, new=135
  Active NSTUBs: old=144, new=144
[CHECK 2] Makefile Base Addresses & FW 1.0.3 Identity: PASS
  MODEL = EOSM2 (expected EOSM2)
  FW_VERSION = 103 (expected 103)
  MAIN_FIRMWARE_ADDR = 0xFF0C0000 (expected 0xFF0C0000)
  ROMBASEADDR = 0xFF0C0000 (expected 0xFF0C0000)
  RESTARTSTART = 0x44C100 (expected 0x44C100)
[CHECK 3] consts.h / gui.h VRAM & BGMT_* Constants Integrity: PASS
  Verified 19 VRAM/HIJACK/ROM constants + MALLOC_STRUCT_ADDR + LV_OVERLAYS_MODE
  Verified 31 BGMT_* keycodes (incl. BGMT_PLAY=0xb, BGMT_MENU=0x6)
[CHECK 4] M-Film Symbol Resolution & Boot Memory Budget (< 605952 B): PASS
  Boot memory: _bss_end(0x4CF400) - RESTARTSTART(0x44C100) = 537344 bytes / 605952 bytes (headroom: 68608 bytes / 67.0 KB)
  filmos.mo symbols: 96 UND (all resolved in 1384 exported syms), 6 GLOBAL defined (0 clashes), 0 .ARM.ex* sections
[CHECK 5] Global Auto-Bootflag Call Scan: PASS
  Scanned files: 64 (+ 03_mfilm git diff) | Forbidden call matches: 0
[CHECK 6] GPL-2.0 / GPL-3.0 License Firewall & SpektraFilm Isolation Scan: PASS
  Scanned files (02_ml_simplified + 03_mfilm changes): 75 | Violations: 0
[ARTIFACT] dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
  Size: 18327416 bytes
  SHA256: b1f25f312c32e2e62a0b07530005b98134d284f17fc1962fee9ac818bd373f84
  Entries: 206 | required_missing=0 | DARKROOM=True | SAMPLES=True | ext_cfgs=20 | attribution=True | junk=0
=== OVERALL SAFETY AUDIT: PASS ===
```

---

## 三、 门禁细项与关键产物摘要

| 检查项 | 审计目标 | 实测结果 | 状态 |
| :--- | :--- | :--- | :---: |
| **CHECK 1** | 新旧 `EOSM2.103/stubs.S` 全部 135 条 `0xFF...` 地址与 144 条 `NSTUB` 100% 一致 | `old=135, new=135`；`RAM_OFFSET` 完全一致 | **`PASS`** |
| **CHECK 2** | `Makefile` 机型、固件 1.0.3、ROM/启动基址匹配 | `MODEL=EOSM2`, `FW_VERSION=103`, `MAIN_FIRMWARE_ADDR=0xFF0C0000`, `ROMBASEADDR=0xFF0C0000`, `RESTARTSTART=0x44C100` | **`PASS`** |
| **CHECK 3** | `consts.h` / `gui.h` 显存基址与 `BGMT_*` 按键事件码零变动 | 19 项 VRAM/HIJACK/ROM 常量 + 31 项 `BGMT_*` 按键码 100% 匹配 | **`PASS`** |
| **CHECK 4** | `autoexec.bin` 启动内存 `< 605,952 bytes`（592 KB）且与 `filmos.mo` 符号表完全对齐 | 启动占用 `537,344 / 605,952 bytes`（余量 `67.0 KB`，较 Stage 3 零增加）；`filmos.mo` 96 项未定义符号 100% 解析，0 冲突，0 unwind 表 | **`PASS`** |
| **CHECK 5** | 全局扫描零自动写入 NVRAM Bootflag 调用 | 扫描 64 文件 + `03_mfilm` 全部 diff，命中 `0` 处 | **`PASS`** |
| **CHECK 6** | **GPL-2.0 / GPL-3.0 协议防火墙与 SpektraFilm 隔离扫描** | 扫描 `02_ml_simplified` 与 `03_mfilm` 共 75 文件，命中 `0` 处 GPL-3.0 许可证头或 `spektrafilm` 源码引用 | **`PASS`** |
| **ARTIFACT** | `dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` 结构与 SHA256 核验 | 206 个条目，含 `autoexec.bin`、`ML/modules/filmos.mo`、20 个外部 `.cfg` 配置与 `PROFILES_ATTRIBUTION.txt`，0 垃圾文件 | **`PASS`** |

### 核心文件 SHA256 校验值

- `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` (`18,327,416` bytes): `b1f25f312c32e2e62a0b07530005b98134d284f17fc1962fee9ac818bd373f84`
- `autoexec.bin`: `7ff3e13c67c15133115fd432c3f875e8301bed6d36e8fc14fec4f15482d252fe`
- `ML/modules/filmos.mo` (`287,188` bytes): `697a9ef029e49f58986942c59853fb056585277da927925afffc905d432f213e`
- `ML/MFILM/profiles/PROFILES_ATTRIBUTION.txt`: `fea4d36597823761d5fc514865ba945c71ff7113a69fea561ec111776ccdd2cb`

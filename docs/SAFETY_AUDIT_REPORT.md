# SAFETY_AUDIT_REPORT.md — Canon EOS M2 (1.0.3) 六项确定性安全与协议合规审计报告

> **最终结论**：**`PASS`**（6 项强制安全与协议合规门禁 + `01` / `02` / `03` 全部三个成品 ZIP 包 `ML/MODULES/EOSM2103.SYM` 非空与结构核验全部通过，允许交付 `dist/` 全部三阶段测试包）

---

## 一、 审计执行命令

```bash
python3 scripts/verify_m2_safety.py \
  dist/01_EOSM2_Clean_ML_Base.zip \
  dist/02_EOSM2_MFilm_023_TestBuild.zip \
  dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
```

## 二、 脚本原始 `stdout` 输出（未经人工删改）

```text
[CHECK 1] stubs.S 100% Hex Address Consistency: PASS
  Golden SHA256: 3e2fac9cd81035a7b290fe601f39c69c1e3359ee05eb14f760e65ca85be27113
  RAM_OFFSET: (0xFFD1F0E4-0x1900) == (0xFFD1F0E4-0x1900)
  0xFF... lines: ref=135, build=135
  Active NSTUBs: ref=144, build=144
[CHECK 2] Makefile Base Addresses & FW 1.0.3 Identity: PASS
  MODEL = EOSM2 (expected EOSM2)
  FW_VERSION = 103 (expected 103)
  MAIN_FIRMWARE_ADDR = 0xFF0C0000 (expected 0xFF0C0000)
  ROMBASEADDR = 0xFF0C0000 (expected 0xFF0C0000)
  RESTARTSTART = 0x44C100 (expected 0x44C100)
  ML_MODULES_SYM_NAME = EOSM2103.SYM (expected EOSM2103.SYM)
[CHECK 3] consts.h / gui.h VRAM & BGMT_* Constants Integrity: PASS
  Verified 20 VRAM/HIJACK/ROM/MALLOC constants + LV_OVERLAYS_MODE
  Verified 31 BGMT_* keycodes (incl. BGMT_PLAY=0xb, BGMT_MENU=0x6)
[CHECK 4] M-Film Symbol Resolution & Boot Memory Budget (< 605952 B): PASS
  Boot memory: _bss_end(0x4CF400) - RESTARTSTART(0x44C100) = 537344 bytes / 605952 bytes (headroom: 68608 bytes / 67.0 KB)
  filmos.mo symbols: 96 UND (all resolved in 1384 exported syms), 6 GLOBAL defined (0 clashes), 0 .ARM.ex* sections
[CHECK 5] Global Auto-Bootflag Call Scan: PASS
  Scanned files: 77 (+ mfilm git diff) | Forbidden call matches: 0
[CHECK 6] GPL-2.0 / GPL-3.0 License Firewall & SpektraFilm Isolation Scan: PASS
  Scanned files (firmware tree + patches + mfilm changes): 90 | Violations: 0
[ARTIFACT] dist/01_EOSM2_Clean_ML_Base.zip
  Size: 1658202 bytes
  SHA256: c21ec7c285e5965e78ca4d05a9dc71990739a46ab5f51410c11a2092681ae4a5
  Entries: 52 | EOSM2103.SYM=36578 B | required_missing=0 | legacy_sym=0 | DARKROOM=False | SAMPLES=False | ext_cfgs=0 | attribution=False | junk=0
[ARTIFACT] dist/02_EOSM2_MFilm_023_TestBuild.zip
  Size: 18469723 bytes
  SHA256: 2bd9287a0801bfbf9eadd9862f6938b90af462b570cc2ae5ca51c6944b956f7a
  Entries: 196 | EOSM2103.SYM=36710 B | required_missing=0 | legacy_sym=0 | DARKROOM=True | SAMPLES=True | ext_cfgs=0 | attribution=False | junk=0
[ARTIFACT] dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
  Size: 18488231 bytes
  SHA256: 4d519037c724bb160749baba11f6361b56a181bcb3a23233ce845cca8ba7edb2
  Entries: 219 | EOSM2103.SYM=36710 B | required_missing=0 | legacy_sym=0 | DARKROOM=True | SAMPLES=True | ext_cfgs=20 | attribution=True | junk=0
=== OVERALL SAFETY AUDIT: PASS ===
```

---

## 三、 门禁细项与关键产物摘要

| 检查项 | 审计目标 | 实测结果 | 状态 |
| :--- | :--- | :--- | :---: |
| **CHECK 1** | `EOSM2.103/stubs.S` 黄金 SHA256 与构建树全部 135 条 `0xFF...` 地址、144 条 `NSTUB` 100% 一致 | Golden SHA256 匹配；`ref=135, build=135`；`RAM_OFFSET` 完全一致 | **`PASS`** |
| **CHECK 2** | `Makefile` 机型、固件 1.0.3、ROM/启动基址及 DryOS 8.3 符号文件名匹配 | `MODEL=EOSM2`, `FW_VERSION=103`, `MAIN_FIRMWARE_ADDR=0xFF0C0000`, `ROMBASEADDR=0xFF0C0000`, `RESTARTSTART=0x44C100`, `ML_MODULES_SYM_NAME=EOSM2103.SYM` | **`PASS`** |
| **CHECK 3** | `consts.h` / `gui.h` 黄金 SHA256、显存基址与 `BGMT_*` 按键事件码零变动 | 20 项 VRAM/HIJACK/ROM/MALLOC 常量 + `LV_OVERLAYS_MODE` + 31 项 `BGMT_*` 按键码 100% 匹配 | **`PASS`** |
| **CHECK 4** | `autoexec.bin` 启动内存 `< 605,952 bytes`（592 KB）、内嵌 `ML/MODULES/EOSM2103.SYM` 路径且与 `filmos.mo` 符号表完全对齐 | 启动占用 `537,344 / 605,952 bytes`（余量 `67.0 KB`）；`autoexec.bin` 仅含 `ML/MODULES/EOSM2103.SYM`（无旧 9 字符 `EOSM2_103.sym`）；`filmos.mo` 96 项未定义符号 100% 解析，0 冲突，0 unwind 表 | **`PASS`** |
| **CHECK 5** | 全局扫描零自动写入 NVRAM Bootflag 调用 | 扫描 77 个源码/补丁文件 + M-Film 全部 diff，命中 `0` 处 | **`PASS`** |
| **CHECK 6** | **GPL-2.0 / GPL-3.0 协议防火墙与 SpektraFilm 隔离扫描** | 扫描固件树、补丁与 M-Film 改动共 90 文件，命中 `0` 处 GPL-3.0 许可证头或 `spektrafilm` 源码引用 | **`PASS`** |
| **ARTIFACT 01** | `dist/01_EOSM2_Clean_ML_Base.zip` 结构与 `ML/MODULES/EOSM2103.SYM` 非空核验 | 52 个条目，`EOSM2103.SYM` = `36,578 B`，0 旧符号名，0 垃圾文件 | **`PASS`** |
| **ARTIFACT 02** | `dist/02_EOSM2_MFilm_023_TestBuild.zip` 结构与 `ML/MODULES/EOSM2103.SYM` 非空核验 | 196 个条目，`EOSM2103.SYM` = `36,710 B`，含 `ML/MODULES/filmos.mo`、`ML/DARKROOM/`、`ML/SAMPLES/`，0 旧符号名，0 垃圾文件 | **`PASS`** |
| **ARTIFACT 03** | `dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` 结构与 `ML/MODULES/EOSM2103.SYM` 非空核验 | 219 个条目，`EOSM2103.SYM` = `36,710 B`，含 `ML/MODULES/filmos.mo`、20 个外部 `.cfg` 配置与 `PROFILES_ATTRIBUTION.txt`，0 旧符号名，0 垃圾文件 | **`PASS`** |

---

## 四、 DryOS 8.3 短文件名修复说明（根因闭环）

1. **实机报错根因**：EOS M2 单卡槽在 DryOS `src/fio-ml.c` 下正常映射到 `B:/`（`ML_CARD = &available_cards[CARD_B]`），但默认 `ML_MODULES_SYM_NAME` 生成的 `EOSM2_103.sym` 主文件名长 9 个字符，超出 DryOS 原生 FAT32（未开启 LFN）的 **8.3 短文件名限制**，导致 `FIO_GetFileSize("ML/MODULES/EOSM2_103.sym", ...)` 直接返回文件不存在，`_module_load_all()` 提前退出，未注册可见 `Modules` 标签页且未加载 `filmos.mo`。
2. **修复方案**：在 `platform/EOSM2.103/Makefile` 中定义 `ML_MODULES_SYM_NAME = EOSM2103.SYM`（严格 8+3 全大写，与上游 `1100D.105` / `1300D.110` 规避机制一致），`src/module.c` 通过 `-DCONFIG_MODULES_MODEL_SYM=\"EOSM2103.SYM\"` 自动查找 `ML/MODULES/EOSM2103.SYM`，打包脚本统一规范化输出 `ML/MODULES/EOSM2103.SYM` 与 `ML/MODULES/filmos.mo`。

---

## 五、 核心文件 SHA256 校验值（本次本地复现构建）

- `dist/01_EOSM2_Clean_ML_Base.zip` (`1,658,202` bytes): `c21ec7c285e5965e78ca4d05a9dc71990739a46ab5f51410c11a2092681ae4a5`
- `dist/02_EOSM2_MFilm_023_TestBuild.zip` (`18,469,723` bytes): `2bd9287a0801bfbf9eadd9862f6938b90af462b570cc2ae5ca51c6944b956f7a`
- `dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` (`18,488,231` bytes): `4d519037c724bb160749baba11f6361b56a181bcb3a23233ce845cca8ba7edb2`
- `autoexec.bin` (Stage 01, `453,088` bytes): `ced994d7344def002f92970eeb3c2ca94d223fb14f99a032b3cdda59c41aaa02`
- `autoexec.bin` (Stage 02/03, `453,984` bytes): `0f40e9a3bdf25e55e74fd882708c6b00a4de9172180bd00dbbe2948ea6c09948`
- `ML/MODULES/EOSM2103.SYM` (Stage 02/03, `36,710` bytes): `3babc4c5685e81a288bfeb8811cfcb46b623ad3f5b17ea9caa307bb5794ae25c`
- `ML/MODULES/filmos.mo` (`287,188` bytes): `ca408629cec1b3acdc803abfb0f7f083add2ab70e6364fac77c487dc4026644a`
- `ML/MFILM/profiles/PROFILES_ATTRIBUTION.txt` (`1,862` bytes): `fea4d36597823761d5fc514865ba945c71ff7113a69fea561ec111776ccdd2cb`

# SAFETY_AUDIT_REPORT.md — Canon EOS M2 (1.0.3) 六项确定性安全与协议合规审计报告

> **最终结论**：**`PASS`**（6 项强制安全与协议合规门禁 + 成品 ZIP 结构核验 + 跨机型 `EOSM.202` 冒烟编译 + 宿主机 `fos_extprof` 零泄漏单元测试全部通过，允许交付 `dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`）

---

## 一、 审计执行命令

```bash
python3 scripts/verify_m2_safety.py dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
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
[ARTIFACT] dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
  Size: 18488243 bytes
  SHA256: 8ae94d461a71c43ff48812fa9caece0b70b4ff53a919ba7b31e01575a9d577b5
  Entries: 219 | required_missing=0 | DARKROOM=True | SAMPLES=True | ext_cfgs=20 | attribution=True | junk=0
=== OVERALL SAFETY AUDIT: PASS ===
```

---

## 三、 门禁细项与关键产物摘要

| 检查项 | 审计目标 | 实测结果 | 状态 |
| :--- | :--- | :--- | :---: |
| **CHECK 1** | `EOSM2.103/stubs.S` 黄金 SHA256 与构建树全部 135 条 `0xFF...` 地址、144 条 `NSTUB` 100% 一致 | Golden SHA256 匹配；`ref=135, build=135`；`RAM_OFFSET` 完全一致 | **`PASS`** |
| **CHECK 2** | `Makefile` 机型、固件 1.0.3、ROM/启动基址匹配 | `MODEL=EOSM2`, `FW_VERSION=103`, `MAIN_FIRMWARE_ADDR=0xFF0C0000`, `ROMBASEADDR=0xFF0C0000`, `RESTARTSTART=0x44C100` | **`PASS`** |
| **CHECK 3** | `consts.h` / `gui.h` 黄金 SHA256、显存基址与 `BGMT_*` 按键事件码零变动 | 20 项 VRAM/HIJACK/ROM/MALLOC 常量 + `LV_OVERLAYS_MODE` + 31 项 `BGMT_*` 按键码 100% 匹配 | **`PASS`** |
| **CHECK 4** | `autoexec.bin` 启动内存 `< 605,952 bytes`（592 KB）且与 `filmos.mo` 符号表完全对齐 | 启动占用 `537,344 / 605,952 bytes`（余量 `67.0 KB`，零增长）；`filmos.mo` 96 项未定义符号 100% 解析，0 冲突，0 unwind 表 | **`PASS`** |
| **CHECK 5** | 全局扫描零自动写入 NVRAM Bootflag 调用 | 扫描 77 个源码/补丁文件 + M-Film 全部 diff，命中 `0` 处 | **`PASS`** |
| **CHECK 6** | **GPL-2.0 / GPL-3.0 协议防火墙与 SpektraFilm 隔离扫描** | 扫描固件树、补丁与 M-Film 改动共 90 文件，命中 `0` 处 GPL-3.0 许可证头或 `spektrafilm` 源码引用 | **`PASS`** |
| **ARTIFACT** | `dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` 结构与 SHA256 核验 | 219 个条目，含 `autoexec.bin`、`ML/modules/filmos.mo`、20 个外部 `.cfg` 配置与 `PROFILES_ATTRIBUTION.txt`，0 垃圾文件 | **`PASS`** |

---

## 四、 `fos_extprof` 全机型通用化审计、跨机型编译与内存池单元测试

1. **全机型通用性代码审计（`patches/03-mfilm-extprof-loader.patch`）**：
   - 核查 `fos_extprof.h`、`fos_extprof.c`、`fos_film.c`、`fos_dev.c`、`filmroll.c` 与 `filmos_mod.h` 全部接入点：
     - **零 `EOSM2` 专属宏**（不依赖 `CONFIG_EOSM2`）；
     - **零硬编码屏幕坐标**（不直接访问 VRAM，仅填充标准 `fos_label` / `fos_film` / `fos_look` 元数据）；
     - **零特定相机内存或盘符假设**（文件遍历与读写完全通过 `fos_port_card()` / `fos_port_list()` / `fos_port_open()` / `fos_port_read()` / `fos_port_close()`，内存分配完全通过 `fos_port_alloc()` / `fos_port_free()`，天然兼容 `EOSM2.103`、`EOSM.202`、`6D.116` 等全部 M-Film 支持机型）。
2. **跨机型（`EOSM.202`）`filmos.mo` 冒烟编译**：
   - 使用 `ML_SRC="${PWD}/build/magiclantern_simplified" bash build/mfilm-canon-film-simulation/ml-dev/build_fork.sh EOSM.202 --module`（内置 `FATAL_WARNINGS=y` 及 `-Wall -Wextra -Werror -Wdouble-promotion -Wnull-dereference`）完整编译上游机型 `EOSM.202` 的 `filmos.mo`。
   - **实测结果**：**`PASS`** — 零编译错误、零新增警告，成功产出 `build/mfilm-canon-film-simulation/ml-dev/out/fork/ML/modules/filmos.mo`（`287,284` bytes），包含全部 `fos_extprof_*` 符号且 0 `.ARM.ex*` unwind 节。
3. **宿主机内存池零泄漏单元测试（`gcc -O2 -Wall -Wextra -Werror`）**：
   - 在宿主机对 `fos_extprof.c` 执行完整生命周期测试（含合法彩色/黑白 `.cfg` 解析、畸形与非 `.cfg` 过滤、3D LUT 即时合成、重复调用 `fos_extprof_load_all()`、释放 `fos_extprof_free_all()` 及覆盖全部分配点的 OOM 故障注入）。
   - **实测结果**：**`PASS`** — `fos_extprof host unit test PASS: Allocs=39, Frees=39, LiveBytes=0, PeakBytes=11056`（严格满足 `Allocs == Frees`，零内存泄漏）。

---

## 五、 核心文件 SHA256 校验值（本次本地复现构建）

- `dist/01_EOSM2_Clean_ML_Base.zip`: `9f32c5ad70b62f9b7f00333b76c174c520ff552ba85cc21c7bf2f001538633f2`
- `dist/02_EOSM2_MFilm_023_TestBuild.zip`: `fa5646dd91a918b77e1cadaf9ea53f2bed37141723234e3d96053807a38f3ef8`
- `dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` (`18,488,243` bytes): `8ae94d461a71c43ff48812fa9caece0b70b4ff53a919ba7b31e01575a9d577b5`
- `autoexec.bin` (`454,048` bytes): `400f6a68cca7743c13dda8dc58e56a6e3c89d15f13d7f2258acd7041a865a1c3`
- `ML/modules/filmos.mo` (`287,188` bytes): `819c2420be8da4247618b4f6f4404b6f4c1c6d7efdf20d9cb66b89bb6743c9e8`
- `ML/MFILM/profiles/PROFILES_ATTRIBUTION.txt` (`1,862` bytes): `fea4d36597823761d5fc514865ba945c71ff7113a69fea561ec111776ccdd2cb`

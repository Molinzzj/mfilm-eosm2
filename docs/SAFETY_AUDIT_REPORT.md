# SAFETY_AUDIT_REPORT.md — Canon EOS M2 (1.0.3) M-Film 0.2.3 自动化安全审计报告

- **目标机型与固件**：Canon EOS M2（DIGIC 5 / ARM946E-S / 官方固件 **1.0.3** / `EOSM2.103`）
- **构建版本**：`reticulatedpines/magiclantern_simplified` (`142472e9`) + `HNGSeries/mfilm-canon-film-simulation` (`3c3986dd`, **M-Film 0.2.3**, `--module` 外挂模块模式)
- **审计脚本**：`scripts/verify_m2_safety.py`
- **最终门禁裁决**：**`PASS`**（全部 5 项硬性门禁 + ZIP 结构核验均通过）

---

## 一、 自动化审计原始输出

执行命令：
```bash
python3 scripts/verify_m2_safety.py dist/02_EOSM2_MFilm_023_TestBuild.zip
```

审计输出摘要（退出码 `0`）：
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
  Scanned files: 60 (+ M-Film git diff) | Forbidden call matches: 0
[ARTIFACT] dist/02_EOSM2_MFilm_023_TestBuild.zip
  Size: 18527660 bytes
  SHA256: f63ed2986139bb4cd2836c815b41344642021d569f83c683defda2e38698a103
  Entries: 196 | required_missing=0 | DARKROOM=True | SAMPLES=True | junk=0
=== OVERALL SAFETY AUDIT: PASS ===
```

---

## 二、 关键架构与内存安全复核

1. **开机内存占用与 592 KB 固定预留红线**：
   - `EOSM2.103` 采用 `boot-d45-am.c` 的固定 `AllocateMemory` 预留机制（`0x44C100` ~ `0x4E0000`，硬上限 `605,952 bytes`）。
   - 集成 M-Film 0.2.3 三个核心钩子（`filmhook.c`）并采用 `--module` 外挂模块模式后，`_bss_end(0x4CF400) - RESTARTSTART(0x44C100)` 仅为 **`537,344 bytes`**（相比纯净底座仅增加 `1,024 bytes`），保留 **`68,608 bytes`（`67.0 KB`）安全余量**，不会触发 `boot.h` 的 3 长 3 短读卡灯开机拒启保护。
2. **EOS M 无反双特性完整继承**：
   - `fork/src/filmroll.c`：`#if defined(CONFIG_EOSM) || defined(CONFIG_EOSM2)` 启用 `FOS_LV_ONLY = 1` 与 `HUD_HOLDS = (!FOS_LV_ONLY || canon_hidden)`，完整继承 `Settings -> Advanced -> Hide Canon's graphics` 原厂图形屏蔽开关。
   - `filmos/fos_hud.c`：`#if !defined(CONFIG_EOSM) && !defined(CONFIG_EOSM2)` 跳过单反顶屏（top plate）绘制代码，仅保留低开机内存取景器 HUD 直接屏幕绘制路径。
3. **暗房 CR2 显影与 JPEG 输出内存池路径**：
   - `fos_dev.c`、`fos_jpeg.c`、`fos_dark.c` 均通过 `fos_port_alloc()` → `tmp_malloc()`（`src/mem.h` 中映射到 `MEM_TEMPORARY`，优先借用相机图像缓存池 `shoot_malloc`）分配大块显影/编码缓冲区，文件读取使用 `fio_malloc()`。
   - 显影结束或失败路径均通过 `fos_jpeg_close()`、`fos_dev_free()`、`big_free()` 及时调用 `fos_port_free()` → `free()` 释放；且 `big_setup()` 主动预留 `512 KB + FOS_PRINT_W*FOS_PRINT_H*3` 余量并在不足时自动降级尺寸，防止 DIGIC 5 运行内存 OOM。
4. **模块加载器兼容性**：
   - 使用通配符剥离 GCC 12 `libgcc` 的全部 `.ARM.exidx*` / `.ARM.extab*`（含 `.rel.ARM.ex*`）unwind 段，消除 Magic Lantern TCC 模块加载器崩溃隐患。
   - `filmos.mo` 全部 96 个未定义外部符号 100% 命中 `ML/modules/EOSM2_103.sym`（1,384 个导出符号），零缺失、零符号冲突。

---

## 三、 成品与核心二进制 SHA256 校验值

| 文件 | 大小 | SHA256 |
| :--- | :--- | :--- |
| `01_EOSM2_Clean_ML_Base.zip` | `1,659,995` bytes | `9f52ae767858d2079a8d4d528b9aa7ce6aa2a9437393becfffd2640fbfd8b8c8` |
| `02_EOSM2_MFilm_023_TestBuild.zip` | `18,527,660` bytes | `f63ed2986139bb4cd2836c815b41344642021d569f83c683defda2e38698a103` |
| `autoexec.bin` (M-Film) | `454,304` bytes | `d3e7e7a4fbd316d25f9e0c9c5f60e565d5b21e643897df6cc5ae3644ad0dc6e6` |
| `ML/modules/filmos.mo` | `278,340` bytes | `fc52ae0f83d5a7ad31fd210402d1326a6d372a79abad656561e308a9cb11c7bd` |
| `ML/modules/EOSM2_103.sym` | `36,684` bytes | `2f30d824277007b7dab31a9b01455b7806cf2a87bd7abed148aeefddabbf29db` |
| `ML-SETUP.FIR` | `34,012` bytes | `a77d4b8a5121ce386e4c9e64c55b80b208deb7415fd0e4da79966a43e31a951b` |

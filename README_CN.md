# M-Film for Canon EOS M2（官方固件 1.0.3）

[![Build & Safety Audit](https://github.com/Molinzzj/mfilm-eosm2/actions/workflows/build-and-audit.yml/badge.svg)](https://github.com/Molinzzj/mfilm-eosm2/actions/workflows/build-and-audit.yml)
![Hardware Verification](https://img.shields.io/badge/EOS%20M2%20(1.0.3)-Hardware%20Verified%20(PASS)-brightgreen)

[English Documentation (README.md)](./README.md)

为 **Canon EOS M2**（DIGIC 5 / ARM946E-S，官方固件 **1.0.3**）移植现代 **Magic Lantern**（基于 [`reticulatedpines/magiclantern_simplified`](https://github.com/reticulatedpines/magiclantern_simplified)），并完整集成 **M-Film v0.2.3**（[`HNGSeries/mfilm-canon-film-simulation`](https://github.com/HNGSeries/mfilm-canon-film-simulation)）胶片模拟与机内暗房系统。

> **实机验证状态**：**Hardware Verified (PASS)** — 已在真实 **Canon EOS M2（官方固件 1.0.3）** 机身上完整通过第一阶段（纯净魔灯底座）、第二阶段（M-Film 0.2.3 核心与机内暗房）及第三阶段（20 款外置 SpektraFilm `.cfg` 胶片加载与显影）全部实测。

---

## ⚠️ 安全警告 — 使用前请务必阅读

> [!CAUTION]
> - **🔴 重要固件红线警告 — 仅支持官方固件 `1.0.3`，严禁升级至 `1.0.4`！**
>   - 本项目严格锁定且仅支持 **Canon EOS M2 官方固件 `1.0.3`**（`EOSM2.103`）。
>   - 当前为 **`1.0.1`** 或 **`1.0.2`** 的用户，可从佳能官网下载官方 **`1.0.3`** 固件安全升级后再使用。
>   - **严禁升级至佳能官网最新的 `1.0.4` 安全补丁版固件！`1.0.4` 无法降级且完全不支持 Magic Lantern / M-Film！**
> - **强烈推荐非持久化加载**：请通过相机原厂菜单 **扳手设置 → 固件版本 1.0.3 → 固件升级（Firmware Update）** 进行安全非持久化加载。除非明确了解风险，否则**请勿**写入或开启相机 NVRAM Bootflag（开机自启）。
> - **零自动 Bootflag 写入**：本项目全部构建均经过 `scripts/verify_m2_safety.py` 静态与二进制门禁审计，确认无任何自动 `EnableBootDisk` / `SetBootFlag` 调用，且 100% 保留经实机验证的 `EOSM2.103` 硬件地址表。
> - **自刷风险提示**：运行第三方相机固件存在固有风险，请自担风险。在非持久化加载模式下，若遇到黑屏或卡死，**直接抠出电池静置 5 秒后装回**即可 100% 恢复佳能原厂系统。

---

## 核心特性

- **现代魔灯底座（`EOSM2.103`）— Hardware Verified (PASS)**：将经典 EOS M2 1.0.3 DryOS 端口迁移至 `magiclantern_simplified`，100% 原样保留全部 144 个有效 `NSTUB` 固件地址、显存基址及 `BGMT_*` 按键码；符号表采用严格符合 DryOS FAT32 8.3 短文件名规范的 **`ML/MODULES/EOSM2103.SYM`**，确保模块加载稳定可靠。
- **M-Film v0.2.3 外挂模块模式（`--module`）— Hardware Verified (PASS)**：将 Film OS 与机内 CR2→JPEG 暗房编译为外挂模块 `ML/MODULES/filmos.mo`，严格控制在 DIGIC 5 固定 592 KB（`605,952 B`）开机内存红线内（实际占用 `537,344 B`，剩余 `67.0 KB` 安全余量）。
- **无反低内存 HUD 与原厂图形屏蔽**：完整继承 EOS M 无反优化 — 跳过单反顶屏代码、采用低开机内存取景器 HUD 直接绘制，并支持 **`Settings → Advanced → Hide Canon's graphics`** 一键屏蔽佳能原厂曝光标尺与图标。
- **全机型通用外置胶片加载器（`fos_extprof`）— Hardware Verified (PASS)**：纯 GPL-2.0 净室实现，零 `EOSM2` 专属宏、零硬编码屏幕坐标与特定相机内存假设，全面基于 `fos_port_*` 文件与临时内存池接口，兼容所有 M-Film 支持机型（`EOSM2.103`、`EOSM.202`、`6D.116` 等）；已通过 EOS M2（1.0.3）真机 20 款外置 `(SF)` `.cfg` 实测、上游 `EOSM.202` 的 `filmos.mo` 冒烟编译（`FATAL_WARNINGS=y` 零错误零警告）及宿主机内存池零泄漏单元测试（`Allocs == Frees`）。
- **三阶段发布包（Three-Stage Release Bundles）**：
  - `01_EOSM2_Clean_ML_Base.zip`：纯净魔灯底座（含 `ML/MODULES/EOSM2103.SYM`），用于独立验证开机、菜单与按键响应。
  - `02_EOSM2_MFilm_023_TestBuild.zip`：标准 M-Film v0.2.3 发布包（含 `ML/MODULES/filmos.mo`、`ML/MODULES/EOSM2103.SYM` 及内置机内暗房 LUT 与胶片预设）。
  - `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`：M-Film v0.2.3 集成动态外置配置加载器（`fos_extprof`），并在 `ML/MFILM/profiles/` 目录预置 20 款离线烘焙的 SpektraFilm `(SF)` 胶片配置。

---

## 快速上手指南（4 步完成）

1. **确认固件（仅限 `1.0.3`）并准备 SD 卡**：确认 EOS M2 为官方固件 **`1.0.3`**（`1.0.1` / `1.0.2` 用户可从佳能官网下载 `1.0.3` 升级；**严禁升级至 `1.0.4`**），使用满电电池与 **≤ 32 GB 的 FAT32 格式 SD 卡**（建议先在相机内格式化一次）。
2. **下载成品压缩包**：前往 [GitHub Releases](https://github.com/Molinzzj/mfilm-eosm2/releases) 或本仓库 [GitHub Actions (`Build & Safety Audit`)](https://github.com/Molinzzj/mfilm-eosm2/actions/workflows/build-and-audit.yml) 最新绿灯记录的 **Artifacts（`eos-m2-mfilm-bundles-and-reports`，保留 30 天）**，下载 `01_EOSM2_Clean_ML_Base.zip`、`02_EOSM2_MFilm_023_TestBuild.zip` 或 `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`（推荐 — 预置 20 款 `(SF)` 外置胶片配置），并核对 `.sha256` 校验值。
3. **解压至 SD 卡根目录**：将压缩包**直接解压至 SD 卡根目录**，确保根目录直接出现 `autoexec.bin`、`ML-SETUP.FIR`、`ML/MODULES/EOSM2103.SYM` 与 `ML/` 文件夹（切勿多套一层子目录）。若使用 `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`，解压后还会自动填充 `ML/MFILM/profiles/*.cfg`（20 款 `(SF)` 配置）与 `ML/MFILM/profiles/PROFILES_ATTRIBUTION.txt`，开机进入 M-Film 选卷架即可直接选用。
4. **通过固件升级安全加载**：插卡开机，将拍摄模式拨盘调至 **M / Av / Tv** 静态照片档，在佳能菜单中将画质设为 **RAW**（机内暗房必需），进入 **固件版本 1.0.3 → 固件升级** 执行非持久化加载。进入实时取景后**长按删除键（Trash）**即可呼出 Magic Lantern / M-Film 菜单。

覆盖全部三个发布包的完整三阶段实机验证报告（**Hardware Verified (PASS)**）请参阅 [`docs/REAL_CAMERA_SMOKE_TEST.md`](./docs/REAL_CAMERA_SMOKE_TEST.md)。

---

## 仓库目录结构

```text
.
├── .github/workflows/
│   └── build-and-audit.yml              # 全自动 CI：三包构建、EOSM.202 冒烟、6 项安全审计与产物上传
├── platform/EOSM2.103/                  # 审计通过的 EOS M2 (1.0.3) 平台源码目录
├── patches/
│   ├── 01-ml-simplified-eosm2.patch     # 针对 magiclantern_simplified 的最小化补丁
│   ├── 02-mfilm-eosm2.patch             # 针对 M-Film v0.2.3 的最小化补丁
│   └── 03-mfilm-extprof-loader.patch    # 全机型通用净室 GPL-2.0 外置 .cfg 胶片加载器补丁 (fos_extprof)
├── scripts/
│   ├── bake_sd_profiles.py              # 宿主机离线黑盒 SpektraFilm 烘焙脚本 -> ML/MFILM/profiles/*.cfg
│   ├── build_all.sh                     # 自动拉取上游特定 Commit、打补丁并构建 01/02 包脚本
│   ├── build_03_bundle.sh               # 非交互式 03 包组装脚本（独立临时目录克隆烘焙，零仓库污染）
│   └── verify_m2_safety.py              # 6 项静态/二进制安全与协议合规门禁审计脚本
├── docs/
│   ├── REAL_CAMERA_SMOKE_TEST.md        # 三阶段实机安全冒烟测试指南
│   ├── SAFETY_AUDIT_REPORT.md           # 6 项安全审计、跨机型编译与零泄漏测试报告（PASS）
│   └── SPEKTRAFILM_BAKE_REPORT.md       # SpektraFilm 离线烘焙与 ΔE2000 色差评估报告
├── LICENSE                              # GNU General Public License v2.0 协议全文
├── README.md                            # 英文主说明文档
└── README_CN.md                         # 中文说明文档
```

---

## 从源码构建指南

### 构建依赖

- **ARM 交叉编译器**：`arm-none-eabi-gcc`、`binutils-arm-none-eabi`、`libnewlib-arm-none-eabi`（已在 Ubuntu `gcc-arm-none-eabi` 与 xPack GNU Arm Embedded GCC `12.3.1-1.2` 验证通过）
- **宿主机工具**：`gcc`、`make`、`git`、`python3`、`zip`、`unzip`
- **Python 3 依赖**：`docutils`、`setuptools`、`numpy`、`segno`（若运行 `scripts/build_03_bundle.sh` 离线烘焙，另需 `scipy`、`colour-science`、`scikit-image`、`matplotlib`、`opt-einsum`、`numba`、`OpenImageIO`、`pyfftw`、`rawpy`、`exiv2`、`lensfunpy`）

### 一键复现构建（`01`、`02` 与 `03` 测试包）

```bash
git clone https://github.com/Molinzzj/mfilm-eosm2.git
cd mfilm-eosm2

# 构建第一阶段（纯净魔灯底座 01）与第二阶段（M-Film v0.2.3 02）
./scripts/build_all.sh

# 可选：在独立临时目录自动烘焙 20 款 SpektraFilm (SF) 配置并组装第三阶段 03 测试包
./scripts/build_03_bundle.sh
```

- `scripts/build_all.sh` 会自动拉取锁定版本的 `reticulatedpines/magiclantern_simplified`（`142472e9`）与 `HNGSeries/mfilm-canon-film-simulation`（`3c3986dd`，v0.2.3），合入 `platform/EOSM2.103/` 与全部补丁，并产出 `dist/01_EOSM2_Clean_ML_Base.zip`、`dist/02_EOSM2_MFilm_023_TestBuild.zip` 及其 `.sha256` 校验文件。
- `scripts/build_03_bundle.sh` 会自动将 `andreavolpato/spektrafilm` 浅克隆至仓库外的独立临时目录（`mktemp -d`，退出自动清理），调用 `scripts/bake_sd_profiles.py` 生成 20 款 `.cfg` 与 `PROFILES_ATTRIBUTION.txt`，并与 `02` 包二进制合并产出 `dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` 及 `.sha256`，不向 Git 源码库提交任何 `.cfg` 数据文件。

### 运行 6 项确定性安全与合规审计

```bash
python3 scripts/verify_m2_safety.py dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip
```

完整 6 项安全与协议合规门禁、跨机型（`EOSM.202`）冒烟编译及宿主机 `Allocs == Frees` 零泄漏测试结果见 [`docs/SAFETY_AUDIT_REPORT.md`](./docs/SAFETY_AUDIT_REPORT.md)。

---

## 外置胶片配置加载器与协议隔离架构（GPL-2.0 / CC BY-SA 4.0）

为在不向 GPL-2.0 固件树引入任何 GPL-3.0 代码的前提下支持第三方光谱胶片配置，本项目实现了严格的**协议防火墙 + SD 卡聚合（Aggregation）隔离架构**：

1. **全机型通用纯 GPL-2.0 净室固件端加载器（[`patches/03-mfilm-extprof-loader.patch`](./patches/03-mfilm-extprof-loader.patch)）**：
   - 在 `ML/modules/filmos.mo` 中新增独立编写的 `fos_extprof.c` / `fos_extprof.h`。
   - **全机型通用设计**：不含任何 `EOSM2` 专属宏、硬编码屏幕坐标或特定相机内存假设，全面调用 `fos_port_card()`、`fos_port_list()`、`fos_port_open()`/`read()`/`close()` 与 `fos_port_alloc()`/`free()` 抽象接口，兼容所有 M-Film 支持机型（`EOSM2.103`、`EOSM.202`、`6D.116` 等）。
   - 开机或进入选卷架/机内暗房时，自动扫描 SD 卡 `ML/MFILM/profiles/*.cfg` 纯文本参数化胶片配置文件，动态追加至 M-Film 选卷列表。
   - 在暗房显影时按需根据 `.cfg` 中的纯数值参数（`3×3` 线性色彩矩阵 + RGB 分通道广义 Logistic 色调曲线与反差参数 + `3×3` 显示输出矩阵）即时合成 `33×33×33` Cineon 3D LUT。
   - **开机静态内存零占用 & 零内存泄漏**：全部解析缓冲与预设数组均在 `filmos.mo` 运行期通过相机临时内存池（`fos_port_alloc` / `tmp_malloc`）按需申请并及时释放，`autoexec.bin` 开机静态内存保持 `537,344 / 605,952 bytes`（余量 `67.0 KB`）纹丝不动；宿主机全生命周期与 OOM 故障注入单元测试确认 `Allocs=39, Frees=39, LiveBytes=0`。
2. **宿主机端独立黑盒烘焙工具（[`scripts/bake_sd_profiles.py`](./scripts/bake_sd_profiles.py) 与 [`scripts/build_03_bundle.sh`](./scripts/build_03_bundle.sh)）**：
   - 将独立克隆的外部光谱模拟器（`andreavolpato/spektrafilm`）作为纯黑盒运行（关闭光晕、物理颗粒、眩光与自动曝光），输入 496 点合成测试图（24 色标准 ColorChecker + 6×6×6 RGB 色彩立方体 + 256 级对数灰阶斜坡）。
   - 使用 `scipy.optimize.least_squares` 拟合输出纯文本 `ML/MFILM/profiles/*.cfg`，并自动生成遵循 **CC BY-SA 4.0** 的 `PROFILES_ATTRIBUTION.txt` 与色差报告 [`docs/SPEKTRAFILM_BAKE_REPORT.md`](./docs/SPEKTRAFILM_BAKE_REPORT.md)（20 款胶片 24 色 ColorChecker 平均 ΔE2000 = `2.42`，全图 496 点平均 ΔE2000 = `1.93`）。
   - **本 GPL-2.0 源码仓库不混入任何受 CC BY-SA 4.0 约束的 `.cfg` 数据文件**；用户可直接从 GitHub Actions Artifacts 获取完整 `03` 包，或本地执行 `./scripts/build_03_bundle.sh` 一键生成。

---

## 开发方式与安全审计说明

本项目采用 **AI 辅助（Google Antigravity）+ 确定性静态审计 + GitHub Actions 全自动 CI** 的工程化流程完成跨代移植与集成：

- **硬件地址零编造原则**：所有底层固件偏移均直接继承自经过实机验证的 EOS M2（1.0.3）移植分支（`ccritix/magic-lantern`），严禁 AI 推算或修改任何硬件地址。`platform/EOSM2.103/` 中的全部 **135 条 `0xFF...` 固件函数地址**（`stubs.S`）、`ROMBASEADDR = 0xFF0C0000`、`RESTARTSTART = 0x44C100`、显存基址及 `BGMT_*` 按键事件码均保持 100% 原值，并由 [`scripts/verify_m2_safety.py`](./scripts/verify_m2_safety.py) 内置黄金 SHA256 摘要强校验锁定。
- **全自动 CI 与 6 项确定性门禁**：每次推送至 `main` 或发起 Pull Request 均自动触发 [`.github/workflows/build-and-audit.yml`](./.github/workflows/build-and-audit.yml)，完整执行三包构建、`EOSM.202` 跨机型 `filmos.mo` 冒烟编译（`FATAL_WARNINGS=y`）及 6 项确定性安全/协议门禁（启动内存 `< 592 KB`、零自动 Bootflag 写入、零 GPL-3.0 污染），任一项失败即阻断 CI，通过后自动归档 30 天可下载 Artifacts。
- **当前验证状态 — Hardware Verified (PASS)**：交叉编译、`EOSM.202` 跨机型冒烟编译、宿主机内存池零泄漏测试、全项 6 道静态安全及协议合规审计，以及 **Canon EOS M2（官方固件 `1.0.3`）真机三阶段全链路实测**（第一阶段纯净魔灯底座 + `ML/MODULES/EOSM2103.SYM`、第二阶段 M-Film 0.2.3 核心暗房、第三阶段 20 款外置 SpektraFilm `.cfg` 胶片加载与显影）均已 **PASS**。仍强烈推荐通过相机菜单的**“固件升级（Firmware Update）”**进行非持久化加载。

---

## 上游致谢（Credits）

本项目的实现离不开 Magic Lantern 与 M-Film 开源社区的长期贡献：

- **[`HNGSeries/mfilm-canon-film-simulation`](https://github.com/HNGSeries/mfilm-canon-film-simulation)** — M-Film (v0.2.3) 胶片模拟操作系统、盲拍防回放、低内存取景器 HUD、原厂图形屏蔽与机内 CR2 暗房引擎。
- **[`reticulatedpines/magiclantern_simplified`](https://github.com/reticulatedpines/magiclantern_simplified)** — 现代化 Magic Lantern 代码底座与构建系统。
- **Bilal / [`ccritix/magic-lantern`](https://github.com/ccritix/magic-lantern)** — 原始 Canon EOS M2（1.0.3）DryOS 固件端口、`stubs.S` 地址表、`consts.h` 显存常量及 `gui.h` 按键事件映射。
- **[`andreavolpato/spektrafilm`](https://github.com/andreavolpato/spektrafilm)** — 光谱胶片模拟参考模型与实测胶片/印相纸数据集（CC BY-SA 4.0），用于通过 `scripts/bake_sd_profiles.py` 离线烘焙外置 `.cfg` 配置文件。

---

## 开源协议

本仓库中的所有固件补丁、平台代码与构建脚本均遵循 **GNU General Public License v2.0（GPL-2.0）** 开源协议（全文见 [`LICENSE`](./LICENSE)），与 Magic Lantern 及 M-Film 保持完全兼容。通过 `scripts/bake_sd_profiles.py` 从 SpektraFilm 黑盒烘焙生成的外部 `.cfg` 数据文件属于独立的 CC BY-SA 4.0 数据资产，仅以 SD 卡聚合（Aggregation）方式分发，不纳入本 GPL-2.0 源码提交。

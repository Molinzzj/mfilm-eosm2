# M-Film for Canon EOS M2（官方固件 1.0.3）

[English Documentation (README.md)](./README.md)

为 **Canon EOS M2**（DIGIC 5 / ARM946E-S，官方固件 **1.0.3**）移植现代 **Magic Lantern**（基于 [`reticulatedpines/magiclantern_simplified`](https://github.com/reticulatedpines/magiclantern_simplified)），并完整集成 **M-Film v0.2.3**（[`HNGSeries/mfilm-canon-film-simulation`](https://github.com/HNGSeries/mfilm-canon-film-simulation)）胶片模拟与机内暗房系统。

---

## ⚠️ 安全警告 — 使用前请务必阅读

> [!CAUTION]
> - **仅支持官方固件 1.0.3**：本项目严格锁定 **Canon EOS M2 官方固件 `1.0.3`**（`EOSM2.103`）。使用前请先在相机菜单确认 `固件版本 / Firmware Ver. 1.0.3`，**切勿**在其他机型或固件版本上运行。
> - **强烈推荐非持久化加载**：请通过相机原厂菜单 **扳手设置 → 固件版本 1.0.3 → 固件升级（Firmware Update）** 进行安全非持久化加载。在早期测试验证完成前，**请勿**写入或开启相机 NVRAM Bootflag（开机自启）。
> - **零自动 Bootflag 写入**：本项目全部构建均经过 `scripts/verify_m2_safety.py` 静态与二进制门禁审计，确认无任何自动 `EnableBootDisk` / `SetBootFlag` 调用，且 100% 保留经实机验证的 `EOSM2.103` 硬件地址表。
> - **自刷风险提示**：运行第三方相机固件存在固有风险，请自担风险。在非持久化加载模式下，若遇到黑屏或卡死，**直接抠出电池静置 5 秒后装回**即可 100% 恢复佳能原厂系统。

---

## 核心特性

- **现代魔灯底座（`EOSM2.103`）**：将经典 EOS M2 1.0.3 DryOS 端口迁移至 `magiclantern_simplified`，100% 原样保留全部 144 个有效 `NSTUB` 固件地址、显存基址及 `BGMT_*` 按键码。
- **M-Film v0.2.3 外挂模块模式（`--module`）**：将 Film OS 与机内 CR2→JPEG 暗房编译为外挂模块 `ML/modules/filmos.mo`，严格控制在 DIGIC 5 固定 592 KB（`605,952 B`）开机内存红线内（实际占用 `537,344 B`，剩余 `67.0 KB` 安全余量）。
- **无反低内存 HUD 与原厂图形屏蔽**：完整继承 EOS M 无反优化 — 跳过单反顶屏代码、采用低开机内存取景器 HUD 直接绘制，并支持 **`Settings → Advanced → Hide Canon's graphics`** 一键屏蔽佳能原厂曝光标尺与图标。
- **两步验证成品包**：
  - `01_EOSM2_Clean_ML_Base.zip`：纯净魔灯底座，用于先行验证开机、菜单与按键响应。
  - `02_EOSM2_MFilm_023_TestBuild.zip`：完整 M-Film v0.2.3 测试包（含机内暗房 LUT、字体与胶片样片）。

---

## 快速上手指南（4 步完成）

1. **确认固件并准备 SD 卡**：确认 EOS M2 为官方固件 **1.0.3**，使用满电电池与 **≤ 32 GB 的 FAT32 格式 SD 卡**（建议先在相机内格式化一次）。
2. **下载成品压缩包**：前往 [GitHub Releases](https://github.com/Molinzzj/mfilm-eosm2/releases) 下载 `01_EOSM2_Clean_ML_Base.zip`（建议首次先测底座）及 `02_EOSM2_MFilm_023_TestBuild.zip`，并核对 `.sha256` 校验值。
3. **解压至 SD 卡根目录**：将压缩包**直接解压至 SD 卡根目录**，确保根目录直接出现 `autoexec.bin`、`ML-SETUP.FIR` 与 `ML/` 文件夹（切勿多套一层子目录）。
4. **通过固件升级安全加载**：插卡开机，将拍摄模式拨盘调至 **M / Av / Tv** 静态照片档，在佳能菜单中将画质设为 **RAW**（机内暗房必需），进入 **固件版本 1.0.3 → 固件升级** 执行非持久化加载。进入实时取景后按 **垃圾桶 / 删除键**（或长按向下键）即可呼出 Magic Lantern / M-Film。

详细的两步实机测试检查清单请参阅 [`docs/REAL_CAMERA_SMOKE_TEST.md`](./docs/REAL_CAMERA_SMOKE_TEST.md)。

---

## 仓库目录结构

```text
.
├── platform/EOSM2.103/              # 审计通过的 EOS M2 (1.0.3) 平台源码目录
├── patches/
│   ├── 01-ml-simplified-eosm2.patch # 针对 magiclantern_simplified 的最小化补丁
│   └── 02-mfilm-eosm2.patch         # 针对 M-Film v0.2.3 的最小化补丁
├── scripts/
│   ├── build_all.sh                 # 自动拉取上游特定 Commit、打补丁并一键编译脚本
│   └── verify_m2_safety.py          # 5 项强制硬件地址与零 Bootflag 安全审计脚本
├── docs/
│   ├── REAL_CAMERA_SMOKE_TEST.md    # 两步实机安全冒烟测试指南
│   └── SAFETY_AUDIT_REPORT.md       # 自动化安全审计报告（PASS）
├── LICENSE                          # GNU General Public License v2.0 协议全文
├── README.md                        # 英文主说明文档
└── README_CN.md                     # 中文说明文档
```

---

## 从源码构建指南

### 构建依赖

- **ARM 交叉编译器**：`arm-none-eabi-gcc`（已验证版本：xPack GNU Arm Embedded GCC `12.3.1-1.2`）
- **宿主机工具**：`gcc`、`make`、`git`、`python3`、`zip`、`unzip`
- **Python 3 依赖**：`docutils`、`setuptools`、`numpy`、`segno`

### 一键复现构建

```bash
git clone https://github.com/Molinzzj/mfilm-eosm2.git
cd mfilm-eosm2
./scripts/build_all.sh
```

`scripts/build_all.sh` 会自动完成以下步骤：
1. 拉取官方上游 `reticulatedpines/magiclantern_simplified`（锁定 Commit `142472e9`）与 `HNGSeries/mfilm-canon-film-simulation`（锁定 Commit `3c3986dd`，v0.2.3）。
2. 复制 `platform/EOSM2.103/` 并应用 `patches/01-ml-simplified-eosm2.patch`。
3. 编译输出纯净魔灯底座 `dist/01_EOSM2_Clean_ML_Base.zip`。
4. 应用 `patches/02-mfilm-eosm2.patch` 并执行 M-Film `build_fork.sh EOSM2.103 --module`。
5. 打包输出 `dist/02_EOSM2_MFilm_023_TestBuild.zip` 并生成 `.sha256` 校验文件。

### 运行静态与二进制安全审计

```bash
python3 scripts/verify_m2_safety.py dist/02_EOSM2_MFilm_023_TestBuild.zip
```

完整 6 项安全与协议合规门禁审计结果见 [`docs/SAFETY_AUDIT_REPORT.md`](./docs/SAFETY_AUDIT_REPORT.md)。

---

## 外置胶片配置加载器与协议隔离架构（GPL-2.0 / CC BY-SA 4.0）

为在不向 GPL-2.0 固件树引入任何 GPL-3.0 代码的前提下支持第三方光谱胶片配置，本项目实现了严格的**协议防火墙 + SD 卡聚合（Aggregation）隔离架构**：

1. **纯 GPL-2.0 净室固件端加载器（[`patches/03-mfilm-extprof-loader.patch`](./patches/03-mfilm-extprof-loader.patch)）**：
   - 在 `ML/modules/filmos.mo` 中新增独立编写的 `fos_extprof.c` / `fos_extprof.h`。
   - 开机或进入选卷架/机内暗房时，自动扫描 SD 卡 `ML/MFILM/profiles/*.cfg` 纯文本参数化胶片配置文件，动态追加至 M-Film 选卷列表。
   - 在暗房显影时按需根据 `.cfg` 中的纯数值参数（`3×3` 线性色彩矩阵 + RGB 分通道广义 Logistic 色调曲线与反差参数 + `3×3` 显示输出矩阵）即时合成 `33×33×33` Cineon 3D LUT。
   - **开机静态内存零占用**：全部解析缓冲与预设数组均在 `filmos.mo` 运行期通过相机临时内存池（`fos_port_alloc` / `tmp_malloc`）按需申请并及时释放，`autoexec.bin` 开机静态内存保持 `537,344 / 605,952 bytes`（余量 `67.0 KB`）纹丝不动。
2. **宿主机端独立黑盒烘焙工具（[`scripts/bake_sd_profiles.py`](./scripts/bake_sd_profiles.py)）**：
   - 将独立克隆的外部光谱模拟器（如 `andreavolpato/spektrafilm`）作为纯黑盒运行（关闭光晕、物理颗粒、眩光与自动曝光），输入 496 点合成测试图（24 色标准 ColorChecker + 6×6×6 RGB 色彩立方体 + 256 级对数灰阶斜坡）。
   - 使用 `scipy.optimize.least_squares` 拟合输出纯文本 `ML/MFILM/profiles/*.cfg`，并自动生成遵循 **CC BY-SA 4.0** 的 `PROFILES_ATTRIBUTION.txt` 与色差报告 [`docs/SPEKTRAFILM_BAKE_REPORT.md`](./docs/SPEKTRAFILM_BAKE_REPORT.md)（20 款胶片 24 色 ColorChecker 平均 ΔE2000 = `2.42`，全图 496 点平均 ΔE2000 = `1.93`）。
   - **本 GPL-2.0 源码仓库不混入任何受 CC BY-SA 4.0 约束的 `.cfg` 数据文件**；用户可自行运行 `scripts/bake_sd_profiles.py` 生成后拷贝至 SD 卡 `ML/MFILM/profiles/` 目录即可生效。

---

## 开发方式与安全审计说明

本项目采用 **AI 辅助（Google Antigravity）+ 确定性静态审计** 的工程化流程完成跨代移植与集成：

- **硬件地址零编造原则**：所有底层固件偏移均直接继承自经过实机验证的 EOS M2（1.0.3）移植分支（`ccritix/magic-lantern`），严禁 AI 推算或修改任何硬件地址。`platform/EOSM2.103/` 中的全部 **135 条 `0xFF...` 固件函数地址**（`stubs.S`）、`ROMBASEADDR = 0xFF0C0000`、`RESTARTSTART = 0x44C100`、显存基址及 `BGMT_*` 按键事件码均保持 100% 原值。
- **确定性 6 项 Python 安全与合规门禁**：每次构建打包前均强制运行 [`scripts/verify_m2_safety.py`](scripts/verify_m2_safety.py)，机械核验地址表一致性、DIGIC 5 启动内存余量（严格低于 `592 KB` 上限）、**零自动改写相机 NVRAM Bootflag 调用**以及**零 GPL-3.0 / 第三方源码污染**。
- **当前验证状态**：交叉编译与全项 6 道静态安全及协议合规审计均已通过（当前处于 `Pre-release` 阶段）。在完成 EOS M2（1.0.3）真机冒烟测试前，请务必仅通过相机菜单的**“固件升级（Firmware Update）”**进行非持久化加载。

---

## 上游致谢（Credits）

本项目的实现离不开 Magic Lantern 与 M-Film 开源社区的长期贡献：

- **[`HNGSeries/mfilm-canon-film-simulation`](https://github.com/HNGSeries/mfilm-canon-film-simulation)** — M-Film (v0.2.3) 胶片模拟操作系统、盲拍防回放、低内存取景器 HUD、原厂图形屏蔽与机内 CR2 暗房引擎。
- **[`reticulatedpines/magiclantern_simplified`](https://github.com/reticulatedpines/magiclantern_simplified)** — 现代化 Magic Lantern 代码底座与构建系统。
- **Bilal / [`ccritix/magic-lantern`](https://github.com/ccritix/magic-lantern)** — 原始 Canon EOS M2（1.0.3）DryOS 固件端口、`stubs.S` 地址表、`consts.h` 显存常量及 `gui.h` 按键事件映射。

---

## 开源协议

本仓库中的所有固件补丁、平台代码与构建脚本均遵循 **GNU General Public License v2.0（GPL-2.0）** 开源协议（全文见 [`LICENSE`](./LICENSE)），与 Magic Lantern 及 M-Film 保持完全兼容。通过 `scripts/bake_sd_profiles.py` 从 SpektraFilm 黑盒烘焙生成的外部 `.cfg` 数据文件属于独立的 CC BY-SA 4.0 数据资产，仅以 SD 卡聚合（Aggregation）方式分发，不纳入本 GPL-2.0 源码提交。


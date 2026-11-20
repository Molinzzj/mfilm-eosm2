# SpektraFilm 离线黑盒烘焙与色差（ΔE2000）评估报告

## 一、 协议隔离与烘焙方法概述

- **协议防火墙架构**：
  - 宿主机离线脚本 `scripts/bake_sd_profiles.py`（由非交互打包脚本 `scripts/build_03_bundle.sh` 或 GitHub Actions CI 自动调用）将 `andreavolpato/spektrafilm` 克隆于仓库外的独立临时目录（`mktemp -d`，打包后自动清理），严格作为外部黑盒模拟器运行，**零源码/头文件/数据数组拷贝至 GPL-2.0 固件树**。
  - 输出的纯文本数值配置文件（`ML/MFILM/profiles/*.cfg`）随附 `PROFILES_ATTRIBUTION.txt`，规范遵循 **CC BY-SA 4.0** 署名共享协议，在 SD 卡上与 GPL-2.0 固件二进制（`autoexec.bin` / `ML/modules/filmos.mo`）构成合规的 **Aggregation（聚合）** 隔离。
- **一键复现命令与 CI 产物**：
  - 本地复现：先执行 `./scripts/build_all.sh` 构建 `01`/`02` 包，再执行 `./scripts/build_03_bundle.sh` 自动拉取 SpektraFilm、烘焙全部 20 款 `.cfg` 并组装 `dist/03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` 及 `.sha256`。
  - 云端自动构建：GitHub Actions 工作流 `.github/workflows/build-and-audit.yml` 会在每次推送至 `main` 或手动触发时自动产出并上传 `dist/*.zip`、`dist/*.sha256`、`docs/SAFETY_AUDIT_REPORT.md` 与本报告（Artifacts 保留 30 天）。
- **黑盒采样配置**：
  - 关闭光晕（`halation.active = False`）、物理颗粒（`grain.active = False`）、镜头/印相眩光（`glare.active = False`）、DIR 空间扩散与自动曝光（`auto_exposure = False`），输入标准线性 sRGB（`0.18 = 18%` 中灰），输出显示 sRGB。
  - 合成采样测试图包含：**24 色标准 ColorChecker** + **6×6×6（216 点）RGB 色彩立方体** + **256 级对数灰阶斜坡**（`-7.0` 至 `+3.5` EV），共 `496` 个采样点。
- **参数化拟合模型（36 自由度，与 `fos_extprof.c` 逐比特一致）**：
  - 线性场景 `3×3` 色彩矩阵 + RGB 分通道广义 Logistic 色调曲线（反差 `contrast`、中灰支点 `pivot`、黑场 `black`、白场 `white`、非对称指数 `gamma`）+ 显示空间 `3×3` 输出矩阵与偏置，经 `scipy.optimize.least_squares`（TRF + Soft-L1 鲁棒损失）拟合。

## 二、 汇总指标

- **烘焙胶片总数**：`20` 款（覆盖 Kodak Pro/Consumer/Cine、Fujifilm C-41 及 E-6/K-14 反转片）
- **24 色 ColorChecker 平均色差（ΔE2000）**：**`2.42`**
- **24 色 ColorChecker 单色块最大色差（ΔE2000）**：`7.66`
- **全图 496 采样点（含 6×6×6 色彩立方体与 256 级灰阶）平均色差（ΔE2000）**：**`1.93`**
- **离线烘焙总耗时**：`29.9 s`

## 三、 逐胶片拟合精度明细表

| # | 胶片名称 | 配置文件 | 工艺 / ISO | 印相纸配对 | ColorChecker 平均 ΔE00 | ColorChecker 最大 ΔE00 | 全图 496 点平均 ΔE00 |
| :-: | :--- | :--- | :--- | :--- | :-: | :-: | :-: |
| 01 | Ektar 100 (SF) | `kodak_ektar_100.cfg` | C-41 / ISO 100 | `kodak_portra_endura` | **2.46** | 5.75 | 1.99 |
| 02 | Portra 160 (SF) | `kodak_portra_160.cfg` | C-41 / ISO 160 | `kodak_portra_endura` | **2.21** | 4.78 | 1.87 |
| 03 | Portra 400 (SF) | `kodak_portra_400.cfg` | C-41 / ISO 400 | `kodak_portra_endura` | **2.31** | 4.71 | 1.85 |
| 04 | Portra 800 (SF) | `kodak_portra_800.cfg` | C-41 / ISO 800 | `kodak_portra_endura` | **2.19** | 4.23 | 1.70 |
| 05 | Portra 800+1 (SF) | `kodak_portra_800_push1.cfg` | C-41 / ISO 1600 | `kodak_portra_endura` | **2.62** | 5.68 | 2.13 |
| 06 | Portra 800+2 (SF) | `kodak_portra_800_push2.cfg` | C-41 / ISO 3200 | `kodak_portra_endura` | **3.05** | 7.66 | 2.47 |
| 07 | Gold 200 (SF) | `kodak_gold_200.cfg` | C-41 / ISO 200 | `kodak_endura_premier` | **2.49** | 5.68 | 2.06 |
| 08 | UltraMax 400 (SF) | `kodak_ultramax_400.cfg` | C-41 / ISO 400 | `kodak_endura_premier` | **2.48** | 5.71 | 2.07 |
| 09 | Vision3 50D (SF) | `kodak_vision3_50d.cfg` | ECN-2 / ISO 50 | `kodak_2383` | **2.50** | 5.88 | 1.93 |
| 10 | Vision3 250D (SF) | `kodak_vision3_250d.cfg` | ECN-2 / ISO 250 | `kodak_2383` | **2.49** | 6.14 | 1.96 |
| 11 | Verita 200D (SF) | `kodak_verita_200d.cfg` | ECN-2 / ISO 200 | `kodak_2383` | **2.57** | 6.57 | 1.95 |
| 12 | Vision3 200T (SF) | `kodak_vision3_200t.cfg` | ECN-2 / ISO 200 | `kodak_2383` | **2.52** | 5.80 | 1.92 |
| 13 | Vision3 500T (SF) | `kodak_vision3_500t.cfg` | ECN-2 / ISO 500 | `kodak_2383` | **2.43** | 5.50 | 1.95 |
| 14 | Pro 400H (SF) | `fujifilm_pro_400h.cfg` | C-41 / ISO 400 | `fujifilm_crystal_archive_typeii` | **2.25** | 4.36 | 1.73 |
| 15 | Fujicolor C200 (SF) | `fujifilm_c200.cfg` | C-41 / ISO 200 | `fujifilm_crystal_archive_typeii` | **2.40** | 5.42 | 1.85 |
| 16 | Superia X-TRA (SF) | `fujifilm_xtra_400.cfg` | C-41 / ISO 400 | `fujifilm_crystal_archive_typeii` | **2.38** | 5.78 | 1.98 |
| 17 | Ektachrome 100 (SF) | `kodak_ektachrome_100.cfg` | E-6 / ISO 100 | `反转正片 (直出)` | **2.07** | 4.64 | 1.65 |
| 18 | Kodachrome 64 (SF) | `kodak_kodachrome_64.cfg` | K-14 / ISO 64 | `反转正片 (直出)` | **2.25** | 3.56 | 1.78 |
| 19 | Velvia 100 (SF) | `fujifilm_velvia_100.cfg` | E-6 / ISO 100 | `反转正片 (直出)` | **2.50** | 5.62 | 1.93 |
| 20 | Provia 100F (SF) | `fujifilm_provia_100f.cfg` | E-6 / ISO 100 | `反转正片 (直出)` | **2.27** | 4.94 | 1.82 |

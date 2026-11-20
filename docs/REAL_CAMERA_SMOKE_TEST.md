# REAL_CAMERA_SMOKE_TEST.md — Canon EOS M2 (1.0.3) 实机三阶段安全冒烟测试报告与指南

> **实机验证总状态**：**`Hardware Verified (PASS)`**
> - **验证机型**：Canon EOS M2（DIGIC 5 / ARM946E-S，官方固件 **`1.0.3`**）
> - **验证结果**：第一阶段（纯净魔灯底座）、第二阶段（M-Film 0.2.3 核心暗房）与第三阶段（20 款外置 SpektraFilm `.cfg` 胶片加载与显影）**全部真机实测通过（PASS）**。
> - **菜单呼出方式**：实时取景（LiveView）下**长按删除键（Trash）**；模块符号表严格采用 DryOS FAT32 8.3 规范的 **`ML/MODULES/EOSM2103.SYM`**。

> [!CAUTION]
> **🔴 重要固件红线警告 — 仅支持官方固件 `1.0.3`，严禁升级至 `1.0.4`！**
> - 本项目严格锁定且仅适用于官方固件版本为 **`1.0.3`** 的 **Canon EOS M2**（开机进入原厂菜单检查 `固件版本 / Firmware Ver. 1.0.3`）。
> - 当前为 **`1.0.1`** 或 **`1.0.2`** 的用户，可从佳能官网下载官方 **`1.0.3`** 升级包安全升级后再使用。
> - **严禁升级至佳能官网最新的 `1.0.4` 安全补丁版固件！`1.0.4` 无法降级且完全不支持 Magic Lantern / M-Film！**
> - 本次全部发布包均支持**非持久化固件升级加载**，**切勿**在未充分了解风险前自动或手动刷写相机 NVRAM Bootflag。若遇到黑屏或卡死，**直接抠出电池静置 5 秒再装回**即可 100% 恢复佳能原厂系统。
> - 建议使用 **满电电池** 与 **≤ 32 GB 的 FAT32 格式 SD 卡**（在相机内格式化一次后，再插到电脑拷贝文件）。
> - **产物获取方式**：可从 [GitHub Releases (`v1.0.0`)](https://github.com/Molinzzj/mfilm-eosm2/releases) 下载正式发布包，也可前往本仓库 [GitHub Actions (`Build & Safety Audit`)](https://github.com/Molinzzj/mfilm-eosm2/actions/workflows/build-and-audit.yml) 的最新绿灯运行记录中下载 **Artifacts（`eos-m2-mfilm-bundles-and-reports`，保留 30 天）**，或本地依次运行 `./scripts/build_all.sh` 与 `./scripts/build_03_bundle.sh` 复现构建。

---

## 第一阶段：验证纯净魔灯底座（`01_EOSM2_Clean_ML_Base.zip`）— `Hardware Verified (PASS)`

**目的**：先独立确认 `EOSM2.103` 的硬件地址、显存映射、按键事件码、DryOS 8.3 符号表 `ML/MODULES/EOSM2103.SYM` 与 592 KB 开机内存预留完全健康，排除底座问题。

1. **校验与解压**：
   - 使用随包 `.sha256` 文件核对 `01_EOSM2_Clean_ML_Base.zip` 完整性（`v1.0.0` 发布包 SHA256：`fc694b0170642606ad1dfe291e4a7f695b9e2b9286782a7766cc982f59a6a91d`）。
   - 将压缩包**直接解压至 FAT32 SD 卡根目录**（确保根目录直接出现 `autoexec.bin`、`ML-SETUP.FIR` 与 `ML/MODULES/EOSM2103.SYM`，不要多套一层子目录）。
2. **固件升级非持久化加载**：
   - 插卡开机，将拍摄模式拨盘调至 **M / Av / Tv 静态照片模式**（不要在录像档）。
   - 进入佳能原厂菜单 → 扳手设置页 → **固件版本（Firmware Ver. 1.0.3）** → 确认执行 **固件升级（Firmware Update）**。
   - 若加载 `ML-SETUP.FIR` 时提示引导选项，请按非持久化测试方式仅引导 `autoexec.bin`（**切勿**在未确认安全前启用开机自动启动 / Bootflag）。
3. **通过标准（实机全部 PASS）**：
   - [x] 读卡灯不出现 **3 长 3 短循环闪烁**，屏幕正常亮屏进入实时取景（LiveView），且控制台无任何 `.sym` 缺失报错（`ML/MODULES/EOSM2103.SYM` 正常加载）。
   - [x] 在实时取景下**长按删除键（Trash）**呼出 Magic Lantern 菜单，菜单文字清晰、无花屏错位，顶部标签页正常包含 **`Modules`** 标签页。
   - [x] 上/下/左/右/SET/MENU/PLAY 按键响应准确，无错键或卡死。
   - [x] 进入 `Debug -> Free Memory` 确认剩余内存正常，随后正常关机。

---

## 第二阶段：验证 M-Film 0.2.3 胶片系统（`02_EOSM2_MFilm_023_TestBuild.zip`）— `Hardware Verified (PASS)`

**目的**：在底座验证通过后，验证外挂模块 `ML/MODULES/filmos.mo` 依托 `ML/MODULES/EOSM2103.SYM` 的自动加载、选卷、盲拍防回放、隐藏原厂图形与机内暗房 CR2→JPEG 显影全链路。

1. **清空 SD 卡并解压 M-Film 发布包**：
   - 使用随包 `.sha256` 文件核对 `02_EOSM2_MFilm_023_TestBuild.zip`（`v1.0.0` 发布包 SHA256：`8a71290de209388694b9e96f216b623d60aeff82a346c92e59c4898cf7da0b22`）。
   - 删除卡上旧的 `autoexec.bin` 与 `ML/` 目录，将 `02_EOSM2_MFilm_023_TestBuild.zip` 直接解压至 SD 卡根目录。
   - 确认根目录存在 `autoexec.bin`、`ML-SETUP.FIR`、`ML/MODULES/filmos.mo`、`ML/MODULES/EOSM2103.SYM`、`ML/SETTINGS/filmos.en`、`ML/data/FOSFONT.BIN`、`ML/data/FOSFILMS.BIN`、`ML/DARKROOM/` 与 `ML/SAMPLES/`。
2. **将相机画质设为 RAW**：
   - 开机后先在佳能原厂菜单中将图像画质设为 **RAW**（机内暗房依赖 `.CR2` 文件显影）。
   - 同第一阶段方式通过 **固件升级（Firmware Update）** 加载 M-Film。
3. **四项核心功能逐项冒烟（实机全部 PASS）**：
   - **① 选卷装片（Film Shelf）**：
     - [x] 进入实时取景后**长按删除键（Trash）**呼出菜单，自动进入 **M-Film 胶片主界面**。
     - [x] 浏览胶片架（可按 PLAY 预览样片），任选一卷内置胶片（如 Kodak Portra 400 / Gold 200）并装卷（Load Roll）。
   - **② 盲拍与防回放（Blind Shooting）**：
     - [x] 回到取景器界面，M-Film 取景器 HUD（剩余张数、测光、胶片型号）正常直接绘制在屏幕上。
     - [x] 拍摄测试照片，计数正常递增；按 **PLAY（回放键）** 确认盲拍锁生效、无法直接回看未冲洗照片。
   - **③ 原厂图形屏蔽（Hide Canon's graphics）**：
     - [x] 进入 M-Film `Settings -> Advanced -> Hide Canon's graphics` 并开启。
     - [x] 返回取景器，佳能原厂曝光标尺与图标成功屏蔽、不再穿透覆盖 M-Film HUD（关闭后恢复正常）。
   - **④ 机内暗房显影（In-Camera Darkroom）**：
     - [x] 在 M-Film 中提前退卷 / 结束当前卷（Rewind / Finish Roll），进入 **Darkroom（暗房）**。
     - [x] 选择输出尺寸对拍摄的 CR2 执行显影。
     - [x] 进度条平滑推进直至生成 JPEG，无死机、无 OOM 报错。

---

## 第三阶段：验证外置胶片配置加载器与 20 款 `(SF)` 胶卷（`03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`）— `Hardware Verified (PASS)`

**目的**：在第二阶段确认 M-Film 主体稳定后，验证纯 GPL-2.0 外置配置加载器（`fos_extprof`）从 SD 卡动态扫描、加载 20 款离线烘焙的 SpektraFilm `(SF)` 参数化胶片，以及机内即时合成 `33×33×33` Cineon 3D LUT 显影的稳定性与内存安全性。

1. **校验、解压并核对 SD 卡目录结构**：
   - 使用随包 `.sha256` 文件核对 `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`（`v1.0.0` 发布包 SHA256：`72d0c895f2ce05dfb4ca4646021551d095929377b1f6fbeafb2fb50e16fee9a4`）。
   - 清空 SD 卡上旧的 `autoexec.bin` 与 `ML/` 目录，将 `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` 直接解压至 SD 卡根目录。
   - **关键目录核查**：打开 SD 卡中的 `ML/MFILM/profiles/` 目录，确认以下文件完整存在：
     - [x] 共 **20 个 `.cfg` 胶片配置文件**（如 `kodak_portra_400.cfg`、`kodak_ektar_100.cfg`、`kodak_vision3_500t.cfg`、`fujifilm_pro_400h.cfg`、`fujifilm_velvia_100.cfg`、`kodak_kodachrome_64.cfg` 等）。
     - [x] 存在 **`PROFILES_ATTRIBUTION.txt`**（CC BY-SA 4.0 协议署名说明）。
2. **通过固件升级加载并检查选卷架动态追加（实机全部 PASS）**：
   - 保持画质为 **RAW**，按第一阶段方式通过 **固件升级（Firmware Update）** 执行非持久化加载。
   - 进入实时取景后**长按删除键（Trash）**呼出 M-Film 选卷架（Film Shelf），在各个分组（Colour / Slide / Cine）向后翻页：
     - [x] 选卷架末尾动态出现全部 20 款带 **`(SF)`** 后缀的外置胶卷（如 `Portra 400 (SF)`、`Ektar 100 (SF)`、`Vision3 500T (SF)`、`Pro 400H (SF)`、`Velvia 100 (SF)` 等），罐体标签颜色、品牌文字与 ISO 标识显示正常、无乱码。
     - [x] `ML/FILMROLL.LOG` 确认正常加载 `ML/MFILM/profiles` 外置胶片列表。
3. **连续切卷稳定性测试（实机全部 PASS）**：
   - [x] 在选卷架中快速连续左右切换不同内置与 `(SF)` 外置胶卷（跨 Colour / Slide / Cine 分组），界面刷新流畅、无卡顿、无花屏、无死机。
   - [x] 选用 `(SF)` 胶卷执行装卷（Load Roll）并拍摄 RAW 照片，HUD 显示的胶卷名称、ISO 与计数正常。
4. **暗房即时 3D LUT 显影验证（实机全部 PASS）**：
   - [x] 提前退卷 / 结束当前卷（Rewind / Finish Roll），进入 **Darkroom（暗房）**。
   - [x] 对使用 `(SF)` 胶卷拍摄的 `.CR2` 执行机内显影。
   - [x] `fos_extprof_build_lut()` 在相机临时内存池中即时合成 `33×33×33` Cineon 3D LUT 并平滑完成显影输出 JPEG，色彩风格符合所选 `(SF)` 胶卷特征，全过程无死机、无 OOM 报错。
   - [x] 换装另一款 `(SF)` 胶卷继续拍摄与显影，二次切卷即时重算 LUT 稳定无泄漏。

---

## 四、 异常排查与日志收集

- **卡死 / 黑屏**：直接拔电池 5 秒后装回即可恢复原厂固件，无任何持久化损伤。
- **未看到 `(SF)` 胶卷**：请核对 SD 卡目录路径是否严格为 `ML/MFILM/profiles/*.cfg`（注意大小写与不要多嵌套一层目录），并检查 `ML/FILMROLL.LOG` 中的 `extprof:` 日志。
- **问题反馈日志**：请保留 SD 卡上的 `ML/FILMROLL.LOG` 与 `ML/LOGS/` 下的最新日志文件，连同复现步骤一并提交至 GitHub Issues 即可精准定位。

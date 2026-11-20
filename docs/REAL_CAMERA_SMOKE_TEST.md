# REAL_CAMERA_SMOKE_TEST.md — Canon EOS M2 (1.0.3) 实机三阶段安全冒烟测试指南

> **安全铁律提醒**：
> - 仅适用于官方固件版本为 **1.0.3** 的 **Canon EOS M2**（开机进入原厂菜单检查 `固件版本 / Firmware Ver. 1.0.3`）。
> - 本次全部测试产物均为**非持久化加载验证包**，**严禁**在首次测试中自动或手动刷写相机 NVRAM Bootflag。若遇到黑屏或卡死，**直接抠出电池静置 5 秒再装回**即可 100% 恢复佳能原厂系统。
> - 建议使用 **满电电池** 与 **≤ 32 GB 的 FAT32 格式 SD 卡**（在相机内格式化一次后，再插到电脑拷贝文件）。
> - **产物获取方式**：可从 [GitHub Releases](https://github.com/Molinzzj/mfilm-eosm2/releases) 下载发布包，也可直接前往本仓库 [GitHub Actions (`Build & Safety Audit`)](https://github.com/Molinzzj/mfilm-eosm2/actions/workflows/build-and-audit.yml) 的最新绿灯运行记录中下载 **Artifacts（`eos-m2-mfilm-bundles-and-reports`，保留 30 天）**，或本地依次运行 `./scripts/build_all.sh` 与 `./scripts/build_03_bundle.sh` 复现构建。

---

## 第一阶段：验证纯净魔灯底座（`01_EOSM2_Clean_ML_Base.zip`）

**目的**：先独立确认 `EOSM2.103` 的硬件地址、显存映射、按键事件码与 592 KB 开机内存预留完全健康，排除底座问题。

1. **校验与解压**：
   - 使用随包 `.sha256` 文件核对 `01_EOSM2_Clean_ML_Base.zip` 完整性（本次本地验证 SHA256：`9f32c5ad70b62f9b7f00333b76c174c520ff552ba85cc21c7bf2f001538633f2`；若使用 CI Artifacts 请以对应运行产出的 `.sha256` 为准）。
   - 将压缩包**直接解压至 FAT32 SD 卡根目录**（确保根目录直接出现 `autoexec.bin`、`ML-SETUP.FIR` 与 `ML/` 文件夹，不要多套一层子目录）。
2. **固件升级非持久化加载**：
   - 插卡开机，将拍摄模式拨盘调至 **M / Av / Tv 静态照片模式**（不要在录像档）。
   - 进入佳能原厂菜单 → 扳手设置页 → **固件版本（Firmware Ver. 1.0.3）** → 确认执行 **固件升级（Firmware Update）**。
   - 若加载 `ML-SETUP.FIR` 时提示引导选项，请按非持久化测试方式仅引导 `autoexec.bin`（**切勿**在未确认安全前启用开机自动启动 / Bootflag）。
3. **通过标准（Pass Criteria）**：
   - [ ] 读卡灯不出现 **3 长 3 短循环闪烁**，屏幕正常亮屏进入实时取景（LiveView）。
   - [ ] 按机身 **垃圾桶 / 删除键（Delete / Trash）**（或长按向下键 / 双指触摸）呼出 Magic Lantern 菜单，菜单文字清晰、无花屏错位。
   - [ ] 上/下/左/右/SET/MENU/PLAY 按键响应准确，无错键或卡死。
   - [ ] 进入 `Debug -> Free Memory` 确认剩余内存正常，随后正常关机。

---

## 第二阶段：验证 M-Film 0.2.3 胶片系统（`02_EOSM2_MFilm_023_TestBuild.zip`）

**目的**：在底座验证通过后，验证外挂模块 `ML/modules/filmos.mo` 的加载、选卷、盲拍防回放、隐藏原厂图形与单张机内暗房 CR2→JPEG 显影全链路。

1. **清空 SD 卡并解压 M-Film 测试包**：
   - 使用随包 `.sha256` 文件核对 `02_EOSM2_MFilm_023_TestBuild.zip`（本次本地验证 SHA256：`fa5646dd91a918b77e1cadaf9ea53f2bed37141723234e3d96053807a38f3ef8`）。
   - 删除卡上旧的 `autoexec.bin` 与 `ML/` 目录，将 `02_EOSM2_MFilm_023_TestBuild.zip` 直接解压至 SD 卡根目录。
   - 确认根目录存在 `autoexec.bin`、`ML-SETUP.FIR`、`ML/modules/filmos.mo`、`ML/modules/EOSM2_103.sym`、`ML/SETTINGS/filmos.en`、`ML/data/FOSFONT.BIN`、`ML/data/FOSFILMS.BIN`、`ML/DARKROOM/` 与 `ML/SAMPLES/`。
2. **将相机画质设为 RAW**：
   - 开机后先在佳能原厂菜单中将图像画质设为 **RAW**（机内暗房依赖 `.CR2` 文件显影）。
   - 同第一阶段方式通过 **固件升级（Firmware Update）** 加载 M-Film。
3. **四项核心功能逐项冒烟**：
   - **① 选卷装片（Film Shelf）**：
     - [ ] 进入实时取景后按 Magic Lantern 菜单键，确认自动进入 **M-Film 胶片主界面**（而非原版 ML 菜单；若进入原版 ML 菜单，请到 `Modules` 标签查看 `filmos.mo` 加载日志）。
     - [ ] 浏览胶片架（可按 PLAY 预览样片），任选一卷内置胶片（如 Kodak Portra 400 / Gold 200）并装卷（Load Roll）。
   - **② 盲拍与防回放（Blind Shooting）**：
     - [ ] 回到取景器界面，确认 M-Film 取景器 HUD（剩余张数、测光、胶片型号）正常直接绘制在屏幕上。
     - [ ] 拍摄 1～2 张测试照片，确认计数递增；尝试按 **PLAY（回放键）**，确认盲拍锁生效、无法直接回看未冲洗照片。
   - **③ 原厂图形屏蔽（Hide Canon's graphics）**：
     - [ ] 进入 M-Film `Settings -> Advanced -> Hide Canon's graphics` 并开启。
     - [ ] 返回取景器，确认佳能原厂曝光标尺与图标被屏蔽、不再穿透覆盖 M-Film HUD（关闭该选项后佳能对焦框与图标恢复正常）。
   - **④ 单张暗房显影（In-Camera Darkroom）**：
     - [ ] 在 M-Film 中提前退卷 / 结束当前卷（Rewind / Finish Roll），进入 **Darkroom（暗房）**。
     - [ ] 先选择 **Small** 或 **Medium** 输出尺寸，对刚才拍摄的 1 张 CR2 执行单张显影。
     - [ ] 观察进度条平滑推进直至生成 JPEG，无死机、无 OOM 报错（如需排查，关机后插卡检查 `ML/FILMROLL.LOG`）。

---

## 第三阶段：验证外置胶片配置加载器与 20 款 `(SF)` 胶卷（`03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`）

**目的**：在第二阶段确认 M-Film 主体稳定后，验证纯 GPL-2.0 外置配置加载器（`fos_extprof`）从 SD 卡动态扫描、加载 20 款离线烘焙的 SpektraFilm `(SF)` 参数化胶片，以及机内即时合成 `33×33×33` Cineon 3D LUT 显影的稳定性与内存安全性。

1. **校验、解压并核对 SD 卡目录结构**：
   - 使用随包 `.sha256` 文件核对 `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip`（本次本地验证 SHA256：`8ae94d461a71c43ff48812fa9caece0b70b4ff53a919ba7b31e01575a9d577b5`）。
   - 清空 SD 卡上旧的 `autoexec.bin` 与 `ML/` 目录，将 `03_EOSM2_MFilm_ExtProfiles_TestBuild.zip` 直接解压至 SD 卡根目录。
   - **关键目录核查**：打开 SD 卡中的 `ML/MFILM/profiles/` 目录，确认以下文件完整存在：
     - [ ] 共 **20 个 `.cfg` 胶片配置文件**（如 `kodak_portra_400.cfg`、`kodak_ektar_100.cfg`、`kodak_vision3_500t.cfg`、`fujifilm_pro_400h.cfg`、`fujifilm_velvia_100.cfg`、`kodak_kodachrome_64.cfg` 等）。
     - [ ] 存在 **`PROFILES_ATTRIBUTION.txt`**（CC BY-SA 4.0 协议署名说明）。
2. **通过固件升级加载并检查选卷架动态追加**：
   - 保持画质为 **RAW**，按第一阶段方式通过 **固件升级（Firmware Update）** 执行非持久化加载。
   - 进入实时取景后呼出 M-Film 选卷架（Film Shelf），在各个分组（Colour / Slide / Cine）向后翻页：
     - [ ] 确认选卷架末尾动态出现了带 **`(SF)`** 后缀的外置胶卷（例如 `Portra 400 (SF)`、`Ektar 100 (SF)`、`Vision3 500T (SF)`、`Pro 400H (SF)`、`Velvia 100 (SF)` 等），且罐体标签颜色、品牌文字与 ISO 标识显示正常、无乱码。
     - [ ] （可选）查看 `ML/FILMROLL.LOG`，确认出现 `extprof: loaded 20 external profiles from ML/MFILM/profiles` 日志记录。
3. **连续切卷稳定性测试**：
   - [ ] 在选卷架中快速连续左右切换至少 5～10 款不同内置与 `(SF)` 外置胶卷（跨 Colour / Slide / Cine 分组），确认界面刷新流畅、无卡顿、无花屏、无死机。
   - [ ] 任选一款 `(SF)` 胶卷（推荐 `Portra 400 (SF)` 或 `Velvia 100 (SF)`）执行装卷（Load Roll），拍摄 1～2 张 RAW 照片，确认 HUD 显示的胶卷名称、ISO 与计数正常。
4. **暗房即时 3D LUT 显影验证**：
   - [ ] 提前退卷 / 结束当前卷（Rewind / Finish Roll），进入 **Darkroom（暗房）**。
   - [ ] 选择 **Small** 或 **Medium** 输出尺寸，对刚刚用 `(SF)` 胶卷拍摄的 `.CR2` 执行机内显影。
   - [ ] 确认 `fos_extprof_build_lut()` 在相机临时内存池中即时合成 `33×33×33` Cineon 3D LUT 并平滑完成显影输出 JPEG，色彩风格符合所选 `(SF)` 胶卷特征，全过程无死机、无 OOM 报错。
   - [ ] （进阶）再次换装另一款风格差异明显的 `(SF)` 胶卷（如 `Vision3 500T (SF)` 或 `Kodachrome 64 (SF)`）拍 1 张并显影，确认二次切卷即时重算 LUT 稳定无泄漏。

---

## 四、 异常排查与日志收集

- **卡死 / 黑屏**：直接拔电池 5 秒后装回即可恢复原厂固件，无任何持久化损伤。
- **未看到 `(SF)` 胶卷**：请核对 SD 卡目录路径是否严格为 `ML/MFILM/profiles/*.cfg`（注意大小写与不要多嵌套一层目录），并检查 `ML/FILMROLL.LOG` 中的 `extprof:` 日志。
- **问题反馈日志**：请保留 SD 卡上的 `ML/FILMROLL.LOG` 与 `ML/LOGS/` 下的最新日志文件，连同复现步骤一并提交至 GitHub Issues 即可精准定位。

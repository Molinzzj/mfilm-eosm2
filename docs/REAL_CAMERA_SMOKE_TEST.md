# REAL_CAMERA_SMOKE_TEST.md — Canon EOS M2 (1.0.3) 实机两步安全冒烟指南

> **安全铁律提醒**：
> - 仅适用于官方固件版本为 **1.0.3** 的 **Canon EOS M2**（开机进入原厂菜单检查 `固件版本 / Firmware Ver. 1.0.3`）。
> - 本次全部测试产物均为**非持久化加载验证包**，**严禁**在首次测试中自动或手动刷写相机 NVRAM Bootflag。若遇到黑屏或卡死，**直接抠出电池静置 5 秒再装回**即可 100% 恢复佳能原厂系统。
> - 建议使用 **满电电池** 与 **≤ 32 GB 的 FAT32 格式 SD 卡**（在相机内格式化一次后，再插到电脑拷贝文件）。

---

## 第一步：验证纯净魔灯底座（`01_EOSM2_Clean_ML_Base.zip`）

**目的**：先独立确认 `EOSM2.103` 的硬件地址、显存映射、按键事件码与 592 KB 开机内存预留完全健康，排除底座问题。

1. **校验与解压**：
   - 核对 `01_EOSM2_Clean_ML_Base.zip` 的 SHA256：`9f52ae767858d2079a8d4d528b9aa7ce6aa2a9437393becfffd2640fbfd8b8c8`。
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

## 第二步：验证 M-Film 0.2.3 胶片系统（`02_EOSM2_MFilm_023_TestBuild.zip`）

**目的**：在底座验证通过后，验证外挂模块 `ML/modules/filmos.mo` 的加载、选卷、盲拍防回放、隐藏原厂图形与单张机内暗房 CR2→JPEG 显影全链路。

1. **清空 SD 卡并解压 M-Film 测试包**：
   - 核对 `02_EOSM2_MFilm_023_TestBuild.zip` 的 SHA256：`f63ed2986139bb4cd2836c815b41344642021d569f83c683defda2e38698a103`。
   - 删除卡上旧的 `autoexec.bin` 与 `ML/` 目录，将 `02_EOSM2_MFilm_023_TestBuild.zip` 直接解压至 SD 卡根目录。
   - 确认根目录存在 `autoexec.bin`、`ML/modules/filmos.mo`、`ML/modules/EOSM2_103.sym`、`ML/SETTINGS/filmos.en`、`ML/data/FOSFONT.BIN`、`ML/data/FOSFILMS.BIN`、`ML/DARKROOM/` 与 `ML/SAMPLES/`。
2. **将相机画质设为 RAW**：
   - 开机后先在佳能原厂菜单中将图像画质设为 **RAW**（机内暗房依赖 `.CR2` 文件显影）。
   - 同第一步方式通过 **固件升级（Firmware Update）** 加载 M-Film。
3. **四项核心功能逐项冒烟**：
   - **① 选卷装片（Film Shelf）**：
     - 进入实时取景后按 Magic Lantern 菜单键，确认自动进入 **M-Film 胶片主界面**（而非原版 ML 菜单；若进入原版 ML 菜单，请到 `Modules` 标签查看 `filmos.mo` 加载日志）。
     - 浏览胶片架（可按 PLAY 预览样片），任选一卷胶片（如 Kodak Portra 400 / Gold 200）并装卷（Load Roll）。
   - **② 盲拍与防回放（Blind Shooting）**：
     - 回到取景器界面，确认 M-Film 取景器 HUD（剩余张数、测光、胶片型号）正常直接绘制在屏幕上。
     - 拍摄 1～2 张测试照片，确认计数递增；尝试按 **PLAY（回放键）**，确认盲拍锁生效、无法直接回看未冲洗照片。
   - **③ 原厂图形屏蔽（Hide Canon's graphics）**：
     - 进入 M-Film `Settings -> Advanced -> Hide Canon's graphics` 并开启。
     - 返回取景器，确认佳能原厂曝光标尺与图标被屏蔽、不再穿透覆盖 M-Film HUD（关闭该选项后佳能对焦框与图标恢复正常）。
   - **④ 单张暗房显影（In-Camera Darkroom）**：
     - 在 M-Film 中提前退卷 / 结束当前卷（Rewind / Finish Roll），进入 **Darkroom（暗房）**。
     - 先选择 **Small** 或 **Medium** 输出尺寸，对刚才拍摄的 1 张 CR2 执行单张显影。
     - 观察进度条平滑推进直至生成 JPEG，无死机、无 OOM 报错（如需排查，关机后插卡检查 `ML/FILMROLL.LOG`）。

---

## 三、 异常排查与日志收集

- **卡死 / 黑屏**：直接拔电池 5 秒后装回即可恢复原厂固件，无任何持久化损伤。
- **问题反馈日志**：请保留 SD 卡上的 `ML/FILMROLL.LOG` 与 `ML/LOGS/` 下的最新日志文件，连同复现步骤一并提交至 GitHub Issues 即可精准定位。

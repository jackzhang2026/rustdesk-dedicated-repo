# BCS Beam macOS — 第二阶段交接(网络修复合入 + 验证清单)

**致:macOS 组负责人。日期:2026-08-27。自成一体,不依赖任何对话上下文。**
**当前仓库 tip:`a434dc0`(GitHub `origin/main`)。开工第一步:`git pull`。**

---

## 0. 一句话

你们的品牌化工作(`a4788ab`)已合入主线并确认质量很高;在那之后主线上又落了
**三个跨平台的网络层修复**(今天一天内定位并在 Windows 真机验证闭环),macOS 构建
**必须重新编译**才能带上它们——不重编的话,客户端会卡在 "Connecting..." 永远到不了
Ready。本文档说清楚:改了什么、你们继承什么、验证时哪个失败是预期内的不要去查。

## 1. 你们已完成的(确认收货,无需重做)

`a4788ab`(bundle id `com.brocent.bcsbeam`、`PRODUCT_NAME = BCS Beam`、icns/托盘图标、
deployment target 12.3、`build.py` 的 .app 路径)——全部正确,特别是 **`BCS Beam.app`
与编译内置 `APP_NAME` 精确一致**这一点,正是 Windows 端踩过的安装检测坑,你们一次做对了。
`build.py` 的 create-dmg 文案也已是 "BCS Beam Installer"。剩下的 `RustDesk.app` 字样
只存在于 Sciter(非 Flutter)死代码路径(`build.py` ~563-577 行),所有平台都不编译,
不用动。

## 2. `a4788ab` 之后主线新增了什么(你们 pull 后自动继承,重编译生效)

按时间序,三个网络提交 + 文档:

| 提交 | 内容 | 对 macOS 的意义 |
|---|---|---|
| `b4deeb7` | 强制所有连接走 TCP rendezvous(为大陆中转铺路) | **已被 b18c867 修订**,单独看会误导 |
| `c29bb26` | `secure_tcp()` 容忍"服务器不主动发加密握手"(我们自建的 OSS hbbs 就是完全被动的,连上后一个字节都不发;原代码把这个超时当致命错误→无限重连) | 跨平台 Rust,macOS 同样受益 |
| `b18c867` | **最终形态:UDP 优先,连续 10 次注册零响应才回退 TCP**(GeoDNS 统一域名后无法按主机名判断,只能运行时探测) | 跨平台 Rust,macOS 的实际连接行为由它决定 |
| `a434dc0` | Windows 真机验证记录(见 §4 基线) | 参考 |

**背景中最重要的一条**(已在服务器源码层面证实,写在
`HANDOFF_UDP_FALLBACK_BUILD_20260827.md` §3):开源版 `rustdesk-server` 的 hbbs
**在 TCP 路径上根本不实现客户端注册**(`RegisterPk` 回 `NOT_SUPPORT`、`RegisterPeer`
无处理分支,注册只在 UDP 路径实现)。所以:

> **TCP 兜底路径在服务端补丁(独立任务,Linux 侧负责)落地前,注册必然失败。
> 这是已知的、预期内的、已跟踪的状态——macOS 验证时如果碰到,不要花时间诊断。**

## 3. macOS 验证清单(重编译后)

- [ ] `git pull` 后全量重编译(Rust 变了,不能只重打包)
- [ ] **主验证:直连 HK 场景**——默认服务器 `beam-relay.centoffer.com`,普通网络下
      启动应**快速到 Ready**(UDP 第一把就通,无 ~30 秒延迟)。这是对 `b4deeb7` 回归
      的验收,不过关要大声报出来
- [ ] 安装检测:`.app` 放入 `/Applications` 后,应用内不再出现"安装"类提示
      (`src/platform/macos.rs` 按 `/Applications/BCS Beam.app` 判断,你们命名已对齐)
- [ ] 托盘图标:浅色/深色菜单栏各看一眼(你们换的新 B 字图标)
- [ ] About / License 页:完整法定名称 + 四个 brocent.com 链接(License / Terms of
      Service / Privacy / 官网)——这些来自共享 Flutter 代码,应自动正确,扫一眼即可
- [ ] (可选,预期失败)把服务器改成 `beam-relaycn.brocent.com`:应看到 ~30 秒 UDP
      探测后切 TCP、不再疯狂重连、但到不了 Ready——**这是 §2 说的预期内失败**,
      确认"失败得跟预期一样"即可,不用查

## 4. Windows 基线(对照用)

v1.3.9.29797178(同一份源码状态)已在 Windows 真机完成正向验证:安装后几分钟内
hbbs 服务器日志出现该机器的 `update_pk` 注册记录(TCP-only 故障期间为零条),UDP
rendezvous 套接字稳定,Ready 恢复。macOS 重编译后行为应与此一致。

## 5. macOS 侧剩余工作(按优先级)

1. 本文档 §3 的验证(当前最重要)
2. **签名 + 公证**:需要 Apple Developer Program 账号/证书——这是组织层面的依赖,
   请直接与 Jack 确认账号归属;技术路径见 `HANDOFF_MACOS_BUILD.md` §4 与
   `.github/workflows/flutter-build.yml` 的 codesign/notarize 步骤
3. **x86_64(Intel)构建决策**:目前只验证了 arm64;要不要出 Intel 版、还是只支持
   Apple Silicon,请与 Jack 定
4. DMG 视觉(背景图等):可参考 `branding/installer-art/` 的 Windows 安装向导美术风格

## 6. 提醒(Windows 端反复踩过)

- `.gitignore` 有全局 `*png`/`*svg` 规则,新增图片资源后**务必确认 `git status`
  真的列出了文件**(已咬人三次);需要豁免就按 `.gitignore` 末尾现有写法加
- 提交信息里若涉及网络/安全行为变化,写清楚影响面(参考 `c29bb26` 的写法——
  说明降级的只是可选传输层握手,会话端到端加密不受影响)

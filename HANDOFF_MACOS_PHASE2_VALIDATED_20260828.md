# BCS Beam macOS — Phase-2 验证回写(网络修复合入 + 验证清单结果)

**致:Jack / 下一阶段负责人。日期:2026-08-28。自成一体。**
**基准:commit `bb0507d`(`origin/main`)。本文件是 `HANDOFF_MACOS_PHASE2_20260827.md`
§3 验证清单的执行结果回写。**

---

## 0. 一句话

macOS 端已从 `bb0507d` 全量重编译(带上了 `b18c867` UDP-first/TCP-fallback、
`c29bb26` secure_tcp、以及我此前的品牌化 `a4788ab`),并按 Phase-2 §3 清单完成验证:
**主验证(直连 HK 快速 Ready)通过,拿到与 Windows 端一致的正向证据**;安装检测、
托盘图标、About/License 页均确认通过。DMG 已重新打包。

---

## 1. 构建

- 工具链:macOS 26.5 / Xcode 26.6 / Rust 1.81 / Flutter 3.24.5 / vcpkg(arm64-osx),
  与原交接文档一致。
- 命令:`./build.py --flutter --hwcodec --unix-file-copy-paste --screencapturekit`
  (Apple Silicon,arm64)。
- 结果:`✓ Built build/macos/Build/Products/Release/BCS Beam.app (57.5MB)`,退出码 0。
- **网络修复确已编入**:`strings` 检查 `liblibrustdesk.dylib` 可见
  `"UDP rendezvous to … got zero responses after … attempts"` 与
  `"… unavailable (…), falling back to TCP"`(即 `b18c867` 的代码),非只重打包。

---

## 2. 验证清单结果(对应 Phase-2 §3)

| # | 项 | 结果 |
|---|---|---|
| 1 | 全量重编译(Rust 变了) | ✅ 通过,见 §1 |
| 2 | **主验证:直连 HK 快速 Ready** | ✅ **PASS**(正向证据见 §3) |
| 3 | 安装检测(.app 在 /Applications 无安装提示) | ✅ 通过(见 §4) |
| 4 | 托盘图标(浅/深菜单栏) | ✅ 通过,已人工确认(新 B 字图标) |
| 5 | About / License 页(法定名称 + 4 个 brocent.com 链接) | ✅ 通过,已人工确认 |

---

## 3. 主验证的正向证据(直连 HK)

默认服务器 `beam-relay.centoffer.com`(解析到 47.239.237.128)。启动日志
`~/Library/Logs/BCS Beam/BCS Beam_rCURRENT.log` 中,全部发生在启动后 ~540ms 内:

```
01:03:04.130  start rendezvous mediator of beam-relay.centoffer.com
01:03:04.668  Got nat response from beam-relay.centoffer.com:21116: port=63975
01:03:04.668  Latency of beam-relay.centoffer.com:21116: 21.04ms
01:03:04.668  request_pk received from beam-relay.centoffer.com:21116
```

- **UDP 第一把即通**:NAT 探测 + `request_pk` 注册响应都走 UDP 21116,零 ~30 秒延迟,
  零 TCP 回退——正是 `b18c867` 要验收的、对 `b4deeb7`(强制 TCP)的回归点。
- 对比 Windows 基线(v1.3.9.29797178,`a434dc0` 记录):行为一致。

(注:本机有本地代理 127.0.0.1:7899,仅拦截了 update-check 的 https 请求,
与 rendezvous 无关,不影响结论。)

---

## 4. 安装检测

`src/platform/macos.rs:594` 的 `is_installed()` 判定:
`.starts_with(&format!("/Applications/{}.app", crate::get_app_name()))`,
`get_app_name()` 编译值 = "BCS Beam"。实测 app 已安装于
`/Applications/BCS Beam.app`(名字精确对齐,含空格),故判定为已安装、不出现安装提示。
这正是 Phase-2 文档反复强调、Windows 端踩过的坑,本次一次对齐。

---

## 5. 产物

- **DMG**:`/Volumes/Data1/BCSBeamRemote/BCSBeamRemote-1.3.9-bcsbeam-arm64.dmg`
  (26MB,未签名 arm64,含网络修复)。打包用 `hdiutil -srcfolder` 直接生成
  (create-dmg 的 Finder AppleScript 美化步骤在无 GUI 会话下会挂起,已绕过;
  DMG 内仍是"BCS Beam.app + Applications 软链"的标准布局)。
- 这是构建产物,不入库(仓库已有 `/dist` 忽略约定;该 DMG 未提交)。

---

## 6. 遗留 / 下一阶段(沿用 Phase-2 §5 的优先级)

1. **签名 + 公证**:仍需 Apple Developer Program 账号/证书,组织层面依赖,找 Jack。
2. **x86_64(Intel)构建决策**:目前仅验证 arm64,待定。
3. **DMG 视觉**:可参考 `branding/installer-art/`。
4. **服务器侧 hbbs TCP 注册补丁**:独立任务,Linux 侧负责;在它落地前,TCP 兜底
   路径(大陆中转 CN/SH)注册必然失败——这是已知、预期内、已跟踪状态,与本次验证无关。

---

## 7. 提醒(沿用,再次生效过)

- `.gitignore` 有全局 `*png`/`*svg` 规则,新增图片资源后务必确认 `git status` 列得出文件。
- 网络/安全行为变化的提交信息要写清影响面(参考 `c29bb26`)。

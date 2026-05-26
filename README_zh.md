# SteamVR 自启动管理器

[English](README.md) | [简体中文] | [日本語](README_ja.md) | [한국어](README_ko.md)

一个 Windows 桌面 GUI，用来更直观地管理 SteamVR 的 `.vrmanifest` 注册和自启动开关。

## 功能

- 自动识别 Steam 安装目录，也可以手动选择。
- 读取 `Steam/config/appconfig.json` 中的 `manifest_paths`。
- 解析每个 `.vrmanifest` 里的应用名称、`app_key`、启动程序和参数。
- 通过 `Steam/config/vrappconfig/<app_key>.vrappconfig` 开启或关闭自启动。
- 添加任意 Windows 程序，自动生成独立 `.vrmanifest` 并注册到 SteamVR。
- 删除注册时会先备份配置，不会删除目标程序本身。
- 默认的 `steamapps.vrmanifest` 总表不会被工具删除，避免影响 SteamVR 正常识别已安装应用。
- 支持多选列表项，并批量开启、关闭或删除注册。
- 支持白色、黑色、跟随系统主题。
- 支持交互式备份管理：新建、刷新、打开、删除、还原。
- 首次运行会按系统语言选择界面语言，语言列表顺序为 English、中文、日本語、한국어。
- 会记住语言、主题、Steam 目录和窗口大小。
- 使用自定义窗口图标。
- 新版界面去掉了持续加载动画，缩放窗口时更轻。
- 内置中文、英文、日文、韩语界面，右上角可以随时切换。

## 运行

优先双击 `steamvr_autostart_manager.pyw`。如果 Windows 没有关联 `.pyw`，就双击 `run.bat`，或者在这个目录运行：

```powershell
py -3 steamvr_autostart_manager.py
```

如果 Steam 安装在 `C:\Program Files` 或 `C:\Program Files (x86)`且写配置失败，请右键用管理员身份运行。

## 备份

点击“备份管理”可以查看已有备份，并执行新建、打开、删除和还原。新建备份会把当前 `appconfig.json`、`steamapps.vrmanifest`、`vrappconfig` 目录和已注册的 manifest 文件复制到 `%LOCALAPPDATA%\SteamVRManifestManager\manual_backups\...`。

还原备份前，工具会自动先备份一次当前配置，避免误操作后没有回退点。

## 打包为 exe

如果已经安装 PyInstaller，可以双击 `build_exe.bat`，生成文件在 `dist/SteamVR-Autostart-Manager.exe`。作者和版本信息会写入 exe 元数据，发布者为 AlanBacker。

没有 PyInstaller 时先运行：

```powershell
py -3 -m pip install pyinstaller
```

## 打包安装版

安装 Inno Setup 后双击 `build_installer.bat`，生成文件在 `installer_output/SteamVR-Autostart-Manager-Setup.exe`。

```powershell
winget install --id JRSoftware.InnoSetup -e
```

## SteamVR 配置说明

SteamVR/OpenVR 提供了添加 manifest、移除 manifest、读取/设置自动启动的应用接口。这个工具没有直接调用 OpenVR DLL，而是编辑 SteamVR 持久化配置文件：

- `Steam/config/appconfig.json`：保存长期注册的 manifest 路径。
- `Steam/config/vrappconfig/<app_key>.vrappconfig`：保存单个应用的 `autolaunch` 状态。

添加程序时，本工具会在 `%LOCALAPPDATA%\SteamVRManifestManager\manifests\...` 下生成类似这样的 manifest：

```json
{
   "source": "builtin",
   "applications": [
      {
         "app_key": "local.autostart.example.12345678",
         "launch_type": "binary",
         "binary_path_windows": "C:\\Path\\To\\Program.exe",
         "arguments": "",
         "is_dashboard_overlay": true,
         "strings": {
            "zh_cn": {
               "name": "Example",
               "description": "由 AlanBacker 制作的 SteamVR 自启动管理器注册。"
            },
            "en_us": {
               "name": "Example",
               "description": "Registered by AlanBacker's SteamVR Autostart Manager."
            },
            "ja_jp": {
               "name": "Example",
               "description": "AlanBacker 製 SteamVR 自動起動マネージャーによって登録されました。"
            },
            "ko_kr": {
               "name": "Example",
               "description": "AlanBacker가 만든 SteamVR 자동 시작 관리자가 등록했습니다."
            }
         }
      }
   ]
}
```

建议在关闭 SteamVR 后再修改配置，然后重新启动 SteamVR 查看效果。

## 开源协议

本项目采用 MIT 开源协议 - 详情请参阅 [LICENSE](LICENSE) 文件。

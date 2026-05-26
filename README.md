# SteamVR Autostart Manager

[English] | [简体中文](README_zh.md) | [日本語](README_ja.md) | [한국어](README_ko.md)

A Windows desktop GUI application to manage SteamVR `.vrmanifest` registration and autostart toggles more intuitively.

## Features

- Automatically detects the Steam installation directory, with an option to select it manually.
- Reads `manifest_paths` in `Steam/config/appconfig.json`.
- Parses the app name, `app_key`, launch binary path, and arguments from each `.vrmanifest`.
- Enables or disables autostart via `Steam/config/vrappconfig/<app_key>.vrappconfig`.
- Adds any Windows program, automatically generating an independent `.vrmanifest` and registering it with SteamVR.
- Backs up configuration files before removing registration, without deleting the target program itself.
- Protects the default `steamapps.vrmanifest` index from being removed by the tool to avoid affecting SteamVR's recognition of installed games.
- Supports multi-selection in the list to enable, disable, or remove registrations in batch.
- Supports Light, Dark, and System-matching theme modes.
- Interactive backup management: Create, Refresh, Open, Delete, and Restore backups.
- Automatically selects the interface language on first run based on the system locale (Language order: English, Chinese, Japanese, Korean).
- Persists user preferences for language, theme mode, Steam directory, and window size.
- Uses a custom window icon.
- The new UI eliminates continuous loading animations and is more lightweight when resizing.
- Built-in English, Chinese, Japanese, and Korean interfaces, switchable at any time from the top right corner.

## Running

Double-clicking `steamvr_autostart_manager.pyw` is preferred. If Windows does not have `.pyw` files associated with Python, double-click `run.bat` or run the following command in this directory:

```powershell
py -3 steamvr_autostart_manager.py
```

If Steam is installed in `C:\Program Files` or `C:\Program Files (x86)` and the configuration file fails to write, please right-click and run as administrator.

## Backups

Click "Backup Manager" to view existing backups, create new backups, open the backup folder, delete, or restore. Creating a backup copies the current `appconfig.json`, `steamapps.vrmanifest`, `vrappconfig` directory, and registered manifest files to `%LOCALAPPDATA%\SteamVRManifestManager\manual_backups\...`.

Before restoring a backup, the tool will automatically back up the current configuration first to ensure there is a rollback point.

## Packaging as EXE

If PyInstaller is installed, you can double-click `build_exe.bat` to generate the file at `dist/SteamVR-Autostart-Manager.exe`. Author and version information will be written to the EXE metadata (Publisher: AlanBacker).

If PyInstaller is not installed, install it first using:

```powershell
py -3 -m pip install pyinstaller
```

## Packaging the Installer

Install Inno Setup, then double-click `build_installer.bat` to generate the installer at `installer_output/SteamVR-Autostart-Manager-Setup.exe`.

```powershell
winget install --id JRSoftware.InnoSetup -e
```

## SteamVR Configuration Details

SteamVR/OpenVR provides API interfaces to add manifests, remove manifests, and read/set autostart apps. This tool directly edits the SteamVR persistent configuration files instead of calling OpenVR DLLs:

- `Steam/config/appconfig.json`: Saves long-term registered manifest paths.
- `Steam/config/vrappconfig/<app_key>.vrappconfig`: Saves the `autolaunch` state of individual applications.

When adding a program, the tool generates a manifest under `%LOCALAPPDATA%\SteamVRManifestManager\manifests\...` similar to the following:

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

It is recommended to modify configurations when SteamVR is closed, and then restart SteamVR to see the changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

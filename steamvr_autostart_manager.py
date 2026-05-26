from __future__ import annotations

import hashlib
import json
import locale
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError as exc:  # pragma: no cover - tkinter is part of normal Windows Python installs.
    raise SystemExit("This tool needs tkinter. Please install the standard Windows Python build.") from exc

if sys.platform == "win32":
    import winreg
else:  # pragma: no cover - the target is Windows, but keeping imports safe helps tests on other hosts.
    winreg = None  # type: ignore[assignment]


APP_TITLE = "SteamVR 自启动管理器"
APP_VENDOR_DIR = "SteamVRManifestManager"
DEFAULT_STEAM_PATHS = (
    r"C:\Program Files (x86)\Steam",
    r"C:\Program Files\Steam",
)
LANGUAGES = {
    "en": "English",
    "zh": "中文",
    "ja": "日本語",
    "ko": "한국어",
}
DEFAULT_LANGUAGE = "en"
THEME_MODES = ("system", "light", "dark")
DEFAULT_THEME = "system"
THEME_COLORS = {
    "light": {
        "bg": "#eef2f7",
        "surface": "#ffffff",
        "surface_alt": "#f8fafc",
        "header": "#132238",
        "accent": "#14b8a6",
        "accent_hover": "#0f9f91",
        "accent_pressed": "#0b8378",
        "button": "#e7edf5",
        "button_hover": "#dbe6f2",
        "button_pressed": "#ccd8e6",
        "danger": "#ef4444",
        "danger_surface": "#fee2e2",
        "danger_text": "#991b1b",
        "text": "#132238",
        "muted": "#64748b",
        "border": "#d7dee9",
        "selected": "#dff8f5",
        "tree_heading": "#e8eef6",
        "tree_bg": "#ffffff",
        "subtitle": "#b8c7d9",
    },
    "dark": {
        "bg": "#0d1117",
        "surface": "#161b22",
        "surface_alt": "#1f2937",
        "header": "#050a12",
        "accent": "#2dd4bf",
        "accent_hover": "#14b8a6",
        "accent_pressed": "#0f766e",
        "button": "#253244",
        "button_hover": "#304158",
        "button_pressed": "#3b4d65",
        "danger": "#fb7185",
        "danger_surface": "#3f1d2a",
        "danger_text": "#fecdd3",
        "text": "#e5eef8",
        "muted": "#9fb0c3",
        "border": "#334155",
        "selected": "#164e63",
        "tree_heading": "#233044",
        "tree_bg": "#10161f",
        "subtitle": "#aab8c8",
    },
}
COLORS = THEME_COLORS["light"].copy()
I18N = {
    "zh": {
        "app_title": "SteamVR 自启动管理器",
        "app_subtitle": "管理 .vrmanifest 注册、启动项和自动启动状态",
        "steam_dir": "Steam 目录",
        "browse": "浏览...",
        "refresh": "刷新",
        "language": "语言",
        "theme": "主题",
        "theme_system": "跟随系统",
        "theme_light": "白色",
        "theme_dark": "黑色",
        "registered_apps": "已注册应用",
        "actions": "操作",
        "name": "名称",
        "autolaunch": "自启动",
        "app_key": "App Key",
        "launch_type": "启动类型",
        "manifest": "Manifest",
        "details": "详情",
        "select_app_hint": "选择一个应用查看详情。",
        "add_program": "添加程序",
        "enable_autostart": "开启自启动",
        "disable_autostart": "关闭自启动",
        "remove_registration": "删除注册",
        "open_config_dir": "打开配置目录",
        "open_manifest": "打开 Manifest",
        "backup_current_config": "备份当前配置",
        "backup_manager": "备份管理",
        "backup_records": "备份记录",
        "backup_created_at": "创建时间",
        "backup_location": "位置",
        "backup_items": "内容",
        "backup_create": "新建备份",
        "backup_restore": "还原选中",
        "backup_delete": "删除选中",
        "backup_open": "打开备份目录",
        "backup_refresh": "刷新",
        "backup_close": "关闭",
        "backup_empty": "还没有备份记录。",
        "backup_select_one": "请先选择一个备份。",
        "backup_restore_confirm": "确定要还原这个备份吗？\n\n{path}\n\n当前配置会先自动备份，然后再还原选中的备份。",
        "backup_delete_confirm": "确定要删除这个备份吗？\n\n{path}",
        "status_backup_restored": "已还原备份：{path}",
        "status_backup_deleted": "已删除备份：{path}",
        "ready": "准备就绪",
        "no_steam_dir": "没有找到 Steam 目录，请手动选择。",
        "loaded": "已加载：{path}",
        "status_added": "已添加：{path}",
        "status_enabled": "已开启：{name}",
        "status_disabled": "已关闭：{name}",
        "status_removed": "已删除注册：{path}",
        "status_enabled_many": "已开启 {count} 个应用",
        "status_disabled_many": "已关闭 {count} 个应用",
        "status_removed_many": "已删除 {count} 个 manifest 注册",
        "status_backup_done": "已备份到：{path}",
        "choose_steam_dir": "选择 Steam 安装目录",
        "select_an_app": "请先选择一个应用。",
        "select_steam_first": "请先选择 Steam 目录。",
        "no_app_key": "该条目没有 App Key，不能设置自启动。",
        "no_selected_app_key": "选中的项目里没有可设置自启动的 App Key。",
        "selected_count": "已选择 {count} 个应用。",
        "no_removable_manifest": "选中的项目里没有可删除的 manifest。",
        "default_manifest_title": "无法删除默认总表",
        "default_manifest_message": "这是 SteamVR 默认的 steamapps.vrmanifest 总表，不建议从 appconfig.json 移除。\n\n如果只是想阻止某个程序随 SteamVR 启动，请选中它后点击“关闭自启动”。",
        "remove_prompt": "确定要从 SteamVR 注册列表里移除这个 manifest 吗？\n\n{path}\n\n这不会删除目标程序本身。相关配置会先备份。",
        "remove_prompt_many": "确定要从 SteamVR 注册列表里移除选中的 {count} 个 manifest 吗？\n\n这不会删除目标程序本身。相关配置会先备份。",
        "path_info": "路径：{path}",
        "unable_open": "无法打开：{path}\n{error}",
        "autostart_on": "开启",
        "autostart_off": "关闭",
        "autostart_unset": "未设置",
        "autostart_error": "异常",
        "detail_name": "名称：{value}",
        "detail_app_key": "App Key：{value}",
        "detail_program": "程序：{value}",
        "detail_args": "参数：{value}",
        "detail_cwd": "工作目录：{value}",
        "detail_manifest": "Manifest：{value}",
        "detail_autoconfig": "自启动配置：{value}",
        "detail_problem": "问题：{value}",
        "add_dialog_title": "添加自启动程序",
        "program_path": "程序路径",
        "display_name": "显示名称",
        "launch_args": "启动参数",
        "working_directory": "工作目录",
        "overlay_check": "作为 SteamVR Dashboard Overlay 注册",
        "autolaunch_check": "添加后立即开启自启动",
        "cancel": "取消",
        "add": "添加",
        "choose_program": "选择要随 SteamVR 启动的程序",
        "windows_program": "Windows 程序",
        "all_files": "所有文件",
        "choose_working_dir": "选择工作目录",
    },
    "en": {
        "app_title": "SteamVR Autostart Manager",
        "app_subtitle": "Manage .vrmanifest registration, launch entries, and autostart state",
        "steam_dir": "Steam Folder",
        "browse": "Browse...",
        "refresh": "Refresh",
        "language": "Language",
        "theme": "Theme",
        "theme_system": "System",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "registered_apps": "Registered Apps",
        "actions": "Actions",
        "name": "Name",
        "autolaunch": "Autostart",
        "app_key": "App Key",
        "launch_type": "Launch Type",
        "manifest": "Manifest",
        "details": "Details",
        "select_app_hint": "Select an app to view details.",
        "add_program": "Add Program",
        "enable_autostart": "Enable Autostart",
        "disable_autostart": "Disable Autostart",
        "remove_registration": "Remove Registration",
        "open_config_dir": "Open Config Folder",
        "open_manifest": "Open Manifest",
        "backup_current_config": "Back Up Current Config",
        "backup_manager": "Backup Manager",
        "backup_records": "Backup Records",
        "backup_created_at": "Created",
        "backup_location": "Location",
        "backup_items": "Items",
        "backup_create": "Create Backup",
        "backup_restore": "Restore Selected",
        "backup_delete": "Delete Selected",
        "backup_open": "Open Backup Folder",
        "backup_refresh": "Refresh",
        "backup_close": "Close",
        "backup_empty": "No backup records yet.",
        "backup_select_one": "Select a backup first.",
        "backup_restore_confirm": "Restore this backup?\n\n{path}\n\nThe current config will be backed up first, then the selected backup will be restored.",
        "backup_delete_confirm": "Delete this backup?\n\n{path}",
        "status_backup_restored": "Restored backup: {path}",
        "status_backup_deleted": "Deleted backup: {path}",
        "ready": "Ready",
        "no_steam_dir": "Steam folder was not found. Please choose it manually.",
        "loaded": "Loaded: {path}",
        "status_added": "Added: {path}",
        "status_enabled": "Enabled: {name}",
        "status_disabled": "Disabled: {name}",
        "status_removed": "Removed registration: {path}",
        "status_enabled_many": "Enabled autostart for {count} apps",
        "status_disabled_many": "Disabled autostart for {count} apps",
        "status_removed_many": "Removed {count} manifest registrations",
        "status_backup_done": "Backed up to: {path}",
        "choose_steam_dir": "Choose Steam installation folder",
        "select_an_app": "Select an app first.",
        "select_steam_first": "Choose the Steam folder first.",
        "no_app_key": "This entry has no App Key, so autostart cannot be changed.",
        "no_selected_app_key": "None of the selected entries has an App Key that can be changed.",
        "selected_count": "{count} apps selected.",
        "no_removable_manifest": "None of the selected entries has a removable manifest.",
        "default_manifest_title": "Default manifest protected",
        "default_manifest_message": "This is SteamVR's default steamapps.vrmanifest index and should stay registered in appconfig.json.\n\nTo stop one program from starting with SteamVR, select it and click Disable Autostart.",
        "remove_prompt": "Remove this manifest from SteamVR's registered list?\n\n{path}\n\nThe target program will not be deleted. Related configuration files will be backed up first.",
        "remove_prompt_many": "Remove the selected {count} manifest registrations from SteamVR's registered list?\n\nTarget programs will not be deleted. Related configuration files will be backed up first.",
        "path_info": "Path: {path}",
        "unable_open": "Could not open: {path}\n{error}",
        "autostart_on": "On",
        "autostart_off": "Off",
        "autostart_unset": "Unset",
        "autostart_error": "Issue",
        "detail_name": "Name: {value}",
        "detail_app_key": "App Key: {value}",
        "detail_program": "Program: {value}",
        "detail_args": "Arguments: {value}",
        "detail_cwd": "Working folder: {value}",
        "detail_manifest": "Manifest: {value}",
        "detail_autoconfig": "Autostart config: {value}",
        "detail_problem": "Problem: {value}",
        "add_dialog_title": "Add Autostart Program",
        "program_path": "Program Path",
        "display_name": "Display Name",
        "launch_args": "Launch Arguments",
        "working_directory": "Working Folder",
        "overlay_check": "Register as a SteamVR Dashboard Overlay",
        "autolaunch_check": "Enable autostart after adding",
        "cancel": "Cancel",
        "add": "Add",
        "choose_program": "Choose the program to start with SteamVR",
        "windows_program": "Windows Program",
        "all_files": "All Files",
        "choose_working_dir": "Choose working folder",
    },
    "ja": {
        "app_title": "SteamVR 自動起動マネージャー",
        "app_subtitle": ".vrmanifest の登録、起動項目、自動起動状態を管理",
        "steam_dir": "Steam フォルダー",
        "browse": "参照...",
        "refresh": "更新",
        "language": "言語",
        "theme": "テーマ",
        "theme_system": "システム",
        "theme_light": "ライト",
        "theme_dark": "ダーク",
        "registered_apps": "登録済みアプリ",
        "actions": "操作",
        "name": "名前",
        "autolaunch": "自動起動",
        "app_key": "App Key",
        "launch_type": "起動タイプ",
        "manifest": "Manifest",
        "details": "詳細",
        "select_app_hint": "アプリを選択すると詳細を表示します。",
        "add_program": "プログラムを追加",
        "enable_autostart": "自動起動を有効化",
        "disable_autostart": "自動起動を無効化",
        "remove_registration": "登録を削除",
        "open_config_dir": "設定フォルダーを開く",
        "open_manifest": "Manifest を開く",
        "backup_current_config": "現在の設定をバックアップ",
        "backup_manager": "バックアップ管理",
        "backup_records": "バックアップ記録",
        "backup_created_at": "作成日時",
        "backup_location": "場所",
        "backup_items": "内容",
        "backup_create": "新規バックアップ",
        "backup_restore": "選択を復元",
        "backup_delete": "選択を削除",
        "backup_open": "バックアップフォルダーを開く",
        "backup_refresh": "更新",
        "backup_close": "閉じる",
        "backup_empty": "バックアップ記録はまだありません。",
        "backup_select_one": "先にバックアップを選択してください。",
        "backup_restore_confirm": "このバックアップを復元しますか？\n\n{path}\n\n現在の設定を先に自動バックアップしてから、選択したバックアップを復元します。",
        "backup_delete_confirm": "このバックアップを削除しますか？\n\n{path}",
        "status_backup_restored": "バックアップを復元しました：{path}",
        "status_backup_deleted": "バックアップを削除しました：{path}",
        "ready": "準備完了",
        "no_steam_dir": "Steam フォルダーが見つかりません。手動で選択してください。",
        "loaded": "読み込み済み：{path}",
        "status_added": "追加しました：{path}",
        "status_enabled": "有効化しました：{name}",
        "status_disabled": "無効化しました：{name}",
        "status_removed": "登録を削除しました：{path}",
        "status_enabled_many": "{count} 個のアプリを有効化しました",
        "status_disabled_many": "{count} 個のアプリを無効化しました",
        "status_removed_many": "{count} 個の manifest 登録を削除しました",
        "status_backup_done": "バックアップ先：{path}",
        "choose_steam_dir": "Steam インストールフォルダーを選択",
        "select_an_app": "先にアプリを選択してください。",
        "select_steam_first": "先に Steam フォルダーを選択してください。",
        "no_app_key": "この項目には App Key がないため、自動起動を設定できません。",
        "no_selected_app_key": "選択した項目には変更可能な App Key がありません。",
        "selected_count": "{count} 個のアプリを選択中です。",
        "no_removable_manifest": "選択した項目には削除可能な manifest がありません。",
        "default_manifest_title": "既定の manifest は保護されています",
        "default_manifest_message": "これは SteamVR 既定の steamapps.vrmanifest インデックスです。appconfig.json から削除しないでください。\n\n特定のプログラムを SteamVR と一緒に起動させたくない場合は、その項目を選んで「自動起動を無効化」をクリックしてください。",
        "remove_prompt": "この manifest を SteamVR の登録リストから削除しますか？\n\n{path}\n\n対象プログラム自体は削除されません。関連設定は先にバックアップされます。",
        "remove_prompt_many": "選択した {count} 個の manifest 登録を SteamVR の登録リストから削除しますか？\n\n対象プログラム自体は削除されません。関連設定は先にバックアップされます。",
        "path_info": "パス：{path}",
        "unable_open": "開けませんでした：{path}\n{error}",
        "autostart_on": "有効",
        "autostart_off": "無効",
        "autostart_unset": "未設定",
        "autostart_error": "異常",
        "detail_name": "名前：{value}",
        "detail_app_key": "App Key：{value}",
        "detail_program": "プログラム：{value}",
        "detail_args": "引数：{value}",
        "detail_cwd": "作業フォルダー：{value}",
        "detail_manifest": "Manifest：{value}",
        "detail_autoconfig": "自動起動設定：{value}",
        "detail_problem": "問題：{value}",
        "add_dialog_title": "自動起動プログラムを追加",
        "program_path": "プログラムのパス",
        "display_name": "表示名",
        "launch_args": "起動引数",
        "working_directory": "作業フォルダー",
        "overlay_check": "SteamVR Dashboard Overlay として登録",
        "autolaunch_check": "追加後に自動起動を有効化",
        "cancel": "キャンセル",
        "add": "追加",
        "choose_program": "SteamVR と一緒に起動するプログラムを選択",
        "windows_program": "Windows プログラム",
        "all_files": "すべてのファイル",
        "choose_working_dir": "作業フォルダーを選択",
    },
    "ko": {
        "app_title": "SteamVR 자동 시작 관리자",
        "app_subtitle": ".vrmanifest 등록, 시작 항목, 자동 시작 상태 관리",
        "steam_dir": "Steam 폴더",
        "browse": "찾아보기...",
        "refresh": "새로고침",
        "language": "언어",
        "theme": "테마",
        "theme_system": "시스템",
        "theme_light": "라이트",
        "theme_dark": "다크",
        "registered_apps": "등록된 앱",
        "actions": "작업",
        "name": "이름",
        "autolaunch": "자동 시작",
        "app_key": "App Key",
        "launch_type": "시작 유형",
        "manifest": "Manifest",
        "details": "세부 정보",
        "select_app_hint": "앱을 선택하면 세부 정보를 볼 수 있습니다.",
        "add_program": "프로그램 추가",
        "enable_autostart": "자동 시작 켜기",
        "disable_autostart": "자동 시작 끄기",
        "remove_registration": "등록 삭제",
        "open_config_dir": "설정 폴더 열기",
        "open_manifest": "Manifest 열기",
        "backup_current_config": "현재 설정 백업",
        "backup_manager": "백업 관리",
        "backup_records": "백업 기록",
        "backup_created_at": "생성 시간",
        "backup_location": "위치",
        "backup_items": "내용",
        "backup_create": "새 백업",
        "backup_restore": "선택 항목 복원",
        "backup_delete": "선택 항목 삭제",
        "backup_open": "백업 폴더 열기",
        "backup_refresh": "새로고침",
        "backup_close": "닫기",
        "backup_empty": "아직 백업 기록이 없습니다.",
        "backup_select_one": "먼저 백업을 선택해 주세요.",
        "backup_restore_confirm": "이 백업을 복원할까요?\n\n{path}\n\n현재 설정을 먼저 자동 백업한 뒤 선택한 백업을 복원합니다.",
        "backup_delete_confirm": "이 백업을 삭제할까요?\n\n{path}",
        "status_backup_restored": "백업 복원됨: {path}",
        "status_backup_deleted": "백업 삭제됨: {path}",
        "ready": "준비 완료",
        "no_steam_dir": "Steam 폴더를 찾지 못했습니다. 직접 선택해 주세요.",
        "loaded": "로드됨: {path}",
        "status_added": "추가됨: {path}",
        "status_enabled": "켜짐: {name}",
        "status_disabled": "꺼짐: {name}",
        "status_removed": "등록 삭제됨: {path}",
        "status_enabled_many": "{count}개 앱의 자동 시작을 켰습니다",
        "status_disabled_many": "{count}개 앱의 자동 시작을 껐습니다",
        "status_removed_many": "{count}개 manifest 등록을 삭제했습니다",
        "status_backup_done": "백업 위치: {path}",
        "choose_steam_dir": "Steam 설치 폴더 선택",
        "select_an_app": "먼저 앱을 선택해 주세요.",
        "select_steam_first": "먼저 Steam 폴더를 선택해 주세요.",
        "no_app_key": "이 항목에는 App Key가 없어 자동 시작을 설정할 수 없습니다.",
        "no_selected_app_key": "선택한 항목 중 변경할 수 있는 App Key가 없습니다.",
        "selected_count": "{count}개 앱이 선택되었습니다.",
        "no_removable_manifest": "선택한 항목 중 삭제할 수 있는 manifest가 없습니다.",
        "default_manifest_title": "기본 manifest 보호됨",
        "default_manifest_message": "이 항목은 SteamVR 기본 steamapps.vrmanifest 인덱스라 appconfig.json에서 제거하지 않는 것이 좋습니다.\n\n특정 프로그램만 SteamVR과 함께 시작하지 않게 하려면 해당 항목을 선택하고 “자동 시작 끄기”를 클릭하세요.",
        "remove_prompt": "이 manifest를 SteamVR 등록 목록에서 제거할까요?\n\n{path}\n\n대상 프로그램 자체는 삭제되지 않습니다. 관련 설정은 먼저 백업됩니다.",
        "remove_prompt_many": "선택한 {count}개 manifest 등록을 SteamVR 등록 목록에서 제거할까요?\n\n대상 프로그램 자체는 삭제되지 않습니다. 관련 설정은 먼저 백업됩니다.",
        "path_info": "경로: {path}",
        "unable_open": "열 수 없음: {path}\n{error}",
        "autostart_on": "켜짐",
        "autostart_off": "꺼짐",
        "autostart_unset": "미설정",
        "autostart_error": "문제",
        "detail_name": "이름: {value}",
        "detail_app_key": "App Key: {value}",
        "detail_program": "프로그램: {value}",
        "detail_args": "인수: {value}",
        "detail_cwd": "작업 폴더: {value}",
        "detail_manifest": "Manifest: {value}",
        "detail_autoconfig": "자동 시작 설정: {value}",
        "detail_problem": "문제: {value}",
        "add_dialog_title": "자동 시작 프로그램 추가",
        "program_path": "프로그램 경로",
        "display_name": "표시 이름",
        "launch_args": "시작 인수",
        "working_directory": "작업 폴더",
        "overlay_check": "SteamVR Dashboard Overlay로 등록",
        "autolaunch_check": "추가 후 자동 시작 켜기",
        "cancel": "취소",
        "add": "추가",
        "choose_program": "SteamVR과 함께 시작할 프로그램 선택",
        "windows_program": "Windows 프로그램",
        "all_files": "모든 파일",
        "choose_working_dir": "작업 폴더 선택",
    },
}


class SteamVRConfigError(Exception):
    """Raised when SteamVR configuration cannot be read or written safely."""


@dataclass
class AppEntry:
    manifest_path: Path
    app_key: str
    name: str
    description: str
    launch_type: str
    binary_path: str
    arguments: str
    working_directory: str
    is_dashboard_overlay: bool
    autolaunch: Optional[bool]
    autolaunch_config_path: Path
    manifest_exists: bool
    manifest_error: str = ""


@dataclass
class BackupEntry:
    path: Path
    created_at: str
    location: str
    item_count: int


def app_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / APP_VENDOR_DIR


def generated_manifest_root() -> Path:
    return app_data_dir() / "manifests"


def settings_path() -> Path:
    return app_data_dir() / "settings.json"


def tr(lang: str, key: str, **kwargs: Any) -> str:
    template = I18N.get(lang, I18N[DEFAULT_LANGUAGE]).get(key, I18N[DEFAULT_LANGUAGE].get(key, key))
    return template.format(**kwargs) if kwargs else template


def load_settings() -> Dict[str, Any]:
    try:
        data = read_json_file(settings_path(), {})
        return data if isinstance(data, dict) else {}
    except SteamVRConfigError:
        return {}


def save_settings(updates: Dict[str, Any]) -> None:
    data = load_settings()
    data.update(updates)
    try:
        write_json_file(settings_path(), data)
    except SteamVRConfigError:
        pass


def load_language() -> str:
    data = load_settings()
    if data.get("language") in LANGUAGES:
        return str(data["language"])
    return detect_system_language()


def save_language(lang: str) -> None:
    if lang not in LANGUAGES:
        return
    save_settings({"language": lang})


def detect_system_language() -> str:
    candidates: List[str] = []
    for getter in (locale.getlocale, locale.getdefaultlocale):
        try:
            value = getter()[0]
        except (TypeError, ValueError):
            value = None
        if value:
            candidates.append(str(value).lower())
    for env_name in ("LANG", "LANGUAGE"):
        value = os.environ.get(env_name)
        if value:
            candidates.append(value.lower())

    joined = " ".join(candidates)
    if "zh" in joined or "chinese" in joined:
        return "zh"
    if "ja" in joined or "japanese" in joined:
        return "ja"
    if "ko" in joined or "korean" in joined:
        return "ko"
    return DEFAULT_LANGUAGE


def load_theme() -> str:
    data = load_settings()
    if data.get("theme") in THEME_MODES:
        return str(data["theme"])
    return DEFAULT_THEME


def save_theme(theme: str) -> None:
    if theme not in THEME_MODES:
        return
    save_settings({"theme": theme})


def system_prefers_dark() -> bool:
    if sys.platform != "win32" or winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return int(value) == 0
    except OSError:
        return False


def effective_theme(theme: str) -> str:
    if theme == "dark":
        return "dark"
    if theme == "system" and system_prefers_dark():
        return "dark"
    return "light"


def apply_color_theme(theme: str) -> None:
    global COLORS
    COLORS = THEME_COLORS[effective_theme(theme)].copy()


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def create_app_icon(master: tk.Misc) -> tk.PhotoImage:
    image = tk.PhotoImage(master=master, width=32, height=32)
    image.put("#0b1220", to=(0, 0, 32, 32))
    image.put("#101b2d", to=(2, 2, 30, 30))
    image.put("#14b8a6", to=(6, 6, 26, 9))
    image.put("#38bdf8", to=(6, 9, 10, 26))
    image.put("#e5eef8", to=(12, 12, 16, 26))
    image.put("#e5eef8", to=(16, 12, 23, 16))
    image.put("#e5eef8", to=(20, 16, 24, 26))
    image.put("#14b8a6", to=(12, 20, 24, 23))
    image.put("#38bdf8", to=(24, 6, 27, 26))
    return image


def manual_backup_roots(config_dir: Optional[Path] = None) -> List[Path]:
    roots = [app_data_dir() / "manual_backups"]
    if config_dir is not None:
        roots.append(config_dir / "vrmanifest_manager_backups" / "manual")
    return roots


class SmoothAppTable(tk.Frame):
    row_height = 32
    header_height = 40
    wheel_pixels = 42

    def __init__(self, master: tk.Misc, select_callback: Any):
        super().__init__(master, bg=COLORS["surface"], highlightthickness=0)
        self.select_callback = select_callback
        self.columns: List[Dict[str, Any]] = []
        self.rows: List[Dict[str, Any]] = []
        self.selected: set[int] = set()
        self.anchor_index: Optional[int] = None
        self.hover_index: Optional[int] = None
        self.scroll_target = 0.0
        self.scroll_job: Optional[str] = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.header = tk.Canvas(self, height=self.header_height, highlightthickness=0, bd=0, bg=COLORS["tree_heading"])
        self.header.grid(row=0, column=0, sticky="ew")
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=COLORS["tree_bg"], yscrollincrement=1, takefocus=True)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Modern.Vertical.TScrollbar")
        self.scrollbar.grid(row=1, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.header.bind("<Configure>", lambda _event: self.redraw())
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda _event: self._scroll_by(-self.wheel_pixels))
        self.canvas.bind("<Button-5>", lambda _event: self._scroll_by(self.wheel_pixels))
        self.canvas.bind("<Control-a>", self._select_all_event)
        self.canvas.bind("<Control-A>", self._select_all_event)

    def set_columns(self, columns: List[Dict[str, Any]]) -> None:
        self.columns = columns
        self.redraw()

    def set_rows(self, rows: List[Dict[str, Any]]) -> None:
        self.rows = rows
        self.selected = {index for index in self.selected if index < len(rows)}
        self.hover_index = None
        self.anchor_index = min(self.selected) if self.selected else None
        self.scroll_target = clamp(self.scroll_target, 0.0, self._max_scroll())
        self._jump_to(self.scroll_target)
        self.redraw()

    def selection(self) -> Tuple[str, ...]:
        return tuple(str(index) for index in sorted(self.selected))

    def selection_set(self, item_ids: Iterable[str]) -> None:
        self.selected = set()
        for item_id in item_ids:
            try:
                index = int(item_id)
            except ValueError:
                continue
            if 0 <= index < len(self.rows):
                self.selected.add(index)
        self.anchor_index = min(self.selected) if self.selected else None
        self.redraw_rows()
        self.select_callback()

    def selection_remove(self, _item_ids: Iterable[str]) -> None:
        self.clear_selection()

    def clear_selection(self) -> None:
        self.selected.clear()
        self.anchor_index = None
        self.redraw_rows()
        self.select_callback()

    def focus(self, _item_id: str = "") -> None:
        self.canvas.focus_set()

    def get_children(self) -> Tuple[str, ...]:
        return tuple(str(index) for index in range(len(self.rows)))

    def exists(self, item_id: str) -> bool:
        try:
            index = int(item_id)
        except ValueError:
            return False
        return 0 <= index < len(self.rows)

    def see(self, item_id: str) -> None:
        if not self.exists(item_id):
            return
        index = int(item_id)
        row_top = index * self.row_height
        row_bottom = row_top + self.row_height
        current = self.canvas.canvasy(0)
        height = max(1, self.canvas.winfo_height())
        if row_top < current:
            self._jump_to(row_top)
        elif row_bottom > current + height:
            self._jump_to(row_bottom - height)

    def redraw(self) -> None:
        self.configure(bg=COLORS["surface"])
        self.redraw_header()
        self.redraw_rows()

    def redraw_header(self) -> None:
        self.header.delete("all")
        width = max(1, self.header.winfo_width())
        self.header.configure(bg=COLORS["tree_heading"])
        self.header.create_rectangle(0, 0, width, self.header_height, fill=COLORS["tree_heading"], outline="")
        x = 0
        for column in self._resolved_columns(width):
            self.header.create_text(
                x + column["width"] / 2,
                self.header_height / 2,
                text=column["title"],
                fill=COLORS["text"],
                font=("Microsoft YaHei UI", 10, "bold"),
                anchor="center",
            )
            x += column["width"]

    def redraw_rows(self) -> None:
        self.canvas.delete("all")
        width = max(1, self.canvas.winfo_width())
        height = self._content_height()
        self.canvas.configure(bg=COLORS["tree_bg"], scrollregion=(0, 0, width, height))
        columns = self._resolved_columns(width)
        for index, row in enumerate(self.rows):
            y = index * self.row_height
            if index in self.selected:
                bg = COLORS["selected"]
            elif index == self.hover_index:
                bg = COLORS["surface_alt"]
            else:
                bg = COLORS["tree_bg"]
            self.canvas.create_rectangle(0, y, width, y + self.row_height, fill=bg, outline="")
            self.canvas.create_line(0, y + self.row_height, width, y + self.row_height, fill=COLORS["border"])
            x = 0
            for column in columns:
                value = str(row.get(column["key"], ""))
                color = row.get("color", COLORS["text"]) if column["key"] in {"name", "autolaunch", "app_key", "launch_type"} else COLORS["text"]
                anchor = column.get("anchor", "w")
                text_anchor = "center" if anchor == "center" else "w"
                text_x = x + column["width"] / 2 if text_anchor == "center" else x + 8
                self.canvas.create_text(
                    text_x,
                    y + self.row_height / 2,
                    text=self._ellipsize(value, column["width"]),
                    fill=color,
                    font=("Microsoft YaHei UI", 10),
                    anchor=text_anchor,
                )
                x += column["width"]

    def _resolved_columns(self, width: int) -> List[Dict[str, Any]]:
        fixed = sum(column["width"] for column in self.columns if not column.get("stretch"))
        stretch_columns = [column for column in self.columns if column.get("stretch")]
        extra = max(0, width - fixed)
        resolved: List[Dict[str, Any]] = []
        for column in self.columns:
            item = dict(column)
            if column.get("stretch") and stretch_columns:
                item["width"] = max(column["width"], extra // len(stretch_columns))
            resolved.append(item)
        return resolved

    def _ellipsize(self, value: str, width: int) -> str:
        max_chars = max(4, int((width - 16) / 7))
        if len(value) <= max_chars:
            return value
        return value[: max_chars - 1] + "…"

    def _content_height(self) -> int:
        return max(1, len(self.rows) * self.row_height)

    def _max_scroll(self) -> float:
        return max(0.0, self._content_height() - max(1, self.canvas.winfo_height()))

    def _on_canvas_configure(self, _event: tk.Event) -> None:
        self.scroll_target = clamp(self.canvas.canvasy(0), 0.0, self._max_scroll())
        self.redraw()

    def _on_click(self, event: tk.Event) -> str:
        self.canvas.focus_set()
        index = int(self.canvas.canvasy(event.y) // self.row_height)
        if index < 0 or index >= len(self.rows):
            self.clear_selection()
            return "break"
        shift = bool(event.state & 0x0001)
        ctrl = bool(event.state & 0x0004)
        if shift and self.anchor_index is not None:
            start, end = sorted((self.anchor_index, index))
            self.selected = set(range(start, end + 1))
        elif ctrl:
            if index in self.selected:
                self.selected.remove(index)
            else:
                self.selected.add(index)
            self.anchor_index = index
        else:
            self.selected = {index}
            self.anchor_index = index
        self.redraw_rows()
        self.select_callback()
        return "break"

    def _on_motion(self, event: tk.Event) -> None:
        index = int(self.canvas.canvasy(event.y) // self.row_height)
        new_hover = index if 0 <= index < len(self.rows) else None
        if new_hover != self.hover_index:
            self.hover_index = new_hover
            self.redraw_rows()

    def _on_leave(self, _event: tk.Event) -> None:
        if self.hover_index is not None:
            self.hover_index = None
            self.redraw_rows()

    def _select_all_event(self, _event: tk.Event) -> str:
        self.selection_set(str(index) for index in range(len(self.rows)))
        return "break"

    def _on_mousewheel(self, event: tk.Event) -> str:
        return self._scroll_by((-event.delta / 120) * self.wheel_pixels)

    def _scroll_by(self, pixels: float) -> str:
        if self.scroll_job is not None:
            try:
                self.after_cancel(self.scroll_job)
            except tk.TclError:
                pass
        current = self.canvas.canvasy(0)
        if abs(self.scroll_target - current) > self.wheel_pixels * 3:
            self.scroll_target = current
        self.scroll_target = clamp(self.scroll_target + pixels, 0.0, self._max_scroll())
        self._animate_scroll(0, current, self.scroll_target)
        return "break"

    def _animate_scroll(self, frame: int, start: float, target: float) -> None:
        progress = min(1.0, (frame + 1) / 9)
        eased = 1 - (1 - progress) ** 3
        value = start + (target - start) * eased
        self._jump_to(value)
        if progress >= 1.0:
            self._jump_to(target)
            self.scroll_job = None
            return
        self.scroll_job = self.after(10, lambda: self._animate_scroll(frame + 1, start, target))

    def _jump_to(self, y: float) -> None:
        max_scroll = self._max_scroll()
        y = clamp(y, 0.0, max_scroll)
        self.canvas.yview_moveto(0.0 if max_scroll <= 0 else y / self._content_height())


def detect_steam_path() -> Optional[Path]:
    candidates: List[Path] = []

    if sys.platform == "win32" and winreg is not None:
        registry_locations: Tuple[Tuple[Any, str, str], ...] = (
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
        )
        for hive, key_name, value_name in registry_locations:
            try:
                with winreg.OpenKey(hive, key_name) as key:
                    value, _ = winreg.QueryValueEx(key, value_name)
                    if value:
                        candidates.append(Path(str(value).replace("/", "\\")))
            except OSError:
                continue

    candidates.extend(Path(path) for path in DEFAULT_STEAM_PATHS)

    for candidate in candidates:
        if (candidate / "steam.exe").exists() or (candidate / "config").exists():
            return candidate
    return candidates[0] if candidates else None


def normalize_for_compare(path: Path | str) -> str:
    expanded = os.path.expandvars(os.path.expanduser(str(path)))
    return os.path.normcase(os.path.abspath(expanded))


def ensure_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def read_json_file(path: Path, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise SteamVRConfigError(f"JSON 格式错误：{path}\n{exc}") from exc
    except OSError as exc:
        raise SteamVRConfigError(f"读取失败：{path}\n{exc}") from exc


def write_json_file(path: Path, data: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=3)
            handle.write("\n")
        tmp_path.replace(path)
    except OSError as exc:
        raise SteamVRConfigError(
            f"写入失败：{path}\n\n请确认当前用户有写入权限；如果是在写 Steam 配置，请尝试用管理员身份运行本工具。"
        ) from exc


def backup_file(path: Path, backup_root: Optional[Path] = None) -> Optional[Path]:
    if not path.exists():
        return None

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    preferred_root = backup_root or path.parent / "vrmanifest_manager_backups"
    fallback_root = app_data_dir() / "backups"
    for root in (preferred_root, fallback_root):
        try:
            root.mkdir(parents=True, exist_ok=True)
            target = root / f"{path.name}.{timestamp}.bak"
            shutil.copy2(path, target)
            return target
        except OSError:
            continue
    raise SteamVRConfigError(f"无法为配置文件创建备份：{path}")


def safe_app_key_part(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", ".", text.strip())
    cleaned = re.sub(r"\.+", ".", cleaned).strip(".-_")
    return cleaned or "app"


def make_app_key(display_name: str, exe_path: Path) -> str:
    seed = f"{display_name}|{exe_path}".encode("utf-8", "ignore")
    digest = hashlib.sha1(seed).hexdigest()[:8]
    return f"local.autostart.{safe_app_key_part(display_name or exe_path.stem)}.{digest}"


def validate_app_key(app_key: str) -> None:
    if not app_key:
        raise SteamVRConfigError("App Key 不能为空。")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", app_key):
        raise SteamVRConfigError("App Key 只能包含英文字母、数字、点、下划线和短横线。")


def localized_string(strings: Any, key: str, fallback: str = "") -> str:
    if not isinstance(strings, dict):
        return fallback
    for locale in ("zh_cn", "zh-CN", "en_us", "en-US", "ja_jp", "ja-JP", "ko_kr", "ko-KR"):
        section = strings.get(locale)
        if isinstance(section, dict) and section.get(key):
            return str(section[key])
    for section in strings.values():
        if isinstance(section, dict) and section.get(key):
            return str(section[key])
    return fallback


class SteamVRConfig:
    def __init__(self, steam_root: Path):
        self.steam_root = steam_root
        self.config_dir = steam_root / "config"
        self.appconfig_path = self.config_dir / "appconfig.json"
        self.vrappconfig_dir = self.config_dir / "vrappconfig"

    @property
    def default_steamapps_manifest(self) -> Path:
        return self.config_dir / "steamapps.vrmanifest"

    def load_appconfig(self) -> Dict[str, Any]:
        default = {"manifest_paths": [str(self.default_steamapps_manifest)]}
        data = read_json_file(self.appconfig_path, default)
        if not isinstance(data, dict):
            raise SteamVRConfigError(f"appconfig.json 顶层必须是 JSON 对象：{self.appconfig_path}")
        data["manifest_paths"] = [str(item) for item in ensure_list(data.get("manifest_paths")) if str(item).strip()]
        if not data["manifest_paths"]:
            data["manifest_paths"] = [str(self.default_steamapps_manifest)]
        return data

    def save_appconfig(self, data: Dict[str, Any]) -> None:
        backup_file(self.appconfig_path, self.config_dir / "vrmanifest_manager_backups")
        write_json_file(self.appconfig_path, data)

    def manifest_paths(self) -> List[Path]:
        data = self.load_appconfig()
        return [Path(os.path.expandvars(os.path.expanduser(item))) for item in data["manifest_paths"]]

    def add_manifest_path(self, manifest_path: Path) -> None:
        manifest_path = manifest_path.resolve()
        data = self.load_appconfig()
        current = [normalize_for_compare(item) for item in data["manifest_paths"]]
        if normalize_for_compare(manifest_path) not in current:
            data["manifest_paths"].append(str(manifest_path))
            self.save_appconfig(data)

    def remove_manifest_path(self, manifest_path: Path) -> None:
        target = normalize_for_compare(manifest_path)
        data = self.load_appconfig()
        new_paths = [item for item in data["manifest_paths"] if normalize_for_compare(item) != target]
        if len(new_paths) == len(data["manifest_paths"]):
            return
        data["manifest_paths"] = new_paths
        self.save_appconfig(data)

    def autolaunch_config_path(self, app_key: str) -> Path:
        return self.vrappconfig_dir / f"{app_key}.vrappconfig"

    def get_autolaunch(self, app_key: str) -> Optional[bool]:
        path = self.autolaunch_config_path(app_key)
        if not path.exists():
            return None
        data = read_json_file(path, {})
        if not isinstance(data, dict):
            return None
        value = data.get("autolaunch")
        return bool(value) if isinstance(value, bool) else None

    def set_autolaunch(self, app_key: str, enabled: bool) -> None:
        validate_app_key(app_key)
        path = self.autolaunch_config_path(app_key)
        data = read_json_file(path, {}) if path.exists() else {}
        if not isinstance(data, dict):
            data = {}
        data["autolaunch"] = bool(enabled)
        data.setdefault("last_launch_time", "0")
        backup_file(path, self.config_dir / "vrmanifest_manager_backups")
        write_json_file(path, data)

    def delete_autolaunch_config(self, app_key: str) -> None:
        path = self.autolaunch_config_path(app_key)
        if path.exists():
            backup_file(path, self.config_dir / "vrmanifest_manager_backups")
            try:
                path.unlink()
            except OSError as exc:
                raise SteamVRConfigError(f"删除自启动配置失败：{path}\n{exc}") from exc

    def backup_current_config(self) -> Path:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        roots = manual_backup_roots(self.config_dir)
        last_error: Optional[OSError] = None
        for root in roots:
            backup_dir = root / timestamp
            try:
                backup_dir.mkdir(parents=True, exist_ok=False)
                self._copy_current_config_to(backup_dir)
                return backup_dir
            except OSError as exc:
                last_error = exc
                continue
        raise SteamVRConfigError(f"备份当前配置失败：{last_error}")

    def _copy_current_config_to(self, backup_dir: Path) -> None:
        def copy_if_exists(src: Path, dst: Path) -> None:
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        copy_if_exists(self.appconfig_path, backup_dir / "appconfig.json")
        copy_if_exists(self.default_steamapps_manifest, backup_dir / "steamapps.vrmanifest")

        if self.vrappconfig_dir.exists():
            shutil.copytree(self.vrappconfig_dir, backup_dir / "vrappconfig", dirs_exist_ok=True)

        manifest_backup_dir = backup_dir / "registered_manifests"
        seen: set[str] = set()
        manifest_records: List[Dict[str, str]] = []
        for manifest_path in self.manifest_paths():
            marker = normalize_for_compare(manifest_path)
            if marker in seen or not manifest_path.exists():
                continue
            seen.add(marker)
            suffix = manifest_path.suffix or ".vrmanifest"
            digest = hashlib.sha1(marker.encode("utf-8", "ignore")).hexdigest()[:8]
            filename = f"{safe_app_key_part(manifest_path.stem)}-{digest}{suffix}"
            copy_if_exists(manifest_path, manifest_backup_dir / filename)
            manifest_records.append({"original_path": str(manifest_path), "backup_file": filename})
        write_json_file(backup_dir / "manifest_index.json", manifest_records)

    def list_backups(self) -> List[BackupEntry]:
        entries: List[BackupEntry] = []
        seen: set[str] = set()
        for root in manual_backup_roots(self.config_dir):
            if not root.exists():
                continue
            try:
                candidates = [path for path in root.iterdir() if path.is_dir()]
            except OSError:
                continue
            for path in candidates:
                marker = normalize_for_compare(path)
                if marker in seen:
                    continue
                seen.add(marker)
                entries.append(
                    BackupEntry(
                        path=path,
                        created_at=self._backup_created_at(path),
                        location=str(path),
                        item_count=sum(1 for item in path.rglob("*") if item.is_file()),
                    )
                )
        entries.sort(key=lambda entry: entry.path.name, reverse=True)
        return entries

    def _backup_created_at(self, path: Path) -> str:
        try:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(path.stat().st_mtime))
        except OSError:
            return path.name

    def restore_backup(self, backup_dir: Path) -> None:
        backup_dir = backup_dir.resolve()
        if not self._is_known_backup_dir(backup_dir):
            raise SteamVRConfigError(f"不是本工具管理的备份目录：{backup_dir}")
        if not backup_dir.exists():
            raise SteamVRConfigError(f"备份不存在：{backup_dir}")

        self.backup_current_config()

        def restore_file(name: str, target: Path) -> None:
            src = backup_dir / name
            if src.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)

        restore_file("appconfig.json", self.appconfig_path)
        restore_file("steamapps.vrmanifest", self.default_steamapps_manifest)

        vrappconfig_backup = backup_dir / "vrappconfig"
        if vrappconfig_backup.exists():
            if self.vrappconfig_dir.exists():
                shutil.rmtree(self.vrappconfig_dir)
            shutil.copytree(vrappconfig_backup, self.vrappconfig_dir)

        manifest_records = read_json_file(backup_dir / "manifest_index.json", [])
        if isinstance(manifest_records, list):
            for record in manifest_records:
                if not isinstance(record, dict):
                    continue
                original_path = record.get("original_path")
                backup_file = record.get("backup_file")
                if not original_path or not backup_file:
                    continue
                src = backup_dir / "registered_manifests" / str(backup_file)
                dst = Path(str(original_path))
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)

    def delete_backup(self, backup_dir: Path) -> None:
        backup_dir = backup_dir.resolve()
        if not self._is_known_backup_dir(backup_dir):
            raise SteamVRConfigError(f"不是本工具管理的备份目录：{backup_dir}")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

    def _is_known_backup_dir(self, backup_dir: Path) -> bool:
        backup_dir = backup_dir.resolve()
        for root in manual_backup_roots(self.config_dir):
            try:
                root_resolved = root.resolve()
            except OSError:
                continue
            if backup_dir == root_resolved:
                return False
            try:
                backup_dir.relative_to(root_resolved)
                return True
            except ValueError:
                continue
        return False

    def parse_manifest(self, manifest_path: Path) -> List[AppEntry]:
        manifest_path = Path(manifest_path)
        if not manifest_path.exists():
            return [
                AppEntry(
                    manifest_path=manifest_path,
                    app_key="",
                    name="缺失的 manifest",
                    description="",
                    launch_type="",
                    binary_path="",
                    arguments="",
                    working_directory="",
                    is_dashboard_overlay=False,
                    autolaunch=None,
                    autolaunch_config_path=self.vrappconfig_dir,
                    manifest_exists=False,
                    manifest_error="文件不存在",
                )
            ]

        try:
            data = read_json_file(manifest_path, {})
        except SteamVRConfigError as exc:
            return [
                AppEntry(
                    manifest_path=manifest_path,
                    app_key="",
                    name="无法解析的 manifest",
                    description="",
                    launch_type="",
                    binary_path="",
                    arguments="",
                    working_directory="",
                    is_dashboard_overlay=False,
                    autolaunch=None,
                    autolaunch_config_path=self.vrappconfig_dir,
                    manifest_exists=True,
                    manifest_error=str(exc),
                )
            ]

        apps = ensure_list(data.get("applications") if isinstance(data, dict) else None)
        entries: List[AppEntry] = []
        for app in apps:
            if not isinstance(app, dict):
                continue
            app_key = str(app.get("app_key") or "")
            name = localized_string(app.get("strings"), "name", app_key or manifest_path.stem)
            description = localized_string(app.get("strings"), "description", "")
            launch_type = str(app.get("launch_type") or "")
            binary = str(app.get("binary_path_windows") or app.get("binary_path") or "")
            arguments = str(app.get("arguments") or "")
            working_directory = str(app.get("working_directory") or app.get("working_dir") or "")
            autolaunch = self.get_autolaunch(app_key) if app_key else None
            entries.append(
                AppEntry(
                    manifest_path=manifest_path,
                    app_key=app_key,
                    name=name,
                    description=description,
                    launch_type=launch_type,
                    binary_path=binary,
                    arguments=arguments,
                    working_directory=working_directory,
                    is_dashboard_overlay=bool(app.get("is_dashboard_overlay")),
                    autolaunch=autolaunch,
                    autolaunch_config_path=self.autolaunch_config_path(app_key) if app_key else self.vrappconfig_dir,
                    manifest_exists=True,
                )
            )

        if not entries:
            entries.append(
                AppEntry(
                    manifest_path=manifest_path,
                    app_key="",
                    name="空 manifest",
                    description="",
                    launch_type="",
                    binary_path="",
                    arguments="",
                    working_directory="",
                    is_dashboard_overlay=False,
                    autolaunch=None,
                    autolaunch_config_path=self.vrappconfig_dir,
                    manifest_exists=True,
                    manifest_error="没有 applications 条目",
                )
            )
        return entries

    def all_entries(self) -> List[AppEntry]:
        entries: List[AppEntry] = []
        seen_manifest_paths: set[str] = set()
        for manifest_path in self.manifest_paths():
            marker = normalize_for_compare(manifest_path)
            if marker in seen_manifest_paths:
                continue
            seen_manifest_paths.add(marker)
            entries.extend(self.parse_manifest(manifest_path))
        return entries

    def create_manifest_for_program(
        self,
        exe_path: Path,
        display_name: str,
        app_key: str,
        arguments: str = "",
        working_directory: str = "",
        dashboard_overlay: bool = True,
        enable_autolaunch: bool = True,
    ) -> Path:
        exe_path = exe_path.resolve()
        if not exe_path.exists():
            raise SteamVRConfigError(f"程序不存在：{exe_path}")
        if exe_path.suffix.lower() not in {".exe", ".bat", ".cmd", ".com"}:
            raise SteamVRConfigError("请选择 Windows 可启动程序（.exe/.bat/.cmd/.com）。")
        display_name = display_name.strip() or exe_path.stem
        validate_app_key(app_key)

        manifest_dir = generated_manifest_root() / safe_app_key_part(app_key)
        manifest_path = manifest_dir / "app.vrmanifest"
        descriptions = {
            "zh_cn": "由 AlanBacker 制作的 SteamVR 自启动管理器注册。",
            "en_us": "Registered by AlanBacker's SteamVR Autostart Manager.",
            "ja_jp": "AlanBacker 製 SteamVR 自動起動マネージャーによって登録されました。",
            "ko_kr": "AlanBacker가 만든 SteamVR 자동 시작 관리자가 등록했습니다.",
        }
        app_data: Dict[str, Any] = {
            "app_key": app_key,
            "launch_type": "binary",
            "binary_path_windows": str(exe_path),
            "arguments": arguments.strip(),
            "strings": {
                locale: {"name": display_name, "description": description}
                for locale, description in descriptions.items()
            },
        }
        if working_directory.strip():
            app_data["working_directory"] = working_directory.strip()
        if dashboard_overlay:
            app_data["is_dashboard_overlay"] = True

        manifest = {"source": "builtin", "applications": [app_data]}
        write_json_file(manifest_path, manifest)
        self.add_manifest_path(manifest_path)
        self.set_autolaunch(app_key, enable_autolaunch)
        return manifest_path


class AddProgramDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, config: SteamVRConfig, lang: str):
        super().__init__(master)
        self.config = config
        self.lang = lang
        self.result: Optional[Dict[str, Any]] = None
        self.title(self._t("add_dialog_title"))
        if hasattr(master, "_app_icon"):
            self.iconphoto(False, getattr(master, "_app_icon"))
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.exe_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.app_key_var = tk.StringVar()
        self.args_var = tk.StringVar()
        self.cwd_var = tk.StringVar()
        self.overlay_var = tk.BooleanVar(value=True)
        self.autolaunch_var = tk.BooleanVar(value=True)

        self._build()
        self.bind("<Return>", lambda _event: self._submit())
        self.bind("<Escape>", lambda _event: self.destroy())
        self.exe_entry.focus_set()

    def _t(self, key: str, **kwargs: Any) -> str:
        return tr(self.lang, key, **kwargs)

    def _build(self) -> None:
        outer = ttk.Frame(self, padding=18, style="Surface.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(1, weight=1)

        ttk.Label(outer, text=self._t("program_path"), style="Field.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.exe_entry = ttk.Entry(outer, textvariable=self.exe_var, width=58)
        self.exe_entry.grid(row=0, column=1, sticky="ew", pady=(0, 8), padx=(12, 8))
        ttk.Button(outer, text=self._t("browse"), command=self._browse_exe).grid(row=0, column=2, pady=(0, 8))

        ttk.Label(outer, text=self._t("display_name"), style="Field.TLabel").grid(row=1, column=0, sticky="w", pady=8)
        name_entry = ttk.Entry(outer, textvariable=self.name_var, width=58)
        name_entry.grid(row=1, column=1, sticky="ew", pady=8, padx=(12, 8), columnspan=2)
        self.name_var.trace_add("write", self._sync_app_key)

        ttk.Label(outer, text=self._t("app_key"), style="Field.TLabel").grid(row=2, column=0, sticky="w", pady=8)
        ttk.Entry(outer, textvariable=self.app_key_var, width=58).grid(
            row=2, column=1, sticky="ew", pady=8, padx=(12, 8), columnspan=2
        )

        ttk.Label(outer, text=self._t("launch_args"), style="Field.TLabel").grid(row=3, column=0, sticky="w", pady=8)
        ttk.Entry(outer, textvariable=self.args_var, width=58).grid(
            row=3, column=1, sticky="ew", pady=8, padx=(12, 8), columnspan=2
        )

        ttk.Label(outer, text=self._t("working_directory"), style="Field.TLabel").grid(row=4, column=0, sticky="w", pady=8)
        ttk.Entry(outer, textvariable=self.cwd_var, width=58).grid(row=4, column=1, sticky="ew", pady=8, padx=(12, 8))
        ttk.Button(outer, text=self._t("browse"), command=self._browse_cwd).grid(row=4, column=2, pady=8)

        ttk.Checkbutton(
            outer,
            text=self._t("overlay_check"),
            variable=self.overlay_var,
        ).grid(row=5, column=1, sticky="w", pady=(12, 0), padx=(12, 8), columnspan=2)
        ttk.Checkbutton(
            outer,
            text=self._t("autolaunch_check"),
            variable=self.autolaunch_var,
        ).grid(row=6, column=1, sticky="w", pady=(6, 14), padx=(12, 8), columnspan=2)

        button_row = ttk.Frame(outer, style="Surface.TFrame")
        button_row.grid(row=7, column=0, columnspan=3, sticky="e", pady=(10, 0))
        ttk.Button(button_row, text=self._t("cancel"), command=self.destroy).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_row, text=self._t("add"), command=self._submit, style="Accent.TButton").grid(row=0, column=1)

    def _browse_exe(self) -> None:
        filename = filedialog.askopenfilename(
            title=self._t("choose_program"),
            filetypes=[
                (self._t("windows_program"), "*.exe *.bat *.cmd *.com"),
                (self._t("all_files"), "*.*"),
            ],
        )
        if not filename:
            return
        exe_path = Path(filename)
        self.exe_var.set(str(exe_path))
        if not self.name_var.get().strip():
            self.name_var.set(exe_path.stem)
        if not self.cwd_var.get().strip():
            self.cwd_var.set(str(exe_path.parent))
        self._sync_app_key()

    def _browse_cwd(self) -> None:
        directory = filedialog.askdirectory(title=self._t("choose_working_dir"))
        if directory:
            self.cwd_var.set(directory)

    def _sync_app_key(self, *_args: Any) -> None:
        if getattr(self, "_editing_key", False):
            return
        exe = self.exe_var.get().strip()
        name = self.name_var.get().strip()
        if not exe and not name:
            return
        self._editing_key = True
        try:
            self.app_key_var.set(make_app_key(name or Path(exe).stem, Path(exe or name)))
        finally:
            self._editing_key = False

    def _submit(self) -> None:
        try:
            exe_path = Path(self.exe_var.get().strip())
            display_name = self.name_var.get().strip() or exe_path.stem
            app_key = self.app_key_var.get().strip()
            validate_app_key(app_key)
            self.result = {
                "exe_path": exe_path,
                "display_name": display_name,
                "app_key": app_key,
                "arguments": self.args_var.get(),
                "working_directory": self.cwd_var.get(),
                "dashboard_overlay": self.overlay_var.get(),
                "enable_autolaunch": self.autolaunch_var.get(),
            }
        except SteamVRConfigError as exc:
            messagebox.showerror(self._t("app_title"), str(exc), parent=self)
            return
        self.destroy()


class BackupManagerDialog(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        config: SteamVRConfig,
        lang: str,
        status_callback: Any,
        restore_callback: Any,
        open_path_callback: Any,
    ):
        super().__init__(master)
        self.config = config
        self.lang = lang
        self.status_callback = status_callback
        self.restore_callback = restore_callback
        self.open_path_callback = open_path_callback
        self.entries: List[BackupEntry] = []
        self.title(self._t("backup_manager"))
        if hasattr(master, "_app_icon"):
            self.iconphoto(False, getattr(master, "_app_icon"))
        self.configure(bg=COLORS["bg"])
        self.geometry("900x460")
        self.minsize(760, 380)
        self.transient(master)
        self._build()
        self._load_backups()

    def _t(self, key: str, **kwargs: Any) -> str:
        return tr(self.lang, key, **kwargs)

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        outer = ttk.Frame(self, padding=16, style="Root.TFrame")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, minsize=180)
        outer.rowconfigure(1, weight=1)

        ttk.Label(outer, text=self._t("backup_records"), style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))

        columns = ("created", "items", "location")
        self.tree = ttk.Treeview(outer, columns=columns, show="headings", selectmode="browse", style="Modern.Treeview")
        self.tree.heading("created", text=self._t("backup_created_at"))
        self.tree.heading("items", text=self._t("backup_items"))
        self.tree.heading("location", text=self._t("backup_location"))
        self.tree.column("created", width=170, minwidth=150)
        self.tree.column("items", width=90, minwidth=70, anchor="center")
        self.tree.column("location", width=520, minwidth=280)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        self.tree.bind("<Double-1>", lambda _event: self._open_selected())

        scroll = ttk.Scrollbar(outer, orient="vertical", command=self.tree.yview, style="Modern.Vertical.TScrollbar")
        scroll.grid(row=1, column=0, sticky="nse", padx=(0, 12))
        self.tree.configure(yscrollcommand=scroll.set)

        actions = ttk.Frame(outer, padding=12, style="Surface.TFrame")
        actions.grid(row=1, column=1, sticky="nsew")
        actions.columnconfigure(0, weight=1)
        ttk.Button(actions, text=self._t("backup_create"), command=self._create_backup, style="Accent.TButton").grid(row=0, column=0, sticky="ew", pady=(0, 9))
        ttk.Button(actions, text=self._t("backup_restore"), command=self._restore_selected).grid(row=1, column=0, sticky="ew", pady=(0, 9))
        ttk.Button(actions, text=self._t("backup_open"), command=self._open_selected).grid(row=2, column=0, sticky="ew", pady=(0, 9))
        ttk.Button(actions, text=self._t("backup_refresh"), command=self._load_backups).grid(row=3, column=0, sticky="ew", pady=(0, 9))
        ttk.Button(actions, text=self._t("backup_delete"), command=self._delete_selected, style="Danger.TButton").grid(row=4, column=0, sticky="ew", pady=(18, 9))
        ttk.Button(actions, text=self._t("backup_close"), command=self.destroy).grid(row=5, column=0, sticky="ew", pady=(18, 0))

    def _load_backups(self) -> None:
        self.entries = self.config.list_backups()
        self.tree.delete(*self.tree.get_children())
        for index, entry in enumerate(self.entries):
            self.tree.insert("", "end", iid=str(index), values=(entry.created_at, entry.item_count, entry.location))
        if not self.entries:
            self.status_callback(self._t("backup_empty"))

    def _selected_backup(self) -> Optional[BackupEntry]:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(self._t("backup_manager"), self._t("backup_select_one"), parent=self)
            return None
        try:
            return self.entries[int(selection[0])]
        except (ValueError, IndexError):
            messagebox.showinfo(self._t("backup_manager"), self._t("backup_select_one"), parent=self)
            return None

    def _create_backup(self) -> None:
        try:
            backup_dir = self.config.backup_current_config()
            self.status_callback(self._t("status_backup_done", path=backup_dir))
            self._load_backups()
            for index, entry in enumerate(self.entries):
                if normalize_for_compare(entry.path) == normalize_for_compare(backup_dir):
                    self.tree.selection_set(str(index))
                    self.tree.focus(str(index))
                    self.tree.see(str(index))
                    break
        except SteamVRConfigError as exc:
            messagebox.showerror(self._t("backup_manager"), str(exc), parent=self)

    def _restore_selected(self) -> None:
        entry = self._selected_backup()
        if not entry:
            return
        if not messagebox.askyesno(self._t("backup_manager"), self._t("backup_restore_confirm", path=entry.path), parent=self):
            return
        try:
            self.config.restore_backup(entry.path)
            self.restore_callback()
            self.status_callback(self._t("status_backup_restored", path=entry.path))
            self._load_backups()
        except SteamVRConfigError as exc:
            messagebox.showerror(self._t("backup_manager"), str(exc), parent=self)
        except OSError as exc:
            messagebox.showerror(self._t("backup_manager"), str(exc), parent=self)

    def _delete_selected(self) -> None:
        entry = self._selected_backup()
        if not entry:
            return
        if not messagebox.askyesno(self._t("backup_manager"), self._t("backup_delete_confirm", path=entry.path), parent=self):
            return
        try:
            self.config.delete_backup(entry.path)
            self.status_callback(self._t("status_backup_deleted", path=entry.path))
            self._load_backups()
        except SteamVRConfigError as exc:
            messagebox.showerror(self._t("backup_manager"), str(exc), parent=self)
        except OSError as exc:
            messagebox.showerror(self._t("backup_manager"), str(exc), parent=self)

    def _open_selected(self) -> None:
        entry = self._selected_backup()
        if entry:
            self.open_path_callback(entry.path)


class SteamVRManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self._app_icon = create_app_icon(self)
        self.iconphoto(True, self._app_icon)
        self.settings = load_settings()
        self.lang = load_language()
        self.theme_mode = load_theme()
        apply_color_theme(self.theme_mode)
        self.title(self._t("app_title"))
        self.geometry(str(self.settings.get("window_geometry") or "1120x720"))
        self.minsize(980, 620)
        self.configure(bg=COLORS["bg"])
        self.config_model: Optional[SteamVRConfig] = None
        self.entries: List[AppEntry] = []
        self.steam_path_var = tk.StringVar(value=str(self.settings.get("steam_path") or detect_steam_path() or ""))
        self.status_var = tk.StringVar(value=self._t("ready"))
        self.details_var = tk.StringVar(value=self._t("select_app_hint"))
        self.language_var = tk.StringVar(value=LANGUAGES[self.lang])
        self.theme_var = tk.StringVar(value=self._theme_label(self.theme_mode))
        self._configure_styles()
        self._build()
        self._load_from_path()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _t(self, key: str, **kwargs: Any) -> str:
        return tr(self.lang, key, **kwargs)

    def _theme_label(self, theme: str) -> str:
        return self._t(f"theme_{theme}")

    def _theme_labels(self) -> List[str]:
        return [self._theme_label(theme) for theme in THEME_MODES]

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        body_font = ("Microsoft YaHei UI", 10)
        heading_font = ("Microsoft YaHei UI", 10, "bold")
        title_font = ("Microsoft YaHei UI", 20, "bold")
        subtitle_font = ("Microsoft YaHei UI", 10)

        style.configure(".", font=body_font)
        style.configure("Root.TFrame", background=COLORS["bg"])
        style.configure("Header.TFrame", background=COLORS["header"])
        style.configure("Surface.TFrame", background=COLORS["surface"], relief="flat")
        style.configure("SurfaceAlt.TFrame", background=COLORS["surface_alt"], relief="flat")
        style.configure("Title.TLabel", background=COLORS["header"], foreground="#ffffff", font=title_font)
        style.configure("Subtitle.TLabel", background=COLORS["header"], foreground=COLORS["subtitle"], font=subtitle_font)
        style.configure("Section.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=("Microsoft YaHei UI", 12, "bold"))
        style.configure("Field.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=heading_font)
        style.configure("Body.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=body_font)
        style.configure("Muted.TLabel", background=COLORS["surface"], foreground=COLORS["muted"], font=body_font)
        style.configure("Status.TLabel", background=COLORS["bg"], foreground=COLORS["muted"], font=body_font)
        style.configure(
            "TEntry",
            padding=(8, 6),
            fieldbackground=COLORS["tree_bg"],
            foreground=COLORS["text"],
            insertcolor=COLORS["text"],
            bordercolor=COLORS["border"],
        )
        style.configure(
            "TCombobox",
            padding=(8, 5),
            background=COLORS["button"],
            fieldbackground=COLORS["tree_bg"],
            foreground=COLORS["text"],
            selectbackground=COLORS["tree_bg"],
            selectforeground=COLORS["text"],
            bordercolor=COLORS["border"],
            arrowcolor=COLORS["text"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["tree_bg"]), ("!disabled", COLORS["tree_bg"])],
            background=[("readonly", COLORS["button"]), ("active", COLORS["button_hover"])],
            foreground=[("readonly", COLORS["text"]), ("!disabled", COLORS["text"])],
            selectbackground=[("readonly", COLORS["tree_bg"])],
            selectforeground=[("readonly", COLORS["text"])],
            arrowcolor=[("readonly", COLORS["text"]), ("active", COLORS["accent"])],
        )
        style.configure(
            "Header.TCombobox",
            padding=(8, 5),
            background="#0b1220",
            fieldbackground="#0b1220",
            foreground="#ffffff",
            selectbackground="#0b1220",
            selectforeground="#ffffff",
            bordercolor=COLORS["accent"],
            arrowcolor="#ffffff",
        )
        style.map(
            "Header.TCombobox",
            fieldbackground=[("readonly", "#0b1220"), ("!disabled", "#0b1220")],
            background=[("readonly", "#0b1220"), ("active", "#111c2f")],
            foreground=[("readonly", "#ffffff"), ("!disabled", "#ffffff")],
            selectbackground=[("readonly", "#0b1220")],
            selectforeground=[("readonly", "#ffffff")],
            arrowcolor=[("readonly", "#ffffff"), ("active", COLORS["accent"])],
        )
        self.option_add("*TCombobox*Listbox.background", COLORS["tree_bg"])
        self.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
        self.option_add("*TCombobox*Listbox.selectBackground", COLORS["selected"])
        self.option_add("*TCombobox*Listbox.selectForeground", COLORS["text"])
        style.configure("TCheckbutton", background=COLORS["surface"], foreground=COLORS["text"])
        style.map("TCheckbutton", background=[("active", COLORS["surface"])])
        style.configure("TButton", padding=(12, 8), borderwidth=0, background=COLORS["button"], foreground=COLORS["text"])
        style.map("TButton", background=[("active", COLORS["button_hover"]), ("pressed", COLORS["button_pressed"])])
        style.configure("Accent.TButton", padding=(14, 9), borderwidth=0, background=COLORS["accent"], foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", COLORS["accent_hover"]), ("pressed", COLORS["accent_pressed"])], foreground=[("disabled", "#d9f2ef")])
        style.configure("Danger.TButton", padding=(14, 9), borderwidth=0, background=COLORS["danger_surface"], foreground=COLORS["danger_text"])
        style.map("Danger.TButton", background=[("active", COLORS["danger_surface"]), ("pressed", COLORS["danger_surface"])])
        style.configure(
            "Modern.Treeview",
            background=COLORS["tree_bg"],
            fieldbackground=COLORS["tree_bg"],
            foreground=COLORS["text"],
            borderwidth=0,
            rowheight=32,
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=COLORS["tree_heading"],
            foreground=COLORS["text"],
            relief="flat",
            font=heading_font,
            padding=(8, 8),
        )
        style.map("Modern.Treeview", background=[("selected", COLORS["selected"])], foreground=[("selected", COLORS["text"])])
        style.layout(
            "Modern.Vertical.TScrollbar",
            [
                (
                    "Vertical.Scrollbar.trough",
                    {
                        "sticky": "ns",
                        "children": [
                            ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"}),
                        ],
                    },
                )
            ],
        )
        style.configure(
            "Modern.Vertical.TScrollbar",
            gripcount=0,
            width=10,
            relief="flat",
            borderwidth=0,
            background=COLORS["muted"],
            darkcolor=COLORS["muted"],
            lightcolor=COLORS["muted"],
            troughcolor=COLORS["surface_alt"],
            bordercolor=COLORS["surface_alt"],
            arrowcolor=COLORS["surface_alt"],
        )
        style.map(
            "Modern.Vertical.TScrollbar",
            background=[("active", COLORS["accent"]), ("pressed", COLORS["accent"])],
            troughcolor=[("active", COLORS["surface_alt"])],
        )

    def _build(self) -> None:
        self.title(self._t("app_title"))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = tk.Frame(self, bg=COLORS["header"], height=112)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.columnconfigure(0, weight=1)

        title_wrap = tk.Frame(header, bg=COLORS["header"])
        title_wrap.grid(row=0, column=0, sticky="w", padx=24, pady=(20, 8))
        ttk.Label(title_wrap, text=self._t("app_title"), style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(title_wrap, text=self._t("app_subtitle"), style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))

        lang_wrap = tk.Frame(header, bg=COLORS["header"])
        lang_wrap.grid(row=0, column=1, sticky="e", padx=24, pady=(14, 8))
        ttk.Label(lang_wrap, text=self._t("language"), style="Subtitle.TLabel").grid(row=0, column=0, sticky="e", padx=(0, 10))
        self.language_var.set(LANGUAGES[self.lang])
        self.language_combo = ttk.Combobox(
            lang_wrap,
            textvariable=self.language_var,
            values=list(LANGUAGES.values()),
            width=12,
            state="readonly",
            style="Header.TCombobox",
        )
        self.language_combo.grid(row=0, column=1, sticky="e")
        self.language_combo.bind("<<ComboboxSelected>>", self._change_language)
        ttk.Label(lang_wrap, text=self._t("theme"), style="Subtitle.TLabel").grid(row=1, column=0, sticky="e", padx=(0, 10), pady=(8, 0))
        self.theme_var.set(self._theme_label(self.theme_mode))
        self.theme_combo = ttk.Combobox(
            lang_wrap,
            textvariable=self.theme_var,
            values=self._theme_labels(),
            width=12,
            state="readonly",
            style="Header.TCombobox",
        )
        self.theme_combo.grid(row=1, column=1, sticky="e", pady=(8, 0))
        self.theme_combo.bind("<<ComboboxSelected>>", self._change_theme)

        top = ttk.Frame(self, padding=(18, 16), style="Surface.TFrame")
        top.grid(row=1, column=0, sticky="ew", padx=18, pady=(18, 12))
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text=self._t("steam_dir"), style="Field.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.steam_path_var).grid(row=0, column=1, sticky="ew", padx=(14, 10))
        ttk.Button(top, text=self._t("browse"), command=self._browse_steam_dir).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(top, text=self._t("refresh"), command=self._load_from_path, style="Accent.TButton").grid(row=0, column=3)

        main = ttk.Frame(self, padding=(18, 0, 18, 12), style="Root.TFrame")
        main.grid(row=2, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, minsize=220)
        main.rowconfigure(0, weight=1)

        table_card = ttk.Frame(main, padding=14, style="Surface.TFrame")
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        table_card.columnconfigure(0, weight=1)
        table_card.rowconfigure(1, weight=1)
        ttk.Label(table_card, text=self._t("registered_apps"), style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.tree = SmoothAppTable(table_card, self._on_select)
        self.tree.set_columns(
            [
                {"key": "name", "title": self._t("name"), "width": 190},
                {"key": "autolaunch", "title": self._t("autolaunch"), "width": 102, "anchor": "center"},
                {"key": "app_key", "title": self._t("app_key"), "width": 230},
                {"key": "launch_type", "title": self._t("launch_type"), "width": 110, "anchor": "center"},
                {"key": "manifest", "title": self._t("manifest"), "width": 430, "stretch": True},
            ]
        )
        self.tree.grid(row=1, column=0, sticky="nsew")

        actions = ttk.Frame(main, padding=14, style="Surface.TFrame")
        actions.grid(row=0, column=1, sticky="nsew")
        actions.columnconfigure(0, weight=1)
        ttk.Label(actions, text=self._t("actions"), style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))
        ttk.Button(actions, text=self._t("add_program"), command=self._add_program, style="Accent.TButton").grid(row=1, column=0, sticky="ew", pady=(0, 9))
        ttk.Button(actions, text=self._t("enable_autostart"), command=lambda: self._toggle_selected(True)).grid(row=2, column=0, sticky="ew", pady=(0, 9))
        ttk.Button(actions, text=self._t("disable_autostart"), command=lambda: self._toggle_selected(False)).grid(row=3, column=0, sticky="ew", pady=(0, 9))
        ttk.Button(actions, text=self._t("open_manifest"), command=self._open_manifest).grid(row=4, column=0, sticky="ew", pady=(0, 9))
        ttk.Button(actions, text=self._t("open_config_dir"), command=self._open_config_dir).grid(row=5, column=0, sticky="ew", pady=(0, 9))
        ttk.Button(actions, text=self._t("backup_manager"), command=self._backup_current_config).grid(row=6, column=0, sticky="ew", pady=(0, 9))
        ttk.Button(actions, text=self._t("remove_registration"), command=self._remove_selected, style="Danger.TButton").grid(row=7, column=0, sticky="ew", pady=(18, 0))

        detail_frame = ttk.Frame(self, padding=(18, 14), style="Surface.TFrame")
        detail_frame.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 12))
        detail_frame.columnconfigure(0, weight=1)
        ttk.Label(detail_frame, text=self._t("details"), style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(detail_frame, textvariable=self.details_var, justify="left", wraplength=1040, style="Body.TLabel").grid(row=1, column=0, sticky="ew", pady=(8, 0))

        status = ttk.Frame(self, padding=(18, 0, 18, 14), style="Root.TFrame")
        status.grid(row=4, column=0, sticky="ew")
        status.columnconfigure(0, weight=1)
        ttk.Label(status, textvariable=self.status_var, anchor="e", style="Status.TLabel").grid(row=0, column=0, sticky="e")

    def _browse_steam_dir(self) -> None:
        directory = filedialog.askdirectory(title=self._t("choose_steam_dir"))
        if directory:
            self.steam_path_var.set(directory)
            self._load_from_path()

    def _load_from_path(self) -> None:
        steam_path = Path(self.steam_path_var.get().strip())
        if not steam_path:
            self._set_status(self._t("no_steam_dir"))
            return
        try:
            self.config_model = SteamVRConfig(steam_path)
            self.entries = self.config_model.all_entries()
            save_settings({"steam_path": str(steam_path)})
        except SteamVRConfigError as exc:
            messagebox.showerror(self._t("app_title"), str(exc), parent=self)
            self.entries = []

        self._populate_tree()
        if self.config_model:
            self._set_status(self._t("loaded", path=self.config_model.appconfig_path))

    def _populate_tree(self) -> None:
        rows: List[Dict[str, Any]] = []
        for index, entry in enumerate(self.entries):
            if entry.manifest_error:
                autolaunch = self._t("autostart_error")
                color = COLORS["danger"]
            elif entry.autolaunch is True:
                autolaunch = self._t("autostart_on")
                color = "#047857"
            elif entry.autolaunch is False:
                autolaunch = self._t("autostart_off")
                color = "#b45309"
            else:
                autolaunch = self._t("autostart_unset")
                color = COLORS["muted"]
            rows.append(
                {
                    "name": entry.name,
                    "autolaunch": autolaunch,
                    "app_key": entry.app_key,
                    "launch_type": entry.launch_type,
                    "manifest": str(entry.manifest_path),
                    "color": color,
                }
            )
        self.tree.set_rows(rows)
        self.details_var.set(self._t("select_app_hint"))

    def _selected_entry(self) -> Optional[AppEntry]:
        entries = self._selected_entries()
        if not entries:
            return None
        return entries[0]

    def _selected_entries(self, prompt: bool = True) -> List[AppEntry]:
        selection = self.tree.selection()
        if not selection:
            if prompt:
                messagebox.showinfo(self._t("app_title"), self._t("select_an_app"), parent=self)
            return []
        entries: List[AppEntry] = []
        for item_id in selection:
            try:
                entries.append(self.entries[int(item_id)])
            except (ValueError, IndexError):
                continue
        if not entries and prompt:
            messagebox.showinfo(self._t("app_title"), self._t("select_an_app"), parent=self)
            return []
        return entries

    def _on_select(self, _event: Any = None) -> None:
        selection = self.tree.selection()
        if not selection:
            self.details_var.set(self._t("select_app_hint"))
            return
        selected = self._selected_entries(prompt=False)
        if len(selected) > 1:
            preview = "\n".join(f"- {entry.name}" for entry in selected[:8])
            if len(selected) > 8:
                preview += f"\n- ..."
            self.details_var.set(f"{self._t('selected_count', count=len(selected))}\n{preview}")
            return
        if not selected:
            return
        entry = selected[0]
        lines = [
            self._t("detail_name", value=entry.name),
            self._t("detail_app_key", value=entry.app_key or "-"),
            self._t("detail_program", value=entry.binary_path or "-"),
            self._t("detail_args", value=entry.arguments or "-"),
            self._t("detail_cwd", value=entry.working_directory or "-"),
            self._t("detail_manifest", value=entry.manifest_path),
            self._t("detail_autoconfig", value=entry.autolaunch_config_path),
        ]
        if entry.manifest_error:
            lines.append(self._t("detail_problem", value=entry.manifest_error))
        self.details_var.set("\n".join(lines))

    def _select_all_apps(self, _event: tk.Event) -> str:
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children)
            self.tree.focus(children[0])
        return "break"

    def _add_program(self) -> None:
        if not self.config_model:
            messagebox.showerror(self._t("app_title"), self._t("select_steam_first"), parent=self)
            return
        dialog = AddProgramDialog(self, self.config_model, self.lang)
        self.wait_window(dialog)
        if not dialog.result:
            return
        try:
            manifest_path = self.config_model.create_manifest_for_program(**dialog.result)
            self._load_from_path()
            self._set_status(self._t("status_added", path=manifest_path))
        except SteamVRConfigError as exc:
            messagebox.showerror(self._t("app_title"), str(exc), parent=self)

    def _toggle_selected(self, enabled: bool) -> None:
        if not self.config_model:
            return
        selected = self._selected_entries()
        if not selected:
            return
        valid_entries: List[AppEntry] = []
        seen_keys: set[str] = set()
        for entry in selected:
            if entry.app_key and entry.app_key not in seen_keys:
                valid_entries.append(entry)
                seen_keys.add(entry.app_key)
        if not valid_entries:
            message = self._t("no_app_key") if len(selected) == 1 else self._t("no_selected_app_key")
            messagebox.showerror(self._t("app_title"), message, parent=self)
            return
        try:
            for entry in valid_entries:
                self.config_model.set_autolaunch(entry.app_key, enabled)
            self._load_from_path()
            if len(valid_entries) == 1:
                key = "status_enabled" if enabled else "status_disabled"
                self._set_status(self._t(key, name=valid_entries[0].name))
            else:
                key = "status_enabled_many" if enabled else "status_disabled_many"
                self._set_status(self._t(key, count=len(valid_entries)))
        except SteamVRConfigError as exc:
            messagebox.showerror(self._t("app_title"), str(exc), parent=self)

    def _remove_selected(self) -> None:
        if not self.config_model:
            return
        selected = self._selected_entries()
        if not selected:
            return
        default_marker = normalize_for_compare(self.config_model.default_steamapps_manifest)
        removable_manifests: Dict[str, Path] = {}
        default_only = True
        for entry in selected:
            marker = normalize_for_compare(entry.manifest_path)
            if marker == default_marker:
                continue
            default_only = False
            removable_manifests.setdefault(marker, entry.manifest_path)

        if not removable_manifests and default_only:
            messagebox.showinfo(
                self._t("default_manifest_title"),
                self._t("default_manifest_message"),
                parent=self,
            )
            return
        if not removable_manifests:
            messagebox.showinfo(self._t("app_title"), self._t("no_removable_manifest"), parent=self)
            return

        if len(removable_manifests) == 1:
            manifest_path = next(iter(removable_manifests.values()))
            prompt = self._t("remove_prompt", path=manifest_path)
        else:
            prompt = self._t("remove_prompt_many", count=len(removable_manifests))
        if not messagebox.askyesno(self._t("app_title"), prompt, parent=self):
            return
        try:
            for manifest_path in removable_manifests.values():
                self.config_model.remove_manifest_path(manifest_path)
            for item in self.entries:
                if normalize_for_compare(item.manifest_path) not in removable_manifests:
                    continue
                if item.app_key:
                    self.config_model.delete_autolaunch_config(item.app_key)
            self._load_from_path()
            if len(removable_manifests) == 1:
                self._set_status(self._t("status_removed", path=next(iter(removable_manifests.values()))))
            else:
                self._set_status(self._t("status_removed_many", count=len(removable_manifests)))
        except SteamVRConfigError as exc:
            messagebox.showerror(self._t("app_title"), str(exc), parent=self)

    def _backup_current_config(self) -> None:
        if not self.config_model:
            messagebox.showerror(self._t("app_title"), self._t("select_steam_first"), parent=self)
            return
        BackupManagerDialog(
            self,
            self.config_model,
            self.lang,
            self._set_status,
            self._load_from_path,
            self._open_path,
        )

    def _open_config_dir(self) -> None:
        if not self.config_model:
            return
        self._open_path(self.config_model.config_dir)

    def _open_manifest(self) -> None:
        entry = self._selected_entry()
        if entry:
            self._open_path(entry.manifest_path)

    def _open_path(self, path: Path) -> None:
        try:
            if sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                messagebox.showinfo(self._t("app_title"), self._t("path_info", path=path), parent=self)
        except OSError as exc:
            messagebox.showerror(self._t("app_title"), self._t("unable_open", path=path, error=exc), parent=self)

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)
        self._flash_status()

    def _flash_status(self) -> None:
        style = ttk.Style(self)
        style.configure("Status.TLabel", background=COLORS["bg"], foreground=COLORS["accent"])
        self.after(850, lambda: style.configure("Status.TLabel", background=COLORS["bg"], foreground=COLORS["muted"]))

    def _change_language(self, _event: Any = None) -> None:
        selected = self.language_var.get()
        for code, label in LANGUAGES.items():
            if label == selected:
                self.lang = code
                break
        save_language(self.lang)
        self.theme_var.set(self._theme_label(self.theme_mode))
        for child in self.winfo_children():
            child.destroy()
        self.status_var.set(self._t("ready"))
        self.details_var.set(self._t("select_app_hint"))
        self._configure_styles()
        self._build()
        self._populate_tree()

    def _change_theme(self, _event: Any = None) -> None:
        selected = self.theme_var.get()
        for mode in THEME_MODES:
            if self._theme_label(mode) == selected:
                self.theme_mode = mode
                break
        save_theme(self.theme_mode)
        apply_color_theme(self.theme_mode)
        self.configure(bg=COLORS["bg"])
        for child in self.winfo_children():
            child.destroy()
        self._configure_styles()
        self._build()
        self._populate_tree()

    def _on_close(self) -> None:
        save_settings(
            {
                "language": self.lang,
                "theme": self.theme_mode,
                "steam_path": self.steam_path_var.get().strip(),
                "window_geometry": self.geometry(),
            }
        )
        self.destroy()


def main() -> None:
    app = SteamVRManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()

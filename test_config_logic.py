import json
import os
import tempfile
import unittest
from pathlib import Path

from steamvr_autostart_manager import SteamVRConfig, make_app_key


class SteamVRConfigTests(unittest.TestCase):
    def test_create_manifest_and_toggle_autolaunch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_localappdata = os.environ.get("LOCALAPPDATA")
            os.environ["LOCALAPPDATA"] = str(root / "LocalAppData")
            steam = root / "Steam"
            exe = root / "Tool.exe"
            exe.write_text("", encoding="utf-8")

            try:
                config = SteamVRConfig(steam)
                key = make_app_key("Tool", exe)
                manifest_path = config.create_manifest_for_program(
                    exe_path=exe,
                    display_name="Tool",
                    app_key=key,
                    arguments="--demo",
                    working_directory=str(root),
                    dashboard_overlay=True,
                    enable_autolaunch=True,
                )

                appconfig = json.loads((steam / "config" / "appconfig.json").read_text(encoding="utf-8"))
                self.assertIn(str(manifest_path), appconfig["manifest_paths"])

                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                app = manifest["applications"][0]
                self.assertEqual(app["app_key"], key)
                self.assertEqual(app["binary_path_windows"], str(exe.resolve()))
                self.assertEqual(app["arguments"], "--demo")
                self.assertTrue(app["is_dashboard_overlay"])
                self.assertEqual({"zh_cn", "en_us", "ja_jp", "ko_kr"}, set(app["strings"]))
                self.assertIn("AlanBacker", app["strings"]["en_us"]["description"])

                self.assertTrue(config.get_autolaunch(key))
                config.set_autolaunch(key, False)
                self.assertFalse(config.get_autolaunch(key))

                entries = [entry for entry in config.all_entries() if entry.app_key == key]
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0].app_key, key)
                self.assertFalse(entries[0].autolaunch)

                backup_dir = config.backup_current_config()
                self.assertTrue((backup_dir / "appconfig.json").exists())
                self.assertTrue((backup_dir / "vrappconfig" / f"{key}.vrappconfig").exists())
                self.assertTrue(any((backup_dir / "registered_manifests").glob("*.vrmanifest")))
                self.assertTrue((backup_dir / "manifest_index.json").exists())
                self.assertTrue(any(entry.path == backup_dir for entry in config.list_backups()))

                config.remove_manifest_path(manifest_path)
                self.assertEqual(config.manifest_paths(), [steam / "config" / "steamapps.vrmanifest"])

                config.restore_backup(backup_dir)
                restored_appconfig = json.loads((steam / "config" / "appconfig.json").read_text(encoding="utf-8"))
                self.assertIn(str(manifest_path), restored_appconfig["manifest_paths"])

                config.delete_backup(backup_dir)
                self.assertFalse(backup_dir.exists())
            finally:
                if old_localappdata is None:
                    os.environ.pop("LOCALAPPDATA", None)
                else:
                    os.environ["LOCALAPPDATA"] = old_localappdata


if __name__ == "__main__":
    unittest.main()

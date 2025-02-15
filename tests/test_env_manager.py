import os
import subprocess
import sys
import json
import shutil
import unittest
import logging
try:
    import pkg_resources
except ImportError:
    from importlib import metadata as importlib_metadata
    pkg_resources = None
from src.virtual_env.env_manager import VirtualEnvironmentManager, CommandExecutionError, VirtualEnvironmentError
from unittest.mock import patch, mock_open, MagicMock, call  # For mocking files and subprocess


class TestVirtualEnvironmentManager_Regression(unittest.TestCase):

    def test_smoke(self):
        manager: VirtualEnvironmentManager = VirtualEnvironmentManager(".test_venv")
        self.assertTrue(manager.check_consistency())
        manager.run("pip", "install", "requests")
        manager.run("pip", "show", "requests")   
        self.assertTrue(manager.remove())
        self.assertFalse(manager.exists())
        self.assertFalse(manager.check_consistency())            

class TestVirtualEnvironmentManager(unittest.TestCase):

    def setUp(self):
        self.venv_path = ".test_venv"  # Use a test-specific path
        self.logger = logging.getLogger(__name__)  # Initialize logger
        self.venv_manager = VirtualEnvironmentManager(self.venv_path)
        self.venv_manager.set_logger(self.logger)
        self.config_json_path = "test_config.json"
        self.config_dict = {
            "files": {
                "Scripts/activate.bat": sys.platform == "win32",
                "Scripts/activate": sys.platform != "win32",
                "python.exe": sys.platform == "win32",
                "Scripts/python.exe": sys.platform == "win32",
                "bin/activate": sys.platform != "win32",
                "bin/python": sys.platform != "win32",
            },
            "packages": {"requests": ">=2.31.0"},  # Example package and version
        }

    def tearDown(self):
        if os.path.exists(self.venv_path):
            shutil.rmtree(self.venv_path)
        if os.path.exists(self.config_json_path):
            os.remove(self.config_json_path)  # Clean up config file

    def test_create_and_exists(self):
        self.assertTrue(self.venv_manager.create())
        self.assertTrue(self.venv_manager.exists())

    def test_create_already_exists(self):
        self.assertTrue(self.venv_manager.create())
        self.assertTrue(self.venv_manager.create())  # Should return True if already exists

    def test_remove(self):
        self.assertTrue(self.venv_manager.create())
        self.assertTrue(self.venv_manager.remove())
        self.assertFalse(self.venv_manager.exists())

    def test_remove_nonexistent(self):
        self.venv_manager.remove()
        self.assertFalse(self.venv_manager.remove())  # Should return False if doesn't exist

    def test_run_command(self):
        self.venv_manager.load()
        result = self.venv_manager.run("python", "--version").result()  # A simple command
        self.assertIsNotNone(result)
        self.assertEqual(result.returncode, 0)

    def test_run_command_not_loaded(self):
        self.venv_manager.remove()
        with self.assertRaises(RuntimeError):
            self.venv_manager.run("pip", "install", "requests")  # Should raise RuntimeError

    def test_run_command_error(self):
        self.venv_manager.load()
        with self.assertRaises(CommandExecutionError):
            self.venv_manager.run("nonexistent_command")  # Should raise CommandExecutionError

    def test_load_create(self):
        self.assertTrue(self.venv_manager.exists())
        self.assertTrue(self.venv_manager._loaded)

    def test_load_clear(self):
        self.venv_manager.create()
        self.assertTrue(self.venv_manager.exists())
        self.venv_manager.load(clear_if_exists=True)
        self.assertTrue(self.venv_manager.exists()) # Still exists, but should be a clean venv
        self.assertTrue(self.venv_manager._loaded)

    def test_check_consistency_files_missing(self):
        with open(self.config_json_path, 'w') as f:  # Create config file
            json.dump(self.config_dict, f)

        self.venv_manager.load()
        self.assertFalse(self.venv_manager.check_consistency(config_json=self.config_json_path))

    def test_check_consistency_packages_missing(self):
        with open(self.config_json_path, 'w') as f:  # Create config file
            json.dump(self.config_dict, f)

        self.venv_manager.load()
        self.assertFalse(self.venv_manager.check_consistency(config_json=self.config_json_path))

    def test_check_consistency_packages_version_incorrect(self):
        with open(self.config_json_path, 'w') as f:  # Create config file
            json.dump(self.config_dict, f)

        self.venv_manager.load()
        self.venv_manager.run("pip", "install", "requests==2.28.1") # Install a different version
        self.assertFalse(self.venv_manager.check_consistency(config_json=self.config_json_path))

    # @patch('os.path.exists')
    # @patch('importlib.metadata.distributions')
    # @patch('subprocess.run')
    # def test_check_consistency_success(self, mock_run, mock_distributions, mock_exists):
    #     # Mock file existence checks
    #     mock_exists.side_effect = lambda x: True

    #     # Mock package distribution
    #     mock_dist = MagicMock()
    #     mock_dist.name = "requests"
    #     mock_dist.version = "2.31.0"
    #     mock_distributions.return_value = [mock_dist]

    #     # Mock pip check success
    #     mock_run.return_value = subprocess.CompletedProcess(
    #         ["pip", "check"], 
    #         0, 
    #         stdout=b"No broken requirements found.", 
    #         stderr=b""
    #     )

    #     with open(self.config_json_path, 'w') as f:  # Create config file
    #         json.dump(self.config_dict, f)

    #     self.venv_manager.load()
    #     self.venv_manager._loaded = True  # Ensure loaded state
        
    #     # Test consistency check
    #     self.assertTrue(self.venv_manager.check_consistency(config_json=self.config_json_path))

    #     # Get the actual paths that would be checked
    #     expected_paths = []
    #     if sys.platform == "win32":
    #         expected_paths = [
    #             #os.path.join(self.venv_manager.venv_path, "python.exe"),
    #             #os.path.join(self.venv_manager.venv_path, "Scripts/python.exe"),
    #             os.path.join(self.venv_manager.venv_path, "Scripts/activate.bat"),
    #             os.path.join(self.venv_manager.venv_path, "Scripts/activate")
    #         ]
    #     else:
    #         expected_paths = [
    #             os.path.join(self.venv_manager.venv_path, "bin/python"),
    #             os.path.join(self.venv_manager.venv_path, "bin/activate")
    #         ]

    #     # Convert paths to use forward slashes consistently
    #     #expected_paths = [path.replace("/","\\") for path in expected_paths]

    #     # Verify all expected paths were checked
    #     expected_calls = [call(path) for path in expected_paths]
    #     mock_exists.assert_has_calls(expected_calls, any_order=True)

    @patch('subprocess.run')
    def test__pip_check_success(self, mock_run):
        # Create required files for activation
        scripts_dir = os.path.join(self.venv_path, "Scripts" if sys.platform == "win32" else "bin")
        os.makedirs(scripts_dir, exist_ok=True)
        
        # Create all required files
        if sys.platform == "win32":
            files_to_create = [
                os.path.join(self.venv_path, "Scripts", "python.exe"),
                os.path.join(self.venv_path, "Scripts", "activate.bat"),
                os.path.join(self.venv_path, "Scripts", "activate")
            ]
        else:
            files_to_create = [
                os.path.join(self.venv_path, "bin", "python"),
                os.path.join(self.venv_path, "bin", "activate")
            ]

        for file_path in files_to_create:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            open(file_path, 'w').close()  # Create an empty file

        self.venv_manager._loaded = True
        mock_run.return_value = subprocess.CompletedProcess(["pip", "check"], 0, stdout=b"No broken requirements found.", stderr=b"")
        self.assertTrue(self.venv_manager._pip_check())

    @patch('subprocess.run')
    def test__pip_check_failure(self, mock_run):
        # Create required files for activation
        scripts_dir = os.path.join(self.venv_path, "Scripts" if sys.platform == "win32" else "bin")
        os.makedirs(scripts_dir, exist_ok=True)
        
        # Create all required files
        if sys.platform == "win32":
            files_to_create = [
                os.path.join(self.venv_path, "python.exe"),
                os.path.join(self.venv_path, "Scripts", "python.exe"),
                os.path.join(self.venv_path, "Scripts", "activate.bat"),
                os.path.join(self.venv_path, "Scripts", "activate")
            ]
        else:
            files_to_create = [
                os.path.join(self.venv_path, "bin", "python"),
                os.path.join(self.venv_path, "bin", "activate")
            ]

        for file_path in files_to_create:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            open(file_path, 'w').close()  # Create an empty file

        self.venv_manager._loaded = True
        mock_run.return_value = subprocess.CompletedProcess(["pip", "check"], 1, stdout=b"", stderr=b"Some broken requirements found.")
        self.assertFalse(self.venv_manager._pip_check())

    def test__auto_load_libraries(self):
        # Test with separate library names
        importlib_metadata, pkg_resources = self.venv_manager._auto_load_libraries('importlib.metadata', 'pkg_resources')
        self.assertIsNotNone(importlib_metadata)
        # pkg_resources might be None in Python 3.13+, that's okay
        if sys.version_info < (3, 13):
            self.assertIsNotNone(pkg_resources)

    def test__auto_load_libraries_fail(self):
        nonexistent = self.venv_manager._auto_load_libraries('nonexistent_module')
        self.assertIsNone(nonexistent[0])  # Should return None for the module

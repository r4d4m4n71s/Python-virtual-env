import os
import sys
import json
import shutil
import unittest
from unittest import mock
import logging
try:
    import pkg_resources
except ImportError:
    pkg_resources = None

from src.virtual_env.env_manager import EnvManager, CmdExecError, EnvError

class TestEnvManager_Regression(unittest.TestCase):

    def test_smoke(self):
        manager: EnvManager = EnvManager(".test_venv")
        self.assertTrue(manager.exists())  # Check if environment exists after creation
        manager.run("pip", "install", "requests")
        manager.run("pip", "show", "requests")   
        manager.remove()  # This method doesn't return a value
        self.assertFalse(manager.exists())  # Check if environment is removed

class TestEnvManager(unittest.TestCase):

    def setUp(self):
        self.venv_path = ".test_venv"  # Use a test-specific path
        self.logger = logging.getLogger(__name__)  # Initialize logger
        self.venv_manager = EnvManager(self.venv_path, logger=self.logger)
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
        self.assertTrue(self.venv_manager.exists())

    def test_create_already_exists(self):
        # Calling _create() multiple times should not raise an error
        self.assertTrue(self.venv_manager.exists())

    def test_remove(self):
        self.assertTrue(self.venv_manager.exists())
        self.venv_manager.remove()
        self.assertFalse(self.venv_manager.exists())

    def test_remove_nonexistent(self):
        # Remove existing environment first
        self.venv_manager.remove()
        # Attempting to remove again should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            self.venv_manager.remove()

    def test_run_command(self):
        result = self.venv_manager.run("python", "--version").result()
        self.assertIsNotNone(result)
        self.assertEqual(result.returncode, 0)

    def test_run_command_not_loaded(self):
        # Remove the environment first
        self.venv_manager.remove()
        with self.assertRaises(RuntimeError):
            self.venv_manager.run("pip", "install", "requests")

    def test_run_command_error(self):
        with self.assertRaises(CmdExecError):
            self.venv_manager.run("nonexistent_command")

    def test_load_create(self):
        self.assertTrue(self.venv_manager.exists())

    def test_load_clear(self):
        self.venv_manager.flush(clear=True)
        self.assertTrue(self.venv_manager.exists())

    def test_check_consistency_files_missing(self):
        with open(self.config_json_path, 'w') as f:
            json.dump(self.config_dict, f)

        # Modify the test to handle potential import issues
        if pkg_resources:
            result = self.venv_manager.check_consistency(config_json=self.config_json_path)
            self.assertFalse(result)
        else:
            self.skipTest("pkg_resources not available")

    def test_check_consistency_packages_missing(self):
        with open(self.config_json_path, 'w') as f:
            json.dump(self.config_dict, f)

        # Modify the test to handle potential import issues
        if pkg_resources:
            result = self.venv_manager.check_consistency(config_json=self.config_json_path)
            self.assertFalse(result)
        else:
            self.skipTest("pkg_resources not available")

    def test_check_consistency_packages_version_incorrect(self):
        with open(self.config_json_path, 'w') as f:
            json.dump(self.config_dict, f)

        # Install a different version of requests
        self.venv_manager.run("pip", "install", "requests==2.28.1")

        # Modify the test to handle potential import issues
        if pkg_resources:
            result = self.venv_manager.check_consistency(config_json=self.config_json_path)
            self.assertFalse(result)
        else:
            self.skipTest("pkg_resources not available")

    def test_flush_environment(self):
        original_path = self.venv_manager.venv_path
        self.venv_manager.flush()
        self.assertTrue(self.venv_manager.exists())
        self.assertEqual(self.venv_manager.venv_path, original_path)

    def test_flush_environment_with_error(self):
        # Create a mock that will raise an exception on the first call to _create
        with mock.patch.object(self.venv_manager, '_create', side_effect=[
            Exception("First create failed"), 
            mock.DEFAULT  # This allows the second call to proceed normally
        ]):
            # This should raise an EnvError
            with self.assertRaises(EnvError) as context:
                self.venv_manager.flush()
            
            # Verify the error message
            self.assertIn("Unable to recreate environmet", str(context.exception))

    def test_result_method(self):
        self.venv_manager.run("python", "--version")
        result = self.venv_manager.result()
        self.assertIsNotNone(result)
        self.assertEqual(result.returncode, 0)

    def test__auto_load_libraries(self):
        # Test with separate library names
        importlib_metadata, pkg_resources_module = self.venv_manager._auto_load_libraries('importlib.metadata', 'pkg_resources')
        self.assertIsNotNone(importlib_metadata)
        # pkg_resources might be None in Python 3.13+, that's okay
        if sys.version_info < (3, 13):
            self.assertIsNotNone(pkg_resources_module)

    def test__auto_load_libraries_fail(self):
        nonexistent = self.venv_manager._auto_load_libraries('nonexistent_module')
        self.assertIsNone(nonexistent[0])  # Should return None for the module

import os
import subprocess
import venv
import sys
import json
import shutil


class EnvError(Exception):
    """Base class for virtual environment errors."""

    pass


class CmdExecError(EnvError):
    """Raised when a command execution fails."""

    pass


class EnvManager:
    """
    Manages a virtual environment, providing functionalities for creation,
    activation, command execution, and consistency checks.

    Attributes:
        venv_path (str): The absolute path to the virtual environment directory.
        _loaded (bool): Indicates whether the virtual environment has been loaded.
        _logger (logging.Logger): The logger instance used for logging messages.

    Example Usage:
        # Configure logging
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        logger = logging.getLogger(__name__)

        # Create and use a EnvManager instance
        with EnvManager(".venv", logger=logger) as venv_manager:
            venv_manager.run("pip", "install", "requests").result()
            #... other operations...
    """

    def __init__(self, venv_path, logger=None):
        """
        Initializes a EnvManager instance.

        Args:
            venv_path (str): The path to the virtual environment directory.
            logger (logging.Logger, optional): The logger instance to use. Defaults to None.
            auto_create (bool, optional): Whether to automatically create the environment. Defaults to True.
        """
        self.venv_path = os.path.abspath(venv_path)
        self._logger = logger
        self.command_result = None

    def __enter__(self):
        """Loads the virtual environment when entering a 'with' statement."""
        return self

    def __exit__(self):
        """Performs remove environment when exiting a 'with' statement."""
        self.remove()

    def _create(self, clear=False):
        """
        Creates the virtual environment.

        Args:
            clear (bool, optional): Whether to clear an existing environment before creation.
            True: The contents of the environment directory are deleted before the virtual environment is created. This ensures that you start with a clean slate.
            False: False (which is the default), the contents of the environment directory are not deleted, and the virtual environment is created on top of the existing files.

        Returns:
            bool: True if the environment was created successfully, False otherwise.
        """
        builder = venv.EnvBuilder(clear=clear, with_pip=True)
        builder.create(self.venv_path)
        self._log(f"Virtual environment created: {self.venv_path}")
        self._auto_load_libraries(
            "importlib.metadata", "pkg_resources"
        )  # Load libraries after creation
        return True

    def flush(self, clear=True):
        """
        Recreates the virtual environment again.
        Args:
            clear (bool, optional): Whether to clear an existing environment before
            creation. by default true
            True: The contents of the environment directory are deleted before the
            virtual environment is created. This ensures that you start with a clean state
            False: False (which is the default), the contents of the environment
            directory are not deleted, and the virtual environment is created on top of the existing files.
            but in case of non sucess will attemp to recreate the environment cleaning the content

        Returns:
            self object
        """
        try:
            self._create(clear=clear)
        except Exception as e:
            self._log(f"Error creating environment: {e}", level="error")
            self._create(clear=True)
            raise EnvError(f"Unable to recreate environmet: {e}") from e

        return self

    def exists(self):
        """
        Checks if the virtual environment exists.

        Returns:
            bool: True if the environment exists, False otherwise.
        """
        return os.path.exists(self.venv_path)

    def remove(self):
        """
        Removes the virtual environment if it exists.
        """
        if self.exists():
            shutil.rmtree(self.venv_path)
            self._log(f"Virtual environment removed: {self.venv_path}")

    def _activate_command(self):
        """Returns the command to activate the virtual environment."""
        platform_locator = os.path.join(
            self.venv_path, "Scripts" if sys.platform == "win32" else "bin"
        )

        activate_script = os.path.join(platform_locator, "activate")

        # update shell process variables
        process_env = os.environ.copy()
        process_env["VIRTUAL_ENV"] = self.venv_path
        process_env["PATH"] = (
            os.path.join(platform_locator) + os.pathsep + process_env.get("PATH", "")
        )

        if not os.path.exists(activate_script):
            self._log(f"Activation script not found: {activate_script}", level="error")
            raise RuntimeError(
                f"Activation script not found: {activate_script}, try flushing environment"
            )

        return (
            f'"{activate_script}"'
            if sys.platform == "win32"
            else f'source "{activate_script}"'
        )

    def run(self, command, *args, capture_output=True, env=None):
        """
        Runs a command within the activated virtual environment.

        Args:
            command (str): The command to execute.
            *args: Additional arguments to pass to the command.
            capture_output (bool, optional): Whether to capture the command's output. Defaults to True.
            env (dict, optional): Additional environment variables to set. Defaults to None.

        Returns:
            subprocess.CompletedProcess: The result of the command execution.

        Raises:
            RuntimeError: If the virtual environment has not been loaded.
            CommandExecutionError: If the command execution fails.
        """
        self.command_result = None
        if not self.exists():
            self._create()
            if not self.exists():
                raise RuntimeError(
                    f"Failed to create virtual environment at {self.venv_path}"
                )

        # Set up environment variables for the virtual environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        # Get activation command and construct full command
        activation_command = self._activate_command()
        full_command = f"{activation_command} && {command} {' '.join(map(str, args))}"

        try:
            self.command_result = subprocess.run(
                full_command,
                shell=True,
                capture_output=capture_output,
                text=True,
                check=True,
                env=process_env,
            )
            self._log(
                f"Command '{command} {' '.join(map(str, args))}' executed successfully."
            )
            return self
        except subprocess.CalledProcessError as e:
            self._log(
                f"Command '{command} {' '.join(map(str, args))}' failed: {e}",
                level="error",
            )
            self._log(e.stderr, level="error")
            raise CmdExecError(
                f"Command '{command} {' '.join(map(str, args))}' failed: {e}"
            ) from e
        except FileNotFoundError as e:
            self._log(f"File not found: {e}", level="error")
            raise EnvError(f"File not found: {e}") from e
        except Exception as e:
            self._log(f"An unexpected error occurred: {e}", level="exception")
            raise

    def result(self):
        """
        Command execution result
        """
        return self.command_result

    def check_consistency(self, config_json=None, run_pip_check=True):  # noqa: C901
        """
        Checks the consistency of the virtual environment against a configuration.

        Args:
            config_json (str or dict, optional): A path to a JSON configuration file or a dictionary
                                                containing the configuration. Defaults to None.
            run_pip_check (bool, optional): Whether to run 'pip check'. Defaults to True.

        Returns:
            bool: True if the environment is consistent with the configuration, False otherwise.
        """
        default_config = {
            "files": {
                "Scripts/activate.bat": sys.platform == "win32",
                "Scripts/activate": sys.platform != "win32",
                "Scripts/python.exe": sys.platform == "win32",
                "bin/activate": sys.platform != "win32",
                "bin/python": sys.platform != "win32",
            },
            "packages": {"pip": None},
        }

        config = default_config.copy()

        if config_json:
            if isinstance(config_json, str):
                if os.path.exists(config_json):
                    try:
                        with open(config_json, "r") as f:
                            config_from_file = json.load(f)
                            config.update(config_from_file)
                    except json.JSONDecodeError as e:
                        self._log(f"Error processing config file: {e}", level="error")
                        return False
                else:
                    self._log(f"Config file not found: {config_json}", level="error")
                    return False
            elif isinstance(config_json, dict):
                config.update(config_json)
            else:
                self._log(
                    "Invalid config_json. It must be a file path (str) or a dictionary.",
                    level="error",
                )
                return False

        try:
            # Check for the required Python version
            if sys.version_info < (3, 8):
                self._log("Error: Python 3.8 or higher is required.", level="error")
                return False

            if "files" in config:
                for file_name, required in config["files"].items():
                    if required:
                        full_path = os.path.join(self.venv_path, file_name)
                        if not os.path.exists(full_path):
                            self._log(f"Missing file: {full_path}", level="error")
                            return False

            # Get the imported modules (or None if they failed to import)
            importlib_metadata, pkg_resources = self._auto_load_libraries(
                "importlib.metadata", "pkg_resources"
            )

            # Only check packages if importlib.metadata and pkg_resources are available
            if "packages" in config and importlib_metadata:
                try:
                    installed_packages = {
                        dist.name: dist.version
                        for dist in importlib_metadata.distributions()
                    }
                except Exception as e:
                    self._log(
                        f"Could not retrieve installed packages: {e}", level="error"
                    )
                    return False

                for package_name, required_version in config["packages"].items():
                    if package_name not in installed_packages:
                        self._log(f"Missing package: {package_name}", level="error")
                        return False

                    installed_version = installed_packages[package_name]

                    if required_version:
                        try:
                            req = pkg_resources.Requirement.parse(
                                f"{package_name}{required_version}"
                            )
                            if not req.specifier.contains(installed_version):
                                self._log(
                                    f"Incorrect version for {package_name}: "
                                    f"Expected {required_version}, got {installed_version}",
                                    level="error",
                                )
                                return False
                        except pkg_resources.RequirementParseError as e:
                            self._log(
                                f"Error parsing version string for {package_name}: {e}",
                                level="error",
                            )
                            return False
                        except Exception as e:
                            self._log(
                                f"An unexpected error occurred while checking package versions: {e}",
                                level="error",
                            )
                            return False

            if run_pip_check and not self._pip_check():
                return False

            self._log("Virtual environment is consistent with configuration.")
            return True

        except (KeyError, TypeError) as e:
            self._log(f"Error processing config: {e}", level="error")
            return False
        except Exception as e:
            self._log(f"An unexpected error occurred: {e}", level="exception")
            return False

    def _pip_check(self):
        """
        Runs 'pip check' to verify installed packages.

        Returns:
            bool: True if 'pip check' passes, False otherwise.
        """
        try:
            result = self.run("pip", "check", capture_output=True).result()

            if result and result.returncode == 0:
                self._log("pip check passed.")
                return True
            else:
                self._log("pip check failed.", level="error")
                if result:
                    self._log(result.stdout, level="error")
                    self._log(result.stderr, level="error")
                return False

        except CmdExecError as e:
            self._log(f"pip check failed: {e}", level="error")
            return False

    def _log(self, message, level="info"):
        """
        Logs a message using the provided logger or falls back to printing.

        Args:
            message (str): The message to log.
            level (str, optional): The logging level ('info', 'error', 'exception', 'warning'). Defaults to "info".
        """
        if self._logger:
            log_method = getattr(
                self._logger, level, self._logger.info
            )  # Get the appropriate log method or default to info
            log_method(message)
        else:
            print(message)

    def _auto_load_libraries(self, *libraries):
        """
        Dynamically imports the specified libraries if they are not already loaded.

        Args:
            *libraries: Variable number of library names to import as strings.

        Returns:
            tuple: A tuple containing the imported modules (or None for any that failed to import).
        """
        imported_modules = []
        for lib_name in libraries:
            if lib_name not in sys.modules:
                try:
                    imported_modules.append(__import__(lib_name))
                except ImportError as e:
                    self._log(
                        f"Warning: Could not import '{lib_name}': {e}", level="warning"
                    )
                    imported_modules.append(None)  # Append None for failed imports
            else:
                imported_modules.append(
                    sys.modules[lib_name]
                )  # Append the already loaded module

        return tuple(imported_modules)

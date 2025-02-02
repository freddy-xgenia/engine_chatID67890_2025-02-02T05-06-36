#plugin_manager.py
# DO NOT DELETE THIS!!!
import types
import urllib.request
import importlib.util
import os
import logging
from typing import Dict

from maths_engine.plugins.base_plugin import BasePlugin

# Set up the logger
logger = logging.getLogger(__name__)


class PluginManager:

    def __init__(self, config=None, state_manager=None, plugin_directory=None):
        if plugin_directory is None:
            plugin_directory = os.path.join(os.getcwd(), "maths_engine", "plugins")

        self.config = config
        self.plugin_directory = plugin_directory
        self.plugins: Dict[str, BasePlugin] = {}  # Holds loaded plugin instances
        self.state_manager = state_manager
        self.user_sandbox = {}  # Holds user-specific namespaces for plugins

    def _generate_user_namespace(self, user_id):
        """Create a unique sandboxed namespace for each user."""
        namespace = types.ModuleType(f"user_{user_id}_namespace")
        namespace.__dict__.update({
            "config": self.config,
            "state_manager":
            self.state_manager,  # Inject common config and state
        })
        return namespace

    def load_plugin_from_url(self, plugin_url, plugin_name):
        try:
            plugin_path = f"/tmp/{plugin_name}.py"
            urllib.request.urlretrieve(plugin_url, plugin_path)
            # logger.info(f"Plugin downloaded to {plugin_path}.")

            if not os.path.exists(plugin_path):
                logger.error(f"Plugin file {plugin_path} does not exist.")

            # Load the plugin as a module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)
            # logger.info(f"Plugin module {plugin_name} loaded successfully.")

            if hasattr(plugin_module, 'init_plugin'):
                return plugin_module.init_plugin
            else:
                raise Exception(f"No init_plugin method found in {plugin_name}")
        except Exception as e:
            logger.error(f"Failed to load plugin from URL {plugin_url}: {str(e)}")
            return None
            
    def has_pending_actions(self):
        """Check if any plugin has pending actions."""
        for plugin in self.plugins.values():
            if plugin.get_actions():  # Assumes plugins have a get_actions method to list pending actions
                return True
        return False

    def get_pending_actions(self):
        """Retrieve the list of pending actions from plugins."""
        pending = {}
        for plugin_name, plugin in self.plugins.items():
            actions = plugin.get_actions()
            if actions:
                pending[plugin_name] = actions
        return pending

    
    def before_spin(self):
        """Call the before_spin method on all loaded plugins."""
        for plugin_name, plugin_instance in self.plugins.items():
            try:
                plugin_instance.before_spin()
            except Exception as e:
                logger.error(
                    f"Error in before_spin of plugin {plugin_name}: {str(e)}")

    def after_spin(self):
        """Call the after_spin method on all loaded plugins."""
        for plugin_name, plugin_instance in self.plugins.items():
            try:
                plugin_instance.after_spin()
            except Exception as e:
                logger.error(
                    f"Error in after_spin of plugin {plugin_name}: {str(e)}")


    def load_plugins(self, plugins_with_params, user_id=None):
        """Load plugins for a specific user or session."""
        if self.config is None:
            logger.error("Configuration not provided. Plugins cannot be loaded.")
            return

        plugin_files = [
            f[:-3] for f in os.listdir(self.plugin_directory)
            if f.endswith(".py") and not f.startswith("__")
        ]

        user_namespace = self._generate_user_namespace(user_id) if user_id else None

        for plugin_name, plugin_params in plugins_with_params.items():
            # Check if plugin_name is a URL, if so, download and load it
            if plugin_params.get('url'):
                plugin_url = plugin_params['url']
                plugin_func = self.load_plugin_from_url(plugin_url, plugin_name)
                if plugin_func:
                    # Remove the 'url' key from plugin_params before passing them to init_plugin
                    plugin_params_cleaned = {k: v for k, v in plugin_params.items() if k != 'url'}

                    plugin = plugin_func(self.config, self.state_manager, **plugin_params_cleaned)
                    self.plugins[plugin_name] = plugin
                    # logger.info(f"Plugin {plugin_name} loaded successfully from URL.")
                continue

            if plugin_name in plugin_files:
                module_name = f"maths_engine.plugins.{plugin_name}"
                try:
                    # Dynamically import the plugin module
                    module = importlib.import_module(module_name)

                    if hasattr(module, "init_plugin"):
                        # Use user-specific namespace if available
                        if user_namespace:
                            exec(f"import {module_name}", user_namespace.__dict__)

                        plugin_params_cleaned = {k: v for k, v in plugin_params.items() if k != 'url'}

                        plugin = module.init_plugin(self.config, self.state_manager, **plugin_params_cleaned)
                        self.plugins[plugin_name] = plugin
                        # logger.info(f"Plugin {plugin_name} loaded successfully.")
                    else:
                        logger.warning(f"Plugin {plugin_name} does not have an init_plugin method.")
                except ImportError as e:
                    logger.error(f"Error loading plugin {plugin_name}: {str(e)}")
                except TypeError as e:
                    logger.error(f"Error initializing plugin {plugin_name}: {str(e)}")
            else:
                logger.warning(f"Plugin {plugin_name} not found.")

    def unload_plugins(self, user_id=None):
        """Unload and delete plugins for a specific user."""
        if not user_id:
            logger.error("User ID not provided. Cannot unload plugins.")
            return

        user_namespace_key = f"user_{user_id}_namespace"

        if user_namespace_key in self.user_sandbox:
            # Unload user-specific plugins
            loaded_plugins = self.plugins.copy(
            )  # Copy to avoid runtime modification issues

            for plugin_name, plugin_instance in loaded_plugins.items():
                # Check if plugin belongs to the specific user
                if plugin_instance.config.user_id == user_id:  # Assuming plugins have user_id stored in their config
                    del self.plugins[plugin_name]
                    # logger.info(
                    #     f"Plugin {plugin_name} for user {user_id} unloaded.")

                    # Remove the plugin file from the plugin directory
                    plugin_path = os.path.join(self.plugin_directory,
                                               f"{plugin_name}.py")
                    if os.path.exists(plugin_path):
                        os.remove(plugin_path)
                        # logger.info(
                        #     f"Plugin file {plugin_path} for user {user_id} removed."
                        # )

            # Clean up user-specific namespace
            del self.user_sandbox[user_namespace_key]
        else:
            logger.warning(f"No plugins loaded for user {user_id}.")

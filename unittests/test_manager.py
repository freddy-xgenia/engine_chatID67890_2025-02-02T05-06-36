import re
import importlib

class TestManager:
    def __init__(self, test_names=None):
        self.modules = []
        self.test_names = test_names or [
            'isaac_rng_test',
        ]
    def load_tests(self):
        for test_name in self.test_names:
            try:
                module_name = f"unittests.{test_name}"
                module = importlib.import_module(module_name)

                if hasattr(module, 'run_test'):
                    self.modules.append(module)
                    print(f"Loaded test {test_name}")
                else:
                    print(f"Module {module_name} does not have 'run_test'")
            except ModuleNotFoundError as e:
                print(f"Error loading test {test_name}: {str(e)}")

    def list_tests(self):
        print(self.modules)
        tests = []
        for module in self.modules:
            module_string = str(module)
            match = re.search(r"<module '(.*?)' from", module_string)
            if match:
                module_name = match.group(1)
                test_name = module_name.split('.')[-1]
                tests.append(test_name)
        return tests

    def run_tests(self):
        results = {}
        for module in self.modules:
            match = re.search(r"<module '(.*?)' from", str(module))
            if not match:
                continue

            module_name = match.group(1)
            test_name = module_name.split('.')[-1]
            results[test_name] = module.run_test()
            
        return results
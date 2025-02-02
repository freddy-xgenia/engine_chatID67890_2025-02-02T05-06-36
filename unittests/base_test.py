from abc import ABC, abstractmethod

class BaseTest(ABC):
    @abstractmethod
    async def run_test(self, simulation):
        """
        Run the test on the provided simulation instance.

        :param simulation: An instance of the Simulation class
        :return: A dictionary containing the test results
        """
        pass

import importlib
import unittest


class PackageLayoutTest(unittest.TestCase):
    def test_sonder_package_imports(self):
        package = importlib.import_module("sonder")

        self.assertEqual(package.__name__, "sonder")

    def test_cli_entrypoint_exists(self):
        cli = importlib.import_module("sonder.transports.cli")

        self.assertTrue(callable(cli.main))

    def test_gateway_entrypoint_exists(self):
        gateway = importlib.import_module("sonder.gateway.app")

        self.assertTrue(callable(gateway.main))


if __name__ == "__main__":
    unittest.main()

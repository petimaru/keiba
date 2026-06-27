from __future__ import annotations

import unittest

from app.dependencies import missing_runtime_dependencies


class DependenciesTest(unittest.TestCase):
    def test_dependency_checker_returns_tuple(self) -> None:
        self.assertIsInstance(missing_runtime_dependencies(), tuple)


if __name__ == "__main__":
    unittest.main()

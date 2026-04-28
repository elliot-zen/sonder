import unittest

from sonder.storage.memory import MemorySessionStore


class MemorySessionStoreTest(unittest.TestCase):
    def test_creates_independent_sessions(self):
        store = MemorySessionStore()

        first = store.get("first")
        second = store.get("second")
        first.append(type(first[0])(role="user", content="hello"))

        self.assertEqual(second[0].role, "system")
        self.assertEqual(second[0].content, "你是一个有用的助手")


if __name__ == "__main__":
    unittest.main()

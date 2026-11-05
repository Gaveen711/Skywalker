import tempfile
import unittest
from pathlib import Path

from skywalker.domain.ai import ChatMessage
from skywalker.infrastructure.conversation_store import ConversationStore


class ConversationStoreTests(unittest.TestCase):
    def test_messages_survive_reopen_and_delete_cascades(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "history.sqlite3"
            store = ConversationStore(path)
            identifier = store.create("A saved conversation")
            messages = [ChatMessage("user", "What's next?"), ChatMessage("assistant", "Hello 👋")]
            for message in messages:
                store.append(identifier, message)
            reopened = ConversationStore(path)
            self.assertEqual(reopened.load(identifier), messages)
            self.assertEqual(reopened.list_conversations(), [(identifier, "A saved conversation")])
            reopened.delete(identifier)
            self.assertEqual(reopened.load(identifier), [])
            self.assertEqual(reopened.list_conversations(), [])

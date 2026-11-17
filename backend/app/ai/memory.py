class ConversationMemory:
    def __init__(self, limit: int = 8) -> None:
        self.limit = limit
        self._items: dict[str, list[dict]] = {}

    def _key(self, user_id: int, session_id: str) -> str:
        return f"{user_id}:{session_id}"

    def history(self, user_id: int, session_id: str) -> list[dict]:
        return list(self._items.get(self._key(user_id, session_id), []))

    def add(self, user_id: int, session_id: str, role: str, content: str) -> None:
        key = self._key(user_id, session_id)
        bucket = self._items.setdefault(key, [])
        bucket.append({"role": role, "content": content[:2000]})
        self._items[key] = bucket[-self.limit :]


memory = ConversationMemory()

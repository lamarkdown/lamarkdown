class MockCache(dict):
    def set(self, key, value, **kwargs):
        self[key] = value

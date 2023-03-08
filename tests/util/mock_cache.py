class MockCache(dict):
    def __init__(self, store: bool = True):
        self.store = store
        self._set_calls = []

    def set(self, key, value, **kwargs):
        '''Mimicks the interface of diskcache's set().'''
        self[key] = value

    def __setitem__(self, key, value):
        self._set_calls.append((key, value))
        if self.store:
            super().__setitem__(key, value)

    @property
    def set_calls(self):
        return self._set_calls

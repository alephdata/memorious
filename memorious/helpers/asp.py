

class ViewForm(dict):
    """Helper for VIEWSTATE in ASP-driven web sites."""

    def __init__(self, element=None, data=None):
        if data is not None:
            self.update(data)
        self.element = element
        for inp in element.findall('.//input'):
            name = inp.get('name')
            if name is None:
                continue
            self[name] = inp.get('value', '')

    def clear(self, name):
        self.pop(name, None)

    @classmethod
    def from_result(cls, result):
        return cls(element=result.html)

from abc import abstractmethod, ABC
from typing import Dict, Optional, Any, List, Union, Callable


def _flat_2_text(features: Dict):
    def _kv_2_str(k, v):
        if isinstance(v, str):
            return f'{k}={v}'
        elif isinstance(v, list):
            raise NotImplementedError()
        else:
            return f'{k}:{v}'
    return ' '.join(map(lambda kv: _kv_2_str(kv[0], kv[1]), features.items()))


class Features:
    def __init__(self, impl):
        self.impl = impl

    @staticmethod
    def _namespaces(d, key: str = '', result: Optional[dict] = None) -> Dict[str, Dict[str, Any]]:
        result = result or {}
        if isinstance(d, Dict):
            for k, v in d.items():
                if isinstance(v, Dict):
                    result = Features._namespaces(v, k, result)
                else:
                    if key not in result:
                        result[key] = {}
                    result[key][k] = v
        if isinstance(d, List):
            raise NotImplementedError()
        return result

    @property
    def namespaces(self):
        return Features._namespaces(self.impl)

    @property
    def txt(self):
        return '|'.join(f'{k} {_flat_2_text(v)} 'for k, v in self.namespaces.items())


class Example(ABC):
    def __init__(self, features, label):
        self.features = Features(features)
        self.label = label

    @property
    @abstractmethod
    def txt(self) -> List[str]:
        ...

    @property
    @abstractmethod
    def dsjson(self) -> str:
        ...


class FeatureFactory:
    def __init__(self, impl):
        self._impl = impl

    @staticmethod
    def _eval(d: Union[Dict, List], i):
        if isinstance(d, Dict):
            result = {}
            for k, v in d.items():
                if isinstance(v, Dict) or isinstance(v, List):
                    result[k] = FeatureFactory._eval(v, i)
                elif isinstance(v, Callable):
                    result[k] = v(i)
                else:
                    result[k] = v
            return result
        if isinstance(d, List):
            result = []
            for v in d:
                if isinstance(v, Dict) or isinstance(v, List):
                    result.append(FeatureFactory._eval(v, i))
                elif isinstance(v, Callable):
                    result.append(v(i))
                else:
                    result.append(v)
            return result
        raise ValueError(f'Unsupported type for the object: {type(d)}')

    def get(self, i):
        return FeatureFactory._eval(self._impl, i)


class ExampleFactory:
    def __init__(self, features, label, example_type):
        self._fg = FeatureFactory(features)
        self._lg = label
        self._et = example_type

    def get(self, i):
        features = self._fg.get(i)
        return self._et(features, self._lg(features, i))

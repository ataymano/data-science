import cb.dsjson.filters as filters
import json
import pandas as pd

# +
def json_load(line):
    try:
        return json.loads(line)
    except:
        return json.loads(line.replace('\x01', ''))

class Predictor: 
    filters = [filters.is_decision]
    
    baselines = {
        'random': lambda obj: 1 / len(obj['a']),
        'baseline1': lambda obj: int(obj['_labelIndex'] == 0)
    }

    def __init__(self, filters = None, baselines = None):
        self.filters = filters if filters is not None else self.filters
        self.baselines = baselines if baselines is not None else self.baselines

    def _decision_2_prediction(self, line, result):
        parsed = json_load(line)
        result['a'].append(parsed['_labelIndex'])         
        result['p'].append(parsed['_label_probability'])
        result['r'].append(-parsed['_label_cost'])

        result['t'].append(pd.to_datetime(parsed['Timestamp']))
        result['n'].append(1 if 'pdrop' not in parsed else 1 / (1 - parsed['pdrop']))

        for baseline_name, baseline_func in self.baselines.items():
            result[('b', baseline_name)].append(baseline_func(parsed))

    def predict(self, lines):
        for f in self.filters:
            lines = filter(lambda l: f(l), lines)
        result = {'t': [], 'a': [], 'p': [], 'r': [], 'n': []}
        for baseline_name in self.baselines:
            result[('b', baseline_name)]=[] 
        for l in lines:
            self._decision_2_prediction(l, result)   
        return pd.DataFrame(result)

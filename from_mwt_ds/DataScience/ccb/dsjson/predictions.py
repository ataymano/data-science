import ccb.dsjson.filters as filters
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
        'random': lambda obj: [1 / len(o['_a']) for o in obj['_outcomes']],
        'baseline1_old': lambda obj: [o['_p'][0] * int(o['_a'][0] == i) for i, o in enumerate(obj['_outcomes'])]
    }

    def __init__(self, filters = None, baselines = None):
        self.filters = filters if filters is not None else self.filters
        self.baselines = baselines if baselines is not None else self.baselines

    def _decision_2_prediction(self, line, result):
        parsed = json_load(line)
        a = []
        p = []
        r = []
        for i, o in enumerate(parsed['_outcomes']):
            a.append(o['_a'][0])         
            p.append(o['_p'][0])
            r.append(-o['_label_cost'])
        result['a'].append(a)         
        result['p'].append(p)
        result['r'].append(r)

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

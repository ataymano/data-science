import json
import pandas as pd

from itertools import chain
from pathlib import Path

from pipeline.progress import dummy_progress, tqdm_progress
import multiprocessing

class FileSizeHasher:
    extension = 'size'
    
    def evaluate(self, path):
        return Path(path).stat().st_size

class Execution:
    def __init__(self, reader, input, hasher, path_gen, processor, process):
        self.reader = reader
        self.input = input
        self.output = path_gen(input)
        self.hasher = hasher
        self.processor = processor
        self.process = process 

    def _is_in_sync(self):
        input_hash = self.hasher.evaluate(self.input)
        output_hash = self._load_hash(self.output)
        return input_hash and output_hash and input_hash == output_hash

    def _sync(self):
        with open(f'{self.output}.{self.hasher.extension}','w') as f:
            f.write(str(self.hasher.evaluate(self.input)))

    def _load_hash(self, path):
        hash_path = f'{path}.{self.hasher.extension}'
        if not Path(hash_path).exists():
            return None
        try:
            hash_value = int(open(hash_path, 'r').read())
        except:
            hash_value = None
        return hash_value

    def run(self):
        if self.process or not Path(self.output).exists() or not self._is_in_sync():
            Path(self.output).parent.mkdir(parents=True, exist_ok=True)
            return self.processor(self.reader(self.input))
        return None
            
    def close(self):
        self._sync()
        return self.output if Path(self.output).exists() else None

def _fork(func, args):
    from multiprocess import Pool
    with Pool(1) as p:
        return p.apply(func, args)

class Fileset:
    def __init__(self, files=[], reader=None, writer=None, type=None):
        self._files = files
        self._reader = reader
        self._writer = writer
        self._type = type

    def read(self, i):
        return self._reader(i, self._files[i])

    def _process_execution(self, execution, progress, fork = False):
        def _run(execution):
            result = execution.run()
            if result is not None:
                self._writer(execution.output, result)
            return execution.close()
        if fork:
            result = _fork(_run, [execution])
        else:
            result = _run(execution)
        progress.on_step()
        return result

    def init(self, executions, progress=tqdm_progress(), procs=max(1, multiprocessing.cpu_count() // 2)):
        self.files = []
        progress.on_start(len(executions))
        if procs == 1:
            for execution in executions:
                self._files.append(self._process_execution(execution, progress))
        else:
            from multiprocessing.pool import ThreadPool
            with ThreadPool(procs) as pool:
                self._files = pool.starmap(self._process_execution, [(e, progress, True) for e in executions])
        progress.on_finish() 
        return self

    def process(self, processor, path_gen=None, process=False, hasher=FileSizeHasher()):
        path_gen = path_gen or (lambda f: f'{f}.{processor.__name__}') 
        return [Execution(lambda p, i=i: self.reader(i, p), p, hasher, path_gen, processor, process) for i, p in enumerate(self.files)]

    def delete(self):
        for f in self.files:
            Path(f).unlink()

    def __getitem__(self, i):
        if isinstance(i, int):
            return self._files[i]

        return self._type(self._files[i])

class MultilineFiles(Fileset):
    @staticmethod
    def _read(i, path):
        return open(path)

    @staticmethod
    def _write(path, lines):
        with open(path, 'w') as f:
            f.writelines(lines)

    def __init__(self, files = []):
        super().__init__(files=files, reader=MultilineFiles._read, writer=MultilineFiles._write, type=MultilineFiles)

class NdJsonFiles(Fileset):
    @staticmethod
    def _read(i, path):
        return map(lambda l : json.loads(l), open(path))

    @staticmethod
    def _write(path, objects):
        with open(path, 'w') as f:
            f.writelines(map(lambda l : f'{json.dumps(l)}\n', objects))

    def __init__(self, files = []):
        super().__init__(files=files, reader=NdJsonFiles._read, writer=NdJsonFiles._write, type=NdJsonFiles) 

class PickleFiles(Fileset):
    @staticmethod
    def _read(i, path):
        return pd.read_pickle(path)

    @staticmethod
    def _write(path, df):
        df.to_pickle(path)

    def __init__(self, files = []):
        super().__init__(files=files, reader=PickleFiles._read, writer=PickleFiles._write, type=PickleFiles)  

    def open(self):
        return pd.concat([self.read(i) for i in range(len(self.files))])

class CsvFiles(Fileset):
    @staticmethod
    def _read(i, path):
        return pd.read_csv(path)

    @staticmethod
    def _write(path, df):
        df.to_csv(path, index=False)

    def __init__(self, files = []):
        super().__init__(files=files, reader=CsvFiles._read, writer=CsvFiles._write, type=CsvFiles) 

    def open(self):
        return pd.concat([self.read(i) for i in range(len(self.files))])

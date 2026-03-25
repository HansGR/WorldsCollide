import hashlib
import numpy as np

_generator = None

def seed(s):
    global _generator
    # convert string seed to deterministic integer for numpy
    hash_bytes = hashlib.sha256(s.encode()).digest()
    seed_int = int.from_bytes(hash_bytes[:16], byteorder='big')
    _generator = np.random.default_rng(seed_int)

def choice(seq):
    index = int(_generator.integers(0, len(seq)))
    return seq[index]

def sample(population, k):
    indices = _generator.choice(len(population), size=k, replace=False)
    return [population[int(i)] for i in indices]

def shuffle(lst):
    _generator.shuffle(lst)

def randint(a, b):
    return int(_generator.integers(a, b + 1))

def randrange(*args):
    if len(args) == 1:
        return int(_generator.integers(0, args[0]))
    elif len(args) == 2:
        return int(_generator.integers(args[0], args[1]))
    elif len(args) == 3:
        return int(_generator.integers(args[0], args[1], args[2]))

def random():
    return float(_generator.random())

def triangular(low, high, mode):
    return float(_generator.triangular(low, mode, high))

def gauss(mu, sigma):
    return float(_generator.normal(mu, sigma))

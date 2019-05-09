#!/usr/bin/python
# coding=utf-8

# pylint: disable=superfluous-parens
# superfluous-parens: Parentheses are good for clarity and portability

"""Unit tests for bloom_filter_mod"""

# mport os
import sys
import math
import time

try:
    import anydbm
except ImportError:
    import dbm as anydbm

import random

import bloom_filter
from bloom_filter.bloom_filter import Redis_backend
import rediscluster

CHARACTERS = 'abcdefghijklmnopqrstuvwxyz1234567890'


NODES = [
    # Fill in the local nodes
    {"host": "localhost",  "port": "30001"},
]

redis  = rediscluster.StrictRedisCluster(startup_nodes=NODES)

def my_range(maximum):
    """A range function with consistent semantics on 2.x and 3.x"""
    value = 0
    while True:
        if value >= maximum:
            break
        yield value
        value += 1


def _test(description, values, trials, error_rate, probe_bitnoer=None, filename=None):
    # pylint: disable=R0913,R0914
    # R0913: We want a few arguments
    # R0914: We want some local variables too.  This is just test code.
    """Some quick automatic tests for the bloom filter class"""
    if not probe_bitnoer:
        probe_bitnoer = bloom_filter.get_bitno_lin_comb

    all_good = True

    divisor = 100000

    rbackend = Redis_backend(redis=redis)
    bloom = bloom_filter.BloomFilter(
        max_elements=trials * 2,
        error_rate=error_rate,
        probe_bitnoer=probe_bitnoer,
        backend=rbackend,
        start_fresh=True,
    )

    message = '\ndescription: %s num_bits_m: %s num_probes_k: %s\n'
    filled_out_message = message % (
        description,
        bloom.num_bits_m,
        bloom.num_probes_k,
    )

    sys.stdout.write(filled_out_message)

    print('starting to add values to an empty bloom filter')
    for valueno, value in enumerate(values.generator()):
        reverse_valueno = values.length() - valueno
        if reverse_valueno % divisor == 0:
            print('adding valueno %d' % reverse_valueno)
        bloom.add(value)

    print('testing all known members')
    include_in_count = sum(include in bloom for include in values.generator())
    if include_in_count == values.length():
        # Good
        pass
    else:
        sys.stderr.write('Include count bad: %s, %d\n' % (include_in_count, values.length()))
        all_good = False

    print('testing random non-members')
    false_positives = 0
    for trialno in my_range(trials):
        if trialno % divisor == 0:
            sys.stderr.write('trialno countdown: %d\n' % (trials - trialno))
        while True:
            candidate = ''.join(random.sample(CHARACTERS, 5))
            # If we accidentally found a member, try again
            if values.within(candidate):
                continue
            if candidate in bloom:
                # print 'We erroneously think %s is in the filter' % candidate
                false_positives += 1
            break

    actual_error_rate = float(false_positives) / trials

    if actual_error_rate > error_rate:
        sys.stderr.write('%s: Too many false positives: actual: %s, expected: %s\n' % (
            sys.argv[0],
            actual_error_rate,
            error_rate,
        ))
        all_good = False

    return all_good


class States(object):
    """Generate the USA's state names"""

    def __init__(self):
        pass

    states = """Alabama Alaska Arizona Arkansas California Colorado Connecticut
        Delaware Florida Georgia Hawaii Idaho Illinois Indiana Iowa Kansas
        Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota
        Mississippi Missouri Montana Nebraska Nevada NewHampshire NewJersey
        NewMexico NewYork NorthCarolina NorthDakota Ohio Oklahoma Oregon
        Pennsylvania RhodeIsland SouthCarolina SouthDakota Tennessee Texas Utah
        Vermont Virginia Washington WestVirginia Wisconsin Wyoming""".split()

    @staticmethod
    def generator():
        """Generate the states"""
        for state in States.states:
            yield state

    @staticmethod
    def within(value):
        """Is the value in our list of states?"""
        return value in States.states

    @staticmethod
    def length():
        """What is the length of our contained values?"""
        return len(States.states)


def random_string():
    """Generate a random, 10 character string - for testing purposes"""
    list_ = []
    for chrno in range(10):
        dummy = chrno
        character = CHARACTERS[int(random.random() * len(CHARACTERS))]
        list_.append(character)
    return ''.join(list_)


class Random_content(object):
    """Generated a bunch of random strings in sorted order"""

    random_content = [random_string() for dummy in range(1000)]

    def __init__(self):
        pass

    @staticmethod
    def generator():
        """Generate all values"""
        for item in Random_content.random_content:
            yield item

    @staticmethod
    def within(value):
        """Test for membership"""
        return value in Random_content.random_content

    @staticmethod
    def length():
        """How many members?"""
        return len(Random_content.random_content)


class Evens(object):
    """Generate a bunch of even numbers"""

    def __init__(self, maximum):
        self.maximum = maximum

    def generator(self):
        """Generate all values"""
        for value in my_range(self.maximum):
            if value % 2 == 0:
                yield str(value)

    def within(self, value):
        """Test for membership"""
        try:
            int_value = int(value)
        except ValueError:
            return False

        if int_value >= 0 and int_value < self.maximum and int_value % 2 == 0:
            return True
        else:
            return False

    def length(self):
        """How many members?"""
        return int(math.ceil(self.maximum / 2.0))


def and_test():
    """Test the & operator"""

    all_good = True

    rbackend = Redis_backend(redis=redis)
    abc = bloom_filter.BloomFilter(max_elements=100, error_rate=0.01,
            backend=rbackend)
    for character in ['a', 'b', 'c']:
        abc += character

    rbackend = Redis_backend(redis=redis)
    bcd = bloom_filter.BloomFilter(max_elements=100, error_rate=0.01,
            backend=rbackend)
    for character in ['b', 'c', 'd']:
        bcd += character

    abc_and_bcd = abc
    abc_and_bcd &= bcd

    if 'a' in abc_and_bcd:
        sys.stderr.write('a in abc_and_bcd, but should not be')
        all_good = False
    if not 'b' in abc_and_bcd:
        sys.stderr.write('b not in abc_and_bcd, but should be')
        all_good = False
    if not 'c' in abc_and_bcd:
        sys.stderr.write('c not in abc_and_bcd, but should be')
        all_good = False
    if 'd' in abc_and_bcd:
        sys.stderr.write('d in abc_and_bcd, but should not be')
        all_good = False

    return all_good


def or_test():
    """Test the | operator"""

    all_good = True

    rbackend = Redis_backend(redis=redis)
    abc = bloom_filter.BloomFilter(max_elements=100, error_rate=0.01,
            backend=rbackend)
    for character in ['a', 'b', 'c']:
        abc += character

    rbackend = Redis_backend(redis=redis)
    bcd = bloom_filter.BloomFilter(max_elements=100, error_rate=0.01,
            backend=rbackend)
    for character in ['b', 'c', 'd']:
        bcd += character

    abc_and_bcd = abc
    abc_and_bcd |= bcd

    if not 'a' in abc_and_bcd:
        sys.stderr.write('a not in abc_and_bcd, but should be')
        all_good = False
    if not 'b' in abc_and_bcd:
        sys.stderr.write('b not in abc_and_bcd, but should be')
        all_good = False
    if not 'c' in abc_and_bcd:
        sys.stderr.write('c not in abc_and_bcd, but should be')
        all_good = False
    if not 'd' in abc_and_bcd:
        sys.stderr.write('d not in abc_and_bcd, but should be')
        all_good = False
    if 'e' in abc_and_bcd:
        sys.stderr.write('e in abc_and_bcd, but should not be')
        all_good = False

    return all_good


def give_description(filename):
    """Return a description of the filename type - could be array, file or hybrid"""
    if filename is None:
        return 'array'
    elif isinstance(filename, tuple):
        if filename[1] == -1:
            return 'mmap'
        else:
            return 'hybrid'
    else:
        return 'seek'


def test_bloom_filter():
    """Unit tests for BloomFilter class"""

    if sys.argv[1:] == ['--performance-test']:
        performance_test = True
    else:
        performance_test = False

    all_good = True

    all_good &= _test('states', States(), trials=100000, error_rate=0.01)

    all_good &= _test('random', Random_content(), trials=10000, error_rate=0.1)
    all_good &= _test('random', Random_content(), trials=10000, error_rate=0.1,
                      probe_bitnoer=bloom_filter.get_bitno_seed_rnd)

    filename = 'bloom-filter-rm-me'
    all_good &= _test('random', Random_content(), trials=10000, error_rate=0.1, filename=filename)

    all_good &= and_test()

    all_good &= or_test()

    if performance_test:
        sqrt_of_10 = math.sqrt(10)
        # for exponent in range(5): # this is a lot, but probably not unreasonable
        for exponent in range(19):  # this is a lot, but probably not unreasonable
            elements = int(sqrt_of_10 ** exponent + 0.5)
            for filename in [None, 'bloom-filter-rm-me', ('bloom-filter-rm-me', 768 * 2 ** 20),
                             ('bloom-filter-rm-me', -1)]:
                description = give_description(filename)
                key = '%s %s' % (description, elements)
                database = anydbm.open('performance-numbers', 'c')
                if key in database.keys():
                    database.close()
                    continue
                if elements >= 100000000 and description == 'seek':
                    continue
                if elements >= 100000000 and description == 'mmap':
                    continue
                if elements >= 1000000000 and description == 'array':
                    continue
                time0 = time.time()
                all_good &= _test(
                    'evens %s elements: %d' % (give_description(filename), elements),
                    Evens(elements),
                    trials=elements,
                    error_rate=1e-2,
                    filename=filename,
                )
                time1 = time.time()
                delta_t = time1 - time0
                # file_ = open('%s.txt' % description, 'a')
                # file_.write('%d %f\n' % (elements, delta_t))
                # file_.close()
                database = anydbm.open('performance-numbers', 'c')
                database[key] = '%f' % delta_t
                database.close()

    # test prob count ok

    rbackend = Redis_backend(redis=redis)
    bloom = bloom_filter.BloomFilter(1000000, error_rate=.99, backend=rbackend)
    all_good &= bloom.num_probes_k == 1
    if not all_good:
        sys.stderr.write('%s: One or more tests failed\n' % sys.argv[0])
        sys.exit(1)


if __name__ == '__main__':
    test_bloom_filter()

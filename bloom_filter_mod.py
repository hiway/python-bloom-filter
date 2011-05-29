
'''Bloom Filter: Probabilistic set membership testing for large sets'''

# Shamelessly borrowed (under MIT license) from http://code.activestate.com/recipes/577686-bloom-filter/
# About Bloom Filters: http://en.wikipedia.org/wiki/Bloom_filter

# Tweaked a bit by Daniel Richard Stromberg, mostly to make it pass pylint

import array
import random

def get_probes(bfilter, key):
	'''Generate a bunch of fast hash functions'''
	hasher = random.Random(key).randrange
	for _ in range(bfilter.num_probes):
		array_index = hasher(len(bfilter.arr))
		bit_index = hasher(32)
		yield array_index, 1 << bit_index

class Bloom_filter:
	'''Probabilistic set membership testing for large sets'''

	def __init__(self, num_bits, num_probes, probe_func=get_probes):
		self.num_bits = num_bits
		num_words = (num_bits + 31) // 32
		self.arr = array.array('L', [0]) * num_words
		self.num_probes = num_probes
		self.probe_func = probe_func

	def add(self, key):
		'''Add an element to the filter'''
		for i, mask in self.probe_func(self, key):
			self.arr[i] |= mask

	def _match_template(self, bfilter):
		'''Compare a sort of signature for two bloom filters.  Used in preparation for binary operations'''
		return (self.num_bits == bfilter.num_bits \
			and self.num_probes == bfilter.num_probes \
			and self.probe_func == bfilter.probe_func)

	def union(self, bfilter):
		'''Compute the set union of two bloom filters'''
		if self._match_template(bfilter):
			self.arr = [a | b for a, b in zip(self.arr, bfilter.arr)]
		else:
			# Union b/w two unrelated bloom filter raises this
			raise ValueError("Mismatched bloom filters")

	def __or__(self, bfilter):
		return self.union(bfilter)

	def intersection(self, bfilter):
		'''Compute the set intersection of two bloom filters'''
		if self._match_template(bfilter):
			self.arr = [a & b for a, b in zip(self.arr, bfilter.arr)]
		else:
			# Intersection b/w two unrelated bloom filter raises this
			raise ValueError("Mismatched bloom filters")

	def __and__(self, bfilter):
		return self.intersection(bfilter)

	def __contains__(self, key):
		return all(self.arr[i] & mask for i, mask in self.probe_func(self, key))



'''Bloom Filter: Probabilistic set membership testing for large sets'''

# Shamelessly borrowed (under MIT license) from http://code.activestate.com/recipes/577686-bloom-filter/
# About Bloom Filters: http://en.wikipedia.org/wiki/Bloom_filter

# Tweaked a bit by Daniel Richard Stromberg, mostly to make it pass pylint

import math
import array
import random

def get_probes(bfilter, key):
	'''Generate a bunch of fast hash functions'''
	hasher = random.Random(key).randrange
	for _ in range(bfilter.num_probes):
		array_index = hasher(len(bfilter.array_))
		bit_index = hasher(32)
		yield array_index, 1 << bit_index

class Bloom_filter:
	'''Probabilistic set membership testing for large sets'''

	def __init__(self, ideal_num_elements, error_rate, probe_func=get_probes):
		if ideal_num_elements <= 0:
			raise ValueError('ideal_num_elements must be > 0')
		if not (0 < error_rate < 1):
			raise ValueError('error_rate must be between 0 and 1 inclusive')

		self.error_rate = error_rate
		# With fewer elements, we should do very well.  With more elements, our error rate "guarantee"
		# drops rapidly.
		self.ideal_num_elements = ideal_num_elements

		self.num_bits = - int((self.ideal_num_elements * math.log(self.error_rate)) / (math.log(2) ** 2))

		self.num_words = int((self.num_bits + 31) / 32)
		self.array_ = array.array('L', [0]) * self.num_words

		self.num_probes = int((self.num_bits / self.ideal_num_elements) * math.log(2))

		self.probe_func = probe_func

	def __repr__(self):
		return 'Bloom_filter(ideal_num_elements=%d, error_rate=%f, num_bits=%d)' % (
			self.ideal_num_elements,
			self.error_rate,
			self.num_bits,
			)

	def add(self, key):
		'''Add an element to the filter'''
		for i, mask in self.probe_func(self, key):
			self.array_[i] |= mask

	def _match_template(self, bfilter):
		'''Compare a sort of signature for two bloom filters.  Used in preparation for binary operations'''
		return (self.num_bits == bfilter.num_bits \
			and self.num_probes == bfilter.num_probes \
			and self.probe_func == bfilter.probe_func)

	def union(self, bfilter):
		'''Compute the set union of two bloom filters'''
		if self._match_template(bfilter):
			self.array_ = [a | b for a, b in zip(self.array_, bfilter.array_)]
		else:
			# Union b/w two unrelated bloom filter raises this
			raise ValueError("Mismatched bloom filters")

	def __or__(self, bfilter):
		return self.union(bfilter)

	def intersection(self, bfilter):
		'''Compute the set intersection of two bloom filters'''
		if self._match_template(bfilter):
			self.array_ = [a & b for a, b in zip(self.array_, bfilter.array_)]
		else:
			# Intersection b/w two unrelated bloom filter raises this
			raise ValueError("Mismatched bloom filters")

	def __and__(self, bfilter):
		return self.intersection(bfilter)

	def __contains__(self, key):
		return all(self.array_[i] & mask for i, mask in self.probe_func(self, key))


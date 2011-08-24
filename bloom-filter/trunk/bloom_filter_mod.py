
'''Bloom Filter: Probabilistic set membership testing for large sets'''

# Shamelessly borrowed (under MIT license) from http://code.activestate.com/recipes/577686-bloom-filter/
# About Bloom Filters: http://en.wikipedia.org/wiki/Bloom_filter

# Tweaked a bit by Daniel Richard Stromberg, mostly to make it pass pylint and give it a little nicer
# __init__ parameters.

import math
import array
import random

# In the literature:
# k is the number of probes - we call this num_probes_k
# m is the number of bits in the filter - we call this num_bits_m
# n is the ideal number of elements to eventually be stored in the filter - we call this ideal_num_elements_n
# p is the desired error rate when full - we call this error_rate_p

def get_probe_index_and_bitmask(bloom_filter, key):
	'''Apply num_probes_k hash functions to key.  Generate the array index and bitmask corresponding to each result'''

	# We're using key as a seed to a pseudorandom number generator
	hasher = random.Random(key).randrange
	for _ in range(bloom_filter.num_probes_k):
		# We could precompute this length for speed.  But we don't
		array_index = hasher(bloom_filter.num_words)
		bit_index = hasher(32)
		yield array_index, 1 << bit_index


class Bloom_filter:
	'''Probabilistic set membership testing for large sets'''

	def __init__(self, ideal_num_elements_n, error_rate_p, probe_offsetter=get_probe_index_and_bitmask):
		if ideal_num_elements_n <= 0:
			raise ValueError('ideal_num_elements_n must be > 0')
		if not (0 < error_rate_p < 1):
			raise ValueError('error_rate_p must be between 0 and 1 inclusive')

		self.error_rate_p = error_rate_p
		# With fewer elements, we should do very well.  With more elements, our error rate "guarantee"
		# drops rapidly.
		self.ideal_num_elements_n = ideal_num_elements_n

		numerator = -1 * self.ideal_num_elements_n * math.log(self.error_rate_p)
		denominator = math.log(2) ** 2
		#self.num_bits_m = - int((self.ideal_num_elements_n * math.log(self.error_rate_p)) / (math.log(2) ** 2))
		real_num_bits_m = numerator / denominator
		self.num_bits_m = int(math.ceil(real_num_bits_m))

		self.num_words = int((self.num_bits_m + 31) / 32)
		self.array_ = array.array('L', [0]) * self.num_words

		# AKA num_offsetters
		# Verified against http://en.wikipedia.org/wiki/Bloom_filter#Probability_of_false_positives
		real_num_probes_k = (self.num_bits_m / self.ideal_num_elements_n) * math.log(2)
		self.num_probes_k = int(math.ceil(real_num_probes_k))

		self.probe_offsetter = probe_offsetter

	def __repr__(self):
		return 'Bloom_filter(ideal_num_elements_n=%d, error_rate_p=%f, num_bits_m=%d)' % (
			self.ideal_num_elements_n,
			self.error_rate_p,
			self.num_bits_m,
			)

	def add(self, key):
		'''Add an element to the filter'''
		for index, mask in self.probe_offsetter(self, key):
			self.array_[index] |= mask

	def __iadd__(self, key):
		self.add(key)
		return self

	def _match_template(self, bloom_filter):
		'''Compare a sort of signature for two bloom filters.  Used in preparation for binary operations'''
		return (self.num_bits_m == bloom_filter.num_bits_m \
			and self.num_probes_k == bloom_filter.num_probes_k \
			and self.probe_offsetter == bloom_filter.probe_offsetter)

	def union(self, bloom_filter):
		'''Compute the set union of two bloom filters'''
		if self._match_template(bloom_filter):
			self.array_ = [a | b for a, b in zip(self.array_, bloom_filter.array_)]
		else:
			# Union b/w two unrelated bloom filter raises this
			raise ValueError("Mismatched bloom filters")

	def __ior__(self, bloom_filter):
		self.union(bloom_filter)
		return self

	def intersection(self, bloom_filter):
		'''Compute the set intersection of two bloom filters'''
		if self._match_template(bloom_filter):
			self.array_ = [a & b for a, b in zip(self.array_, bloom_filter.array_)]
		else:
			# Intersection b/w two unrelated bloom filter raises this
			raise ValueError("Mismatched bloom filters")

	def __iand__(self, bloom_filter):
		self.intersection(bloom_filter)
		return self

	def __contains__(self, key):
		return all(self.array_[i] & mask for i, mask in self.probe_offsetter(self, key))



'''Bloom Filter: Probabilistic set membership testing for large sets'''

# Shamelessly borrowed (under MIT license) from http://code.activestate.com/recipes/577686-bloom-filter/
# About Bloom Filters: http://en.wikipedia.org/wiki/Bloom_filter

# Tweaked a bit by Daniel Richard Stromberg, mostly to make it pass pylint and give it a little nicer
# __init__ parameters.

#mport sys
import math
import array
import random
#mport hashlib

# In the literature:
# k is the number of probes - we call this num_probes_k
# m is the number of bits in the filter - we call this num_bits_m
# n is the ideal number of elements to eventually be stored in the filter - we call this ideal_num_elements_n
# p is the desired error rate when full - we call this error_rate_p

def get_index_bitmask_seed_rnd(bloom_filter, key):
	'''Apply num_probes_k hash functions to key.  Generate the array index and bitmask corresponding to each result'''

	# We're using key as a seed to a pseudorandom number generator
	hasher = random.Random(key).randrange
	for _ in range(bloom_filter.num_probes_k):
		array_index = hasher(bloom_filter.num_words)
		bit_within_word_index = hasher(32)
		yield array_index, 1 << bit_within_word_index


MERSENNES1 = [ 2**x - 1 for x in 17, 31, 127 ]
MERSENNES2 = [ 2**x - 1 for x in 19, 67, 257 ]

def simple_hash(int_list, prime1, prime2, prime3):
	'''Compute a hash value from a list of integers and 3 primes'''
	result = 0
	for integer in int_list:
		result += ((result + integer + prime1) * prime2) % prime3
	return result

def hash1(int_list):
	'''Basic hash function #1'''
	return simple_hash(int_list, MERSENNES1[0], MERSENNES1[1], MERSENNES1[2])

def hash2(int_list):
	'''Basic hash function #2'''
	return simple_hash(int_list, MERSENNES2[0], MERSENNES2[1], MERSENNES2[2])

def get_index_bitmask_lin_comb(bloom_filter, key):
	'''Apply num_probes_k hash functions to key.  Generate the array index and bitmask corresponding to each result'''

	# This one assumes key is either bytes or str (or other list of integers)

	if isinstance(key[0], int):
		int_list = key
	elif isinstance(key[0], str):
		int_list = [ ord(char) for char in key ]
	else:
		raise TypeError

	hash_value1 = hash1(int_list)
	hash_value2 = hash2(int_list)

	# We're using linear combinations of hash_value1 and hash_value2 to obtain num_probes_k hash functions
	for probeno in range(1, bloom_filter.num_probes_k + 1):
		bit_index = hash_value1 + probeno * hash_value2
		bit_within_word_index = bit_index % 32
		array_index = (bit_index // 32) % bloom_filter.num_words
		yield array_index, 1 << bit_within_word_index


class Bloom_filter:
	'''Probabilistic set membership testing for large sets'''

	#def __init__(self, ideal_num_elements_n, error_rate_p, probe_offsetter=get_index_bitmask_seed_rnd):
	def __init__(self, ideal_num_elements_n, error_rate_p, probe_offsetter=get_index_bitmask_lin_comb):
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

# This comes close, but often isn't the same value
#		alternative_real_num_probes_k = -math.log(self.error_rate_p) / math.log(2)
#
#		if abs(real_num_probes_k - alternative_real_num_probes_k) > 1e-6:
#			sys.stderr.write('real_num_probes_k: %f, alternative_real_num_probes_k: %f\n' % 
#				(real_num_probes_k, alternative_real_num_probes_k)
#				)
#			sys.exit(1)

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


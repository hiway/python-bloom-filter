# Sample test for Redis bloom filter

from bloom_filter import BloomFilter

bloom = BloomFilter(max_elements=10000, error_rate=0.1, backend='$redis')

bloom.add("test")

print "test" in bloom

print "1234" in bloom

bloom.add("1234")

print "1234" in bloom

print "Ping" in bloom

bloom.add("Ping")

print "Ping" in bloom

print "Pong" in bloom

bloom.add("Pong")

print "Pong" in bloom

bloom.delete("Pong")

print "Pong" in bloom

print "Tom" in bloom

bloom.add("Tom")

print "Tom" in bloom

bloom.delete("Tom")

print "Tom" in bloom 

print "Jerry" in bloom
bloom.add('Jerry')
print "Jerry" in bloom

bloom.delete('Jerry')


# Sample test for Redis bloom filter

from bloom_filter import BloomFilter
from bloom_filter.bloom_filter import Redis_backend

import rediscluster

NODES = [
    # Fill in the local nodes
    {"host": "localhost",  "port": "30001"},
]
r = rediscluster.StrictRedisCluster(startup_nodes=NODES)

rbackend = Redis_backend(redis=r)

bloom = BloomFilter(max_elements=10000, error_rate=0.1, backend=rbackend)

bloom.add("test")

print 'should be true:' + str("test" in bloom)

print 'should be false:' + str("1234" in bloom)

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


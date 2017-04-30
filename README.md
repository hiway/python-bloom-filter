# bloom-filter

This project builds on `drs-bloom-filter` and `bloom_filter_mod`.
Credits and links can be found in AUTHORS.md.

## Installation

    pip install bloom_filter


## Example:

    from bloom_filter import BloomFilter

    have_met = BloomFilter()

    def have_i_met(name):
        met = name in have_met
        print('Have I met {} before: {}'.format(name, met))

    def meet(name):
        have_met.add(name)
        print('Hello, {}'.format(name))

    for name in ['Harry', 'Larry', 'Moe']:
        have_i_met(name)
        meet(name)
        have_i_met(name)


## Usage:

    from bloom_filter import BloomFilter

    # instantiate BloomFilter with custom settings,
    # max_elements is how many elements you expect the filter to hold.
    # error_rate defines accuracy; You can use defaults with
    # `BloomFilter()` without any arguments. Following example
    # is same as defaults:
    bloom = BloomFilter(max_elements=10000, error_rate=0.1)

    # Test whether the bloom-filter has seen a key:
    assert "test-key" in bloom is False

    # Mark the key as seen
    bloom.add("test-key")

    # Now check again
    assert "test-key" in bloom is True

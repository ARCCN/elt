package org.elt.hazelcast_adapter.hznode;

import org.ardverk.collection.AbstractKeyAnalyzer;

public class IPKeyAnalyzer extends AbstractKeyAnalyzer<IP> {

	/* Here as a dirty hack.
	 * Since Trie implementation is buggy.
	 * We always set the highest bit (32th) to "1".
	 */
	
	private static final long serialVersionUID = -4503928902228373258L;

	private int intCompareUnsigned(int arg0, int arg1) {
		return Long.compare(arg0 & 0xFFFFFFFFL, arg1 & 0xFFFFFFFFL);
	}
	
	@Override
	public int compare(IP arg0, IP arg1) {
		return intCompareUnsigned(arg0.getAddr(), arg1.getAddr());
	}

	public int length(IP key) {
		return 32 - key.getMask();
	}

	public boolean isBitSet(IP key, int keyLength, int bitIndex) {
		if (bitIndex < 0 || bitIndex >= keyLength) {
			return false;
		}
		return (key.getAddr() & (1 << (32 - 1 - bitIndex))) != 0;
	}

	public int bitIndex(IP key, int keyStart, int keyLength, 
						IP found, int foundStart, int foundLength) {
		if (key == null || key.getAddr() == 0) {
			return AbstractKeyAnalyzer.NULL_BIT_KEY;
		}
		if (found == null) {
			return 0;
		}
		int commonLength = Math.min(
				Math.min(keyLength, 32 - keyStart - key.getMask()),
				Math.min(foundLength, 32 - foundStart - found.getMask()));
		
		int addr1, addr2;
		if (commonLength >= 32) {
			addr1 = (key.getAddr() >> (32 - keyStart - commonLength));
			addr2 = (found.getAddr() >> (32 - foundStart - commonLength));
		} else if (foundStart + commonLength == 0) {
			addr1 = addr2 = 0;
		} else {
			addr1 = (key.getAddr() >> (32 - keyStart - commonLength)) & ((1 << (commonLength)) - 1);
			addr2 = (found.getAddr() >> (32 - foundStart - commonLength)) & ((1 << (commonLength)) - 1);
		}
		int diff = Integer.numberOfLeadingZeros(addr1 ^ addr2);
		if (diff != 32) {
			return diff - (32 - commonLength);
		} else if (commonLength == keyLength && commonLength == foundLength) {
			// Nothing was cut off.
			return AbstractKeyAnalyzer.EQUAL_BIT_KEY;
		} else {
			return commonLength;
		}
	}

	public int bitsPerElement() {
		return 1;
	}

	public boolean isPrefix(IP prefix, int offset, int length, IP key) {
		if (offset >= 32) {
			if (length > 0) {
				return false;
			} else {
				return true;
			}
		}
		if (Integer.numberOfLeadingZeros(
				(prefix.getAddr() << offset) ^ key.getAddr()) >= length) {
			return true;
		}
		return false;
	}

	@Override
	public int lengthInBits(IP key) {
		return length(key) + 1;
	}

	@Override
	public boolean isBitSet(IP key, int bitIndex) {
		if (bitIndex == 0) {
			return true;
		}
		--bitIndex;
		return (key.getAddr() & (1 << (32 - 1 - bitIndex))) != 0;
	}

	@Override
	public int bitIndex(IP key, IP otherKey) {
		return bitIndex(key, 0, lengthInBits(key), 
				otherKey, 0, lengthInBits(otherKey)) + 1;
	}

	@Override
	public boolean isPrefix(IP key, IP prefix) {
		return isPrefix(prefix, 0, lengthInBits(prefix), key);
	}
}
package org.elt.hazelcast_adapter;

import org.ardverk.collection.ByteArrayKeyAnalyzer;
import org.ardverk.collection.PatriciaTrie;
import org.ardverk.collection.StringKeyAnalyzer;
import org.elt.hazelcast_adapter.hznode.IP;
import org.elt.hazelcast_adapter.hznode.IPKeyAnalyzer;

public class TrieTest {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		
		PatriciaTrie<byte[], Long> trie1 = new PatriciaTrie<byte[], Long>(ByteArrayKeyAnalyzer.VARIABLE);
		trie1.put(new byte[]{0}, 1L);
		trie1.put(new byte[]{0,0,0}, 2L);
		trie1.get(new byte[]{0});
		
		PatriciaTrie<IP, Long> trie2 = new PatriciaTrie<IP, Long>(new IPKeyAnalyzer());
		trie2.put(new IP(0x00000000, 32), 1L);
		trie2.put(new IP(0x00000000, 31), 4L);
		trie2.put(new IP(0x80000000, 30), 2L);
		trie2.put(new IP(0xC0000000, 30), 3L);
		System.out.println(trie2.get(new IP(0xA0000000, 31)));
		
		PatriciaTrie<String, Long> trie3 = new PatriciaTrie<String, Long>(StringKeyAnalyzer.BYTE);
		trie3.put(new IP(0x00000000, 32).toBinaryString(), 1L);
		trie3.put(new IP(0x00000000, 31).toBinaryString(), 4L);
		trie3.put(new IP(0x80000000, 30).toBinaryString(), 2L);
		trie3.put(new IP(0xC0000000, 30).toBinaryString(), 3L);
		System.out.println(trie3.get(new IP(0xA0000000, 31).toBinaryString()));
	}

}

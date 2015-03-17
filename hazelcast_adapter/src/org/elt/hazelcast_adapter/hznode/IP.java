package org.elt.hazelcast_adapter.hznode;

import java.io.Serializable;

public class IP implements Serializable {
	
	private static final long serialVersionUID = -7223119466516028153L;
	
	private int addr;
	private int mask;
	
	public IP(int addr) {
		this.addr = addr;
		this.mask = 0;
	}
	
	public IP(int addr, int mask) { 
		assert 0 <= mask;
		mask = Math.min(mask, 32);
		if (mask >= 32) {
			this.addr = 0;
		} else {
			this.addr = addr & ~((1 << mask) - 1); 
		}
		this.mask = mask; 
	}
	
	public int getAddr() { return addr; }
	public int getMask() { return mask; }
	
	public static String intToIpString(int ip) {
		return  Integer.toString((ip >> 24) & 0xFF) + "." +
			    Integer.toString((ip >> 16) & 0xFF) + "." +
			    Integer.toString((ip >> 8) & 0xFF) + "." +
				Integer.toString((ip >> 0) & 0xFF);
	}
	
	public String toString() { 
		return intToIpString(addr) + "/" + String.valueOf(mask); 
	}
	
	public String toBinaryString() {
		String s = Integer.toBinaryString(addr);
		s = "00000000000000000000000000000000" + s;
		return s.substring(s.length() - 32, s.length() - mask);
	}
	
	public boolean equals(Object other) {
		if (!(other instanceof IP)) 
			return false;
		IP otherIp = (IP)other;
		return addr == otherIp.addr && mask == otherIp.mask;
	}
}
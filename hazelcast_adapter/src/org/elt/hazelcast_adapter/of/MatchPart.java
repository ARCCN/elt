package org.elt.hazelcast_adapter.of;

import java.io.Serializable;

public class MatchPart implements Comparable, Serializable {
	protected short priority = 0;
	protected OFPMatch match;
	protected String dpid = "";
	protected byte version = -1;
	private final static long serialVersionUID = 0x2000000;
	
	public MatchPart() {
	}
	
	public MatchPart(short priority, OFPMatch match) {
		this.priority = priority;
		this.match = match;
	}
	
	public MatchPart(short priority, OFPMatch match, byte version) {
		this.priority = priority;
		this.match = match;
		this.version = version;
	}
	
	public MatchPart(short priority, OFPMatch match, String dpid, byte version) {
		this.priority = priority;
		this.match = match;
		this.dpid = dpid;
		this.version = version;
	}
	
	public void setDpid(String dpid) {
		this.dpid = dpid;
	}
	
	public OFPMatch getMatch() { return this.match;	}
	public short getPriority() { return this.priority; }
	public String getDpid() { return this.dpid; }
	public byte getVersion() { return this.version; }

	@Override
	public int compareTo(Object arg0) {
		MatchPart mp = (MatchPart)arg0;
		if (mp == null)
			return -1;
		if (mp.version != this.version)
			return -1;
		if (!(mp.dpid.equalsIgnoreCase(this.dpid)))
			return -1;
		return this.match.compareTo(mp.match);
	}
}

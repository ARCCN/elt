package org.elt.hazelcast_adapter.of;

public class OFPRule {
	protected MatchPart match;
	protected InstructionPart inst;
	
	public OFPRule() {
	}
	
	public OFPRule(short priority, OFPMatch match, InstructionPart inst) {
		this.match = new MatchPart(priority, match);
		this.inst = inst;
	}
	
	public OFPRule(short priority, OFPMatch match, InstructionPart inst, byte version) {
		this.match = new MatchPart(priority, match, version);
		this.inst = inst;
	}
	
	public InstructionPart getInstructionPart() { return this.inst; }
}

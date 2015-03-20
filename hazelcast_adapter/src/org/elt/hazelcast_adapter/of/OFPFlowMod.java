package org.elt.hazelcast_adapter.of;

import java.io.Serializable;

import org.elt.hazelcast_adapter.unpack.IDumpable;
import org.elt.hazelcast_adapter.unpack.ILoadable;

public abstract class OFPFlowMod implements ILoadable, IDumpable, Serializable {

	private static final long serialVersionUID = -5475196109678878646L;

	public enum OFPFC {
		OFPFC_UNDEFINED		(-1),
		OFPFC_ADD			 (0), /* New flow. */
		OFPFC_MODIFY 		 (1), /* Modify all matching flows. */
		OFPFC_MODIFY_STRICT  (2), /* Modify entry strictly matching wildcards and priority. */
		OFPFC_DELETE		 (3), /* Delete all matching flows. */
		OFPFC_DELETE_STRICT  (4); /* Delete entry strictly matching wildcards and priority. */
		
		private final int code;
		OFPFC(int code) { this.code = code; }
		public int getValue() { return this.code; }
	};
	
	protected short priority;
	protected byte command;
	protected OFPMatch match;
	protected InstructionPart inst;
	protected byte version;
	
	public OFPFlowMod() {
		this.version = -1;
	}
	
	public OFPFlowMod(short priority, byte command, OFPMatch match, InstructionPart inst) {
		this.priority = priority;
		this.command = command;
		this.match = match;
		this.inst = inst;
		this.version = -1;
	}
	/*
	public OFPRule toRule() {
		if (command == OFPFC.OFPFC_ADD.getValue())
			return new OFPRule(this.priority, this.match, this.inst, this.version);
		else
			return null;
	}
	*/
	public boolean isAdd() { return this.command == OFPFC.OFPFC_ADD.getValue(); }
	public boolean isModify() { return this.command == OFPFC.OFPFC_MODIFY.getValue() ||
			 this.command == OFPFC.OFPFC_MODIFY_STRICT.getValue(); }
	public boolean isDelete() { return this.command == OFPFC.OFPFC_DELETE.getValue() ||
			 this.command == OFPFC.OFPFC_DELETE_STRICT.getValue(); }
	public boolean isStrict() { return this.command == OFPFC.OFPFC_MODIFY_STRICT.getValue() ||
			  this.command == OFPFC.OFPFC_DELETE_STRICT.getValue(); }
	
	public byte getCommand() { return this.command; }
	public void setCommand(byte command) { this.command = command; } 
	public short getPriority() { return this.priority; }
	public byte getVersion() { return this.version; }
	public InstructionPart getInstructionPart() { return this.inst; }
	public OFPMatch getMatch() { return this.match; }
	
	public MatchPart toMatchPart() {
		// TODO WTF?
		/*
		if (!this.isAdd()) {
			return null;
		}
		*/
		return new MatchPart(this.priority, this.match, this.version);
	}
}

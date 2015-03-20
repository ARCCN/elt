package org.elt.hazelcast_adapter.hznode;

import java.io.Serializable;

import org.elt.hazelcast_adapter.TableEntryTag;
import org.elt.hazelcast_adapter.of.InstructionPart;

public class TableValue implements Serializable, Cloneable {

	private static final long serialVersionUID = 6366619143151462230L;
	InstructionPart inst;
	TableEntryTag tag;
	
	public TableValue() {}
	
	public TableValue( InstructionPart inst, TableEntryTag tag) {
		this.inst = inst;
		this.tag = tag;
	}
	
	public void setInstructionPart(InstructionPart inst) { this.inst = inst; }
	public InstructionPart getInstructionPart() { return this.inst; }
	
	public TableEntryTag getTag() { return this.tag; }
	public int getAppsLength() { return this.tag.getAppsLength(); }
	
	@Override
	public TableValue clone() {
		return new TableValue(inst.clone(), tag.clone());
	}
}

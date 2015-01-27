package org.elt.hazelcast_adapter.hznode;

import java.io.Serializable;

import org.elt.hazelcast_adapter.TableEntryTag;
import org.elt.hazelcast_adapter.of.InstructionPart;

public class TableValue implements Serializable {
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
}

package org.elt.hazelcast_flow_table.of;

import java.io.Serializable;

import org.elt.hazelcast_flow_table.unpack.ILoadable;

public abstract class InstructionPart implements ILoadable, Serializable, Cloneable {

	private static final long serialVersionUID = -1074892807019086394L;
	
	@Override
	public InstructionPart clone() {
		return this;
	}
}

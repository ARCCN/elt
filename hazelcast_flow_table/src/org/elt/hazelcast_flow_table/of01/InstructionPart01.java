package org.elt.hazelcast_flow_table.of01;

import java.util.Map;

import org.elt.hazelcast_flow_table.of.InstructionPart;

public class InstructionPart01 extends InstructionPart {

	private static final long serialVersionUID = 324548937211022434L;
	OFPAction01[] actions;
	
	public InstructionPart01() {
	}
	
	public InstructionPart01(OFPAction01 actions[]) {
		this.actions = actions;
	}
	
	public int getActionLength() {
		return this.actions.length;
	}
	
	public void setAction(int i, OFPAction01 act) {
		this.actions[i] = act;
	}
	
	public OFPAction01 getAction(int i) {
		return this.actions[i];
	}
	
	public OFPAction01[] getActions() {
		return this.actions;
	}

	@Override
	public void fromJSON(Map<String, Object> map) {
	}
	
	@Override
	public InstructionPart clone() {
		OFPAction01[] new_actions = new OFPAction01[actions.length];
		for (int i=0; i<actions.length; ++i)
			new_actions[i] = actions[i].clone();
		return new InstructionPart01(new_actions);
	}
}

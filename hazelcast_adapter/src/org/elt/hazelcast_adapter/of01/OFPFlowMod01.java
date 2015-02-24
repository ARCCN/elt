package org.elt.hazelcast_adapter.of01;

import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import org.elt.hazelcast_adapter.of.InstructionPart;
import org.elt.hazelcast_adapter.of.OFPFlowMod;
import org.elt.hazelcast_adapter.of.OFPMatch;

public class OFPFlowMod01 extends OFPFlowMod {
	
	public OFPFlowMod01() {
		this.version = 1;
	}
	
	public OFPFlowMod01(short priority, byte command, OFPMatch match, InstructionPart inst) {
		this.priority = priority;
		this.command = command;
		this.match = match;
		this.inst = inst;
		this.version = 1;
	}
	
	@Override
	public void fromJSON(Map map) throws Exception {
		if ((int)((long)map.get("version")) != this.version)
			throw new Exception();
		this.priority = (short)(long)map.get("priority"); //Integer.parseInt((String)map.get("priority"));
		this.command = (byte)(long)map.get("command");//Integer.parseInt((String)map.get("command"));
		this.match = new OFPMatch01();
		this.match.fromJSON((Map)map.get("match"));
		Object[] actions = (Object[])map.get("actions");
		InstructionPart01 ipart = new InstructionPart01(new OFPAction01[actions.length]);
		for (int i = 0; i < actions.length; ++i) {
			OFPAction01 act = new OFPAction01();
			act.fromJSON((Map)actions[i]);
			ipart.setAction(i, act);
		}	
		this.inst = ipart;
	}

	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("priority", (((int)this.priority) & 0xFFFF));
		map.put("command", (((int)this.command) & 0xFF));
		map.put("match", this.match.dump());
		map.put("version", ((int)this.version) & 0xFF);
		List<Map<String, Object>> actions = new LinkedList<Map<String, Object>>();
		for (OFPAction01 action: ((InstructionPart01)this.inst).getActions()) {
			actions.add(action.dump());
		}
		map.put("actions", actions.toArray(new HashMap[actions.size()]));
		return map;
	}
	
}

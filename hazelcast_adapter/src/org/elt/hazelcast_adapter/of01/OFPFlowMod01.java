package org.elt.hazelcast_adapter.of01;

import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import org.elt.hazelcast_adapter.of.OFPFlowMod;

public class OFPFlowMod01 extends OFPFlowMod {
	byte version = 1;
	
	@Override
	public void fromJSON(Map map) throws Exception {
		if (Integer.parseInt((String)map.get("version")) != this.version)
			throw new Exception();
		this.priority = (short)Integer.parseInt((String)map.get("priority"));
		this.command = (byte)Integer.parseInt((String)map.get("command"));
		this.match = new OFPMatch01();
		this.match.fromJSON((Map)map.get("match"));
		Map[] actions = (Map[])map.get("actions");
		InstructionPart01 ipart = new InstructionPart01(new OFPAction01[actions.length]);
		for (int i = 0; i < actions.length; ++i) {
			ipart.getAction(i).fromJSON(actions[i]);
		}	
		this.inst = ipart;
	}

	@Override
	public Map<String, Object> dump() throws Exception {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("priority", Integer.toString((((int)this.priority) & 0xFFFF)));
		map.put("command", Integer.toString((((int)this.command) & 0xFF)));
		map.put("match", this.match.dump());
		map.put("version", Integer.toString(((int)this.version) & 0xFF));
		List<Map<String, Object>> actions = new LinkedList<Map<String, Object>>();
		for (OFPAction01 action: ((InstructionPart01)this.inst).getActions()) {
			actions.add(action.dump());
		}
		map.put("actions", actions.toArray(new HashMap[actions.size()]));
		return map;
	}
	
}

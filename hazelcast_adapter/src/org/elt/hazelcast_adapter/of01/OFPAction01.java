package org.elt.hazelcast_adapter.of01;

import java.util.Map;

import org.elt.hazelcast_adapter.of.OFPAction;

public class OFPAction01 extends OFPAction {
	private static final long serialVersionUID = 2673843360957500505L;
	short type;
	Map<String, Object> map;
	
	@Override
	public void fromJSON(Map<String, Object> map) {
		// TODO: Different action types.
		this.type = (short)(long)map.get("type");// Integer.parseInt((String)map.get("type"));
		this.map = map;
	}

	@Override
	public Map<String, Object> dump() {
		// Map<String, Object> map = new HashMap<String, Object>();
		// map.put("type", (((int)this.type) & 0xFFFF));
		return this.map;
	}

}

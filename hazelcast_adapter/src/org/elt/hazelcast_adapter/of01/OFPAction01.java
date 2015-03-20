package org.elt.hazelcast_adapter.of01;

import java.util.HashMap;
import java.util.Map;

import org.elt.hazelcast_adapter.of.OFPAction;

public class OFPAction01 extends OFPAction {
	private static final long serialVersionUID = 2673843360957500505L;
	short type;
	Map<String, Object> map;
	
	public OFPAction01() {}
	
	public OFPAction01(short type, Map<String, Object> map) {
		this.type = type;
		this.map = map;
	}
	
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

	@Override
	public OFPAction01 clone() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.putAll(this.map);
		return new OFPAction01(type, map);
	}
}

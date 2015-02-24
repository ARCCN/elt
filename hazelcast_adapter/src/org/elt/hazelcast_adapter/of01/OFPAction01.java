package org.elt.hazelcast_adapter.of01;

import java.util.HashMap;
import java.util.Map;

import org.elt.hazelcast_adapter.of.OFPAction;

public class OFPAction01 extends OFPAction {
	short type;
	
	@Override
	public void fromJSON(Map map) {
		// TODO: Different action types.
		this.type = (short)(long)map.get("type");// Integer.parseInt((String)map.get("type"));
	}

	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("type", (((int)this.type) & 0xFFFF));
		return map;
	}

}

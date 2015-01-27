package org.elt.hazelcast_adapter;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import org.elt.hazelcast_adapter.unpack.IDumpable;

public class CompetitionErrorMessage implements IDumpable {
	FlowModMessage msg;
	FlowModMessage[] masked;
	FlowModMessage[] modified;
	FlowModMessage[] undefined;
	FlowModMessage[] deleted;

	public CompetitionErrorMessage(FlowModMessage msg,	FlowModMessage[] masked, 
			FlowModMessage[] modified, FlowModMessage[] undefined, 
			FlowModMessage[] deleted) {
		this.msg = msg;
		this.masked = masked;
		this.modified = modified;
		this.undefined = undefined;
		this.deleted = deleted;
	}
	
	@Override
	public Map<String, Object> dump() throws Exception {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("msg", this.msg.dump());
		ArrayList<Map<String, Object>> ms = new ArrayList<Map<String, Object>>();
		for (FlowModMessage m: this.masked)
			ms.add(m.dump());
		map.put("masked", ms.toArray(new HashMap[ms.size()]));
		
		ms = new ArrayList<Map<String, Object>>();
		for (FlowModMessage m: this.modified)
			ms.add(m.dump());
		map.put("modified", ms.toArray(new HashMap[ms.size()]));
		
		ms = new ArrayList<Map<String, Object>>();
		for (FlowModMessage m: this.undefined)
			ms.add(m.dump());
		map.put("undefined", ms.toArray(new HashMap[ms.size()]));
		
		ms = new ArrayList<Map<String, Object>>();
		for (FlowModMessage m: this.deleted)
			ms.add(m.dump());
		map.put("deleted", ms.toArray(new HashMap[ms.size()]));
		return map;
	}

	
}

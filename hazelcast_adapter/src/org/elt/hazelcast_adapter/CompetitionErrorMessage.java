package org.elt.hazelcast_adapter;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import org.elt.hazelcast_adapter.unpack.IDumpable;

public class CompetitionErrorMessage implements IDumpable {
	
	public class CompetitionError implements IDumpable {
		String name;
		FlowModMessage key;
		FlowModMessage[] value;
		
		public CompetitionError(String name, FlowModMessage key, FlowModMessage[] value) {
			this.name = name;
			this.key = key;
			this.value = value;
		}
		
		@Override
		public Map<String, Object> dump() {
			Map<String, Object> map = new HashMap<String, Object>();
			map.put("name", name);
			map.put("key", key.dump());
			@SuppressWarnings("unchecked")
			Map<String, Object>[] val = new HashMap[value.length];
			for (int i = 0; i < value.length; ++i) {
				val[i] = value[i].dump();
			}
			map.put("value", val);
			return map;
		}
	}
	
	ArrayList<CompetitionError> errors;
	
	public CompetitionErrorMessage() {
		this.errors = new ArrayList<CompetitionError>();
	}
	
	public void addError(String name, FlowModMessage key, FlowModMessage[] value) {
		this.errors.add(new CompetitionError(name, key, value));
	}
	
	/*
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
	}*/
	
	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("_name", "CompetitionErrorMessage");
		ArrayList<Map<String, Object>> errs = new ArrayList<Map<String, Object>>();
		for (CompetitionError err: this.errors) {
			errs.add(err.dump());
		}
		map.put("errors", errs.toArray(new HashMap[errs.size()]));
		/*
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
		map.put("deleted", ms.toArray(new HashMap[ms.size()]));*/
		return map;
	}

	
}

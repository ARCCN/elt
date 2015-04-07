package org.elt.hazelcast_flow_table.proto;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import org.elt.hazelcast_flow_table.unpack.IDumpable;

public class CompetitionErrorMessage implements IDumpable, Serializable {

	private static final long serialVersionUID = -867923976542465647L;

	public class CompetitionError implements IDumpable, Serializable {

		private static final long serialVersionUID = -6074451502156055654L;
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
	
	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("_name", "CompetitionErrorMessage");
		ArrayList<Map<String, Object>> errs = new ArrayList<Map<String, Object>>();
		for (CompetitionError err: this.errors) {
			errs.add(err.dump());
		}
		map.put("errors", errs.toArray(new HashMap[errs.size()]));
		return map;
	}

	
}

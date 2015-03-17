package org.elt.hazelcast_adapter.hznode;

import java.io.Serializable;
import java.util.Map;

import org.elt.hazelcast_adapter.of.MatchPart;

public class TableEntry implements Serializable, Map.Entry<MatchPart, TableValue> {
	private static final long serialVersionUID = 4598976199388301016L;
	long id;
	MatchPart key;
	TableValue value;
	
	public TableEntry() {
	}
	
	public TableEntry(long id, MatchPart key, TableValue value) {
		this.id = id;
		this.key = key;
		this.value = value;
	}
	
	public MatchPart getKey() { return this.key; }
	public TableValue getValue() { return this.value; }
	public long getId() { return this.id; }

	@Override
	public TableValue setValue(TableValue value) {
		TableValue old = this.value;
		this.value = value;
		return old;
	}
}

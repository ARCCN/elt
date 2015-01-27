package org.elt.hazelcast_adapter.hznode;

import java.io.Serializable;

import org.elt.hazelcast_adapter.TableEntryTag;
import org.elt.hazelcast_adapter.of.OFPRule;

public class TableEntry implements Serializable {
	OFPRule rule;
	TableEntryTag tag;
	
	public TableEntry() {
	}
	
	public TableEntry(OFPRule rule, TableEntryTag tag) {
		this.rule = rule;
		this.tag = tag;
	}
}

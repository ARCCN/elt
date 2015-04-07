package org.elt.hazelcast_flow_table.proto;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import org.elt.hazelcast_flow_table.unpack.IDumpable;
import org.elt.hazelcast_flow_table.unpack.ILoadable;

public class TableEntryTag implements Serializable, ILoadable, IDumpable, Cloneable {

	private static final long serialVersionUID = 2308556032230029851L;
	Set<String> apps;
	Set<Long> nodes;
	int appsLength;
	
	public TableEntryTag() {
		this.apps = new HashSet<String>();
		this.appsLength = this.apps.size();
		this.nodes = new HashSet<Long>();
	}
	
	public TableEntryTag(String[] apps, long node) {
		this.apps = new HashSet<String>(Arrays.asList(apps));
		this.appsLength = this.apps.size();
		this.nodes = new HashSet<Long>();
		this.nodes.add(node);
	}
	
	public TableEntryTag(Set<String> apps, Set<Long> nodes) {
		this.apps = apps;
		this.nodes = nodes;
	}
	
	public void addNode(long node) { this.nodes.add(node); }
	
	public void addApps(String[] apps) {
		this.apps.addAll(Arrays.asList(apps));
		this.appsLength = this.apps.size();
	}
	
	public Set<String> getApps() { return this.apps; }
	public Set<Long> getNodes() { return this.nodes; }
	public int getAppsLength() { return this.appsLength; }
	
	public void update(TableEntryTag other) { 
		this.apps.addAll(other.apps);
		this.appsLength = this.apps.size();
		this.nodes.addAll(other.nodes);
	}

	@Override
	public void fromJSON(Map<String, Object> map) throws Exception {
		this.apps = new HashSet<String>();
		try {
			Object[] objs = (Object [])map.get("apps");
			for (int i=0; i < objs.length; ++i)
				this.apps.add((String)objs[i]);
		}
		catch (Throwable e) {}
		this.appsLength = this.apps.size();
		this.nodes = new HashSet<Long>();
		try {
			Object[] objs = (Object [])map.get("nodes");
			for (int i=0; i < objs.length; ++i)
				this.nodes.add((Long)objs[i]);
		}
		catch (Throwable e) {}
	}

	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("apps", this.apps.toArray(new String[this.apps.size()]));
		ArrayList<String> nds = new ArrayList<String>();
		for (Long nd: this.nodes)
			nds.add(Long.toString(nd));
		map.put("nodes", nds.toArray(new String[nds.size()]));
		return map;
	}
	
	@Override
	public TableEntryTag clone() {
		Set<String> new_apps = new HashSet<String>();
		Set<Long> new_nodes = new HashSet<Long>();
		new_apps.addAll(apps);
		new_nodes.addAll(nodes);
		return new TableEntryTag(new_apps, new_nodes);
	}
}

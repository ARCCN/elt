package org.elt.hazelcast_adapter;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import org.elt.hazelcast_adapter.unpack.IDumpable;
import org.elt.hazelcast_adapter.unpack.ILoadable;

public class TableEntryTag implements Serializable, ILoadable, IDumpable {
	Set<String> apps;
	Set<Long> nodes;
	public int apps_length;
	
	public TableEntryTag() {
		this.apps = new HashSet<String>();
		this.apps_length = this.apps.size();
		this.nodes = new HashSet<Long>();
	}
	
	public TableEntryTag(String[] apps, long node) {
		this.apps = new HashSet<String>(Arrays.asList(apps));
		this.apps_length = this.apps.size();
		this.nodes = new HashSet<Long>();
		this.nodes.add(node);
	}
	
	public void addNode(long node) { this.nodes.add(node); }
	
	public void addApps(String[] apps) {
		this.apps.addAll(Arrays.asList(apps));
		this.apps_length = this.apps.size();
	}
	
	public Set<String> getApps() { return this.apps; }
	public Set<Long> getNodes() { return this.nodes; }
	
	public void update(TableEntryTag other) { 
		this.apps.addAll(other.apps);
		this.apps_length = this.apps.size();
		this.nodes.addAll(other.nodes);
	}

	@Override
	public void fromJSON(Map map) throws Exception {
		// TODO: May fall cause we don't have node in map.
		this.apps = new HashSet<String>();
		try {
			Object[] objs = (Object [])map.get("apps");
			for (int i=0; i < objs.length; ++i)
				this.apps.add((String)objs[i]);
		}
		catch (Throwable e) {}
		this.apps_length = this.apps.size();
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
}

package elt.ControllerInteraction.Messages;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

import org.eclipse.jetty.util.ajax.JSON.Output;

import elt.ControllerInteraction.JsonParser.IDumpable;
import elt.ControllerInteraction.JsonParser.ILoadable;

public class Component implements IDumpable, ILoadable {
	protected String name = "";
	protected ComponentParam[] params = new ComponentParam[0];
	
	public Component() {}
	
	public Component(String name, ComponentParam[] params) {
		this.name = name;
		this.params = params;
	}
	
	public String getName() {
		return name;
	}
	
	public ComponentParam[] getParams() {
		return params;
	}

	@Override
	public void fromJSON(Map map) {
		String name = (String)map.get("name");
		if (name == null)
			return;
		name = name.trim();
		if (name.length() == 0)
			return;
		this.name = name;
		Object[] params = (Object[]) map.get("params");
		if (params == null)
			return;
		this.params = new ComponentParam[params.length];
		int i = 0;
		for (Object param: params) {
			ComponentParam p = new ComponentParam();
			p.fromJSON((Map)param);
			this.params[i++] = p;
		}
	}

	public void toJSON(Output out) {
		out.add(dump());
	}

	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("name", name);
		ArrayList<Map> params = new ArrayList<Map>();
		for (ComponentParam p: this.params) {
			params.add(p.dump());
		}
		map.put("params", params);
		return map;
	}
}

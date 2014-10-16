package elt.ControllerInteraction.Messages;

import java.util.HashMap;
import java.util.Map;

import org.eclipse.jetty.util.ajax.JSON.Output;

import elt.ControllerInteraction.JsonParser.IDumpable;
import elt.ControllerInteraction.JsonParser.ILoadable;

public class ComponentParam implements IDumpable, ILoadable {
	String name = "";
	boolean has_default = false;
	String dflt;
	
	ComponentParam() {}
	
	public String getName() {
		return name;
	}
	
	public boolean hasDefault() {
		return has_default;
	}
	
	public String getDefault() {
		if (!has_default) {
			return null;
		}
		return dflt;
	}
	
	ComponentParam(String name, boolean has_default, String dflt) {
		this.name = name;
		this.has_default = has_default;
		this.dflt = dflt;
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
		Object hdef = map.get("has_default");
		if (hdef == null)
			return;
		this.has_default = (boolean)hdef;
		if (this.has_default) {
			this.dflt = (String)map.get("default");
		}
	}

	public void toJSON(Output out) {
		out.add(dump());
	}

	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("name", name);
		map.put("has_default", has_default);
		map.put("default", dflt);
		return map;
	}
}

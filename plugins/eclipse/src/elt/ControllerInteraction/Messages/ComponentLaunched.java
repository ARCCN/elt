package elt.ControllerInteraction.Messages;

import java.util.HashMap;
import java.util.Map;

public class ComponentLaunched extends ControllerMessage {
	public static String _name = "component_launched";
	protected String component = "";
	
	public ComponentLaunched() {}
	
	public ComponentLaunched(String component) {
		if (component == null)
			return;
		component = component.trim();
		if (component.length() > 0)
			this.component = component;
	}
	
	public String getComponent() {
		return component;
	}
	
	@Override
	public void fromJSON(Map map) {
		if (!isMe(map))
			return;
		String component = (String)map.get("component");
		if (component == null)
			return;
		component = component.trim();
		if (component.length() > 0)
			this.component = component;
	}

	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("_name", ComponentLaunched._name);
		map.put("component", component);
		return map;
	}
}

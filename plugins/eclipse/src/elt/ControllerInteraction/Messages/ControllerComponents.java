package elt.ControllerInteraction.Messages;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class ControllerComponents extends ControllerMessage {
	public static String _name = "controller_components";
	protected Component[] components = new Component[0];
	
	public ControllerComponents() {}
	
	public ControllerComponents(Component[] components) {
		this.components = components;
	}
	
	public Component[] getComponents() {
		return components;
	}
	
	@Override
	public void fromJSON(Map map) {
		if (!isMe(map))
			return;
		Object[] components = (Object[]) map.get("components");
		if (components == null)
			return;
		this.components = new Component[components.length];
		int i = 0;
		for (Object comp: components) {
			Component c = new Component();
			c.fromJSON((Map)comp);
			this.components[i++] = c;
		}
	}

	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("_name", ControllerComponents._name);
		ArrayList<Map> components = new ArrayList<Map>();
		for (Component c: this.components) {
			components.add(c.dump());
		}
		map.put("components", components);
		return map;
	}
}

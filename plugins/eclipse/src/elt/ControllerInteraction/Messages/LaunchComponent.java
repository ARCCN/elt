package elt.ControllerInteraction.Messages;

import java.util.HashMap;
import java.util.Map;

public class LaunchComponent extends ControllerMessage {
	public static String _name = "launch_component";
	protected String component = "";
	protected String[] args = new String[0];
	
	protected void fill(String component, String[] args) {
		if (component == null)
			return;
		component = component.trim();
		if (component.length() == 0 || component.split(" ").length > 1)
			return;
		this.component = component;
		if (args == null)
			return;
		this.args = new String[args.length];
		int i = 0;
		for (String arg: args) {
			this.args[i++] = arg.trim();
		}
	}
	
	public LaunchComponent() {}
	
	public LaunchComponent(String component, String[] args) {
		fill(component, args);
	}
	
	@Override
	public void fromJSON(Map map) {
		if (!isMe(map))
			return;
		String component = (String)map.get("component");
		String[] args = (String[]) map.get("args");
		fill(component, args);
	}
	
	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("_name", LaunchComponent._name);
		map.put("component", this.component);
		map.put("args", args);
		return map;
	}
}

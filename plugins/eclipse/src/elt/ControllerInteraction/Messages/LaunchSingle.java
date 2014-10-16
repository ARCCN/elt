package elt.ControllerInteraction.Messages;

import java.util.Map;

public class LaunchSingle extends LaunchComponent {
	public static String _name = "launch_single";
	
	public LaunchSingle() {}
	
	public LaunchSingle(String component, String[] args) {
		super(component, args);
	}
	
	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = super.dump();
		map.put("_name", this._name);
		return map;
	}
}

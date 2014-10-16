package elt.ControllerInteraction.Messages;

import java.util.HashMap;
import java.util.Map;

public class LaunchHierarchical extends LaunchComponent {
	public static String _name = "launch_hierarchical";
	
	public LaunchHierarchical() {}
	
	public LaunchHierarchical(String component, String[] args) {
		super(component, args);
	}
	
	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = super.dump();
		map.put("_name", this._name);
		return map;
	}
}

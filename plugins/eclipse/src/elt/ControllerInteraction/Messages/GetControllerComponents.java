package elt.ControllerInteraction.Messages;

import java.util.HashMap;
import java.util.Map;


public class GetControllerComponents extends ControllerMessage {
	public static String _name = "get_controller_components";
	
	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = super.dump();
		map.put("_name", this._name);
		return map;
	}
}

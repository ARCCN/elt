package elt.ControllerInteraction.Messages;

import java.util.Map;

public class StopController extends ControllerMessage {
	public static String _name = "stop_controller";
	
	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = super.dump();
		map.put("_name", this._name);
		return map;
	}
}

package elt.ControllerInteraction.Messages;

import java.util.HashMap;
import java.util.Map;

public class StartController extends ControllerMessage {
	public static String _name = "start_controller";
	protected String args = "";
	
	public StartController() {}
	
	public StartController(String args) {
		this.args = args;
	}
	
	@Override
	public void fromJSON(Map map) {
		if (!isMe(map))
			return;
		String args = (String)map.get("args");
		if (args != null)
			this.args = args;
	}
	
	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("_name", this._name);
		map.put("args", args);
		return map;
	}
}

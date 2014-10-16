package elt.ControllerInteraction.Messages;

import java.util.HashMap;
import java.util.Map;

public class ControllerStatus extends ControllerMessage {
	public static String _name = "controller_status";
	protected String status = "no_data";
	enum Status {no_data, running, stopped};
	
	public ControllerStatus() {}
	
	public ControllerStatus(String status) {
		if (Status.valueOf(status) != null)
			this.status = status;
	}
	
	public String getStatus() {
		return status;
	}
	
	@Override
	public void fromJSON(Map map) {
		if (!isMe(map))
			return;
		String status = (String)map.get("status");
		if (Status.valueOf(status) != null)
			this.status = status;
	}

	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("_name", this._name);
		map.put("status", status);
		return map;
	}
}

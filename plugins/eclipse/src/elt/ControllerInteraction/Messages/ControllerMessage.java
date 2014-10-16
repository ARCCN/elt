package elt.ControllerInteraction.Messages;

import java.util.HashMap;
import java.util.Map;

import org.eclipse.jetty.util.ajax.JSON.Output;

import elt.ControllerInteraction.JsonParser.IDumpable;
import elt.ControllerInteraction.JsonParser.ILoadable;

public class ControllerMessage implements IDumpable, ILoadable {
	public static String _name = "controller_message";

	protected boolean isMe(Map map) {
		String my_name;
		try {
			my_name = (String)this.getClass().getField("_name").get(this);
		} catch (IllegalArgumentException | IllegalAccessException
				| NoSuchFieldException | SecurityException e) {
			return false;
		}
		// System.out.println(String.format("%s ~ %s", map.get("_name"), my_name));
		return my_name.equals(map.get("_name"));
	}
	
	@Override
	public void fromJSON(Map map) {		
	}

	public void toJSON(Output out) {
		out.add(dump());
	}

	@Override
	public Map<String, Object> dump() {
		Map<String, Object> map = new HashMap<String, Object>();
		map.put("_name", this._name);
		return map;
	}
}

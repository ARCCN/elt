package elt.ControllerInteraction.JsonParser;

import java.util.Map;

import org.eclipse.jetty.util.ajax.JSON;

import elt.ControllerInteraction.Messages.ControllerMessage;
import elt.ControllerInteraction.Messages.MessageRegistry;

public class JsonParser {
	
	protected MessageRegistry registry = new MessageRegistry();
	
	public ControllerMessage parseMessage(String data) 
			throws InstantiationException, IllegalAccessException {
		Object obj = JSON.parse(data);
		Map map = (Map)obj;
		String _name = (String)map.get("_name");
		Class<? extends ControllerMessage> c = registry.get(_name);
		if (c == null)
			return null;
		ControllerMessage msg = c.newInstance();
		msg.fromJSON(map);
		return msg;
	}
	
	public String encodeMessage(IDumpable message) {
		String json = JSON.toString(message.dump());
		return json;
	}
}

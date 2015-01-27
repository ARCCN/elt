package org.elt.hazelcast_adapter.unpack;

import java.io.IOException;
import java.io.Reader;
import java.util.Map;

import org.eclipse.jetty.util.ajax.JSON;
import org.elt.hazelcast_adapter.FlowModMessage;


public class JsonParser {
	
	public static FlowModMessage decodeMessage(Map map) {
		String _name = (String)map.get("_name");
		if (!_name.equals("FlowModMessage"))
			return null;
		FlowModMessage msg = new FlowModMessage();
		try {
			msg.fromJSON(map);
		}
		catch (Exception e) { return null; }
		return msg;
	}
	
	public static FlowModMessage parseMessage(String data) 
			throws InstantiationException, IllegalAccessException {
		Object obj = JSON.parse(data);
		Map map = (Map)obj;
		return decodeMessage(map);
	}
	
	public static FlowModMessage parseMessage(Reader rd) 
			throws InstantiationException, IllegalAccessException, IOException {
		Object obj = JSON.parse(rd);
		Map map = (Map)obj;
		return decodeMessage(map);
	}

	
	public static String encodeMessage(IDumpable message) throws Exception {
		String json = JSON.toString(message.dump());
		return json;
	}
}

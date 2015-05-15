package org.elt.hazelcast_flow_table.unpack;

import java.io.IOException;
import java.io.Reader;
import java.util.Map;

import org.eclipse.jetty.util.ajax.JSON;
import org.elt.hazelcast_flow_table.proto.FlowModMessage;


public class JsonParser {
	
	public static FlowModMessage decodeMessage(Map<String, Object> map) {
		String _name = (String)map.get("_name");
		if (!_name.equals("FlowModMessage"))
			return null;
		FlowModMessage msg = new FlowModMessage();
		try {
			msg.fromJSON(map);
		}
		catch (Exception e) { e.printStackTrace(); return null; }
		return msg;
	}
	
	public static FlowModMessage parseMessage(String data) 
			throws InstantiationException, IllegalAccessException {
		Object obj = JSON.parse(data);
		@SuppressWarnings("unchecked")
		Map<String, Object> map = (Map<String, Object>)obj;
		return decodeMessage(map);
	}
	
	public static FlowModMessage parseMessage(Reader rd) 
			throws InstantiationException, IllegalAccessException, IOException {
		Object obj = JSON.parse(rd);
		if (obj == null) {
			return null;
		}
		@SuppressWarnings("unchecked")
		Map<String, Object> map = (Map<String, Object>)obj;
		FlowModMessage msg = decodeMessage(map);
		return msg;
	}

	public static String encodeMessage(IDumpable message) {
		
		if (message == null) {
			return "";
		}
		String json = JSON.toString(message.dump());
		return json;
	}
}
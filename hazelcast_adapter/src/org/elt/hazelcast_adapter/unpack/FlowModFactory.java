package org.elt.hazelcast_adapter.unpack;

import java.util.Map;

import org.elt.hazelcast_adapter.of.OFPFlowMod;
import org.elt.hazelcast_adapter.of01.OFPFlowMod01;

public class FlowModFactory {
	public static OFPFlowMod create(Map map) {
		int version = (int)((long)map.get("version")); //Integer.parseInt((String)map.get("version"));
		Class<? extends OFPFlowMod> c;
		
		switch(version) {
		case 1: 
			c = OFPFlowMod01.class;
			break;
		default:
			c = null;
			break;
		};
		
		if (c == null)
			return null;
		try {
			OFPFlowMod instance = c.newInstance();
			instance.fromJSON(map);
			return instance;
		}
		catch (Exception e) {
			return null;
		}
	}
	
	public static Class<? extends OFPFlowMod> getClass(byte version) {
		Class<? extends OFPFlowMod> c;
		switch(version) {
		case 1: 
			c = OFPFlowMod01.class;
			break;
		default:
			c = null;
			break;
		};
		return c;
	}
}

package org.elt.hazelcast_flow_table.unpack;

import java.util.Map;

public interface ILoadable {
	public void fromJSON(Map<String, Object> map) throws Exception;
}

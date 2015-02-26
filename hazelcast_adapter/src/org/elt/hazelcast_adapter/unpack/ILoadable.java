package org.elt.hazelcast_adapter.unpack;

import java.util.Map;

public interface ILoadable {
	public void fromJSON(Map<String, Object> map) throws Exception;
}

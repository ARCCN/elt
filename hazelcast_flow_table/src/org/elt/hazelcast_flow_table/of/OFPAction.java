package org.elt.hazelcast_flow_table.of;

import java.io.Serializable;

import org.elt.hazelcast_flow_table.unpack.IDumpable;
import org.elt.hazelcast_flow_table.unpack.ILoadable;

public abstract class OFPAction implements ILoadable, IDumpable, Serializable, Cloneable {

	private static final long serialVersionUID = -1890488068102575435L;
	
}

package org.elt.hazelcast_adapter.of;

import java.io.Serializable;

import org.elt.hazelcast_adapter.unpack.IDumpable;
import org.elt.hazelcast_adapter.unpack.ILoadable;

public abstract class OFPAction implements ILoadable, IDumpable, Serializable {

	private static final long serialVersionUID = -1890488068102575435L;
	
}
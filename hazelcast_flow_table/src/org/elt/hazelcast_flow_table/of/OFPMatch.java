package org.elt.hazelcast_flow_table.of;

import java.io.Serializable;

import org.elt.hazelcast_flow_table.unpack.IDumpable;
import org.elt.hazelcast_flow_table.unpack.ILoadable;

public abstract class OFPMatch implements ILoadable, Comparable, IDumpable, Serializable {

	private static final long serialVersionUID = -8148843311775210235L;

	public OFPMatch() {}
	
	public abstract IP getSrcIp();
	public abstract IP getDstIp();
}

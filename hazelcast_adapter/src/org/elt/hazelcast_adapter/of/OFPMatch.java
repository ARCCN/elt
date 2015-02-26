package org.elt.hazelcast_adapter.of;

import java.io.Serializable;

import org.elt.hazelcast_adapter.unpack.IDumpable;
import org.elt.hazelcast_adapter.unpack.ILoadable;

public abstract class OFPMatch implements ILoadable, Comparable, IDumpable, Serializable {

	private static final long serialVersionUID = -8148843311775210235L;

	public OFPMatch() {}
	/*
	public int widerThan(OFPMatch m) {
		return 0;
	}
	*/
}

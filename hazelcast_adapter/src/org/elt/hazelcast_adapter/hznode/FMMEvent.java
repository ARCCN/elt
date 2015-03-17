package org.elt.hazelcast_adapter.hznode;

import java.io.Serializable;

import org.elt.hazelcast_adapter.FlowModMessage;

public class FMMEvent implements Serializable {

	private static final long serialVersionUID = 6455848657151288631L;
	private FlowModMessage msg;
	private long source;

	public FMMEvent(FlowModMessage msg, long source) {
		this.msg = msg;
		this.source = source;
	}
	
	public FlowModMessage getMsg() { return this.msg; }
	public long getSource() { return this.source; }
}

package org.elt.hazelcast_adapter;


public interface IFlowTable {
	public CompetitionErrorMessage updateErrorChecking(FlowModMessage msg);
	public void shutdown();
}

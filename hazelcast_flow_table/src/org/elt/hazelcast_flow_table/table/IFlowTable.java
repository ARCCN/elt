package org.elt.hazelcast_flow_table.table;

import org.elt.hazelcast_flow_table.proto.CompetitionErrorMessage;
import org.elt.hazelcast_flow_table.proto.FlowModMessage;



public interface IFlowTable {
	public CompetitionErrorMessage updateErrorChecking(FlowModMessage msg);
	public void shutdown();
}

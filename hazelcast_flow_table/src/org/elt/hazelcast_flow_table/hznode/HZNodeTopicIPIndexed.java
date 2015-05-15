package org.elt.hazelcast_flow_table.hznode;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;
import java.util.Queue;
import java.util.concurrent.Callable;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.Random;

import org.elt.hazelcast_flow_table.proto.CompetitionErrorMessage;
import org.elt.hazelcast_flow_table.proto.FlowModMessage;
import org.elt.hazelcast_flow_table.table.IFlowTable;

import com.hazelcast.core.Hazelcast;
import com.hazelcast.core.HazelcastInstance;
import com.hazelcast.core.HazelcastInstanceAware;
import com.hazelcast.core.IMap;
import com.hazelcast.core.ITopic;
import com.hazelcast.core.IdGenerator;
import com.hazelcast.core.Message;
import com.hazelcast.core.MessageListener;
import com.hazelcast.core.ReplicatedMap;

public class HZNodeTopicIPIndexed implements IFlowTable,
	MessageListener<FMMEvent> {

	HazelcastInstance instance;
	String name;
	long id;
	Lock tableLock = new ReentrantLock();
	Map<String, IPIndexedFlowTable> tables = new HashMap<String, IPIndexedFlowTable>();
	Map<String, Lock> locks = new HashMap<String, Lock>();
	ReplicatedMap<Long, String> nodeMap;
	ReplicatedMap<String, Long> dpidToNode;
	IdGenerator gen;
	ITopic<CompetitionErrorMessage> replies;
	ITopic<FMMEvent> requests;
	Queue<CompetitionErrorMessage> replyQueue = new ConcurrentLinkedQueue<CompetitionErrorMessage>();

	public class UpdateTask
	implements Callable<CompetitionErrorMessage>, Serializable, HazelcastInstanceAware
	{

		private static final long serialVersionUID = 2505663945800111489L;
		private transient HazelcastInstance hazelcastInstance;
		protected String dpid;
		protected FlowModMessage msg;
	
		public UpdateTask(String dpid, FlowModMessage msg) {
			this.dpid = dpid;
			this.msg = msg;
		}
		
		public void setHazelcastInstance( HazelcastInstance hazelcastInstance ) {
		    this.hazelcastInstance = hazelcastInstance;
		}
		
		public CompetitionErrorMessage call() {
		    IMap<String, IPIndexedFlowTable> tables = hazelcastInstance.getMap( "tables" );
		    tables.lock(dpid);
		    IPIndexedFlowTable table = tables.get(dpid);
		    CompetitionErrorMessage error = table.updateErrorChecking(msg);
		    tables.put(dpid, table);
		    tables.unlock(dpid);
		    return error;
		}
	}
	
	public class ReplyListener implements MessageListener<CompetitionErrorMessage> {
		
		private Queue<CompetitionErrorMessage> replyQueue;
		
		public ReplyListener(Queue<CompetitionErrorMessage> replyQueue) {
			this.replyQueue = replyQueue;
		}
		
		@Override
		public void onMessage(Message<CompetitionErrorMessage> arg0) {
			replyQueue.add(arg0.getMessageObject());
		}
	}
	
	public HZNodeTopicIPIndexed() {
		this.instance = Hazelcast.newHazelcastInstance();
		this.gen = this.instance.getIdGenerator("gen");
		this.id = this.gen.newId();
		this.name = this.instance.getCluster().getLocalMember().toString();
		this.nodeMap = this.instance.getReplicatedMap("nodeMap");
		this.nodeMap.put(this.id, this.name);
		this.dpidToNode = this.instance.getReplicatedMap("dpidToNode");
		this.replies = this.instance.getTopic(String.valueOf(this.id) + "-reply");
		this.replies.addMessageListener(new ReplyListener(replyQueue));
		this.requests = this.instance.getTopic(String.valueOf(this.id) + "-request");
		this.requests.addMessageListener(this);
	}
	
	@SuppressWarnings("unused")
	protected CompetitionErrorMessage runUpdateTask(String dpid, FlowModMessage msg) {
		Long node = dpidToNode.get(dpid);
		if (node == null) {
			Long targetId = id;
			// TODO: For tests. Pick random node.
			if (false) {			
				Random generator = new Random();
				Object[] keys = this.nodeMap.keySet().toArray();
				targetId = (Long)keys[generator.nextInt(keys.length)];
			}
			// Take responsibility for this dpid.
			dpidToNode.put(dpid, targetId);
			node = targetId;
			System.err.print(String.format("---Taken responsibility for dpid %s -> %s\n",
								dpid, targetId.toString()));
		}
		ITopic<FMMEvent> topic = this.instance.getTopic(
				String.valueOf(node) + "-request");
		topic.publish(new FMMEvent(msg, id));
		
		// Wait for response.
		// TODO: Async?
		while (this.replyQueue.isEmpty()) {
			try {
				Thread.sleep(1);
			} catch (InterruptedException e) {
			}
		}
		CompetitionErrorMessage error = this.replyQueue.poll();
		return error;
	}
	
	@Override
	public CompetitionErrorMessage updateErrorChecking(FlowModMessage msg) {
		// TODO: Maybe use Executor?
		if (!msg.hasNode()) {
			msg.setNode(this.id);
		}
				
		String dpid = msg.getDpid();
		return runUpdateTask(dpid, msg);
	}

	@Override
	public void shutdown() {
		IPIndexedFlowTable table;
		tableLock.lock();
		for (String dpid: tables.keySet()) {
			table = tables.get(dpid);
			Lock lock = locks.get(dpid);
			lock.lock();
			table.shutdown();
			lock.unlock();
		}
		tableLock.unlock();
		this.instance.shutdown();
	}

	@Override
	public void onMessage(Message<FMMEvent> arg0) {
		// Process request.
		// TODO: Separate thread.
		FlowModMessage msg = arg0.getMessageObject().getMsg();
		String dpid = msg.getDpid();
		tableLock.lock();
		IPIndexedFlowTable table = tables.get(dpid);
		if (table == null) {
			table = new IPIndexedFlowTable(dpid);
			tables.put(dpid, table);
			locks.put(dpid, new ReentrantLock());
		}
		tableLock.unlock();
		Lock lock = locks.get(dpid);
		lock.lock();
	    CompetitionErrorMessage error = table.updateErrorChecking(msg);
	    lock.unlock();
	   
	    // Send reply.
	    ITopic<CompetitionErrorMessage> topic = this.instance.getTopic(String.valueOf(
	    		arg0.getMessageObject().getSource()) + "-reply");
	    topic.publish(error);
	}
}

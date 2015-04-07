package org.elt.hazelcast_flow_table;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Reader;
import java.io.Writer;

import org.elt.hazelcast_flow_table.hznode.HZNodeTopicIPIndexed;
import org.elt.hazelcast_flow_table.proto.CompetitionErrorMessage;
import org.elt.hazelcast_flow_table.proto.FlowModMessage;
import org.elt.hazelcast_flow_table.table.IFlowTable;
import org.elt.hazelcast_flow_table.unpack.JsonParser;

public class HZAdapter {
	public static FlowModMessage read(Reader rd) throws InstantiationException, IllegalAccessException, IOException {
		return JsonParser.parseMessage(rd);
	}
	
	public static void write(Writer wr, String s) throws IOException {
		wr.write(s);
	}
	
	public static void flush(Writer wr) throws IOException {
		wr.flush();
	}
	
	public static void main(String[] args) {
		System.err.println("Starting");
		IFlowTable node = new HZNodeTopicIPIndexed();
		/*
		try {
			System.setIn(new FileInputStream("/home/lantame/SDN/ELT/stress_test.fifo"));
		} catch (FileNotFoundException e1) {
		}
		*/
		/*
		try {
			Thread.sleep(5000);
		} catch (InterruptedException e1) {
		}
		*/
		BufferedReader rd = new BufferedReader(new InputStreamReader(System.in));
		BufferedWriter wr = new BufferedWriter(new OutputStreamWriter(System.out));
		while (true) {
			try {
				// FlowModMessage msg = JsonParser.parseMessage(rd);
				FlowModMessage msg = read(rd);
				if (msg == null)
					break;
				// System.err.println(JsonParser.encodeMessage(msg));
				CompetitionErrorMessage res = node.updateErrorChecking(msg);
				// System.err.println(JsonParser.encodeMessage(res));
				write(wr, JsonParser.encodeMessage(res));
				flush(wr);
				//wr.write(JsonParser.encodeMessage(res));
			} catch (IOException e) {
				System.err.println("EOF");
				break;
			} catch (InstantiationException | IllegalAccessException | RuntimeException e) {
				// Bad message. Ignore?
				e.printStackTrace();
				System.err.println("Unable to decode message");
				try {
					Thread.sleep(1000, 0);
				}
				catch (Throwable ex) {}
				continue;
			} catch (Exception e) {
				System.err.println("Unable to encode message");
			}
				
		}
		/*
		try {
			Thread.sleep(5000);
		}
		catch(Throwable e) {}
		*/
		node.shutdown();
	}

}

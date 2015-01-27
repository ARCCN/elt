package org.elt.hazelcast_adapter;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;

import org.elt.hazelcast_adapter.hznode.HZNode;
import org.elt.hazelcast_adapter.unpack.JsonParser;

public class HZAdapter {

	public static void main(String[] args) {
		/* We get JSON messages separated with a newline. */
		BufferedReader rd = new BufferedReader(new InputStreamReader(System.in));
		BufferedWriter wr = new BufferedWriter(new OutputStreamWriter(System.out));
		HZNode node = new HZNode();
		// String line;
		while (true) {
			try {
				// line = rd.readLine();
				FlowModMessage msg = JsonParser.parseMessage(rd);
				CompetitionErrorMessage res = node.updateErrorChecking(msg);
				wr.write(JsonParser.encodeMessage(res));
				wr.newLine();
				wr.flush();
			} catch (IOException e) {
				System.err.println("EOF");
				break;
			} catch (InstantiationException | IllegalAccessException e) {
				// Bad message. Ignore?
				System.err.println("Unable to decode message");
				continue;
			} catch (Exception e) {
				System.err.println("Unable to encode message");
			}
				
		}
	}

}

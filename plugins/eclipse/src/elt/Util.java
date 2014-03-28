package elt;

import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

public class Util {
	public static Node getChild(Node n, String name) {
		NodeList c = n.getChildNodes();
		for (int i = 0; i < c.getLength(); i++) {
			if (c.item(i).getNodeName().equalsIgnoreCase(name)) {
				return c.item(i);
			}
		}
		return null;
	}
}

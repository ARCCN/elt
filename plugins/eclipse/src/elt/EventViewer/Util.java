package elt.EventViewer;

import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

public class Util {
	public static Node getChild(Node n, String name) {
		return getChildWithIndex(n, name, 0);
	}
	
	public static Node getChildWithIndex(Node n, String name, int index) {
		NodeList c = n.getChildNodes();
		for (int i = 0; i < c.getLength(); i++) {
			if (c.item(i).getNodeName().equalsIgnoreCase(name)) {
				if (index <= 0)
					return c.item(i);
				else
					--index;
			}
		}
		return null;
	}
}

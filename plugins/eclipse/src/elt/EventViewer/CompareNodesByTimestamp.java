package elt.EventViewer;

import java.text.SimpleDateFormat;
import java.util.Comparator;
import java.util.Date;

import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

class CompareNodesByTimestamp implements Comparator<Node> {
	public String getName(Node n) {
		NodeList c = n.getChildNodes();
		String name = "";
		for (int i = 0; i < c.getLength(); i++) {
			if (c.item(i).getNodeName().equalsIgnoreCase("name")) {
				name = c.item(i).getTextContent();
				return name;
			}
		}
		return name;
	}
	
	public int compare(Node n1, Node n2) {
		String name1 = getName(n1);
		String name2 = getName(n2);
		SimpleDateFormat format = new SimpleDateFormat("dd.MM.yyyy HH:mm:ss.SSS");
		try {
			Date d1 = format.parse(name1);
			Date d2 = format.parse(name2);
			if (d1.before(d2))
				return -1;
			if (d2.before(d1))
				return 1;
			return 0;
		}
		catch(Exception e) {
			return 0;
		}
	}
}
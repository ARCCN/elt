package elt.EventViewer;

import org.eclipse.jface.viewers.LabelProvider;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

public class XMLLabelProvider extends LabelProvider {
	public String getText(Object element) {
		if (element instanceof Node) {
			Node node = (Node)element;
			if (node.getNodeName() == "#text") {
				String s = node.getNodeValue();
				if (s == "")
					return "hello";
				return s;
			}
			//Find 'name' sub-element.
			NodeList children = node.getChildNodes();
			for (int i = 0; i < children.getLength(); ++i) {
				Node child = children.item(i);
				if (child.getNodeName().equalsIgnoreCase("name")) {
					return node.getNodeName() + ": " + child.getTextContent();
				}
			}
			if (children.getLength() == 1 && children.item(0).getNodeName() == "#text") {
				return node.getNodeName() + ": " + children.item(0).getTextContent();
			}
			return node.getNodeName();
		}
		return "Unknown";
	}
}

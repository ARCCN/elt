package elt.EventViewer;

import java.util.ArrayList;

import org.eclipse.jface.viewers.ITreeContentProvider;
import org.eclipse.jface.viewers.TreeViewer;
import org.eclipse.jface.viewers.Viewer;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

public class XMLContentProvider implements ITreeContentProvider {

	private static Object[] EMPTY_ARRAY = new Object[0];
	protected TreeViewer viewer;
	protected String hide_tag;

	public XMLContentProvider(String h) {
		super();
		hide_tag = h;
	}

	@Override
	public void dispose() {
		// TODO Auto-generated method stub

	}

	@Override
	public void inputChanged(Viewer viewer, Object oldInput, Object newInput) {
		// TODO Auto-generated method stub
		this.viewer = (TreeViewer) viewer;
	}

	@Override
	public Object[] getElements(Object inputElement) {
		// TODO Auto-generated method stub
		return getChildren(inputElement);
	}

	@Override
	public Object[] getChildren(Object parentElement) {
		// TODO Auto-generated method stub
		if (parentElement instanceof Node) {
			Node parent = (Node) parentElement;
			if (parent.getNodeName().equalsIgnoreCase(hide_tag))
				return null;
			NodeList nodelist = parent.getChildNodes();
			ArrayList<Node> nodes = new ArrayList<Node>();
			for (int n = 0; n < nodelist.getLength(); ++n) {
				if (!nodelist.item(n).getNodeName().equalsIgnoreCase("name")) {
					nodes.add(nodelist.item(n));
				}
			}
			if (nodes.size() == 1 && nodes.get(0).getNodeName() == "#text") {
				return null;
			}
			return nodes.toArray();
		}
		return EMPTY_ARRAY;
	}

	@Override
	public Object getParent(Object element) {
		// TODO Auto-generated method stub
		if (element instanceof Node) {
			Node elem = (Node) element;
			return elem.getParentNode();
		}
		return null;
	}

	@Override
	public boolean hasChildren(Object element) {
		// TODO Auto-generated method stub
		if (element instanceof Node) {
			Node elem = (Node) element;
			if (elem.getNodeName().equalsIgnoreCase(hide_tag))
				return false;
			return elem.hasChildNodes();
		}
		return false;
	}

}

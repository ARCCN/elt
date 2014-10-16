package elt.EventViewer;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

public class XMLReader {
	
	public static boolean eraseBlank(Node node)
	{
		//System.out.print(node.getNodeName());
		if (node.getNodeName() == "#text")
		{
			String s = node.getNodeValue();
			for (int i = 0; i < s.length(); i++) {
		        if ((Character.isWhitespace(s.charAt(i)) == false)) {
		        	return false;
		        }
		    }
			return true;
		}
		else
		{
			NodeList nodes = node.getChildNodes();
			ArrayList<Node> remove = new ArrayList<Node>();
			//System.out.print(nodes.getLength());
			for (int i = 0; i < nodes.getLength(); ++i)
			{
				if (eraseBlank(nodes.item(i)))
				{
					remove.add(nodes.item(i));
				}
			}
			for (Node n: remove) {
				node.removeChild(n);
			}
			return false;
		}
	}
	
	public static void sort(Node node)
	{
		NodeList children = node.getChildNodes();
		ArrayList<Node> to_sort = new ArrayList<Node>();
		ArrayList<Node> not_to_sort = new ArrayList<Node>();
		for (int i = 0; i < children.getLength(); ++i) {
			Node n = children.item(i);
			if (n.getNodeName().equalsIgnoreCase("event")) {
				//Events must be sorted by timestamp
				to_sort.add(n);
			}
			else
			{
				not_to_sort.add(n);
			}
		}
		
		if (to_sort.size() == 0) {
			for (int i = 0; i < children.getLength(); ++i) {
				Node n = children.item(i);
				sort(n);
			}
			return;
		}
		else
		{
			Collections.sort(to_sort, new CompareNodesByTimestamp());
			not_to_sort.addAll(to_sort);
			for (Node n: not_to_sort) {
				node.removeChild(n);
			}
			for (Node n: not_to_sort) {
				node.appendChild(n);
			}
			return;
		}
	}
	
	protected static Document readFiles(File[] files) 
	{
		try {
			DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
			DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();
			Document root = dBuilder.newDocument();
			root.appendChild(root.createElement("root"));
			
			for (File xmlfile : files) {
				Document doc = dBuilder.parse(xmlfile);
				Element elem = doc.getDocumentElement();
				Node imported = root.importNode(elem, true);
				root.getDocumentElement().appendChild(imported);
			}
			root.getDocumentElement().normalize();
			eraseBlank(root.getDocumentElement());
			sort(root.getDocumentElement());
			return root;
		} catch (Exception e) {
		  	e.printStackTrace();
		  	return null;
		}
	}
	
	protected static File[] getFilesFromDir(String dirname)
	{
		try {
			File dir = new File(dirname);
			if (dir.isFile())
				return null;
			File [] files = dir.listFiles(new FilenameFilter() {
			    @Override
			    public boolean accept(File dir, String name) {
			        return name.endsWith(".xml");
			    }
			});
			return files;
		} catch (Exception e) {
		  	e.printStackTrace();
		  	return new File[0];
		}
	}
	
	public static Document read(String path) {
		try {
			return readFiles(getFilesFromDir(path));
		} catch (Exception e) {
		  	e.printStackTrace();
		  	return null;
		}
	}
	
	public static Document read(String[] filenames) 
	{
		try {
			ArrayList<File> files = new ArrayList<File>();
			for (String fn: filenames) {
				File f = new File(fn);
				if (f.isDirectory()) {
					for (File f1 : getFilesFromDir(fn)) {
						files.add(f1);
					}
				}
				else
				{
					files.add(f);
				}
			}
			return readFiles(files.toArray(new File[files.size()]));
		} catch (Exception e) {
		  	e.printStackTrace();
		  	return null;
		}
	}
	
	public static Document appendString(Document target, String element) 
			throws SAXException, IOException, ParserConfigurationException 
	{
		DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
		DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();
		if (target == null) {
			target = dBuilder.newDocument();
			target.appendChild(target.createElement("root"));
		}
		InputStream stream = new ByteArrayInputStream(
				element.getBytes(StandardCharsets.UTF_8));
		System.out.println(element);
		Document doc = dBuilder.parse(stream);
		Element elem = doc.getDocumentElement();
		elem.normalize();
		eraseBlank(elem);
		// We will merge new node into existing tree.
		Element adopter = target.getDocumentElement();
		NodeList nodes, subnodes;
		Node node;
		String client = "", event_type = "";
		Node type_node = null, adopted_parent = null;
		// At least two iterations: client and EventType.
		// TODO: We assume that elem has 1 "client" and 1 "EventType". 
		// TODO: Others will be lost.
		
		
		// TODO: Maybe we should use (<client>, <event_type>) index on root?
		
		// TODO: Bad code. Refactor.
		node = elem;// <client/>
		nodes = node.getChildNodes(); // <name/><event_type/>
		for (int j = 0; j < nodes.getLength(); ++j) {
			if (nodes.item(j).getNodeName().equalsIgnoreCase("name")) {
				client = nodes.item(j).getTextContent();
			} else if (nodes.item(j).getNodeName().equalsIgnoreCase("event_type")) {
				node = nodes.item(j);
				type_node = node;
				subnodes = node.getChildNodes(); // <name/><event/><event/>...
				for (int i = 0; i < subnodes.getLength(); ++i) {
					if (subnodes.item(i).getNodeName().equalsIgnoreCase("name")) {
						event_type = subnodes.item(i).getTextContent();
						break;
					}
				}
			}
		}
		
		node = adopter;
		nodes = adopter.getChildNodes(); // <client/><client/>...
		for (int i = 0; i < nodes.getLength(); ++i) {
			subnodes = nodes.item(i).getChildNodes(); // <name/><event_type/><event_type/>...
			for (int j = 0; j < subnodes.getLength(); ++j) {
				if (subnodes.item(j).getNodeName().equalsIgnoreCase("name") &&
						subnodes.item(j).getTextContent().equals(client)) {
					adopter = (Element) nodes.item(i);
					adopted_parent = elem;
					break;
				}
			}
		}
		if (adopter != node) { // We found our <client>.
			node = adopter;
			nodes = adopter.getChildNodes(); // <name/><event_type/><event_type/>...
			for (int i = 0; i < nodes.getLength(); ++i) {
				if (nodes.item(i).getNodeName().equalsIgnoreCase("event_type")) {
					subnodes = nodes.item(i).getChildNodes(); // <name/><event/><event/>...
					for (int j = 0; j < subnodes.getLength(); ++j) {
						if (subnodes.item(j).getNodeName().equalsIgnoreCase("name") &&
								subnodes.item(j).getTextContent().equals(event_type)) {
							adopter = (Element) nodes.item(i);
							adopted_parent = type_node;
							break;
						}
					}
				}
			}
			// We found something. adopted_parent != null -> 
			// adopter.adopt(adopted_parent.children \ "name")
			nodes = adopted_parent.getChildNodes();
			for (int i = 0; i < nodes.getLength(); ++i) {
				node = nodes.item(i);
				if (!node.getNodeName().equalsIgnoreCase("name")) { //<event_type/> or <event/>
					Node imported = target.importNode(node, true);
					adopter.appendChild(imported);
				}
			}
		} else {
			Node imported = target.importNode(elem, true);
			adopter.appendChild(imported);
		}
		return target;
	}
}

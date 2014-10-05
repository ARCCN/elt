package elt;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.text.SimpleDateFormat;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;



public class XMLReader {
	public static boolean erase_blank(Node node)
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
				if (erase_blank(nodes.item(i)))
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
		
		class CompareTimestamp implements Comparator<Node> {
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
		
		if (to_sort.size() == 0) {
			for (int i = 0; i < children.getLength(); ++i) {
				Node n = children.item(i);
				sort(n);
			}
			return;
		}
		else
		{
			Collections.sort(to_sort, new CompareTimestamp());
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
			erase_blank(root.getDocumentElement());
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
		//TODO: Empty target.
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
		Node imported = target.importNode(elem, true);
		target.getDocumentElement().appendChild(imported);
		return target;
	}
}

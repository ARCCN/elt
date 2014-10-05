package elt;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.util.ArrayList;
import java.util.concurrent.TimeUnit;

import javax.swing.JFileChooser;
import javax.swing.filechooser.FileFilter;
import javax.xml.parsers.ParserConfigurationException;

import org.eclipse.jetty.websocket.client.ClientUpgradeRequest;
import org.eclipse.jetty.websocket.client.WebSocketClient;
import org.eclipse.jface.action.Action;
import org.eclipse.jface.action.IMenuListener;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.IToolBarManager;
import org.eclipse.jface.viewers.TreeViewer;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.part.ViewPart;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.xml.sax.SAXException;

public class ELTView extends ViewPart implements IStringReceiver {

	protected TreeViewer treeViewer;
	protected XMLLabelProvider labelProvider;
	protected XMLContentProvider contentProvider;
	protected TreeViewer eventViewer;
	protected Action openFolderAction, openConnectionAction;
	protected Document root;
	protected String defaultPath = null;
	protected String defaultServer = null;
	
	@Override
	public void createPartControl(Composite parent) {
		GridLayout layout = new GridLayout();
		layout.numColumns = 1;
		layout.verticalSpacing = 2;
		layout.marginWidth = 0;
		layout.marginHeight = 2;
		parent.setLayout(layout);
		
		treeViewer = new TreeViewer(parent);
		contentProvider = new XMLContentProvider("event");
		treeViewer.setContentProvider(contentProvider);
		labelProvider = new XMLLabelProvider();
		treeViewer.setLabelProvider(labelProvider);
		treeViewer.setUseHashlookup(true);
		treeViewer.addSelectionChangedListener(new EventSelectionListener());
		treeViewer.addDoubleClickListener(new TreeClickListener());
		
		GridData layoutData = new GridData();
		layoutData.grabExcessHorizontalSpace = true;
		layoutData.grabExcessVerticalSpace = true;
		layoutData.horizontalAlignment = GridData.FILL;
		layoutData.verticalAlignment = GridData.FILL;
		layoutData.widthHint = 300;
		treeViewer.getControl().setLayoutData(layoutData);
		
		// Create menu, toolbars, filters, sorters.
		createActions();
		createToolbar();
	}


	@Override
	public void setFocus() {
		// TODO Auto-generated method stub

	}
	
	public Node getInitialInput(){
		root = XMLReader.read(defaultPath);
		return root.getDocumentElement();
	}

	protected void createActions() {
		openFolderAction = new Action("Open Xml Files/Folders") {
			public void run() {
				openXmlFolder();
			}
		};
		openConnectionAction = new Action("Connect to logging server") {
			public void run() {
				openXmlConnection();
			}
		};
	}
	
	protected void openXmlConnection() {
		//TODO: FIX! Server address dialog.
		String destUri = "ws://127.0.0.1:8080";
		WebSocketClient client = new WebSocketClient();
		WSocket socket = new WSocket(this);
		try {
            client.start();
            URI echoUri = new URI(destUri);
            ClientUpgradeRequest request = new ClientUpgradeRequest();
            client.connect(socket, echoUri, request);
            //System.out.printf("Connecting to : %s%n", echoUri);
            socket.awaitClose(5, TimeUnit.SECONDS);
        } catch (Throwable t) {
            t.printStackTrace();
        } finally {
            try {
                client.stop();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
		
	}
	
	public void receiveString(String msg){
		try {
			root = XMLReader.appendString(root, msg);
		} catch (SAXException e) {
		} catch (IOException e) {
		} catch (ParserConfigurationException e) {
		}
		resetViewer(root.getDocumentElement());
	}
	
	protected void openXmlFolder() {
		JFileChooser fc;
		if (defaultPath != null)
			fc = new JFileChooser(defaultPath);
		else
			fc = new JFileChooser();
		fc.setFileSelectionMode(JFileChooser.FILES_AND_DIRECTORIES);
		
		class CustomFilter extends FileFilter {
			
			public String getExtension(File f) {
		        String ext = null;
		        String s = f.getName();
		        int i = s.lastIndexOf('.');

		        if (i > 0 &&  i < s.length() - 1) {
		            ext = s.substring(i+1).toLowerCase();
		        }
		        return ext;
		    }
			
			public boolean accept(File f) {
				if (f.isDirectory())
					return true;
				if ("xml".equals(getExtension(f)))
					return true;
				return false;
			}
			
			public String getDescription() {
				return "Folders or *.xml";
			}
		}
		
		
		fc.setFileFilter(new CustomFilter());
		fc.setMultiSelectionEnabled(true);
		int result = fc.showOpenDialog(null);
		if (result != JFileChooser.APPROVE_OPTION)
			return;
		defaultPath = fc.getCurrentDirectory().getAbsolutePath();
		File[] files = fc.getSelectedFiles();
		ArrayList<String> fullnames = new ArrayList<String>();
		for (File f: files) {
			fullnames.add(f.getAbsolutePath());
		}
		root = XMLReader.read(fullnames.toArray(new String[0]));
		resetViewer(root.getDocumentElement());
	}
	
	protected void resetViewer(Node node) {
		treeViewer.setInput(node);
		treeViewer.expandToLevel(2);
		try {
			EventView view = (EventView)PlatformUI.getWorkbench().
				getActiveWorkbenchWindow().getActivePage().
				showView("org.eclipse.ui.elt.EventView");
			view.setEventViewerInput(null);
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	protected void createMenus() {
		IMenuManager rootMenuManager = getViewSite().getActionBars().getMenuManager();
		rootMenuManager.setRemoveAllWhenShown(true);
		rootMenuManager.addMenuListener(new IMenuListener() {
			public void menuAboutToShow(IMenuManager mgr) {
				fillMenu(mgr);
			}
		});
		fillMenu(rootMenuManager);
	}

	protected void fillMenu(IMenuManager rootMenuManager) {
		rootMenuManager.add(openFolderAction);
		rootMenuManager.add(openConnectionAction);
	}
	
	protected void createToolbar() {
		IToolBarManager toolbarManager = getViewSite().getActionBars().getToolBarManager();
		toolbarManager.add(openFolderAction);
		toolbarManager.add(openConnectionAction);
	}
}

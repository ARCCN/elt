package elt;

import java.io.File;
import java.util.ArrayList;
import javax.swing.JFileChooser;
import javax.swing.filechooser.FileFilter;
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

public class ELTView extends ViewPart {

	protected TreeViewer treeViewer;
	protected XMLLabelProvider labelProvider;
	protected XMLContentProvider contentProvider;
	protected TreeViewer eventViewer;
	protected Action openFolderAction;
	protected Document root;
	protected String defaultPath = "/home/lantame/SDN/pox_debugger/pox_debugger/" +
			"pox_ErrorLocalizationTool/event_logs/";
	
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
		//resetViewer(getInitialInput());
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
	}
	
	protected void openXmlFolder() {
		JFileChooser fc = new JFileChooser();
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
		fc.showOpenDialog(null);
		File[] files = fc.getSelectedFiles();
		ArrayList<String> fullnames = new ArrayList<String>();
		for (File f: files) {
			fullnames.add(f.getAbsolutePath());
		}
		
		/*
		FileDialog dialog = new FileDialog(new Shell(), SWT.OPEN | SWT.MULTI);
		dialog.setText("Choose files to open");
		String[] filters = new String[1];
		filters[0] = "*.xml";
		dialog.setFilterExtensions(filters);
		dialog.open();
		String[] filenames = dialog.getFileNames();
		ArrayList<String> fullnames = new ArrayList<String>();
		for (String fn: filenames) {
			fullnames.add(new Path(dialog.getFilterPath()).
					append(fn).toOSString());
		}
		*/
		root = XMLReader.read(fullnames.toArray(new String[0]));
		resetViewer(root.getDocumentElement());
	}
	
	protected void resetViewer(Node node) {
		treeViewer.setInput(node);
		treeViewer.expandToLevel(2);
		try {
			EventView view = (EventView)PlatformUI.getWorkbench().
				getActiveWorkbenchWindow().getActivePage().
				showView("elt.EventView");
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
	}
	
	protected void createToolbar() {
		IToolBarManager toolbarManager = getViewSite().getActionBars().getToolBarManager();
		toolbarManager.add(openFolderAction);
	}
}

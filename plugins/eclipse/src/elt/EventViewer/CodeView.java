package elt.EventViewer;

import java.io.File;

import org.eclipse.core.filesystem.EFS;
import org.eclipse.core.filesystem.IFileStore;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IRegion;
import org.eclipse.jface.viewers.TreeViewer;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.IEditorRegistry;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PlatformUI;
import org.eclipse.ui.ide.FileStoreEditorInput;
import org.eclipse.ui.part.ViewPart;
import org.eclipse.ui.texteditor.ITextEditor;
import org.w3c.dom.Node;

public class CodeView extends ViewPart {
	protected XMLLabelProvider labelProvider;
	protected XMLContentProvider contentProvider;
	protected TreeViewer codeViewer;
	
	@Override
	public void createPartControl(Composite parent) {
		GridLayout layout = new GridLayout();
		layout.numColumns = 1;
		layout.verticalSpacing = 2;
		layout.marginWidth = 0;
		layout.marginHeight = 2;
		parent.setLayout(layout);
		
		codeViewer = new TreeViewer(parent);
		contentProvider = new XMLContentProvider(null);
		codeViewer.setContentProvider(contentProvider);
		labelProvider = new XMLLabelProvider();
		codeViewer.setLabelProvider(labelProvider);
		codeViewer.setUseHashlookup(true);
		codeViewer.addDoubleClickListener(new CodeClickListener(this));
		
		// layout the tree viewer below the text field
		GridData layoutData = new GridData();
		layoutData.grabExcessHorizontalSpace = true;
		layoutData.grabExcessVerticalSpace = true;
		layoutData.horizontalAlignment = GridData.FILL;
		layoutData.verticalAlignment = GridData.FILL;
		codeViewer.getControl().setLayoutData(layoutData);
		
		// Create menu, toolbars, filters, sorters.
	}
	
	public void setCodeViewerInput(Node node)
	{
		codeViewer.setInput(node);
		codeViewer.collapseAll();
		/*
		try {
			NodeList children = node.getChildNodes();
			for (int i = 0; i < children.getLength(); ++i) {
				codeViewer.collapseToLevel(children.item(i), 2);
			}
		}
		catch(Exception e) {}
		*/
		codeViewer.expandToLevel(2);
	}
	
	
	public void openFile(Node node)
	{	
		try {
			Node module = Util.getChild(node, "module");
			String path = Util.getChild(module, "#text").getTextContent();
			Node line = Util.getChild(node, "line");
			int lineno = 0;
			lineno = Integer.parseInt(Util.getChild(line, "#text").getTextContent());

			File file = new File(path);
			IFileStore fileOnLocalDisk = EFS.getStore(file.toURI());
			FileStoreEditorInput editorInput = new FileStoreEditorInput(fileOnLocalDisk);

			IWorkbenchWindow window = PlatformUI.getWorkbench().getActiveWorkbenchWindow();
			IEditorRegistry editorReg = PlatformUI.getWorkbench().getEditorRegistry();
			String editorName = editorReg.getDefaultEditor(path).getId();
			IWorkbenchPage page = window.getActivePage();
			ITextEditor editor = (ITextEditor)page.openEditor(editorInput, editorName);
			IDocument document = editor.getDocumentProvider().getDocument(
					    editor.getEditorInput());
			if (document != null) {
				IRegion lineInfo = null;
				try {
					lineInfo = document.getLineInformation(lineno - 1);
				} catch (Exception e) {}
				if (lineInfo != null) {
					editor.selectAndReveal(lineInfo.getOffset(), lineInfo.getLength());
				}
			}
		}
		catch (Exception e) {
			e.printStackTrace();
		}
		
	}
	
	@Override
	public void setFocus() {
		// TODO Auto-generated method stub

	}
}

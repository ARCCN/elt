package elt;

import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IPerspectiveDescriptor;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.PartInitException;
import org.eclipse.ui.PerspectiveAdapter;

import elt.ControllerInteraction.ControllerInput;

public class ErrorPerspectiveListener extends PerspectiveAdapter {
	@Override
	public void perspectiveOpened(IWorkbenchPage page, IPerspectiveDescriptor perspective) {
		createControllerEditor(page);
	}
	
	public void createControllerEditor(IWorkbenchPage page) {
		try {
			ControllerInput input = new ControllerInput();
			IEditorPart epart = page.openEditor(input,
					"org.eclipse.ui.elt.ControllerEditor");
			//FormEditor editor = (FormEditor)epart;
			//editor.addPage(new ControllerPage(editor, "controller_page", "Controller"));

		} catch (PartInitException e) {
			e.printStackTrace();
		}
	}
}

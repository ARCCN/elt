package elt;

import org.eclipse.ui.IFolderLayout;
import org.eclipse.ui.IPageLayout;
import org.eclipse.ui.IPerspectiveFactory;


public class ErrorPerspective implements IPerspectiveFactory {

	@Override
	public void createInitialLayout(IPageLayout layout) {
		layout.setEditorAreaVisible(true);
		String editorArea = layout.getEditorArea();
		IFolderLayout log_layout =
	                layout.createFolder("log_layout", IPageLayout.LEFT, (float) 0.3, editorArea);
		log_layout.addView("org.eclipse.ui.elt.ELTView");
		IFolderLayout event_layout = 
					layout.createFolder("event_layout", IPageLayout.BOTTOM, (float) 0.7, "log_layout");
		event_layout.addView("org.eclipse.ui.elt.EventView");
		IFolderLayout data_layout = 
				layout.createFolder("data_layout", IPageLayout.RIGHT, (float) 0.5, "log_layout");
		data_layout.addView("org.eclipse.ui.elt.DataView");
		IFolderLayout bot =
                layout.createFolder("bot", IPageLayout.BOTTOM, (float) 0.7, editorArea);
		bot.addView("org.eclipse.ui.elt.CodeView");
	}
}

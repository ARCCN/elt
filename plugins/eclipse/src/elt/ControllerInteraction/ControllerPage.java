package elt.ControllerInteraction;

import java.io.IOException;
import java.util.ArrayList;

import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.StackLayout;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.MessageBox;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.swt.widgets.Text;
import org.eclipse.ui.forms.IManagedForm;
import org.eclipse.ui.forms.editor.FormEditor;
import org.eclipse.ui.forms.editor.FormPage;
import org.eclipse.ui.forms.editor.IFormPage;
import org.eclipse.ui.forms.widgets.FormToolkit;
import org.eclipse.ui.forms.widgets.ScrolledForm;

import elt.ControllerInteraction.JsonParser.JsonParser;
import elt.ControllerInteraction.Messages.*;
import elt.WebSocketConnection.INotified;
import elt.WebSocketConnection.WSocket;
import elt.WebSocketConnection.WebSocketThread;

public class ControllerPage extends FormPage implements IFormPage, INotified {
	protected String destUri = "ws://127.0.0.1:8081/ws";
	protected Thread wsThread;
	protected WSocket controllerSocket;
	protected Button connect, on, off;
	protected Label statusLabel;
	protected Text uriText;
	protected Label uriLabel;
	StackLayout uriLayout;
	Composite uriComposite;
	enum Status {no_data, running, stopped};
	Status controllerStatus;
	protected Label controllerLabel;
	protected JsonParser parser = new JsonParser();
	protected ArrayList<Button> componentButtons = new ArrayList<Button>();
	protected ArrayList<String> components = new ArrayList<String>();
	
	public ControllerPage(FormEditor editor, String id, String title) {
		super(editor, id, title);
	}
	
	public ControllerPage(String id, String title) {
		super(id, title);
	}
	
	public void setDestUri(String destUri) {
		this.destUri = destUri;
	}
	
	protected void createUriComposite(Composite body, FormToolkit toolkit) {
 		GridData gd = new GridData();
		gd.horizontalAlignment = GridData.FILL;
		gd.grabExcessHorizontalSpace = true;
		uriComposite = toolkit.createComposite(body);
		uriComposite.setLayoutData(gd);
		uriLayout = new StackLayout();
		uriComposite.setLayout(uriLayout);
		uriText = toolkit.createText(uriComposite, destUri, SWT.FILL);
		uriLabel = toolkit.createLabel(uriComposite, destUri, SWT.FILL | SWT.BORDER);
		uriLabel.setBackground(new Color(Display.getCurrent(), 200, 200, 200));
		uriLayout.topControl = uriText;
	}
	
	protected void createConnectionArea(Composite body, FormToolkit toolkit) {
		createUriComposite(body, toolkit);
		GridData gd;
		Class[] classes = new Class[1];
		classes[0] = Object.class;
		try {
		connect = toolkit.createButton(body, "Connect", SWT.PUSH);
		connect.addMouseListener(new ControllerMouseAdapter(
				this.getClass().getMethod("toggleConnect", classes), this, null
		));
		connect.addTraverseListener(new ControllerTraverse(
				this.getClass().getMethod("toggleConnect", classes), this, null
		));
		gd = new GridData();
		gd.horizontalAlignment = GridData.FILL;
		gd.grabExcessHorizontalSpace = true;
		connect.setLayoutData(gd);
		} catch (Throwable e) {}
		
		statusLabel = toolkit.createLabel(body, getConnectionStatus(), SWT.FILL | SWT.BORDER);
		gd = new GridData();
		gd.horizontalAlignment = GridData.FILL;
		gd.grabExcessHorizontalSpace = true;
		statusLabel.setLayoutData(gd);
	}
	
	protected void createOnOffArea(Composite body, FormToolkit toolkit) {
		GridData gd;
		Class[] classes = new Class[1];
		classes[0] = Object.class;
		
		try {
		on = toolkit.createButton(body, "ON", SWT.PUSH);
		on.addMouseListener(new ControllerMouseAdapter(
				this.getClass().getMethod("controllerOn", classes), this, null
		));
		on.addTraverseListener(new ControllerTraverse(
				this.getClass().getMethod("controllerOn", classes), this, null
		));
		gd = new GridData();
		gd.horizontalAlignment = GridData.FILL;
		on.setLayoutData(gd);
		} catch (Throwable e) {}
		try {
		off = toolkit.createButton(body, "OFF", SWT.PUSH);
		off.addMouseListener(new ControllerMouseAdapter(
				this.getClass().getMethod("controllerOff", classes), this, null
		));
		off.addTraverseListener(new ControllerTraverse(
				this.getClass().getMethod("controllerOff", classes), this, null
		));
		gd = new GridData();
		gd.horizontalAlignment = GridData.FILL;
		off.setLayoutData(gd);
		} catch (Throwable e) {}
		
		controllerLabel = toolkit.createLabel(body, "", SWT.FILL);
		gd = new GridData();
		gd.horizontalAlignment = GridData.FILL;
		gd.grabExcessHorizontalSpace = true;
		controllerLabel.setLayoutData(gd);
		setControllerStatus(Status.no_data);
	}
	
	@Override
	protected  void	createFormContent(IManagedForm managedForm) {
		FormToolkit toolkit = managedForm.getToolkit();
		ScrolledForm form = managedForm.getForm();
		//form.setText(this.getTitle());
		/*
		Section section = toolkit.createSection(
					form.getBody(),
					Section.TWISTIE | Section.DESCRIPTION);
		Composite client = toolkit.createComposite(section, SWT.WRAP);
		*/
		Composite body = form.getBody();
		GridLayout layout = new GridLayout();
		layout.numColumns = 3;
		body.setLayout(layout);
		GridData gd;
		createConnectionArea(body, toolkit);
		createOnOffArea(body, toolkit);
	}
	
	protected void addComponentButton(Composite body, FormToolkit toolkit, 
			String text, String componentName) {
		Class[] classes = new Class[1];
		classes[0] = Object.class;
		GridData gd;
		
		try {
		Button btn = toolkit.createButton(body, text, SWT.PUSH);
		btn.addMouseListener(new ControllerMouseAdapter(
				this.getClass().getMethod("controllerLaunchComponent", classes), 
				this, componentName
		));
		btn.addTraverseListener(new ControllerTraverse(
				this.getClass().getMethod("controllerLaunchComponent", classes), 
				this, componentName
		));
		gd = new GridData();
		gd.horizontalAlignment = GridData.FILL;
		btn.setLayoutData(gd);
		componentButtons.add(btn);
		components.add(componentName);
		} catch (Throwable e) {}
	}
	
	protected void stopThreadAndReset() {
		if (wsThread != null) {
			wsThread.interrupt();
			wsThread = null;
			controllerSocket = null;
		}
		connect.setText("Connect");
		statusLabel.setText(getConnectionStatus());
		setControllerStatus(Status.no_data);
		removeComponentButtons();
	}
	
	public void toggleConnect(Object arg) {
		boolean wasConnected = connected();
		stopThreadAndReset();
		setUriTextEditable(true);
		if (wasConnected)
			return;
		destUri = uriText.getText();
		setUriTextEditable(false);
		wsThread = new Thread(new WebSocketThread(destUri, this));
		wsThread.setDaemon(true);
		wsThread.start();
	}
	
	protected void setUriTextEditable(boolean ed) {
		uriText.setEnabled(ed);
		if (ed == false) {
			uriLabel.setText(destUri);
			uriLayout.topControl = uriLabel;
		} else {
			uriLayout.topControl = uriText;
		}
		uriComposite.layout();
	}
	
	protected void showMessageBox(String text, String message) {
		Shell s = this.getSite().getWorkbenchWindow().getShell();
		MessageBox m = new MessageBox(s);
		m.setText(text);
		m.setMessage(message);
		m.open();
	}
	
	protected boolean connected() {
		if (wsThread != null && controllerSocket != null && controllerSocket.connected)
			return true;
		return false;
	}
	
	protected String getConnectionStatus() {
		if (connected())
			return "Connected";
		else
			return "Disconnected";
	}
	
	protected void trySendMessage(String msg) {
		if (connected()) {
			try {
				controllerSocket.sendMessage(msg);
			} catch (IOException e) {
				showMessageBox("Error", "Unable to send message. Disconnecting.");
				stopThreadAndReset();
			}
		} else {
			showMessageBox("Error", "Not connected to controller.");
		}
	}
	
	public void controllerOn(Object arg) {
		trySendMessage(parser.encodeMessage(new StartController()));
	}
	
	public void controllerOff(Object arg) {
		trySendMessage(parser.encodeMessage(new StopController()));
	}
	
	public void controllerLaunchComponent(Object arg) {
		String message = "";
		if (arg instanceof String) {
			message = (String)arg;
			// do nothing
		} else {
			// Convert to string,
		}
		trySendMessage(parser.encodeMessage(new LaunchHierarchical(message, null)));
	}

	@Override
	public void processMessage(String msg, Object data) {
		if (msg.equals("ConnectionError"))
		{
			setUriTextEditable(true);
			showMessageBox("Connection error", "Unable to connect to server.");
		} else if (msg.equals("DataReceived")) {
			processData(data);
		} else if (msg.equals("SocketConnected")) {
			controllerSocket = (WSocket)data;
			connect.setText("Disconnect");
			statusLabel.setText(getConnectionStatus());
			trySendMessage(parser.encodeMessage(new GetControllerComponents()));
		} else if (msg.equals("SocketDisconnected")) {
			stopThreadAndReset();
			this.showMessageBox("Disconnected", "Socket disconnected by server\n" + (String)data);
		}
	}
	
	protected void setControllerStatus (Status st) {
		if (st == null) {
			return;
		}
		controllerStatus = st;
		String status = "";
		if (controllerStatus == Status.no_data) {
			status = "no data";
		} else if (controllerStatus == Status.running){
			status = controllerStatus.toString();
			for (Button b: componentButtons) {
				b.setEnabled(true);
			}
		} else if (controllerStatus == Status.stopped) {
			status = controllerStatus.toString();
			for (Button b: componentButtons) {
				b.setEnabled(false);
			}
		}
		controllerLabel.setText("Controller status: " + status);
	}
	
	public void processData(Object data) {
		// TODO: Reaction?
		if (data == null)
			return;
		String msg = ((String)data).trim();
		ControllerMessage message;
		try {
			message = parser.parseMessage(msg);
		} catch(Throwable e) {e.printStackTrace(); return; }
		if (message instanceof ControllerStatus) {
			setControllerStatus(Status.valueOf(((ControllerStatus)message).getStatus()));
		} else if (message instanceof ControllerComponents) {
			processControllerComponents((ControllerComponents)message);
		} else if (message instanceof ComponentLaunched) {
			processComponentLaunched((ComponentLaunched)message);
		}
	}
	
	protected void processComponentLaunched(ComponentLaunched message) {
		String component = message.getComponent();
		componentButtons.get(components.indexOf(component)).setEnabled(false);
	}
	
	protected void removeComponentButtons() {
		Composite body = this.getManagedForm().getForm().getBody();
		for (Button b: componentButtons) {
			b.dispose();
		}
		componentButtons.clear();
		components.clear();
		body.layout();
		//body.pack(true);
		body.redraw();
	}
	
	protected void processControllerComponents(ControllerComponents message) {
		removeComponentButtons();
		Composite body = this.getManagedForm().getForm().getBody();
		FormToolkit toolkit = this.getManagedForm().getToolkit();
		Component[] components = message.getComponents();
		for (Component c: components) {
			// TODO: Process ComponentParams;
			String componentName = c.getName();
			String[] parts = componentName.split("\\.");
			String text = parts[parts.length - 1];
			this.addComponentButton(body, toolkit, text, componentName);
		}
		if (controllerStatus == Status.stopped) {
			for (Button b: componentButtons) {
				b.setEnabled(false);
			}
		}
		
		body.layout();
		body.redraw();
	}
	
	public void dumpState() {
		destUri = uriText.getText();
	}
	
	public void loadState() {
		uriText.setText(destUri);
	}
	/*
	protected void createFormContent(IManagedForm managedForm) {
		ScrolledForm form = managedForm.getForm();
		FormToolkit toolkit = managedForm.getToolkit();
		//form.setText(Messages.getString("SecondPage.title")); //$NON-NLS-1$
		//form.setBackgroundImage(FormArticlePlugin.getDefault().getImage(FormArticlePlugin.IMG_FORM_BG));
		//GridLayout layout = new GridLayout();
		//layout.numColumns = 2;
		//form.getBody().setLayout(layout);
		createTableSection(form, toolkit, "SecondPage.firstSection"); //$NON-NLS-1$
		//createTableSection(form, toolkit,"SecondPage.secondSection");		 //$NON-NLS-1$
	}
	
	private void createTableSection(final ScrolledForm form, FormToolkit toolkit, String title) {
		
		Section section =
			toolkit.createSection(
				form.getBody(),
				Section.TWISTIE | Section.DESCRIPTION);
		section.setActiveToggleColor(
			toolkit.getHyperlinkGroup().getActiveForeground());
		section.setToggleColor(
			toolkit.getColors().getColor(FormColors.SEPARATOR));
		toolkit.createCompositeSeparator(section);
		Composite client = toolkit.createComposite(section, SWT.WRAP);
		
		Composite client = form.getBody();
		GridLayout layout = new GridLayout();
		layout.numColumns = 2;

		client.setLayout(layout);
		//Table t = toolkit.createTable(client, SWT.NULL);
		//GridData gd = new GridData(GridData.FILL_BOTH);
		//gd.heightHint = 200;
		//gd.widthHint = 100;
		//t.setLayoutData(gd);
		//toolkit.paintBordersFor(client);
		Button b = toolkit.createButton(client, "SecondPage.add", SWT.PUSH); //$NON-NLS-1$
		//gd = new GridData(GridData.VERTICAL_ALIGN_BEGINNING);
		//b.setLayoutData(gd);
		
		section.setText(title);
		section.setDescription("SecondPage.desc"); //$NON-NLS-1$
		section.setClient(client);
		section.setExpanded(true);
		section.addExpansionListener(new ExpansionAdapter() {
			public void expansionStateChanged(ExpansionEvent e) {
				form.reflow(false);
			}
		});
		
		//gd = new GridData(GridData.FILL_BOTH);
		//section.setLayoutData(gd);
	}
	*/
}

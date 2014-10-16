package elt.ControllerInteraction;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

import org.eclipse.swt.events.MouseAdapter;
import org.eclipse.swt.events.MouseEvent;

public class ControllerMouseAdapter extends MouseAdapter {
	protected Method method;
	protected Object host;
	protected Object arg;
	
	public ControllerMouseAdapter(Method method, Object host, Object arg) {
		this.method = method;
		this.host = host;
		this.arg = arg;
	}
	
	@Override
	public void mouseDown(MouseEvent evt) {
		try {
			method.invoke(host, arg);
		} catch (IllegalAccessException | IllegalArgumentException
				| InvocationTargetException e) {
			e.printStackTrace();
		}
	}

	@Override
	public void mouseDoubleClick(MouseEvent arg0) {
		// TODO Auto-generated method stub
	}

	@Override
	public void mouseUp(MouseEvent arg0) {
		// TODO Auto-generated method stub
	}
}
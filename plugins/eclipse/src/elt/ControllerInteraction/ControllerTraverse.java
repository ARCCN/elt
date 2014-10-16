package elt.ControllerInteraction;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

import org.eclipse.swt.SWT;
import org.eclipse.swt.events.TraverseEvent;
import org.eclipse.swt.events.TraverseListener;

public class ControllerTraverse implements TraverseListener {
	protected Method method;
	protected Object host;
	protected Object arg;
	
	public ControllerTraverse(Method method, Object host, Object arg) {
		this.method = method;
		this.host = host;
		this.arg = arg;
	}
	
	public void keyTraversed(TraverseEvent ev) {
		//ev.doit = false;
		if (ev.detail != SWT.TRAVERSE_RETURN)
			return;
		try {
			method.invoke(host, arg);
		} catch (IllegalAccessException | IllegalArgumentException
				| InvocationTargetException e) {
			e.printStackTrace();
		}
	}
}

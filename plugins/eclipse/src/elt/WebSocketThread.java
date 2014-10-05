package elt;

import java.net.URI;
import java.util.concurrent.TimeUnit;

import org.eclipse.jetty.websocket.client.ClientUpgradeRequest;
import org.eclipse.jetty.websocket.client.WebSocketClient;
import org.eclipse.swt.widgets.Display;

public class WebSocketThread implements Runnable, IStringReceiver {

	protected String uri;
	protected IGUI gui;
	
	public WebSocketThread(String uri, IGUI gui) {
		this.uri = uri;
		this.gui = gui;
	}
	
	@Override
	public void run() {
		WebSocketClient client = new WebSocketClient();
		WSocket socket = new WSocket(this);
		try {
            client.start();
            URI echoUri = new URI(this.uri);
            ClientUpgradeRequest request = new ClientUpgradeRequest();
            client.connect(socket, echoUri, request);
            
            //System.out.printf("Connecting to : %s%n", echoUri);
            socket.awaitClose(5, TimeUnit.SECONDS);
            if (!socket.connected) {
            	sendMessage("ConnectionError");
            	return;
            }
            socket.awaitClose(100000, TimeUnit.DAYS);
		} catch (InterruptedException t) {
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
	
	class StrRecvRunnable implements Runnable {
		
		private IStringReceiver recv;
		private String msg;
		
		public StrRecvRunnable(IStringReceiver recv, String msg) {
			this.recv = recv;
			this.msg = msg;
		}
		
		public void run() {
			this.recv.receiveString(this.msg);
		}
	}
	
	class MsgSendRunnable implements Runnable {
		
		private INotified recv;
		private Object msg;
		
		public MsgSendRunnable(INotified recv, Object msg) {
			this.recv = recv;
			this.msg = msg;
		}
		
		public void run() {
			this.recv.processMessage(this.msg);
		}
	}
	
	public void receiveString(String msg) {
		Display display = Display.getDefault();
		display.asyncExec(
			new StrRecvRunnable(this.gui, msg)
		);
	}
	
	public void sendMessage(String msg) {
		Display display = Display.getDefault();
		display.asyncExec(
			new MsgSendRunnable(this.gui, (Object)msg)
		);
	}

}

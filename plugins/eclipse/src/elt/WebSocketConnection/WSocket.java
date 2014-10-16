package elt.WebSocketConnection;

import java.io.IOException;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import org.eclipse.jetty.websocket.api.Session;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketClose;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketConnect;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketMessage;
import org.eclipse.jetty.websocket.api.annotations.WebSocket;

@WebSocket
public class WSocket {
	private final CountDownLatch closeLatch;
	private final CountDownLatch connectLatch;
	 
    @SuppressWarnings("unused")
    private Session session;
    protected INotified receiver;
    public boolean connected = false;
    
    public WSocket(INotified receiver) {
    	this.connectLatch = new CountDownLatch(1);
        this.closeLatch = new CountDownLatch(1);
        this.receiver = receiver;
    }
 
    public boolean awaitConnect(int duration, TimeUnit unit) throws InterruptedException {
        return this.connectLatch.await(duration, unit);
    }
    
    public boolean awaitClose(int duration, TimeUnit unit) throws InterruptedException {
        return this.closeLatch.await(duration, unit);
    }
 	
    @OnWebSocketClose
    public void onClose(int statusCode, String reason) {
        System.out.printf("Connection closed: %d - %s%n", statusCode, reason);
        this.receiver.processMessage("SocketDisconnected", 
        		String.format("%d - %s%n", statusCode, reason));
        this.session = null;
        this.closeLatch.countDown();
        this.connected = false;
    }
 
    @OnWebSocketConnect
    public void onConnect(Session session) {
        System.out.printf("Got connect: %s%n", session);
        this.session = session;
        this.connected = true;
        this.connectLatch.countDown();
    }
 
    @OnWebSocketMessage
    public void onMessage(String msg) {
        this.receiver.processMessage("DataReceived", (Object)msg);
    }
    
    public Future<Void> sendMessage(String msg) throws IOException {
    	return this.session.getRemote().sendStringByFuture(msg);
    }
}

package com.upchr.mytool.core.ssh;

import com.jcraft.jsch.*;
import lombok.extern.slf4j.Slf4j;

import java.io.ByteArrayOutputStream;

/**
 * SSH 客户端
 */
@Slf4j
public class SSHClient {

    private final String host;
    private final int port;
    private final String username;
    private final String password;
    private final String privateKey;

    private Session session;

    public SSHClient(String host, int port, String username, String password, String privateKey) {
        this.host = host;
        this.port = port;
        this.username = username;
        this.password = password;
        this.privateKey = privateKey;
    }

    /**
     * 连接
     */
    public void connect() throws JSchException {
        JSch jsch = new JSch();
        
        if (privateKey != null && !privateKey.isEmpty()) {
            jsch.addIdentity("key", privateKey.getBytes(), null, null);
        }

        session = jsch.getSession(username, host, port);
        
        if (password != null && !password.isEmpty()) {
            session.setPassword(password);
        }

        session.setConfig("StrictHostKeyChecking", "no");
        session.connect(10000);
        log.info("SSH 连接成功: {}@{}:{}", username, host, port);
    }

    /**
     * 执行命令
     */
    public SSHResult executeCommand(String command, int timeout) throws Exception {
        if (session == null || !session.isConnected()) {
            throw new IllegalStateException("SSH 未连接");
        }

        ChannelExec channel = null;
        try {
            channel = (ChannelExec) session.openChannel("exec");
            channel.setCommand(command);
            channel.connect(timeout);

            ByteArrayOutputStream outStream = new ByteArrayOutputStream();
            ByteArrayOutputStream errStream = new ByteArrayOutputStream();

            InputStream in = channel.getInputStream();
            InputStream err = channel.getExtInputStream();

            byte[] buffer = new byte[1024];
            while (true) {
                while (in.available() > 0) {
                    int len = in.read(buffer, 0, buffer.length);
                    if (len > 0) outStream.write(buffer, 0, len);
                }
                while (err.available() > 0) {
                    int len = err.read(buffer, 0, buffer.length);
                    if (len > 0) errStream.write(buffer, 0, len);
                }
                if (channel.isClosed()) {
                    while (in.available() > 0) {
                        int len = in.read(buffer, 0, buffer.length);
                        if (len > 0) outStream.write(buffer, 0, len);
                    }
                    while (err.available() > 0) {
                        int len = err.read(buffer, 0, buffer.length);
                        if (len > 0) errStream.write(buffer, 0, len);
                    }
                    break;
                }
                Thread.sleep(100);
            }

            SSHResult result = new SSHResult();
            result.setExitCode(channel.getExitStatus());
            result.setOutput(outStream.toString("UTF-8"));
            result.setError(errStream.toString("UTF-8"));

            return result;
        } finally {
            if (channel != null) {
                channel.disconnect();
            }
        }
    }

    /**
     * 关闭连接
     */
    public void close() {
        if (session != null && session.isConnected()) {
            session.disconnect();
            log.info("SSH 连接已关闭");
        }
    }

    /**
     * 执行结果
     */
    @lombok.Data
    public static class SSHResult {
        private int exitCode;
        private String output;
        private String error;

        public boolean isSuccess() {
            return exitCode == 0;
        }
    }
}

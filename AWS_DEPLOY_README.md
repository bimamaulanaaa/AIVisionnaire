# AI Visionnaire AWS EC2 Deployment Guide

This guide provides instructions for deploying and maintaining your AI Visionnaire application on an AWS EC2 instance.

## Initial Setup

1. **Connect to your EC2 instance**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

2. **Create application directory**:
   ```bash
   mkdir -p ~/AIVisionnaire
   cd ~/AIVisionnaire
   ```

3. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/AIVisionnaire.git .
   ```

4. **Make the run script executable**:
   ```bash
   chmod +x run_aivisionnaire.sh
   ```

5. **Set up Python Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirementstwo.txt
   ```

6. **Update .env file**:
   ```bash
   # Edit the .env file and update APP_PUBLIC_URL with your EC2 public IP
   nano .env
   ```
   Make sure to set `APP_PUBLIC_URL=http://YOUR_EC2_PUBLIC_IP:7861`

## Running the Application

The `run_aivisionnaire.sh` script provides easy commands to manage your application:

1. **Start the application**:
   ```bash
   ./run_aivisionnaire.sh start
   ```

2. **Check application status**:
   ```bash
   ./run_aivisionnaire.sh status
   ```

3. **View application logs**:
   ```bash
   ./run_aivisionnaire.sh logs
   ```

4. **Stop the application**:
   ```bash
   ./run_aivisionnaire.sh stop
   ```

5. **Restart the application**:
   ```bash
   ./run_aivisionnaire.sh restart
   ```

## Troubleshooting Chat History Issues

If you're experiencing issues with chat history not being retained, use the `test_pinecone.py` script to diagnose problems:

1. **Basic Pinecone connectivity test**:
   ```bash
   ./run_aivisionnaire.sh test
   ```

2. **Check a specific user's chat history**:
   ```bash
   ./run_aivisionnaire.sh test --user-id=SOME_USER_ID
   ```

3. **Test storage capabilities**:
   ```bash
   ./run_aivisionnaire.sh test --test-storage
   ```

4. **Get detailed output**:
   ```bash
   ./run_aivisionnaire.sh test --verbose
   ```

5. **Test and clean up afterward**:
   ```bash
   ./run_aivisionnaire.sh test --test-storage --delete
   ```

## Common Issues and Solutions

### Chat History Not Retained

1. **Check Pinecone connectivity**:
   ```bash
   ./run_aivisionnaire.sh test
   ```
   Ensure the connection is successful and you can see your index.

2. **Verify storage is working**:
   ```bash
   ./run_aivisionnaire.sh test --test-storage
   ```
   This tests if messages can be stored in Pinecone.

3. **Check application logs**:
   ```bash
   ./run_aivisionnaire.sh logs
   ```
   Look for error messages related to Pinecone or user IDs.

4. **Ensure user IDs are consistent**:
   - Check if user IDs from Ory are being correctly passed to the Pinecone storage functions.
   - Look for "Processing message for user:" in the logs.

### Application Won't Start

1. **Check for port conflicts**:
   ```bash
   sudo netstat -tulpn | grep 7861
   ```
   If the port is in use, stop the conflicting service or change the port in your .env file.

2. **Check for Python errors**:
   ```bash
   ./run_aivisionnaire.sh logs
   ```
   Look for Python exceptions or errors.

3. **Verify environment variables**:
   Make sure all required environment variables in .env are set correctly.

### Server 502 or Connection Issues

1. **Check if application is running**:
   ```bash
   ./run_aivisionnaire.sh status
   ```

2. **Verify Nginx configuration** (if using Nginx):
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

3. **Check security groups in AWS**:
   Ensure ports 7861, 80, and 443 are open to the internet.

## Updating the Application

1. **Pull latest changes**:
   ```bash
   cd ~/AIVisionnaire
   git pull origin main
   ```

2. **Restart the application**:
   ```bash
   ./run_aivisionnaire.sh restart
   ```

## Setting Up as a System Service

For a more robust deployment, set up the application as a systemd service:

1. **Create a service file**:
   ```bash
   sudo nano /etc/systemd/system/aivisionnaire.service
   ```

2. **Add service configuration**:
   ```
   [Unit]
   Description=AI Visionnaire Service
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/AIVisionnaire
   ExecStart=/home/ubuntu/AIVisionnaire/venv/bin/python gradio-frontend.py
   Restart=always
   RestartSec=10
   StandardOutput=syslog
   StandardError=syslog
   SyslogIdentifier=aivisionnaire
   Environment="PATH=/home/ubuntu/AIVisionnaire/venv/bin"

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable aivisionnaire
   sudo systemctl start aivisionnaire
   ```

4. **Monitor the service**:
   ```bash
   sudo systemctl status aivisionnaire
   sudo journalctl -u aivisionnaire -f
   ``` 
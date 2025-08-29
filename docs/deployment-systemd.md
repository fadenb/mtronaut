# Deploying Mtronaut with Systemd on Ubuntu 24.04

This guide outlines the steps to deploy the Mtronaut application as a Systemd service on an Ubuntu 24.04 server. This ensures the application starts automatically on boot and runs reliably in the background.

## Prerequisites

Before you begin, ensure your Ubuntu 24.04 server is updated and you have `git` installed.

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3-venv python3-pip
```

## 1. Install Poetry

Mtronaut uses Poetry for dependency management. Install it globally:

```bash
sudo apt install python3-poetry
```

## 2. Clone the Mtronaut Repository

Clone the Mtronaut repository to a suitable location on your server, for example, `/opt/mtronaut`.

```bash
sudo mkdir -p /opt/mtronaut
sudo chown -R $USER:$USER /opt/mtronaut # Give your user ownership for setup
git clone https://github.com/fadenb/mtronaut.git /opt/mtronaut
cd /opt/mtronaut
```

## 3. Create a System Group (Optional but Recommended)

For better organization and security, it's recommended to create a dedicated system group for the Mtronaut application.

```bash
sudo addgroup --system mtronaut
```

## 4. Create a System User (Optional but Recommended)

For security, it's best to run the application under a dedicated, unprivileged system user.

```bash
sudo adduser --system --no-create-home --ingroup mtronaut mtronautuser
```

Now, change the ownership of the Mtronaut directory to this new user and ensure proper permissions:

```bash
sudo chown -R mtronautuser:mtronaut /opt/mtronaut
sudo chmod u+rwx /opt/mtronaut
```

## 5. Install Dependencies

Navigate into the cloned directory and install the project dependencies using Poetry. This will also create a virtual environment for the project.

```bash
cd /opt/mtronaut
sudo -u mtronautuser python3 -m venv .venv
sudo -u mtronautuser poetry env use /opt/mtronaut/.venv/bin/python
sudo -u mtronautuser POETRY_CACHE_DIR=/opt/mtronaut/.poetry_cache poetry install --without dev
```

## 6. Create the Systemd Service File

Create a new Systemd service file for Mtronaut.

```bash
sudo nano /etc/systemd/system/mtronaut.service
```

Paste the following content into the file. Make sure the `User` and `Group` match the user you created (e.g., `mtronautuser`). The `ExecStart` command uses `poetry run` to execute `uvicorn` within the project's virtual environment.

```ini
[Unit]
Description=Mtronaut Web Application
After=network.target

[Service]
User=mtronautuser
Group=mtronaut
WorkingDirectory=/opt/mtronaut
ExecStart=/usr/bin/poetry run uvicorn backend.mtronaut.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```



## 7. Reload Systemd and Enable the Service

After creating the service file, reload the Systemd daemon to recognize the new service, then enable and start it.

```bash
sudo systemctl daemon-reload
sudo systemctl enable mtronaut.service
sudo systemctl start mtronaut.service
```

## 8. Verify the Service Status

Check the status of the Mtronaut service to ensure it's running correctly:

```bash
sudo systemctl status mtronaut.service
```

You should see `Active: active (running)`. If there are errors, check the logs:

```bash
sudo journalctl -u mtronaut.service -f
```

## 9. Configure Firewall (UFW)

If you are using UFW (Uncomplicated Firewall), you need to allow traffic on port 8000.

```bash
sudo ufw allow 8000/tcp
sudo ufw enable # If not already enabled
```

## 10. Access Mtronaut

Mtronaut should now be accessible via your server's IP address or domain name on port 8000 (e.g., `http://your_server_ip:8000`).

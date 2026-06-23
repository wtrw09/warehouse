<p align="right">
  <b>English</b> | <a href="README.md"><b>中文</b></a>
</p>

# Warehouse Management System

## 1. Overview

Warehouse Management System is a complete warehouse management solution built on modern web technologies, featuring a front-end/back-end separated architecture. It supports multi-user permission management, material management, inventory tracking, data backup & recovery, and more.
It is designed for small teams with no complex logistics tracking or sorting needs, but requiring LAN-based material inventory recording and viewing.

## 2. Screenshots

### Login & Home

**Login Page**
![Login Page](./screenshot/登录界面.png)

**Default Home Page**
![Default Home Page](./screenshot/默认首页.png)

### Base Data Management

**Warehouse Configuration**
![Warehouse Configuration](./screenshot/仓库配置.png)

**Location Configuration**
![Location Configuration](./screenshot/货位配置.png)

**Specialty Management**
![Specialty Management](./screenshot/专业管理.png)

**Customer Management**
![Customer Management](./screenshot/客户管理.png)

**Supplier Management**
![Supplier Management](./screenshot/供应商管理.png)

**Equipment Information**
![Equipment Information](./screenshot/器材信息.png)

### Inventory Management

**Inbound Management**
![Inbound Management](./screenshot/入库管理.png)

**Outbound Management**
![Outbound Management](./screenshot/出库管理.png)

**Inventory Details**
![Inventory Details](./screenshot/库存明细.png)

**Inventory Transaction Log**
![Inventory Transaction Log](./screenshot/库存变更流水.png)

### Account Management

**Permission Management**
![Permission Management](./screenshot/权限管理.png)

**Role Management**
![Role Management](./screenshot/角色管理.png)

**User Management**
![User Management](./screenshot/用户管理.png)

### System Settings

**Database Management**
![Database Management](./screenshot/数据库管理.png)

**Equipment Code Settings**
![Equipment Code Settings](./screenshot/器材编码设置.png)

**Personal Settings**
![Personal Settings](./screenshot/个人设置.png)

**System Configuration**
![System Configuration](./screenshot/系统配置管理.png)

## 3. Tech Stack

**Backend:**
- **Framework**: FastAPI + SQLModel
- **Database**: SQLite (Main business DB + System config DB)
- **Authentication**: JWT (OAuth2 Bearer Token)
- **Cache**: Redis
- **Containerization**: Docker
- **Others**: Pydantic, bcrypt, fpdf2, etc.

**Frontend:**
- **Framework**: Vue 3 + TypeScript
- **UI Components**: Element Plus
- **Router**: Vue Router
- **State Management**: Pinia
- **Build Tool**: Vite
- **Charts**: ECharts

## 4. Project Structure

```
WarehouseManagement/
├── backend/                 # Backend service
│   ├── backup/             # Backup management module
│   ├── config/             # Configuration files
│   ├── core/               # Core components (security, config, logging, etc.)
│   ├── database/           # Database management
│   ├── initialize/         # System initialization
│   ├── models/             # Data models
│   ├── routes/             # API routes
│   ├── schemas/            # Pydantic schemas
│   ├── utils/              # Utility functions
│   └── main.py             # Application entry point
├── frontend/               # Frontend application
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── services/       # API services
│   │   ├── stores/         # State management
│   │   └── router/         # Route configuration
│   └── package.json
├── warehouseBackend/       # Data storage directory, **auto-generated at runtime**
│   ├── data/              # Database files
│   ├── logs/              # Log files
│   └── backups/           # Backup files
├── config/                # Nginx config files, **auto-generated at runtime**
├── logs/nginx/            # Nginx log files, **auto-generated at runtime**
└── docker-compose.yml     # Docker Compose configuration
```

## 5. Main Features

### 5.1 User Authentication & Permission Management
- **User Registration/Login**: OAuth2 password mode authentication
- **Permission Control**: Role-based access control system
- **Session Management**: JWT token authentication
- **User Management**: User profile maintenance, permission assignment

### 5.2 Base Data Management
- **Warehouse Management**: Multi-warehouse configuration, warehouse info maintenance
- **Customer Management**: Customer profile management
- **Supplier Management**: Supplier information management
- **Location Management**: Warehouse location configuration

### 5.3 Material Management
- **Equipment Management**: Equipment basic info, category management
- **Specialty Management**: Specialty classification system
- **Gear Management**: Gear type management
- **Code System**: Equipment code classification hierarchy management

### 5.4 Inventory Management
- **Inbound Management**: Inbound order creation, approval, execution
- **Outbound Management**: Outbound order creation, approval, execution
- **Inventory Query**: Real-time inventory query, inventory details
- **Inventory Log**: Inventory change record tracking

### 5.5 System Management
- **System Configuration**: System parameter configuration
- **Data Backup**: Automatic/manual data backup
- **Data Recovery**: Backup data recovery
- **System Monitoring**: System status monitoring, log management

### 5.6 Reports & Statistics
- **Dashboard**: Key metrics display
- **Statistical Reports**: Various business statistics
- **Category Ledger**: Equipment category ledger generation
- **Data Export**: Excel, PDF format export

## 6. Installation & Deployment

### 6.1 Requirements
- Python 3.13+
- Node.js 18+
- Docker & Docker Compose (Recommended)

### 6.2 Quick Start (Docker)
1. **Clone the project**
```bash
git clone https://cnb.cool/wtrw09/warehouse.git
# or
git clone https://gitee.com/wtrw09/warehouse.git
# or
git clone https://github.com/wtrw09/warehouse.git
cd WarehouseManagement
```
2. **Pull images**

Images are hosted on CNB Docker Registry, supporting both amd64 and arm64 architectures. `docker pull` will automatically match your CPU architecture:
```bash
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-frontend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-backend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/redis:7.2-alpine
```
3. **Start containers**
Copy `docker-compose.yml`, `start-containers.ps1`, and `start-containers.sh` to your target directory. On Windows, run `start-containers.ps1`; on Linux/Mac, run `start-containers.sh`.
Note: On Linux, you need to add executable permission to `start-containers.sh`:
```bash
$ chmod +x start-containers.sh
```
Then run with admin privileges:
```bash
$ sudo ./start-containers.sh
```
4. **Access the system**
`http://localhost:8081/login` or `http://[your-computer-IP]:8081/login`

### 6.3 Offline Deployment (Alternative)

If the target machine has no network access, you can build images locally using offline build scripts and transfer them for deployment:

1. Use `frontend/build-amd64-offline.ps1` or `frontend/build-arm64-offline.ps1` to build the frontend image
2. Use `backend/build-amd64-offline.ps1` or `backend/build-arm64-offline.ps1` to build the backend image
3. Transfer the generated `.tar` files to the target server
4. Load images on the target server with `docker load -i xxx.tar`

> Note: For offline deployment, modify the image addresses in `docker-compose.yml` to local image names and add `pull_policy: never`.

### 6.4 Manual Deployment
1. **Clone the project**
```bash
git clone https://gitee.com/wtrw09/warehouse.git
cd WarehouseManagement
```
**Backend:**
```bash
cd backend
pip install -r requirements.txt
python main.py
```
**Frontend:**
```bash
cd frontend
npm install
npm run build
npm run dev
```

## 7. System Initialization

The system automatically performs the following initialization on first startup:
1. Check database connection status
2. Create necessary database table structures
3. Initialize system default data
4. Start the scheduled backup scheduler
5. Configure fonts and logging system

## 8. Database Architecture

The system uses a dual-database design:
- **Main Business Database** (`warehouse.db`): Stores business data
- **System Config Database** (`system_config.db`): Stores system configuration and permission data

## 9. Permission System

The system adopts a Role-Based Access Control (RBAC) model:

### 9.1 Permission Levels
1. **System Admin**: Highest privileges, can manage all features
2. **Warehouse Admin**: Manages business operations for designated warehouses
3. **Business Department Representative**: Can view warehouse data but cannot modify, supervisory role only
4. **Viewer**: Can only view inventory data, cannot make any changes, intended for customers (personnel who can request supplies)

### 9.2 Permission Categories
- `AUTH-*`: User authentication related permissions
- `BASE-*`: Base data management permissions
- `STOCK-*`: Inventory management permissions
- `SYSTEM-*`: System management permissions
- `IO-*`: Inbound/outbound operation permissions

## 10. Backup & Recovery

### Backup Strategy
- **Scheduled Backup**: Daily automatic backup
- **Manual Backup**: On-demand manual backup

### Recovery Mechanism
- Supports data recovery from backup files
- Provides recovery status tracking
- Supports selective recovery

## Log Management

The system provides multi-level logging:
- **Application Log**: Business operation records
- **Error Log**: Exception and error records
- **Debug Log**: Development debugging information
- **Recovery Log**: Backup/recovery operation records

## 11. VM Docker Deployment (AlmaLinux 8 Example)

If your Windows system or hardware does not support virtualization and you cannot install Docker directly, you can install Docker in a virtual machine.

### 11.1 Install AlmaLinux in a VM
### 11.2 Add User to sudo
```bash
# 1. Switch to root user
su -
# 2. Edit sudoers file with a text editor (e.g., vim)
vi /etc/sudoers
# 3. Find the line like root ALL=(ALL) ALL and add your user below it
root ALL=(ALL) ALL
userName ALL=(ALL) ALL
```
### 11.3 Network Settings
```bash
# Launch network text UI
sudo nmtui
```
### 11.4 Install OpenSSH Server
```bash
# Start SSH service
sudo systemctl start sshd
sudo systemctl enable sshd
# Check service status
sudo systemctl status sshd
# View IP address (for connection)
ip addr show
```
Configure port forwarding in VirtualBox:
1. VM Settings → Network → Advanced → Port Forwarding
2. Add rule:
    - **Name**: SSH
    - **Protocol**: TCP
    - **Host IP**: (empty)
    - **Host Port**: 2222 (or another unused port)
    - **Guest IP**: (empty)
    - **Guest Port**: 22

### 11.5 Transfer Files from Windows Host
Download docker-20.10.24.tgz, extract it, and transfer it along with docker-compose to the server:
```bash
# Transfer entire folder
scp -P 2222 -r local_folder username@localhost:/home/username/target_directory
```
If you encounter the error WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!:
```bash
# Remove old key record for localhost:2222
ssh-keygen -R [localhost]:2222
```

### 11.6 Install Docker and docker-compose
### 11.6.1 Install Docker
1. Copy all necessary binaries from the Docker static package:
```bash
sudo cp -f docker/* /usr/bin/
# Set execution permissions
sudo chmod +x /usr/bin/docker*
sudo chmod +x /usr/bin/containerd*
sudo chmod +x /usr/bin/ctr
sudo chmod +x /usr/bin/runc
```
2. Create containerd.service:
```bash
[Unit]
Description=containerd container runtime
Documentation=https://containerd.io
After=network.target

[Service]
ExecStartPre=-/sbin/modprobe overlay
ExecStart=/usr/bin/containerd
Restart=always
RestartSec=5
Delegate=yes
KillMode=process

[Install]
WantedBy=multi-user.target
```

```bash
sudo cp containerd.service /etc/systemd/system/
```
3. Run containerd:
```bash
# Test if containerd can run
sudo /usr/bin/containerd --version
# Start containerd service
sudo systemctl daemon-reload
sudo systemctl start containerd
sudo systemctl enable containerd
```

4. Create docker.service:
```bash
[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target firewalld.service
Wants=network-online.target

[Service]
Type=notify
ExecStart=/usr/bin/dockerd
ExecReload=/bin/kill -s HUP $MAINPID
TimeoutSec=0
RestartSec=2
Restart=always
StartLimitBurst=3
StartLimitInterval=60s
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity
Delegate=yes
KillMode=process

[Install]
WantedBy=multi-user.target
```

```bash
sudo cp docker.service /etc/systemd/system/
```

5. Start Docker service:
```bash
# Reload systemd
sudo systemctl daemon-reload
# Start Docker
sudo systemctl start docker
# Enable auto-start
sudo systemctl enable docker
# Verify installation
docker --version
```
6. Enable auto-start on boot:
```bash
# Enable containerd auto-start
sudo systemctl enable containerd
# Enable Docker auto-start
sudo systemctl enable docker
# Verify auto-start status
sudo systemctl is-enabled containerd
sudo systemctl is-enabled docker
```

### 11.6.2 Offline Install docker-compose
```bash
# Copy the downloaded file to the offline machine, then:
# Rename to docker-compose
mv docker-compose-linux-x86_64 docker-compose

# Copy to system path
sudo cp docker-compose /usr/local/bin/

# Set execution permissions
sudo chmod +x /usr/local/bin/docker-compose

# Create symlink (optional)
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

## 11.7 Deploy the Application
### 11.7.1 Pull Images
Images are hosted on CNB Docker Registry, supporting both amd64 and arm64 architectures. `docker pull` will automatically match your CPU architecture:
```bash
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-frontend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-backend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/redis:7.2-alpine
```
If the VM has no network access, use offline build scripts to build images locally and transfer them, see Section 6.3 Offline Deployment.

### 11.7.2 Copy Config Files to VM
Copy `docker-compose.yml` and `start-containers.sh` from the project root to the VM's runtime directory:
```bash
scp -P 2222 docker-compose.yml start-containers.sh cj@localhost:/home/cj/warehouse
```
### 11.7.3 Deploy

```bash
# Create runtime directory under home
sudo mkdir warehouse
cd warehouse
# Pull images (if VM has network access)
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-frontend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-backend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/redis:7.2-alpine
# Set execution permissions
chmod +x start-containers.sh
# Run the script
./start-containers.sh
```

### 11.7.4 Usage
### VirtualBox Port Forwarding Setup
Configure port forwarding in VirtualBox:
1. VM Settings → Network → Advanced → Port Forwarding
2. Add rule:
    - **Name**: Web
    - **Protocol**: TCP
    - **Host IP**: (empty)
    - **Host Port**: 8081
    - **Guest IP**: (empty)
    - **Guest Port**: 8081

Visit `localhost:8081` to access the login page. Default admin username and password are both `admin`.

## 12. Local Development & Debugging
You need to install Redis yourself, set the password to `redis123` and port to `6379`. If Redis is not installed, the system can still run — just ignore the Redis connection errors, as they currently do not affect functionality.

## 13. System Configuration
1. **Access Token Expiration**: Used in JWT mode, sets JWT token expiration time, default 1440 minutes (24 hours).
2. **Sliding Session Timeout & Short-term Token Expiration**: Used in sliding session mode. Short-term token expires after 60 minutes of inactivity by default. If the sliding session timeout has not been exceeded, the system automatically renews the token and resets the sliding session timer. If the sliding session timeout is exceeded, the user will be logged out.
3. **Redis Connection Address**: You can use your own Redis instance instead of the Docker Redis.

## 14. License
This project is licensed under the CC BY-NC-SA 4.0 (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International) License.

- Personal use, modification, and sharing: Completely free, no additional authorization required
- Commercial use: **Prohibited**. Contact the author for commercial licensing
- Attribution to the original author is required; derivative works must use the same license

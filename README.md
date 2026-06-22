# 仓库管理系统 (Warehouse Management System)

## 1.项目概述

仓库管理系统是一个基于现代Web技术栈构建的完整仓库管理解决方案，采用前后端分离架构，支持多用户权限管理、物料管理、库存跟踪、数据备份恢复等功能。
适用于人员少的小部门，没有物流跟踪分拣入库等复杂场景需求，但又需要局域网内记录、查看物料库存的情况。
## 2.运行效果

### 登录与首页

**登录界面**  
![登录界面](./screenshot/登录界面.png)

**默认首页**  
![默认首页](./screenshot/默认首页.png)

### 基础数据管理

**仓库配置**  
![仓库配置](./screenshot/仓库配置.png)

**货位配置**  
![货位配置](./screenshot/货位配置.png)

**专业管理**  
![专业管理](./screenshot/专业管理.png)

**客户管理**  
![客户管理](./screenshot/客户管理.png)

**供应商管理**  
![供应商管理](./screenshot/供应商管理.png)

**器材信息**  
![器材信息](./screenshot/器材信息.png)

### 库存管理

**入库管理**  
![入库管理](./screenshot/入库管理.png)

**出库管理**  
![出库管理](./screenshot/出库管理.png)

**库存明细**  
![库存明细](./screenshot/库存明细.png)

**库存变更流水**  
![库存变更流水](./screenshot/库存变更流水.png)

### 账户管理
**权限管理**  
![权限管理](./screenshot/权限管理.png)

**角色管理**  
![角色管理](./screenshot/角色管理.png)

**用户管理**  
![用户管理](./screenshot/用户管理.png)

### 系统设置
**数据库管理**  
![数据库管理](./screenshot/数据库管理.png)

**器材编码设置**  
![器材编码设置](./screenshot/器材编码设置.png)

**个人设置**  
![个人设置](./screenshot/个人设置.png)

**系统配置管理**  
![系统配置管理](./screenshot/系统配置管理.png)

## 3.技术栈

**后端技术栈:**
- **框架**: FastAPI + SQLModel
- **数据库**: SQLite (主业务数据库 + 系统配置数据库)
- **认证**: JWT (OAuth2 Bearer Token)
- **缓存**: Redis
- **容器化**: Docker
- **其他**: Pydantic、bcrypt、fpdf2等

**前端技术栈:**
- **框架**: Vue 3 + TypeScript
- **UI组件**: Element Plus
- **路由**: Vue Router
- **状态管理**: Pinia
- **构建工具**: Vite
- **图表**: ECharts

## 4.项目结构

```
WarehouseManagement/
├── backend/                 # 后端服务
│   ├── backup/             # 备份管理模块
│   ├── config/             # 配置文件
│   ├── core/               # 核心组件（安全、配置、日志等）
│   ├── database/           # 数据库管理
│   ├── initialize/         # 系统初始化
│   ├── models/             # 数据模型
│   ├── routes/             # API路由
│   ├── schemas/            # Pydantic模式
│   ├── utils/              # 工具函数
│   └── main.py             # 应用入口
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # Vue组件
│   │   ├── services/       # API服务
│   │   ├── stores/         # 状态管理
│   │   └── router/         # 路由配置
│   └── package.json
├── warehouseBackend/       # 数据存储目录,**运行后自动生成**
│   ├── data/              # 数据库文件
│   ├── logs/              # 日志文件
│   └── backups/           # 备份文件
├── config/                # nginx配置文件,**运行后自动生成**
├── logs/nginx/                # nginx日志文件,**运行后自动生成**
└── docker-compose.yml     # Docker编排配置
```

## 5.主要功能模块

### 5.1 用户认证与权限管理
- **用户注册/登录**: OAuth2密码模式认证
- **权限控制**: 基于角色的权限管理系统
- **会话管理**: JWT令牌认证
- **用户管理**: 用户信息维护、权限分配

### 5.2 基础数据管理
- **仓库管理**: 多仓库配置、仓库信息维护
- **客户管理**: 客户档案管理
- **供应商管理**: 供应商信息管理
- **货位管理**: 仓库货位配置

### 5.3 物料管理
- **器材管理**: 器材基本信息、分类管理
- **专业管理**: 专业分类体系
- **装备管理**: 装备类型管理
- **编码体系**: 器材编码分类层级管理

### 5.4 库存管理
- **入库管理**: 入库单创建、审核、执行
- **出库管理**: 出库单创建、审核、执行
- **库存查询**: 实时库存查询、库存明细
- **库存流水**: 库存变更记录跟踪

### 5.5 系统管理
- **系统配置**: 系统参数配置
- **数据备份**: 自动/手动数据备份
- **数据恢复**: 备份数据恢复功能
- **系统监控**: 系统状态监控、日志管理

### 5.6 报表与统计
- **仪表板**: 关键指标展示
- **统计报表**: 各类业务统计
- **分类账页**: 器材分类账页生成
- **数据导出**: Excel、PDF格式导出

## 6.安装与部署

### 6.1环境要求
- Python 3.13+
- Node.js 18+
- Docker & Docker Compose (推荐)

#### 6.2 快速启动 (Docker方式)
1. **克隆项目**
```bash
git clone https://cnb.cool/wtrw09/warehouse.git
#或
git clone https://gitee.com/wtrw09/warehouse.git
#或
git clone https://github.com/wtrw09/warehouse.git
cd WarehouseManagement
```
2. **拉取镜像**

镜像托管在 CNB Docker 制品库，支持 amd64 和 arm64 多架构，docker pull 会自动匹配当前 CPU 架构：
```bash
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-frontend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-backend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/redis:7.2-alpine
```
3. **启动容器**
复制docker-compose.yml和start-containers.ps1和start-containers.sh文件到项目根目录你要运行的目录下,Windows系统运行start-containers.ps1,Linux/Mac系统运行start-containers.sh。
注意：Linux中需要给start-containers.sh添加可执行权限。
```bash
$ chmod +x start-containers.sh
```
然后以管理员权限运行start-containers.sh：
```bash
$ sudo ./start-containers.sh
```
4. **访问系统**
`http://localhost:8081/login`或者`http://[你的电脑IP地址]:8081/login`

### 6.3 离线部署（备选方案）

如果目标机器无法访问网络，可以使用离线构建脚本在本地构建镜像后传输部署：

1. 使用 `frontend/build-amd64-offline.ps1` 或 `frontend/build-arm64-offline.ps1` 脚本构建前端镜像
2. 使用 `backend/build-amd64-offline.ps1` 或 `backend/build-arm64-offline.ps1` 脚本构建后端镜像
3. 将生成的 `.tar` 文件传输到目标服务器
4. 在目标服务器上使用 `docker load -i xxx.tar` 加载镜像

> 注：离线部署时需要修改 docker-compose.yml 中的镜像地址为本地镜像名称，并添加 `pull_policy: never`。

### 6.4 手动部署
1. **克隆项目**
```bash
git clone https://gitee.com/wtrw09/warehouse.git
cd WarehouseManagement
```
**后端部署:**
```bash
cd backend
pip install -r requirements.txt
python main.py
```
**前端部署:**
```bash
cd frontend
npm install
npm run build
npm run dev
```
## 7.系统初始化

系统首次启动时会自动执行初始化流程：
1. 检查数据库连接状态
2. 创建必要的数据库表结构
3. 初始化系统默认数据
4. 启动定时备份调度器
5. 配置字体和日志系统

## 8.数据库架构

系统采用双数据库设计：
- **主业务数据库** (`warehouse.db`): 存储业务数据
- **系统配置数据库** (`system_config.db`): 存储系统配置和权限数据

## 9.权限系统

系统采用基于角色的权限控制(RBAC)模型：

### 9.1 权限层级
1. **系统管理员**: 最高权限，可管理所有功能
2. **仓库管理员**: 管理指定仓库的业务操作
3. **业务部门代表**: 能够查看仓库运行数据，但不能够更改，只有监督作用
4. **查看员**: 仅能够查看库存数据，不能进行任何更改操作，给客户（部门能够申领物资的人）使用

### 9.2 权限分类
- `AUTH-*`: 用户认证相关权限
- `BASE-*`: 基础数据管理权限
- `STOCK-*`: 库存管理权限
- `SYSTEM-*`: 系统管理权限
- `IO-*`: 出入库操作权限

## 10.备份与恢复

### 备份策略
- **定时备份**: 每日自动备份
- **手动备份**: 按需手动创建备份

### 恢复机制
- 支持从备份文件恢复数据
- 提供恢复状态跟踪
- 支持选择性恢复

## 日志管理

系统提供多级别日志记录：
- **应用日志**: 业务操作记录
- **错误日志**: 异常和错误记录
- **调试日志**: 开发调试信息
- **恢复日志**: 备份恢复操作记录

## 11.虚拟机安装部署docker（以almalinux8为例）
如果你的windows系统或电脑硬件不支持虚拟化，无法安装docker，你可以尝试在虚拟机中安装docker。
### 11.1 在虚拟机中安装 almalinux
### 11.2 把用户添加到 sudo 中
```bash
# 1. 切换到 root 用户，首先切换到 root 用户
su -
# 2. 编辑 sudoers 文件，使用文本编辑器（如 vim）打开 /etc/sudoers 文件。
vi /etc/sudoers
# 3. 添加用户到 sudoers 文件，在打开的文件中，找到类似于 root ALL=(ALL) ALL 的行，在其下方添加一行，将 userName 用户添加进去。
root ALL=(ALL) ALL
userName ALL=(ALL) ALL
```
### 11.3 打开网络设置
```bash
# 启动网络文本界面
sudo nmtui
```
### 11.4 安装 OpenSSH 服务器
```bash
# 启动SSH服务 
sudo systemctl start sshd 
sudo systemctl enable sshd 
# 检查服务状态 
sudo systemctl status sshd 
# 查看IP地址（用于连接） 
ip addr show
```
在 VirtualBox 中配置端口转发：
1. 虚拟机设置 → 网络 → 高级 → 端口转发
2. 添加规则：
    - **名称**: SSH
    - **协议**: TCP
    - **主机 IP**: 空
    - **主机端口**: 2222（或其他未占用端口）
    - **子系统 IP**: 空
    - **子系统端口**: 22
### 11.5 从 Windows 主机传输文件
下载 docker-20.10.24.tgz，进行解压，和docker-compose 程序，一起发送到服务器
```bash
# 传输整个文件夹
scp -P 2222 -r 本地文件夹 username@localhost:/home/username/具体目录
```
如果出现错误WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!
```bash
# 删除localhost:2222的旧密钥记录 
ssh-keygen -R [localhost]:2222
```
### 11.6 安装 docker 和 docker-compose
### 11.6.1 安装 docker
1. 从Docker静态包中复制所有必要的二进制文件 
```bash
sudo cp -f docker/* /usr/bin/
# 设置执行权限 
sudo chmod +x /usr/bin/docker*
sudo chmod +x /usr/bin/containerd* 
sudo chmod +x /usr/bin/ctr 
sudo chmod +x /usr/bin/runc
```
2. 编写containerd.service
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
3. 运行 container
```bash
# 测试containerd是否能运行 
sudo /usr/bin/containerd --version
# 启动containerd服务
sudo systemctl daemon-reload
sudo systemctl start containerd
sudo systemctl enable containerd
```

4.  编写docker.service
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

5. 启动Docker服务
```bash
# 重新加载systemd
sudo systemctl daemon-reload
# 启动Docker
sudo systemctl start docker
# 设置开机自启
sudo systemctl enable docker
# 验证安装
docker --version
# 检查Docker版本 
docker --version
```
6. 设置开机启动
```bash
# 启用containerd开机自启
sudo systemctl enable containerd
# 启用Docker开机自启
sudo systemctl enable docker
# 验证是否已启用开机启动
sudo systemctl is-enabled containerd
sudo systemctl is-enabled docker
```
### 11.6.2 离线安装 docker-compose
```bash
# 将下载的文件复制到离线机器，然后执行：
# 重命名为docker-compose
mv docker-compose-linux-x86_64 docker-compose

# 复制到系统路径
sudo cp docker-compose /usr/local/bin/

# 设置执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 创建符号链接（可选）
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```
## 11.7 安装部署程序
### 11.7.1 拉取镜像
镜像托管在 CNB Docker 制品库，支持 amd64 和 arm64 多架构，docker pull 会自动匹配当前 CPU 架构：
```bash
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-frontend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-backend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/redis:7.2-alpine
```
如果虚拟机无法访问网络，可以使用离线构建脚本在本地构建镜像后传输部署，参见 6.3 离线部署。
### 11.7.2 复制配置文件到虚拟机
将根目录下的 `docker-compose.yml` 和 `start-containers.sh` 文件复制到虚拟机的运行目录：
```bash
scp -P 2222 docker-compose.yml start-containers.sh cj@localhost:/home/cj/warehouse
```
### 11.7.3 部署

```
#在home目录下新建运行目录
sudo mkdir warehouse
cd warehouse
#拉取镜像（如果虚拟机可访问网络）
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-frontend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/warehouse-backend:latest
docker pull docker.cnb.cool/wtrw09/warehouse/redis:7.2-alpine
#设置运行权限
chmod +x start-containers.sh
#运行脚本
./start-containers.sh
```
### 11.7.4 使用
###  VirtualBox 端口转发设置
在 VirtualBox 中配置端口转发：
1. 虚拟机设置 → 网络 → 高级 → 端口转发
2. 添加规则：
    - **名称**: SSH
    - **协议**: TCP
    - **主机 IP**: 空
    - **主机端口**: 8081
    - **子系统 IP**: 空
    - **子系统端口**: 8081
访问 localhost:8081 即可访问登录页面，默认管理账号和密码都是admin
## 12.本地运行调试
你需要自己安装redis,设置密码为redis123，端口设置为6379。如果不安装redis,也可运行，可以忽略报错，目前不影响使用。
## 13.系统配置说明
1. 访问令牌过期时间：用于 JWT 模式，设置 JWT 令牌过期时间，默认1440 分钟即 24 小时
2. 滑动会话超时时间和短期访问令牌过期时间：用于滑动会话模式，短期访问令牌过期时间，默认 60 分钟，超过 60 分钟用户不操作，短期令牌过期，如果时间没有超出滑动会话超时时间，则系统自动续上令牌，并重置滑动会话超时时间。如果超过滑动会话超时时间未操作，用户等会被登出。
3. Redis连接地址：可以不用 docker redis，自己配置
## 14.许可证
本项目采用MIT许可证。
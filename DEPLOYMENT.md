## AI面试系统部署指南

本指南将详细介绍如何在Linux云服务器上部署AI面试系统。请按照以下步骤操作。

### 1. 环境准备

确保您的Linux服务器满足以下要求：

*   **操作系统**: Linux (例如 CentOS, Ubuntu, TencentOS)
*   **Python**: 3.8 或更高版本 (推荐使用 `pyenv` 或 `conda` 进行版本管理)
*   **Git**: 用于克隆项目代码
*   **pip**: Python包管理工具

**安装Python (以CentOS为例，其他系统类似)**

```bash
sudo yum install -y python3 python3-pip git
# 或者对于Ubuntu/Debian
# sudo apt update
# sudo apt install -y python3 python3-pip git
```

**验证安装**

```bash
python3 --version
pip3 --version
git --version
```

### 2. 获取项目代码

首先，登录到您的云服务器，然后克隆项目代码到您希望部署的目录。

```bash
git clone <您的项目Git仓库地址>
cd ai_interview # 进入项目根目录
```

### 3. 创建并激活虚拟环境

为了避免依赖冲突，强烈建议为项目创建一个独立的Python虚拟环境。

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装项目依赖

项目的所有Python依赖都列在 `requirements.txt` 文件中。使用 `pip` 安装它们。

```bash
pip install -r requirements.txt
```

### 5. 数据库配置

项目使用了MySQL数据库。您需要确保MySQL服务已安装并运行，然后配置数据库连接。

1.  **安装MySQL客户端 (如果尚未安装)**

    ```bash
    # CentOS
    sudo yum install -y mysql
    # Ubuntu/Debian
    sudo apt install -y default-mysql-client
    ```

2.  **创建数据库和用户**

    登录到您的MySQL服务器，创建数据库和用户，并授予权限。

    ```sql
    CREATE DATABASE ai_interview_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER 'your_db_user'@'localhost' IDENTIFIED BY 'your_db_password';
    GRANT ALL PRIVILEGES ON ai_interview_db.* TO 'your_db_user'@'localhost';
    FLUSH PRIVILEGES;
    EXIT;
    ```

3.  **配置数据库连接**

    项目通过环境变量或配置文件管理数据库连接。请检查项目根目录下的 `.env` 文件（如果存在）或 `config/db_config.py` 文件，并根据您的数据库设置进行修改。

    通常，您需要在 `.env` 文件中添加或修改以下内容：

    ```
    DATABASE_URL="mysql+pymysql://your_db_user:your_db_password@localhost:3306/ai_interview_db"
    ```

### 6. 模型下载与配置

AI面试系统可能依赖于预训练模型。请检查项目中的 `model` 目录或相关文档（例如 `model/model_deployment_guide.md`），了解如何下载和配置所需的AI模型。

通常，您可能需要：

*   从指定链接下载模型文件。
*   将模型文件放置在项目中的特定目录。
*   如果模型路径在代码中硬编码，可能需要修改相关配置文件或代码。

### 7. 启动项目

项目使用 `uvicorn` 启动，入口文件是 `run.py`。

```bash
# 确保您仍在虚拟环境中
source venv/bin/activate

# 启动项目
python3 run.py
```

项目启动后，您应该会看到类似以下输出：

```
Starting server...
Starting app...
App running on: http://<您的服务器IP>:8000
局域网访问地址: http://<您的服务器IP>:8000/ui
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 8. 配置防火墙 (如果需要)

如果您的云服务器开启了防火墙，请确保开放8000端口，以便外部访问。

**对于CentOS/RHEL (使用firewalld)**

```bash
sudo firewall-cmd --zone=public --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

**对于Ubuntu/Debian (使用ufw)**

```bash
sudo ufw allow 8000/tcp
sudo ufw enable
```

### 9. 后台运行 (可选)

为了让项目在您退出SSH会话后继续运行，您可以使用 `nohup` 或 `screen`/`tmux`。

**使用 nohup**

```bash
nohup python3 run.py > app.log 2>&1 &
```

这将把输出重定向到 `app.log` 文件，并在后台运行。您可以使用 `tail -f app.log` 查看日志。

**使用 screen/tmux (推荐)**

`screen` 或 `tmux` 允许您创建可分离的会话。

1.  **安装 screen/tmux**

    ```bash
    # CentOS
    sudo yum install -y screen
    # Ubuntu/Debian
    sudo apt install -y screen
    ```

2.  **创建新会话并运行项目**

    ```bash
screen -S ai_interview_session
# 在新的screen会话中
source venv/bin/activate
python3 run.py
    ```

3.  **分离会话**

    按下 `Ctrl+A` 然后 `D` 键即可分离会话。

4.  **重新连接会话**

    ```bash
screen -r ai_interview_session
    ```

### 10. 访问前端界面

项目启动并端口开放后，您可以通过浏览器访问 `http://<您的服务器IP>:8000/ui` 来使用AI面试系统的前端界面。

希望这份文档能帮助您顺利部署项目！
import uvicorn

import sys
import os
import uvicorn
from database.database import Base, engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



# 修改启动部分代码
if __name__ == "__main__":
    print("Starting server...")
    print("Starting app...")
    # 获取本机局域网IP（自动获取）
    import socket
    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP
    
    local_ip = get_local_ip()
    print(f"App running on: http://{local_ip}:2025")
    print(f"局域网访问地址: http://{local_ip}:2025/ui")  # 前端访问地址
    uvicorn.run("app:app", host="0.0.0.0", port=2025, reload=True)
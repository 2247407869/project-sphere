# 🚀 Hugging Face Spaces 部署检查清单

## 📋 部署前检查

### ✅ 必要文件
- [ ] `app.py` - HF入口文件
- [ ] `main.py` - 主应用程序
- [ ] `requirements.txt` - Python依赖
- [ ] `README.md` - 项目说明（包含HF配置）
- [ ] `src/` - 源代码目录
- [ ] `frontend/` - 前端文件目录
- [ ] `.env.example` - 环境变量示例

### ✅ 配置文件
- [ ] README.md 包含正确的 YAML front matter
- [ ] requirements.txt 包含所有必要依赖
- [ ] app.py 配置正确的端口 (7860)

### ✅ 环境变量准备
- [ ] `DEEPSEEK_API_KEY` - DeepSeek API密钥
- [ ] `INFINICLOUD_URL` - WebDAV服务器URL
- [ ] `INFINICLOUD_USER` - WebDAV用户名
- [ ] `INFINICLOUD_PASS` - WebDAV密码

## 🌐 创建 Hugging Face Space

### 步骤1: 创建Space
1. 访问 https://huggingface.co/spaces
2. 点击 "Create new Space"
3. 填写信息：
   - **Space name**: `project-sphere`
   - **License**: MIT
   - **SDK**: Gradio
   - **Hardware**: CPU basic (免费) 或 CPU upgrade (付费)

### 步骤2: 配置环境变量
在Space的 Settings → Repository secrets 中添加：
```
DEEPSEEK_API_KEY=your_api_key_here
INFINICLOUD_URL=https://your-webdav-server.com/dav
INFINICLOUD_USER=your_username
INFINICLOUD_PASS=your_password
```

### 步骤3: 上传代码
```bash
# 克隆Space仓库
git clone https://huggingface.co/spaces/YOUR_USERNAME/project-sphere
cd project-sphere

# 复制项目文件
cp -r /path/to/project_code/* .

# 提交代码
git add .
git commit -m "Initial deployment of Project Sphere"
git push
```

## 🧪 部署后验证

### 基本功能测试
- [ ] 访问Space URL，页面正常加载
- [ ] 健康检查: `/health` 返回正常状态
- [ ] 主页聊天界面正常显示
- [ ] Debug页面: `/debug` 可以访问

### 核心功能测试
- [ ] 发送消息，AI正常回复
- [ ] 流式响应正常工作
- [ ] 会话保存功能正常
- [ ] 页面刷新后聊天记录保持

### 高级功能测试
- [ ] 提供个人信息，触发记忆创建
- [ ] 手动归档功能正常
- [ ] M3记忆文件正确创建
- [ ] Debug页面显示正确的系统状态

## 🔧 故障排除

### 常见问题
1. **构建失败**
   - 检查 requirements.txt 格式
   - 确保所有文件路径正确

2. **应用无法启动**
   - 检查 app.py 语法
   - 查看 Space 的 Logs 页面

3. **API调用失败**
   - 验证 DEEPSEEK_API_KEY 是否正确
   - 检查API余额是否充足

4. **存储连接失败**
   - 验证WebDAV配置
   - 测试存储服务可用性

### 调试方法
1. 查看Space的 Logs 页面
2. 访问 `/health` 检查系统状态
3. 在Debug页面查看详细信息
4. 检查浏览器开发者工具的网络请求

## 📊 性能优化

### 硬件选择
- **CPU basic** (免费): 适合演示和轻度使用
- **CPU upgrade** (付费): 更稳定，适合生产使用

### 优化建议
- 启用响应缓存
- 优化API调用频率
- 监控资源使用情况

## 🔒 安全注意事项

- [ ] 所有敏感信息都通过HF Secrets配置
- [ ] 代码中没有硬编码的密钥
- [ ] 定期更新依赖包
- [ ] 监控异常访问模式

## 📈 监控和维护

### 定期检查
- [ ] API调用量和余额
- [ ] 存储空间使用情况
- [ ] 应用性能指标
- [ ] 用户反馈和错误日志

### 更新流程
1. 在本地测试更改
2. 更新版本号
3. 提交到Space仓库
4. 验证部署结果

---

## 🎉 部署完成！

恭喜！如果所有检查项都已完成，你的 Project Sphere 应该已经成功部署到 Hugging Face Spaces。

**Space URL**: https://huggingface.co/spaces/YOUR_USERNAME/project-sphere

享受你的AI记忆助手吧！🧠✨
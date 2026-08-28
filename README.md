# 在线答题系统

基于 **Flask** 构建的在线答题/刷题平台，支持四种题型、分组答题解锁路线图、进度保存、排行榜、批量导入导出等完整功能。

## 技术栈

| 层级 | 技术 |
|------|------|
| Web框架 | Flask |
| ORM | SQLAlchemy (Flask-SQLAlchemy, 多 bind 支持) |
| 认证 | Flask-Login |
| 模板引擎 | Jinja2 |
| 数据库 | 默认 SQLite，支持 MySQL/PostgreSQL |
| 数据分离 | 配置 / 用户 / 题库数据可分离存储 |
| 数据导入导出 | pandas + openpyxl |

## 项目结构

```
QuizPlatform/
├── app.py              # 主入口（应用初始化 + 路由注册）
├── config.py           # 配置管理（密钥、数据库URI、管理员账号）
├── models.py           # 数据库模型（7张核心表）
├── utils.py            # 辅助函数（权限装饰器、答案判定、数据库初始化）
├── routes/             # 路由模块
│   ├── __init__.py     # 路由注册中心（Flask蓝图 + 全局中间件）
│   ├── shared.py       # 公共工具（输入验证、文件上传辅助函数）
│   ├── auth.py         # 认证路由（登录/注册/注销）
│   ├── quiz.py         # 核心答题路由（答题/分组/排行榜/学习路线）
│   ├── admin.py        # 管理后台路由（CRUD + 导入导出 + 用户管理）
│   └── api/            # RESTful API 路由（前后端分离）
│       ├── __init__.py # API 蓝图注册
│       ├── auth.py     # API 认证接口
│       ├── quiz.py     # API 答题接口
│       └── admin.py    # API 管理后台接口
├── frontend/           # Vue 3 前端（前后端分离模式）
│   ├── src/
│   │   ├── api/        # API 请求封装
│   │   ├── stores/     # Pinia 状态管理
│   │   ├── views/      # Vue 页面组件
│   │   └── router/     # Vue Router 路由配置
│   ├── package.json
│   └── vite.config.js
├── templates/          # Jinja2 HTML 模板（传统服务端渲染）
│   ├── base.html       # 基础布局（玻璃拟态 + 动态背景）
│   ├── index.html      # 首页（分类展示）
│   ├── login.html      # 登录页
│   ├── register.html   # 注册页
│   ├── quiz.html       # 答题页
│   ├── result.html     # 答题结果页（全对动画）
│   ├── history.html    # 答题历史记录
│   ├── roadmap.html    # 题组学习路线图
│   ├── study.html      # 学习资料页
│   ├── leaderboard.html # 排行榜（领奖台 + 排名表）
│   └── admin/          # 管理后台模板
│       ├── dashboard.html
│       ├── categories.html
│       ├── groups.html
│       ├── group_form.html
│       ├── questions.html
│       ├── question_form.html
│       ├── import.html
│       ├── export.html
│       ├── users.html
│       └── history.html
├── static/             # 静态资源（CSS/JS/图标/背景图）
│   ├── import_prompt.txt
│   └── icons/
├── uploads/            # 上传文件目录
├── instance/           # SQLite 数据库文件（运行时生成）
├── requirements.txt    # Python 依赖
├── runcode.json        # OpenCode 配置文件
├── setup.bat           # Windows 一键安装脚本
├── setup.sh            # Linux/macOS 一键安装脚本
├── deploy.sh           # 生产环境部署脚本
└── .gitignore
```

## 数据模型

| 模型 | 说明 | 关键字段 |
|------|------|----------|
| **User** | 用户 | username, email, password_hash, role(user/admin), status |
| **Category** | 题目分类 | name, parent_id（支持层级分类）, sort_order |
| **Group** | 题目分组 | name, category_id, unlock_order（解锁序号）, study_content, background_image |
| **Question** | 题目 | category_id, group_id, type(single/multiple/judge/fill), content, options, answer, analysis, difficulty |
| **QuizRecord** | 答题记录 | user_id, category_id, score, correct_count, start/end_time |
| **QuizDetail** | 答题详情 | record_id, question_id, user_answer, is_correct, score_earned |
| **UserProgress** | 用户进度 | user_id, category_id, last_completed_group_id（题组解锁依据） |

## 快速开始

### 前置要求

- Python 3.8+
- pip

### 安装与运行

#### 方式一：一键运行（推荐）

- **Windows**：双击运行 `setup.bat`
- **Linux/macOS**：终端执行 `bash setup.sh`

脚本会自动检查 Python 环境、安装依赖并启动服务。

#### 方式二：手动配置

```bash
# 克隆项目
git clone https://github.com/woshigezhe/QuizPlatform.git
cd QuizPlatform

# 国内网络慢可用镜像：
#   git clone https://gitclone.com/github.com/woshigezhe/QuizPlatform.git

# 安装依赖（--only-binary 可避免需要 C++ 编译器）
pip install -r requirements.txt --only-binary :all:

# 运行应用
python app.py
```

访问 **http://127.0.0.1:8000**

### 默认管理员

| 字段 | 值 |
|------|-----|
| 用户名 | `admin` |
| 密码 | `admin123` |

首次启动时数据库和默认管理员账号会自动创建。

## 功能特性

### 用户端

- ✅ **四种题型**：单选、多选、判断、填空
- ✅ **普通答题模式**：选择分类后随机抽取题目作答
- ✅ **分组答题路线图**：题组按解锁顺序排列，全对通过当前题组才能解锁下一组
- ✅ **断点续答**：进度自动保存，下次进入从上次完成的分组继续
- ✅ **学习资料**：每个题组可关联 Markdown/HTML 学习内容
- ✅ **答题历史**：查看个人所有答题记录
- ✅ **排行榜**：按总分和正确率排名
- ✅ **可视化路线图**：图形化展示题组解锁进度

### 管理后台 (`/admin`)

- ✅ **分类管理**：新增/删除题目分类（支持层级分类）
- ✅ **分组管理**：新增/编辑/删除题组，设置解锁顺序、学习内容、背景图片
- ✅ **题目管理**：新增/编辑/删除题目，支持批量删除
- ✅ **批量导入**：支持 Excel/CSV 文件导入题目，自动识别分类和分组
- ✅ **数据导出**：按分类、时间、用户筛选，导出答题记录为 Excel
- ✅ **用户管理**：禁用/启用用户、删除用户及数据、清除答题历史

### 其他特性

- ✅ 全对动画庆祝效果
- ✅ 多数据库支持：默认 SQLite，通过环境变量 `DATABASE_URL` 切换 MySQL/PostgreSQL
- ✅ 自定义背景图片（题组答题页）
- ✅ 管理员权限保护（`admin_required` 装饰器）

## 环境配置

### 自动环境识别

系统会根据以下规则自动判断当前运行环境：

| 触发条件 | 环境 |
|----------|------|
| `ENV=production` | 生产环境 |
| `FLASK_DEBUG=1` 或 `ENV=development` | 开发环境 |
| 通过 `gunicorn` 启动 | 生产环境 |
| 默认 | 开发环境 |

### 开发环境（默认）

无需任何配置，直接 `python app.py` 启动：
- 数据库：SQLite（`instance/quiz.db`）
- SECRET_KEY：使用默认值
- 管理员密码：`admin123`

#### 指定数据库文件路径（可选）

开发/生产环境均可通过 `DB_PATH` 环境变量直接读取指定路径的 SQLite 数据库：

```bash
# Windows
set DB_PATH=D:\data\quiz.db
python app.py

# Linux/macOS
export DB_PATH=/data/quiz.db
python app.py
```

支持绝对路径或相对路径（相对于项目根目录），父目录不存在时自动创建。

### 生产环境

```bash
# 方式一：设置环境标识
export ENV=production

# 方式二：通过 gunicorn 启动自动识别
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

#### 生产环境数据库配置

**选项 A：使用 DATABASE_URL（推荐）**

```bash
# MySQL
export DATABASE_URL=mysql+pymysql://user:password@db-server:3306/quiz_platform

# PostgreSQL
export DATABASE_URL=postgresql://user:password@db-server:5432/quiz_platform
```

**选项 B：使用单独的环境变量**

```bash
export DB_TYPE=mysql           # mysql 或 postgresql
export DB_HOST=db-server
export DB_PORT=3306
export DB_USER=quiz_user
export DB_PASS=your_password
export DB_NAME=quiz_platform
```

**选项 C：数据物理分离（可选高级功能）**

将题库配置、用户数据、答题记录分别存储到不同数据库：

```bash
export CONFIG_DATABASE_URL=mysql+pymysql://user:pass@db1/config_db
export USERS_DATABASE_URL=mysql+pymysql://user:pass@db2/users_db
export RECORDS_DATABASE_URL=mysql+pymysql://user:pass@db3/records_db
```

#### 生产环境安全配置

```bash
export SECRET_KEY=your-random-secret-key-here
export ADMIN_PASSWORD=your-strong-admin-password
export ADMIN_EMAIL=admin@yourdomain.com
```

## 批量导入格式

上传的 Excel/CSV 文件需包含以下列：

| 列名 | 说明 | 示例 |
|------|------|------|
| 分类名称 | 题目所属分类 | `数学` |
| 分组名称 | 题目所属分组（可选） | `第一章` |
| 题型 | single / multiple / judge / fill | `single` |
| 题干 | 题目内容 | `1+1=?` |
| 选项 | 以 \| 分隔（单选/多选时必填） | `A.1\|B.2\|C.3\|D.4` |
| 正确答案 | 答案字符串 | `B` |
| 解析 | 答案解析（可选） | `1+1=2` |
| 难度 | 难度等级（可选，默认1） | `1` |

---

## 架构说明

本项目采用 MVC 分层架构 + RESTful API 双模式设计：

- **传统服务端渲染**：`routes/` 目录下的 Flask 蓝图 + Jinja2 模板，适合直接部署使用
- **前后端分离**：`routes/api/` 目录下的 RESTful API + `frontend/` 目录下的 Vue 3 单页应用
- **公共模块**：`routes/shared.py` 消除路由层和 API 层的代码重复（输入验证、文件上传）

## 安全特性

- Open Redirect 防护：登录重定向 URL 必须为相对路径
- 用户禁用即时生效：管理员禁用用户后，其现有会话立即失效（`before_request` 中间件）
- 会话完整性：所有 session 写入操作均标记 `modified=True`
- 事务完整性：进度删除操作与答题记录创建在同一事务中提交，避免数据不一致
- 日期输入校验：管理后台的日期筛选字段有格式校验和友好的错误提示
- Eager Loading：答题历史查询预加载关联数据，避免 N+1 查询问题
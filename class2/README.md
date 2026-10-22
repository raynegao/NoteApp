# 第二课：NotesApp 建模作业

依据：Session 02 第 33-34 页；NoteApp 版本 `1c83e42`。整理日期：2026-10-09。

本目录是第二课的 **28 条流课堂建模任务**，由课程工作区 `作业/Session02_NotesApp建模/` 的当前成果整理；PDF 来自课程工作区 `output/pdf/`。正式 Project 1 使用 [project1/](../project1/) 中 **16 条流的小组版**，本目录不替换该小组报告。

## 1. 实验观察

学生查看自己的成绩；教师查看、导出和修改成绩；管理员查看用户和班级，创建/删除用户，并使用 Ping。浏览器先向 Flask 发请求，再由 Flask 访问 PostgreSQL，浏览器不直接连接数据库。

使用课程示例账号做了 24 项正常访问检查，全部通过。数据库有 35 个用户、4 个班级、60 条成绩。教师导出班级 1 得到 16 行成绩，全部导出得到 60 行。新增、修改、删除表单只看页面和代码，没有提交。威胁分析没有执行攻击。

## 2. 信任边界

- **TB1**：浏览器与 Flask 之间，客户端输入进入服务器。
- **TB2**：Flask 与 PostgreSQL 之间，应用访问数据库。
- **TB3**：Web 容器与外部 Ping 目标之间。

图中 TB3 带星号：Ping 外部目标时才跨越它。本次只测试容器自身的 `127.0.0.1`；超时提示是本地程序生成的，不是目标返回的数据。

## 3. 数据流图与 Flow List

[查看编号图](数据流图.md) · [打开完整 PDF](Session02_NotesApp_建模作业.pdf)

按功能合并相同方向的数据流。例如成绩页和成绩详情都归入“学生查看成绩”，新增和更新都归入“教师修改成绩”。编号是逻辑箭头，不是每个 HTTP 包的编号。跳转后的页面读取使用对应的查看流程。

| 编号 | 发送方 → 接收方 | 数据 | 边界 |
| --- | --- | --- | --- |
| 1 | 浏览器 → Flask | 登录：用户名和密码 | TB1 |
| 2 | Flask → PostgreSQL | 查询用户账号 | TB2 |
| 3 | PostgreSQL → Flask | 返回账号 ID、用户名、角色 | TB2 |
| 4 | Flask → 浏览器 | 登录结果、会话 Cookie 和跳转 | TB1 |
| 5 | 学生浏览器 → Flask | 查看成绩页或单条成绩详情 | TB1 |
| 6 | Flask → PostgreSQL | 按学生 ID 或成绩 ID 查询成绩 | TB2 |
| 7 | PostgreSQL → Flask | 返回成绩、课程和评语 | TB2 |
| 8 | Flask → 学生浏览器 | 成绩页面 HTML 或详情 JSON | TB1 |
| 9 | 教师浏览器 → Flask | 查看教师页或导出 CSV | TB1 |
| 10 | Flask → PostgreSQL | 查询班级、学生和成绩 | TB2 |
| 11 | PostgreSQL → Flask | 返回查询结果 | TB2 |
| 12 | Flask → 教师浏览器 | 返回教师页面或 CSV 文件 | TB1 |
| 13 | 教师浏览器 → Flask | 新增/更新成绩：ID、成绩、评语 | TB1 |
| 14 | Flask → PostgreSQL | INSERT 或 UPDATE 成绩和评语 | TB2 |
| 15 | PostgreSQL → Flask | 返回写入完成状态 | TB2 |
| 16 | Flask → 教师浏览器 | 跳转到教师页 | TB1 |
| 17 | 管理员浏览器 → Flask | 查看列表、创建用户或删除用户 | TB1 |
| 18 | Flask → PostgreSQL | 查询/插入/删除 users，查询 classes | TB2 |
| 19 | PostgreSQL → Flask | 返回用户/班级数据或执行状态 | TB2 |
| 20 | Flask → 管理员浏览器 | 返回管理页或跳转到管理页 | TB1 |
| 21 | 管理员浏览器 → Flask | 提交 Ping 的 host | TB1 |
| 22 | Flask → Ping 目标 | 发出 ICMP Echo Request | TB3* |
| 23 | Ping 目标 → Flask | 收到 ICMP Echo Reply | TB3* |
| 24 | Flask → PostgreSQL | 查询用户和班级列表 | TB2 |
| 25 | PostgreSQL → Flask | 返回用户和班级列表 | TB2 |
| 26 | Flask → 管理员浏览器 | 返回 Ping 结果和管理页 | TB1 |
| 27 | 浏览器 → Flask | 退出登录 | TB1 |
| 28 | Flask → 浏览器 | 清除会话并跳转到登录页 | TB1 |

## 4. 首版 STRIDE 表

[完整表格](STRIDE.md)对每个编号分别回答六个问题：冒充、篡改、否认、泄露、拒绝服务、越权。`—` 表示当前没有发现这一流的直接威胁，不表示整个系统安全。

- S：示例密码较容易猜；会话密钥固定；API 的 JWT 接受 alg=none，所以有冒用身份的风险。
- T：教师写成绩时只检查角色，没有检查是否是自己的班级；页面也没有转义评语。
- R：修改成绩有一条简单日志，但没有旧值和新值；创建/删除用户、读取及导出没有对应的业务审计。
- I：API 不检查成绩归属；教师页和 CSV 没有按班级归属限制。学生密码、评语在数据库中明文保存。
- D：代码没有请求限速；Ping 同步运行，单次最多等待 10 秒。大量请求可能拖慢服务，未做压测。
- E：Ping 的 host 拼接进 shell 命令，存在命令注入风险；Web 为 root，并挂载 Docker socket，可能扩大后果。

API 不检查成绩归属和 JWT 身份验证弱是两个问题。JWT 不会自动建立管理员会话；不能直接说“伪造 JWT 就能进入 admin”。CSRF 能否成功还取决于浏览器是否发送 Cookie。HTTP 传输风险需要攻击者能接触传输路径；本机 loopback 部署限制了这个范围。

## 5. 代码依据

- 登录与会话：`web/app.py` 的 `login()`、`verify_jwt()`、`login_required()`。
- 成绩读取和权限：`dashboard()`、`api_notes()`、`teacher()`、`export_csv()`。
- 成绩写入和日志：`grades()`、`log()`。
- 用户管理与 Ping：`admin_users()`、`admin_ping()`。
- 评语显示：`web/templates/dashboard.html`、`teacher.html` 中的 `autoescape false`。
- 部署与数据：`web/Dockerfile`、`docker-compose.yml`、`db/init.sql`。只读核对发现 Web 为 root、Docker socket 挂载存在、数据库 SSL 为 off。

原 [简版 Flow List](references/FlowList.md)和[详细草稿](references/FlowList_详细版.md)保留。本作业图和表统一用新的 **1-28** 编号。原简版、原详细版的编号各自独立。

实际检查见 [验证记录.json](验证记录.json)，记录对应 2026-10-09 的本机环境，并非对后续代码版本的重新审计。本课堂稿未声称经过小组确认。伦理声明需本人签署，本次未代签。第三课和正式 Project 1 不在这份课堂稿的范围内。

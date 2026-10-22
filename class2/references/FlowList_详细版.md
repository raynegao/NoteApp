# NotesApp Flow List 草稿

这份清单把你的想法整理为可以画在数据流图上的编号箭头：学生登录和查看成绩、教师新增和更新成绩、管理员新增用户和使用 Test the server。每一行都写清楚谁发送给谁、跨越什么数据，后续在图中使用同一编号，并对应到 STRIDE 表。

- 更新日期：2026-10-07（Europe/Paris）。
- 依据：`Session 02 Threat Model and NotesApp.pdf`第 33–34 页，以及 NotesApp 代码版本 `1c83e42`。
- 主要代码：[app.py](https://github.com/KristenPire/NoteApp/blob/1c83e42/web/app.py)；页面表单见 [学生页](https://github.com/KristenPire/NoteApp/blob/1c83e42/web/templates/dashboard.html)、[教师页](https://github.com/KristenPire/NoteApp/blob/1c83e42/web/templates/teacher.html)、[管理员页](https://github.com/KristenPire/NoteApp/blob/1c83e42/web/templates/admin.html)。
- 历史状态（2026-10-07）：按你的想法整理的 Flow List 草稿，当时完整数据流图和 STRIDE 表尚未完成；编号 29–32 是学生成绩详情功能的补充。当前 28 条流课堂成果见 [class2 作业说明](../README.md)，两份材料编号独立。

## 先分清功能和数据流

“学生登录”是一个功能，可以拆成四条数据流：浏览器提交凭据、Flask 查询数据库、数据库返回匹配的记录、Flask 返回登录响应。

统一写法：**编号. 发送方 → 接收方：消息或数据。**

数据库通过 Flask 与浏览器交换信息。例如“数据库返回成绩”应写成“PostgreSQL → Flask：成绩记录”，再另写“Flask → 学生浏览器：成绩页面”。

## 组件与信任边界

| 组件 | 在图中表示什么 |
| --- | --- |
| 学生浏览器 | 学生使用的客户端 |
| 教师浏览器 | 教师使用的客户端 |
| 管理员浏览器 | 管理员使用的客户端 |
| Flask | 容器中的应用服务器，处理 HTTP 请求、查询数据库、生成响应 |
| PostgreSQL | 保存用户、班级、选课关系和成绩的数据库 |
| 被测主机 | 管理员在 Test the server 中填写的 Ping 目标 |

- **TB1**：浏览器与 Flask 之间。
- **TB2**：Flask 与 PostgreSQL 之间。
- **TB3（视目标而定）**：Flask 容器与被测主机之间。目标位于应用信任区之外时标记 TB3；若目标是容器内的 `127.0.0.1`，可放在应用区域内。页面中的 `127.0.0.1` 指运行 Ping 的 Web 容器自身。

## 编号 Flow List

### A 学生登录

依据 `login()`，对应 `POST /login`。教师和管理员也使用同一登录路由；正式图可以按角色复用这组流程，并注明不同浏览器。

| 编号 | 发送方 → 接收方 | 消息或数据 | 边界 |
| --- | --- | --- | --- |
| 1 | 学生浏览器 → Flask | `POST /login`：`username`、`password` | TB1 |
| 2 | Flask → PostgreSQL | 查询 `users`：使用用户名和密码匹配账号 | TB2 |
| 3 | PostgreSQL → Flask | 匹配的 `id`、`username`、`role`；没有匹配时返回空结果 | TB2 |
| 4 | Flask → 学生浏览器 | 成功时返回会话 Cookie 和重定向；失败时返回带错误提示的登录页 | TB1 |

登录后的跳转会触发后续请求；读取成绩页单独列在 B 组。

### B 学生请求查看成绩

依据 `dashboard()`，对应 `GET /dashboard`，表示打开个人成绩页面。

| 编号 | 发送方 → 接收方 | 消息或数据 | 边界 |
| --- | --- | --- | --- |
| 5 | 学生浏览器 → Flask | `GET /dashboard`：携带会话 Cookie | TB1 |
| 6 | Flask → PostgreSQL | 根据会话中的学生 ID 查询 `notes`，关联 `classes` 获取课程名 | TB2 |
| 7 | PostgreSQL → Flask | 该学生的成绩 ID、课程名、成绩和评语 | TB2 |
| 8 | Flask → 学生浏览器 | 成绩页 HTML；包含成绩列表，以及供详情查询使用的 JWT | TB1 |

你的“数据库返回成绩”对应编号 7；学生真正看到网页还需要编号 8。

### C 教师新增成绩

教师页的表单名为 **Add / update a grade**。`note_id` 留空表示新增成绩，对应 `INSERT`。你原先把“教师修改成绩”和“数据库增加成绩”放在一起，这里将“新增”单独列出。

依据 `grades()` 的新增分支，对应 `POST /grades`。

| 编号 | 发送方 → 接收方 | 消息或数据 | 边界 |
| --- | --- | --- | --- |
| 9 | 教师浏览器 → Flask | `POST /grades`：空 `note_id`、`student_id`、`class_id`、`grade`、`comment`，以及会话 Cookie | TB1 |
| 10 | Flask → PostgreSQL | `INSERT INTO notes`：写入学生 ID、班级 ID、成绩和评语 | TB2 |
| 11 | PostgreSQL → Flask | INSERT 执行完成状态 | TB2 |
| 12 | Flask → 教师浏览器 | HTTP 302，重定向到 `/teacher` | TB1 |

当前 INSERT 没有 `RETURNING`，代码也未读取新增记录 ID，因此编号 11 写执行状态，不写“返回新增成绩详情”。

### D 教师更新已有成绩

`note_id` 填写已有成绩记录 ID 表示更新，对应 `UPDATE`。依据 `grades()` 的更新分支，仍使用 `POST /grades`。

| 编号 | 发送方 → 接收方 | 消息或数据 | 边界 |
| --- | --- | --- | --- |
| 13 | 教师浏览器 → Flask | `POST /grades`：已有 `note_id`、新 `grade`、新 `comment`，以及会话 Cookie；表单同时发送学生和班级 ID | TB1 |
| 14 | Flask → PostgreSQL | `UPDATE notes`：按成绩记录 ID 修改 `grade`、`comment` | TB2 |
| 15 | PostgreSQL → Flask | UPDATE 执行完成状态 | TB2 |
| 16 | Flask → 教师浏览器 | HTTP 302，重定向到 `/teacher` | TB1 |

更新分支只修改成绩和评语。你的“教师更新成绩”和“数据库更新成绩”分别对应编号 13、14。

### E 管理员请求增加用户

依据 `admin_users()` 的 `action=create` 分支，对应 `POST /admin/users`。

| 编号 | 发送方 → 接收方 | 消息或数据 | 边界 |
| --- | --- | --- | --- |
| 17 | 管理员浏览器 → Flask | `POST /admin/users`：`action=create`、`username`、`password`、`role`，以及会话 Cookie | TB1 |
| 18 | Flask → PostgreSQL | `INSERT INTO users`：写入用户名、密码、角色；当前代码将 `teacher_id` 设为 NULL | TB2 |
| 19 | PostgreSQL → Flask | INSERT 执行完成状态 | TB2 |
| 20 | Flask → 管理员浏览器 | HTTP 302，重定向到 `/admin` | TB1 |

新增用户后的重定向会触发 `GET /admin`，再查询并显示用户列表；HTTP 302 本身不包含完整用户列表。

### F 管理员使用 Test the server

你已确认“admin test user”指管理员页的 **Test the server（Ping）**。依据 `admin_ping()`、`_all_users()`、`_all_classes()`，对应 `POST /admin/ping`。

Flask 在 Web 容器内调用 `ping -c 1`，然后重新读取用户与班级列表，并返回包含 Ping 结果的管理页。画图时可把 Flask 与容器内 Ping 程序放在同一应用节点中。

| 编号 | 发送方 → 接收方 | 消息或数据 | 边界 |
| --- | --- | --- | --- |
| 21 | 管理员浏览器 → Flask | `POST /admin/ping`：目标 `host` 和会话 Cookie | TB1 |
| 22 | Flask 容器内 Ping 程序 → 被测主机 | ICMP Echo Request，测试填写的主机是否可达 | TB3 或应用区域内 |
| 23 | 被测主机 → Flask 容器内 Ping 程序 | 收到回应时为 ICMP Echo Reply | TB3 或应用区域内 |
| 24 | Flask → PostgreSQL | 查询 `users`：读取用户列表 | TB2 |
| 25 | PostgreSQL → Flask | 用户 `id`、`username`、`role`、`teacher_id` | TB2 |
| 26 | Flask → PostgreSQL | 查询 `classes`：读取班级列表 | TB2 |
| 27 | PostgreSQL → Flask | 班级 `id`、`name`、`teacher_id` | TB2 |
| 28 | Flask → 管理员浏览器 | 管理页 HTML：Ping 输出、用户列表和班级列表 | TB1 |

你的“数据库返回 user 数据”对应编号 25。Ping 检查的是主机连通性；用户数据来自后续数据库查询。若 Ping 超时，超时提示由本地程序产生，不画成被测主机发送的数据。

### G 补充 学生查询单条成绩详情

这是学生成绩页点击 **Load** 时发生的流程，与 B 组的整页成绩列表区分。依据 `api_notes()` 和学生页的 `loadNote()`。

| 编号 | 发送方 → 接收方 | 消息或数据 | 边界 |
| --- | --- | --- | --- |
| 29 | 学生浏览器 → Flask | `GET /api/notes/<note_id>`：成绩 ID，以及 `Authorization: Bearer <JWT>` | TB1 |
| 30 | Flask → PostgreSQL | 按成绩 ID 查询 `notes`，关联用户和班级信息 | TB2 |
| 31 | PostgreSQL → Flask | 成绩 ID、学生 ID、班级 ID、成绩、评语、学生用户名和课程名 | TB2 |
| 32 | Flask → 学生浏览器 | 成绩详情 JSON；对应记录不存在时返回 HTTP 404 | TB1 |

## 你的原始想法与整理对应

| 你的原始表述 | 整理后的对应 |
| --- | --- |
| 学生登录 | A 组，编号 1–4 |
| 学生请求查看成绩 | B 组，编号 5–8；点击 Load 时是 G 组，编号 29–32 |
| 数据库返回成绩 | 编号 7 或 31，接收方是 Flask |
| 教师修改成绩 | 根据 `note_id` 区分新增（C 组）与更新已有记录（D 组） |
| 数据库增加成绩 | 编号 10：INSERT |
| 教师更新成绩 | 编号 13：提交更新请求 |
| 数据库更新成绩 | 编号 14：UPDATE |
| admin 请求增加 user | 编号 17：提交新增用户请求 |
| 数据库增加 user | 编号 18：INSERT |
| admin test user | 你已确认是 Test the server（Ping），对应 F 组，编号 21–28 |
| 数据库返回 user 数据 | 编号 25；用户查询发生在 Ping 后生成管理页的过程中 |

## 根据清单画图

1. 画学生、教师、管理员三个浏览器，Flask、PostgreSQL，以及 Ping 使用的被测主机。
2. 每行画一条有方向的箭头，写编号和数据摘要。例如：`5 学生浏览器 → Flask：GET /dashboard + 会话 Cookie`。
3. 标出 TB1、TB2；根据被测主机所在的信任区决定是否增加 TB3。
4. 保持图和本清单的编号一致，每个编号对应 STRIDE 表的一行。

本清单先覆盖你的想法与学生详情查询。后续 Explore 时还可以补充 `GET /teacher`、`GET /admin`、成绩导出、用户删除和退出登录等流程；教师页与管理页在重定向后的读取流程也需补齐。

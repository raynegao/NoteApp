# Flow List

```
1. Student → Flask: Login
2. Flask → Database: Look up account
3. Database → Flask: Account information
4. Flask → Student: Login result

5. Student → Flask → Database: Request grades
6. Database → Flask → Student: Return grades

7. Teacher → Flask → Database: Add a grade
8. Teacher → Flask → Database: Update a grade

9. Admin → Flask → Database: Add a user
10. Admin → Flask → Target host: Test the server (Ping)
11. Target host → Flask: Ping reply
12. Flask → Database: Query users
13. Database → Flask: User data
14. Flask → Admin: Ping result and user data
```

## Simple Diagram

```
Student --1--> Flask --2--> Database
Student <--4-- Flask <--3-- Database

Student --5--> Flask --5--> Database
Student <--6-- Flask <--6-- Database

Teacher --7,8--> Flask --7,8--> Database

Admin --9--> Flask --9--> Database
Admin --10--> Flask --10--> Target host
Flask <--11-- Target host

Flask --12--> Database --13--> Flask --14--> Admin
```

## First STRIDE Table



| Question | Flow | Short answer |
| --- | --- | --- |
| S: | 1–4 | Yes, with stolen login details. |
| T | 7–8 | A teacher could change another class's grades. |
| R | 9 | User creation has no log naming the creator. |
| I | 5–6 (grade API) | The API could expose other students' grades. |
| D | 10–11 | Repeated Ping requests could keep the server busy. |
| E | 10 | Ping input could run extra system commands. |

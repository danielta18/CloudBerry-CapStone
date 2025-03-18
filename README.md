# To Do Tracker

To-Do Tracker is a simple and intuitive to-do list application that allows users to manage their tasks efficiently. 
It includes features like task management, reminders with email notifications, file attachments stored in AWS S3, and timezone support.


## Features
- 📝 **Task Management:** Add, edit, and delete tasks.
- ⏰ **Reminders:** Set custom reminders with timezone support.
- 📧 **Email Notifications:** Get reminder emails at the scheduled time.
- 📂 **File Attachments:** Upload and view task-related files stored on AWS S3.
- 🔒 **User Authentication:** Secure login and signup with password hashing.


## 🚀 Deployment

The To-Do Tracker App is hosted on **Amazon EC2**.

### 🌐 **Access**
- The app is accessible at:  
[http://ec2-3-86-199-214.compute-1.amazonaws.com:5000/]

### ⚙️ Tech Stack
- **Backend:** Flask (Python)
- **Database:** MySQL (Amazon RDS)
- **File Storage:** AWS S3
- **Email Notifications:** Flask-Mail with Gmail SMTP
- **Task Scheduling:** APScheduler
- **Hosting:** Amazon EC2 instance (Ubuntu 22.04)
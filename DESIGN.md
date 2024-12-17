# Project VoteHub: Design Document

This document provides a technical overview of **Project VoteHub**, discussing its implementation and the design decisions that guided its development.


## **Project Overview**

Project VoteHub is a web-based application that allows users to share project ideas, vote for their favorite ones, and discover creative ideas. The application is built using Flask for the backend, SQLite for data storage, and HTML, JavaScript, CSS and Bootstrap for a responsive and user-friendly frontend. 

## **Architecture**

The application follows a **Model-View-Controller (MVC)** design pattern:
1. **Model**:
   - SQLite database (`voting.db`) manages persistent storage.
   - The database contains tables for users, projects, and system_status i.e project posting and voting phases.
2. **View**:
   - HTML templates (using Jinja2) in the `templates` directory render dynamic web pages.
   - CSS files in the `static` directory, Bootstrap and JavaScript enhance the visual presentation.
3. **Controller**:
   - `app.py` serves as the main entry point, handling routing, logic, and database interactions.


## **Database Design**

The database consists of three core tables:
1. **`users` Table**:
   - Stores user credentials and voting status.
   - Key fields: `id`, `username`, `hashed_password`, `voted`.
   - Passwords are hashed using `werkzeug.security` for security purposes.
   - `voted` status determines wether a user has voted or not
2. **`projects` Table**:
   - Stores details of user-submitted projects.
   - Key fields: `id`, `title`, `description`, `youtube_link`, `votes`.
3. **`system_status` Table**:
   -Manages the posting of projects and voting by the users.
   - Key fields: `posting_status`, `voting_status`
   - Ensures users can post and vote for a project at the same time.


## **Key Features and Implementation**

### **User Authentication**
- **Sign Up and Login**:
  - Users sign up by providing a username and password entered twice.
  - Passwords are hashed using `generate_password_hash` from `werkzeug.security`.
  - Login sessions are managed using Flask sessions.
- **Admin Access**:
  - Admins are identified using their IDs in the `users` table.
  - Admins can manage posting and voting for projects as well as user data.

### **Project Management**
- **Posting Projects**:
  - Users submit projects via a form on `post_project.html`.
  - Project data (title, description, YouTube link) is validated and stored in the database.
- **Viewing Projects**:
  - Projects are dynamically rendered on the View Projects page using the `view_projects.html` template.
  - The project with the highest votes is displayed in the `index.html`.

### **Voting System**
- Users can cast votes for projects.
- Each vote updates the `votes` field in the `projects` table.
- To prevent multiple votes, the `users` table tracks the users that have voted.


## **Frontend Design**

1. **Templates**:
   - Templates are stored in the `templates` directory and rendered using Jinja2.
   - Key templates:
     - `index.html`: Homepage showing top projects.
     - `login.html`: User login page.
     - `signup.html`: User registration page
     - `post_project.html`: Form for submitting projects.
     - `view_projects.html`: Project rendering page
2. **Styling**:
   - The `static/main.css` file provides custom styles for the project.
   - Bootstrap is used for responsive layout and consistency.
   - JavaScript is used to provide additional confetti styling in the homepage.


## **Design Decisions**

1. **Framework Choice**:
   - Flask was chosen for its simplicity and flexibility, ideal for our small project.
2. **Database**:
   - SQLite was selected due to its lightweight nature and ease of setup, making it suitable for local development.
3. **Password Security**:
   - Passwords are securely hashed using industry-standard tools from `werkzeug.security`.
4. **Responsive Design**:
   - Bootstrap ensures the application is accessible on devices of all sizes.


-- Seed data for TaskFlow Pro
USE taskflow_pro;

-- Default departments
INSERT INTO departments (name, description) VALUES
('Engineering', 'Software development and technical operations'),
('Design', 'UI/UX and creative design'),
('Marketing', 'Marketing and growth'),
('Human Resources', 'HR and people operations'),
('Sales', 'Sales and business development'),
('Operations', 'Business operations and support');

-- Default admin user (password: Admin@123)
-- bcrypt hash for Admin@123
INSERT INTO users (email, password_hash, role, is_active, email_verified) VALUES
('admin@taskflow.pro', '$2b$12$ifZWD9sbStwwktUxGK061.UZvM3RdWMMJr3bMFM3YCzhAT8ULP.B6', 'admin', TRUE, TRUE),
('manager@taskflow.pro', '$2b$12$ifZWD9sbStwwktUxGK061.UZvM3RdWMMJr3bMFM3YCzhAT8ULP.B6', 'manager', TRUE, TRUE),
('employee@taskflow.pro', '$2b$12$ifZWD9sbStwwktUxGK061.UZvM3RdWMMJr3bMFM3YCzhAT8ULP.B6', 'employee', TRUE, TRUE);

INSERT INTO employees (user_id, employee_code, first_name, last_name, phone, department_id, designation, joining_date, employment_status, skills) VALUES
(1, 'EMP001', 'Alex', 'Johnson', '+1-555-0101', 1, 'System Administrator', '2023-01-15', 'active', '["Leadership", "System Architecture", "DevOps"]'),
(2, 'EMP002', 'Sarah', 'Chen', '+1-555-0102', 1, 'Engineering Manager', '2023-03-20', 'active', '["Team Management", "Agile", "Python", "React"]'),
(3, 'EMP003', 'Mike', 'Williams', '+1-555-0103', 1, 'Software Developer', '2023-06-01', 'active', '["JavaScript", "TypeScript", "Node.js", "React"]');

UPDATE departments SET head_id = 2 WHERE id = 1;

INSERT INTO user_settings (user_id, theme, dashboard_widgets) VALUES
(1, 'dark', '["stats","tasks","activity","deadlines","analytics","productivity"]'),
(2, 'dark', '["stats","tasks","activity","deadlines","analytics"]'),
(3, 'dark', '["stats","tasks","deadlines"]');

-- Sample labels
INSERT INTO labels (name, color, created_by) VALUES
('Bug', '#EF4444', 1),
('Feature', '#3B82F6', 1),
('Enhancement', '#8B5CF6', 1),
('Documentation', '#06B6D4', 1),
('Urgent', '#F59E0B', 1);

-- Sample projects
INSERT INTO projects (name, description, status, health_status, start_date, end_date, completion_percentage, created_by) VALUES
('TaskFlow Pro v2.0', 'Major platform upgrade with new features and improved UX', 'active', 'on_track', '2025-01-01', '2025-12-31', 65.00, 1),
('Mobile App Launch', 'Cross-platform mobile application development', 'active', 'at_risk', '2025-03-01', '2025-09-30', 40.00, 2),
('API Modernization', 'REST to GraphQL migration project', 'planning', 'on_track', '2025-06-01', '2025-11-30', 10.00, 2);

INSERT INTO project_members (project_id, employee_id, role) VALUES
(1, 1, 'owner'), (1, 2, 'manager'), (1, 3, 'developer'),
(2, 2, 'manager'), (2, 3, 'developer'),
(3, 2, 'manager'), (3, 3, 'developer');

INSERT INTO project_milestones (project_id, title, description, due_date, is_completed) VALUES
(1, 'MVP Release', 'Minimum viable product launch', '2025-06-30', TRUE),
(1, 'Beta Testing', 'Closed beta with select users', '2025-09-30', FALSE),
(1, 'Public Launch', 'Full public release', '2025-12-31', FALSE);

-- Sample tasks
INSERT INTO tasks (title, description, status, priority, project_id, assigned_to, created_by, due_date, estimated_hours, actual_hours, progress_percentage) VALUES
('Design dashboard wireframes', 'Create high-fidelity wireframes for the new dashboard', 'completed', 'high', 1, 3, 2, '2025-05-15 17:00:00', 16, 14, 100),
('Implement authentication system', 'Build secure login, signup, and session management', 'in_progress', 'critical', 1, 3, 1, '2025-07-15 17:00:00', 40, 28, 70),
('Setup CI/CD pipeline', 'Configure automated testing and deployment', 'review', 'high', 1, 2, 1, '2025-07-10 17:00:00', 24, 20, 85),
('Write API documentation', 'Document all REST endpoints with examples', 'not_started', 'medium', 1, 3, 2, '2025-08-01 17:00:00', 12, 0, 0),
('Mobile responsive testing', 'Test all pages on various mobile devices', 'on_hold', 'medium', 2, 3, 2, '2025-07-20 17:00:00', 8, 0, 0),
('Database optimization', 'Optimize slow queries and add indexes', 'overdue', 'high', 1, 2, 1, '2025-06-25 17:00:00', 16, 10, 60),
('User onboarding flow', 'Design and implement user onboarding', 'in_progress', 'medium', 2, 3, 2, '2025-08-15 17:00:00', 20, 8, 40),
('Security audit', 'Perform comprehensive security review', 'not_started', 'critical', 1, 1, 1, '2025-09-01 17:00:00', 32, 0, 0);

INSERT INTO task_labels (task_id, label_id) VALUES (1, 2), (2, 2), (2, 5), (6, 1), (6, 5);

INSERT INTO subtasks (task_id, title, is_completed, position) VALUES
(2, 'Login page', TRUE, 1),
(2, 'Signup page', TRUE, 2),
(2, 'Password reset flow', FALSE, 3),
(2, 'Session management', FALSE, 4);

INSERT INTO comments (task_id, user_id, content) VALUES
(2, 2, 'Great progress on the auth module! Make sure to add rate limiting.'),
(2, 3, 'Working on the password reset flow now. Should be done by EOD.'),
(6, 1, 'This is overdue - please prioritize this task.');

INSERT INTO notifications (user_id, type, title, message, link, is_read) VALUES
(3, 'task_assigned', 'New Task Assigned', 'You have been assigned: Implement authentication system', '/dashboard/tasks/2', FALSE),
(3, 'deadline_reminder', 'Deadline Approaching', 'Task "Implement authentication system" is due in 2 days', '/dashboard/tasks/2', FALSE),
(2, 'overdue_alert', 'Overdue Task Alert', 'Task "Database optimization" is overdue', '/dashboard/tasks/6', FALSE),
(1, 'task_completed', 'Task Completed', 'Mike completed "Design dashboard wireframes"', '/dashboard/tasks/1', TRUE);

INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES
(1, 'login', 'user', 1, '{"method": "email"}'),
(2, 'task_created', 'task', 2, '{"title": "Implement authentication system"}'),
(3, 'task_updated', 'task', 2, '{"field": "status", "old": "not_started", "new": "in_progress"}'),
(1, 'employee_created', 'employee', 3, '{"name": "Mike Williams"}');

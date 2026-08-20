INSERT INTO jclg_stream (stream_id, stream_code, stream_name) VALUES
    (1, 'MPC', 'Mathematics, Physics, Chemistry'),
    (2, 'BiPC', 'Biology, Physics, Chemistry'),
    (3, 'MEC', 'Mathematics, Economics, Commerce'),
    (4, 'CEC', 'Civics, Economics, Commerce'),
    (5, 'HEC', 'History, Economics, Civics')
ON CONFLICT (stream_id) DO UPDATE SET stream_code = EXCLUDED.stream_code, stream_name = EXCLUDED.stream_name;

INSERT INTO jclg_group (group_id, group_code, group_name, stream_id) VALUES
    (1, 'MPC-1', 'MPC Group 1', 1),
    (2, 'BiPC-1', 'BiPC Group 1', 2),
    (3, 'MEC-1', 'MEC Group 1', 3),
    (4, 'CEC-1', 'CEC Group 1', 4),
    (5, 'HEC-1', 'HEC Group 1', 5)
ON CONFLICT (group_id) DO UPDATE SET group_code = EXCLUDED.group_code, group_name = EXCLUDED.group_name, stream_id = EXCLUDED.stream_id;

INSERT INTO jclg_student (student_id, student_code, admission_no, name, class_name, section, stream_id, group_id)
SELECT values.student_id, values.student_code, values.admission_no, values.name, values.class_name, values.section,
       stream.stream_id, grp.group_id
FROM (VALUES
    (1, 1, 'STU001', 'JCLG2026001', 'Aarav Reddy', 'MPC', 'MPC-1', 'MPC', 'MPC-1'),
    (2, 2, 'STU002', 'JCLG2026002', 'Diya Sharma', 'BiPC', 'BiPC-1', 'BiPC', 'BiPC-1'),
    (3, 3, 'STU003', 'JCLG2026003', 'Sneha Patel', 'CEC', 'CEC-1', 'CEC', 'CEC-1'),
    (4, 4, 'STU004', 'JCLG2026004', 'Rahul Nair', 'MEC', 'MEC-1', 'MEC', 'MEC-1'),
    (5, 5, 'STU005', 'JCLG2026005', 'Kavya Iyer', 'HEC', 'HEC-1', 'HEC', 'HEC-1')
) AS values(student_id, student_code, admission_no, name, class_name, section, stream_code, group_code)
JOIN jclg_stream stream ON stream.stream_code = values.stream_code
JOIN jclg_group grp ON grp.group_code = values.group_code
ON CONFLICT (student_id) DO UPDATE SET
    student_code = EXCLUDED.student_code,
    admission_no = EXCLUDED.admission_no, name = EXCLUDED.name,
    class_name = EXCLUDED.class_name, section = EXCLUDED.section,
    stream_id = EXCLUDED.stream_id, group_id = EXCLUDED.group_id;

INSERT INTO jclg_parent (parent_id, name, contact, relation) VALUES
    (1, 'Suresh Reddy', '+91-9876500001', 'Father'),
    (2, 'Meena Sharma', '+91-9876500002', 'Mother'),
    (3, 'Rajesh Patel', '+91-9876500003', 'Father'),
    (4, 'Lakshmi Nair', '+91-9876500004', 'Mother'),
    (5, 'Vijay Iyer', '+91-9876500005', 'Father')
ON CONFLICT (parent_id) DO UPDATE SET name = EXCLUDED.name, contact = EXCLUDED.contact, relation = EXCLUDED.relation;

INSERT INTO jclg_student_parent (student_id, parent_id) VALUES
    (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)
ON CONFLICT DO NOTHING;

INSERT INTO jclg_subject (subject_id, subject_code, subject_name, stream_id) VALUES
    (1, 'MPC-MAT', 'Mathematics', 1), (2, 'MPC-PHY', 'Physics', 1), (3, 'MPC-CHE', 'Chemistry', 1),
    (4, 'BPC-BIO', 'Biology', 2), (5, 'BPC-PHY', 'Physics', 2), (6, 'BPC-CHE', 'Chemistry', 2),
    (7, 'MEC-MAT', 'Mathematics', 3), (8, 'MEC-ECO', 'Economics', 3), (9, 'MEC-COM', 'Commerce', 3),
    (10, 'CEC-CIV', 'Civics', 4), (11, 'CEC-ECO', 'Economics', 4), (12, 'CEC-COM', 'Commerce', 4),
    (13, 'HEC-HIS', 'History', 5), (14, 'HEC-ECO', 'Economics', 5), (15, 'HEC-CIV', 'Civics', 5)
ON CONFLICT (subject_id) DO UPDATE SET subject_code = EXCLUDED.subject_code, subject_name = EXCLUDED.subject_name, stream_id = EXCLUDED.stream_id;

INSERT INTO jclg_exam (exam_id, exam_name, exam_date) VALUES
    (1, 'Unit Test 1', '2026-07-15'), (2, 'Quarterly Examination', '2026-08-01')
ON CONFLICT (exam_id) DO UPDATE SET exam_name = EXCLUDED.exam_name, exam_date = EXCLUDED.exam_date;

INSERT INTO jclg_attendance (student_id, attendance_date, status, assignments_completed, participation_score, engagement_status)
SELECT student_id, attendance_date, status, assignments_completed, participation_score, engagement_status
FROM (VALUES
    (1, '2026-08-01'::date, true, 10, 8.5, 'Active'), (1, '2026-08-02'::date, true, 10, 9.0, 'Active'),
    (2, '2026-08-01'::date, true, 9, 8.0, 'Active'), (2, '2026-08-02'::date, true, 9, 8.5, 'Active'),
    (3, '2026-08-01'::date, true, 7, 7.0, 'Improving'), (3, '2026-08-02'::date, false, 6, 6.0, 'Needs Attention'),
    (4, '2026-08-01'::date, true, 9, 8.0, 'Active'), (4, '2026-08-02'::date, true, 9, 8.5, 'Active'),
    (5, '2026-08-01'::date, true, 8, 7.0, 'Improving'), (5, '2026-08-02'::date, false, 7, 6.5, 'Needs Attention')
) AS attendance(student_id, attendance_date, status, assignments_completed, participation_score, engagement_status)
WHERE NOT EXISTS (
    SELECT 1 FROM jclg_attendance existing
    WHERE existing.student_id = attendance.student_id AND existing.attendance_date = attendance.attendance_date
);

INSERT INTO jclg_marks (student_id, subject_id, exam_id, marks_obtained, total_marks, exam_date, status)
SELECT values.student_id, values.subject_id, values.exam_id, values.marks_obtained,
       values.total_marks, exam.exam_date, 'Published'
FROM (VALUES
    (1, 1, 2, 88.0, 100.0), (1, 2, 2, 82.0, 100.0), (1, 3, 2, 86.0, 100.0),
    (2, 4, 2, 91.0, 100.0), (2, 5, 2, 87.0, 100.0), (2, 6, 2, 89.0, 100.0),
    (3, 10, 2, 68.0, 100.0), (3, 11, 2, 72.0, 100.0), (3, 12, 2, 70.0, 100.0),
    (4, 7, 2, 84.0, 100.0), (4, 8, 2, 81.0, 100.0), (4, 9, 2, 86.0, 100.0),
    (5, 13, 2, 62.0, 100.0), (5, 14, 2, 65.0, 100.0), (5, 15, 2, 60.0, 100.0)
) AS values(student_id, subject_id, exam_id, marks_obtained, total_marks)
JOIN jclg_exam exam ON exam.exam_id = values.exam_id
WHERE NOT EXISTS (
    SELECT 1 FROM jclg_marks existing
    WHERE existing.student_id = values.student_id AND existing.subject_id = values.subject_id AND existing.exam_id = values.exam_id
);

INSERT INTO jclg_result (student_id, exam_id, total_marks, percentage, grade, status)
SELECT values.student_id, values.exam_id, values.total_marks, values.percentage, values.grade, 'Published'
FROM (VALUES
    (1, 2, 300, 85.33, 'A'), (2, 2, 300, 89.00, 'A'),
    (3, 2, 300, 70.00, 'B'), (4, 2, 300, 83.67, 'A'),
    (5, 2, 300, 62.33, 'C')
) AS values(student_id, exam_id, total_marks, percentage, grade)
WHERE NOT EXISTS (
    SELECT 1 FROM jclg_result existing
    WHERE existing.student_id = values.student_id AND existing.exam_id = values.exam_id
);

INSERT INTO jclg_ai_usage (student_id, module_name, tokens_used, used_at)
SELECT values.student_id, values.module_name, values.tokens_used, values.used_at::timestamptz
FROM (VALUES
    (1, 'Student Analysis', 420, '2026-08-05T10:00:00+05:30'),
    (2, 'Student Analysis', 390, '2026-08-05T10:05:00+05:30'),
    (3, 'Risk Analysis', 510, '2026-08-05T10:10:00+05:30'),
    (4, 'Student Analysis', 405, '2026-08-05T10:15:00+05:30'),
    (5, 'Risk Analysis', 560, '2026-08-05T10:20:00+05:30')
) AS values(student_id, module_name, tokens_used, used_at)
WHERE NOT EXISTS (
    SELECT 1 FROM jclg_ai_usage existing
    WHERE existing.student_id = values.student_id
      AND existing.module_name = values.module_name
      AND existing.used_at = values.used_at::timestamptz
);

INSERT INTO jclg_ai_insight (student_id, stream_id, analysis_type, risk_level, recommendation)
SELECT values.student_id, stream.stream_id, values.analysis_type, values.risk_level, values.recommendation
FROM (VALUES
    (1, 'MPC', 'Performance Review', 'Low', 'Maintain consistent practice in Mathematics and Physics.'),
    (2, 'BiPC', 'Performance Review', 'Low', 'Continue laboratory practice and revise Biology diagrams weekly.'),
    (3, 'CEC', 'Risk Analysis', 'High', 'Improve attendance and use guided revision for Civics and Economics.'),
    (4, 'MEC', 'Performance Review', 'Low', 'Continue balanced preparation across Mathematics, Economics, and Commerce.'),
    (5, 'HEC', 'Risk Analysis', 'Moderate', 'Attend all classes and complete weekly History and Civics revision.')
) AS values(student_id, stream_code, analysis_type, risk_level, recommendation)
JOIN jclg_stream stream ON stream.stream_code = values.stream_code
WHERE NOT EXISTS (
    SELECT 1 FROM jclg_ai_insight existing
    WHERE existing.student_id = values.student_id AND existing.analysis_type = values.analysis_type
);
